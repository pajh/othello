# Dataset conversion contract

The converter reads a run directory or its `games.jsonl`, validates schema-v1 records, replays every eligible normal game through `rig.engine`, and excludes well-formed forfeits. Malformed or inconsistent records fail with source context. No game rules are reimplemented in the converter.

## Samples

Replay starts from the engine's initial board with Black to move. Each saved position is checked against the replayed pre-action board, actor, and legal action (including a forced pass represented by `null`). The final board, termination and winner must agree. For each accepted action, including a pass and the terminal winning move, apply the action and emit one post-action sample. Plane 0 marks the acting player's discs; plane 1 marks the opponent's. Empty cells are zero in both planes. The target is +1 for an actor win, -1 for a loss, or 0 for a draw. Forfeits produce no samples.

Public parser interface: `training.data.load_games(input_path) -> dict`, returning `source_path`, metadata `run_id`, `input_game_count`, `skipped_forfeit_count`, and eligible games in input order. Each game contains `game_id` and its ply-ordered samples; each sample contains binary `(2, 8, 8)` planes, outcome, game ID and ply.

## Split and archives

CLI: `python -m training.convert --input PATH --output-dir PATH --seed INT [--train-fraction FLOAT]`. The seed is a nonnegative integer; the finite fraction must satisfy `0 < fraction < 1` and defaults to 0.8. Use NumPy `default_rng(seed).permutation` over eligible games, assign the first `floor(fraction * count)` games to training, and keep every game's samples together. Flatten in permutation order, preserving each game's original ply order. Reject empty splits.

Write fixed `training.npz` and `validation.npz`, each containing only:

- `boards`: `uint8`, shape `(N, 2, 8, 8)`;
- `outcomes`: `int8`, shape `(N,)`, values -1/0/+1;
- `game_ids`: fixed-width Unicode, shape `(N,)`, with no object/pickle data;
- `plies`: `uint8`, shape `(N,)`, after validating bounds.

The converter stages artifacts before publishing their fixed names and writes `conversion-summary.txt` last; multi-file publication is not atomic. The summary records source/run identity, paths, schema and encoding versions, NumPy version, split settings and exact game/position/outcome counts.

The supervised smoke against the retained collection passed: 1,000 eligible games split 800/200 into 48,321/12,090 rows (60,411 total), with pickle-free archive loading and two after-action perspective spots agreeing. That collection had no forfeits, so the exclusion path was not runtime-exercised. See [collection-1000-review.md](collection-1000-review.md).
