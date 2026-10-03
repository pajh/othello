#!/usr/bin/env python3
"""Collect and review a user-run NN self-play batch (default 5,000 games)."""

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'runs/selfplay-5000'
CHECKPOINT = (ROOT / 'checkpoints/first-model/run-2103bc51994e46a099f8b3d78618efd3'
              / 'best.pt')
GAMES = 5000
SEED = 90001
WORKERS = 1
BOT_MODULE = 'bots.nn_bot'
SEED_DERIVATION = 'sha256-first-8-bytes-big-endian:{master_seed}:{game_index}:{bot_id}'
#: Execution fields a run's metadata.json may record, and what a run written
#: before they existed reports instead of the current argument defaults.
EXECUTION_FIELDS = ('workers_requested', 'workers_effective', 'numerical_threads')
UNKNOWN_EXECUTION = 'not recorded by that run'


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def nonnegative_int(value):
    try:
        parsed = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError('must be an integer') from None
    if parsed < 0:
        raise argparse.ArgumentTypeError('must be 0 or greater')
    return parsed


def positive_int(value):
    try:
        parsed = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError('must be an integer') from None
    if parsed < 1:
        raise argparse.ArgumentTypeError('must be 1 or greater')
    return parsed


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seed', type=nonnegative_int, default=SEED)
    parser.add_argument('--games', type=nonnegative_int, default=GAMES)
    parser.add_argument('--workers', type=positive_int, default=WORKERS,
                        help='worker processes passed to rig.cli (1 or more); '
                             '1 keeps the sequential collection path '
                             '(default: %d)' % WORKERS)
    parser.add_argument('--output-dir', type=Path, default=OUTPUT)
    parser.add_argument('--checkpoint', type=Path, default=CHECKPOINT)
    parser.add_argument('--review-run', type=Path,
                        help='review an existing run directory without recollecting')
    return parser.parse_args(argv)


def write_json_atomic(path, value):
    temporary = None
    try:
        with tempfile.NamedTemporaryFile('w', encoding='utf-8', dir=path.parent,
                                         prefix='.' + path.name + '.',
                                         delete=False) as stream:
            temporary = Path(stream.name)
            json.dump(value, stream, indent=2)
            stream.write('\n')
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def write_latest(path, content):
    temporary = None
    try:
        with tempfile.NamedTemporaryFile('w', encoding='utf-8', dir=path.parent,
                                         prefix='.' + path.name + '.',
                                         delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(content)
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def derived_seed(master_seed, game_index, bot_id):
    source = f'{master_seed}:{game_index}:{bot_id}'.encode('ascii')
    return int.from_bytes(hashlib.sha256(source).digest()[:8], 'big')


def launch_bot_id(checkpoint):
    """Return the canonical bot's actual ID for *checkpoint*.

    The ID comes from ``bots.nn_bot.get_id()``, the single source of the
    collection identity, so it cannot drift out of step with the bot that
    actually plays. The checkpoint environment variable is set first because
    importing the module loads the checkpoint. Called only on the collection
    path, never for ``--help``.
    """
    os.environ['OTHELLO_NN_CHECKPOINT'] = str(checkpoint)
    import bots.nn_bot
    return bots.nn_bot.get_id()


def largest(counts):
    return max(counts.values(), default=0)


def summary_value(text, label):
    match = re.search(r'^%s: (\d+)$' % re.escape(label), text, re.MULTILINE)
    require(match is not None, 'CLI summary is missing %s' % label)
    return int(match.group(1))


def execution_fields(metadata):
    """Return the run's execution fields for the reports.

    Every value comes from the run's own metadata.json. A field that run did
    not record reports as unknown, so reviewing a collection made before the
    fields existed never displays this session's argument defaults as if they
    described that run.
    """
    return {field: metadata.get(field, UNKNOWN_EXECUTION)
            for field in EXECUTION_FIELDS}


def execution_lines(fields, prefix='workers'):
    """Return report lines for the run's execution fields."""
    return ['%s requested: %s' % (prefix, fields['workers_requested']),
            '%s effective: %s' % (prefix, fields['workers_effective']),
            'numerical threads: %s' % fields['numerical_threads']]


def review_run(run_dir, provenance=None, elapsed=None):
    run_dir = run_dir.resolve()
    metadata_path = run_dir / 'metadata.json'
    games_path = run_dir / 'games.jsonl'
    summary_path = run_dir.parent / 'run-summary.txt'
    require(metadata_path.is_file() and games_path.is_file(),
            'run must contain metadata.json and games.jsonl: %s' % run_dir)
    metadata = json.loads(metadata_path.read_text(encoding='utf-8'))
    if provenance is None:
        stored = run_dir / 'collection-provenance.json'
        if stored.is_file():
            provenance = json.loads(stored.read_text(encoding='utf-8'))
        else:
            pending = run_dir.parent / 'collection-provenance-pending.json'
            if pending.is_file():
                provenance = json.loads(pending.read_text(encoding='utf-8'))
    require(metadata['bot1_module'] == BOT_MODULE and metadata['bot2_module'] == BOT_MODULE,
            'run bot modules do not match expected NN module')
    # The identity comes from the run's own retained records, not from whichever
    # bot source is current, so reviewing a historical run is independent of the
    # present code. This self-play helper additionally requires both seats to
    # report the same ID, and any saved launch provenance must agree with it.
    bot1_id = metadata['bot1_id']
    bot2_id = metadata['bot2_id']
    require(bot1_id == bot2_id,
            'run bot1/bot2 IDs differ (%r vs %r) for this self-play helper'
            % (bot1_id, bot2_id))
    require(metadata['starting_player_mode'].startswith('alternating'),
            'run does not use alternating starting colours')
    require(metadata['seed_derivation'] == SEED_DERIVATION,
            'run uses an unexpected per-bot seed derivation')
    if provenance:
        for field in ('master_seed', 'requested_games'):
            require(metadata[field] == provenance[field],
                    'metadata %s disagrees with saved launch provenance' % field)
        require(provenance['bot_id'] == bot1_id,
                'saved provenance bot ID %r disagrees with retained run ID %r'
                % (provenance.get('bot_id'), bot1_id))

    requested = metadata['requested_games']
    seed = metadata['master_seed']
    fields = execution_fields(metadata)
    traces = Counter()
    prefixes = {size: Counter() for size in (4, 8, 12)}
    first_late_game = {}
    shared_late_keys = set()
    late_rows = 0
    completed = normal = forfeits = draws = 0
    wins = {1: 0, 2: 0}
    black_games = {1: 0, 2: 0}
    with games_path.open(encoding='utf-8') as stream:
        for line_number, line in enumerate(stream, 1):
            if not line.strip():
                continue
            record = json.loads(line)
            index = completed
            require(record['game_index'] == index,
                    'record line %d has unexpected game index' % line_number)
            require(record['termination'] in ('normal', 'forfeit'),
                    'game %d has invalid termination' % index)
            bots = record['bots']
            expected_black = 1 if index % 2 == 0 else 2
            require(bots['1']['colour'] == expected_black
                    and bots['2']['colour'] == 3 - expected_black,
                    'game %d colours do not alternate' % index)
            for bot_id in (1, 2):
                bot = bots[str(bot_id)]
                require(bot['module'] == BOT_MODULE,
                        'game %d bot %d module mismatch' % (index, bot_id))
                require(bot['seed'] == derived_seed(seed, index, bot_id),
                        'game %d bot %d seed derivation mismatch' % (index, bot_id))
            black_games[1 if expected_black == 1 else 2] += 1
            termination = record['termination']
            if termination == 'normal':
                normal += 1
                require(record['training_eligible'] is True,
                        'normal game %d is not training eligible' % index)
                require(record['forfeiting_bot'] is None and record['error'] is None,
                        'normal game %d contains forfeit fields' % index)
            else:
                forfeits += 1
                require(record['training_eligible'] is False
                        and record['forfeiting_bot'] in (1, 2),
                        'forfeit game %d has inconsistent eligibility/forfeiter' % index)
            winner = record['winner_bot']
            require(winner in (0, 1, 2), 'game %d has invalid winner bot' % index)
            if winner == 0:
                draws += 1
            else:
                wins[winner] += 1

            positions = record['positions']
            trace = tuple((position['to_play'], position['action'])
                          for position in positions)
            traces[trace] += 1
            for size, counts in prefixes.items():
                if len(trace) >= size:
                    counts[trace[:size]] += 1
            for position in positions[12:]:
                late_rows += 1
                key = (position['board'], position['to_play'])
                previous = first_late_game.get(key)
                if previous is None:
                    first_late_game[key] = index
                elif previous != index:
                    shared_late_keys.add(key)
            completed += 1

    require(completed == requested,
            'expected %d records, found %d' % (requested, completed))
    require(black_games == {1: (requested + 1) // 2, 2: requested // 2},
            'alternating colour totals are inconsistent: %s' % black_games)
    require(summary_path.is_file(), 'CLI run-summary.txt is missing')
    summary = summary_path.read_text(encoding='utf-8')
    for expected in ('bot 1 ID: %s (%s)' % (bot1_id, BOT_MODULE),
                     'bot 2 ID: %s (%s)' % (bot2_id, BOT_MODULE),
                     'state: completed', 'master seed: %d' % seed,
                     'seed derivation: %s' % SEED_DERIVATION,
                     'starting player mode: alternating'):
        require(expected in summary, 'CLI summary missing %r' % expected)
    for label, count in (('requested games', requested), ('completed games', completed),
                         ('normal terminations', normal), ('forfeits', forfeits),
                         ('draws', draws), ('wins, bot 1 (%s)' % BOT_MODULE, wins[1]),
                         ('wins, bot 2 (%s)' % BOT_MODULE, wins[2])):
        require(summary_value(summary, label) == count,
                'CLI summary %s disagrees with game records' % label)

    total_duplicate_games = completed - len(traces)
    duplicate_groups = sum(value >= 2 for value in traces.values())
    repeated_rows = sum(count for count in traces.values() if count >= 2)
    shared_rows = sum(1 for key, first in first_late_game.items()
                      if key in shared_late_keys)
    # Count all rows with a key shared by at least two games in a second pass,
    # keeping only one key per distinct position during the first pass.
    if shared_late_keys:
        shared_rows = 0
        with games_path.open(encoding='utf-8') as stream:
            for line in stream:
                if line.strip():
                    record = json.loads(line)
                    shared_rows += sum((p['board'], p['to_play']) in shared_late_keys
                                       for p in record['positions'][12:])
    lines = [
        'NN self-play diversity summary',
        'status: checked; descriptive measures only, no thresholds',
        'run directory: %s' % run_dir,
        'checkpoint: %s' % (provenance.get('checkpoint') if provenance else 'unknown (no saved launch provenance)'),
        'bot IDs: %s / %s' % (bot1_id, bot2_id),
        'master seed: %d' % seed,
        'requested/completed: %d / %d' % (requested, completed),
        'normal terminations: %d; forfeits: %d; draws: %d' % (normal, forfeits, draws),
        'wins by bot ID: bot 1=%d; bot 2=%d' % (wins[1], wins[2]),
        'Black assignments: bot 1=%d; bot 2=%d' % (black_games[1], black_games[2]),
    ]
    lines += execution_lines(fields)
    lines += [
        'CLI elapsed: %s' % ('%.3f s' % elapsed if elapsed is not None else 'not measured by review mode'),
        '',
        'Exact action-trace duplicates: %d duplicate groups; %d games in those groups; largest group %d; duplicate excess %d.'
        % (duplicate_groups, repeated_rows, largest(traces), total_duplicate_games),
    ]
    for size, counts in prefixes.items():
        represented = sum(counts.values())
        lines.append('First %d actions: %d unique prefixes among %d games; largest group %d.'
                     % (size, len(counts), represented, largest(counts)))
    lines += [
        'Exact cross-game late-position overlap after 12 actions: %d distinct shared (board, to_play) keys; %d rows of %d late rows use those keys.'
        % (len(shared_late_keys), shared_rows, late_rows),
        'Late-position keys use absolute board colours; no symmetry canonicalisation. These descriptive counts make no independence claim.',
    ]
    if provenance:
        lines.append('checkpoint provenance file: %s' % (run_dir / 'collection-provenance.json'))
    diversity_path = run_dir.parent / 'diversity-summary.txt'
    check_path = run_dir.parent / 'match-check.txt'
    write_latest(diversity_path, '\n'.join(lines) + '\n')
    check = [
        'status: passed', 'run directory: %s' % run_dir,
        'checkpoint: %s' % (provenance.get('checkpoint') if provenance else 'unknown'),
        'bot IDs: %s / %s' % (bot1_id, bot2_id),
        'seed: %d' % seed, 'games: requested %d; completed %d' % (requested, completed),
        'normal terminations: %d; forfeits: %d' % (normal, forfeits),
        'Black assignments: bot 1=%d; bot 2=%d' % (black_games[1], black_games[2]),
        'wins: bot 1=%d; bot 2=%d; draws=%d' % (wins[1], wins[2], draws),
    ]
    check += execution_lines(fields)
    check += [
        'CLI elapsed: %s' % ('%.3f s' % elapsed if elapsed is not None else 'not measured by review mode'),
        'seed derivation: verified against every game record',
        'CLI summary: IDs, counts, outcomes, seed and alternating mode agree',
        'diversity report: %s' % diversity_path.resolve(),
    ]
    write_latest(check_path, '\n'.join(check) + '\n')
    print('PASS: %d games checked (%d normal, %d forfeits); reports: %s and %s'
          % (completed, normal, forfeits, check_path.resolve(), diversity_path.resolve()))


def collect(args):
    checkpoint = args.checkpoint.resolve()
    require(checkpoint.is_file(), 'checkpoint does not exist: %s' % checkpoint)
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    provenance_path = output / 'collection-provenance-pending.json'
    require(not provenance_path.exists(),
            'pending provenance already exists; inspect it and use --review-run if collection completed')
    # The collection identity is whatever the canonical bot reports for this
    # checkpoint, so it can never disagree with the module the runner launches.
    bot_id = launch_bot_id(checkpoint)
    provenance = {
        'bot_id': bot_id, 'bot_module': BOT_MODULE,
        'checkpoint': str(checkpoint), 'master_seed': args.seed,
        'requested_games': args.games,
        'workers_requested': args.workers,
        'seed_derivation': SEED_DERIVATION,
        'created_before_cli_launch': True,
    }
    write_json_atomic(provenance_path, provenance)
    before = {p.resolve() for p in output.glob('run-*') if p.is_dir()}
    env = os.environ.copy()
    env['OTHELLO_NN_CHECKPOINT'] = str(checkpoint)
    command = [sys.executable, '-m', 'rig.cli', '--bot1', BOT_MODULE,
               '--bot2', BOT_MODULE, '--games', str(args.games),
               '--seed', str(args.seed), '--workers', str(args.workers),
               '--output-dir', str(output)]
    print('Checkpoint: %s\nBot ID: %s\nSeed: %d\nGames: %d\nWorkers: %d\nStarting CLI collection.'
          % (checkpoint, bot_id, args.seed, args.games, args.workers), flush=True)
    started = time.perf_counter()
    process = subprocess.Popen(command, cwd=ROOT, env=env)
    run_dir = None
    try:
        while process.poll() is None:
            current_runs = [p.resolve() for p in output.glob('run-*')
                            if p.is_dir() and p.resolve() not in before]
            if len(current_runs) == 1 and run_dir is None:
                run_dir = current_runs[0]
                write_json_atomic(run_dir / 'collection-provenance.json', provenance)
            time.sleep(0.25)
        code = process.returncode
    except KeyboardInterrupt:
        code = process.wait()
        if run_dir is None:
            current_runs = [p.resolve() for p in output.glob('run-*')
                            if p.is_dir() and p.resolve() not in before]
            if len(current_runs) == 1:
                run_dir = current_runs[0]
        if run_dir is not None:
            provenance['cli_exit_code'] = code
            write_json_atomic(run_dir / 'collection-provenance.json', provenance)
        print('Collection interrupted; provenance remains at %s' % provenance_path,
              file=sys.stderr)
        return 130
    elapsed = time.perf_counter() - started
    runs = [p.resolve() for p in output.glob('run-*')
            if p.is_dir() and p.resolve() not in before]
    require(len(runs) == 1, 'expected one new run directory, found %d' % len(runs))
    run_dir = runs[0]
    provenance['cli_exit_code'] = code
    provenance['cli_elapsed_seconds'] = round(elapsed, 3)
    write_json_atomic(run_dir / 'collection-provenance.json', provenance)
    if code:
        print('CLI exited %d; raw run and provenance retained at %s'
              % (code, run_dir), file=sys.stderr)
        return code
    review_run(run_dir, provenance=provenance, elapsed=elapsed)
    provenance_path.unlink(missing_ok=True)
    return 0


def main():
    args = parse_args()
    if args.games < 1:
        raise RuntimeError('--games must be at least 1')
    if args.review_run:
        review_run(args.review_run)
        pending = args.review_run.resolve().parent / 'collection-provenance-pending.json'
        pending.unlink(missing_ok=True)
        return 0
    return collect(args)


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError, TypeError, RuntimeError) as exc:
        print('Self-play collection failed: %s' % exc, file=sys.stderr)
        raise SystemExit(1) from exc
