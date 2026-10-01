#!/usr/bin/env python3
"""Quantize a raw float32 parameter blob with one shared 256-value codebook.

Writes a small codebook plus one byte per parameter, and also writes the
reconstructed raw blob so the existing C comparison rig can score the quantized
weights before any C decoder exists.

Command line::

    venv/bin/python scripts/quantize_nn_blob.py --input PATH --output-dir DIR \\
        [--seed INT]

Input is the raw little-endian float32 blob produced by
``scripts/export_nn_blob.py``: 49,537 values, 198,148 bytes, no header.

Method
------
All weights **and** biases share ONE codebook of 256 float32 values, fitted
with ``sklearn.cluster.KMeans(n_clusters=256, random_state=seed, n_init=1,
max_iter=300, algorithm='lloyd')`` on the values reshaped to ``(N, 1)``. No
per-layer tables, no alternative methods, no tuning.

Every original value is then assigned to its nearest **stored** float32 center,
not to the pre-cast float64 center KMeans computed: the centers are cast to
float32 first, so the indices must be chosen against exactly the bytes that
``codebook.bin`` contains. KMeans' own labels are used only where they agree
with that nearest-center assignment, which this script verifies rather than
assumes; where they disagree the batched nearest assignment decides.

Outputs, all in ``--output-dir`` under fixed names:

- ``codebook.bin`` — 256 little-endian float32 centers, 1,024 bytes.
- ``indices.bin`` — 49,537 uint8 nearest-center indices in original parameter
  order, 49,537 bytes.
- ``model.bin`` — ``codebook[indices]`` expanded back to raw little-endian
  float32, 198,148 bytes. Temporary: it exists so the existing C rig can score
  quantized weights without a C decoder.
- ``quantization-summary.txt`` — source, seed, library versions, method, file
  sizes and the weight-space error.

This is a parameter-quantization size/error measurement only. It does not
claim the quantized model plays the same, and it does not evaluate strength:
the existing FP32 comparison tolerance will likely fail against the quantized
blob, and that is a measurement to read, not a reason to change anything here.
"""

import argparse
import sys
from pathlib import Path

import numpy as np
import sklearn
from sklearn.cluster import KMeans

TOTAL_ELEMENTS = 49537
TOTAL_BYTES = TOTAL_ELEMENTS * 4
CODEBOOK_SIZE = 256
INDEX_BYTES = TOTAL_ELEMENTS
CODEBOOK_BYTES = CODEBOOK_SIZE * 4
PACKED_BYTES = CODEBOOK_BYTES + INDEX_BYTES
# Base64 is 4 characters per 3 bytes, rounded up to a multiple of 4.
BASE64_LENGTH = 4 * -(-PACKED_BYTES // 3)

FLOAT_DTYPE = np.dtype('<f4')

CODEBOOK_NAME = 'codebook.bin'
INDICES_NAME = 'indices.bin'
MODEL_NAME = 'model.bin'
SUMMARY_NAME = 'quantization-summary.txt'

# Batch size for the nearest-center assignment, so the comparison stays small.
ASSIGNMENT_BATCH = 4096


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        prog='python scripts/quantize_nn_blob.py',
        description='Quantize a raw float32 parameter blob with one shared '
                    '256-value codebook.',
    )
    parser.add_argument('--input', required=True, type=Path, metavar='PATH',
                        help='raw float32 blob to quantize')
    parser.add_argument('--output-dir', required=True, type=Path, metavar='DIR',
                        help='directory receiving the four output files')
    parser.add_argument('--seed', type=int, default=12345, metavar='INT',
                        help='KMeans random_state (default: 12345)')
    return parser.parse_args(argv)


def read_blob(path):
    """Return the blob as a float32 array, rejecting any wrong size."""
    resolved = path.expanduser().resolve()
    if not resolved.is_file():
        raise ValueError('input blob does not exist: %s' % resolved)
    size = resolved.stat().st_size
    if size != TOTAL_BYTES:
        raise ValueError('%s is %d bytes, expected %d for %d float32 values'
                         % (resolved, size, TOTAL_BYTES, TOTAL_ELEMENTS))
    values = np.fromfile(str(resolved), dtype=FLOAT_DTYPE)
    if values.size != TOTAL_ELEMENTS:
        raise ValueError('%s yielded %d values, expected %d'
                         % (resolved, values.size, TOTAL_ELEMENTS))
    return resolved, values


def fit_codebook(values, seed):
    """Return the float32 codebook for *values*."""
    samples = np.asarray(values, dtype=np.float32).reshape(-1, 1)
    kmeans = KMeans(n_clusters=CODEBOOK_SIZE, random_state=seed, n_init=1,
                    max_iter=300, algorithm='lloyd')
    kmeans.fit(samples)
    centers = np.ascontiguousarray(kmeans.cluster_centers_.reshape(-1),
                                   dtype=FLOAT_DTYPE)
    if centers.size != CODEBOOK_SIZE:
        raise ValueError('KMeans returned %d centers, expected %d'
                         % (centers.size, CODEBOOK_SIZE))
    return centers, kmeans.labels_


def nearest_center_indices(values, centers):
    """Return, for each value, the index of the nearest stored float32 center.

    Batched so the (batch, 256) difference array stays small. Distances are
    computed in float64 from the float32 center values, which is what makes the
    result independent of how KMeans labelled its own fit.
    """
    centers64 = np.asarray(centers, dtype=np.float64)
    indices = np.empty(values.size, dtype=np.uint8)
    for start in range(0, values.size, ASSIGNMENT_BATCH):
        stop = min(start + ASSIGNMENT_BATCH, values.size)
        block = np.asarray(values[start:stop], dtype=np.float64).reshape(-1, 1)
        distances = np.abs(block - centers64.reshape(1, -1))
        indices[start:stop] = np.argmin(distances, axis=1).astype(np.uint8)
    return indices


def write_files(output_dir, values, centers, indices):
    """Write the four outputs and return their paths."""
    output_dir = output_dir.expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    reconstructed = np.asarray(centers, dtype=FLOAT_DTYPE)[indices.astype(
        np.int64)]

    codebook_path = output_dir / CODEBOOK_NAME
    indices_path = output_dir / INDICES_NAME
    model_path = output_dir / MODEL_NAME
    centers.tofile(str(codebook_path))
    indices.tofile(str(indices_path))
    np.ascontiguousarray(reconstructed, dtype=FLOAT_DTYPE).tofile(str(model_path))

    for path, expected in ((codebook_path, CODEBOOK_BYTES),
                           (indices_path, INDEX_BYTES),
                           (model_path, TOTAL_BYTES)):
        actual = path.stat().st_size
        if actual != expected:
            raise ValueError('%s is %d bytes, expected %d'
                             % (path, actual, expected))
    return codebook_path, indices_path, model_path, reconstructed


def quantize(input_path, output_dir, seed):
    """Quantize the blob and write all four outputs; return a result dict."""
    resolved, values = read_blob(input_path)
    centers, kmeans_labels = fit_codebook(values, seed)
    indices = nearest_center_indices(values, centers)

    # KMeans labels are only trusted where they agree with the nearest stored
    # center. Disagreement means the float32 cast changed the winner, so the
    # nearest-center assignment is authoritative for those values.
    mismatches = int(np.count_nonzero(
        kmeans_labels.astype(np.int64) != indices.astype(np.int64)))

    codebook_path, indices_path, model_path, reconstructed = write_files(
        output_dir, values, centers, indices)

    error = np.abs(reconstructed.astype(np.float64) - values.astype(np.float64))
    lines = [
        'Othello shared-codebook quantization (256 values)',
        '===============================================',
        '',
        'source blob: %s' % resolved,
        'source elements: %d (%d bytes)' % (TOTAL_ELEMENTS, TOTAL_BYTES),
        'seed: %d' % seed,
        'numpy version: %s' % np.__version__,
        'scikit-learn version: %s' % sklearn.__version__,
        'method: one shared float32 codebook for all weights and biases',
        'kmeans: n_clusters=256 random_state=%d n_init=1 max_iter=300 '
        'algorithm=lloyd' % seed,
        'assignment: nearest stored float32 center, batched',
        'kmeans label disagreements after the float32 cast: %d' % mismatches,
        '',
        'codebook.bin: %d bytes (%d centers, float32 little-endian)'
        % (codebook_path.stat().st_size, CODEBOOK_SIZE),
        'indices.bin: %d bytes (%d uint8, original parameter order)'
        % (indices_path.stat().st_size, INDEX_BYTES),
        'model.bin: %d bytes (codebook expanded by the indices)'
        % model_path.stat().st_size,
        '',
        'packed size: %d bytes' % PACKED_BYTES,
        'base64 length before any header or compression: %d characters'
        % BASE64_LENGTH,
        '',
        'weight mean absolute error: %.9g' % float(error.mean()),
        'weight max absolute error: %.9g' % float(error.max()),
        'weight mean squared error: %.9g' % float((error ** 2).mean()),
        '',
        'model.bin is a temporary reconstruction so the existing C comparison',
        'rig can score quantized weights before a C decoder exists. It is not',
        'a promoted model and says nothing about playing strength.',
    ]
    summary_path = output_dir / SUMMARY_NAME
    summary_path.write_text('\n'.join(lines) + '\n', encoding='utf-8')

    return {
        'source': resolved,
        'codebook_path': codebook_path,
        'indices_path': indices_path,
        'model_path': model_path,
        'summary_path': summary_path,
        'mismatches': mismatches,
        'mean_absolute_error': float(error.mean()),
        'max_absolute_error': float(error.max()),
        'mean_squared_error': float((error ** 2).mean()),
    }


def main(argv=None):
    args = parse_args(argv)
    try:
        result = quantize(args.input, args.output_dir, args.seed)
    except (ValueError, OSError) as exc:
        print('quantization failed: %s' % exc, file=sys.stderr)
        return 1
    print('quantized %s (seed %d)' % (result['source'], args.seed))
    print('  %s: %d bytes' % (result['codebook_path'], CODEBOOK_BYTES))
    print('  %s: %d bytes' % (result['indices_path'], INDEX_BYTES))
    print('  %s: %d bytes' % (result['model_path'], TOTAL_BYTES))
    print('  %s' % result['summary_path'])
    print('  weight mean/max absolute error: %.9g / %.9g'
          % (result['mean_absolute_error'], result['max_absolute_error']))
    print('  kmeans label disagreements: %d' % result['mismatches'])
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
