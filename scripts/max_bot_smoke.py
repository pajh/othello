#!/usr/bin/env python3
"""User-run 100-game integration check for max_bot versus random_bot."""

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'work/max-bot-smoke'
GAMES = 100
SEED = 54321


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    before = {path.name for path in OUTPUT.glob('run-*') if path.is_dir()}
    command = [
        sys.executable, '-m', 'rig.cli',
        '--bot1', 'bots.max_bot', '--bot2', 'bots.random_bot',
        '--games', str(GAMES), '--seed', str(SEED),
        '--output-dir', str(OUTPUT),
    ]
    print('Running 100 games; artifacts will be in %s' % OUTPUT, flush=True)
    process = subprocess.Popen(command, cwd=ROOT)
    try:
        exit_code = process.wait()
    except KeyboardInterrupt:
        exit_code = process.wait()
        return exit_code if exit_code else 130

    new_runs = [path for path in OUTPUT.glob('run-*')
                if path.is_dir() and path.name not in before]
    if exit_code:
        if new_runs:
            print('CLI failed; preserve and inspect %s' % new_runs[0], file=sys.stderr)
        return exit_code
    require(len(new_runs) == 1,
            'expected one new run directory, found %d' % len(new_runs))
    run_dir = new_runs[0]
    records = []
    with (run_dir / 'games.jsonl').open(encoding='utf-8') as stream:
        records = [json.loads(line) for line in stream if line.strip()]
    require(len(records) == GAMES,
            'expected %d records, found %d' % (GAMES, len(records)))

    bot1_black = bot2_black = 0
    for index, record in enumerate(records):
        require(record['game_index'] == index, 'unexpected game index %d' % index)
        require(record['termination'] == 'normal' and record['training_eligible'] is True,
                'game %d was not a normal eligible completion' % index)
        require(record['forfeiting_bot'] is None and record['error'] is None,
                'game %d records a forfeit/error' % index)
        bots = record['bots']
        require(bots['1']['module'] == 'bots.max_bot'
                and bots['2']['module'] == 'bots.random_bot',
                'game %d has unexpected bot modules' % index)
        expected_bot1_colour = 1 if index % 2 == 0 else 2
        require(bots['1']['colour'] == expected_bot1_colour
                and bots['2']['colour'] == 3 - expected_bot1_colour,
                'game %d colours do not alternate as expected' % index)
        bot1_black += bots['1']['colour'] == 1
        bot2_black += bots['2']['colour'] == 1
    require(bot1_black == bot2_black == 50,
            'expected balanced 50/50 Black assignment, got %d/%d'
            % (bot1_black, bot2_black))

    summary_path = OUTPUT / 'run-summary.txt'
    summary = summary_path.read_text(encoding='utf-8')
    for expected in ('state: completed', 'requested games: 100',
                     'completed games: 100', 'normal terminations: 100',
                     'forfeits: 0'):
        require(expected in summary, 'summary missing %r' % expected)
    print('PASS: 100 normal games, zero forfeits, alternating colours.')
    print('Run: %s' % run_dir)
    print('Summary: %s' % summary_path)
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError, TypeError, RuntimeError) as exc:
        print('Smoke check failed: %s' % exc, file=sys.stderr)
        raise SystemExit(1) from exc
