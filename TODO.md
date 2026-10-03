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
- [x] T067 — promote latest hosted candidate to repository models/best.pt, full commit/push, dispatch 5000-game four-worker hosted training/evaluation with fresh seed90004. User authorized.

- [x] T068 — retrieve full Generation008 hosted artifact and summarize actual symmetry training/1000-game parent evaluation. Candidate adoption/export remains user decision.

- [x] T069 — promote Generation008 candidate, dispatch next hosted round seed90005, quantize/embed/scrunch/compile new CGsubmission for user paste.

- [x] T070 — retrieve/summarize second symmetry-hosted round, preserve candidate/parent/reports; record userCG17thWood2. Further adoption/CGrefresh/experiment awaits user selection.

- [x] T071 — push Generation009candidate asbest and dispatch unchanged hosted5000/1000 round seed90006; CGrebuild deferred.

- [x] T072 — retrieve third symmetryround/results and agreedaftermeal rebuildCGsubmission from newcandidate; bytecheck/compile/onegame complete, userCGsubmissionnext.

- Open decision (2026-10-02): opening-book source, character budget, coverage/handoff and deployment-only versus training use. User reports #1 Wood2 below BOSS. Current source leaves12225characters; preserve current R2/T0.05 self-play until user selects a change. Discussion only, no implementation task allocated.

- Agreed design direction2026-10-02: C-only opening lines encoded as0..63square indices, symmetry-aware history-prefix lookup and NN fallback. Decide source/continuations before bounded implementation.
- Idea (not agreed implementation): Python bots might later sample randomly from a3–4move opening book; current R2/T0.05 training/evaluation remain unchanged.

- T073 — Edaxbookgenerator6broad/8total: userselected locallevel14 process/outputcheck before hostedlevel38. OpenCode implementationdispatch prepared; onlygenerator/handoff, noanalysisruns. Runtime~1minuteistargetnotmeasurement; hostedworkflow/jobseparateafterreview.

- T073 cancelledbyuser after~5minutes Edaxsourceinvestigation; no scripts/generate_edax_book.py or generatorhandoff exists. Scope was too broad. Prepared narrowerT073a docs/edax-query-task.md: one sequentialquery, knownexistingbookprecondition, nohistoricalstartupresearch/source-reading/concurrency. Notdispatched; fullgenerator remainsdeferred.

- UserreplacesT073combinedplanwith3stages: prefixenumerationonly, Edaxreplyaddition, narrowextension. T073bprepared docs/opening-prefix-task.md: alllegal0..depthinclusive comma-separatedhistories; noEdax. Querytaskdeferred. Own-policyfilteringandfourtransformencoding remainlaterwork.

- T073b complete: scripts/generate_opening_prefixes.py and docs/opening-prefix-handoff.md delivered. Sourceinspectionconfirmsengine-basedDFS/all0..depthinclusive/comma-separatedhistories. OpenCodereportsdepth2check17legaluniquerows and guards passed; primary didnotrerunchecks. Depth6user-runpending; noEdaxquery/generation.

- T074 userauthorizesexistingprefixfilefour-symmetryreduction; task docs/opening-symmetry-task.md, separatecanonicalfile/inputpreserved. Expected2479rowsincludingempty. OpenCodeimplementationdispatch; fullreductionuser-run.

- T074complete: scripts/canonicalize_opening_prefixes.py and docs/opening-symmetry-handoff.md. OpenCodereportssyntheticempty+4openingcheck->2rows, idempotence/passchecks andoutputrefusalpassed; observedtransformpair/indexbugfixed. Full9913->2479reductionuser-runpending; noEdax/policyfilter.

- T075 authorized: evaluatefull2479canonicalprefixfile, parameterizedcores/depth; persistent1threadEdaxworkerscontiguousDFS chunks/undo+suffix replay/orderedstitch. No culling/extension/workflow. Firstuser-runcores4/level10target20–40s(unmeasured); hosted38laterafterreview. Task docs/edax-evaluation-task.md.

- T075deliveredandstubcheckspassedperOpenCode; primaryreviewcaught0.25squietwaitperprompt (~155sminimumfor2479hintprompts/4workersplusnavigation). T075anarrowfixdispatchedbeforeuser-run. Mode3correction accepted: originaltaskmode0wouldautoplayWhite. NoactualEdaxbatchyet.

- T075acomplete: quiet0.25spromptwaitremoved; terminalbare>ornewline>predicate. OpenCodereportssplitpipechecks0.050/0.100secondsandparse/stub/syntaxpass; noEdaxexecution. Useractualcores4/depth10runpending.

- T076authorized: evaluatorearlyfeedback10/12.5/15minutes, perworkerETA,total>5hthreeconsecutivechecks→stop;5helapsedcap;retaincompletedpartialanalyses,noautomaticdepthchange. Task docs/edax-runtime-limit-task.md. LocalLunaoutputcheckpassed docs/edax-local-results.md. NohostedEdaxworkflow/runyet.

- T076completeperOpenCode: earlyperworkerchecks/threebreachesstop/hardcap/atomicpartials/summaries;syntheticpass,noEdaxrun. Primaryreviewcompleted. T077hostedworkflowtaskprepared; primarycopiedcanonicalinputandvalid84bytestartupbook to data/opening-book/. Nojob/commit/push yet.

- T077complete: manual .github/workflows/edax-book.yml plus docs/edax-hosted-handoff.md. Primarysourceinspectionconfirmsretainedinput/startupbook/pinnedEdax/4workers38/defaultETA+hardcap/alwaysartifactuploads. OpenCodestaticchecksreportedpassed;nohostedruntimeyet. Requiredworkflow/evaluator/dataassets stilluntracked; explicitcommit/push/dispatchapprovalrequestedbeforelaunch.

- T078userselectsexactterminalendgameminimaxinPythoncanonicalbot, configurableCOUNT_LEFT/default0; proposedactivationempty<=cutoff,terminalWDLobjective/noNNleaves, deterministicbestwithfirstties. OpenCodetask docs/nn-endgame-task.md. Laterzeroequivalenceand8or10vs0user-run; noevaluation/traininglaunch. IDchangesaffectrigRNGseeds; equivalenceusesmatchedRNGstreams.

- T078complete: canonicalNN005-R2-T0.05-C0 terminalnegamax/alphabeta/forcedpasses,COUNT_LEFTdefault0/<=activation. OpenCodereportsfocusedreference/bypass/settingscheckspassed; primarysourceinspectiondone,noactualgames. Lunauser-runonegameC0equivalencehelperdispatched, compareNN004sourcefrom07ed0aevsNN005withsamecheckpoint/explicitper-seatRNGstreams; no8/10matchyet.

- User-authorized level-34/four-worker Edax retry committed/pushed a18b453 and dispatched https://github.com/pajh/othello/actions/runs/37027471923; observed in_progress. Same retained 2479 prefixes, checks at 10/12.5/15 minutes, five-hour estimate/hard limits. Results pending; no automatic depth reduction or book adoption.

- User-run NN C0 equivalence passed: seed97001/models/best.pt, NN-004-R2-T0.05 versus NN-005-R2-T0.05-C0, 61 plies, 61 stateful and 61 greedy comparisons with matched RNG streams; terminal White41–23. This establishes unchanged choices/RNG on this one game with solver disabled; C8/C10 strength comparisons remain unrun.

- T079 authorized: disposable C6/C8/C10 snapshots of canonical NN005 and existing-runner commands for 100-game strength/runtime comparisons, C0 baseline and optional both-seat C8 throughput. Same selected weights/R2/T0.05; no games/jobs/training launched. Scope docs/nn-cutoff-comparison-task.md; OpenCode implementation delegation.

- T079 complete: disposable NN005 C6/C8/C10 snapshots and docs/nn-cutoff-comparison-handoff.md delivered. OpenCode reports py_compile/diff checks passed; primary reviewed C8 diff and existing-runner commands. All use required checkpoint environment, unchanged R2/T0.05. C0 equivalence passed earlier; cutoff strength/runtime batches and both-seat self-play timing remain user-run/unrun.

- User completed C8-versus-C0 comparison: same models/best.pt (selected Generation010),100games,seed98008,fourworkers,alternatingcolours; C8 won65–35,0draws/forfeits, user shell walltime8.33s. Raw runs/nn-c8-vs-c0/run-7b28c26eeab344618124900f8acce5b8/. C0/C0 baseline also saved:100normal,44/2/54,seed98000,raw runs/nn-c0-vs-c0/run-c66a971b32c54887ae8b524d93e2c591/; summary has no elapsed field,baseline walltime not supplied here,so slowdown ratio unquantified. C8/C8 throughput and C10 comparisons remain unrun; no canonical cutoff change/training launch.

- User-run both-seat C8 throughput:100games,seed98008,fourworkers,models/best.pt,R2/T0.05;100normal,0forfeits,56/3/41 seat outcomes,wall8.26s,userCPU31.65s. Raw runs/nn-c8-vs-c8/run-6ae57e99b2e54bddae1142d960eb1ff2/. Simple same-machine 5000-game extrapolation8.26*50=413s(~6m53s), includes repeated startup in extrapolation and is approximate. Similar walltime to single-seat C8 batch8.33s; baseline slowdown percentage unknown. No training/hosted job or cutoff adoption authorized by this result alone.

- User explicitly selected Generation012 best as new models/best.pt and canonical C8 for hosted5000 self-play/training plus1000 C8candidate-vs-C8exactparent evaluation. Commit040e249 pushed; run https://github.com/pajh/othello/actions/runs/37030679887 observed in_progress,collectionseed90009/evaluationseed190009/workers4. Canonical nowNN-006-R2-T0.05-C8; conversion8symmetries,continuedweights/freshAdam/patience1 unchanged. Edax level34 run37027471923 concurrently active. Results pending; Cdeployment weights unchanged. Earlier comparison commands using canonical as C0 are now historical because canonical is C8; use retained revision for future C0 comparisons.

- Generation015 hosted37030679887 failed AFTER all5000 games completed normally0forfeits (2429/130/2441,~503s collection). Observed error: helper hardcoded BOT_ID NN004R2T0.05 rejects actualNN006R2T0.05C8; conversion/training/evaluation skipped. Artifact upload succeeded; retrieval runs/github-c8-first/. T081 narrow helper-ID fix delegated; raw provenance incorrectly embeds old ID and must remain honest, no candidate trained.

- T081 verified one-line collector BOT_ID fix, committed/pushed aa173e0. Generation015 retry https://github.com/pajh/othello/actions/runs/37032114143 observed in_progress; same selectedGeneration012best/C8/5000games/seed90009/workers4 and1000evalseed190009, other training settings unchanged. Fresh collection rerun; initialfailedartifact preserved runs/github-c8-first/. No candidate/results yet.

- T082 user-requested identity flow correction authorized: canonical get_id() supplies new collection provenance; saved metadata/provenance supplies reviews/reports; workflow evaluation report reads actual IDs instead of duplicating hardcoded names. Keep consistency checks and distinct checkpoint provenance. Bounded OpenCode task docs/nn-identity-flow-task.md; active hosted retry unaffected.

- T082 complete/reviewed: collector now reads canonical get_id() after checkpoint setup for launch provenance, retained metadata IDs for review/reports, requires same-seat IDs and provenance agreement. Hosted eval summary parses recorded IDs; no duplicated fixed ID remains. OpenCode reports synthetic identity/mismatch/history/parser/help/syntax checks passed; primary diff inspection done. Changes local/uncommitted, active37032114143 uses its prior checked-out revision; no games/jobs launched by T082.

- Generation015 retry37032114143 succeeded; downloaded runs/github-c8-retry/.5000normal/0forfeits,2429/130/2441,collection510.154s. Candidate bestepoch1MSE0.176499 vs loadedparent0.179488 on samevalidation split;2epochs/patience1,training29.581s.1000 C8candidate-vs-C8Generation012parent seed190009:560wins/37draws/403losses,57.85%score,0forfeits. Newcandidate runs/github-c8-retry/checkpoints/github-candidate/best.pt; exactparent runs/github-c8-retry/runs/github-selfplay/parent.pt. Evidence supports improved weights underC8; C0/greedy/Cdeployment improvement not measured. No promotion/export/newjob.

- User-requested latest Generation015 C model rebuild completed via Luna existing tooling. Prior assets archived runs/c-generation010/. New submission runs/c-submission/submission.c87775chars (12225headroom),SHA256a4a028ad702c67e39410877448de636d878d3afe0a6fa5c33d7c7749c07979e6; GCC buildclean,embedded quantized reconstructionbyteidenticalPASS,leakdetectiondisabledforpriorptracelimitation. QuantizationMAE0.00142061329/max0.02498734. One seed96003smokevsrandom normal0forfeits/Cwin runs/c-generation015-smoke/run-7d975b742cbc469891482431db13e812. Csource greedy unchanged/no minimax/book yet; no checkpointpromotion/commit/push/CGsubmission. Handoff docs/c-generation015-handoff.md.

- T083 user-authorized isolated Z85 encoding trial: existing C probe hashes currentBase64 and trialZ85 decodedpayload/FP32blob; binarylength/hash/byteidentity successcriterion; compile trialsinglefile and measure complete source net savings. Preserve productionBase64/currentsubmission; no model change, games, jobs or promotion. Task docs/z85-encoding-test-task.md delegated OpenCode.

- T083 isolatedZ85trial completed: decodedtruepayload50561bytes and expandedFP32blob198148bytes identical to Base64/reference (CpayloadCRC bce3a986,decodedCRC2205bf07,cmpPASS). Trialcomplete source runs/c-z85-test/z85/submission.c83574chars vs87775baseline,net4201saved,16426headroom (6426after hypothetical10000charbook). OpenCode reports cleancompile andASan/UBSan; primaryhandoff/trigraphfixreview done. Real C11trigraph??!caught in Z85literal; generator splits adjacent literals betweenquestionmarks to preservebytes (7char overheadincluded). ProductionBase64paths unchanged; trialnotadopted,no game/modelchange/commit/push. Handoff docs/z85-encoding-test-handoff.md.

- T084 user-authorized Z85 productionpromotion/removalofactiveBase64modelencoder/decoder plus read-only whitespace/privateidentifier savingsestimate; OpenCode boundedtask docs/z85-promotion-task.md. PreserveBase64archives/modelweights; no minimification/renaming or jobs/commit/push.

- T084 reported complete: canonicalZ85codec replacesBase64,tests/pass/smoke; regeneratedsubmission83566chars(net4209vsBase64),read-onlywhitespaceestimate5282chars. ArchivedBase64 runs/c-base64-final/. No cleanup applied/commit/push. T085 user explicitly requests Luna implementation: attributedEdaxportable scalar legalmovegeneratoravailableinCbot,maskverification/scrunch/exactsize; nosearch/flipper/choicechange.

- T085 Luna completed attributedEdax4.6 scalar one-stageparallelprefix legalmoves: staticinline u64valid_moves(u64mine,u64theirs),typedefuint64_tu64; C VERSION004. No NNchoice/search/flipperchanges. Enginecomparison4004maskPASS (explicitedges,longrays,nomoves +32seededtrajectories/1999positionsbothplayers). makebot/exactsubmissionGCCclean; submission84767chars vs83566(+1201),headroom15233;5233afterhypothetical10000book. Priorretained runs/c-bitboard-moves/prior-submission.c. Handoff docs/c-bitboard-moves-handoff.md; no game/CGsubmit/commit/push. Primarysource/sizeinspection done.

- User-requested flipperinvestigation complete docs/c-flipper-investigation.md. EdaxAVX2ppseq7791comment-strippedchars(includes5777masktablechars),BMI2 11301plussharedMASK_X; other scalarfastvariants52436–137239chars. Tinyflip_slowreferencefunction670charsbeforeadaptation. Recommend table-free scalarpropagationestimated1–2KB,measurebeforeSIMD; no implementation/benchmark/CPU capabilityclaim. Currentafter10Kbook budget5233beforewhitespacecleanup.

- T086 user selects compactscalarbitboardflipper,explicitLunainsertion/enginecomparison; futureOpenCodenegamax and user-runcutoffmeasurements separate. Allowed c/bot.c+docs/c-scalar-flipper-handoff.md andgeneratedartifacts. Userprefersendgameclosingoverbookspacepriority; no search/strategyintegration/game/leaguegainclaim yet.

- T086 Luna completed portabletable-free scalarcoordinate-ray flip_discs(u64mine,u64theirs,intsquare),returnsflips/noboardmutation;C VERSION005,chooserunchanged. Engineflipmask/resultboardchecks31172PASS across32seededtrajectories+targetededge/corner/diagonal6disc/multiraycases. makebot/exactsinglefileGCCclean. Submission85648chars(+881),headroom14352;4352afterhypothetical10000bookbeforewhitespacecleanup. Priorarchive runs/c-scalar-flipper/prior-submission.c; handoff docs/c-scalar-flipper-handoff.md. No search/game/throughputbenchmark/CGsubmit/commit/push; speedunknown. Primarysize/sourceinspection done.

- T087 authorized2026-10-03: commit/push prepared work, continue Generation015best via hosted5000/1000 round seed90010/190010 with unchangedC8 training settings. Dispatch/results pending.
- T088 authorized: OpenCode C terminal-only negamax, save NN fallback and respect remaining turn time; Luna focused review. Activation cutoff pending user selection. No opening-book review/integration or minification in this chunk.

- T087 localcommit18ee53a completed2026-10-03 with explicit inspectedfile staging; Python syntax and gitdiffchecks passed. Push/GitHubdispatch remain unrun: automatic approval rejected unrestrictedstaging+masterpush; user asked to explicitlyapprove origin/masterpush and configuredrun. Cnegamax draft work/c-negamax-task-draft.md prepared only; activation/time settings pendinguserselection, no OpenCodeimplementation dispatched.
