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

- [x] T009 — four-worker parallel game collection requested; spec ready in docs/parallel-and-github-design.md. Bunny implemented CLI --workers (default1), spawn workers and parent ordered writing. Static checks reported passed; no game runtime yet. Focused Luna source review requested.
- [ ] T010 — separate strength-evaluation mode without position logs.
- [ ] T011 — single-game HTML report.
- [x] T040 — Luna prepared scripts/nn_selfplay_collect.py and docs/nn-selfplay-collection-handoff.md. User completed 5,000 normal games, zero forfeits; results summary requested from Luna.
- [ ] T041 — Convert new collection with whole-game 80/20 split, then second training batch in a fresh checkpoint directory. User selected continuing the existing best model weights on 2026-10-01; current trainer supports fresh initialization only, so a bounded Bunny change is needed first. User selected a new Adam optimizer; load model weights only. User executes, Luna reviews.
- [ ] T042 — Evaluate candidate separately; parent-versus-child checkpoint selection in one process is not currently supported. User chooses evaluation/design scope.
- [x] T043 — collection helper --workers pass-through and metadata execution fields delivered; static checks reported passed, no parallel collection run.
- [x] T044 — manual four-worker GitHub Actions collection workflow and README instructions delivered. Bunny reports YAML/shell/static checks passed. No hosted runtime, commit or push yet.
- Outcome asymmetry across three exploratory seeds remains unexplained despite no obvious source bug; the milestone smoke passed but no conclusive bias diagnosis was performed. Further investigation is a user decision.
- Resume from [next-session.md](docs/next-session.md). No deferred implementation or experiment runs automatically.

## Resolved observed issues

I001–I006 are resolved. They covered an invalid EMPTY forfeit actor, incorrect recorded colour assignment, notification skip logging, contextual UTF-8 errors, overlapping archive planes, and a string/Path history join. The original failures and exact corrections remain in `GENERATIONS.md`; no open issue is inferred from untested paths.

## Observed compatibility correction

- [x] I007 — parallel worker initializer imports optional torch unconditionally, breaking random-only multi-core use in core-only installations. Luna source finding in work/parallel-review.md; Bunny corrected to inspect sys.modules after bot loads; focused initializer checks reported passed. No pool/game runtime.

## Current priority — 2026-10-01

1. User-authorized commit/push of prepared work including model copy.
2. T041: prepare continuation support, then user-run conversion and second training on the completed 5,000-game collection (parent weights, new Adam).
3. After training, user-run local multi-core and GitHub proving runs. These runtimes remain unproven.
