#!/usr/bin/env python3
"""User-run 100-game check for NN-002-R2 versus random_bot."""

import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'work/nn-opening-smoke'
CHECKPOINT = (ROOT / 'checkpoints/first-model/run-2103bc51994e46a099f8b3d78618efd3'
              / 'best.pt').resolve()
GAMES = 100
SEED = 78901
NN_ID = 'NN-002-R2'
RANDOM_ID = 'RAND-001'
CHECK_REPORT = OUTPUT / 'match-check.txt'


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def summary_count(text, label):
    match = re.search(r'^%s: (\d+)$' % re.escape(label), text, re.MULTILINE)
    require(match is not None, 'summary missing %s' % label)
    return int(match.group(1))


def write_report(text):
    temporary = None
    try:
        with tempfile.NamedTemporaryFile('w', encoding='utf-8', dir=OUTPUT,
                                         prefix='.match-check-', delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(text)
        os.replace(temporary, CHECK_REPORT)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def main():
    require(CHECKPOINT.is_file(), 'checkpoint does not exist: %s' % CHECKPOINT)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    before = {path.name for path in OUTPUT.glob('run-*') if path.is_dir()}
    env = os.environ.copy()
    env['OTHELLO_NN_CHECKPOINT'] = str(CHECKPOINT)
    print('Checkpoint: %s' % env['OTHELLO_NN_CHECKPOINT'], flush=True)
    command = [
        sys.executable, '-m', 'rig.cli',
        '--bot1', 'bots.nn_bot', '--bot2', 'bots.random_bot',
        '--games', str(GAMES), '--seed', str(SEED),
        '--output-dir', str(OUTPUT),
    ]
    process = subprocess.Popen(command, cwd=ROOT, env=env)
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
    metadata = json.loads((run_dir / 'metadata.json').read_text(encoding='utf-8'))
    require(metadata['bot1_id'] == NN_ID and metadata['bot2_id'] == RANDOM_ID,
            'run metadata has unexpected bot IDs')
    require(metadata['bot1_module'] == 'bots.nn_bot'
            and metadata['bot2_module'] == 'bots.random_bot',
            'run metadata has unexpected bot modules')
    require(metadata['master_seed'] == SEED
            and metadata['requested_games'] == GAMES
            and metadata['starting_player_mode'].startswith('alternating'),
            'run metadata has unexpected seed, count or colour mode')

    with (run_dir / 'games.jsonl').open(encoding='utf-8') as stream:
        records = [json.loads(line) for line in stream if line.strip()]
    require(len(records) == GAMES,
            'expected %d records, found %d' % (GAMES, len(records)))

    nn_black = random_black = nn_wins = random_wins = draws = 0
    for index, record in enumerate(records):
        require(record['game_index'] == index, 'unexpected game index %d' % index)
        require(record['termination'] == 'normal'
                and record['training_eligible'] is True,
                'game %d was not a normal eligible completion' % index)
        require(record['forfeiting_bot'] is None and record['error'] is None,
                'game %d records a forfeit/error' % index)
        bots = record['bots']
        require(bots['1']['module'] == 'bots.nn_bot'
                and bots['2']['module'] == 'bots.random_bot',
                'game %d has unexpected bot modules' % index)
        nn_colour = 1 if index % 2 == 0 else 2
        require(bots['1']['colour'] == nn_colour
                and bots['2']['colour'] == 3 - nn_colour,
                'game %d colours do not alternate' % index)
        nn_black += bots['1']['colour'] == 1
        random_black += bots['2']['colour'] == 1
        if record['winner_bot'] == 1:
            nn_wins += 1
        elif record['winner_bot'] == 2:
            random_wins += 1
        elif record['winner_bot'] == 0:
            draws += 1
        else:
            raise RuntimeError('game %d has invalid winner_bot' % index)
    require(nn_black == random_black == 50,
            'expected balanced 50/50 Black assignment, got %d/%d'
            % (nn_black, random_black))

    summary_path = OUTPUT / 'run-summary.txt'
    summary = summary_path.read_text(encoding='utf-8')
    for expected in (
        'bot 1 ID: %s (bots.nn_bot)' % NN_ID,
        'bot 2 ID: %s (bots.random_bot)' % RANDOM_ID,
        'state: completed', 'requested games: 100', 'completed games: 100',
        'normal terminations: 100', 'forfeits: 0',
    ):
        require(expected in summary, 'summary missing %r' % expected)
    require(summary_count(summary, 'wins, bot 1 (bots.nn_bot)') == nn_wins
            and summary_count(summary, 'wins, bot 2 (bots.random_bot)') == random_wins
            and summary_count(summary, 'draws') == draws,
            'summary win/draw counts disagree with records')

    write_report(
        'status: passed\nrun directory: %s\ncheckpoint: %s\n'
        'seed: %d\nbot 1 ID: %s (bots.nn_bot)\n'
        'bot 2 ID: %s (bots.random_bot)\n'
        'games: 100 normal, 0 forfeits; 50 Black each\n'
        'nn_bot: wins=%d draws=%d losses=%d\n'
        'random_bot: wins=%d draws=%d losses=%d\n'
        % (run_dir.resolve(), CHECKPOINT, SEED, NN_ID, RANDOM_ID,
           nn_wins, draws, random_wins, random_wins, draws, nn_wins)
    )
    print('PASS: 100 normal games, zero forfeits, alternating colours.')
    print('nn_bot: wins=%d draws=%d losses=%d'
          % (nn_wins, draws, random_wins))
    print('random_bot: wins=%d draws=%d losses=%d'
          % (random_wins, draws, nn_wins))
    print('Run: %s' % run_dir.resolve())
    print('Summary: %s' % summary_path.resolve())
    print('Checkpoint selection: %s' % CHECK_REPORT.resolve())
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError, TypeError, RuntimeError) as exc:
        print('Smoke check failed: %s' % exc, file=sys.stderr)
        raise SystemExit(1) from exc
