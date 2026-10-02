#!/usr/bin/env python3
"""Reduce an opening prefix file to one canonical representative per symmetry.

Reads comma-separated lowercase coordinate histories (a blank line is the empty
history) and writes the canonical form of each distinct history, keeping the
order in which canonical histories are first encountered.  The four transforms
are identity, 180-degree rotation, main-diagonal reflection and anti-diagonal
reflection; these preserve the initial coloured board.  Standard library only.
"""

import argparse
from pathlib import Path

_TRANSFORMS = (
    lambda r, c: (r, c),           # identity
    lambda r, c: (7 - r, 7 - c),   # 180-degree rotation
    lambda r, c: (c, r),           # main-diagonal reflection
    lambda r, c: (7 - c, 7 - r),   # anti-diagonal reflection
)


def coordinate_to_square(token):
    """Parse a lowercase coordinate such as ``f5`` into a 0..63 square."""
    col = ord(token[0]) - ord("a")
    row = int(token[1:]) - 1
    return row * 8 + col


def square_to_coordinate(square):
    """Return a lowercase coordinate such as ``f5`` for a 0..63 square."""
    row, col = divmod(square, 8)
    return "%s%d" % (chr(ord("a") + col), row + 1)


def canonical_history(history):
    """Return the lexicographically smallest transform of *history*.

    *history* is a sequence of square indices with optional ``"pass"`` tokens;
    passes are unchanged by every transform.
    """
    candidates = []
    for transform in _TRANSFORMS:
        moved = []
        for item in history:
            if item == "pass":
                moved.append("pass")
            else:
                row, col = transform(*divmod(item, 8))
                moved.append(row * 8 + col)
        candidates.append(tuple(moved))
    return min(candidates)


def format_history(history):
    return ",".join("pass" if item == "pass" else square_to_coordinate(item)
                    for item in history)


def parse_history(line):
    tokens = [token for token in line.split(",") if token != ""]
    return [token if token == "pass" else coordinate_to_square(token)
            for token in tokens]


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path,
                        help="existing comma-separated prefix file")
    parser.add_argument("--output", required=True, type=Path,
                        help="canonical output file; parent directory is created")
    return parser.parse_args()


def main():
    args = parse_args()
    source = args.input.expanduser()
    output = args.output.expanduser()
    if not source.is_file():
        raise SystemExit("input file not found: %s" % source)
    if output.exists():
        raise SystemExit("refusing to overwrite existing output: %s" % output)
    output.parent.mkdir(parents=True, exist_ok=True)

    counts = {}
    seen = set()
    total = 0
    with source.open("r") as handle, output.open("w") as out:
        for line in handle:
            history = parse_history(line.rstrip("\n").rstrip("\r"))
            canonical = canonical_history(history)
            if canonical in seen:
                continue
            seen.add(canonical)
            out.write(format_history(canonical))
            out.write("\n")
            counts[len(canonical)] = counts.get(len(canonical), 0) + 1
            total += 1

    for length in sorted(counts):
        print("length %d: %d" % (length, counts[length]))
    print("total: %d" % total)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
