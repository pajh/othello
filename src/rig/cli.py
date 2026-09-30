"""Sequential batch games and raw logs: ``python -m rig.cli``.

Implements docs/batch-design.md: sequential execution, reproducible
per-game seeds, alternating (or forced) bot-to-colour assignment, a fresh
run directory holding ``metadata.json`` and ``games.jsonl``, and a latest
run summary with optional numbered history.

Bots are loaded by module path and must expose a callable
``play(observation, *, rng)``.  The module is imported once and the same
``play`` function may serve both seats.  An import failure or a non-callable
``play`` is a setup error, not a game forfeit.  A bot exception during a
game becomes a forfeit record and the batch continues.

Two optional module attributes are supported.  ``get_id()`` is called once
during setup and returns the bot's display ID, which is printed, written into
``metadata.json`` and shown in the summary; a module without it reports its
module name.  ``create_player()``, when present, is called afresh for each bot
seat in each game and the returned callable plays that game, so a module that
keeps per-game state starts clean every game and the two seats never share
state; a module without it uses its module-level ``play``, which is the
stateless behaviour.  A factory that raises or returns a non-callable is an
ordinary batch failure with module context, not a fabricated forfeit.  Seed
derivation, colour assignment and the runner's per-bot, per-game RNGs are
unchanged, and no bot ID is written into ``games.jsonl`` or the training
archives.

Every finished game is recorded and flushed immediately, so an
interruption or a failure keeps all completed games.  Nothing is
accumulated across games: only per-game state and the running tally.

Exit status: 0 on normal completion (recorded forfeits are counted and do
not fail the batch), 2 for a setup error, 1 for an engine or writer
failure during the batch, 130 after ``KeyboardInterrupt``.

Standard library only; Python >= 3.10.
"""

import argparse
import hashlib
import importlib
import json
import os
import platform
import sys
import uuid
from datetime import datetime, timezone
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

from rig.records import (
    BLACK_COLOUR,
    SCHEMA_VERSION,
    WHITE_COLOUR,
    make_game_record,
    write_game_record,
)
from rig.runner import run_game

# Recorded in metadata.json so a run can be reproduced from its own files.
SEED_DERIVATION_ID = 'sha256-first-8-bytes-big-endian:{master_seed}:{game_index}:{bot_id}'

SUMMARY_NAME = 'run-summary.txt'
METADATA_NAME = 'metadata.json'
RECORDS_NAME = 'games.jsonl'

# Progress is printed this many times per batch at most (plus the first
# game), so a long run shows movement without flooding the terminal.
PROGRESS_DIVISIONS = 10

EXIT_OK = 0
EXIT_FAILED = 1
EXIT_SETUP = 2
EXIT_INTERRUPTED = 130


class SetupError(Exception):
    """A user-facing problem outside game play: bad arguments, an
    unimportable bot module, a missing ``play``, or an unusable output
    directory."""


def _positive_int(text):
    """argparse type for --games: an int of 1 or more."""
    try:
        value = int(text)
    except ValueError:
        raise argparse.ArgumentTypeError('must be an integer') from None
    if value < 1:
        raise argparse.ArgumentTypeError('must be 1 or greater')
    return value


def _parse_args(argv):
    parser = argparse.ArgumentParser(
        prog='python -m rig.cli',
        description='Play a sequential batch of Othello games and write '
                    'replayable raw records.',
    )
    parser.add_argument('--bot1', required=True, metavar='MODULE',
                        help='importable bot module for bot 1, exposing '
                             'play(observation, *, rng)')
    parser.add_argument('--bot2', required=True, metavar='MODULE',
                        help='importable bot module for bot 2, exposing '
                             'play(observation, *, rng)')
    parser.add_argument('--games', required=True, type=_positive_int,
                        metavar='N',
                        help='number of games to play (1 or more)')
    parser.add_argument('--seed', required=True, type=int, metavar='N',
                        help='master RNG seed; per-game seeds are derived '
                             'from it')
    parser.add_argument('--force-start', type=int, choices=(1, 2),
                        default=None, metavar='{1,2}',
                        help='always let this bot ID play Black; default '
                             'alternates colours by game index')
    parser.add_argument('--output-dir', default='runs/', metavar='DIR',
                        help='directory for run directories and the latest '
                             'summary (default: runs/)')
    parser.add_argument('--keep-history', action='store_true',
                        help='rotate the previous latest summary to the next '
                             'unused run-summary.N.txt before publishing the '
                             'replacement')
    return parser.parse_args(argv)


def _read_bot_id(module, module_name):
    """Return the bot's display ID, or raise SetupError.

    A module may expose ``get_id()``; it is called once here, during setup.
    The result must be a nonempty single-line string without control
    characters, so it can be printed and written into metadata safely. A
    module without ``get_id`` keeps working and reports its module name as a
    legacy display ID.
    """
    getter = getattr(module, 'get_id', None)
    if getter is None:
        return module_name
    if not callable(getter):
        raise SetupError(
            'bot module %r has a get_id attribute that is not callable'
            % module_name
        )
    try:
        value = getter()
    except Exception as exc:
        raise SetupError(
            'bot module %r get_id raised %s: %s'
            % (module_name, type(exc).__name__, exc)
        ) from exc
    if not isinstance(value, str):
        raise SetupError(
            'bot module %r get_id must return a string, got %s'
            % (module_name, type(value).__name__)
        )
    if not value:
        raise SetupError('bot module %r get_id returned an empty string'
                         % module_name)
    if '\n' in value or '\r' in value:
        raise SetupError(
            'bot module %r get_id returned a multi-line value' % module_name
        )
    if any(ord(character) < 32 or ord(character) == 127 for character in value):
        raise SetupError(
            'bot module %r get_id returned a value with control characters'
            % module_name
        )
    return value


def _load_bot(module_name):
    """Return ``{'play', 'create_player', 'id'}`` for a bot module.

    ``play`` is required.  ``create_player`` is optional: when the module
    exposes it, the batch calls it afresh for each bot seat in each game, so
    a module that keeps per-game state starts from a clean state every time;
    when it is absent, the module-level ``play`` is used directly.  ``id`` is
    the display ID from ``get_id()``, or the module name for a legacy module
    without it.  Any problem is a SetupError raised before any output is
    created.
    """
    try:
        module = importlib.import_module(module_name)
    except Exception as exc:
        raise SetupError(
            'cannot import bot module %r: %s: %s'
            % (module_name, type(exc).__name__, exc)
        ) from exc
    play = getattr(module, 'play', None)
    if not callable(play):
        raise SetupError(
            'bot module %r does not provide a callable play' % module_name
        )
    factory = getattr(module, 'create_player', None)
    if factory is not None and not callable(factory):
        raise SetupError(
            'bot module %r has a create_player attribute that is not callable'
            % module_name
        )
    return {
        'play': play,
        'create_player': factory,
        'id': _read_bot_id(module, module_name),
    }


def _new_player(bot, module_name, bot_id, game_index):
    """Return the callable that plays one bot seat in one game.

    With a ``create_player`` factory this is a fresh closure for this seat
    and game, so a stateful bot never carries state between games or between
    the two seats.  Without one it is the module-level ``play``.  A factory
    that raises or returns a non-callable is an ordinary batch failure with
    module context, not a fabricated forfeit.
    """
    factory = bot['create_player']
    if factory is None:
        return bot['play']
    try:
        player = factory()
    except Exception as exc:
        raise RuntimeError(
            'create_player for bot %d (module %r, game %d) raised %s: %s'
            % (bot_id, module_name, game_index, type(exc).__name__, exc)
        ) from exc
    if not callable(player):
        raise RuntimeError(
            'create_player for bot %d (module %r, game %d) returned %s, '
            'which is not callable'
            % (bot_id, module_name, game_index, type(player).__name__)
        )
    return player


def _derive_seed(master_seed, game_index, bot_id):
    """Return bot *bot_id*'s seed for *game_index* (docs/batch-design.md).

    The seed is the unsigned big-endian integer from the first eight bytes
    of SHA-256 over the ASCII text ``f'{master_seed}:{game_index}:{bot_id}'``.
    It depends on nothing else, so it is independent of scheduling and of
    the colour mode.
    """
    text = f'{master_seed}:{game_index}:{bot_id}'.encode('ascii')
    return int.from_bytes(hashlib.sha256(text).digest()[:8], 'big')


def _black_bot_id(game_index, force_start):
    """Return the bot ID that plays Black in *game_index*.

    Without --force-start, bot 1 is Black on even game indices and bot 2 on
    odd ones, so the two bots split the colours as evenly as the game count
    allows.  Black always moves first.
    """
    if force_start is not None:
        return force_start
    return 1 if game_index % 2 == 0 else 2


def _mode_text(force_start):
    if force_start is None:
        return 'alternating (bot 1 Black on even game indices)'
    return 'forced: bot %d always Black' % force_start


def _project_version():
    try:
        return version('othello-learning')
    except PackageNotFoundError:
        return 'unknown'


def _create_run_dir(output_dir):
    """Create and return a fresh ``run-<uuid hex>`` directory.

    The name is unique and never reused, so existing raw artifacts are
    never overwritten.
    """
    for _ in range(16):
        run_dir = output_dir / ('run-' + uuid.uuid4().hex)
        try:
            run_dir.mkdir()
        except FileExistsError:
            continue
        return run_dir
    raise SetupError(
        'could not create a unique run directory in %s' % output_dir
    )


def _write_metadata(run_dir, run_id, args, started_at, bot1_id, bot2_id):
    """Write run-level metadata and return its path.

    The bot display IDs are recorded next to the module names they came
    from.  They are run-level identity only: no ID is written into
    ``games.jsonl``, a game record's ``bots``/``config`` fields, the training
    archives or any label, so the schema-1 record format is untouched.
    """
    metadata = {
        'run_id': run_id,
        'run_directory': run_dir.name,
        'schema_version': SCHEMA_VERSION,
        'started_at_utc': started_at,
        'project_version': _project_version(),
        'python_version': platform.python_version(),
        'platform': platform.platform(),
        'git_revision': 'unknown',
        'bot1_module': args.bot1,
        'bot2_module': args.bot2,
        'bot1_id': bot1_id,
        'bot2_id': bot2_id,
        'master_seed': args.seed,
        'requested_games': args.games,
        'starting_player_mode': _mode_text(args.force_start),
        'seed_derivation': SEED_DERIVATION_ID,
    }
    path = run_dir / METADATA_NAME
    with open(path, 'w', encoding='utf-8') as stream:
        json.dump(metadata, stream, indent=2)
        stream.write('\n')
    return path


def _tally(tally, record):
    """Add one finished record's outcome to the running *tally*."""
    if record['termination'] == 'forfeit':
        tally['forfeit'] += 1
    else:
        tally['normal'] += 1
    winner_bot = record['winner_bot']
    if winner_bot == 0:
        tally['draws'] += 1
    else:
        tally[winner_bot] += 1


def _summary_text(state, *, run_id, run_dir, output_dir, args, tally,
                  completed, artifacts, error=None, bot1_id=None, bot2_id=None):
    """Return the full text of the latest run summary.

    This is collection bookkeeping for one batch, not a strength
    evaluation: a forfeit is counted as a win for the opponent.  The two bot
    ID lines sit directly below the title for every run state, including a
    failed or interrupted one, and the existing module-labelled wins lines are
    unchanged so current parsers keep working.
    """
    lines = [
        'Othello batch run summary',
        '========================',
        'bot 1 ID: %s (%s)' % (bot1_id or args.bot1, args.bot1),
        'bot 2 ID: %s (%s)' % (bot2_id or args.bot2, args.bot2),
        '',
        'state: %s' % state,
        'run id: %s' % run_id,
        'run directory: %s' % run_dir,
        '',
        'requested games: %d' % args.games,
        'completed games: %d' % completed,
        'normal terminations: %d' % tally['normal'],
        'forfeits: %d' % tally['forfeit'],
        'draws: %d' % tally['draws'],
        '',
        'wins, bot 1 (%s): %d' % (args.bot1, tally[1]),
        'wins, bot 2 (%s): %d' % (args.bot2, tally[2]),
        '',
        'master seed: %d' % args.seed,
        'seed derivation: %s' % SEED_DERIVATION_ID,
        'starting player mode: %s' % _mode_text(args.force_start),
        'latest summary: %s' % (output_dir / SUMMARY_NAME),
    ]
    if error is not None:
        lines += ['', 'error: %s' % error]
    lines += ['', 'artifacts:']
    lines += ['  %s' % path for path in artifacts]
    return '\n'.join(lines) + '\n'


def _next_history_path(output_dir, latest):
    """Return the next unused ``run-summary.N.txt`` path."""
    stem = latest.stem
    suffix = latest.suffix
    number = 1
    while (output_dir / ('%s.%d%s' % (stem, number, suffix))).exists():
        number += 1
    return output_dir / ('%s.%d%s' % (stem, number, suffix))


def _publish_summary(output_dir, text, keep_history):
    """Write *text* as the latest summary, then return its path.

    The complete replacement is written to a temporary file first, so a
    failure cannot destroy the previous summary.  With *keep_history* the
    previous summary is rotated to the next unused numbered sibling first;
    an existing archive is never overwritten.
    """
    latest = output_dir / SUMMARY_NAME
    temporary = output_dir / ('.%s.tmp-%s' % (SUMMARY_NAME, uuid.uuid4().hex))
    try:
        with open(temporary, 'w', encoding='utf-8') as stream:
            stream.write(text)
        if keep_history and latest.exists():
            os.replace(latest, _next_history_path(output_dir, latest))
        os.replace(temporary, latest)
    except OSError:
        try:
            temporary.unlink()
        except OSError:
            pass
        raise
    return latest


def _run_batch(args, loaded_bots, run_id, run_dir, tally):
    """Play every game, writing one record per finished game.

    Returns the number of completed games.  A bot forfeit is recorded and
    the batch continues; an engine or writer failure is raised after the
    completed records are already flushed, and KeyboardInterrupt is
    re-raised so the caller can publish an interrupted summary.

    *loaded_bots* maps bot ID 1 and 2 to the dictionaries ``_load_bot``
    returned.  Each game asks both bots for a fresh player, so a stateful bot
    starts clean every game and each seat keeps its own state.
    Bot-to-colour mapping, seed derivation and the runner's per-bot, per-game
    RNGs are unchanged.  The per-game ``bots`` dict below is the record
    assignment, which is why the parameter is named differently.
    """
    modules = {1: args.bot1, 2: args.bot2}
    step = max(1, args.games // PROGRESS_DIVISIONS)
    completed = 0

    with open(run_dir / RECORDS_NAME, 'w', encoding='utf-8') as stream:
        for index in range(args.games):
            seeds = {bot_id: _derive_seed(args.seed, index, bot_id)
                     for bot_id in (1, 2)}
            black_id = _black_bot_id(index, args.force_start)
            white_id = 2 if black_id == 1 else 1
            # Record the colours actually played in this game, so that
            # default alternation and --force-start are both reflected in
            # the assignment.  A fixed bot-ID mapping would misreport the
            # second and later games.
            colours = {black_id: BLACK_COLOUR, white_id: WHITE_COLOUR}
            bots = {
                bot_id: {
                    'module': modules[bot_id],
                    'colour': colours[bot_id],
                    'seed': seeds[bot_id],
                    'config': {},
                }
                for bot_id in (1, 2)
            }
            players = {bot_id: _new_player(loaded_bots[bot_id],
                                           modules[bot_id], bot_id, index)
                       for bot_id in (1, 2)}
            result = run_game(
                players[black_id], players[white_id],
                black_seed=seeds[black_id], white_seed=seeds[white_id],
            )
            record = make_game_record(
                result, run_id=run_id, game_index=index, bots=bots,
            )
            write_game_record(stream, record)
            completed += 1
            _tally(tally, record)
            if completed == 1 or completed % step == 0:
                print('completed %d/%d games (normal %d, forfeits %d)'
                      % (completed, args.games, tally['normal'],
                         tally['forfeit']))
                sys.stdout.flush()
    return completed


def main(argv=None):
    """Entry point for ``python -m rig.cli``; returns the exit status."""
    args = _parse_args(argv)

    try:
        bots = {1: _load_bot(args.bot1), 2: _load_bot(args.bot2)}
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        run_id = uuid.uuid4().hex
        run_dir = _create_run_dir(output_dir)
    except SetupError as exc:
        print('setup error: %s' % exc, file=sys.stderr)
        return EXIT_SETUP
    except OSError as exc:
        print('setup error: %s: %s' % (type(exc).__name__, exc),
              file=sys.stderr)
        return EXIT_SETUP

    tally = {'normal': 0, 'forfeit': 0, 'draws': 0, 1: 0, 2: 0}
    completed = 0
    state = 'failed'
    error_text = None
    print('run %s: %d games, %s, master seed %d'
          % (run_dir.name, args.games, _mode_text(args.force_start),
             args.seed))
    print('bot 1 ID: %s (%s)' % (bots[1]['id'], args.bot1))
    print('bot 2 ID: %s (%s)' % (bots[2]['id'], args.bot2))
    sys.stdout.flush()

    try:
        started_at = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
        metadata_path = _write_metadata(run_dir, run_id, args, started_at,
                                        bots[1]['id'], bots[2]['id'])
    except (OSError, ValueError, TypeError) as exc:
        error_text = '%s: %s' % (type(exc).__name__, exc)
        print('run %s: failed before the first game: %s'
              % (run_dir.name, error_text), file=sys.stderr)
        summary_path = None
    else:
        try:
            completed = _run_batch(args, bots, run_id, run_dir, tally)
        except KeyboardInterrupt:
            state = 'interrupted'
            print('\nrun %s: interrupted after %d completed games; completed '
                  'records are kept' % (run_dir.name, completed),
                  file=sys.stderr)
        except Exception as exc:
            error_text = '%s: %s' % (type(exc).__name__, exc)
            print('run %s: failed after %d completed games: %s'
                  % (run_dir.name, completed, error_text), file=sys.stderr)
        else:
            state = 'completed'

        artifacts = [metadata_path, run_dir / RECORDS_NAME]
        try:
            text = _summary_text(
                state, run_id=run_id, run_dir=run_dir, output_dir=output_dir,
                args=args, tally=tally, completed=completed,
                artifacts=artifacts, error=error_text,
                bot1_id=bots[1]['id'], bot2_id=bots[2]['id'],
            )
            summary_path = _publish_summary(output_dir, text,
                                            args.keep_history)
        except OSError as exc:
            summary_path = None
            print('warning: could not write the summary: %s: %s'
                  % (type(exc).__name__, exc), file=sys.stderr)
            if error_text is not None:
                print('original failure: %s' % error_text, file=sys.stderr)

    if state == 'completed':
        print('completed %d/%d games; normal %d, forfeits %d, draws %d'
              % (completed, args.games, tally['normal'], tally['forfeit'],
                 tally['draws']))
        print('  bot 1 (%s) wins: %d' % (args.bot1, tally[1]))
        print('  bot 2 (%s) wins: %d' % (args.bot2, tally[2]))
        if tally['forfeit']:
            print('note: %d forfeit(s) were recorded; those games are '
                  'excluded from training' % tally['forfeit'])
        print('bot 1 ID: %s (%s)' % (bots[1]['id'], args.bot1))
        print('bot 2 ID: %s (%s)' % (bots[2]['id'], args.bot2))
        if summary_path is not None:
            print('summary: %s' % summary_path)
        return EXIT_OK
    if state == 'interrupted':
        print('bot 1 ID: %s (%s)' % (bots[1]['id'], args.bot1))
        print('bot 2 ID: %s (%s)' % (bots[2]['id'], args.bot2))
        if summary_path is not None:
            print('interrupted summary: %s' % summary_path)
        return EXIT_INTERRUPTED
    print('bot 1 ID: %s (%s)' % (bots[1]['id'], args.bot1))
    print('bot 2 ID: %s (%s)' % (bots[2]['id'], args.bot2))
    return EXIT_FAILED


if __name__ == '__main__':
    raise SystemExit(main())
