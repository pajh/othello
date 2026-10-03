#!/usr/bin/env python3
"""Compare NN-005 COUNT_LEFT=0 with the retained NN-004 source once."""

import argparse
import importlib.util
import os
from pathlib import Path
import random
import subprocess
import sys
import tempfile


BASELINE_COMMIT = '07ed0ae'
DEFAULT_CHECKPOINT = 'models/best.pt'


def _load_baseline(project_root):
    source = subprocess.check_output(
        ['git', 'show', BASELINE_COMMIT + ':src/bots/nn_bot.py'],
        cwd=project_root, text=True)
    with tempfile.TemporaryDirectory(prefix='nn004-baseline-') as temp_dir:
        path = Path(temp_dir) / 'nn004_bot.py'
        path.write_text(source)
        spec = importlib.util.spec_from_file_location('nn004_baseline', path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    return module


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--checkpoint', default=DEFAULT_CHECKPOINT,
                        help='checkpoint loaded by both revisions '
                             '(default: %(default)s)')
    parser.add_argument('--seed', type=int, default=97001,
                        help='explicit seed for the paired seat RNGs '
                             '(default: %(default)s)')
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parents[1]
    checkpoint = Path(args.checkpoint).expanduser()
    if not checkpoint.is_absolute():
        checkpoint = project_root / checkpoint
    checkpoint = checkpoint.resolve()
    if not checkpoint.is_file():
        parser.error('checkpoint does not exist or is not a file: %s' % checkpoint)

    os.environ['OTHELLO_NN_CHECKPOINT'] = str(checkpoint)
    sys.path.insert(0, str(project_root / 'src'))
    from rig import engine
    from rig.types import Observation, PreviousAction
    from bots import nn_bot as current

    if current.COUNT_LEFT != 0:
        parser.error('current NN COUNT_LEFT must be 0, got %r' % current.COUNT_LEFT)
    old = _load_baseline(project_root)

    # Independent but paired streams per seat. Bot IDs never enter seed derivation.
    rngs = {
        engine.BLACK: (random.Random(args.seed), random.Random(args.seed)),
        engine.WHITE: (random.Random(args.seed + 1), random.Random(args.seed + 1)),
    }
    players = {
        engine.BLACK: (old.create_player(), current.create_player()),
        engine.WHITE: (old.create_player(), current.create_player()),
    }
    board = engine.initial_board()
    player = engine.BLACK
    previous = PreviousAction(kind='start')
    plies = stateful_comparisons = greedy_comparisons = 0

    def report(status, outcome='pending'):
        print('%s plies=%d outcome=%s checkpoint=%s old_id=%s new_id=%s '
              'seed=%d stateful_comparisons=%d greedy_comparisons=%d' %
              (status, plies, outcome, checkpoint, old.get_id(), current.get_id(),
               args.seed, stateful_comparisons, greedy_comparisons))

    while not engine.is_terminal(board):
        legal = engine.legal_moves(board, player)
        observation = Observation(board=board, player=player,
                                  legal_moves=legal,
                                  previous_action=previous)
        old_rng, new_rng = rngs[player]
        old_move = players[player][0](observation, rng=old_rng)
        new_move = players[player][1](observation, rng=new_rng)
        stateful_comparisons += 1

        greedy_old_rng = random.Random(args.seed + 2 + plies)
        greedy_new_rng = random.Random(args.seed + 2 + plies)
        greedy_old = old.play(observation, rng=greedy_old_rng)
        greedy_new = current.play(observation, rng=greedy_new_rng)
        greedy_comparisons += 1
        if (greedy_old != greedy_new or
                greedy_old_rng.getstate() != greedy_new_rng.getstate()):
            report('FAIL greedy mismatch')
            print('player=%d board=%r old_move=%r new_move=%r' %
                  (player, board, greedy_old, greedy_new))
            return 1

        if (old_move != new_move or
                old_rng.getstate() != new_rng.getstate()):
            report('FAIL stateful mismatch')
            print('player=%d board=%r old_move=%r new_move=%r' %
                  (player, board, old_move, new_move))
            return 1

        board = engine.apply_move(board, player, old_move)
        plies += 1
        previous = (PreviousAction(kind='pass') if old_move is None else
                    PreviousAction(kind='move', square=old_move))
        player = -player

    black, white = engine.disc_counts(board)
    winner = engine.winner(board)
    outcome = 'draw %d-%d' % (black, white) if winner == engine.EMPTY else (
        'black %d-%d' % (black, white) if winner == engine.BLACK else
        'white %d-%d' % (white, black))
    report('PASS', outcome)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
