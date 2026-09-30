#!/usr/bin/env python3
"""User-run wrapper for the first retained-dataset training run."""

import json
import math
import os
import re
import subprocess
import sys
import tempfile
import time
import uuid
from pathlib import Path

import torch


ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / 'runs/run-197b46d72b9447ebb2e315321400b3e8/dataset'
RUNS = ROOT / 'checkpoints/first-model'
TRAIN_CHECK = RUNS / 'training-check.txt'
EXPECTED = {
    'source_training_games': 800,
    'source_training_rows': 48321,
    'source_validation_games': 200,
    'source_validation_rows': 12090,
}
STATE_SHAPES = {
    'network.0.weight': (256, 128), 'network.0.bias': (256,),
    'network.2.weight': (64, 256), 'network.2.bias': (64,),
    'network.4.weight': (1, 64), 'network.4.bias': (1,),
}


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def field(text, name):
    match = re.search(r'^%s: (.+)$' % re.escape(name), text, re.MULTILINE)
    require(match is not None, 'summary is missing %s' % name)
    return match.group(1)


def verify_run(output):
    names = ('best.pt', 'last.pt', 'training-history.json', 'training-summary.txt')
    paths = {name: output / name for name in names}
    for name, path in paths.items():
        require(path.is_file() and path.stat().st_size > 0,
                'missing or empty artifact: %s' % path)

    checkpoints = {
        name: torch.load(paths[name], map_location='cpu', weights_only=True)
        for name in ('best.pt', 'last.pt')
    }
    for name, checkpoint in checkpoints.items():
        for key, expected in EXPECTED.items():
            require(checkpoint.get(key) == expected,
                    '%s has wrong %s' % (name, key))
        require((checkpoint.get('checkpoint_version'), checkpoint.get('model_version'),
                 checkpoint.get('encoding_version')) == (1, 1, 1),
                '%s has incompatible checkpoint/model/encoding versions' % name)
        state = checkpoint.get('model_state_dict', {})
        require(set(state) == set(STATE_SHAPES), '%s has an unexpected model state' % name)
        for key, shape in STATE_SHAPES.items():
            value = state[key]
            require(tuple(value.shape) == shape and bool(torch.isfinite(value).all()),
                    '%s parameter %s has wrong shape or nonfinite values' % (name, key))

    history = json.loads(paths['training-history.json'].read_text(encoding='utf-8'))
    epochs = history.get('epochs')
    require(isinstance(epochs, list) and epochs, 'training history has no completed epochs')
    require(history.get('config') == checkpoints['last.pt'].get('config'),
            'history and checkpoint config differ')
    require(history['config'] == {
        'epochs': 30, 'batch_size': 256, 'learning_rate': 0.001,
        'seed': 12345, 'patience': 3,
    }, 'training did not use the agreed starting defaults')
    best_entry = min(epochs, key=lambda row: row['validation_loss'])
    last_entry = epochs[-1]
    best = checkpoints['best.pt']
    last = checkpoints['last.pt']
    require(best['completed_epoch'] == best_entry['epoch'] == best['best_epoch'],
            'best checkpoint epoch disagrees with history')
    require(last['completed_epoch'] == last_entry['epoch'],
            'last checkpoint epoch disagrees with history')
    require(last['best_epoch'] == best_entry['epoch'],
            'last checkpoint best epoch disagrees with history')
    require(math.isclose(best['validation_loss'], best_entry['validation_loss'],
                         rel_tol=1e-9, abs_tol=1e-12)
            and math.isclose(last['validation_loss'], last_entry['validation_loss'],
                             rel_tol=1e-9, abs_tol=1e-12),
            'checkpoint validation losses disagree with history')
    require(math.isclose(last['best_validation_loss'], best['best_validation_loss'],
                         rel_tol=1e-9, abs_tol=1e-12),
            'best/last checkpoints disagree on best validation loss')
    require(math.isclose(best['best_validation_loss'], best_entry['validation_loss'],
                         rel_tol=1e-9, abs_tol=1e-12)
            and best_entry.get('is_best') is True,
            'best checkpoint metadata disagrees with history')
    summary = paths['training-summary.txt'].read_text(encoding='utf-8')
    require(field(summary, 'best epoch') == str(best_entry['epoch']),
            'summary best epoch disagrees with history')
    require(field(summary, 'completed epochs') == str(last_entry['epoch']),
            'summary completed epoch count disagrees with history')
    require(field(summary, 'stop reason') in ('patience', 'max_epochs'),
            'summary does not describe a completed training run')
    require(field(summary, 'best validation MSE') == '%.6f' % best_entry['validation_loss'],
            'summary best validation MSE disagrees with history')
    return last_entry['epoch'], best_entry['epoch']


def write_check(text):
    RUNS.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile('w', encoding='utf-8', dir=RUNS,
                                         prefix='.training-check-', delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(text)
        os.replace(temporary, TRAIN_CHECK)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def main():
    RUNS.mkdir(parents=True, exist_ok=True)
    output = (RUNS / ('run-' + uuid.uuid4().hex)).resolve()
    print('Training output: %s' % output, flush=True)
    command = [sys.executable, '-m', 'training.train',
               '--dataset-dir', str(DATASET), '--output-dir', str(output)]
    started = time.perf_counter()
    interrupted = False
    try:
        process = subprocess.Popen(command, cwd=ROOT)
        try:
            exit_code = process.wait()
        except KeyboardInterrupt:
            interrupted = True
            exit_code = process.wait()
            if exit_code == 0:
                exit_code = 130
    except OSError as exc:
        exit_code = 1
        failure = 'could not start trainer: %s' % exc
    elapsed = time.perf_counter() - started
    if exit_code == 0:
        try:
            last_epoch, best_epoch = verify_run(output)
            note = ('PASS: epochs=%d best_epoch=%d elapsed=%.1fs output=%s\n'
                    % (last_epoch, best_epoch, elapsed, output))
        except (OSError, RuntimeError, ValueError, KeyError) as exc:
            exit_code = 1
            note = 'CHECK FAILED: %s elapsed=%.1fs output=%s\n' % (exc, elapsed, output)
    elif 'failure' in locals():
        note = 'FAILED: %s elapsed=%.1fs output=%s\n' % (failure, elapsed, output)
    else:
        note = '%s: trainer exit %d elapsed=%.1fs output=%s\n' % (
            'INTERRUPTED' if interrupted or exit_code == 130 else 'FAILED',
            exit_code, elapsed, output)
    try:
        write_check(note)
    except OSError as exc:
        print('Could not update %s: %s' % (TRAIN_CHECK, exc), file=sys.stderr)
    print(note, end='', flush=True)
    return exit_code


if __name__ == '__main__':
    raise SystemExit(main())
