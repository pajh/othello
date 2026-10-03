#!/usr/bin/env python3
"""Compare wrapper-inclusive C decision latency with canonical NN call latency.

This is a small, sequential, single-process 100-game helper. It times each
callable at the same boundary the runner uses; C measurements include protocol
serialization, pipes, child startup on the first actual move, and validation.
"""

import argparse
import hashlib
import importlib
import json
import math
import os
from pathlib import Path
import statistics
import subprocess
import sys
import time
import uuid


ROOT = Path(__file__).resolve().parents[1]
SEED_DEFAULT = 99016
GAMES_DEFAULT = 100
SEARCH_EMPTIES = 16
SEARCH_BUDGET_MS = 140
SEARCH_CLOCK_INTERVAL = 256
PLATFORM_TURN_MS = 150


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, 'rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def percentile(values, fraction):
    """Nearest-rank percentile (fraction from 0 to 1)."""
    ordered = sorted(values)
    return ordered[max(0, math.ceil(len(ordered) * fraction) - 1)]


def aggregate(rows):
    values = [row['elapsed_ns'] / 1_000_000 for row in rows]
    if not values:
        return {'count': 0}
    return {
        'count': len(values),
        'min_ms': min(values),
        'mean_ms': statistics.fmean(values),
        'p50_ms': percentile(values, .50),
        'p95_ms': percentile(values, .95),
        'p99_ms': percentile(values, .99),
        'max_ms': max(values),
        'over_150ms': sum(value > PLATFORM_TURN_MS for value in values),
        'over_2000ms': sum(value > 2000 for value in values),
    }


def format_stats(stats, include_first_move_limit=False):
    if not stats['count']:
        return 'n=0'
    text = ('n={count}, min/mean/p50/p95/p99/max={min_ms:.3f}/'
            '{mean_ms:.3f}/{p50_ms:.3f}/{p95_ms:.3f}/{p99_ms:.3f}/'
            '{max_ms:.3f} ms, >150ms={over_150ms}').format(**stats)
    if include_first_move_limit:
        text += ', >2000ms=%d' % stats['over_2000ms']
    return text


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--games', type=int, default=GAMES_DEFAULT)
    parser.add_argument('--seed', type=int, default=SEED_DEFAULT)
    parser.add_argument('--checkpoint', required=True, type=Path)
    parser.add_argument('--output-dir', required=True, type=Path)
    args = parser.parse_args(argv)
    if args.games < 1:
        parser.error('--games must be positive')

    checkpoint = args.checkpoint.resolve()
    if not checkpoint.is_file():
        parser.error('checkpoint does not exist: %s' % checkpoint)
    c_executable = ROOT / 'build/c-random-bot'
    submission = ROOT / 'runs/c-submission/submission.c'
    if not c_executable.is_file():
        parser.error('C executable is missing; build it with make bot first')
    if not submission.is_file():
        parser.error('generated C submission is missing: %s' % submission)

    sys.path.insert(0, str(ROOT / 'src'))
    os.environ['OTHELLO_NN_CHECKPOINT'] = str(checkpoint)
    from rig import engine
    from rig.records import make_game_record, write_game_record
    from rig.runner import run_game
    from rig.cli import _derive_seed

    c_module = importlib.import_module('bots.c_random_bot')
    nn_module = importlib.import_module('bots.nn_bot')
    import torch
    c_id = c_module.get_id()
    nn_id = nn_module.get_id()
    # The Python wrapper deliberately retains its historical C-RAND ID; the
    # embedded executable's C-NN identity is recorded separately below.
    if nn_id != 'NN-006-R2-T0.05-C8':
        raise RuntimeError('unexpected Python bot identity: %s' % nn_id)

    run_id = uuid.uuid4().hex
    output_dir = args.output_dir.resolve()
    run_dir = output_dir / ('run-' + run_id)
    run_dir.mkdir(parents=True, exist_ok=False)
    timings_path = run_dir / 'raw-timings.jsonl'
    games_path = run_dir / 'games.jsonl'
    all_rows = {'C': [], 'Python': []}
    first_rows = {'C': [], 'Python': []}
    later_rows = {'C': [], 'Python': []}
    endgame_rows = {'C': [], 'Python': []}
    tallies = {'normal': 0, 'forfeit': 0, 'C': 0, 'Python': 0, 'draw': 0}
    started = time.perf_counter()

    with open(timings_path, 'w', encoding='utf-8') as timing_stream, \
            open(games_path, 'w', encoding='utf-8') as games_stream:
        for game_index in range(args.games):
            c_is_black = game_index % 2 == 0
            seat_kind = {
                engine.BLACK: 'C' if c_is_black else 'Python',
                engine.WHITE: 'Python' if c_is_black else 'C',
            }
            bot_ids = {
                engine.BLACK: 1 if c_is_black else 2,
                engine.WHITE: 2 if c_is_black else 1,
            }
            actual_turns = {'C': 0, 'Python': 0}
            ply = 0

            players = {}
            wrapped_players = {}
            for colour in (engine.BLACK, engine.WHITE):
                kind = seat_kind[colour]
                module = c_module if kind == 'C' else nn_module
                player = module.create_player()
                wrapped_players[colour] = player

                def timed_player(observation, *, rng, _kind=kind,
                                 _player=player, _game=game_index):
                    nonlocal ply
                    move_ply = ply
                    ply += 1
                    empty_count = observation.board.count(engine.EMPTY)
                    legal_count = len(observation.legal_moves)
                    start_ns = time.perf_counter_ns()
                    action = _player(observation, rng=rng)
                    elapsed_ns = time.perf_counter_ns() - start_ns
                    is_pass = action is None
                    first_actual = False
                    if not is_pass:
                        actual_turns[_kind] += 1
                        first_actual = actual_turns[_kind] == 1
                    row = {
                        'game': _game,
                        'seat': _kind,
                        'player': 'black' if observation.player == engine.BLACK else 'white',
                        'ply': move_ply,
                        'empties': empty_count,
                        'legal_count': legal_count,
                        'action': action,
                        'pass': is_pass,
                        'first_actual_move': first_actual,
                        'elapsed_ns': elapsed_ns,
                    }
                    timing_stream.write(json.dumps(row, separators=(',', ':')) + '\n')
                    if not is_pass:
                        all_rows[_kind].append(row)
                        if first_actual:
                            first_rows[_kind].append(row)
                        else:
                            later_rows[_kind].append(row)
                            if empty_count <= SEARCH_EMPTIES and legal_count > 1:
                                endgame_rows[_kind].append(row)
                    return action

                players[colour] = timed_player

            seeds = {bot_id: _derive_seed(args.seed, game_index, bot_id)
                     for bot_id in (1, 2)}
            game_started = time.perf_counter()
            result = run_game(
                players[engine.BLACK], players[engine.WHITE],
                black_seed=seeds[bot_ids[engine.BLACK]],
                white_seed=seeds[bot_ids[engine.WHITE]],
            )
            # Explicitly close each C child before starting the next game.
            for player in wrapped_players.values():
                owner = getattr(player, '__self__', None)
                if owner is not None:
                    owner.close()

            bot_records = {}
            for colour in (engine.BLACK, engine.WHITE):
                bot_id = bot_ids[colour]
                bot_records[bot_id] = {
                    'module': 'bots.c_random_bot' if seat_kind[colour] == 'C'
                              else 'bots.nn_bot',
                    'colour': 1 if colour == engine.BLACK else 2,
                    'seed': seeds[bot_id],
                    'config': {},
                }
            record = make_game_record(
                result, run_id=run_id, game_index=game_index,
                bots=bot_records,
            )
            write_game_record(games_stream, record)
            tallies[result.termination] += 1
            if result.termination == 'normal':
                if result.winner == engine.EMPTY:
                    tallies['draw'] += 1
                else:
                    tallies['C' if result.winner == engine.BLACK
                            and seat_kind[engine.BLACK] == 'C'
                            or result.winner == engine.WHITE
                            and seat_kind[engine.WHITE] == 'C'
                            else 'Python'] += 1
            if game_index == 0 or (game_index + 1) % 10 == 0:
                print('completed %d/%d games; current game %.2fs' %
                      (game_index + 1, args.games,
                       time.perf_counter() - game_started), flush=True)

    elapsed = time.perf_counter() - started
    summaries = {}
    for name, rows in (('first_actual_move', first_rows),
                       ('later_actual_turns', later_rows),
                       ('later_endgame_subset', endgame_rows)):
        summaries[name] = {kind: aggregate(rows[kind]) for kind in ('C', 'Python')}

    gcc = subprocess.run(['gcc', '--version'], capture_output=True,
                         text=True, check=True).stdout.splitlines()[0]
    metadata = {
        'run_id': run_id,
        'games': args.games,
        'seed': args.seed,
        'workers': 1,
        'assignment': 'alternating colours; C Black on even game indices',
        'python_bot': nn_id,
        'python_checkpoint': str(checkpoint),
        'python_checkpoint_sha256': sha256_file(checkpoint),
        'c_bot_source_identity': 'C-NN-006',
        'c_wrapper_reported_identity': c_id,
        'c_search': {'max_empties': SEARCH_EMPTIES,
                     'budget_ms': SEARCH_BUDGET_MS,
                     'clock_interval_nodes': SEARCH_CLOCK_INTERVAL},
        'c_embedded_model_generation': 'Generation016',
        'c_submission_sha256': sha256_file(submission),
        'c_executable_sha256': sha256_file(c_executable),
        'compiler': gcc,
        'compile_flags': 'GCC -std=c11 -O3 -Wall -Wextra -I runs/c-model-embedded -lm',
        'torch_threads': torch.get_num_threads(),
        'torch_interop_threads': torch.get_num_interop_threads(),
        'measurement': 'perf_counter_ns around runner play callable; C includes wrapper serialization/pipes/first-process startup/validation; Python times its callable only',
        'threshold_ms': PLATFORM_TURN_MS,
        'threshold_is_strict': True,
        'forfeit_deadlines_enforced': False,
        'elapsed_seconds': elapsed,
        'game_counts': tallies,
        'timing_summaries': summaries,
    }
    metadata_path = run_dir / 'timing-results.json'
    metadata_path.write_text(json.dumps(metadata, indent=2) + '\n', encoding='utf-8')

    lines = [
        'C endgame decision timing comparison',
        'games: %d; seed: %d; workers: 1; elapsed: %.3fs' %
        (args.games, args.seed, elapsed),
        'bot IDs: C-NN-006 (wrapper reports %s) vs %s' % (c_id, nn_id),
        'C SETTINGS: <=%d empties, %d ms search budget, clock every %d nodes' %
        (SEARCH_EMPTIES, SEARCH_BUDGET_MS, SEARCH_CLOCK_INTERVAL),
        'C embedded model and Python checkpoint are Generation016; checkpoint SHA256 %s' %
        metadata['python_checkpoint_sha256'],
        'Timing wraps the rig play call. C includes Python wrapper/protocol and child startup; Python is callable-only.',
        '150ms is reported as a strict observation threshold, not enforced; forced passes excluded.',
        'First actual moves (includes C child startup):',
        '  C: ' + format_stats(summaries['first_actual_move']['C'], True),
        '  Python: ' + format_stats(summaries['first_actual_move']['Python'], True),
        'Later actual turns:',
        '  C: ' + format_stats(summaries['later_actual_turns']['C']),
        '  Python: ' + format_stats(summaries['later_actual_turns']['Python']),
        'Later turns with <=16 empties and >1 legal move:',
        '  C: ' + format_stats(summaries['later_endgame_subset']['C']),
        '  Python: ' + format_stats(summaries['later_endgame_subset']['Python']),
        'game outcomes: ' + json.dumps(tallies, sort_keys=True),
        'raw data: %s' % run_dir,
    ]
    report = '\n'.join(lines) + '\n'
    output_dir.mkdir(parents=True, exist_ok=True)
    latest = output_dir / 'timing-summary.txt'
    temporary = output_dir / ('.timing-summary.tmp-' + run_id)
    temporary.write_text(report, encoding='utf-8')
    os.replace(temporary, latest)
    print(report, end='')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
