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

- [x] T049 — first hosted5000 latest-best selfplay -> conversion -> candidate training, download artifacts and exact parent, then local100candidate-parent. Bunny workflow-only extension dispatched; model copy prepared. No hosted job yet.
- [ ] T050 — later desired hosted1000candidate-parent evaluation and reports; design direction only, outside first hosted-run scope.

- T049 workflow implementation delivered; remote5000dispatch is next, using models/best.pt (third model), seed90003/workers4. No hosted1000evaluation.

- [ ] T051 — C bot/export/decompress/Makefile/combine plan prepared in docs/c-bot-plan.md, implementation not started. User explicitly requests200,000+position C/PyTorch parity comparison, user-run via Luna helper. Await CG protocol/size constraints and deployment setting; compression/precision remains a user choice.

- [ ] T052 — early C FP16 weight-storage experiment after FP32 parity: same weights rounded to binary16, decoded to float32 for C arithmetic; score/selection/size comparison plus user-chosen playing-strength comparison. Initial C design remains FP32. No experiment run.

- T049 remote stages complete: run36841281392 success and downloaded runs/github-first/. Local100candidate/exactparent remains to run; hosted1000evaluation still later stage.

- T049 local downloadedcandidate/parent100 complete54/4/42. Future hosted1000evaluation remains T050; no new job or promotion selected.

- [x] T053 — user-selected100greedy hostedcandidate vs random; disposable nn_eval_bot now selects downloaded hostedcandidate, ID NN-EVAL-002-R0-T0. Command prepared; no game launched.

- T053 user result100wins/0draws/0losses,100normal0forfeits. No further games launched.

- [x] T054 — random C bot c/bot.c and bots.c_random_bot stdin/stdout wrapper, make bot, one initial smoke, then user-run100 versus RAND-001 with no forfeits and roughly balanced performance. Manual CG submission after local success; neural headers/combine excluded from first deliverable.

- T054 implementation/one-game smoke complete; remaining: user-run100 versus RAND-001 (seed94001, workers1, runs/c-random-vs-random), then manual CG submission if satisfactory. Referee coordinate mapping confirmed; actual CG run unknown. Future Bunny tasks one deliverable at a time.

- [x] T055 — remove routine C stderr move/startup/pass chatter; retain real errors and move stdout. One-file Bunny task, build only.

- T054 complete: user clean local100 reported49–44, then actual CG run finished normally14–50 against BOSS1. Random C protocol proof of concept exercised locally and on CG. Neural forward/export/compression/combine remain separate future tasks.

- [x] T056 — standalone c/nn.h Model/Layer/setup/forward, current hardcoded architecture, c/test_nn.c random-data ASan/UBSan/leak smoke. No bot integration or production teardown. One bounded deliverable.
- [x] T057 — real model blob export/load and C/PyTorch comparison completed on10,000known replay-derived boards (superseded arbitrary random inputs). User run PASS, maximum absolute error2.38418579e-7, zero outside tolerance/nonfinite/range failures.

- [x] T057a — simple Python checkpoint exporter to model.bin and blob-layout.txt, fixed agreed tensor order/little-endianFP32; export hostedcandidate once and verify198148bytes. No C edits or numerical checks.

- [x] T057b — Python test CSV generator, run10,000known after-action boards from hosted validation dataset through matching hostedcandidate, CSV sanity check. Explicit user authorization to run this generator; C reader/comparison separate next task. Supersedes random-input corpus in T057.

- [x] T057c — C rig reads model.bin into Model.blob and real-board reference CSV, setup once/forward per row, tolerance1e-5absolute+1e-5relative, concise PASS/FAIL summary, sanitizer build. User-run10000comparison; no bot integration.

- T057c rig delivered and built cleanly; actual10000position C/PyTorch/sanitizer run remains user-run/unperformed. T057 overall numerical comparison still open.

- [x] I008 — observed C comparison host-check false rejection on x86_64: byte test reversed. Correct expected1.0f bytes to00/00/80/3f with4byte guard; rebuild, user reruns corpus.

- T057c runtime complete after I008 fix:10000/10000rows compared, mean error1.61441334e-8, max2.38418579e-7, PASS; user sanitizer-enabled execution showed no diagnostics.

- C submission constraint confirmed by user:100000source characters. Current FP32/FP16 raw-DEFLATE Base64/Base85 sizes exceed limit before C overhead. Compression codec/weight precision/text encoding choice remains open; do not implement oversized payload route without decision.

- [x] T058 — sklearn shared256center codebook for49537parameters, byteindices, reconstructedFP32blob and simple errors/sizes; then user10000board score comparison vs original CSV. Ctable decode separate next task. Model budget75000chars, code25000, hardtotal100000.

- T058 exporter/quantization complete; user10000board score-drift run remains pending. No adoption or Ccodebook decoder yet.

- T058 quantized10000board comparison user-complete:MAE0.000824199575/max0.00866732001,0invalidscores,9780strictFP32gate failures. Separate quantization acceptance/move-selection/playing-strength decision remains open; original parity gate retained.

- T058 deployment direction: prioritize actual quantizedbot strength, defer oversized-original comparisons unless diagnosing observed problem. Compression decision evidence: combinedpayload saves only2672Base64chars viaDEFLATE; uncompressed67416chars already within75000modelbudget. Recommend no DEFLATE; pending user choice, startup unmeasured.

- [x] T059a — Python emit uncompressedBase64 model.h from existingcodebook+indices, lengths and packed/expandedCRC32, simpleheaderdecode/reconstructionbytecheck and75000charbudget.
- [x] T059b — next separate authorizedtask afterT059a: CBase64decode/checkpayload, expandcodebookindices into FP32blob/checkCRC, bytecomparewith previousquantizedblob; same10000board results expected. No compression or botintegration yet.

- T059b Cdecode/reconstruction smoke complete:byteexactquantizedblob,bothCRCs/passcleanASanUBSan/leakcheck. FirstBase64padding arithmetic error fixed during observedcheck. User10000score rerun pending; no botintegration.

- [x] T060 — single-pass scripts/scrunch.py: replace mainquotedincludes withheadercontents, removequotedincludesinsidepastedheaders, stripcomments safely/nootherminification, character/bytecount andwarn100000. No recursion or neuralbotintegration. Mainmustlistalllocalheadersinorder.

- T060 delivered:currentrandomsubmission3816chars,3header scratchcheck81486chars/zeroquotedincludes/compiled. Actualbotstillrandom. GCCO3inline prefix recommendation researched; injectionnotimplemented, CPUtargetselectionopen.

- [x] T061 — wire quantizedembeddedNN into bot.c greedyfromstart; CGboard/candidateflips/actorplanes/forward, startupmodelonce, gccbuild/onesmoke. No header/wrapper/scrunchchanges in thisBunnytask.

- [x] T062 — prependO3inline in scrunch, generateactualneuralCGsubmission/count and compileexactfilewithGCC. Wrapperidentityfixseparate.

- T062 finalneuralCGsubmission88256chars/bytes,11744belowlimit, exactGCCbuildclean. ActualCGneuralrunpending; localwrapperidentitystillstale.

- [x] T063 — scrunch removesnewlineonlyforcomment-bearinglineswithnocode; preservesoriginalblanklines/codewhitespace/literals. Regenerateactualneuralfile/count/exactGCCcompile.

- [x] I009 — observedremainingcommentblankblocks:markeachlineconsumedinblock_comment ascomment, notonlyopeningline. Regenerateandinspectactualfilehead/size/compile; preserveintentionalblanklines.

- [x] T064 — single current commandguide for allscripts/tools: localmulticorecollection/conversion/training/evaluation, GitHubdispatch/download, NNblob/codebook/header/tests/GCC/scrunch/CGsubmission. Verifyflagsagainstactualsource, linkREADME/index.

- [x] T065 — optional eight-way board symmetry expansion after whole-game split, training and validation independently.
- [x] T066 — hosted 1000-game R2/T0.05 candidate-vs-exact-parent evaluation, summaries/logs/artifact inclusion; enable symmetry conversion and patience1.
- [ ] T067 — promote latest hosted candidate to repository models/best.pt, full commit/push, dispatch 5000-game four-worker hosted training/evaluation with fresh seed90004. User authorized.
