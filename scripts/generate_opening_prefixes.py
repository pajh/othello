#!/usr/bin/env python3
"""Enumerate every legal move prefix from the initial Othello board.

Writes one history per line for all lengths from 0 through ``--depth``
inclusive.  Each line is a comma-separated sequence of lowercase coordinates
(for example ``f5,d6,c3``).  The empty initial history is a single blank line.
No boards, scores or metadata are written, and Edax is never used.
"""

import argparse
from pathlib import Path

from rig.engine import BLACK, apply_move, initial_board, legal_moves


def square_to_coordinate(square):
    """Return a lowercase coordinate such as ``f5`` for a 0..63 square."""
    row, col = divmod(square, 8)
    return "%s%d" % (chr(ord("a") + col), row + 1)


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--depth",
        required=True,
        type=int,
        help="maximum number of recorded turn actions (inclusive)",
    )
    parser.add_argument(
        "--output",
        required=True,
        type=Path,
        help="output text file; its parent directory is created",
    )
    return parser.parse_args()


def enumerate_prefixes(board, player, actions, depth, emit):
    """Depth-first enumeration in ascending ``legal_moves`` order."""
    emit(actions)
    if len(actions) >= depth:
        return

    moves = legal_moves(board, player)
    if moves:
        for move in moves:
            actions.append(square_to_coordinate(move))
            enumerate_prefixes(apply_move(board, player, move), -player,
                               actions, depth, emit)
            actions.pop()
        return

    # The player on turn has no legal move.
    other = -player
    if not legal_moves(board, other):
        return  # terminal board: no further action to record
    # Forced pass: record it, switch player, and continue.
    actions.append("pass")
    enumerate_prefixes(board, other, actions, depth, emit)
    actions.pop()


def main():
    args = parse_args()
    if args.depth < 0:
        raise SystemExit("--depth must be a nonnegative integer")

    output = args.output.expanduser()
    if output.exists():
        raise SystemExit("refusing to overwrite existing output: %s" % output)
    output.parent.mkdir(parents=True, exist_ok=True)

    counts = [0] * (args.depth + 1)

    with output.open("w") as handle:

        def emit(actions):
            counts[len(actions)] += 1
            handle.write(",".join(actions))
            handle.write("\n")

        enumerate_prefixes(initial_board(), BLACK, [], args.depth, emit)

    for length, count in enumerate(counts):
        print("length %d: %d" % (length, count))
    print("total: %d" % sum(counts))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
