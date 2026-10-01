# Hosted symmetry training results

GitHub Actions run [36887079634](https://github.com/pajh/othello/actions/runs/36887079634) completed on 2026-10-01. The job ran from 15:48:07 to 15:56:56 UTC (8m49s). Recorded stage times were collection 4m42s, conversion 1m29s, training 43s, and evaluation 58s; setup and other workflow overhead account for the remainder.

## Collection and conversion

Self-play completed all 5,000 requested games using `NN-004-R2-T0.05` in both seats, seed 90004, alternating colours, and four workers. All 5,000 games terminated normally, with zero forfeits; there were 184 draws, 2,374 bot 1 wins, and 2,442 bot 2 wins. The collector's recorded elapsed time was 281.285 seconds. All 5,000 games (302,422 positions) entered conversion.

With split seed 12345, the 4,000-game training split contained 241,974 original positions and the 1,000-game validation split contained 60,448. Eight-way board symmetry expansion produced 1,935,792 training rows and 483,584 validation rows (duplicates retained).

## Training and evaluation

Training initialized from `models/best.pt` weights with a fresh Adam optimizer. Settings were 30 maximum epochs, batch size 256, learning rate 0.001, seed 12345, and patience 1. On this split, starting training/validation MSE was 0.200269 / 0.196363. The best validation MSE was 0.190112 at epoch 2; final training MSE after epoch 3 was 0.183592 and final validation MSE was 0.190593. Training stopped by patience after 41.319 seconds. The selected candidate checkpoint is `best.pt`.

In a separate 1,000-game alternating-colour match (seed 190004), the candidate using `best.pt` won 633 games, drew 37, and lost 330 to the parent checkpoint, for a score of 0.6515 using wins plus half-draws. Both bots used NN R2/T0.05 settings and four workers; neither forfeited.

This is encouraging evidence that the trained candidate performed better in this particular parent match. It does not isolate symmetry augmentation as the cause: the candidate also reflects further training on this collection, and the match is one seeded evaluation. Candidate adoption remains a user decision.

## Retained artifacts

- Self-play raw records and metadata: `runs/github-symmetry/runs/github-selfplay/run-c44c8d02c26d4715a999885f8f7a5a51/` (`games.jsonl`, `metadata.json`, `collection-provenance.json`).
- Converted splits and row counts: `runs/github-symmetry/runs/github-selfplay/run-c44c8d02c26d4715a999885f8f7a5a51/dataset/`.
- Candidate checkpoints and training history: `runs/github-symmetry/checkpoints/github-candidate/` (`best.pt`, `last.pt`, `training-history.json`, `training-summary.txt`).
- Parent comparison checkpoint: `runs/github-symmetry/runs/github-selfplay/parent.pt`.
- Evaluation records and summary: `runs/github-symmetry/runs/github-evaluation/run-5e2990ff5c6f496c9fdf5f47949e695f/` and `runs/github-symmetry/runs/github-evaluation/evaluation-summary.txt`.

The copied workflow artifacts are under `runs/github-symmetry/`; absolute runner paths in their summaries refer to the temporary GitHub Actions workspace.
