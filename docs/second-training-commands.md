# Second training preparation

Run the dataset conversion from the project directory:

```sh
venv/bin/python -m training.convert --input runs/selfplay-5000/run-9ad69fb4e22d413c8905b2e392c33b36 --output-dir runs/selfplay-5000/run-9ad69fb4e22d413c8905b2e392c33b36/dataset --seed 12345
```

Conversion completed with 4,000 training games / 241,396 rows and 1,000 validation games / 60,425 rows. Conversion replays the recorded logs and may take longer than the training run. The user runs and monitors commands.

The training run completed. Its command used `--dataset-dir runs/selfplay-5000/run-9ad69fb4e22d413c8905b2e392c33b36/dataset`, `--output-dir checkpoints/second-model/run-selfplay-5000`, and the parent checkpoint `checkpoints/first-model/run-2103bc51994e46a099f8b3d78618efd3/best.pt`, with 30 epochs, batch size 256, learning rate 0.001, seed 12345, and patience 3. Results are recorded in [second-training-results.md](second-training-results.md).
