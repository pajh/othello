"""Schema-v1 game-record parsing, replay and sample transformation.

Stage 1 of the dataset converter (docs/dataset-converter-task.md). The
public interface is :func:`load_games`, which reads a saved run directory
(or its ``games.jsonl``), validates every record against the schema-v1
contract, replays eligible normal games through ``rig.engine`` and turns
each accepted action into one after-action sample.

Nothing here splits, writes archives, summarises or trains; that is Stage
2 in ``training.convert``. ``rig.engine`` is the only implementation of
the rules and is never duplicated.

Returned structure::

    {
        "source_path": str,        # resolved games.jsonl path
        "run_id": str,             # run_id from metadata.json
        "input_game_count": int,   # nonblank JSONL lines
        "skipped_forfeit_count": int,
        "games": [                 # eligible games, input order
            {"game_id": str, "samples": [
                {"board": [own_plane, opponent_plane],  # 8x8 of 0/1
                 "outcome": -1 | 0 | 1,                # actor's view
                 "game_id": str,
                 "ply": int},
                ...
            ]},
            ...
        ],
    }

A sample's board is the position *after* its action, encoded from the
acting player's perspective: plane 0 marks that player's discs, plane 1
the opponent's, empty cells are 0 in both. ``outcome`` uses the game's
recorded final result, not a perfect-play value.

Any malformed input raises :class:`ValueError` naming the file, line and
game, so a bad record fails closed instead of producing partial data.
Standard library only; Python >= 3.10.
"""

import json
from pathlib import Path

from rig import engine

_SIZE = 8
_CELLS = _SIZE * _SIZE
_BOARD_CHARS = '012'

_METADATA_NAME = 'metadata.json'
_RECORDS_NAME = 'games.jsonl'

_RECORD_FIELDS = frozenset({
    'schema_version', 'run_id', 'game_id', 'game_index', 'bots', 'winner',
    'winner_bot', 'termination', 'training_eligible', 'forfeiting_bot',
    'error', 'positions', 'final_board', 'disc_counts',
})
_POSITION_FIELDS = frozenset({'ply', 'board', 'to_play', 'action'})
_BOT_FIELDS = frozenset({'module', 'colour', 'seed', 'config'})
_DISC_COUNT_FIELDS = frozenset({'black', 'white'})
_BOT_IDS = ('1', '2')
_COLOURS = (0, 1, 2)

# Record cell/colour codes and rig.engine values are different: records use
# 0 empty/draw, 1 Black, 2 White; the engine uses 0, 1 and -1.
_CELL_CHARS = ('0', '1', '2')
_ENGINE_CELLS = (engine.EMPTY, engine.BLACK, engine.WHITE)
_COLOUR_TO_ENGINE = {
    0: engine.EMPTY,
    1: engine.BLACK,
    2: engine.WHITE,
}
_ENGINE_TO_CELL = dict(zip(_ENGINE_CELLS, _CELL_CHARS))


def _fail(context, message):
    raise ValueError('%s: %s' % (context, message))


def _is_int(value):
    """True for a real int; bools are rejected wherever an int is required."""
    return isinstance(value, int) and not isinstance(value, bool)


def _is_board_string(value):
    return (
        isinstance(value, str)
        and len(value) == _CELLS
        and all(char in _BOARD_CHARS for char in value)
    )


def _encode_board(board):
    """Return an engine board as 64 record characters from ``012``."""
    return ''.join(_ENGINE_TO_CELL[cell] for cell in board)


def _resolve_paths(input_path):
    """Return ``(metadata_path, games_path)`` for a run directory or JSONL file."""
    given = Path(input_path)
    if given.is_dir():
        run_dir = given
        games_path = run_dir / _RECORDS_NAME
    else:
        games_path = given
        run_dir = given.parent
    metadata_path = run_dir / _METADATA_NAME
    if not metadata_path.is_file():
        _fail(str(given), 'run metadata not found at %s' % metadata_path)
    if not games_path.is_file():
        _fail(str(given), 'game records not found at %s' % games_path)
    return metadata_path, games_path.resolve()


def _read_metadata(metadata_path):
    """Validate metadata.json and return its run ID."""
    context = str(metadata_path)
    try:
        text = metadata_path.read_text(encoding='utf-8')
    except UnicodeDecodeError as exc:
        _fail(context, 'metadata is not valid UTF-8: %s' % exc)
    except OSError as exc:
        _fail(context, 'cannot read metadata: %s' % exc)
    try:
        metadata = json.loads(text)
    except json.JSONDecodeError as exc:
        _fail(context, 'invalid JSON: %s' % exc)
    if not isinstance(metadata, dict):
        _fail(context, 'metadata must be a JSON object')
    if not _is_int(metadata.get('schema_version')) or metadata['schema_version'] != 1:
        _fail(context, 'schema_version must be the integer 1')
    run_id = metadata.get('run_id')
    if not isinstance(run_id, str) or not run_id:
        _fail(context, 'run_id must be a nonempty string')
    requested = metadata.get('requested_games')
    if not _is_int(requested) or requested <= 0:
        _fail(context, 'requested_games must be a positive integer')
    return run_id


def _validate_bots(bots, context):
    """Validate the bot assignment and return ``{bot_id: colour}``."""
    if not isinstance(bots, dict) or set(bots) != set(_BOT_IDS):
        _fail(context, 'bots must be an object with exactly the string keys "1" and "2"')
    colours = {}
    for bot_id in _BOT_IDS:
        entry = bots[bot_id]
        where = '%s bots["%s"]' % (context, bot_id)
        if not isinstance(entry, dict) or set(entry) != _BOT_FIELDS:
            _fail(where, 'bot entry must be an object with exactly module, colour, seed, config')
        if not isinstance(entry['module'], str) or not entry['module']:
            _fail(where, 'module must be a nonempty string')
        if not _is_int(entry['colour']) or entry['colour'] not in (1, 2):
            _fail(where, 'colour must be the integer 1 or 2')
        if not _is_int(entry['seed']):
            _fail(where, 'seed must be an integer')
        if not isinstance(entry['config'], dict):
            _fail(where, 'config must be an object')
        colours[bot_id] = entry['colour']
    if sorted(colours.values()) != [1, 2]:
        _fail(context, 'bot colours 1 and 2 must each be used once, got %s'
              % sorted(colours.values()))
    return colours


def _validate_result(record, colours, context):
    """Validate winner/termination/eligibility fields."""
    for name in ('winner', 'winner_bot'):
        if not _is_int(record[name]) or record[name] not in _COLOURS:
            _fail(context, '%s must be the integer 0, 1 or 2' % name)
    winner = record['winner']
    winner_bot = record['winner_bot']
    if winner == 0:
        if winner_bot != 0:
            _fail(context, 'a draw must have winner 0 and winner_bot 0')
    else:
        holder = next(bot_id for bot_id, colour in colours.items() if colour == winner)
        if winner_bot != int(holder):
            _fail(context, 'winner_bot %d does not hold the winning colour %d'
                  % (winner_bot, winner))
    if not isinstance(record['training_eligible'], bool):
        _fail(context, 'training_eligible must be a boolean')
    forfeiting_bot = record['forfeiting_bot']
    if forfeiting_bot is not None and (
        not _is_int(forfeiting_bot) or forfeiting_bot not in (1, 2)
    ):
        _fail(context, 'forfeiting_bot must be null or the integer 1 or 2')
    error = record['error']
    if error is not None and not isinstance(error, str):
        _fail(context, 'error must be null or a string')
    if record['termination'] == 'normal':
        if not record['training_eligible']:
            _fail(context, 'a normal game must be training eligible')
        if forfeiting_bot is not None:
            _fail(context, 'a normal game must not name a forfeiting bot')
        if error is not None:
            _fail(context, 'a normal game must not carry an error')
    else:
        if record['training_eligible']:
            _fail(context, 'a forfeited game must not be training eligible')
        if forfeiting_bot is None:
            _fail(context, 'a forfeited game must name a forfeiting bot')


def _validate_positions(positions, context):
    """Validate the ordered position list without touching the engine."""
    if not isinstance(positions, list):
        _fail(context, 'positions must be a list')
    expected_to_play = 1
    for index, position in enumerate(positions):
        where = '%s position %d' % (context, index)
        if not isinstance(position, dict) or set(position) != _POSITION_FIELDS:
            _fail(where, 'position must be an object with exactly ply, board, to_play, action')
        if not _is_int(position['ply']) or position['ply'] != index:
            _fail(where, 'ply must be the contiguous index %d' % index)
        if not _is_board_string(position['board']):
            _fail(where, 'board must be 64 characters from 012')
        if not _is_int(position['to_play']) or position['to_play'] != expected_to_play:
            _fail(where, 'to_play must alternate from Black (1); expected %d'
                  % expected_to_play)
        expected_to_play = 2 if expected_to_play == 1 else 1
        action = position['action']
        if action is not None and (not _is_int(action) or not 0 <= action < _CELLS):
            _fail(where, 'action must be null or an integer square 0..63')


def _validate_final_state(record, context):
    """Validate final_board encoding and disc_counts against that board."""
    if not _is_board_string(record['final_board']):
        _fail(context, 'final_board must be 64 characters from 012')
    counts = record['disc_counts']
    if not isinstance(counts, dict) or set(counts) != _DISC_COUNT_FIELDS:
        _fail(context, 'disc_counts must be an object with exactly black and white')
    final_board = record['final_board']
    for name, char in (('black', '1'), ('white', '2')):
        expected = final_board.count(char)
        if not _is_int(counts[name]) or counts[name] != expected:
            _fail(context, 'disc_counts.%s must be %d for the final board'
                  % (name, expected))


def _parse_record(line, context, run_id):
    """Parse and validate one JSONL line; return the record object."""
    try:
        record = json.loads(line)
    except json.JSONDecodeError as exc:
        _fail(context, 'invalid JSON: %s' % exc)
    if not isinstance(record, dict):
        _fail(context, 'record must be a JSON object')
    keys = set(record)
    if keys != _RECORD_FIELDS:
        _fail(context, 'field mismatch missing=%s unexpected=%s'
              % (sorted(_RECORD_FIELDS - keys), sorted(keys - _RECORD_FIELDS)))
    if not _is_int(record['schema_version']) or record['schema_version'] != 1:
        _fail(context, 'schema_version must be the integer 1')
    if not isinstance(record['run_id'], str) or not record['run_id']:
        _fail(context, 'run_id must be a nonempty string')
    if record['run_id'] != run_id:
        _fail(context, 'run_id %r does not match metadata run_id %r'
              % (record['run_id'], run_id))
    if not isinstance(record['game_id'], str) or not record['game_id']:
        _fail(context, 'game_id must be a nonempty string')
    if not _is_int(record['game_index']) or record['game_index'] < 0:
        _fail(context, 'game_index must be a nonnegative integer')
    if record['termination'] not in ('normal', 'forfeit'):
        _fail(context, 'unknown termination %r' % (record['termination'],))
    colours = _validate_bots(record['bots'], context)
    _validate_result(record, colours, context)
    _validate_positions(record['positions'], context)
    _validate_final_state(record, context)
    return record


def _planes(board, actor):
    """Return ``[own_plane, opponent_plane]`` as 8x8 grids of 0/1."""
    opponent = engine.WHITE if actor == engine.BLACK else engine.BLACK
    own_plane = [[0] * _SIZE for _ in range(_SIZE)]
    other_plane = [[0] * _SIZE for _ in range(_SIZE)]
    for square in range(_CELLS):
        cell = board[square]
        if cell == actor:
            own_plane[square // _SIZE][square % _SIZE] = 1
        elif cell == opponent:
            other_plane[square // _SIZE][square % _SIZE] = 1
    return [own_plane, other_plane]


def _outcome(winner, actor):
    """Return +1/0/-1 for *actor* from the game's recorded result."""
    if winner == 0:
        return 0
    return 1 if _COLOUR_TO_ENGINE[winner] == actor else -1


def _build_game(record, context):
    """Replay one eligible game and return ``{game_id, samples}``."""
    board = engine.initial_board()
    to_play = engine.BLACK
    samples = []
    for index, position in enumerate(record['positions']):
        where = '%s position %d' % (context, index)
        if _encode_board(board) != position['board']:
            _fail(where, 'stored board does not match the replayed board')
        actor = _COLOUR_TO_ENGINE[position['to_play']]
        if actor != to_play:
            _fail(where, 'stored to_play does not match the replayed side to move')
        if engine.is_terminal(board):
            _fail(where, 'actions continue after the engine reached a terminal board')
        try:
            after = engine.apply_move(board, actor, position['action'])
        except ValueError as exc:
            _fail(where, 'engine rejected the recorded action: %s' % exc)
        samples.append({
            'board': _planes(after, actor),
            'outcome': _outcome(record['winner'], actor),
            'game_id': record['game_id'],
            'ply': position['ply'],
        })
        board = after
        to_play = engine.WHITE if to_play == engine.BLACK else engine.BLACK

    if not samples:
        _fail(context, 'an eligible game must contain at least one sample')
    if _encode_board(board) != record['final_board']:
        _fail(context, 'replayed final board does not match final_board')
    if not engine.is_terminal(board):
        _fail(context, 'replayed final position is not terminal')
    black_count, white_count = engine.disc_counts(board)
    counts = record['disc_counts']
    if (black_count, white_count) != (counts['black'], counts['white']):
        _fail(context, 'replayed disc counts %s do not match the recorded %s'
              % ([black_count, white_count], [counts['black'], counts['white']]))
    if engine.winner(board) != _COLOUR_TO_ENGINE[record['winner']]:
        _fail(context, 'engine winner does not match the recorded winner colour')
    return {'game_id': record['game_id'], 'samples': samples}


def load_games(input_path):
    """Parse, validate and replay a saved run into converter samples.

    *input_path* is either a run directory containing ``metadata.json`` and
    ``games.jsonl``, or the ``games.jsonl`` file itself. Well-formed
    forfeited games are validated and counted but contribute no samples.

    Returns the dictionary documented in the module docstring. Raises
    :class:`ValueError` naming the file, line and game on any malformed
    input, including a replay that disagrees with the record.
    """
    metadata_path, games_path = _resolve_paths(input_path)
    run_id = _read_metadata(metadata_path)

    games = []
    skipped_forfeit_count = 0
    input_game_count = 0
    seen_game_ids = set()
    seen_indexes = set()
    decoded_line_count = 0
    try:
        with open(games_path, encoding='utf-8') as stream:
            for line_number, line in enumerate(stream, start=1):
                decoded_line_count = line_number
                if not line.strip():
                    continue
                input_game_count += 1
                record = _parse_record(
                    line, '%s line %d' % (games_path, line_number), run_id
                )
                game_id = record['game_id']
                context = '%s line %d game_id=%s' % (games_path, line_number, game_id)
                if game_id in seen_game_ids:
                    _fail(context, 'duplicate game_id')
                if record['game_index'] in seen_indexes:
                    _fail(context, 'duplicate game_index %d' % record['game_index'])
                seen_game_ids.add(game_id)
                seen_indexes.add(record['game_index'])
                if record['termination'] == 'forfeit':
                    skipped_forfeit_count += 1
                    continue
                games.append(_build_game(record, context))
    except UnicodeDecodeError as exc:
        # A text stream decodes in blocks, so the failing line is the next
        # one after the last line read; that is the context available.
        _fail('%s line %d' % (games_path, decoded_line_count + 1),
              'games.jsonl is not valid UTF-8: %s' % exc)

    return {
        'source_path': str(games_path),
        'run_id': run_id,
        'input_game_count': input_game_count,
        'skipped_forfeit_count': skipped_forfeit_count,
        'games': games,
    }
