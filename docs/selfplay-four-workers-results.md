# Four-worker self-play results

The user-run collection completed all 5,000 games normally with zero forfeits. Both seats used `NN-004-R2-T0.05` and `checkpoints/second-model/run-selfplay-5000/best.pt`, with master seed 90002. The run requested and used four workers with one numerical thread per worker. Bot 1 won 2,459 games, bot 2 won 2,369, and 172 were draws; each seat had Black for 2,500 games. The seed derivation and saved CLI summary were checked successfully.

CLI elapsed time was 249.131 seconds; the user's approximate fish wall-clock was 250 seconds. The previous 5,000-game collection took 914.067 seconds by CLI, so the observed CLI-time ratio is about 3.67×. This is a practical comparison, not a controlled speed benchmark: the seed, checkpoint, and game traces changed, and the fish wall-clock timing scope differs from the CLI timing.

Diversity measurements are descriptive only: there were no duplicate full action traces; 4,815 distinct first-eight-action prefixes, and three distinct shared late-position keys across six of 241,935 late rows. These counts make no claim that examples are independent. Local multi-worker runtime was exercised successfully. GitHub Actions has not been run.

Reports and raw game records are under `runs/selfplay-5000-second/`; the run is `runs/selfplay-5000-second/run-4930cc31f42e4534a4feaf919d672a78/`.

To convert this run into a dataset with seed 12345 and the default 80/20 whole-game split, run from the project root:

```sh
venv/bin/python -m training.convert --input runs/selfplay-5000-second/run-4930cc31f42e4534a4feaf919d672a78 --output-dir runs/selfplay-5000-second/run-4930cc31f42e4534a4feaf919d672a78/dataset --seed 12345
```
