# Second training results

The run continued from the parent checkpoint's weights with a fresh Adam optimizer and no optimizer state carried over. It used 4,000 training games (241,396 rows) and 1,000 validation games (60,425 rows), with epochs=30, batch_size=256, learning_rate=0.001, seed=12345, and patience=3.

Starting validation MSE was 0.203582. The best result was 0.193218 at epoch 1, about 5.1% lower on the same validation split. Training stopped after four epochs when patience reached three, in 7.465 seconds. The final validation MSE rose to 0.209542. These results describe validation loss on this split and do not establish a strength improvement.

Saved artifacts: `checkpoints/second-model/run-selfplay-5000/best.pt`, `last.pt`, `training-history.json`, and `training-summary.txt`.
