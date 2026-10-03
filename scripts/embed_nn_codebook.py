#!/usr/bin/env python3
"""Embed a quantized codebook and index blob into a C header as Z85 text.

Command line::

    venv/bin/python scripts/embed_nn_codebook.py --codebook PATH \\
        --indices PATH --output-dir DIR

Inputs are the two quantized files from ``scripts/quantize_nn_blob.py``:

- ``codebook.bin`` — 256 little-endian float32 centers, 1,024 bytes;
- ``indices.bin`` — 49,537 uint8 nearest-center indices in original parameter
  order.

The true payload is exactly those bytes concatenated: codebook first, then
indices, no header and no padding, 50,561 bytes. Z85 encodes four binary bytes
as five ASCII characters with the exact zeroMQ Z85 alphabet, so the true payload
is first padded with **three zero bytes** to 50,564 (divisible by 4). Z85 is an
**encoding only**: there is no compression of any kind here and no
decompression stage. It is chosen over Base64 because it is denser (five ASCII
characters per four bytes instead of four per three) while still surviving being
pasted into a C string literal as plain ASCII.

Outputs under ``--output-dir``:

- ``model.h`` — a guarded C header with the lengths, two CRC32 checksums and the
  payload as adjacent quoted 120-character chunks in a ``static const char``
  array. The character count excludes the terminating NUL. Both the true payload
  size and the padded size are recorded: the decoder ignores only the known
  three zero padding bytes, after checking they are zero.
- ``embedding-summary.txt`` — source paths, sizes, lengths and both checksums.

Trigraph safety: the Z85 alphabet contains ``?``, and a ``??`` pair followed by
one of ``=/'()!<>-`` inside a C string literal would be translated by C11 into a
single byte. ``quoted_chunks`` therefore breaks the literal between the two
``?`` characters wherever that would happen (trigraph translation precedes
string-literal concatenation), so the decoded bytes are unchanged.

The decoded checksum is the canonical reconstruction: the stored codebook read
as 256 little-endian float32 values, the indices expanded in original order,
written back as little-endian float32 bytes. That is what makes the embedded
payload verifiable against the existing reconstructed ``model.bin`` without
changing any float, center or label. CRC32 is the standard unsigned 32-bit
``zlib.crc32`` over the true payload bytes (padding excluded) and, separately,
over the reconstructed float bytes.

The whole generated header must fit 75,000 characters, which the script checks
and enforces.
"""

import argparse
import sys
import zlib
from pathlib import Path

import numpy as np

CODEBOOK_VALUES = 256
CODEBOOK_BYTES = CODEBOOK_VALUES * 4
PARAMETER_COUNT = 49537
INDEX_BYTES = PARAMETER_COUNT
PAYLOAD_BYTES = CODEBOOK_BYTES + INDEX_BYTES       # true payload: 50561
PADDING_BYTES = 3
PADDED_BYTES = PAYLOAD_BYTES + PADDING_BYTES       # 50564, divisible by 4
ENCODED_LENGTH = PADDED_BYTES // 4 * 5             # 63205
DECODED_BYTES = PARAMETER_COUNT * 4
CHUNK_CHARS = 120
HEADER_CHAR_LIMIT = 75000

# The exact standard Z85 alphabet (zeroMQ RFC 32).
Z85_ALPHABET = (
    '0123456789'
    'abcdefghijklmnopqrstuvwxyz'
    'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    '.-:+=^!/*?&<>()[]{}@%$#'
)
if len(Z85_ALPHABET) != 85:
    raise SystemExit('Z85 alphabet must hold exactly 85 characters')

FLOAT_DTYPE = np.dtype('<f4')

HEADER_NAME = 'model.h'
SUMMARY_NAME = 'embedding-summary.txt'


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        prog='python scripts/embed_nn_codebook.py',
        description='Embed a codebook and index blob into a C header as Z85 '
                    'text, with CRC32 checksums. No compression.',
    )
    parser.add_argument('--codebook', required=True, type=Path, metavar='PATH',
                        help='codebook.bin: 256 little-endian float32 centers')
    parser.add_argument('--indices', required=True, type=Path, metavar='PATH',
                        help='indices.bin: 49537 uint8 indices, original order')
    parser.add_argument('--output-dir', required=True, type=Path, metavar='DIR',
                        help='directory receiving model.h and the summary')
    return parser.parse_args(argv)


def read_exact(path, expected_bytes, what):
    """Return the file's bytes, rejecting any other size."""
    resolved = path.expanduser().resolve()
    if not resolved.is_file():
        raise ValueError('%s does not exist: %s' % (what, resolved))
    data = resolved.read_bytes()
    if len(data) != expected_bytes:
        raise ValueError('%s is %s with %d bytes, expected %d'
                         % (what, resolved, len(data), expected_bytes))
    return resolved, data


def reconstruct_fp32_bytes(codebook_bytes, index_bytes):
    """Return the canonical expanded little-endian float32 bytes."""
    centers = np.frombuffer(codebook_bytes, dtype=FLOAT_DTYPE)
    if centers.size != CODEBOOK_VALUES:
        raise ValueError('codebook holds %d float32 values, expected %d'
                         % (centers.size, CODEBOOK_VALUES))
    indices = np.frombuffer(index_bytes, dtype=np.uint8)
    if indices.size != PARAMETER_COUNT:
        raise ValueError('indices hold %d values, expected %d'
                         % (indices.size, PARAMETER_COUNT))
    expanded = np.asarray(centers, dtype=FLOAT_DTYPE)[indices.astype(np.int64)]
    return np.ascontiguousarray(expanded, dtype=FLOAT_DTYPE).tobytes()


def z85_encode(data):
    """Return *data* (a multiple of 4 bytes) as Z85 text.

    Four big-endian grouped bytes become one 32-bit value written as five
    base-85 characters, most significant first, exactly as RFC 32 requires.
    """
    if len(data) % 4 != 0:
        raise ValueError('Z85 needs a length divisible by 4, got %d' % len(data))
    out = []
    for start in range(0, len(data), 4):
        value = ((data[start] << 24) | (data[start + 1] << 16)
                 | (data[start + 2] << 8) | data[start + 3])
        group = []
        for _ in range(5):
            group.append(Z85_ALPHABET[value % 85])
            value //= 85
        out.extend(reversed(group))
    return ''.join(out)


def quoted_chunks(encoded):
    """Return *encoded* as quoted C string chunks of at most 120 characters.

    A trigraph sequence (``??`` followed by one of ``=/'()!<>-``) inside a C
    string literal would be translated before tokenisation in C11, so ``??!``
    would become ``|`` and silently corrupt the payload. Trigraph translation
    (phase 1) happens before adjacent string literals are concatenated
    (phase 6), so any trigraph is broken by ending one literal between the two
    ``?`` characters and starting the next with the third character. The bytes
    are unchanged.
    """
    trigraphs = {c for c in "=/'()!<>-"}
    parts = []
    current = []
    index = 0
    while index < len(encoded):
        character = encoded[index]
        current.append(character)
        if (character == '?' and index + 2 < len(encoded)
                and encoded[index + 1] == '?'
                and encoded[index + 2] in trigraphs):
            # Break the literal after this '?' so the two '?' never meet.
            parts.append(''.join(current))
            current = []
        index += 1
    if current:
        parts.append(''.join(current))

    lines = []
    for part in parts:
        for start in range(0, len(part), CHUNK_CHARS):
            lines.append('    "%s"' % part[start:start + CHUNK_CHARS])
    return lines


def render_header(codebook_path, indices_path, encoded, payload_crc,
                  decoded_crc):
    """Return the complete model.h text."""
    lines = [
        '/* Generated by scripts/embed_nn_codebook.py on 2026-10-02.',
        ' * Do not edit by hand: regenerate from the codebook and indices.',
        ' *',
        ' * Payload layout, concatenated with no header and no padding:',
        ' *   bytes      0 .. 1023  codebook, 256 little-endian IEEE754 binary32',
        ' *                          (float32) centers',
        ' *   bytes   1024 .. 50560  indices, %d uint8 values in original'
        % PARAMETER_COUNT,
        ' *                          parameter order',
        ' *',
        ' * Z85 text below decodes to %d bytes: the %d true payload bytes'
        % (PADDED_BYTES, PAYLOAD_BYTES),
        ' * followed by %d zero padding bytes added only to reach a multiple of 4.'
        % PADDING_BYTES,
        ' * The decoder ignores those known zero bytes after checking they are',
        ' * zero; the payload CRC32 is over the %d true bytes, not the padding.'
        % PAYLOAD_BYTES,
        ' * Interpreting the codebook as %d little-endian float32 values and'
        % CODEBOOK_VALUES,
        ' * expanding each index to that center, in order, yields the canonical',
        ' * reconstruction of %d' % DECODED_BYTES,
        ' * little-endian float32 bytes, whose CRC32 is the decoded checksum.',
        ' *',
        ' * Z85 is an encoding only. Nothing here is compressed.',
        ' *',
        ' * Sources:',
        ' *   codebook: %s' % codebook_path,
        ' *   indices:  %s' % indices_path,
        ' */',
        '',
        '#ifndef MODEL_H',
        '#define MODEL_H',
        '',
        '#include <stdint.h>',
        '',
        '#define MODEL_CODEBOOK_COUNT %du' % CODEBOOK_VALUES,
        '#define MODEL_PARAMETER_COUNT %du' % PARAMETER_COUNT,
        '#define MODEL_PAYLOAD_BYTES %du' % PAYLOAD_BYTES,
        '#define MODEL_PAYLOAD_PADDED_BYTES %du' % PADDED_BYTES,
        '#define MODEL_DECODED_BYTES %du' % DECODED_BYTES,
        '#define MODEL_Z85_LENGTH %du' % ENCODED_LENGTH,
        '',
        '/* CRC32 (IEEE, zlib.crc32) of the %d true payload bytes.' % PAYLOAD_BYTES,
        ' * Checked after Z85 decoding, over the true bytes excluding padding. */',
        '#define MODEL_PAYLOAD_CRC32 UINT32_C(0x%08x)' % payload_crc,
        '',
        '/* CRC32 (IEEE, zlib.crc32) of the %d reconstructed float32 bytes.'
        % DECODED_BYTES,
        ' * Checked after expanding the indices. */',
        '#define MODEL_DECODED_CRC32 UINT32_C(0x%08x)' % decoded_crc,
        '',
        '/* %d Z85 characters, excluding the terminating NUL. */'
        % ENCODED_LENGTH,
        'static const char model_z85[] =',
    ]
    lines += quoted_chunks(encoded)
    lines += [
        '    ;',
        '',
        '#endif /* MODEL_H */',
        '',
    ]
    return '\n'.join(lines)


def embed(codebook_path, indices_path, output_dir):
    """Write model.h and embedding-summary.txt; return a result dict."""
    resolved_codebook, codebook_bytes = read_exact(
        codebook_path, CODEBOOK_BYTES, 'codebook')
    resolved_indices, index_bytes = read_exact(
        indices_path, INDEX_BYTES, 'indices')

    payload = codebook_bytes + index_bytes
    if len(payload) != PAYLOAD_BYTES:
        raise ValueError('payload is %d bytes, expected %d'
                         % (len(payload), PAYLOAD_BYTES))

    decoded_bytes = reconstruct_fp32_bytes(codebook_bytes, index_bytes)
    if len(decoded_bytes) != DECODED_BYTES:
        raise ValueError('reconstruction is %d bytes, expected %d'
                         % (len(decoded_bytes), DECODED_BYTES))

    padded = payload + bytes(PADDING_BYTES)
    if len(padded) != PADDED_BYTES:
        raise ValueError('padded payload is %d bytes, expected %d'
                         % (len(padded), PADDED_BYTES))

    encoded = z85_encode(padded)
    if len(encoded) != ENCODED_LENGTH:
        raise ValueError('Z85 text is %d characters, expected %d'
                         % (len(encoded), ENCODED_LENGTH))

    payload_crc = zlib.crc32(payload) & 0xffffffff
    decoded_crc = zlib.crc32(decoded_bytes) & 0xffffffff

    header_text = render_header(resolved_codebook, resolved_indices, encoded,
                                payload_crc, decoded_crc)
    if len(header_text) > HEADER_CHAR_LIMIT:
        raise ValueError('generated header is %d characters, over the %d limit'
                         % (len(header_text), HEADER_CHAR_LIMIT))

    output_dir = output_dir.expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    header_path = output_dir / HEADER_NAME
    header_path.write_text(header_text, encoding='ascii')

    summary_path = output_dir / SUMMARY_NAME
    summary = [
        'Othello Z85 header embedding',
        '============================',
        '',
        'source codebook: %s (%d bytes)' % (resolved_codebook, CODEBOOK_BYTES),
        'source indices: %s (%d bytes)' % (resolved_indices, INDEX_BYTES),
        'true payload bytes: %d (codebook then indices, no header or padding)'
        % PAYLOAD_BYTES,
        'zero padding bytes: %d' % PADDING_BYTES,
        'padded payload bytes: %d (multiple of 4)' % PADDED_BYTES,
        'z85 characters: %d (excluding the terminating NUL)' % ENCODED_LENGTH,
        'z85 chunk characters: %d, last chunk shorter' % CHUNK_CHARS,
        'reconstructed float32 bytes: %d' % DECODED_BYTES,
        'payload CRC32 (true bytes): 0x%08x' % payload_crc,
        'decoded CRC32: 0x%08x' % decoded_crc,
        'crc32: standard unsigned 32-bit zlib.crc32, no compression applied',
        '',
        'header: %s' % header_path,
        'header characters: %d (limit %d)'
        % (len(header_text), HEADER_CHAR_LIMIT),
        'header bytes on disk: %d' % header_path.stat().st_size,
        'encoding: Z85 only, plain ASCII, no compression',
    ]
    summary_path.write_text('\n'.join(summary) + '\n', encoding='utf-8')

    return {
        'header_path': header_path,
        'summary_path': summary_path,
        'header_characters': len(header_text),
        'header_bytes': header_path.stat().st_size,
        'encoded_length': len(encoded),
        'payload_crc': payload_crc,
        'decoded_crc': decoded_crc,
        'decoded_bytes': decoded_bytes,
        'payload': payload,
        'encoded': encoded,
    }


def main(argv=None):
    args = parse_args(argv)
    try:
        result = embed(args.codebook, args.indices, args.output_dir)
    except (ValueError, OSError) as exc:
        print('embedding failed: %s' % exc, file=sys.stderr)
        return 1
    print('wrote %s' % result['header_path'])
    print('  header characters: %d (limit %d)'
          % (result['header_characters'], HEADER_CHAR_LIMIT))
    print('  z85 characters: %d' % result['encoded_length'])
    print('  payload CRC32: 0x%08x' % result['payload_crc'])
    print('  decoded CRC32: 0x%08x' % result['decoded_crc'])
    print('wrote %s' % result['summary_path'])
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
