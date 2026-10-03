# Hosted symmetry round — results

GitHub Actions run [36906357664](https://github.com/pajh/othello/actions/runs/36906357664) completed successfully on 2026-10-01. The job ran 18:22:40–18:32:07 UTC (9m27s). It used commit `baa893816cf7b0e367bdb37dc81c38162bcfdd41`, four hosted CPUs, and parent `models/best.pt` (the previously selected Generation009 checkpoint).

Collection used NN-004-R2-T0.05 self-play, seed 90006, four workers and one numerical thread per worker. All 5,000 games terminated normally with zero forfeits: bot 1/bot 2/draws = 2,443/2,423/134, with 2,500 Black assignments per seat. CLI collection time was 327.189s. The saved diversity report found no duplicate action traces and no shared exact late-position keys after 12 actions; these descriptive counts make no independence claim.

Conversion retained all 5,000 games and 302,808 pre-expansion positions, using a whole-game 80/20 split (seed 12345): 4,000 training games / 242,227 positions and 1,000 validation games / 60,581 positions. Eight-way spatial symmetry expansion produced 1,937,816 training rows and 484,648 validation rows. Actor planes were not swapped.

Training initialized from the hosted parent weights with a fresh Adam optimizer and current settings. Starting train/validation MSE was 0.184505/0.187069; constant validation baseline was 0.244016. It completed two epochs before patience stopped the run. Best epoch was 1, with validation MSE 0.185902; final train/validation MSE was 0.177591/0.186646. Trainer time was 30.597s (2.802s load time). The best checkpoint is `runs/github-symmetry-third/checkpoints/github-candidate/best.pt`; parent copy is `runs/github-symmetry-third/runs/github-selfplay/parent.pt`.

The 1,000-game alternating-colour evaluation used matching NN-004-R2-T0.05 settings and the exact downloaded parent checkpoint. Candidate/parent/draw results were 602/369/29, zero forfeits, seed 190006. Candidate score was 61.65%. Raw run: `runs/github-symmetry-third/runs/github-evaluation/run-b50e5e4f3c0c47e0816065be0b0edce0`; fixed report: `runs/github-symmetry-third/runs/github-evaluation/evaluation-summary.txt`.

For context, the two earlier hosted symmetry candidates scored 65.15% against their own exact parent in Generation008 and 59% in Generation009, each over 1,000 games. This round's 61.65% is against a distinct parent opponent. These batches do not establish a trend or prove plateau, slowdown, or robustness across seeds. Validation losses are each from their own converted split and should not be compared across rounds as if measured on the same data.

Saved collection, conversion, training, evaluation and runtime reports are under `runs/github-symmetry-third/`. No training or evaluation jobs were started for this review.
