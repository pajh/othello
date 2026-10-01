# Project status

Updated: 2026-10-01.

- The end-to-end pipeline is implemented: rules/runner/record CLI, whole-game dataset conversion, CPU outcome model/trainer, and versioned bots. Canonical contracts: [project-plan.md](docs/project-plan.md), [batch-design.md](docs/batch-design.md), [dataset-design.md](docs/dataset-design.md), [first-model-design.md](docs/first-model-design.md).
- Current NN bot: `NN-004-R2-T0.05`, two uniformly random own moves then seeded weighted selection; candidate inference is batched. Model/checkpoint and training settings are documented. Temperature and model design remain starting choices.
- Latest user self-play run: seed 89014, 100 normal games, zero forfeits, bot 1/2/draw 52/46/2. CLI time 16.257 s (6.151 games/s); helper analysis elapsed 16.296 s. All 100 traces match the prior NN-003 run at the same seed. Against the user's approximate 23 s/100 baseline, this was about 29% less elapsed time; not a controlled benchmark. See [nn-batched-inference-results.md](docs/nn-batched-inference-results.md).
- Three retained NN-003 batches at seeds 89012/89013/89014 gave bot 1/2/draw 34/64/2, 36/59/5, 52/46/2. The outcome reversal does not establish a persistent seat bias. The first 5,000-game collection is complete; no parallel run or new training has started. See [nn-selfplay-seed-review.md](docs/nn-selfplay-seed-review.md).
- The first 1,000-game random collection and 800/200 dataset split are retained under `runs/run-197b46d72b9447ebb2e315321400b3e8/`. The supervised first model trained for four epochs; best validation MSE was 0.212422 at epoch 1 versus constant baseline 0.235027. See [collection-1000-review.md](docs/collection-1000-review.md) and [first-training-results.md](docs/first-training-results.md).
- The installed OpenCode completion hook delivered a notice visibly while this chat was idle; active-turn delivery remains uncertain. Notifications were last recorded as enabled. See [notification-workflow.md](docs/notification-workflow.md).
- Session resumed: T040's user-run 5,000-game collection/check helper is ready: scripts/nn_selfplay_collect.py, default seed 90001, retained parent checkpoint provenance. Luna reports syntax/help/AST/diff checks passed; game runtime is unverified. User completed 5,000 normal self-play games, zero forfeits, 2,397/2,424/179 bot1/bot2/draw; CLI elapsed 914.067s. Artifacts: runs/selfplay-5000/run-9ad69fb4e22d413c8905b2e392c33b36. Luna saved-report summary requested. No training has started. User selected continuing the existing best model weights for the second training batch; a bounded Bunny trainer change is needed before training. User selected a new Adam optimizer; load model weights only. Artifact locations and OpenCode recovery instructions are in [next-session.md](docs/next-session.md). Historical failures and corrections remain in `GENERATIONS.md`.

- While collection runs, user requested a four-core workflow and GitHub Actions collection. Design prepared in [parallel-and-github-design.md](docs/parallel-and-github-design.md); implementation, remote runs and checkpoint upload remain unperformed.

- User authorized Bunny T009 multi-core CLI implementation; dispatch in progress. gh confirmed pajh/othello PUBLIC. Selected baseline copied to models/first-model.pt with a narrow ignore exception for future GitHub checkout; no commit/push performed.

- T009 CLI multi-core implementation delivered (src/rig/cli.py, src/rig/parallel.py). Bunny reports syntax/import/help checks passed; no games or timings run. Focused Luna source review requested; T043 helper pass-through is next dispatch. Completed collection summary: docs/selfplay-5000-results.md.

- T043 delivered: helper accepts --workers and reports recorded execution fields; static checks reported passed, no parallel runtime. Luna found I007 (unconditional optional torch import in workers); narrow correction is next dispatch before T044.

- I007 corrected: optional torch is inspected after bot imports, then thread limits set if present. Bunny reports focused initializer checks passed; real NN worker/pool runtime unrun. T044 GitHub-hosted collection workflow dispatched, no hosted execution/commit/push.

- T044 delivered: .github/workflows/selfplay.yml, manual collection on ubuntu-24.04 with four workers and models/first-model.pt, downloadable artifact and job summary. Bunny reports YAML/shell/static checks passed. Workflow/dependencies/pool/artifact upload remain unrun on GitHub; no commit/push. Next hosted step is user-authorized commit/push, then user-run dispatch with chosen seed/count.

- Priority set by user: commit/push all prepared changes, then convert the retained 5,000-game collection and train from parent weights with fresh Adam. Local multi-core and hosted proving runs are deferred until after this training; both remain unproven.
