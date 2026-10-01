# Third training run

This continuation initialized from the second model's `best.pt` using a fresh Adam optimizer and the recorded settings: 30 maximum epochs, batch size 256, learning rate 0.001, seed 12345, and patience 3. It used 241,586 training rows from 4,000 games and 60,343 validation rows from 1,000 games.

On this run's validation split, initial MSE was 0.199267. The best checkpoint, `best.pt`, was selected at epoch 1 with validation MSE 0.186284, about 6.5% lower than the initial value on the same split. Training stopped after four epochs by patience, in about 7.1 seconds. Training loss continued to fall while validation loss rose after epoch 1, indicating later train/validation divergence.

This records validation fit only; it makes no claim about playing strength. Losses should not be compared across different validation datasets.
