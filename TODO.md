# Tasks and issues

## Completed milestones

- [x] T001–T008 — engine scaffold, bot interface, runner and one-game smoke.
- [x] T012–T016 — schema-v1 record writer, I001 correction, sequential CLI, batch smoke and notification workflow. Batch colour failure I002 was reproduced and corrected; details remain in `GENERATIONS.md`.
- [x] T017–T021 — 1,000-game collection, schema replay/conversion and user-run 800/200 dataset smoke. See [collection-1000-review.md](docs/collection-1000-review.md) and [dataset-design.md](docs/dataset-design.md).
- [x] T022–T026 — CPU PyTorch setup, outcome MLP/trainer, first training run and learned-bot integration. The first failed training setup and its I006 correction remain recorded in `GENERATIONS.md`; successful result is [first-training-results.md](docs/first-training-results.md).
- [x] T027–T030 — deterministic max-bot scaffold and learned-bot/random matches. Reports: [max-bot-smoke-results.md](docs/max-bot-smoke-results.md), [nn-bot-smoke-results.md](docs/nn-bot-smoke-results.md).
- [x] T031–T033 — bot IDs, per-seat player lifecycle and NN opening integration. See [nn-opening-smoke-results.md](docs/nn-opening-smoke-results.md).
- [x] T034–T036 — weighted NN self-play and three fresh-seed runs; no stable seat advantage or bug was established. See [nn-selfplay-results.md](docs/nn-selfplay-results.md) and [nn-selfplay-seed-review.md](docs/nn-selfplay-seed-review.md).
- [x] T037–T038 — batched candidate inference and user-run timing. See [nn-batched-inference-results.md](docs/nn-batched-inference-results.md).
- [x] T039 — ignore local environments, caches, scratch data, runs, checkpoints and build artifacts.
- [x] Documentation cull — consolidated canonical architecture/workflow references and removed obsolete one-off prompts and handoffs; history and result reports retained.

## Deferred and open decisions

- [ ] T009 — parallel game execution.
- [ ] T010 — separate strength-evaluation mode without position logs.
- [ ] T011 — single-game HTML report.
- The user has not selected a next experiment. Temperature, architecture, learning method and any larger collection remain user decisions. Do not dispatch new work from this backlog without an explicit bounded task.

## Resolved observed issues

I001–I006 are resolved. They covered an invalid EMPTY forfeit actor, incorrect recorded colour assignment, notification skip logging, contextual UTF-8 errors, overlapping archive planes, and a string/Path history join. The original failures and exact corrections remain in `GENERATIONS.md`; no open issue is inferred from untested paths.
