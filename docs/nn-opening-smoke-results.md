# NN random-opening smoke result (T033)

The supervised run completed 100/100 normal games with zero forfeits and alternating colours (50 games as Black for each bot), seed `78901`. Summary and metadata agree on `NN-002-R2` (`bots.nn_bot`) versus `RAND-001` (`bots.random_bot`).

`nn_bot` won 77, drew 3 and lost 20; its draw-adjusted score was 78.5% (77 + 3/2 points out of 100). The helper reported PASS and recorded the selected checkpoint as [best.pt](/home/paul/dev/othello/checkpoints/first-model/run-2103bc51994e46a099f8b3d78618efd3/best.pt). Run artifacts are under `/home/paul/dev/othello/work/nn-opening-smoke/run-149bd65db0aa488f8e26a9d045fcbeea/`; helper report: `/home/paul/dev/othello/work/nn-opening-smoke/match-check.txt`.

For context, the earlier seed-67890 comparison without the random-opening setting produced 78 wins, 3 draws and 19 losses. These are separate 100-game batches, so their difference does not establish a causal opening effect. The smoke verifies the recorded IDs, normal completion, no forfeits and balanced colours; it is not a broader playing-strength evaluation.
