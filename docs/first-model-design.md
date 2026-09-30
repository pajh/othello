# First outcome model and training baseline

The first supervised pipeline is a measured baseline, not an assumption that iterative self-play improves strength.

## Representation and model

- Input is dataset encoding version 1: binary own/opponent planes `(N, 2, 8, 8)` from the acting player's perspective, after an accepted action. Convert to float32 and flatten in C order, own plane followed by opponent plane; no added features, scaling or augmentation.
- `OutcomeMLP` is `128 -> 256 -> 64 -> 1`, ReLU after each hidden layer and sigmoid output, with biases. It has 49,537 trainable parameters. No dropout, normalization or residual connections.
- Output in `[0, 1]` estimates expected recorded outcome `P(win) + 0.5 * P(draw)`; 0.5 does not imply a likely draw. Targets map -1/0/+1 to 0/0.5/1.
- Checkpoints identify architecture and encoding versions; inference loads the selected checkpoint once and uses a read-only evaluation model.

## Agreed initial training settings

Mean squared error, Adam learning rate 0.001 with other defaults and no weight decay, batch size 256, seed 12345, maximum 30 epochs, and patience 3 epochs without a strictly lower full-validation mean loss. Keep the best-validation checkpoint and the latest epoch checkpoint. Shuffle training rows each epoch; validation is not used for gradients. No scheduler, augmentation or parameter sweep.

These settings produced one user-run baseline: four epochs completed, best epoch 1 validation MSE 0.212422 versus constant baseline 0.235027; validation worsened after epoch 1 while training loss fell. The selected `best.pt` is retained under `checkpoints/first-model/run-2103bc51994e46a099f8b3d78618efd3/`. See [first-training-results.md](first-training-results.md) for timing and full results.

The current inference bot scores after-action candidate boards from its own perspective. Its settings and later batched-inference measurements are recorded separately in the bot/match result documents. Prediction loss and playing strength are distinct. The model and temperature are starting choices, not measured optima.
