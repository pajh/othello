# `nn_bot` supervised match result

The saved summary confirms 100 completed games, all normal with zero forfeits: `nn_bot` 78 wins, random bot 19 wins, and 3 draws. The master seed was 67890, with default alternating starts. `match-check.txt` reports its record check passed, including 50 Black assignments per bot; this scrub did not inspect `games.jsonl`.

The helper selected `/home/paul/dev/othello/checkpoints/first-model/run-2103bc51994e46a099f8b3d78618efd3/best.pt`. The recorded win rate is 78%; the draw-adjusted score is `(78 + 0.5 × 3) / 100 = 79.5%`. This is a favorable result for this single seeded 100-game batch against `random_bot`, not evidence of self-play improvement or optimal play, and it does not isolate an activation-function effect.

Run artifacts: `work/nn-bot-smoke/run-3ab2e0476c7643cdb1ec227fa291b9c2/`; the CLI summary is `work/nn-bot-smoke/run-summary.txt` and the helper record is `work/nn-bot-smoke/match-check.txt`. These paths are noted here; the raw `work/` artifacts are disposable.
