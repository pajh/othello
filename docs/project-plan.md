# Project architecture and scope

This is a supervised personal learning project for Othello rules, reproducible bots and outcome-based training. The user chooses experiments and runs larger collections, benchmarks and training jobs. The current pipeline includes a standard-library game rig, versioned JSONL records, NumPy conversion, a small CPU PyTorch model/trainer, and user-run bot evaluation.

## Source layout

- `src/rig/` owns the rules engine, observation types, single-game runner, record serialization and sequential batch CLI.
- `src/bots/` contains `random_bot`, the deterministic `max_bot` scaffold, and `nn_bot`.
- `src/training/` contains schema-v1 record replay/conversion, the outcome MLP and its trainer.
- `scripts/` contains small supervised helpers; larger jobs are launched and monitored by the user.
- `runs/` and `checkpoints/` retain generated data and models; `work/` is disposable scratch space. These generated directories are ignored by Git.

Import names are `rig.*`, `bots.*` and `training.*`; `src/` is a package source root. The existing `venv/` is the local environment. See [README.md](../README.md) for setup and run commands.

## Runtime and data contracts

`rig.engine` is the sole rules implementation. A bot exposes `play(observation, *, rng)` and may expose `get_id()` and `create_player()`. The batch CLI assigns separate seeded random streams by bot identity and creates a fresh player for each seat in each game. Default colour assignment alternates. See [batch-design.md](batch-design.md) for the CLI seed rules and authoritative schema-v1 record format.

Eligible normal games are replayed through the engine to construct post-action samples, including forced passes, from the acting player's own/opponent perspective. Forfeits are excluded. Whole eligible games are shuffled and split before rows are flattened; the retained 1,000-game collection produced 60,411 positions and an 800/200 split. See [dataset-design.md](dataset-design.md) for exact archive contracts.

The baseline model and training choices are recorded in [first-model-design.md](first-model-design.md). The retained model has been evaluated against random and in self-play; reports distinguish prediction loss, match outcomes and timing without treating one batch as proof of general strength.

## Working boundaries

Use small bounded changes with explicit file scopes and saved handoffs. Keep the engine authoritative, avoid unnecessary frameworks and dependencies, preserve failed results, and record actual work in `status.md`, `TODO.md` and `GENERATIONS.md`. Changes to architecture, training method, bot settings, temperature or collection decisions belong to the user. Parallel games, endgame search and deployment/export are not implemented.
