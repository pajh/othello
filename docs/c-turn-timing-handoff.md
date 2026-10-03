# C endgame timing helper handoff

The timing helper is ready at `scripts/check_c_turn_timing.py`. It runs games
sequentially with one worker, alternates colours, and derives per-seat game
seeds through the existing `rig.cli._derive_seed` convention. It wraps the
callables given to `rig.runner.run_game` with `perf_counter_ns`, saves every
timing row in `raw-timings.jsonl`, and writes replayable schema-v1 games with
`rig.records`. It explicitly closes each C child after the game.

The default is 100 games and seed 99016. After the C model build is ready, run:

```sh
venv/bin/python scripts/check_c_turn_timing.py \
  --checkpoint runs/github-c8-second/checkpoints/github-candidate/best.pt \
  --output-dir runs/c-turn-timing
```

The latest report is atomically replaced at
`runs/c-turn-timing/timing-summary.txt`. Each run keeps raw games, raw timing
rows, and JSON metadata in its own `run-<uuid>` directory. The report includes
first actual moves separately (including C process startup, with a strict
2,000 ms count), later actual moves, and later moves at 16 or fewer empties
with multiple legal actions. Those groups report min, mean, nearest-rank p50,
p95, p99, max, and strict `>150 ms` counts. Forced passes stay in the raw log
and are excluded from actual-move aggregates. No deadline is enforced and
latency does not cause forfeits.

C latency includes the Python wrapper's board/action serialization, pipe I/O,
child startup on its first actual move, and response validation. Python latency
measures only the bot callable. This is a wrapper-inclusive comparison, not a
precise subtraction of wrapper overhead. The helper records C-NN-006 separately
from the wrapper's historical `C-RAND-001` ID, Python bot/checkpoint hash,
embedded model generation, generated submission and executable hashes, GCC
version/flags, PyTorch thread counts, settings, seeds, counts, and elapsed time.
Both C and Python use the Generation 016 candidate weights.

Checks actually run: `py_compile`, CLI `--help`, and a four-value aggregate
stub covering percentile ranks and strict 150 ms / 2,000 ms thresholds passed.
No games were run while preparing this helper.
