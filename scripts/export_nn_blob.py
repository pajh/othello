#!/usr/bin/env python3
"""Export one selected checkpoint's parameters as a raw float32 blob.

Writes ``model.bin``: a headerless, contiguous, little-endian IEEE754 float32
array in exactly the layout ``c/nn.h`` addresses, plus ``blob-layout.txt``
describing it.

Command line::

    venv/bin/python scripts/export_nn_blob.py --checkpoint PATH --output-dir DIR

Both arguments are required. The checkpoint is selected explicitly: nothing
here picks the newest run, scans a directory or falls back to another model.

Layout
------
The six tensors are written in a fixed order, each flattened in C (row-major)
order so a weight matrix becomes one row per output neuron, matching PyTorch's
``nn.Linear`` storage and ``c/nn.h``'s dot-product loop:

===============  ==========  =======  =============  ==========
key              shape       elements  element offset  byte offset
===============  ==========  =======  =============  ==========
network.0.weight (256, 128)      32768              0          0
network.0.bias   (256,)            256          32768     131072
network.2.weight  (64, 256)      16384          33024     132096
network.2.bias    (64,)             64          49408     197632
network.4.weight  (1, 64)           64          49472     197888
network.4.bias    (1,)               1          49536     198144
===============  ==========  =======  =============  ==========

Total: 49,537 elements, 198,148 bytes.

Nothing else is written: no header, no padding, no pointers, no metadata, no
optimizer state, no RNG state and no training information. Dtype ``'<f4'`` is
little-endian float32 regardless of the host's native byte order.

This is a byte-layout export only. It does not check values, compare against
anything or measure size against a platform limit; those are separate stages.
"""

import argparse
import sys
from pathlib import Path

import numpy as np
import torch

#: Key, expected shape, element count and element offset, in export order.
TENSOR_LAYOUT = (
    ('network.0.weight', (256, 128), 32768, 0),
    ('network.0.bias', (256,), 256, 32768),
    ('network.2.weight', (64, 256), 16384, 33024),
    ('network.2.bias', (64,), 64, 49408),
    ('network.4.weight', (1, 64), 64, 49472),
    ('network.4.bias', (1,), 1, 49536),
)

TOTAL_ELEMENTS = 49537
BYTES_PER_ELEMENT = 4
TOTAL_BYTES = TOTAL_ELEMENTS * BYTES_PER_ELEMENT

DTYPE = np.dtype('<f4')
ARCHITECTURE = '128 -> 256 -> 64 -> 1'
ACTIVATIONS = 'ReLU, ReLU, sigmoid'

BINARY_NAME = 'model.bin'
LAYOUT_NAME = 'blob-layout.txt'


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        prog='python scripts/export_nn_blob.py',
        description='Export one selected checkpoint as a raw float32 blob for '
                    'the C model, plus a layout description.',
    )
    parser.add_argument('--checkpoint', required=True, type=Path, metavar='PATH',
                        help='checkpoint to export; selected explicitly')
    parser.add_argument('--output-dir', required=True, type=Path, metavar='DIR',
                        help='directory receiving model.bin and blob-layout.txt')
    return parser.parse_args(argv)


def load_state(checkpoint_path):
    """Return the checkpoint's model_state_dict, or fail with a clear message."""
    resolved = checkpoint_path.expanduser().resolve()
    if not resolved.is_file():
        raise ValueError('checkpoint does not exist: %s' % resolved)
    checkpoint = torch.load(resolved, map_location='cpu', weights_only=True)
    if not isinstance(checkpoint, dict):
        raise ValueError('%s is not a checkpoint dictionary (got %s)'
                         % (resolved, type(checkpoint).__name__))
    state = checkpoint.get('model_state_dict')
    if state is None:
        raise ValueError('%s has no model_state_dict' % resolved)
    return resolved, state


def flatten_tensor(state, key, shape):
    """Return *key* as a flat little-endian float32 array in C order."""
    if key not in state:
        raise ValueError('model_state_dict is missing %s' % key)
    tensor = state[key]
    if tuple(tensor.shape) != shape:
        raise ValueError('%s has shape %s, expected %s'
                         % (key, tuple(tensor.shape), shape))
    # detach().cpu() makes the export independent of any autograd graph or
    # device the checkpoint happened to carry; .numpy() shares memory, so the
    # contiguous copy below is required before writing.
    array = tensor.detach().cpu().numpy()
    return np.ascontiguousarray(array, dtype=DTYPE).reshape(-1)


def export(checkpoint_path, output_dir):
    """Write model.bin and blob-layout.txt; return a small result dict."""
    resolved, state = load_state(checkpoint_path)

    parts = []
    for key, shape, _elements, _offset in TENSOR_LAYOUT:
        parts.append(flatten_tensor(state, key, shape))
    blob = np.concatenate(parts)

    if blob.size != TOTAL_ELEMENTS:
        raise ValueError('assembled blob has %d elements, expected %d'
                         % (blob.size, TOTAL_ELEMENTS))

    output_dir = output_dir.expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    binary_path = output_dir / BINARY_NAME
    # tofile writes the array's own bytes with no header or padding.
    blob.tofile(str(binary_path))

    written = binary_path.stat().st_size
    if written != TOTAL_BYTES:
        raise ValueError('%s is %d bytes, expected %d'
                         % (binary_path, written, TOTAL_BYTES))

    lines = [
        'Othello C model blob export',
        '============================',
        '',
        'source checkpoint: %s' % resolved,
        'architecture: %s' % ARCHITECTURE,
        'activations: %s' % ACTIVATIONS,
        'weight layout: C row-major, one row per output neuron',
        'dtype: float32 little-endian IEEE754 binary32 (numpy <f4)',
        'binary file: %s' % binary_path,
        'header/padding/metadata: none',
        'optimizer, RNG and training state: not exported',
        '',
        'total elements: %d' % TOTAL_ELEMENTS,
        'total bytes: %d' % TOTAL_BYTES,
        '',
        'key | shape | elements | element offset | byte offset',
    ]
    for key, shape, elements, offset in TENSOR_LAYOUT:
        lines.append('%s | %s | %d | %d | %d'
                     % (key, 'x'.join(str(size) for size in shape),
                        elements, offset, offset * BYTES_PER_ELEMENT))
    lines += [
        '',
        'The offsets are the ones c/nn.h uses:',
        'layer 0 weights 0 bias 32768, layer 1 weights 33024 bias 49408,',
        'layer 2 weights 49472 bias 49536.',
    ]
    layout_path = output_dir / LAYOUT_NAME
    layout_path.write_text('\n'.join(lines) + '\n', encoding='utf-8')

    return {
        'checkpoint': resolved,
        'binary_path': binary_path,
        'layout_path': layout_path,
        'elements': int(blob.size),
        'bytes': written,
    }


def main(argv=None):
    args = parse_args(argv)
    try:
        result = export(args.checkpoint, args.output_dir)
    except (ValueError, OSError) as exc:
        print('export failed: %s' % exc, file=sys.stderr)
        return 1
    print('exported %s' % result['checkpoint'])
    print('  %s: %d elements, %d bytes'
          % (result['binary_path'], result['elements'], result['bytes']))
    print('  %s' % result['layout_path'])
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
