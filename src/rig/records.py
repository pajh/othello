"""Game-record builder and writer for batch runs (schema version 1).

The record schema is authoritative in docs/batch-design.md.  This module
only builds and serialises one completed-game record: it does not run
games, derive seeds, create run directories, write run metadata or
format summaries.  The caller owns the stream, the run metadata and the
batch loop.

Colour codes
------------
Records use ``0`` for empty/draw, ``1`` for Black and ``2`` for White,
while ``rig.engine`` uses ``EMPTY=0``, ``BLACK=1`` and ``WHITE=-1``.
Bot IDs (1/2) are command-line identities and are kept separate from
colours, even when both bot module names are identical.

Positions are reconstructed by replaying ``GameResult.actions`` through
``rig.engine`` from ``engine.initial_board()``; each position records the
board *before* its action.  A replay that disagrees with the result is a
writer error (``ValueError``), never a bot forfeit.

Standard library only; Python >= 3.10.
"""

import json

from rig import engine
from rig.engine import Board
from rig.runner import GameResult

SCHEMA_VERSION = 1

# Record colour codes (docs/batch-design.md).
EMPTY_COLOUR = 0
BLACK_COLOUR = 1
WHITE_COLOUR = 2

_CELLS = 64
_BOT_IDS = (1, 2)

# Engine cell value -> record board character.
_CELL_CODES = {
    engine.EMPTY: '0',
    engine.BLACK: '1',
    engine.WHITE: '2',
}

# Engine colour value -> record colour code.
_COLOUR_CODES = {
    engine.EMPTY: EMPTY_COLOUR,
    engine.BLACK: BLACK_COLOUR,
    engine.WHITE: WHITE_COLOUR,
}


def encode_board(board: Board) -> str:
    """Return *board* as 64 row-major characters drawn from ``'012'``.

    Engine ``EMPTY`` becomes ``'0'``, ``BLACK`` becomes ``'1'`` and
    ``WHITE`` becomes ``'2'``.  Square numbering is row-major, so the
    string is a direct image of the engine tuple.  Raises ``ValueError``
    for a board that is not 64 valid engine cells (bools rejected).
    """
    chars = []
    for cell in board:
        if (
            isinstance(cell, bool)
            or not isinstance(cell, int)
            or cell not in _CELL_CODES
        ):
            raise ValueError(
                'board cells must be engine.EMPTY, engine.BLACK or engine.WHITE'
            )
        chars.append(_CELL_CODES[cell])
    if len(chars) != _CELLS:
        raise ValueError('board must have exactly %d cells' % _CELLS)
    return ''.join(chars)


def _require_colour(colour, what):
    """Return the record code for engine colour *colour* (bools rejected)."""
    if (
        isinstance(colour, bool)
        or not isinstance(colour, int)
        or colour not in _COLOUR_CODES
    ):
        raise ValueError(
            '%s must be engine.EMPTY, engine.BLACK or engine.WHITE' % what
        )
    return _COLOUR_CODES[colour]


def _require_bot_id(key, what):
    """Return bot ID 1 or 2 for an int or string key (bools rejected)."""
    if isinstance(key, bool):
        raise ValueError('%s must be bot ID 1 or 2' % what)
    if isinstance(key, str) and key in ('1', '2'):
        return int(key)
    if isinstance(key, int) and key in _BOT_IDS:
        return key
    raise ValueError('%s must be bot ID 1 or 2' % what)


def _normalise_bots(bots):
    """Validate *bots* and return ``(entries, colour_to_bot_id)``.

    ``bots`` maps a bot ID (``1``/``2`` as int or string) to a dict with
    ``module``, ``colour``, ``seed`` and ``config``.  The returned entries
    are rebuilt in schema key order with string IDs for the record.
    """
    if not isinstance(bots, dict):
        raise ValueError('bots must be a dict keyed by bot ID')

    entries = {}
    for key, entry in bots.items():
        bot_id = _require_bot_id(key, 'bot key')
        if bot_id in entries:
            raise ValueError('duplicate bot ID %d' % bot_id)
        entries[bot_id] = _bot_entry(bot_id, entry)

    if set(entries) != set(_BOT_IDS):
        raise ValueError('bots must describe exactly bot IDs 1 and 2')
    colours = sorted(entries[bot_id]['colour'] for bot_id in _BOT_IDS)
    if colours != [BLACK_COLOUR, WHITE_COLOUR]:
        raise ValueError('bots must use record colours 1 and 2 exactly once')

    colour_to_bot = {
        entries[bot_id]['colour']: bot_id for bot_id in _BOT_IDS
    }
    return entries, colour_to_bot


def _bot_entry(bot_id, entry):
    """Return a validated schema-shaped dict for one bot."""
    if not isinstance(entry, dict):
        raise ValueError('bots[%d] must be a dict' % bot_id)
    expected = ('module', 'colour', 'seed', 'config')
    missing = [name for name in expected if name not in entry]
    if missing:
        raise ValueError(
            'bots[%d] is missing %s' % (bot_id, ', '.join(missing))
        )
    unexpected = [name for name in entry if name not in expected]
    if unexpected:
        raise ValueError(
            'bots[%d] has unexpected %s'
            % (bot_id, ', '.join(sorted(str(name) for name in unexpected)))
        )
    module = entry['module']
    if not isinstance(module, str) or not module:
        raise ValueError('bots[%d].module must be a non-empty string' % bot_id)
    colour = entry['colour']
    if (
        isinstance(colour, bool)
        or not isinstance(colour, int)
        or colour not in (BLACK_COLOUR, WHITE_COLOUR)
    ):
        raise ValueError('bots[%d].colour must be 1 or 2' % bot_id)
    seed = entry['seed']
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise ValueError('bots[%d].seed must be an int (bools rejected)' % bot_id)
    config = entry['config']
    if not isinstance(config, dict):
        raise ValueError('bots[%d].config must be a dict' % bot_id)
    return {
        'module': module,
        'colour': colour,
        'seed': seed,
        'config': config,
    }


def _replay_positions(actions):
    """Return ``(positions, final_board)`` for accepted *actions*.

    The replay starts from ``engine.initial_board()`` with Black to move
    and alternates the colour after every accepted action, including
    passes.  Position *ply* *n* holds the board *before* action *n*, the
    record colour code of the player who took it, and the action itself
    (a square ``0..63``, or ``None`` for a forced pass).  Any inconsistency
    with the action sequence raises ``ValueError``.
    """
    if not isinstance(actions, (tuple, list)):
        raise ValueError('result.actions must be a sequence of (colour, action)')

    board = engine.initial_board()
    to_play = engine.BLACK
    positions = []
    for ply, pair in enumerate(actions):
        if not isinstance(pair, (tuple, list)) or len(pair) != 2:
            raise ValueError('action %d must be a (colour, action) pair' % ply)
        colour, action = pair
        if colour != to_play:
            raise ValueError(
                'action %d was taken by the wrong colour' % ply
            )
        if action is not None and (
            isinstance(action, bool) or not isinstance(action, int)
        ):
            raise ValueError(
                'action %d must be a square 0..63 or None' % ply
            )
        positions.append({
            'ply': ply,
            'board': encode_board(board),
            'to_play': _COLOUR_CODES[colour],
            'action': action,
        })
        board = engine.apply_move(board, colour, action)
        to_play = engine.WHITE if to_play == engine.BLACK else engine.BLACK
    return positions, board


def make_game_record(
    result: GameResult,
    *,
    run_id: str,
    game_index: int,
    bots: dict,
) -> dict:
    """Return a complete schema-v1 record dict for one finished game.

    *result* is a ``rig.runner.GameResult`` (any object with the same
    fields works).  *bots* is the caller's assignment: a dict keyed by
    bot ID (``1``/``2``, int or string) whose entries carry ``module``,
    ``colour`` (``1``/``2``), ``seed`` and ``config``.  Colour
    assignments must use colours 1 and 2 exactly once.

    The record's ``bots`` field is the validated assignment under keys
    ``'1'``/``'2'``; ``winner_bot`` and ``forfeiting_bot`` are the IDs
    holding the winning and forfeiting colours (``0`` means a draw).
    ``positions`` comes from replaying the accepted actions, and
    ``final_board``/``disc_counts`` describe the result board (the board
    at forfeit time for a forfeit), with no invented terminal
    ``to_play``.  ``game_id`` is ``f"{run_id}-{game_index}"``.

    Raises ``ValueError`` for an inconsistent colour assignment, a
    malformed result or a replay that does not reproduce ``result.board``.
    """
    if not isinstance(run_id, str) or not run_id:
        raise ValueError('run_id must be a non-empty string')
    if (
        isinstance(game_index, bool)
        or not isinstance(game_index, int)
        or game_index < 0
    ):
        raise ValueError('game_index must be a non-negative integer (bools rejected)')

    entries, colour_to_bot = _normalise_bots(bots)

    winner = _require_colour(result.winner, 'result.winner')
    termination = result.termination
    if termination not in ('normal', 'forfeit'):
        raise ValueError("termination must be 'normal' or 'forfeit'")
    if termination == 'normal':
        if result.forfeiting_player is not None:
            raise ValueError('a normal game must not name a forfeiting player')
    else:
        forfeiting_colour = _require_colour(
            result.forfeiting_player, 'result.forfeiting_player'
        )
        # A forfeit is caused by Black or White; EMPTY (or a draw colour)
        # is a malformed result, not a colour that can be mapped to a bot.
        if forfeiting_colour == EMPTY_COLOUR:
            raise ValueError(
                'result.forfeiting_player must be engine.BLACK or engine.WHITE'
            )
    if result.error is not None and not isinstance(result.error, str):
        raise ValueError('result.error must be a string or None')
    if not isinstance(result.training_eligible, bool):
        raise ValueError('result.training_eligible must be a bool')
    if termination == 'forfeit' and result.training_eligible:
        raise ValueError('a forfeited game cannot be training eligible')

    positions, replayed = _replay_positions(result.actions)
    if replayed != tuple(result.board):
        raise ValueError('replayed board does not match result.board')

    black_count, white_count = engine.disc_counts(result.board)
    if (black_count, white_count) != (result.black_count, result.white_count):
        raise ValueError('result disc counts do not match result.board')

    winner_bot = 0 if winner == EMPTY_COLOUR else colour_to_bot[winner]
    forfeiting_bot = None
    if result.forfeiting_player is not None:
        forfeiting_bot = colour_to_bot[
            _COLOUR_CODES[result.forfeiting_player]
        ]

    return {
        'schema_version': SCHEMA_VERSION,
        'run_id': run_id,
        'game_id': '%s-%d' % (run_id, game_index),
        'game_index': game_index,
        'bots': {
            '1': entries[1],
            '2': entries[2],
        },
        'winner': winner,
        'winner_bot': winner_bot,
        'termination': termination,
        'training_eligible': result.training_eligible,
        'forfeiting_bot': forfeiting_bot,
        'error': result.error,
        'positions': positions,
        'final_board': encode_board(result.board),
        'disc_counts': {'black': black_count, 'white': white_count},
    }


def write_game_record(stream, record: dict) -> None:
    """Write *record* to *stream* as one compact JSON line, then flush.

    Uses ``json.dumps(..., allow_nan=False)`` with compact separators and
    no key sorting, so field order is the record's insertion order.  The
    caller owns the stream and its path, plus all run metadata; this
    function writes exactly one line and nothing else, so a caller that
    writes a record per game gets a flushed, complete-games-only log.
    """
    line = json.dumps(record, allow_nan=False, separators=(',', ':'))
    stream.write(line + '\n')
    stream.flush()
