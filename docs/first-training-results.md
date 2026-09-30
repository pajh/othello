# First CPU training run

Run: `checkpoints/first-model/run-2103bc51994e46a099f8b3d78618efd3/`. The saved split had 48,321 training rows from 800 games and 12,090 validation rows from 200 games. Settings were 30 maximum epochs, batch size 256, Adam learning rate 0.001, seed 12345, patience 3. Runtime was Python 3.14.7, PyTorch 2.14.1+cpu, NumPy 2.5.3, with 4 Torch threads and 4 interop threads.

Training stopped after four completed epochs at patience. Best validation MSE was 0.212422 at epoch 1, versus the constant training-target-mean baseline 0.235027, a 9.6% reduction; untrained validation MSE was 0.236017. Training MSE declined from 0.197927 after epoch 1 to 0.113117 after epoch 4, while validation MSE rose to 0.242892, consistent with overfitting after the first epoch. This is validation prediction only; it says nothing about playing strength.

The trainer reports 0.094 s loading and 2.252 s total wall time. Epochs took 0.289–0.314 s (about 0.30 s each). The wrapper reports 4.1 s for the subprocess plus its post-run artifact checks; the user estimated roughly 3 s perceived runtime. These timing boundaries differ and should not be compared as the same measurement.

`training-check.txt` reports PASS. Checkpoints are `best.pt` and `last.pt` in the run directory above; history and summary are retained beside them. This note reflects the saved summary/history and wrapper report only; no checkpoint was loaded for this review.
