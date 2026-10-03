# Generation016 hosted C8 training results

GitHub run [37110298551](https://github.com/pajh/othello/actions/runs/37110298551) completed in 7m22s. The retained artifacts agree across the run summaries, collection provenance, conversion summary, training history and evaluation records.

The collection used `NN-006-R2-T0.05-C8` in both seats, seed 90010, four workers, and `models/best.pt` as the parent input. It completed 5,000/5,000 games with 5,000 normal terminations and zero forfeits: bot 1 won 2,442, bot 2 won 2,423, and there were 135 draws. The collection CLI elapsed time was 270.338 seconds. The diversity summary and provenance report the same counts and seed.

Conversion split the 5,000 eligible games into 4,000 training and 1,000 validation games (split seed 12345), skipping no forfeits. Before augmentation, the splits contained 242,385 and 60,597 positions. Eight-way symmetry expansion produced 1,939,080 training rows and 484,776 validation rows. The conversion summary records actor planes unchanged and duplicates retained.

Training initialized weights from the supplied parent checkpoint with a fresh Adam optimizer. On this run’s fixed validation split, loaded-parent MSE was 0.187736; candidate best validation MSE was 0.186244 at epoch 1, an absolute reduction of about 0.001492. Training stopped after epoch 2 under patience 1; epoch 2 validation MSE was 0.187054. Total trainer time was 21.028 seconds. The candidate checkpoint is `runs/github-c8-second/checkpoints/github-candidate/best.pt`; `last.pt` is the final epoch and is not the best-validation checkpoint.

The 1,000-game evaluation used seed 190010, four workers, alternating colours and C8 on both seats. The candidate won 566, drew 15 and lost 419 against the exact parent, with zero forfeits. Its score was 57.35%. Both bots report ID `NN-006-R2-T0.05-C8`; the evaluation summary identifies the distinct weights by path: candidate `checkpoints/github-candidate/best.pt`, parent `runs/github-selfplay/parent.pt`. The retained evaluation run is `runs/github-c8-second/runs/github-evaluation/run-32aa9217d4fd41228cbc381320f0af4f/`.

These results support considering the best candidate weights for further C8 work: validation improved on the same split and the candidate scored above the exact parent in this seeded comparison. They do not establish an improvement for the greedy C deployment, because neither greedy-C play nor the new negamax configuration was evaluated here. No weights were promoted by this review.

Collection and conversion artifacts are under `runs/github-c8-second/runs/github-selfplay/run-807055a6f121446d94e1673078a927b6/`; training history and summary are under `runs/github-c8-second/checkpoints/github-candidate/`.
