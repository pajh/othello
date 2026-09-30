"""First CPU trainer for the fixed outcome model.

Bounded by docs/first-trainer-task.md; architecture and settings come from
docs/first-model-design.md, which the user accepted. This module reads the
converter's NPZ splits, trains :class:`training.model.OutcomeMLP` on CPU
and writes checkpoints, a history file and a fixed-name summary. It is
deliberately a single ordinary script, not a framework: no registry, no
resume command, no configuration file, no GPU or parallel data loading.

Command line::

    python -m training.train --dataset-dir PATH --output-dir PATH \\
        [--epochs INT] [--batch-size INT] [--learning-rate FLOAT] \\
        [--seed INT] [--patience INT]

Defaults: 30 epochs, batch 256, learning rate 0.001, seed 12345, patience
3. ``--help`` prints and exits without reading data or creating output.

The dataset directory must contain ``training.npz`` and ``validation.npz``
with exactly the four arrays produced by the converter (encoding version 1,
binary ``uint8`` own/opponent planes, ``int8`` outcomes, fixed-width Unicode
game IDs, ``uint8`` plies). Archives are opened once with
``allow_pickle=False``; rows are never re-split and raw logs are never
reparsed. Targets are ``(outcome + 1) / 2`` in float32, so a loss is 0.0, a
draw 0.5 and a win 1.0.

Method: ``torch.manual_seed(seed)`` before the model is built, mean squared
error loss, ``torch.optim.Adam`` with the configured learning rate and
default settings otherwise, and a reshuffled pass over the training rows
each epoch. After every epoch the whole training and validation sets are
re-scored in ``eval()`` mode under ``no_grad``; those two numbers describe
the same finished-epoch model, and validation gradients are never computed.
The best checkpoint is the completed epoch with the strictly lowest
validation loss; training stops after ``patience`` consecutive epochs
without improvement or at the epoch limit. A non-finite loss is an error and
is never published as a successful epoch.

The output directory must be fresh or empty, so earlier runs are preserved.
Artifacts are ``best.pt``, ``last.pt``, ``training-history.json`` and
``training-summary.txt``; checkpoints are written through a temporary
sibling and ``os.replace``, but the set of files is not published
atomically. Checkpoints carry enough state to resume at an epoch boundary
in a later task; no resume path exists here.

Timings use ``time.perf_counter``. The load time covers dataset reading and
validation only. An epoch's reported time covers shuffling, the update
passes, both evaluations and that epoch's artifact writes. The total covers
the whole run, from before the dataset is read to after the summary is
written. No performance target is claimed.
"""

import argparse
import json
import math
import os
import platform
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import torch

from training.model import MODEL_VERSION, OutcomeMLP

CHECKPOINT_VERSION = 1
ENCODING_VERSION = 1
ARCHITECTURE = (
    'OutcomeMLP: flatten(2*8*8=128) -> Linear(128,256) -> ReLU -> '
    'Linear(256,64) -> ReLU -> Linear(64,1) -> Sigmoid, 49537 parameters'
)
ACTIVATIONS = 'ReLU after each hidden layer, Sigmoid on the output logit'
PERSPECTIVE = (
    'after-action position seen from the acting player; plane 0 own discs, '
    'plane 1 opponent discs, flattened in C order from dimension 1'
)
TARGET_MAPPING = 'float32 (outcome + 1) / 2, so loss 0.0, draw 0.5, win 1.0'

TRAINING_ARCHIVE = 'training.npz'
VALIDATION_ARCHIVE = 'validation.npz'
BEST_NAME = 'best.pt'
LAST_NAME = 'last.pt'
HISTORY_NAME = 'training-history.json'
SUMMARY_NAME = 'training-summary.txt'
ARRAY_NAMES = ('boards', 'outcomes', 'game_ids', 'plies')

EXIT_OK = 0
EXIT_FAILED = 1
EXIT_INTERRUPTED = 130


def _positive_int(text):
    try:
        value = int(text)
    except ValueError:
        raise argparse.ArgumentTypeError('must be an integer') from None
    if value < 1:
        raise argparse.ArgumentTypeError('must be 1 or greater')
    return value


def _nonnegative_int(text):
    try:
        value = int(text)
    except ValueError:
        raise argparse.ArgumentTypeError('must be an integer') from None
    if value < 0:
        raise argparse.ArgumentTypeError('must be 0 or greater')
    return value


def _positive_float(text):
    try:
        value = float(text)
    except ValueError:
        raise argparse.ArgumentTypeError('must be a number') from None
    if not math.isfinite(value) or value <= 0.0:
        raise argparse.ArgumentTypeError('must be finite and greater than 0')
    return value


def _parse_args(argv):
    parser = argparse.ArgumentParser(
        prog='python -m training.train',
        description='Train the fixed outcome MLP on the converted dataset '
                    'splits (CPU only).',
    )
    parser.add_argument('--dataset-dir', required=True, metavar='PATH',
                        help='directory holding training.npz and validation.npz')
    parser.add_argument('--output-dir', required=True, metavar='PATH',
                        help='fresh or empty directory for checkpoints, history '
                             'and summary')
    parser.add_argument('--epochs', type=_positive_int, default=30, metavar='INT',
                        help='maximum epochs (default: 30)')
    parser.add_argument('--batch-size', type=_positive_int, default=256, metavar='INT',
                        help='rows per batch, remainder included (default: 256)')
    parser.add_argument('--learning-rate', type=_positive_float, default=0.001,
                        metavar='FLOAT',
                        help='Adam learning rate (default: 0.001)')
    parser.add_argument('--seed', type=_nonnegative_int, default=12345, metavar='INT',
                        help='torch manual seed (default: 12345)')
    parser.add_argument('--patience', type=_positive_int, default=3, metavar='INT',
                        help='stop after this many epochs without a lower '
                             'validation loss (default: 3)')
    return parser.parse_args(argv)


@dataclass(frozen=True)
class Split:
    """One validated split, already converted to CPU float32 tensors."""

    name: str
    boards: torch.Tensor
    targets: torch.Tensor
    game_ids: tuple
    rows: int
    game_count: int


def _fail(context, message):
    raise ValueError('%s: %s' % (context, message))


def _require(condition, context, message):
    if not condition:
        _fail(context, message)


def load_split(dataset_dir, archive_name):
    """Load and validate one split archive, returning a :class:`Split`."""
    path = Path(dataset_dir) / archive_name
    context = str(path)
    _require(path.is_file(), context, 'dataset split not found')
    try:
        with np.load(path, allow_pickle=False) as archive:
            found = set(archive.files)
            _require(found == set(ARRAY_NAMES), context,
                     'expected exactly the arrays %s, found %s'
                     % (sorted(ARRAY_NAMES), sorted(found)))
            boards = archive['boards']
            outcomes = archive['outcomes']
            game_ids = archive['game_ids']
            plies = archive['plies']
    except ValueError as exc:
        # NumPy raises its own ValueError for arrays it cannot read, such as
        # an object dtype that allow_pickle=False refuses. Keep this module's
        # context convention instead of leaking a bare library message.
        if str(exc).startswith(context + ':'):
            raise
        _fail(context, str(exc))
    except OSError as exc:
        _fail(context, 'cannot read archive: %s' % exc)

    _require(boards.dtype == np.uint8, context,
             'boards must be uint8, got %s' % boards.dtype)
    _require(boards.ndim == 4 and tuple(boards.shape[1:]) == (2, 8, 8), context,
             'boards must have shape (N, 2, 8, 8), got %s' % (tuple(boards.shape),))
    _require(outcomes.dtype == np.int8, context,
             'outcomes must be int8, got %s' % outcomes.dtype)
    _require(outcomes.ndim == 1, context,
             'outcomes must have shape (N,), got %s' % (tuple(outcomes.shape),))
    _require(plies.dtype == np.uint8, context,
             'plies must be uint8, got %s' % plies.dtype)
    _require(plies.ndim == 1, context,
             'plies must have shape (N,), got %s' % (tuple(plies.shape),))
    _require(game_ids.dtype.kind == 'U', context,
             'game_ids must be fixed-width Unicode, got %s' % game_ids.dtype)

    rows = boards.shape[0]
    _require(rows > 0, context, 'archive holds no rows')
    for name, array in (('outcomes', outcomes), ('game_ids', game_ids), ('plies', plies)):
        _require(array.shape[0] == rows, context,
                 '%s has %d rows but boards has %d' % (name, array.shape[0], rows))
    _require(bool(np.isin(boards, (0, 1)).all()), context,
             'board planes must contain only 0 and 1')
    # Binary planes must also be disjoint: a cell cannot hold both the
    # actor's disc and the opponent's disc.
    overlap = np.argwhere((boards[:, 0] == 1) & (boards[:, 1] == 1))
    if overlap.shape[0]:
        _fail(context, 'own and opponent planes overlap at %d cell(s), first at '
                       'row %d column %d'
             % (overlap.shape[0], overlap[0][0], overlap[0][1]))
    _require(bool(np.isin(outcomes, (-1, 0, 1)).all()), context,
             'outcomes must contain only -1, 0 and 1')
    ids = tuple(str(value) for value in game_ids.tolist())
    _require(all(ids), context, 'game_ids must not contain empty values')

    return Split(
        name=archive_name,
        boards=torch.from_numpy(np.ascontiguousarray(boards)).to(torch.float32),
        targets=(torch.from_numpy(np.ascontiguousarray(outcomes)).to(torch.float32) + 1.0) / 2.0,
        game_ids=ids,
        rows=rows,
        game_count=len(set(ids)),
    )


def load_datasets(dataset_dir):
    """Load both splits and require that their game IDs are disjoint."""
    training = load_split(dataset_dir, TRAINING_ARCHIVE)
    validation = load_split(dataset_dir, VALIDATION_ARCHIVE)
    shared = set(training.game_ids) & set(validation.game_ids)
    _require(not shared, str(dataset_dir),
             'the splits share %d game IDs, for example %s'
             % (len(shared), sorted(shared)[:3]))
    return training, validation


def constant_baseline_loss(training_targets, validation_targets):
    """MSE on validation of the constant predictor equal to the mean training target."""
    mean_target = float(training_targets.mean())
    return float(((validation_targets - mean_target) ** 2).mean())


def evaluate(model, boards, targets, batch_size):
    """Full-set MSE in eval mode under no_grad; sum of squared errors over rows."""
    model.eval()
    total = 0.0
    rows = boards.shape[0]
    with torch.no_grad():
        for start in range(0, rows, batch_size):
            stop = min(start + batch_size, rows)
            difference = model(boards[start:stop]) - targets[start:stop]
            total += float((difference ** 2).sum())
    return total / rows


def _write_atomic(path, write):
    """Write *path* through a temporary sibling, then rename it into place."""
    temporary = path.with_name(path.name + '.tmp')
    try:
        with open(temporary, 'wb') as stream:
            write(stream)
        os.replace(temporary, path)
    except BaseException:
        try:
            temporary.unlink()
        except OSError:
            pass
        raise


def save_checkpoint(path, payload):
    """Serialise *payload* to *path* atomically enough for one file."""
    _write_atomic(path, lambda stream: torch.save(payload, stream))
    return path


def build_checkpoint(*, completed_epoch, best_epoch, best_validation_loss,
                     no_improvement_count, training_loss, validation_loss,
                     model, optimizer, config, paths, counts, load_seconds,
                     total_seconds):
    """Return the checkpoint dictionary for one completed epoch.

    Every value is an ordinary Python object or a tensor, so the file loads
    with ``torch.load(..., map_location='cpu', weights_only=True)``.
    """
    return {
        'checkpoint_version': CHECKPOINT_VERSION,
        'model_version': MODEL_VERSION,
        'encoding_version': ENCODING_VERSION,
        'architecture': ARCHITECTURE,
        'activations': ACTIVATIONS,
        'perspective': PERSPECTIVE,
        'target_mapping': TARGET_MAPPING,
        'model_state_dict': model.state_dict(),
        'optimizer_state_dict': optimizer.state_dict(),
        'torch_rng_state': torch.get_rng_state(),
        'completed_epoch': completed_epoch,
        'best_epoch': best_epoch,
        'best_validation_loss': best_validation_loss,
        'no_improvement_count': no_improvement_count,
        'training_loss': training_loss,
        'validation_loss': validation_loss,
        'config': dict(config),
        'dataset_dir': paths['dataset_dir'],
        'output_dir': paths['output_dir'],
        'source_training_games': counts['training_games'],
        'source_training_rows': counts['training_rows'],
        'source_validation_games': counts['validation_games'],
        'source_validation_rows': counts['validation_rows'],
        # str(), not the raw attribute: torch.__version__ is a TorchVersion
        # object, which torch.load(weights_only=True) refuses to unpickle.
        'torch_version': str(torch.__version__),
        'numpy_version': np.__version__,
        'python_version': platform.python_version(),
        'device': 'cpu',
        'torch_num_threads': torch.get_num_threads(),
        'torch_num_interop_threads': torch.get_num_interop_threads(),
        'elapsed_load_seconds': load_seconds,
        'elapsed_total_seconds': total_seconds,
    }


def _require_finite(value, label, epoch):
    if not math.isfinite(value):
        raise ValueError('%s at epoch %s is %r; the epoch is not published'
                         % (label, epoch, value))


def train_loop(training, validation, config, paths, counts, load_seconds, started):
    """Run the training loop and return the result dictionary for the summary.

    Raises ValueError for a non-finite loss. A KeyboardInterrupt ends the
    loop, leaves the checkpoints already written in place and is reported
    through ``stop_reason``.
    """
    torch.manual_seed(config['seed'])
    model = OutcomeMLP()
    optimizer = torch.optim.Adam(model.parameters(), lr=config['learning_rate'])
    loss_function = torch.nn.MSELoss()
    batch_size = config['batch_size']

    initial_training_loss = evaluate(model, training.boards, training.targets, batch_size)
    initial_validation_loss = evaluate(model, validation.boards, validation.targets, batch_size)
    _require_finite(initial_training_loss, 'initial training loss', 0)
    _require_finite(initial_validation_loss, 'initial validation loss', 0)
    baseline_loss = constant_baseline_loss(training.targets, validation.targets)
    _require_finite(baseline_loss, 'constant baseline validation loss', 0)

    history = {
        'config': dict(config),
        'initial': {
            'training_loss': initial_training_loss,
            'validation_loss': initial_validation_loss,
        },
        'constant_baseline_validation_loss': baseline_loss,
        'epochs': [],
    }
    # paths['output_dir'] is a string (main() keeps it that way for
    # checkpoint metadata), so convert it before joining, as the later
    # writes in this loop already do.
    _write_history(Path(paths['output_dir']) / HISTORY_NAME, history)
    print('epoch 0 (untrained) train_mse=%.6f validation_mse=%.6f '
          'constant_baseline_validation_mse=%.6f'
          % (initial_training_loss, initial_validation_loss, baseline_loss))
    sys.stdout.flush()

    best_epoch = None
    best_validation_loss = None
    training_loss = initial_training_loss
    validation_loss = initial_validation_loss
    no_improvement_count = 0
    stop_reason = 'max_epochs'
    completed_epoch = 0

    try:
        for epoch in range(1, config['epochs'] + 1):
            epoch_started = time.perf_counter()
            model.train()
            order = torch.randperm(training.rows)
            for start in range(0, training.rows, batch_size):
                index = order[start:start + batch_size]
                optimizer.zero_grad()
                loss = loss_function(model(training.boards[index]),
                                     training.targets[index])
                loss.backward()
                optimizer.step()

            training_loss = evaluate(model, training.boards, training.targets, batch_size)
            validation_loss = evaluate(model, validation.boards, validation.targets, batch_size)
            _require_finite(training_loss, 'training loss', epoch)
            _require_finite(validation_loss, 'validation loss', epoch)
            completed_epoch = epoch

            improved = best_epoch is None or validation_loss < best_validation_loss
            if improved:
                best_epoch = epoch
                best_validation_loss = validation_loss
                no_improvement_count = 0
            else:
                no_improvement_count += 1

            payload = build_checkpoint(
                completed_epoch=epoch, best_epoch=best_epoch,
                best_validation_loss=best_validation_loss,
                no_improvement_count=no_improvement_count,
                training_loss=training_loss, validation_loss=validation_loss,
                model=model, optimizer=optimizer, config=config, paths=paths,
                counts=counts, load_seconds=load_seconds,
                total_seconds=time.perf_counter() - started,
            )
            if improved:
                save_checkpoint(Path(paths['output_dir']) / BEST_NAME, payload)
            save_checkpoint(Path(paths['output_dir']) / LAST_NAME, payload)
            history['epochs'].append({
                'epoch': epoch,
                'training_loss': training_loss,
                'validation_loss': validation_loss,
                'no_improvement_count': no_improvement_count,
                'is_best': improved,
                'seconds': time.perf_counter() - epoch_started,
            })
            _write_history(Path(paths['output_dir']) / HISTORY_NAME, history)
            epoch_seconds = history['epochs'][-1]['seconds']

            print('epoch %d/%d train_mse=%.6f validation_mse=%.6f elapsed=%.1fs'
                  % (epoch, config['epochs'], training_loss, validation_loss,
                     epoch_seconds))
            sys.stdout.flush()
            if no_improvement_count >= config['patience']:
                stop_reason = 'patience'
                break
    except KeyboardInterrupt:
        stop_reason = 'interrupted'

    return {
        'initial_training_loss': initial_training_loss,
        'initial_validation_loss': initial_validation_loss,
        'constant_baseline_validation_loss': baseline_loss,
        'training_loss': training_loss,
        'validation_loss': validation_loss,
        'best_epoch': best_epoch,
        'best_validation_loss': best_validation_loss,
        'no_improvement_count': no_improvement_count,
        'completed_epoch': completed_epoch,
        'stop_reason': stop_reason,
    }


def _write_history(path, history):
    """Write training-history.json atomically, keeping per-epoch timings."""
    _write_atomic(path, lambda stream: stream.write(
        json.dumps(history, indent=2).encode('utf-8')))


def summary_text(result, config, paths, counts, load_seconds, total_seconds):
    """Return the fixed-name final summary text."""
    lines = [
        'Othello first training run',
        '=========================',
        '',
        'dataset directory: %s' % paths['dataset_dir'],
        'output directory: %s' % paths['output_dir'],
        '',
        'training rows: %d from %d games' % (counts['training_rows'],
                                             counts['training_games']),
        'validation rows: %d from %d games' % (counts['validation_rows'],
                                               counts['validation_games']),
        '',
        'settings: epochs=%d batch_size=%d learning_rate=%s seed=%d patience=%d'
        % (config['epochs'], config['batch_size'], config['learning_rate'],
           config['seed'], config['patience']),
        'device: cpu, torch threads=%d interop threads=%d'
        % (torch.get_num_threads(), torch.get_num_interop_threads()),
        'versions: torch %s, numpy %s, python %s'
        % (torch.__version__, np.__version__, platform.python_version()),
        'model: %s' % ARCHITECTURE,
        'checkpoint/encoding versions: %d/%d, model version %d'
        % (CHECKPOINT_VERSION, ENCODING_VERSION, MODEL_VERSION),
        'target mapping: %s' % TARGET_MAPPING,
        '',
        'untrained training MSE: %.6f' % result['initial_training_loss'],
        'untrained validation MSE: %.6f' % result['initial_validation_loss'],
        'constant baseline validation MSE: %.6f'
        % result['constant_baseline_validation_loss'],
        '',
        'completed epochs: %d' % result['completed_epoch'],
        'stop reason: %s' % result['stop_reason'],
        'best epoch: %s' % ('none' if result['best_epoch'] is None
                            else result['best_epoch']),
        'best validation MSE: %s'
        % ('none' if result['best_validation_loss'] is None
           else '%.6f' % result['best_validation_loss']),
        'final training MSE: %s' % ('none' if result['completed_epoch'] == 0
                                     else '%.6f' % result['training_loss']),
        'final validation MSE: %s' % ('none' if result['completed_epoch'] == 0
                                       else '%.6f' % result['validation_loss']),
        'epochs without improvement at stop: %d' % result['no_improvement_count'],
        '',
        'load seconds: %.3f' % load_seconds,
        'total seconds: %.3f' % total_seconds,
        '',
        'artifacts:',
        '  %s' % (Path(paths['output_dir']) / BEST_NAME),
        '  %s' % (Path(paths['output_dir']) / LAST_NAME),
        '  %s' % (Path(paths['output_dir']) / HISTORY_NAME),
        '  %s' % (Path(paths['output_dir']) / SUMMARY_NAME),
    ]
    return '\n'.join(lines) + '\n'


def _require_empty_output_dir(output_dir):
    context = str(output_dir)
    if output_dir.exists():
        _require(output_dir.is_dir(), context, 'output path exists and is not a directory')
        _require(not any(output_dir.iterdir()), context,
                 'output directory is not empty; choose a fresh directory so '
                 'earlier runs are preserved')


def main(argv=None):
    """Entry point for ``python -m training.train``; returns the exit status."""
    args = _parse_args(argv)
    config = {
        'epochs': args.epochs,
        'batch_size': args.batch_size,
        'learning_rate': args.learning_rate,
        'seed': args.seed,
        'patience': args.patience,
    }
    dataset_dir = Path(args.dataset_dir).resolve()
    output_dir = Path(args.output_dir).resolve()
    started = time.perf_counter()
    try:
        _require_empty_output_dir(output_dir)
        output_dir.mkdir(parents=True)
        training, validation = load_datasets(dataset_dir)
    except (ValueError, OSError) as exc:
        print('training failed before starting: %s' % exc, file=sys.stderr)
        return EXIT_FAILED
    load_seconds = time.perf_counter() - started

    paths = {'dataset_dir': str(dataset_dir), 'output_dir': str(output_dir)}
    counts = {
        'training_games': training.game_count,
        'training_rows': training.rows,
        'validation_games': validation.game_count,
        'validation_rows': validation.rows,
    }
    print('dataset %s: training %d rows/%d games, validation %d rows/%d games'
          % (dataset_dir, training.rows, training.game_count,
             validation.rows, validation.game_count))
    print('device cpu, torch threads=%d interop threads=%d'
          % (torch.get_num_threads(), torch.get_num_interop_threads()))

    try:
        result = train_loop(training, validation, config, paths, counts,
                            load_seconds, started)
    except (ValueError, RuntimeError, OSError) as exc:
        print('training failed: %s' % exc, file=sys.stderr)
        return EXIT_FAILED
    except KeyboardInterrupt:
        print('training interrupted before any epoch completed', file=sys.stderr)
        return EXIT_INTERRUPTED

    total_seconds = time.perf_counter() - started
    try:
        _write_atomic(output_dir / SUMMARY_NAME, lambda stream: stream.write(
            summary_text(result, config, paths, counts, load_seconds,
                         total_seconds).encode('utf-8')))
    except OSError as exc:
        print('training finished but the summary could not be written: %s' % exc,
              file=sys.stderr)
        return EXIT_FAILED

    print('best epoch: %s (validation MSE %s)'
          % (result['best_epoch'],
             'none' if result['best_validation_loss'] is None
             else '%.6f' % result['best_validation_loss']))
    print('stop reason: %s after %d completed epoch(s), total %.1fs'
          % (result['stop_reason'], result['completed_epoch'], total_seconds))
    print('artifacts in %s: %s, %s, %s, %s'
          % (output_dir, BEST_NAME, LAST_NAME, HISTORY_NAME, SUMMARY_NAME))
    if result['stop_reason'] == 'interrupted':
        print('interrupted summary: %s' % (output_dir / SUMMARY_NAME),
              file=sys.stderr)
        return EXIT_INTERRUPTED
    return EXIT_OK


if __name__ == '__main__':
    raise SystemExit(main())
