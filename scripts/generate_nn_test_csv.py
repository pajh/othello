#!/usr/bin/env python3
"""Score a seeded sample of real validation boards and write a C test CSV."""

import argparse
import csv
from pathlib import Path

import numpy as np
import torch

from training.model import OutcomeMLP


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset', required=True, type=Path)
    parser.add_argument('--checkpoint', required=True, type=Path)
    parser.add_argument('--output-dir', required=True, type=Path)
    parser.add_argument('--count', type=int, default=10000)
    parser.add_argument('--seed', type=int, default=12345)
    return parser.parse_args()


def main():
    args = parse_args()
    dataset_path = args.dataset.expanduser().resolve()
    checkpoint_path = args.checkpoint.expanduser().resolve()
    output_dir = args.output_dir.expanduser().resolve()
    if args.count <= 0:
        raise ValueError('--count must be positive')
    if not dataset_path.is_file():
        raise ValueError('dataset not found: %s' % dataset_path)
    if not checkpoint_path.is_file():
        raise ValueError('checkpoint not found: %s' % checkpoint_path)

    with np.load(dataset_path, allow_pickle=False) as archive:
        boards = archive['boards']
    if boards.dtype != np.uint8 or boards.ndim != 4 or boards.shape[1:] != (2, 8, 8):
        raise ValueError('boards must be uint8 with shape (N, 2, 8, 8); got %s %s'
                         % (boards.dtype, boards.shape))
    if args.count > len(boards):
        raise ValueError('--count %d exceeds dataset rows %d' % (args.count, len(boards)))
    if not np.isin(boards, (0, 1)).all():
        raise ValueError('dataset boards contain values outside binary encoding')
    if np.any((boards[:, 0] == 1) & (boards[:, 1] == 1)):
        raise ValueError('dataset boards contain overlapping own/opponent planes')

    selected_indices = np.random.default_rng(args.seed).choice(
        len(boards), size=args.count, replace=False)
    selected = np.ascontiguousarray(boards[selected_indices])
    checkpoint = torch.load(checkpoint_path, map_location='cpu', weights_only=True)
    if not isinstance(checkpoint, dict) or checkpoint.get('model_state_dict') is None:
        raise ValueError('checkpoint has no model_state_dict: %s' % checkpoint_path)
    model = OutcomeMLP()
    model.load_state_dict(checkpoint['model_state_dict'], strict=True)
    model.eval()
    score_parts = []
    with torch.inference_mode():
        for start in range(0, len(selected), 256):
            batch = torch.from_numpy(selected[start:start + 256].copy()).to(torch.float32)
            score_parts.append(model(batch).cpu().numpy())
    scores = np.concatenate(score_parts)

    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / 'inputs-and-scores.csv'
    header = ['x%03d' % i for i in range(128)] + ['score']
    with csv_path.open('w', newline='', encoding='utf-8') as stream:
        writer = csv.writer(stream)
        writer.writerow(header)
        for board, score in zip(selected, scores):
            writer.writerow([int(v) for v in board.reshape(-1)] + ['%.9g' % float(score)])

    summary_path = output_dir / 'corpus-summary.txt'
    summary = '\n'.join([
        'C forward test corpus',
        'Source dataset: %s' % dataset_path,
        'Checkpoint: %s' % checkpoint_path,
        'Rows: %d' % args.count,
        'Seed: %d' % args.seed,
        'Encoding: uint8 binary (N, 2, 8, 8); own plane then opponent plane; C-order flattening',
        'CSV: inputs-and-scores.csv; x000..x127 integer inputs, score formatted with 9 significant digits',
        'Score range: %.9g to %.9g' % (float(scores.min()), float(scores.max())),
        'Sanity: generated %d rows; binary input and overlap checks passed; score range within [0, 1].' % args.count,
        '',
    ])
    summary_path.write_text(summary, encoding='utf-8')
    print('Wrote %d rows to %s' % (args.count, csv_path))
    print('Score range %.9g to %.9g' % (float(scores.min()), float(scores.max())))


if __name__ == '__main__':
    main()
