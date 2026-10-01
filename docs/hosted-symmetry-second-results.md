# Hosted symmetry round 2 results

GitHub Actions run [36891605722](https://github.com/pajh/othello/actions/runs/36891605722), attempt 1, completed successfully on 2026-10-01. Commit `b25322fbf95d13c22b2b3440abb4414c49a710cc`; 4 runner CPUs. The job ran 9m30s overall (16:23:25–16:32:55 UTC): collection 5m22s, conversion 1m37s, training 34s, evaluation 1m07s (rounded step times).

## Collection and conversion

- Parent input: `models/best.pt`, the selected Generation 008 epoch-2 checkpoint; preserved locally as [parent.pt](/home/paul/dev/othello/runs/github-symmetry-second/runs/github-selfplay/parent.pt).
- Self-play: 5,000 games, seed 90005, four workers, alternating colours; both seats `NN-004-R2-T0.05`. All 5,000 terminated normally, with 0 forfeits: bot 1 won 2,456, bot 2 won 2,402, and 142 were draws.
- Whole-game split before augmentation: 4,000 training games and 1,000 validation games; no games skipped. Eight symmetry transforms per position yielded 1,937,416 training rows (242,177 before expansion) and 484,384 validation rows (60,548 before expansion).
- Run directory: [self-play artifacts](/home/paul/dev/othello/runs/github-symmetry-second/runs/github-selfplay); raw game records remain at `runs/github-symmetry-second/runs/github-selfplay/run-f6ebfa3b934c41e481b1cba5ca8973c6/games.jsonl`.

## Training

Continued parent weights from `models/best.pt` with a fresh Adam optimizer and current settings (30 epoch maximum, batch 256, learning rate 0.001, seed 12345, patience 1; CPU, 2 Torch threads). Initial train/validation MSE was 0.194076/0.194623. Two epochs ran; best was epoch 1 at validation MSE 0.192371. Final epoch validation MSE was 0.192742 and final training MSE 0.182563. Training summary reports 31.647 seconds total, including 3.430 seconds loading. Candidate checkpoint: [best.pt](/home/paul/dev/othello/runs/github-symmetry-second/checkpoints/github-candidate/best.pt); parent remains separately preserved above.

## Candidate versus parent

The 1,000-game evaluation used seed 190005, alternating colours, four workers, and matching `NN-004-R2-T0.05` settings. Candidate (bot 1) won 577, drew 26, and lost 397: **59.00% score**, 0 forfeits. The exact evaluated files are [candidate best.pt](/home/paul/dev/othello/runs/github-symmetry-second/checkpoints/github-candidate/best.pt) and [parent.pt](/home/paul/dev/othello/runs/github-symmetry-second/runs/github-selfplay/parent.pt); raw match records are at `runs/github-symmetry-second/runs/github-evaluation/run-f52013869dcb496da58e0cb177735f0f/games.jsonl`.

The preceding hosted parent match was 633/37/330 (65.15%) in 1,000 games. These are distinct parent-candidate match batches and the new score is lower; this comparison alone does not establish a cause or a trend. Separately, the user reports that the deployed previous quantized candidate moved from rank 78 to rank 17 in Wood 2. That is independent CodinGame arena evidence, not a measurement of this new candidate or a controlled quantization comparison.

Detailed downloaded reports and logs are under `runs/github-symmetry-second/`.
