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
- [ ] T042 — user selected candidate versus random100 and candidate versus parent100, alternating colours. User superseded wrapper design with disposable hardcoded candidate clone; Bunny replacement task dispatched; Luna prepares launch commands afterward. User runs/monitors, no games by agents.
- [x] T043 — collection helper --workers pass-through and metadata execution fields delivered; static checks reported passed, no parallel collection run.
- [x] T044 — manual four-worker GitHub Actions collection workflow and README instructions delivered. Bunny reports YAML/shell/static checks passed. No hosted runtime, commit or push yet.
- Outcome asymmetry across three exploratory seeds remains unexplained despite no obvious source bug; the milestone smoke passed but no conclusive bias diagnosis was performed. Further investigation is a user decision.
- Resume from [next-session.md](docs/next-session.md). No deferred implementation or experiment runs automatically.

## Resolved observed issues

I001–I006 are resolved. They covered an invalid EMPTY forfeit actor, incorrect recorded colour assignment, notification skip logging, contextual UTF-8 errors, overlapping archive planes, and a string/Path history join. The original failures and exact corrections remain in `GENERATIONS.md`; no open issue is inferred from untested paths.

## Observed compatibility correction

- [x] I007 — parallel worker initializer imports optional torch unconditionally, breaking random-only multi-core use in core-only installations. Luna source finding in work/parallel-review.md; Bunny corrected to inspect sys.modules after bot loads; focused initializer checks reported passed. No pool/game runtime.

## Current priority — 2026-10-01

1. Completed: prepared work and model pushed as 1e6e72f.
2. T041: prepare continuation support, then user-run conversion and second training on the completed 5,000-game collection (parent weights, new Adam).
3. After training, user-run local multi-core and GitHub proving runs. These runtimes remain unproven.

- T041a dispatched: --initial-checkpoint model-weights initialization with new Adam; no training/epochs by Bunny. Luna prepares concise conversion commands, no extra helper.

- T041 conversion completed by user: 4,000/1,000 games and 241,396/60,425 rows. Continued training remains pending trainer handoff and user launch.

- [x] T041a — trainer --initial-checkpoint weights-only initialization delivered; Bunny reports synthetic load/fresh-optimizer checks passed. Real parent checkpoint and training runtime still unrun. User launch command preparation is next.

- [x] T041 — user conversion and second training completed: parent weights/new Adam, best epoch1 at validationMSE0.193218, candidate checkpoints/second-model/run-selfplay-5000/best.pt. T042 playing-strength evaluation next decision; multi-core/GitHub proving runs remain deferred/unproven.

- T042a replacement completed directly per user: disposable nn_candidate_bot.py is canonical committed clone plus one hardcoded-checkpoint line. Parent unchanged, candidate shares NN-004 code ID; reports must distinguish checkpoint paths. No evaluation matches yet.

- T042 first match complete: candidate/random100 at86/5/9. Agreed parent/candidate100 remains to run.

- [x] T042 — user completed both100-game evaluations: candidate/random86/5/9; candidate/parent62/6/32. No additional matches or promotion agreed. Next previously agreed work: local multi-core and GitHub proving runs, still unrun.

- [x] T045 — user-run5,000 NN self-play games with workers4, second-model best.pt, seed90002, runs/selfplay-5000-second/. Compare actual timing to prior914.067s; next training conditional on satisfactory collection. No run by agents.

- [x] T046 — convert Generation004 collection and continue second-model best.pt with fresh Adam into separate third-model candidate; user-run commands, no jobs by agents.

- T046 conversion portion complete:241,586/60,343positions. Third-model training remains user-run/unstarted.

- Third-model training completed; playing-strength evaluation remains a next user choice. Disposable clone still points to second-model checkpoint; update one string before using it to evaluate third-model.

- [x] T047 — user-selected greedy evaluation option against random: disposable nn_eval_bot copy selecting latest third-model best.pt, random_moves0/temperature0; canonical self-play settings unchanged. Bunny task dispatched; no match yet.

- T047 delivered bots.nn_eval_bot (NN-EVAL-001-R0-T0), hardcoded third-model best.pt. Syntax/source checks reported passed; user-run100against random is ready but unrun.

- T047 greedy/random100 user run completed97/2/1. Third-vs-second evaluation remains unrun; further matches/experiments are user choices.

- [x] T048 — user selected100third-model vs second-model games, both R2/T0.05, alternating colours. Disposable candidate recreated from canonical with one checkpoint-line substitution to third-model best.pt; opponent env selects second-model best.pt. Command seed92002/ workers1, runs/third-model-vs-parent; not run yet.

- T048 user result63/4/33,100normal0forfeits. Further collection/training/evaluation decisions remain with user; hosted runtime still unrun.

- [ ] T049 — first hosted5000 latest-best selfplay -> conversion -> candidate training, download artifacts and exact parent, then local100candidate-parent. Bunny workflow-only extension dispatched; model copy prepared. No hosted job yet.
- [ ] T050 — later desired hosted1000candidate-parent evaluation and reports; design direction only, outside first hosted-run scope.

- T049 workflow implementation delivered; remote5000dispatch is next, using models/best.pt (third model), seed90003/workers4. No hosted1000evaluation.
