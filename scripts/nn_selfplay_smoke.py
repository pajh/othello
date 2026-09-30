#!/usr/bin/env python3
"""User-run NN self-play smoke with exact action-trace diversity counts."""

import hashlib
import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'work/nn-selfplay-smoke'
CHECKPOINT = (ROOT / 'checkpoints/first-model/run-2103bc51994e46a099f8b3d78618efd3'
              / 'best.pt').resolve()
GAMES = 100
SEED = 89012
BOT_ID = 'NN-004-R2-T0.05'
CHECK_REPORT = OUTPUT / 'match-check.txt'
DIVERSITY_REPORT = OUTPUT / 'diversity-summary.txt'


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def summary_count(text, label):
    match = re.search(r'^%s: (\d+)$' % re.escape(label), text, re.MULTILINE)
    require(match is not None, 'summary missing %s' % label)
    return int(match.group(1))


def write_latest(path, text, prefix):
    temporary = None
    try:
        with tempfile.NamedTemporaryFile('w', encoding='utf-8', dir=path.parent,
                                         prefix=prefix, delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(text)
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def derived_seed(master_seed, game_index, bot_id):
    value = f'{master_seed}:{game_index}:{bot_id}'.encode('ascii')
    return int.from_bytes(hashlib.sha256(value).digest()[:8], 'big')


def nonnegative_int(text):
    try:
        value = int(text)
    except ValueError:
        raise argparse.ArgumentTypeError('must be an integer') from None
    if value < 0:
        raise argparse.ArgumentTypeError('must be 0 or greater')
    return value


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seed', type=nonnegative_int, default=SEED,
                        help='master RNG seed (default: %(default)s)')
    return parser.parse_args(argv)


def largest_group(counts):
    return max(counts.values(), default=0)


def main():
    helper_started = time.perf_counter()
    args = parse_args()
    seed = args.seed
    require(CHECKPOINT.is_file(), 'checkpoint does not exist: %s' % CHECKPOINT)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    before = {path.name for path in OUTPUT.glob('run-*') if path.is_dir()}
    env = os.environ.copy()
    env['OTHELLO_NN_CHECKPOINT'] = str(CHECKPOINT)
    print('Checkpoint: %s' % env['OTHELLO_NN_CHECKPOINT'], flush=True)
    command = [
        sys.executable, '-m', 'rig.cli',
        '--bot1', 'bots.nn_bot', '--bot2', 'bots.nn_bot',
        '--games', str(GAMES), '--seed', str(seed),
        '--output-dir', str(OUTPUT),
    ]
    subprocess_started = time.perf_counter()
    process = subprocess.Popen(command, cwd=ROOT, env=env)
    try:
        exit_code = process.wait()
    except KeyboardInterrupt:
        exit_code = process.wait()
        return exit_code if exit_code else 130
    subprocess_elapsed = time.perf_counter() - subprocess_started
    new_runs = [path for path in OUTPUT.glob('run-*')
                if path.is_dir() and path.name not in before]
    if exit_code:
        if new_runs:
            print('CLI failed; preserve and inspect %s' % new_runs[0], file=sys.stderr)
        return exit_code
    require(len(new_runs) == 1,
            'expected one new run directory, found %d' % len(new_runs))
    run_dir = new_runs[0]
    metadata = json.loads((run_dir / 'metadata.json').read_text(encoding='utf-8'))
    require(metadata['bot1_id'] == BOT_ID and metadata['bot2_id'] == BOT_ID,
            'metadata bot IDs do not match %s' % BOT_ID)
    require(metadata['bot1_module'] == 'bots.nn_bot'
            and metadata['bot2_module'] == 'bots.nn_bot',
            'metadata bot modules are unexpected')
    require(metadata['master_seed'] == seed and metadata['requested_games'] == GAMES
            and metadata['starting_player_mode'].startswith('alternating'),
            'metadata has unexpected seed, count or colour mode')

    with (run_dir / 'games.jsonl').open(encoding='utf-8') as stream:
        records = [json.loads(line) for line in stream if line.strip()]
    require(len(records) == GAMES,
            'expected %d records, found %d' % (GAMES, len(records)))

    black_counts = {1: 0, 2: 0}
    wins = {1: 0, 2: 0}
    draws = 0
    traces = []
    late_rows = []
    for index, record in enumerate(records):
        require(record['game_index'] == index, 'unexpected game index %d' % index)
        require(record['termination'] == 'normal'
                and record['training_eligible'] is True,
                'game %d was not a normal eligible completion' % index)
        require(record['forfeiting_bot'] is None and record['error'] is None,
                'game %d records a forfeit/error' % index)
        bots = record['bots']
        require(bots['1']['module'] == 'bots.nn_bot'
                and bots['2']['module'] == 'bots.nn_bot',
                'game %d has unexpected bot modules' % index)
        expected_black = 1 if index % 2 == 0 else 2
        require(bots['1']['colour'] == expected_black
                and bots['2']['colour'] == 3 - expected_black,
                'game %d colours do not alternate' % index)
        black_counts[1] += bots['1']['colour'] == 1
        black_counts[2] += bots['2']['colour'] == 1
        for bot_id in (1, 2):
            expected = derived_seed(seed, index, bot_id)
            require(bots[str(bot_id)]['seed'] == expected,
                    'game %d bot %d seed does not match derivation' % (index, bot_id))
        require(bots['1']['seed'] != bots['2']['seed'],
                'game %d has identical per-bot seeds' % index)
        if record['winner_bot'] in (1, 2):
            wins[record['winner_bot']] += 1
        elif record['winner_bot'] == 0:
            draws += 1
        else:
            raise RuntimeError('game %d has invalid winner_bot' % index)
        positions = record['positions']
        trace = tuple((position['to_play'], position['action'])
                      for position in positions)
        traces.append(trace)
        late_rows.extend((position['board'], position['to_play'], index)
                         for position in positions[12:])
    require(black_counts == {1: 50, 2: 50},
            'expected 50 Black games per bot, got %s' % black_counts)

    summary_path = OUTPUT / 'run-summary.txt'
    summary = summary_path.read_text(encoding='utf-8')
    for expected in (
        'bot 1 ID: %s (bots.nn_bot)' % BOT_ID,
        'bot 2 ID: %s (bots.nn_bot)' % BOT_ID,
        'state: completed', 'requested games: 100', 'completed games: 100',
        'normal terminations: 100', 'forfeits: 0',
    ):
        require(expected in summary, 'summary missing %r' % expected)
    require(summary_count(summary, 'wins, bot 1 (bots.nn_bot)') == wins[1]
            and summary_count(summary, 'wins, bot 2 (bots.nn_bot)') == wins[2]
            and summary_count(summary, 'draws') == draws,
            'summary outcomes disagree with records')

    trace_counts = Counter(traces)
    unique_traces = len(trace_counts)
    prefix_lines = []
    for prefix_len in (4, 8, 12):
        prefixes = [trace[:prefix_len] for trace in traces
                    if len(trace) >= prefix_len]
        counts = Counter(prefixes)
        prefix_lines.append(
            'first %d actions: %d unique prefixes among %d games; '
            'largest group %d games'
            % (prefix_len, len(counts), len(prefixes), largest_group(counts))
        )

    game_sets = defaultdict(set)
    late_key_rows = []
    for board, to_play, game_index in late_rows:
        key = (board, to_play)
        game_sets[key].add(game_index)
        late_key_rows.append(key)
    shared_keys = {key for key, game_indices in game_sets.items()
                   if len(game_indices) >= 2}
    shared_rows = sum(key in shared_keys for key in late_key_rows)
    late_row_count = len(late_key_rows)
    shared_pct = 100.0 * shared_rows / late_row_count if late_row_count else 0.0
    largest_trace = largest_group(trace_counts)
    helper_elapsed = time.perf_counter() - helper_started
    games_per_second = GAMES / subprocess_elapsed if subprocess_elapsed else float('inf')
    estimated_5000 = subprocess_elapsed * (5000 / GAMES)

    diversity = [
        'NN self-play diversity summary',
        'status: descriptive; no diversity threshold',
        'run directory: %s' % run_dir.resolve(),
        'checkpoint: %s' % CHECKPOINT,
        'bot IDs: %s / %s' % (BOT_ID, BOT_ID),
        'seed: %d' % seed,
        'CLI elapsed: %.3f s (includes process startup, import/checkpoint load, games, logging and CLI work).'
        % subprocess_elapsed,
        'CLI throughput: %.3f games/s; 5,000-game linear estimate: %.1f s (%.2f min).'
        % (games_per_second, estimated_5000, estimated_5000 / 60),
        'Helper elapsed through diversity analysis (before report publication): %.3f s.' % helper_elapsed,
        'normal games: 100; forfeits: 0; Black assignment: 50 each',
        'outcomes by bot ID: bot 1 wins=%d; bot 2 wins=%d; draws=%d'
        % (wins[1], wins[2], draws),
        '',
        'Full exact traces use ordered (to_play, action) tuples; passes are null.',
        'unique full traces: %d / 100' % unique_traces,
        'duplicate groups: %d; largest group: %d; duplicate excess: %d'
        % (sum(count >= 2 for count in trace_counts.values()),
           largest_trace, GAMES - unique_traces),
        '',
        'Prefix diversity uses the first N recorded actions, including passes.',
        *prefix_lines,
        '',
        'Late positions are positions[12:] (after the first 12 recorded actions).',
        'Exact absolute-colour key: (pre-action board string, to_play colour).',
        'Distinct late keys: %d; late rows: %d.' % (len(game_sets), late_row_count),
        'Keys occurring in at least two distinct games: %d.' % len(shared_keys),
        'Late rows carrying such a cross-game-shared key: %d / %d (%.2f%%).'
        % (shared_rows, late_row_count, shared_pct),
        'Initial common boards are excluded. No symmetry canonicalisation is used.',
        'A unique trace does not imply an independent game.',
    ]
    write_latest(DIVERSITY_REPORT, '\n'.join(diversity) + '\n', '.diversity-')
    write_latest(
        CHECK_REPORT,
        'status: passed\nrun directory: %s\ncheckpoint: %s\nseed: %d\n'
        'bot IDs: %s / %s\ngames: 100 normal, 0 forfeits; 50 Black each\n'
        'wins: bot 1=%d, bot 2=%d; draws=%d\n'
        'CLI elapsed: %.3f s; throughput: %.3f games/s; 5,000-game linear estimate: %.1f s\n'
        'helper elapsed through diversity analysis, before report publication: %.3f s\n'
        'diversity report: %s\n'
        % (run_dir.resolve(), CHECKPOINT, seed, BOT_ID, BOT_ID,
           wins[1], wins[2], draws, subprocess_elapsed, games_per_second,
           estimated_5000, helper_elapsed, DIVERSITY_REPORT.resolve()),
        '.match-check-',
    )
    print('PASS: 100 normal self-play games, zero forfeits, balanced colours.')
    print('CLI elapsed: %.3f s (includes startup/import/checkpoint load, games and CLI work); %.3f games/s.'
          % (subprocess_elapsed, games_per_second))
    print('5,000-game linear estimate: %.1f s (%.2f min); helper elapsed through analysis, before report publication: %.3f s.'
          % (estimated_5000, estimated_5000 / 60, helper_elapsed))
    print('Run: %s' % run_dir.resolve())
    print('Checkpoint: %s' % CHECKPOINT)
    print('Diversity report: %s' % DIVERSITY_REPORT.resolve())
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError, TypeError, RuntimeError) as exc:
        print('Self-play smoke failed: %s' % exc, file=sys.stderr)
        raise SystemExit(1) from exc
