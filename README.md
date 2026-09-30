# Othello learning project

A personal learning project for Othello rules, bots, and later training experiments. The current rules engine is at `src/rig/engine.py`; one user-run random-versus-random smoke game completed normally, which is a minimal integration check rather than a full correctness check.

## Setup

The existing local environment is `venv/`. From the repository root, activate it and install this project in editable mode:

```sh
source venv/bin/activate
python -m pip install -e .
```

These are user-run setup commands. Core runtime dependencies remain empty; NumPy and PyTorch are optional training/data extras described below. Setuptools is used to build/install the package. The editable install makes `rig`, `bots`, and `training` importable from `src/`.

## Optional dataset and CPU training dependencies

The rules engine and bots stay dependency-free. To install the training extra with the official CPU-only PyTorch wheel, first install `torch` from the PyTorch CPU index, then install the project extra:

```sh
venv/bin/python -m pip install torch --index-url https://download.pytorch.org/whl/cpu
venv/bin/python -m pip install -e '.[training]'
```

The existing `data` extra remains available for NumPy-only dataset conversion (`venv/bin/python -m pip install -e '.[data]'`). The `training` extra includes NumPy and PyTorch; no GPU, torchvision, or torchaudio packages are required.

## First user-run training

To train the initial CPU MLP on the retained 80/20 dataset using the agreed defaults (up to 30 epochs with validation-based patience), run:

```sh
venv/bin/python scripts/train_first.py
```

The helper streams epoch timing and writes each run to a fresh `checkpoints/first-model/run-<uuid>/` directory. It prints the selected output path before training and updates the concise latest check at `checkpoints/first-model/training-check.txt`.

## Structure

- `src/rig/` — game rules and runtime components.
- `src/bots/` — bot implementations.
- `src/training/` — future training utilities.
- `docs/documentation-index.md` — retained architecture, workflow and result documents.
- `work/` — disposable scratch space.
- `runs/` and `checkpoints/` — retained run records and model artifacts; generated contents are ignored by Git.

The retained architecture and data contracts are indexed in [docs/documentation-index.md](docs/documentation-index.md). Larger experiments and future features remain under user control.

## Smoke game

After the editable install, run one seeded random-versus-random game from the repository root:

```sh
venv/bin/python scripts/smoke.py
```

This small integration check prints the winner, final disc counts, and number of actions. It exits nonzero if the game ends by forfeit.

## Batch games

The batch command line plays a sequential batch of games and writes raw, replayable records. Each `--bot1`/`--bot2` value is an importable module exposing a callable `play(observation, *, rng)`; the module is imported once and the same function may play both seats.

```sh
venv/bin/python -m rig.cli --bot1 bots.random_bot --bot2 bots.random_bot --games 100 --seed 12345
```

| option | meaning |
| --- | --- |
| `--bot1`, `--bot2` | required bot module names. Bot ID 1 and 2 are command-line identities, kept distinct even when the names are identical. |
| `--games N` | required number of games (1 or more). |
| `--seed N` | required master RNG seed (any integer). |
| `--force-start {1,2}` | optional: that bot ID always plays Black. |
| `--output-dir DIR` | optional output root, default `runs/`. |
| `--keep-history` | rotate the previous latest summary to the next unused `run-summary.N.txt` before publishing the replacement. |

Colours: Black always moves first. By default bot 1 is Black on even game indices (starting at 0) and bot 2 on odd ones, so the colours alternate; `--force-start` overrides that. An unimportable module or a missing `play` is a setup error that stops the batch before any game; a bot exception during a game is recorded as a forfeit and the batch continues.

### Bot identity and per-game players

A bot module may expose `get_id()`, returning a short single-line display ID such as `RAND-001` or `NN-004-R2-T0.05`. The CLI calls it once during setup, then prints the IDs as prominent `bot 1 ID:` / `bot 2 ID:` lines at startup and at the end, includes them just below the title of `run-summary.txt`, and records them as `bot1_id` and `bot2_id` in `metadata.json`. A module without `get_id` still works and reports its module name instead. IDs are run-level identity only; they are not written into `games.jsonl`, the training archives or any label, so the record schema is unchanged.

A bot module may also expose `create_player()`. When it does, the CLI calls it afresh for each bot seat in each game and plays that game with the returned callable, so a stateful bot starts clean every game and the two seats never share state — this is how `bots.nn_bot` gets its random opening. Modules without `create_player` keep using their module-level `play`, which is the stateless behaviour. Both forms accept the same `play(observation, *, rng)` call and use the runner's per-bot, per-game seeded RNG.

Seeds: bot `b`'s seed for game index `i` is the unsigned big-endian integer from the first eight bytes of SHA-256 over the ASCII text `<master_seed>:<i>:<b>`. It depends on nothing else, so results reproduce from the master seed alone and the colour mode does not change per-bot seeds. Both bot seeds are recorded in every game record.

Output, under a fresh `run-<uuid hex>/` directory in the output root:

- `metadata.json` — run ID, schema version, UTC start time, project/Python/platform versions, supplied module names, bot display IDs, master seed, requested game count, starting-player mode, seed-derivation identifier.
- `games.jsonl` — one complete JSON object per finished game, flushed immediately, so an interruption keeps the games already finished. Each record holds the bot assignment (module, colour 1 or 2, seed), winner colour and winning bot ID, termination (`normal` or `forfeit`), training eligibility, the board before each accepted action, the final board and disc counts. A forfeiting game keeps only its accepted moves and is never training eligible.

Colour codes in records are `0` empty/draw, `1` Black, `2` White; boards are 64 row-major characters from `012`. `0` for `winner` means a draw and `0` for `winner_bot` likewise. `docs/batch-design.md` is the authoritative schema.

The latest summary is written to `<output-dir>/run-summary.txt` and holds the state (completed, interrupted, failed), run directory, requested/completed counts, normal/forfeit/draw totals, wins per bot ID, seeds and mode, and the artifact paths. It is collection bookkeeping, not a strength measurement: a forfeit counts as a win for the opponent.

To rerun the small two-game CLI smoke check, use:

```sh
venv/bin/python scripts/batch_smoke.py
```

It invokes the CLI with two random bots, master seed `12345`, and stores the inspectable run under `work/batch-smoke/`. The initial supervised run passed; this helper remains available for future rig changes.

To run the 100-game `max_bot` versus random integration check with alternating colours and seed `54321`, use:

```sh
venv/bin/python scripts/max_bot_smoke.py
```

The helper streams the CLI output and stores the fresh run under `work/max-bot-smoke/`. It checks normal completion, zero forfeits, module identity and balanced colour assignment; it does not use wins as an acceptance criterion.

To run the supervised 100-game neural-bot comparison, use:

```sh
venv/bin/python scripts/nn_bot_smoke.py
```

The helper explicitly selects the retained `best.pt` checkpoint through `OTHELLO_NN_CHECKPOINT`, streams the CLI output and saves records under `work/nn-bot-smoke/`. It reports `nn_bot` wins, random-bot wins and draws separately; this single run is not a strength threshold.

To check the `NN-002-R2` random-opening integration with a fresh per-seat player each game, use:

```sh
venv/bin/python scripts/nn_opening_smoke.py
```

This runs 100 alternating games with seed `78901` against `random_bot`, selects the retained `best.pt` checkpoint, and stores the run under `work/nn-opening-smoke/`. It checks IDs, normal completion, zero forfeits and balanced colours; win counts are reported without a strength threshold.

To run weighted NN self-play and collect exact trace/prefix and late-position overlap counts, use:

```sh
venv/bin/python scripts/nn_selfplay_smoke.py --seed 89014
```

This runs 100 alternating games using `NN-004-R2-T0.05`, with the retained `best.pt` checkpoint and seed `89014` under `work/nn-selfplay-smoke/`. The helper still defaults to seed `89012`; `--seed` accepts any nonnegative integer. It records CLI elapsed time, games per second, and a 5,000-game linear estimate in its latest reports. The estimate is descriptive rather than a runtime promise; earlier raw run directories are retained. Batched inference may change floating-point results slightly, so games are not promised to be byte-identical across bot versions.

Exit status: 0 when the batch finishes, including when forfeits were recorded; 2 for a setup error; 1 if the engine or writer failed (completed records are kept and a best-effort failed summary is written); 130 after Ctrl-C (completed records are kept and an interrupted summary is published). Progress is printed about ten times per batch; there is no per-move output, and bot output never enters `games.jsonl`.

Execution is sequential only: there is no resume, parallel scheduling, or HTML game report. Dataset conversion and model training are available through the documented helpers. Stateful bots expose `create_player()` so the rig creates an independent callable per seat per game; stateless bots may continue to expose only `play`. Seed replay assumes the same code and Python environment, though recorded moves replay without any RNG.
