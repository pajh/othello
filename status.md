# Project status

Updated: 2026-10-01.

- The end-to-end pipeline is implemented: rules/runner/record CLI, whole-game dataset conversion, CPU outcome model/trainer, and versioned bots. Canonical contracts: [project-plan.md](docs/project-plan.md), [batch-design.md](docs/batch-design.md), [dataset-design.md](docs/dataset-design.md), [first-model-design.md](docs/first-model-design.md).
- Current NN bot: `NN-004-R2-T0.05`, two uniformly random own moves then seeded weighted selection; candidate inference is batched. Model/checkpoint and training settings are documented. Temperature and model design remain starting choices.
- Latest user self-play run: seed 89014, 100 normal games, zero forfeits, bot 1/2/draw 52/46/2. CLI time 16.257 s (6.151 games/s); helper analysis elapsed 16.296 s. All 100 traces match the prior NN-003 run at the same seed. Against the user's approximate 23 s/100 baseline, this was about 29% less elapsed time; not a controlled benchmark. See [nn-batched-inference-results.md](docs/nn-batched-inference-results.md).
- Three retained NN-003 batches at seeds 89012/89013/89014 gave bot 1/2/draw 34/64/2, 36/59/5, 52/46/2. The outcome reversal does not establish a persistent seat bias. No new 5,000-game collection, parallel run or training has started. See [nn-selfplay-seed-review.md](docs/nn-selfplay-seed-review.md).
- The first 1,000-game random collection and 800/200 dataset split are retained under `runs/run-197b46d72b9447ebb2e315321400b3e8/`. The supervised first model trained for four epochs; best validation MSE was 0.212422 at epoch 1 versus constant baseline 0.235027. See [collection-1000-review.md](docs/collection-1000-review.md) and [first-training-results.md](docs/first-training-results.md).
- The installed OpenCode completion hook delivered a notice visibly while this chat was idle; active-turn delivery remains uncertain. Notifications were last recorded as enabled. See [notification-workflow.md](docs/notification-workflow.md).
- No coding task is active. Next experiment and any changes to model/bot settings remain the user's decision. Historical failures and corrections are in `GENERATIONS.md`.
