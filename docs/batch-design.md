# Batch games and raw logs — design

CLI: python -m rig.cli --bot1 bots.random_bot --bot2 bots.random_bot --games 100 --seed 12345

Optional --force-start 1 or 2 always assigns that bot Black. Default alternates: bot 1 Black for game index 0, bot 2 Black for index 1. Black always moves first. --games is a positive integer; --seed is the required integer master RNG seed. --output-dir defaults to runs/. All execution is sequential for now.

Bot IDs 1/2 mean command-line identities, even when both module names are identical. Board/turn/winner colour codes mean 0=empty/draw, 1=Black, 2=White. Map engine WHITE=-1 to record code 2. Keep winning bot identity separate from winning colour.

For game index i (zero based) and bot ID b, derive its seed as the unsigned integer from the first 8 bytes of SHA256 of the ASCII string f'{master_seed}:{i}:{b}', interpreted big-endian. Assign those bot seeds to the appropriate colours for run_game. No shared random stream, Python hash(), or scheduling-dependent seeds. Changing colour mode keeps per-bot seeds unchanged. Record both bot and colour assignments. Seed replay assumes matching code/Python environment; recorded moves support replay without RNGs.

## Output

Create a fresh non-hidden run-<uuidhex>/ under output-dir, with metadata.json and games.jsonl. Fixed filenames inside the run; run identity prevents overwriting raw data. Record run ID, schema version, UTC start time, Python/platform/project version, supplied module names, master seed, requested count, starting-player mode and seed derivation identifier. No dependency on Git being initialised; revision unknown is acceptable.

games.jsonl has one complete JSON object per finished game, flushed immediately. Keep completed games on interruption. Engine/writer failures abort visibly; a bot forfeit is a completed record and the batch continues. No partial current-game record. No resume or parallel execution in this stage.

Latest summary: output-dir/run-summary.txt. Include run directory, requested/completed game counts, normal/forfeit/draw totals and wins by bot ID, seeds/mode and completion/interruption/failure state. This is collection bookkeeping, not the deferred strength-evaluation mode. Optional --keep-history rotates the old summary to next unused run-summary.N.txt. Prepare replacement completely in a temporary work file before publication; never overwrite archive files. Without --keep-history replace only latest summary. Raw bot prints/debug output must not enter games.jsonl; no per-turn output from the rig.

## Game schema v1

Top-level fields:
- schema_version: 1; run_id: string; game_id: string (run_id plus game index); game_index: integer.
- bots: object keys '1' and '2', each with module, colour (1/2), seed, config (empty object for now).
- winner: colour 0/1/2; winner_bot: bot ID 0/1/2 (0 draw).
- termination: 'normal' or 'forfeit'; training_eligible: boolean.
- forfeiting_bot: 1/2 or null; error: string or null.
- positions: ordered array of {ply, board, to_play, action}; ply starts 0 and counts accepted actions including passes. board is 64 row-major characters from [012], BEFORE that action; to_play is colour 1/2; action is square 0..63 or null (forced pass).
- final_board: encoded final board, separate from position samples (no invented terminal to_play).
- disc_counts: {black: integer, white: integer}.

Reconstruct positions by replaying `GameResult.actions` through the existing engine. Ensure the final board matches the result board; mismatches are writer errors, not forfeits. A forfeit record includes only its accepted prefix and is not training eligible. `winner` describes the recorded game result, not a perfect-play value. Training conversion, game-level splitting and actor-relative after-action arrays are specified in [dataset-design.md](dataset-design.md).

The sequential CLI and schema-v1 writer are implemented. Execution is sequential, not parallel. Endgame search, HTML reports, resume and parallel scheduling are not implemented.
