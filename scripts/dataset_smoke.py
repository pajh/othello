#!/usr/bin/env python3
"""User-run smoke check for the saved 1,000-game dataset conversion."""

import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / 'runs/run-197b46d72b9447ebb2e315321400b3e8'
OUTPUT = RUN / 'dataset'
SEED = 12345
TRAIN_GAMES = 800
VALIDATION_GAMES = 200
TOTAL_GAMES = 1000
TOTAL_ROWS = 60411


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def read_source_expectations():
    """Read labels/counts only; do not replay rules or build converter samples."""
    expected = {}
    for line_number, line in enumerate((RUN / 'games.jsonl').open(encoding='utf-8'), 1):
        if not line.strip():
            continue
        record = json.loads(line)
        require(record['termination'] == 'normal',
                'expected the saved collection to contain no forfeits')
        require(record['training_eligible'] is True,
                'source game %s is not training-eligible' % record['game_id'])
        game_id = record['game_id']
        require(game_id not in expected,
                'duplicate source game_id %s at line %d' % (game_id, line_number))
        labels = []
        for position in record['positions']:
            actor = position['to_play']
            winner = record['winner']
            labels.append(0 if winner == 0 else (1 if actor == winner else -1))
        require(labels, 'source game %s has no actions' % game_id)
        expected[game_id] = labels
    require(len(expected) == TOTAL_GAMES,
            'expected %d source games, found %d' % (TOTAL_GAMES, len(expected)))
    require(sum(map(len, expected.values())) == TOTAL_ROWS,
            'source action total differs from expected %d' % TOTAL_ROWS)
    return expected


def load_archive(path):
    with np.load(path, allow_pickle=False) as archive:
        require(set(archive.files) == {'boards', 'outcomes', 'game_ids', 'plies'},
                '%s has unexpected arrays %r' % (path, archive.files))
        arrays = {name: archive[name] for name in archive.files}
    boards = arrays['boards']
    outcomes = arrays['outcomes']
    game_ids = arrays['game_ids']
    plies = arrays['plies']
    require(boards.dtype == np.dtype('uint8') and boards.ndim == 4
            and boards.shape[1:] == (2, 8, 8),
            '%s boards shape/dtype is %r/%s' % (path, boards.shape, boards.dtype))
    require(outcomes.dtype == np.dtype('int8') and outcomes.shape == (len(boards),),
            '%s outcomes shape/dtype mismatch' % path)
    require(game_ids.dtype.kind == 'U' and game_ids.shape == (len(boards),),
            '%s game_ids must be fixed-width Unicode with one value per row' % path)
    require(plies.dtype == np.dtype('uint8') and plies.shape == (len(boards),),
            '%s plies shape/dtype mismatch' % path)
    require(np.isin(boards, (0, 1)).all(), '%s boards contain nonbinary values' % path)
    require((boards.sum(axis=1) <= 1).all(),
            '%s own/opponent planes overlap on occupied cells' % path)
    require(np.isin(outcomes, (-1, 0, 1)).all(),
            '%s outcomes contain values outside -1/0/+1' % path)
    return arrays


def grouped_ids_and_plies(arrays, expected, label):
    ids = arrays['game_ids'].tolist()
    plies = arrays['plies'].tolist()
    groups = {}
    seen_closed = set()
    prior = None
    for game_id, ply in zip(ids, plies):
        if game_id != prior:
            if game_id in seen_closed:
                raise RuntimeError('%s rows for game %s are not contiguous' % (label, game_id))
            if prior is not None:
                seen_closed.add(prior)
            prior = game_id
            groups[game_id] = []
        groups[game_id].append(ply)
    for game_id, game_plies in groups.items():
        require(game_id in expected, '%s contains unknown game_id %s' % (label, game_id))
        require(game_plies == list(range(len(expected[game_id]))),
                '%s plies for %s are incomplete or out of order' % (label, game_id))
    return set(groups)


def summary_value(text, pattern, name):
    match = re.search(pattern, text, re.MULTILINE)
    require(match is not None, 'summary missing %s' % name)
    return match


def mapped_planes(board_string, actor):
    own_char = str(actor)
    other_char = '2' if own_char == '1' else '1'
    own = np.fromiter((cell == own_char for cell in board_string), dtype=np.uint8)
    other = np.fromiter((cell == other_char for cell in board_string), dtype=np.uint8)
    return np.stack((own.reshape(8, 8), other.reshape(8, 8)))


def perspective_spot_check(expected, archives):
    source_game = None
    source_record = None
    for line in (RUN / 'games.jsonl').open(encoding='utf-8'):
        record = json.loads(line)
        if record['termination'] == 'normal' and len(record['positions']) >= 3:
            source_game = record['game_id']
            source_record = record
            break
    require(source_record is not None, 'no game has three positions for perspective spot-check')
    arrays = next((a for a in archives if source_game in set(a['game_ids'].tolist())), None)
    require(arrays is not None, 'spot-check game absent from both archives')
    indexes = np.flatnonzero(arrays['game_ids'] == source_game)
    require(len(indexes) >= 3, 'spot-check game rows are incomplete')
    for action_index in (0, 1):
        position = source_record['positions'][action_index]
        next_position = source_record['positions'][action_index + 1]
        expected_board = mapped_planes(next_position['board'], position['to_play'])
        actual_index = indexes[action_index]
        require(np.array_equal(arrays['boards'][actual_index], expected_board),
                'after-action perspective mismatch for %s ply %d'
                % (source_game, action_index))
        winner = source_record['winner']
        actor = position['to_play']
        expected_outcome = 0 if winner == 0 else (1 if winner == actor else -1)
        require(int(arrays['outcomes'][actual_index]) == expected_outcome,
                'outcome sign mismatch for %s ply %d' % (source_game, action_index))


def run():
    command = [
        sys.executable, '-m', 'training.convert',
        '--input', str(RUN), '--output-dir', str(OUTPUT), '--seed', str(SEED),
    ]
    result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
    if result.returncode:
        raise RuntimeError('converter failed (%d): %s%s' %
                           (result.returncode, result.stdout, result.stderr))

    expected = read_source_expectations()
    training = load_archive(OUTPUT / 'training.npz')
    validation = load_archive(OUTPUT / 'validation.npz')
    train_ids = grouped_ids_and_plies(training, expected, 'training')
    validation_ids = grouped_ids_and_plies(validation, expected, 'validation')
    require(len(train_ids) == TRAIN_GAMES and len(validation_ids) == VALIDATION_GAMES,
            'expected 800/200 split, got %d/%d' % (len(train_ids), len(validation_ids)))
    require(not train_ids & validation_ids, 'a game appears in both splits')
    require(train_ids | validation_ids == set(expected),
            'split game IDs do not cover every eligible source game')
    require(len(training['boards']) + len(validation['boards']) == TOTAL_ROWS,
            'archive row total is not %d' % TOTAL_ROWS)
    summary = (OUTPUT / 'conversion-summary.txt').read_text(encoding='utf-8')
    require('source run id (from metadata.json): c503b2b07e6a46f9bb1a1a78e9bfdac5'
            in summary, 'summary has the wrong metadata run ID')
    expected_summary = {
        'training games': (r'^training games \(floor-rounded\): (\d+)$', TRAIN_GAMES),
        'validation games': (r'^validation games: (\d+)$', VALIDATION_GAMES),
        'input games': (r'^input games: (\d+)$', TOTAL_GAMES),
        'forfeits': (r'^skipped forfeit games: (\d+)$', 0),
        'eligible games': (r'^eligible games: (\d+)$', TOTAL_GAMES),
        'total positions': (r'^total positions: (\d+)$', TOTAL_ROWS),
        'training positions': (r'^training positions: (\d+)$', len(training['boards'])),
        'validation positions': (r'^validation positions: (\d+)$', len(validation['boards'])),
    }
    for name, (pattern, value) in expected_summary.items():
        match = summary_value(summary, pattern, name)
        require(int(match.group(1)) == value, 'summary %s count mismatch' % name)
    require(summary_value(summary, r'^split seed: (\d+)$', 'split seed').group(1)
            == str(SEED), 'summary split seed mismatch')
    require(summary_value(summary, r'^split train fraction: ([^\n]+)$',
                          'split fraction').group(1) == '0.8',
            'summary split fraction mismatch')
    for label, arrays in (('training', training), ('validation', validation)):
        match = summary_value(
            summary, r'^%s outcomes: -1=(\d+) 0=(\d+) \+1=(\d+)$' % label,
            label + ' outcome counts',
        )
        actual = tuple(int(np.count_nonzero(arrays['outcomes'] == value))
                       for value in (-1, 0, 1))
        require(tuple(map(int, match.groups())) == actual,
                '%s outcome counts do not match arrays' % label)
        source_labels = [label for game_id in (train_ids if label == 'training'
                                               else validation_ids)
                         for label in expected[game_id]]
        require(actual == tuple(source_labels.count(value) for value in (-1, 0, 1)),
                '%s outcome counts do not match source records' % label)

    perspective_spot_check(expected, (training, validation))
    print('PASS: 1,000 eligible games, 800/200 split, 60,411 rows; '
          'arrays, summary, IDs/plies, labels, and two perspective rows agree.')
    print('Artifacts: %s' % OUTPUT)
    print('The forfeit-exclusion path is not exercised by this zero-forfeit collection.')


if __name__ == '__main__':
    try:
        run()
    except (OSError, RuntimeError, ValueError) as exc:
        print('FAIL: %s' % exc, file=sys.stderr)
        raise SystemExit(1)
