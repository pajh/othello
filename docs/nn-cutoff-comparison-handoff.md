# NN cutoff comparison handoff

Updated: 2026-10-02. T079. Matches are **unrun**; this task only prepared the
disposable bots and these commands.

## What was created

Three prominently marked disposable snapshots of the current canonical
`src/bots/nn_bot.py` (VERSION 005, exact terminal endgame negamax):

| File | ID | Difference from canonical |
| --- | --- | --- |
| `src/bots/nn_c6_bot.py` | `NN-005-R2-T0.05-C6` | `COUNT_LEFT = 6` + header marker |
| `src/bots/nn_c8_bot.py` | `NN-005-R2-T0.05-C8` | `COUNT_LEFT = 8` + header marker |
| `src/bots/nn_c10_bot.py` | `NN-005-R2-T0.05-C10` | `COUNT_LEFT = 10` + header marker |

Each file starts with a `# DISPOSABLE SNAPSHOT` comment directing development
back to `src/bots/nn_bot.py`. Everything else is copied verbatim: `VERSION`
stays `005` as snapshot provenance, `RANDOM_MOVES = 2` and `TEMPERATURE = 0.05`
are unchanged, and each copy keeps the required `OTHELLO_NN_CHECKPOINT`
environment selection so both seats load the same explicitly chosen weights.
Canonical `nn_bot.py` is unchanged at `COUNT_LEFT = 0`. There is no shared
configuration abstraction.

## Commands (existing runner, unchanged)

All use the retained selected Generation010 checkpoint `models/best.pt`,
`--workers 4`, and the default alternating colours (no `--force-start`).
`time` measures the whole batch's wall time; the runner's `run-summary.txt`
also carries an elapsed field.

```sh
# C6 vs canonical C0
time OTHELLO_NN_CHECKPOINT=$PWD/models/best.pt venv/bin/python -m rig.cli \
  --bot1 bots.nn_c6_bot --bot2 bots.nn_bot --games 100 --seed 98006 \
  --workers 4 --output-dir runs/nn-c6-vs-c0

# C8 vs canonical C0
time OTHELLO_NN_CHECKPOINT=$PWD/models/best.pt venv/bin/python -m rig.cli \
  --bot1 bots.nn_c8_bot --bot2 bots.nn_bot --games 100 --seed 98008 \
  --workers 4 --output-dir runs/nn-c8-vs-c0

# C10 vs canonical C0
time OTHELLO_NN_CHECKPOINT=$PWD/models/best.pt venv/bin/python -m rig.cli \
  --bot1 bots.nn_c10_bot --bot2 bots.nn_bot --games 100 --seed 98010 \
  --workers 4 --output-dir runs/nn-c10-vs-c0

# C0 vs C0 baseline, same weights and worker count
time OTHELLO_NN_CHECKPOINT=$PWD/models/best.pt venv/bin/python -m rig.cli \
  --bot1 bots.nn_bot --bot2 bots.nn_bot --games 100 --seed 98000 \
  --workers 4 --output-dir runs/nn-c0-vs-c0
```

Compare each cutoff batch's wall time against the C0/C0 baseline. This is a
**practical throughput comparison across different game traces**, not a
controlled per-node benchmark: each cutoff changes which moves are played, so
the games themselves differ.

## Optional later self-play timing command

To measure both-seat solver throughput relevant to a future 5,000-game
collection (both seats at the same cutoff):

```sh
time OTHELLO_NN_CHECKPOINT=$PWD/models/best.pt venv/bin/python -m rig.cli \
  --bot1 bots.nn_c8_bot --bot2 bots.nn_c8_bot --games 100 --seed 98108 \
  --workers 4 --output-dir runs/nn-c8-vs-c8
```

A rough 5,000-game estimate is this batch's wall time × 50 **only** if hardware,
worker count and settings match; it is not a guaranteed GitHub runtime and the
GitHub runner is unmeasured. No training or workflow change is part of this
task.

## Notes on RNG streams

The bot ID is part of the derived per-seat RNG seeding, so changing the cutoff
changes the derived RNG streams. That is expected here, because these are
strength matches and each cutoff should be free to play its own games. It is
the opposite of the completed zero-cutoff equivalence check, which had to hold
the per-seat RNG streams identical to compare like with like. Do not compare
these matches by CLI seed alone.

## Checks actually performed

- `py_compile` succeeds for all three snapshot files.
- `diff` against canonical `src/bots/nn_bot.py` shows **only** the 5-line
  disposable marker and the single `COUNT_LEFT` line differing (7 changed diff
  lines each); no other code or comment was altered.
- Grep confirms each file has exactly one `COUNT_LEFT`, `VERSION = '005'` and
  the unmodified `ID = ...-C{COUNT_LEFT}` interpolation, so the IDs embed
  `C6`/`C8`/`C10`.
- No model was loaded, no game or match was run, and no benchmark, Edax call,
  commit or push was performed.

## Limitations

- No strength or timing result exists yet; all matches above are unrun.
- The disposable snapshots are snapshots only: they can go stale as canonical
  `nn_bot.py` evolves and should be regenerated before later comparisons.
- No strength claim is made, and large cutoffs are exponential in the number of
  empty squares.
