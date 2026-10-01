# First hosted collection and training results

GitHub Actions run [36841281392](https://github.com/pajh/othello/actions/runs/36841281392) completed successfully on commit `669a1fd296526e19663fee27cf026b697d7f04f5` (`master`). The workflow job took about 4m14s including setup; the collection CLI itself took 161.608 seconds.

## Collection

The run collected all 5,000 requested self-play games with `NN-004-R2-T0.05` in both seats, master seed 90003, alternating Black assignments, four requested and effective workers, and one pinned numerical thread. All 5,000 terminated normally; there were no forfeits. Bot 1 won 2,377, bot 2 won 2,444, and 179 were draws. Seed derivation and consistency between the CLI summary and game records were reported verified. The diversity report found no duplicate full action traces; its other overlap counts are descriptive only and make no independence claim.

Collection source artifacts are `runs/github-selfplay/run-a618633805de46679deccb20377b348a/metadata.json` and `games.jsonl` (run ID `16d5145aefcc451f9a97025563bf7d94`). The run directory also contains `collection-provenance.json` and the converted dataset.

## Conversion and training

Conversion used all 5,000 games (zero skipped forfeits), producing 302,313 positions. The fixed split (seed 12345) assigned 4,000 games / 241,811 positions to training and 1,000 games / 60,502 positions to validation.

Training initialized from the parent weights at `models/best.pt`, using a fresh Adam optimizer and the current settings (30 maximum epochs, batch size 256, learning rate 0.001, seed 12345, patience 3). On this same validation split, the loaded parent weights had validation MSE 0.205014; the best candidate was epoch 1 at 0.198206. The constant baseline was 0.240008. Training stopped after epoch 4 for patience; each epoch took about 0.978 seconds and total training time was 5.693 seconds. Final epoch training MSE was 0.153492 while validation MSE rose to 0.215063, so the retained candidate is `best.pt`, not `last.pt`.

Hosted artifacts: `runs/github-selfplay/run-a618633805de46679deccb20377b348a/dataset/{training.npz,validation.npz,conversion-summary.txt}` and `checkpoints/github-candidate/{best.pt,last.pt,training-history.json,training-summary.txt}`. The workflow copied the exact parent checkpoint to `runs/github-selfplay/parent.pt`; candidate and parent checkpoints are preserved separately. These loss results describe this dataset split and do not establish a playing-strength change. A local parent-versus-candidate match has not yet been run.
