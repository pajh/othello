"""Dataset conversion: seeded whole-game split into NPZ archives plus a summary.

Stage 2 of the dataset converter (docs/dataset-converter-task.md). Stage 1's
``training.data.load_games`` is called exactly once and is the only source
of samples: this module never reparses records, replays games or reopens
the JSONL.

Command line::

    python -m training.convert --input PATH --output-dir PATH --seed INT \\
        [--train-fraction FLOAT]

``--input`` accepts the run directory or its ``games.jsonl``. Eligible games
are split whole — never by sample — with
``numpy.random.default_rng(seed).permutation`` over the games in input
order; the first ``floor(fraction * eligible_games)`` go to training and the
rest to validation. A split with either side empty is an error.

``--symmetries`` (default off, so existing conversions are unchanged) augments
each split **after** that whole-game split: every sample is replaced by the
eight board symmetries — identity, the three rotations, and the mirror image of
each rotation — giving exactly eight rows per original sample even where a
symmetric board makes some identical. Only the two spatial axes move; the actor's
own plane is never swapped with the opponent's and the outcome is never
recomputed, since rotating the table cannot change who was playing.
``outcomes``, ``game_ids`` and ``plies`` are repeated in the same order, so the
archive schema and dtypes are untouched and games stay whole and separate.

Each split is written to a fixed ``training.npz`` / ``validation.npz`` with
exactly four arrays: ``boards`` uint8 ``(N, 2, 8, 8)``, ``outcomes`` int8
``(N,)``, ``game_ids`` fixed-width Unicode ``(N,)`` and ``plies`` uint8
``(N,)``. Game IDs are never stored as objects, so the archives load with
``numpy.load(..., allow_pickle=False)``.

All artifacts are built in a staging directory inside the output directory
and only then moved onto the fixed filenames, so a failure part-way cannot
publish a partial set. Each individual rename is atomic; the set of three
files is not published atomically, so a crash between renames can leave
some files newer than others. A rerun replaces the three files.

``conversion-summary.txt`` is published last and records the source run and
path, the metadata run ID, output paths, schema and encoding versions, the
NumPy version, the split parameters, and the counts needed to check the
archives by hand.
"""

import argparse
import math
import os
import shutil
import sys
import tempfile
from pathlib import Path

import numpy as np

from training.data import load_games

RECORD_SCHEMA_VERSION = 1
ENCODING_VERSION = 1

TRAINING_NAME = 'training.npz'
VALIDATION_NAME = 'validation.npz'
SUMMARY_NAME = 'conversion-summary.txt'
_PUBLISH_ORDER = (TRAINING_NAME, VALIDATION_NAME, SUMMARY_NAME)

_SIZE = 8
_PLANES = 2
_PLY_MAX = 255

EXIT_OK = 0
EXIT_FAILED = 1


def _nonnegative_int(text):
    """argparse type for --seed."""
    try:
        value = int(text)
    except ValueError:
        raise argparse.ArgumentTypeError('must be an integer') from None
    if value < 0:
        raise argparse.ArgumentTypeError('must be 0 or greater')
    return value


def _fraction(text):
    """argparse type for --train-fraction: finite and strictly inside (0, 1)."""
    try:
        value = float(text)
    except ValueError:
        raise argparse.ArgumentTypeError('must be a number') from None
    if not math.isfinite(value) or not 0.0 < value < 1.0:
        raise argparse.ArgumentTypeError('must be finite and strictly between 0 and 1')
    return value


def _parse_args(argv):
    parser = argparse.ArgumentParser(
        prog='python -m training.convert',
        description='Split a saved run of recorded games into seeded training '
                    'and validation NPZ archives, with a conversion summary.',
    )
    parser.add_argument('--input', required=True, metavar='PATH',
                        help='run directory or its games.jsonl')
    parser.add_argument('--output-dir', required=True, metavar='PATH',
                        help='directory receiving training.npz, validation.npz '
                             'and conversion-summary.txt')
    parser.add_argument('--seed', required=True, type=_nonnegative_int, metavar='INT',
                        help='nonnegative seed for the whole-game split')
    parser.add_argument('--train-fraction', type=_fraction, default=0.8, metavar='FLOAT',
                        help='share of eligible games used for training, '
                             'strictly between 0 and 1 (default: 0.8)')
    parser.add_argument('--symmetries', action='store_true',
                        help='augment each split after the whole-game split with '
                             'the eight board symmetries (identity, three '
                             'rotations and the mirror image of each), giving '
                             'exactly eight rows per original sample; game '
                             'counts are unchanged (default: off)')
    return parser.parse_args(argv)


def game_id_width(games):
    """Return the fixed-width game-ID length covering every eligible game."""
    if not games:
        raise ValueError('no eligible games to convert')
    return max(len(game['game_id']) for game in games)


def split_games(games, seed, train_fraction):
    """Return ``(training_games, validation_games)`` as a seeded whole-game split.

    The permutation is taken over the eligible games in input order, so the
    split depends only on the seed, the fraction and the number of eligible
    games. Samples of one game are never separated.
    """
    count = len(games)
    if count < 2:
        raise ValueError('at least two eligible games are needed to split, got %d' % count)
    train_count = math.floor(train_fraction * count)
    if train_count < 1 or train_count > count - 1:
        raise ValueError(
            'train fraction %r leaves an empty split for %d eligible games'
            % (train_fraction, count)
        )
    order = np.random.default_rng(seed).permutation(count)
    training = [games[int(index)] for index in order[:train_count]]
    validation = [games[int(index)] for index in order[train_count:]]
    return training, validation


def transform_plane(plane, transform):
    """Return one plane under a symmetry *transform*.

    A transform is ``(rotations, reflected)``: mirror left to right when
    *reflected*, then apply *rotations* clockwise quarter turns (0 to 3). Only
    the last two axes move, so this works unchanged on a single 8x8 plane and on
    a whole (planes, 8, 8) stack and never touches the plane axis.
    """
    result = np.asarray(plane)
    if transform[1]:
        result = result[..., :, ::-1]
    rotations = transform[0] % 4
    if rotations:
        result = np.rot90(result, k=rotations, axes=(-2, -1))
    return result


#: The eight board symmetries, in the order their rows are written: identity,
#: then the three rotations, then the mirror image of each rotation.
TRANSFORMS = tuple((rotations, reflected)
                   for reflected in (False, True)
                   for rotations in range(4))

TRANSFORM_NAMES = ('identity', 'rotate90', 'rotate180', 'rotate270',
                   'mirror', 'mirror_rotate90', 'mirror_rotate180',
                   'mirror_rotate270')


def expand_symmetries(boards, outcomes, game_ids, plies):
    """Return the eight-fold augmentation of one already-split sample set.

    Each original row produces exactly eight rows, in TRANSFORMS order, even when
    a symmetric board makes some of them identical to each other: the row count
    stays a predictable eight times the original and no sample is dropped.
    ``outcomes``, ``game_ids`` and ``plies`` are repeated in that same order, so
    the two planes, the label, the game and the ply of a row always stay
    together. Games keep their own IDs, so a split still holds whole games and
    the trainer's disjointness check still works.
    """
    rows = boards.shape[0]
    if rows == 0:
        raise ValueError('a split with no positions cannot be expanded')
    expanded_boards = np.zeros((rows * len(TRANSFORMS), _PLANES, _SIZE, _SIZE),
                               dtype=boards.dtype)
    expanded_outcomes = np.zeros((rows * len(TRANSFORMS),), dtype=outcomes.dtype)
    expanded_game_ids = np.empty((rows * len(TRANSFORMS),), dtype=game_ids.dtype)
    expanded_plies = np.zeros((rows * len(TRANSFORMS),), dtype=plies.dtype)
    for index, transform in enumerate(TRANSFORMS):
        start = index * rows
        stop = start + rows
        expanded_boards[start:stop] = np.asarray(
            [transform_plane(boards[row], transform) for row in range(rows)])
        expanded_outcomes[start:stop] = outcomes
        expanded_game_ids[start:stop] = game_ids
        expanded_plies[start:stop] = plies
    return {'boards': expanded_boards, 'outcomes': expanded_outcomes,
            'game_ids': expanded_game_ids, 'plies': expanded_plies}


def build_arrays(games, id_length):
    """Return the four split arrays, flattened in game order then ply order."""
    positions = sum(len(game['samples']) for game in games)
    if positions == 0:
        raise ValueError('a split with no positions cannot be written as an archive')
    boards = np.zeros((positions, _PLANES, _SIZE, _SIZE), dtype=np.uint8)
    outcomes = np.zeros((positions,), dtype=np.int8)
    game_ids = np.empty((positions,), dtype='U%d' % id_length)
    plies = np.zeros((positions,), dtype=np.uint8)
    offset = 0
    for game in games:
        game_id = game['game_id']
        for sample in game['samples']:
            ply = sample['ply']
            if isinstance(ply, bool) or not isinstance(ply, int) or not 0 <= ply <= _PLY_MAX:
                raise ValueError('ply %r in game %s is outside the uint8 range 0..%d'
                                 % (ply, game_id, _PLY_MAX))
            boards[offset, 0] = sample['board'][0]
            boards[offset, 1] = sample['board'][1]
            outcomes[offset] = sample['outcome']
            game_ids[offset] = game_id
            plies[offset] = ply
            offset += 1
    written = [str(value) for value in game_ids]
    expected = [sample['game_id'] for game in games for sample in game['samples']]
    if written != expected:
        raise ValueError(
            'game IDs were truncated at width %d; widen id_length' % id_length
        )
    return {'boards': boards, 'outcomes': outcomes, 'game_ids': game_ids, 'plies': plies}


def _outcome_counts(outcomes):
    return {
        '-1': int(np.count_nonzero(outcomes == -1)),
        '0': int(np.count_nonzero(outcomes == 0)),
        '+1': int(np.count_nonzero(outcomes == 1)),
    }


def summary_text(collection, *, seed, train_fraction, train_count, validation_count,
                 training_arrays, validation_arrays, output_dir, numpy_version,
                 symmetries=False, original_training_positions=None,
                 original_validation_positions=None):
    """Return the full text of conversion-summary.txt."""
    games = collection['games']
    source_path = collection['source_path']
    training_counts = _outcome_counts(training_arrays['outcomes'])
    validation_counts = _outcome_counts(validation_arrays['outcomes'])
    total_positions = sum(len(game['samples']) for game in games)
    if original_training_positions is None:
        original_training_positions = training_arrays['outcomes'].shape[0]
    if original_validation_positions is None:
        original_validation_positions = validation_arrays['outcomes'].shape[0]
    lines = [
        'Othello dataset conversion summary',
        '===================================',
        '',
        'source path: %s' % source_path,
        'source run directory: %s' % Path(source_path).parent,
        'source run id (from metadata.json): %s' % collection['run_id'],
        'output directory: %s' % output_dir,
        '  %s' % TRAINING_NAME,
        '  %s' % VALIDATION_NAME,
        '  %s' % SUMMARY_NAME,
        '',
        'record schema version: %d' % RECORD_SCHEMA_VERSION,
        'sample encoding version: %d' % ENCODING_VERSION,
        'numpy version: %s' % numpy_version,
        '',
        'split seed: %d' % seed,
        'split train fraction: %s' % train_fraction,
        'training games (floor-rounded): %d' % train_count,
        'validation games: %d' % validation_count,
        '',
        'input games: %d' % collection['input_game_count'],
        'skipped forfeit games: %d' % collection['skipped_forfeit_count'],
        'eligible games: %d' % len(games),
        'total positions: %d' % total_positions,
        '',
        'eight-way symmetry expansion: %s'
        % ('enabled' if symmetries else 'off'),
    ]
    if symmetries:
        lines += [
            '  transforms per sample: %d (%s)'
            % (len(TRANSFORMS), ', '.join(TRANSFORM_NAMES)),
            '  each sample becomes exactly %d rows, duplicates kept; only the two'
            % len(TRANSFORMS),
            '  spatial axes move, the actor planes are never swapped and the',
            "  outcome, game ID and ply are repeated in the same order, so game",
            '  counts above are still actual games.',
        ]
    lines += [
        '',
        'training positions: %d' % training_arrays['outcomes'].shape[0],
        'validation positions: %d' % validation_arrays['outcomes'].shape[0],
    ]
    if symmetries:
        lines += [
            'training positions before expansion: %d' % original_training_positions,
            'validation positions before expansion: %d' % original_validation_positions,
        ]
    lines += [
        '',
        'training outcomes: -1=%d 0=%d +1=%d'
        % (training_counts['-1'], training_counts['0'], training_counts['+1']),
        'validation outcomes: -1=%d 0=%d +1=%d'
        % (validation_counts['-1'], validation_counts['0'], validation_counts['+1']),
    ]
    return '\n'.join(lines) + '\n'


def convert(input_path, output_dir, seed, train_fraction=0.8, symmetries=False):
    """Convert a saved run into the two archives and the summary.

    The whole-game split happens first, exactly as before, and each split is
    then built independently. With *symmetries* each built split is augmented to
    eight rows per original sample, so the two splits are never mixed and no
    game can appear in both after expansion.

    Returns a dict of published paths and counts. Raises ValueError for a
    malformed collection, an unusable split or a truncated game ID, and
    OSError for filesystem failures. Nothing is published unless every
    artifact was built successfully.
    """
    collection = load_games(input_path)
    games = collection['games']
    id_length = game_id_width(games)
    training_games, validation_games = split_games(games, seed, train_fraction)
    training_arrays = build_arrays(training_games, id_length)
    validation_arrays = build_arrays(validation_games, id_length)
    original_training_positions = training_arrays['outcomes'].shape[0]
    original_validation_positions = validation_arrays['outcomes'].shape[0]
    if symmetries:
        training_arrays = expand_symmetries(**training_arrays)
        validation_arrays = expand_symmetries(**validation_arrays)
    text = summary_text(
        collection,
        seed=seed,
        train_fraction=train_fraction,
        train_count=len(training_games),
        validation_count=len(validation_games),
        training_arrays=training_arrays,
        validation_arrays=validation_arrays,
        output_dir=output_dir,
        numpy_version=np.__version__,
        symmetries=symmetries,
        original_training_positions=original_training_positions,
        original_validation_positions=original_validation_positions,
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix='.convert-', dir=str(output_dir)))
    try:
        np.savez_compressed(staging / TRAINING_NAME, **training_arrays)
        np.savez_compressed(staging / VALIDATION_NAME, **validation_arrays)
        (staging / SUMMARY_NAME).write_text(text, encoding='utf-8')
        # Every artifact exists; only now do the fixed names appear.
        for name in _PUBLISH_ORDER:
            os.replace(staging / name, output_dir / name)
    finally:
        shutil.rmtree(staging, ignore_errors=True)

    return {
        'run_id': collection['run_id'],
        'input_game_count': collection['input_game_count'],
        'skipped_forfeit_count': collection['skipped_forfeit_count'],
        'eligible_game_count': len(games),
        'training_game_count': len(training_games),
        'validation_game_count': len(validation_games),
        'training_positions': int(training_arrays['outcomes'].shape[0]),
        'validation_positions': int(validation_arrays['outcomes'].shape[0]),
        'original_training_positions': int(original_training_positions),
        'original_validation_positions': int(original_validation_positions),
        'symmetries': bool(symmetries),
        'transform_count': len(TRANSFORMS) if symmetries else 1,
        'training_path': output_dir / TRAINING_NAME,
        'validation_path': output_dir / VALIDATION_NAME,
        'summary_path': output_dir / SUMMARY_NAME,
    }


def main(argv=None):
    """Entry point for ``python -m training.convert``; returns the exit status."""
    args = _parse_args(argv)
    output_dir = Path(args.output_dir)
    try:
        result = convert(args.input, output_dir, args.seed, args.train_fraction,
                         args.symmetries)
    except ValueError as exc:
        print('conversion failed: %s' % exc, file=sys.stderr)
        return EXIT_FAILED
    except OSError as exc:
        print('conversion failed: %s: %s' % (type(exc).__name__, exc), file=sys.stderr)
        return EXIT_FAILED
    print('converted run %s' % result['run_id'])
    print('  eight-way symmetry expansion: %s'
          % ('enabled, %d transforms per sample' % result['transform_count']
             if result['symmetries'] else 'off'))
    print('  eligible games: %d (input %d, skipped forfeits %d)'
          % (result['eligible_game_count'], result['input_game_count'],
             result['skipped_forfeit_count']))
    print('  training:   %d games, %d positions (was %d) -> %s'
          % (result['training_game_count'], result['training_positions'],
             result['original_training_positions'], result['training_path']))
    print('  validation: %d games, %d positions (was %d) -> %s'
          % (result['validation_game_count'], result['validation_positions'],
             result['original_validation_positions'],
             result['validation_path']))
    print('  summary: %s' % result['summary_path'])
    return EXIT_OK


if __name__ == '__main__':
    raise SystemExit(main())
