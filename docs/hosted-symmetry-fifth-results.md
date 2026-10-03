# Hosted symmetry fifth results — Generation 012

GitHub Actions run [37013882628](https://github.com/pajh/othello/actions/runs/37013882628) completed successfully. Its downloaded artifact is retained at `runs/github-symmetry-fifth/selfplay-37013882628-1/`. This is a fresh continuation from the retained Generation010 checkpoint; it did not use Generation011's candidate.

## Collection and conversion

- Parent checkpoint: `runs/github-symmetry-fifth/selfplay-37013882628-1/runs/github-selfplay/parent.pt` (copied from the selected `models/best.pt`, Generation010).
- Both self-play seats used `NN-004-R2-T0.05` (`bots.nn_bot`), 5,000 games, master seed 90008, alternating colours, four workers, one pinned numerical thread per worker. The collector completed 5,000 normal games with zero forfeits: bot 1 won 2,381, bot 2 won 2,496, and 123 were draws. Collection CLI elapsed time was 327.583 seconds.
- Whole-game 80/20 split, seed 12345, followed by eight-way symmetry expansion. Conversion produced 1,938,896 training positions from 4,000 games and 484,752 validation positions from 1,000 games. Forfeits skipped: zero. Details: `runs/github-symmetry-fifth/selfplay-37013882628-1/runs/github-selfplay/conversion.log` and `.../run-83b7527983394b0582ff04c555742f4c/dataset/`.
- Descriptive diversity counts: zero duplicate complete action traces; 244 unique first-four-action prefixes among 5,000 games, 4,899 unique first-eight prefixes, and 4,999 unique first-twelve prefixes among 4,999 games. These do not establish statistical independence. Full report: `runs/github-symmetry-fifth/selfplay-37013882628-1/runs/github-selfplay/diversity-summary.txt`.

## Training and evaluation

Training continued from Generation010 parent weights with a fresh Adam optimizer, CPU, seed 12345, batch size 256, learning rate 0.001, maximum 30 epochs, patience 1. The initial validation MSE was 0.193386; best was epoch 1 at 0.192354. Training stopped after two epochs and 29.350 seconds. The candidate is `runs/github-symmetry-fifth/selfplay-37013882628-1/checkpoints/github-candidate/best.pt`; the exact parent copy is under `runs/github-symmetry-fifth/selfplay-37013882628-1/runs/github-selfplay/parent.pt`.

The candidate scored 507 wins, 22 draws, and 471 losses against that retained Generation010 parent in 1,000 alternating-colour games (seed 190008, four workers, zero forfeits), or 51.8% by `(wins + 0.5 × draws) / games`. This is a modest observed edge and does not establish a playing-strength improvement. Generation011's 48.8% result came from a different candidate trained from the same parent; the two batches do not establish that either candidate is stronger or that results are trending.

Evaluation report: `runs/github-symmetry-fifth/selfplay-37013882628-1/runs/github-evaluation/evaluation-summary.txt`; full game summary: `.../runs/github-evaluation/run-summary.txt`. Candidate training report: `runs/github-symmetry-fifth/selfplay-37013882628-1/checkpoints/github-candidate/training-summary.txt`.
