# Review: first 1,000-game collection

Read-only structural review of `runs/run-197b46d72b9447ebb2e315321400b3e8/` and `runs/run-summary.txt`.

- Metadata and summary agree: 1,000 requested/completed, all normal, 0 forfeits, 55 draws, bot 1 wins 484, bot 2 wins 461; seed 12345 and alternating starts.
- Parsed all 1,000 JSONL records. Every game is training-eligible; 60,411 total positions.
- Bot colours are balanced (each bot Black 500 times and White 500 times); results map consistently from winner colour to winner bot.
- All 1,000 game IDs and indexes are unique; each bot has 1,000 unique seeds.
- Basic checks passed for final-board encoding and disc counts, plus position board encoding, ply sequence, alternating `to_play`, and action range/pass representation.
- This checks record shape and internal bookkeeping only. It does not replay moves, establish legality/engine correctness, or make positions independent; the games share the same engine and collection setup.
