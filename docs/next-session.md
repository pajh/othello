# Where we are and next steps

Saved 2026-10-01; resumed-session update: T040 helper is ready at scripts/nn_selfplay_collect.py; launch/recovery details in docs/nn-selfplay-collection-handoff.md. Static checks passed; no collection or training has run. No coding job is active. The next agreed work is 5,000 NN-versus-NN games and a second training batch, under user supervision; nothing starts automatically.

## Current baseline

- Repository: git@github.com:pajh/othello.git, branch master. Initial commit 5232391 was pushed successfully. Subsequent handover notes are local changes unless separately committed.
- Source under src/rig, src/bots and src/training; existing environment is venv/ (no leading dot). Installed Python 3.14.7, CPU PyTorch 2.14.1+cpu and NumPy 2.5.3.
- Model: 128 -> 256 -> 64 -> 1, hidden ReLU, sigmoid score, 49,537 parameters. Own/opponent binary planes, after-action acting-player perspective; targets map -1/0/+1 to 0/0.5/1. Score estimates expected outcome, not perfect-play value.
- First collection: 1,000 random games, seed12345, retained at runs/run-197b46d72b9447ebb2e315321400b3e8/. Dataset under its dataset/ directory: 800 training games/48,321 rows and 200 validation games/12,090 rows.
- First training: MSE, Adam lr0.001, batch256, seed12345, max30 epochs, patience3. Four epochs ran; best epoch1 validation MSE0.212422 versus constant0.235027. Later epochs overfit. Selected checkpoint: checkpoints/first-model/run-2103bc51994e46a099f8b3d78618efd3/best.pt. Preserve it; last.pt is not the selected model.
- Current bot: NN-004-R2-T0.05. First two own actual moves uniformly random; passes do not count. Then temperature0.05 softmax sampling using the runner's per-seat seeded RNG. Candidate boards scored in one PyTorch batch. Fresh closure per seat/game; shared read-only network loads once per process. Module-level play remains a greedy primitive; the CLI invokes create_player to enable configured exploration.
- RAND-001 and MAX-001 remain available. Increment a bot's three-digit VERSION on every completed edit revision, including corrections. IDs are prominent in console/reports/metadata, not raw positions or NPZ arrays. Bot code version is distinct from trained model identity; checkpoint selection must also be recorded.

## Evidence and limits

Greedy learned bot versus random:78/3/19 (wins/draws/losses); random-opening version:77/3/20, on different seeds. Weighted self-play at seeds89012/89013/89014 gave bot1/bot2/draw34/64/2,36/59/5,52/46/2. Each batch had100normal games,0forfeits and100unique traces. Latest prefixes were unique by8actions, with no exact cross-game later-position repeats. These measures do not prove independent examples or diversity under spatial symmetries.

Bot2's initial lead reversed but pooled122/169/9 still leaned bot2. Source review found no direct identity-specific state error. The original asymmetry is not proven to be a bug or conclusively explained. Do not silently treat it as resolved; more diagnosis is optional user-directed work.

NN-004 timing at seed89014:100games in16.257s CLI time (includes startup/load/games/logging),6.151games/s. All100traces matched NN-003 at the same seed. Approx29% less time than the user's approximate23s baseline. Linear5,000estimate812.9s/13.55min, not a measured larger run. Parallelism remains deferred; no --cores flag exists.

## Next session: collection and second training

1. Check the current bot ID, checkpoint and output locations before starting. Keep existing settings fixed for this experiment. Use a fresh master seed; 90001 is a proposed value, not a previously run batch.
2. Have Luna prepare a small user-run collection/check/report helper for5,000games. Existing self-play smoke helper is fixed at100games; do not silently reuse it as a5,000helper. The existing CLI already supports arbitrary game counts. Keep new raw data under runs/, not disposable work/; record both IDs, checkpoint path, seed, count, timing, zero/actual forfeits and diversity in fixed latest reports.
3. User launches and monitors collection. A direct CLI command, if seed90001 is chosen, is:

```sh
OTHELLO_NN_CHECKPOINT="$PWD/checkpoints/first-model/run-2103bc51994e46a099f8b3d78618efd3/best.pt" \
venv/bin/python -m rig.cli \
  --bot1 bots.nn_bot --bot2 bots.nn_bot --games 5000 --seed 90001 \
  --output-dir runs/selfplay-5000
```

The CLI makes a fresh run-<uuid>/ directory and fixed run-summary.txt. Its metadata records IDs, but not checkpoint selection: the Luna helper/report must explicitly preserve that selection. Model weights remain loaded once; do not add speculative performance work before measuring the larger run.

4. Convert the completed run through training.convert into its dataset/ subdirectory, seed12345 and default80/20 split (4,000/1,000 eligible games if none forfeit). Whole games remain together, forfeits excluded. Converter replays games and may take longer than training; do not mistake that time for neural training. Luna prepares the exact command with the actual new run path and checks the mini report.
5. Resumed-session decision (2026-10-01): the user selected continuing the existing best model weights for the second training batch. Current training.train always initializes a fresh model and has no resume/fine-tune input option; a separately scoped Bunny change is required before training. User selected a new Adam optimizer; load model weights only. Preserve the selected parent best.pt and record its path in candidate metadata. The initial handoff's fresh-versus-fine-tune choice is now settled.
6. Preserve parent checkpoint and dataset; save candidate to a fresh checkpoints/second-model/ run directory. Unless changed by the user, initial trainer settings remain those above. User runs training and Luna reviews timing/validation/report results. Losses on different validation datasets are not directly comparable measures of improvement.
7. Measure candidate playing strength separately, using balanced colours and fresh/fixed evaluation seeds. Current nn_bot selects one checkpoint per process through one environment variable, so two instances cannot currently load different parent/child checkpoints in the same process. Direct parent-versus-child matches need a small separate configuration/loading change; otherwise evaluate each separately against random. Do not assume self-play retraining improves strength.

Allocate Generation003 to the new collection/training experiment when it actually starts; record configuration, artifacts, failures and results in GENERATIONS.md. Do not overwrite or rewrite Generation002.

## Reconnect OpenCode and notifications

Installed OpenCode is v2.0.20. Current verified session ID: ses_f0cb2b2e1ffe7wbI0MsfT217MO; title at verification was "Python project overview and current status in 10 lines". From the project root:

```sh
opencode session list
opencode --session ses_f0cb2b2e1ffe7wbI0MsfT217MO
```

Confirm the visible session if it changes. If the old session is unavailable, open a new one, get its actual ID and update AGENTS.md/workflow registration; do not invent an ID or infer one from recency. Git contains the instructions, not the user's OpenCode conversation history. A fresh conversation should read AGENTS.md, status.md, TODO.md, this document and the relevant canonical design.

Implementation is Space Bunny Free, explicit --model opencode/space-bunny-free and --agent build. Omitting model can inherit the session's model; we deliberately pin Bunny. Omitting agent previously inherited Plan and produced no implementation. One bite-size task at a time, exact allowed files and stopping point. Luna handles small helpers, reviews and concise results; user executes larger jobs. Keep code and raw logs out of the design chat. Avoid turning small maintenance into long consolidation work.

Plugin files are tracked: opencode.json loads ./plugins/codex-notify; entry is plugins/codex-notify/index.js, using scripts/notify_codex.sh. It is project-local, visible through /plugins, not globally installed. Reopen/reload OpenCode from the project directory (opencode reload is supported by this installed build) when needed, without interrupting active work.

Notification state is ignored under work/codex-notify/ and must be recreated after a clone or scratch cleanup. In the intended Codex chat, refresh registration before dispatch:

```sh
bash scripts/notify_codex.sh register "$CODEX_THREAD_ID" ses_f0cb2b2e1ffe7wbI0MsfT217MO
bash scripts/notify_codex.sh on
bash scripts/notify_codex.sh status
```

Use the new chat's CODEX_THREAD_ID; do not hardcode yesterday's target. At handover, registration targets01a0f2cb-7f39-7c70-a8e4-3e8a796d3d71 and notifications are on. Registration preserves on/off state; fresh state defaults off. Manual off control is available. Hook event is session.execution.succeeded with data.sessionID. It forwards completed final assistant text once. Idle-chat delivery was verified; active-turn delivery remains uncertain. Dispatch and end the design turn, do not loop polling. Saved handoff is the fallback if notification fails.

The Bash script uses codex queue (not --queue), resolves codex on PATH or /usr/lib/chatgpt/resources/codex, and fails gracefully if unavailable. No daemon-version preflight or daemon restart is required. Hook/notification logs stay in work/codex-notify/. Do not create another skill/MCP/global plugin just to resume this workflow.

## What Git does not contain

venv/, work/, runs/, checkpoints/, packaging metadata and generated arrays/logs are ignored. The trained weights and original/derived datasets are local only, even though their paths/results are documented. Recreating a checkout from Git alone does not recreate those artifacts: preserve/copy them separately or recollect/retrain. The existing local copies must not be deleted during cleanup. CPU environment recreation commands are in README.md. The OpenCode binary/provider login/session history likewise are not installed or restored by cloning this repository.

## OpenCode routing correction — 2026-10-01 resumed session

Current user-identified conversation is `Overview of Python files, rig, NN bot, and training rig`, ID `ses_f09b671eaffeJHQOKjugvgpYJR`; use it instead of the older ID in the original reconnect instructions above. Notifications registered to the current design chat. BUNNY-LIVE-HELLO-02 dispatched; visible confirmation pending.

## Active collection and parallel/hosted design — 2026-10-01

User launched the first 5,000-game collection and confirmed progress output at 500 games. Completion/results pending; do not interrupt it or launch another experiment. Four-worker collection and manually triggered GitHub Actions spec is ready in docs/parallel-and-github-design.md. No implementation or upload yet. Current visible Bunny route BUNNY-LIVE-HELLO-02 was confirmed by the user.

## Hosted collection ready locally — 2026-10-01

T009, T043 and I007 correction delivered; no parallel game runtime yet. T044 manual GitHub Actions workflow delivered with static checks reported passed. Repository is public; models/first-model.pt is the baseline copy intended for Git tracking. No commit/push or hosted dispatch. Next: user-authorized commit/push of prepared work, then manual collection with user-selected seed/count. User also asked about a bash alias for OpenCode: shell is the actual tool; a small V2 plugin appears feasible but has not been implemented.

## User priority update — 2026-10-01

User authorized committing/pushing all prepared work. After push, priority is conversion of the completed 5,000-game collection and continued training from parent weights with a new Adam optimizer. Prepare trainer support via Bunny and concise user-run commands via Luna; user monitors conversion/training. Circle back to local multi-core and GitHub proving runs only after training. Multi-core and hosted runtime are still unproven.

- Push completed: origin/master 1e6e72f includes prepared source/workflow/docs and models/first-model.pt. No hosted run. Bunny now receives trainer --initial-checkpoint task; Luna prepares conversion command for retained run. Both conversion and second training still unrun.

## Second training complete — 2026-10-01

User completed continuation weights/new Adam on selfplay5000 dataset. Candidate checkpoints/second-model/run-selfplay-5000/best.pt, best epoch1 validationMSE0.193218 vs loaded-parent0.203582 on same split. Four epochs, patience stop, total7.5s. No strength result yet; choose evaluation next. Multi-core/hosted proving runs remain unproven. Trainer/records changes after 1e6e72f are not yet pushed.

## Candidate evaluations complete — 2026-10-01

User ran candidate/random100 at86/5/9 (seed91001), then candidate/parent100 at62/6/32 (seed91002), alternating colours, workers1, no forfeits. Candidate65% score vs parent supports improvement in this batch. Parent/candidate have same NN-004 code ID but different module/checkpoint selectors; disposable clone uses hardcoded local candidate path. No plateau conclusion or automatic promotion. Local multi-core and GitHub proving runs remain next previously agreed work and unrun.

## Next collection selected — 2026-10-01

User authorized committing current changes, then user-run5,000games with4workers. Prepared command uses canonical nn_bot on both seats, candidate checkpoints/second-model/run-selfplay-5000/best.pt, fresh seed90002, output runs/selfplay-5000-second/. Fresh data can feed another training round if results look good; no job started or further training launched. Timing comparison against previous914.067s is practical rather than controlled because checkpoint and game traces change. Allocate next generation when this collection actually starts.

## Four-worker collection completed — 2026-10-01

Generation004: latest second-model best.pt self-play5000games, seed90002, workers4, run runs/selfplay-5000-second/run-4930cc31f42e4534a4feaf919d672a78.5000normal0forfeits,2459/2369/172 outcomes, helperPASS. Fish~4m10s. Local multicore now exercised; GitHub unrun. Next user-run conversion seed12345/default80/20 then continue second-model best.pt/new Adam in separate third-model output. No conversion/training yet for this collection.

- Generation004 conversion complete: dataset/ holds241,586training and60,343validation rows (4000/1000games). Next training uses second-model/run-selfplay-5000/best.pt, saves third-model/run-selfplay-5000; new Adam, current defaults. Unrun.

## Third model trained — 2026-10-01

Generation004 continuation completed: latest selected checkpoints/third-model/run-selfplay-5000/best.pt, epoch1 validation0.186284 vs starting second-model0.199267 on this split;4epochs,total7.1s. Prior models preserved. No third-model match yet; current disposable clone still hardcodes second-model path and must get one-string update for third-model evaluation. GitHub runtime remains unrun.

- Latest evaluation: third-model greedy NN-EVAL-001-R0-T0 vs RAND-001 at97/2/1 in100games,seed92001,zero forfeits. Raw runs/third-model-greedy-vs-random/run-d5597b0937c542d6a73b4d26afc50c98. This differs in both checkpoint/settings from second-model86/5/9; third-vs-second still unrun.

- Third-vs-second evaluation completed:63/4/33 in100games,seed92002,workers1,matching R2/T0.05,zero forfeits. Raw runs/third-model-vs-parent/run-fb413356522944729cb509d5ad45df37. Both successive candidate-vs-parent batches gave65%score. Latest third-model best.pt remains selected; no next round started.

## First hosted training requested — 2026-10-01

User requests hosted5000latest-best vs best, conversion/training candidate, download parent/candidate/logs, then local100candidate-parent. models/best.pt prepared from third-model best.pt; Bunny receives workflow extension only. Primary to commit/push and dispatch seed90003/workers4 after handoff. No remote job yet. Future desired hosted1000evaluation recorded as separate next stage, no automatic promotion.

- First hosted job submitted: https://github.com/pajh/othello/actions/runs/36841281392, commit669a1fd,5000games/seed90003/workers4/models/best.pt. Observed in_progress. Check status, download exact artifact and review saved summaries via Luna; then user-run100candidate/exact-downloaded-parent. No outcome or promotion yet.

## Hosted artifacts downloaded — 2026-10-01

Run36841281392 successful, downloaded runs/github-first/. Parent runs/github-first/runs/github-selfplay/parent.pt; candidate runs/github-first/checkpoints/github-candidate/best.pt. Disposable candidate clone now selects hosted candidate, canonical uses explicitparentenv. Next user-run100head-to-head with matchingR2/T0.05; candidate strength/promotion unresolved. Hostedcollection161.608s,training5.693s,bestepoch1val0.198206vsloadedparent0.205014same split. C plan FP32initial plus earlyFP16weight-storage comparison.

- Hostedcandidate local100vs exactparent complete54/4/42 (56%score),seed93001,zero forfeits. Batch supports apparent smaller gain than prior65%,65%, but slowdown/plateau uncertain. Raw runs/github-candidate-vs-parent/run-2cc0170b01414cad97143493008d2925. No repositorybest replacement/new experiment.

- Hostedcandidate greedy vs random achieved100/0/0 in100games,seed93002,zero forfeits. Raw runs/github-candidate-greedy-vs-random/run-69af4aeefd634e81b1a9b0ca0037b009. Candidate weights at runs/github-first/checkpoints/github-candidate/best.pt; greedycopy NN-EVAL-002-R0-T0. C plan design-only with FP32initial/earlyFP16comparison.

## Current hosted round — 2026-10-01

Latest commands: docs/command-guide.md. User authorized full push and Generation008 hosted run: models/best.pt now first-hosted candidate,5000games seed90004/workers4,8way symmetry after whole-game split,continued weights/newAdam/patience1,1000candidate-parent evaluation seed190004. Candidate remains a download pending user adoption. See status.md latest entries for dispatch URL/results.

- Dispatch confirmed: https://github.com/pajh/othello/actions/runs/36887079634, commit b9aea93, observed in_progress. Download selfplay-36887079634-1 after completion to a fresh runs/ directory; review collection/conversion/training and evaluation-summary.txt before considering adoption.

- Generation008 successful and downloaded runs/github-symmetry/. Candidate633/37/330 vs parent in1000games (65.15%), zeroforfeits. Bestepoch2 validation0.190112 vs starting0.196363,3epochs/patience1. New candidate is runs/github-symmetry/checkpoints/github-candidate/best.pt; exactparent runs/github-symmetry/runs/github-selfplay/parent.pt. Repository best and existing Cpayload not changed by retrieval; choose adoption/export next.

- Latest requested run: https://github.com/pajh/othello/actions/runs/36891605722,seed90005,parent Generation008epoch2,observed in_progress. NewCGquantizedsubmission runs/c-submission/submission.c87775chars compiled/reconstructionchecked/onesmoke; readyforpaste. OldCGassets runs/c-generation007/. No hosted outcome/newCGleague result yet.

- Generation009 run36891605722 successful, downloaded runs/github-symmetry-second/. Newcandidate577/26/397 vs exactparent in1000games (59%score),0forfeits;bestepoch1MSE0.192371 vs starting0.194623,2epochs/patience1. Candidate runs/github-symmetry-second/checkpoints/github-candidate/best.pt; not promoted/exported. CurrentCGGeneration008quantizedbot reached17thWood2 peruser.

- T071 complete: latestbest committed/pushed baa8938; Generation010 run36906357664 https://github.com/pajh/othello/actions/runs/36906357664 dispatched/observed in_progress.5000games/seed90006/workers4/eightsymmetries/patience1/eval1000seed190006. Results pending; Cbotrebuild deferred.

- LatestGeneration010candidate602/29/369 in1000parentgames (61.65%),downloaded runs/github-symmetry-third/. NewquantizedCGsource runs/c-submission/submission.c87775chars compiled/bytechecked/onesmoked; readyforuserpaste. Repositorymodels/best.pt stillGeneration009parent; no furtherpush/job authorized.

- Generation011 dispatched after explicit commit/push approval: commit36dc562, https://github.com/pajh/othello/actions/runs/37010404989 observedin_progress. LatestGeneration010parent,5000games seed90007/workers4/currentR2T0.05/symmetries/newAdam/patience1,1000eval seed190007. Results pending. C-only opening-book approach and Edax generation choices recorded in docs/opening-book-plan.md; no Edax install/generation/integration yet.

- Generation011 completed successfully: GitHub37010404989, job9m17s, downloaded runs/github-symmetry-fourth/selfplay-37010404989-1/.5000normal0forfeits seed90007/workers4. Bestepoch1 validationMSE0.193566 vs starting0.194720;2epochs/patience1,training29.461s.1000candidate-parent games seed190007:475candidatewins/26draws/499losses,48.8%score,0forfeits. No demonstrated playing-strength improvement; near-even result does not establish decline/plateau. Generation010 remains selected; no promotion/export/newjob.

- Generation012 requested/dispatched https://github.com/pajh/othello/actions/runs/37013882628 from retainedGeneration010 (existing36dc562), seeds90008/190008,5000collection/1000evaluation/workers4/unchangedsettings. Generation011 retained withoutpromotion. Luna Edax4.6setup complete under tools/edax with included eval.dat; docs/edax-setup-handoff.md. No Edax analysis run; user-run one-position smoke next.

- Generation012 GitHub37013882628completedsuccess, artifactsdownloaded runs/github-symmetry-fifth/.1000candidate-vs-retainedGeneration010parent:507wins/22draws/471losses,51.8%score,0forfeits,seed190008. Bestepoch1validationMSE0.192354vsstarting0.193386;twoepochs/patience1,29.350straining. Modestobservededge,notclearimprovement; candidate notpromoted. Lunaresultsreportreviewdispatched; collectiondetailsnotyetsummarized.

- Userexplicitlyauthorizedcommit/push/hostedEdaxlaunch2026-10-02. Commit07ed0ae pushed: evaluator/prefixhelpers/manualworkflow/2479canonicalinput/84bytestartupbook/setupandhandoffdocs. Run https://github.com/pajh/othello/actions/runs/37024860120 dispatched atEdaxlevel38/4workers. Earlychecks10/12.5/15min,threeconsecutiveestimatedtotal>5hstop,5helapsedcap;partialsalwaysuploaded. Runtime/resultsunknown; noculling/narrowextension/Cbookadoption.

- HostedEdax37024860120stoppedasdesigned after901.2s(15min), reasonSTOPPED_ESTIMATE,61/2479completed,lastperworkerestimate11.93h (earlier~17h). Workercompleted19/15/13/14. GitHubredXisnonzeroincompletestop;artifactuploadsuccess. Downloadedpartial61analyses/logs/summary runs/edax-hosted-level38/edax-book-37024860120-1/. No protocolfailureorcompletebookclaim; no lowerleveljobstarted.

- User-authorized level-34/four-worker Edax retry committed/pushed a18b453 and dispatched https://github.com/pajh/othello/actions/runs/37027471923; observed in_progress. Same retained 2479 prefixes, checks at 10/12.5/15 minutes, five-hour estimate/hard limits. Results pending; no automatic depth reduction or book adoption.

- User-run NN C0 equivalence passed: seed97001/models/best.pt, NN-004-R2-T0.05 versus NN-005-R2-T0.05-C0, 61 plies, 61 stateful and 61 greedy comparisons with matched RNG streams; terminal White41–23. This establishes unchanged choices/RNG on this one game with solver disabled; C8/C10 strength comparisons remain unrun.

- User completed C8-versus-C0 comparison: same models/best.pt (selected Generation010),100games,seed98008,fourworkers,alternatingcolours; C8 won65–35,0draws/forfeits, user shell walltime8.33s. Raw runs/nn-c8-vs-c0/run-7b28c26eeab344618124900f8acce5b8/. C0/C0 baseline also saved:100normal,44/2/54,seed98000,raw runs/nn-c0-vs-c0/run-c66a971b32c54887ae8b524d93e2c591/; summary has no elapsed field,baseline walltime not supplied here,so slowdown ratio unquantified. C8/C8 throughput and C10 comparisons remain unrun; no canonical cutoff change/training launch.

- User-run both-seat C8 throughput:100games,seed98008,fourworkers,models/best.pt,R2/T0.05;100normal,0forfeits,56/3/41 seat outcomes,wall8.26s,userCPU31.65s. Raw runs/nn-c8-vs-c8/run-6ae57e99b2e54bddae1142d960eb1ff2/. Simple same-machine 5000-game extrapolation8.26*50=413s(~6m53s), includes repeated startup in extrapolation and is approximate. Similar walltime to single-seat C8 batch8.33s; baseline slowdown percentage unknown. No training/hosted job or cutoff adoption authorized by this result alone.

- User explicitly selected Generation012 best as new models/best.pt and canonical C8 for hosted5000 self-play/training plus1000 C8candidate-vs-C8exactparent evaluation. Commit040e249 pushed; run https://github.com/pajh/othello/actions/runs/37030679887 observed in_progress,collectionseed90009/evaluationseed190009/workers4. Canonical nowNN-006-R2-T0.05-C8; conversion8symmetries,continuedweights/freshAdam/patience1 unchanged. Edax level34 run37027471923 concurrently active. Results pending; Cdeployment weights unchanged. Earlier comparison commands using canonical as C0 are now historical because canonical is C8; use retained revision for future C0 comparisons.

- Generation015 hosted37030679887 failed AFTER all5000 games completed normally0forfeits (2429/130/2441,~503s collection). Observed error: helper hardcoded BOT_ID NN004R2T0.05 rejects actualNN006R2T0.05C8; conversion/training/evaluation skipped. Artifact upload succeeded; retrieval runs/github-c8-first/. T081 narrow helper-ID fix delegated; raw provenance incorrectly embeds old ID and must remain honest, no candidate trained.

- T081 verified one-line collector BOT_ID fix, committed/pushed aa173e0. Generation015 retry https://github.com/pajh/othello/actions/runs/37032114143 observed in_progress; same selectedGeneration012best/C8/5000games/seed90009/workers4 and1000evalseed190009, other training settings unchanged. Fresh collection rerun; initialfailedartifact preserved runs/github-c8-first/. No candidate/results yet.

- T082 complete/reviewed: collector now reads canonical get_id() after checkpoint setup for launch provenance, retained metadata IDs for review/reports, requires same-seat IDs and provenance agreement. Hosted eval summary parses recorded IDs; no duplicated fixed ID remains. OpenCode reports synthetic identity/mismatch/history/parser/help/syntax checks passed; primary diff inspection done. Changes local/uncommitted, active37032114143 uses its prior checked-out revision; no games/jobs launched by T082.

- Generation015 retry37032114143 succeeded; downloaded runs/github-c8-retry/.5000normal/0forfeits,2429/130/2441,collection510.154s. Candidate bestepoch1MSE0.176499 vs loadedparent0.179488 on samevalidation split;2epochs/patience1,training29.581s.1000 C8candidate-vs-C8Generation012parent seed190009:560wins/37draws/403losses,57.85%score,0forfeits. Newcandidate runs/github-c8-retry/checkpoints/github-candidate/best.pt; exactparent runs/github-c8-retry/runs/github-selfplay/parent.pt. Evidence supports improved weights underC8; C0/greedy/Cdeployment improvement not measured. No promotion/export/newjob.

- User-requested latest Generation015 C model rebuild completed via Luna existing tooling. Prior assets archived runs/c-generation010/. New submission runs/c-submission/submission.c87775chars (12225headroom),SHA256a4a028ad702c67e39410877448de636d878d3afe0a6fa5c33d7c7749c07979e6; GCC buildclean,embedded quantized reconstructionbyteidenticalPASS,leakdetectiondisabledforpriorptracelimitation. QuantizationMAE0.00142061329/max0.02498734. One seed96003smokevsrandom normal0forfeits/Cwin runs/c-generation015-smoke/run-7d975b742cbc469891482431db13e812. Csource greedy unchanged/no minimax/book yet; no checkpointpromotion/commit/push/CGsubmission. Handoff docs/c-generation015-handoff.md.

- T083 isolatedZ85trial completed: decodedtruepayload50561bytes and expandedFP32blob198148bytes identical to Base64/reference (CpayloadCRC bce3a986,decodedCRC2205bf07,cmpPASS). Trialcomplete source runs/c-z85-test/z85/submission.c83574chars vs87775baseline,net4201saved,16426headroom (6426after hypothetical10000charbook). OpenCode reports cleancompile andASan/UBSan; primaryhandoff/trigraphfixreview done. Real C11trigraph??!caught in Z85literal; generator splits adjacent literals betweenquestionmarks to preservebytes (7char overheadincluded). ProductionBase64paths unchanged; trialnotadopted,no game/modelchange/commit/push. Handoff docs/z85-encoding-test-handoff.md.

- User reports latest Generation015 NN-only C submission promoted to Wood League1 on2026-10-02. Arena promotion observed by user; no minimax/book yet.

- T085 Luna completed attributedEdax4.6 scalar one-stageparallelprefix legalmoves: staticinline u64valid_moves(u64mine,u64theirs),typedefuint64_tu64; C VERSION004. No NNchoice/search/flipperchanges. Enginecomparison4004maskPASS (explicitedges,longrays,nomoves +32seededtrajectories/1999positionsbothplayers). makebot/exactsubmissionGCCclean; submission84767chars vs83566(+1201),headroom15233;5233afterhypothetical10000book. Priorretained runs/c-bitboard-moves/prior-submission.c. Handoff docs/c-bitboard-moves-handoff.md; no game/CGsubmit/commit/push. Primarysource/sizeinspection done.

- T086 Luna completed portabletable-free scalarcoordinate-ray flip_discs(u64mine,u64theirs,intsquare),returnsflips/noboardmutation;C VERSION005,chooserunchanged. Engineflipmask/resultboardchecks31172PASS across32seededtrajectories+targetededge/corner/diagonal6disc/multiraycases. makebot/exactsinglefileGCCclean. Submission85648chars(+881),headroom14352;4352afterhypothetical10000bookbeforewhitespacecleanup. Priorarchive runs/c-scalar-flipper/prior-submission.c; handoff docs/c-scalar-flipper-handoff.md. No search/game/throughputbenchmark/CGsubmit/commit/push; speedunknown. Primarysize/sourceinspection done.

- 2026-10-03: User reports 204th Wood League1 and authorizes committing/pushing current work, a new hosted training round, then C terminal-only timed negamax. Selected parent for next round: Generation015 best.pt (runs/github-c8-retry/checkpoints/github-candidate/best.pt), copied to models/best.pt. Planned5000/seed90010/workers4/C8/R2T0.05/symmetries/freshAdam/patience1/eval1000seed190010. Dispatch pending; no new result. Opening-book artifact review deferred until after negamax. Current OpenCode session title03 Oct2026 - Othello, ses_eff32efa6ffeeQp9LPctJ4GKCT; greeting/reply marker OPENCODE-HELLO-20261003-01 confirmed. No visible-terminal receipt claim beyond user-provided title/reply.
