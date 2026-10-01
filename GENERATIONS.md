# Generation history

Workflow experiment (2026-09-30): shared OpenCode terminal delivery was verified. An initial summary went to the older records-writer session and was invisible to the user's separate overview conversation. After confirming the visible session ID, a second read-only task produced BUNNY-LIVE-CHECK-01 in the user's terminal. Current ID and reproducible instructions are in docs/opencode-workflow.md and AGENTS.md. No coding/game execution occurred in these checks; any speed benefit remains unmeasured.

Report convention agreed 2026-09-30: generated summaries keep a fixed latest filename; optional history moves previous versions to numbered siblings (e.g. run-summary.34.txt). Report archive numbers are separate from experiment generations.

Permanent chronological record. Raw logs belong in run artifacts; keep this history readable and factual.

## Generation 000 — 2026-09-30 — Initial infrastructure and project design

- Purpose: establish a supervised, reproducible Othello learning project without choosing the user's experiments.
- Changes: OpenCode LongCat 2.5 Preview Free implemented the initial rules engine. It was moved from an inner othello package to engine.py at the root during layout discussion, then relocated unchanged to src/rig/engine.py after the src/rig, src/bots, src/training layout was agreed. Scaffold added explicit setuptools package discovery, package markers, and README setup instructions using the existing venv/ directory.
- Workflow: small bounded coding tasks; Luna prepares small run scripts and formats results; user runs and monitors larger jobs. Initial verification is one random-versus-random smoke game, with focused tests added for observed problems.
- Project records: status.md, TODO.md, this history and disposable work/ established; responsibilities documented in AGENTS.md.
- Actually run: implementation tooling only. No environment was created, no package installed, and no game, smoke check, benchmark or training run occurred. No trained model exists.
- Results: engine code delivered; at that stage correctness and throughput were unknown. The temporary implementation handoff was culled; the implementation and later smoke result remain described here.
- Next: user-run editable installation (`python -m pip install -e .` after activating venv/); later coding stages remain separately scoped.
- Update 2026-09-30: OpenCode LongCat 2.5 Preview Free delivered the one-game runner in `src/rig/runner.py`; Luna prepared `scripts/smoke.py` and documented its command in README. A venv import check showed `rig` was not installed (`ModuleNotFoundError`), so no editable install or game was run at that point. The user later completed the smoke successfully.
- Correction/update 2026-09-30: the user subsequently ran the smoke helper successfully: normal termination, winner=1 (engine BLACK), Black 51, White 13, 64 discs total, and 61 accepted actions. This confirms the user's environment could import and run the project; the exact setup command and additional checks are unknown. The run meets the agreed smoke acceptance criterion but does not establish full rules correctness. Next: separately scoped versioned-records work, followed by batch CLI.

- Workflow update (2026-09-30): user selected Space Bunny Free for the next OpenCode coding task after observing slow LongCat delivery. No Space Bunny task has run yet.

- Space Bunny Free delivered `src/rig/records.py` for T007. It builds schema-v1 records by replaying accepted actions and writes flushed compact JSONL. The original handoff reported only syntax parsing; no imports, games, runtime checks, or JSON serialization were run then. Luna's initial source review found I001: EMPTY as `forfeiting_player` passed colour validation and later triggered `KeyError` rather than the documented `ValueError`. The bounded correction and remaining forfeit-path limitation are recorded below. Different coding tasks were not a controlled model benchmark.

- Space Bunny Free made the bounded T012 fix for I001 by explicitly rejecting EMPTY as a forfeiting player with `ValueError` before bot mapping. Luna reviewed the changed branch and handoff; the reported transient stub calls cover EMPTY, several invalid values, and a normal zero-action result. No game, runner-produced forfeit, or JSONL serialization/round-trip was run, so broader runtime behavior remains unverified. Next: batch CLI task is ready for separate dispatch.

### Update — 2026-09-30 — Sequential batch collection interface setup

- Purpose: deliver bounded T013 batch collection and prepare the T014 user-run smoke check.
- Changes: Space Bunny Free delivered `src/rig/cli.py` with sequential game execution, deterministic per-bot seeds, alternating or forced colours, fresh run artifacts and concise summaries. Luna prepared `scripts/batch_smoke.py`; README documents its command. The temporary helper handoff was later culled.
- Actually run: Space Bunny Free reports syntax parsing, module import, `--help`, and pure seed/colour helper checks. The first user helper run played two normal games but caught I002: both JSONL records assigned bot 1 Black; its summary counted two bot 2 wins. After the source correction, the user reran the helper successfully: two normal, training-eligible games, no forfeits/draws, alternating recorded colours, and one win per bot. Corrected run artifacts are under `work/batch-smoke/run-e09a62cd62344e2ca7aa327d67f25c84/`; the original failed records remain under `work/batch-smoke/run-c6ae5e8c5319465483384cad9287d0d8/`.
- Results: the user's two-game smoke exposed I002 (bot 1 was recorded as Black in both games); the corrected rerun verified default alternation, game records, training eligibility and summary output. It did not verify `--force-start`, failure handling, summary history or broader CLI behavior. The original diagnosis and correction handoff were culled after preserving this evidence.
- Next: no batch smoke work remains. No training, benchmark, or larger collection job was launched.

### Update — 2026-09-30 — Notification control script handoff

- Space Bunny Free delivered `scripts/notify_codex.sh`; Luna source-reviewed it and `bash -n` passed. Initial checks covered safe no-send paths only. No queue message or daemon command was run then. A source review found I003: the receiver-unavailable skip logged why but omitted the unsent message. The branch was corrected; the original script review and handoff were culled after preserving the issue and fix here and in the reusable notification workflow.
- Space Bunny Free applied the bounded I003 correction: the receiver-unavailable log line now includes the unsent message passed through `one_line`; Luna source-reviewed that branch. The handoff reports `bash -n` passed. No receiver or queue command was run, so actual preflight logging and visible delivery remain unverified. Next: a live route check is required before any plugin work.

### Update — 2026-09-30 — Queue route and local hook

- The user's direct shell notification CODEX-QUEUE-CHECK-01 reached this Codex chat. This disproved the assumption that a successful daemon-version preflight was needed for queue delivery. Bunny updated the script to call the verified queue route directly and preserve manual enablement during registration.
- Bunny delivered the project-local hook and explicit `opencode.json` registration; syntax/config checks passed according to the handoff. Parent reloaded configuration successfully and sent a read-only startup task; Bunny returned OPENCODE-HOOK-STARTUP-01. No hook log appeared and plugin listing reported no plugins. Automatic delivery remains unverified, notifications are off, and configuration discovery is being investigated. No experiment or training run occurred.
- Runtime correction: server logs rejected the entry-file path because configured plugin paths must be directories. Bunny changed the entry to `./plugins/codex-notify`, which produced a baseline. First delivery check still did not send; bounded content-free diagnostics showed `session.execution.succeeded` with `data.sessionID` rather than `session.idle`. Bunny corrected those fields and removed temporary event logging.
- OPENCODE-HOOK-DELIVERY-02 then completed with one automatic extraction and dispatch (exit 0). The script logged queue acceptance of message `01a0f3a4-ce84-7e50-9045-59999550b551` for this chat. Visible receipt is pending until the current turn ends. Notifications left on; no global installation, training or game run occurred.
- Follow-up: the user reports no visible message after the turn ended. Luna found the marker/queue UUID in the target thread's rollout record and no remaining `queued_items` row, but record presence does not establish a visible user message or model receipt. No executable mismatch was found. Delivery acceptance remains incomplete; investigate pickup/display before claiming success.
- Correction to that diagnostic inference: the inspected rollout hits were our tool output/report, not an injected user message. The subsequent delayed read-only task OPENCODE-HOOK-IDLE-03 finished after the design turn ended; its automatic notification visibly arrived in this chat and was acknowledged. This establishes delivery while idle; delivery of the earlier accepted message during an active turn remains unexplained. Use dispatch-and-finish rather than completion polling.

### Update — 2026-10-01 — Documentation consolidation

- Removed 69 obsolete one-off task prompts, implementation handoffs, source reviews and superseded layout notes. Retained 16 canonical architecture/interface/workflow documents and actual result reports, indexed in `docs/documentation-index.md`.
- Preserved observed failures, corrections, experiment outcomes and limitations in this chronology and the retained result reports. Generated artifacts were not changed. No code, experiment, game, training job or Git operation was performed.

## Generation 001 — 2026-09-30 — First random-versus-random collection

- Purpose: collect the first retained outcome-labelled game logs with the existing sequential rig; no model trained.
- Configuration: `bots.random_bot` against itself, 1,000 games, master seed 12345, alternating bot colours. User executed and supervised the run; shell reported approximately 18 seconds.
- Retained artifacts: `runs/run-197b46d72b9447ebb2e315321400b3e8/metadata.json` and `games.jsonl`; latest summary `runs/run-summary.txt`. Permanent review: `docs/collection-1000-review.md`.
- Results: 1,000 normal games, no forfeits, 55 draws; bot 1 wins 484, bot 2 wins 461. Each bot played Black 500 times and White 500 times. All games are training-eligible, containing 60,411 positions.
- Luna parsed every record and confirmed summary agreement, unique IDs/indexes/per-bot seeds, board encoding/disc counts and basic position/action/result bookkeeping. No full move replay or comprehensive engine verification was performed; positions within/between games are not independent samples.
- Conclusion: the collection rig completed this supervised run and produced structurally consistent records. This provides no evidence of learned playing strength. Next design step: raw-log conversion to training representation/targets and a split by whole game; framework/model/training decisions remain open.
- Preparation update: user agreed one post-action row per accepted action, own/opponent planes from the actor's perspective, outcome -1/0/+1 for that actor, no swapped duplicates, and exclusion of all forfeited games. Whole games are shuffled/split with a recorded seed; default is 80/20 with exact floor rounding. Luna installed/import-verified NumPy 2.5.3 in existing venv. The retained contract is now [dataset-design.md](docs/dataset-design.md).
- Stage 1 handoff: Bunny reports full replay of 1,000 games/60,411 accepted actions into after-action actor-relative samples, perspective/outcome checks, 13 malformed variants and a skipped-forfeit fixture. Luna source-reviewed the interface/transformation and found one contextual UTF-8 error-reporting gap (I004); correction dispatched. Luna's lightweight raw-record count found 420 pass actions across 331 games, contradicting the handoff's no-pass claim. Stage 2 archives/split/report and training remain unimplemented; source review did not independently rerun the full replay.
- Stage 1 acceptance: Bunny corrected contextual UTF-8 errors and reports two invalid-byte fixtures plus a valid single-record regression. Luna source-reviewed and signed off; JSONL line numbers on decode failures are lower bounds because decoding is buffered, with codec offset retained. No full replay rerun or training. Stage 2 now authorised for bounded dispatch.
- Stage 2 handoff: Bunny delivered `training.convert`, optional NumPy dependency and converter handoff. Reports pure split/array checks and one throwaway two-game conversion with pickle-free archive loading and summary agreement. Retained 1,000-game conversion has not run. Outputs are staged, then replaced individually with summary last; the three-file set is not atomic and interrupted publication can mix versions. Luna source review/helper preparation underway; no training.
- Stage 2 acceptance/preparation: Luna source review found no blocker; prepared and AST-checked `scripts/dataset_smoke.py` for the user to run. It will convert the retained collection, verify 800/200 whole games and 60,411 total rows, safe NPZ types, report/source agreement and two after-action perspective spots. Actual conversion remains unrun. Zero-forfeit collection cannot runtime-test exclusion; no games or training launched.
- User-run dataset smoke passed: 1,000 eligible games split 800/200 with seed 12345 and fraction 0.8. Training contains 48,321 rows (loss/draw/win 22,808/2,597/22,916); validation contains 12,090 rows (5,668/724/5,698). Luna read the saved summary to confirm counts, schema/encoding 1 and NumPy 2.5.3. `training.npz`, `validation.npz` and `conversion-summary.txt` retained under `runs/run-197b46d72b9447ebb2e315321400b3e8/dataset/`. Smoke reports arrays, summary, IDs/plies, labels and two perspective spots agree. Full-run forfeit exclusion was not exercised because source has zero forfeits. No training occurred; framework/model/objective decisions remain open.
- Tooling setup (2026-09-30): user authorised PyTorch installation before model design. Luna installed torch 2.14.1+cpu from the official CPU wheel index into existing venv/ (Python 3.14.7), preserving NumPy 2.5.3. Imports and a tiny CPU tensor backward check passed, gradient [4.0]. Added optional training dependencies; installation commands are in README. At that point no model/training run existed and model choices remained open.
- First-model infrastructure (2026-09-30): user agreed actor-relative 128-input MLP 128/256/64/1 with ReLU hidden layers and sigmoid expected-outcome score; 49,537 parameters. Bunny delivered src/training/model.py under T023 and reports synthetic output-shape/range and gradient checks passed. No optimizer step, dataset read or training. Luna source review requested. User requested validation-loss stopping with best checkpoint retention; exact first-run trainer settings proposed separately. This is infrastructure, not a trained-model generation.
- Trainer infrastructure (2026-09-30): user accepted MSE, Adam lr0.001, batch256, seed12345, maximum30 epochs, patience3. Bunny delivered CPU trainer with full-set end-of-epoch losses, untrained and constant baselines, best/last checkpoints and fixed history/summary names. Reports pure loader/validator/baseline checks and a weights-only checkpoint roundtrip passed; fixed TorchVersion serialization and archive error context during these checks. Training loop and real dataset untouched. Luna source review and user-run helper requested; no timing or learning result yet.
- Trainer acceptance/helper preparation: Luna found I005 missing overlapping-plane rejection; Bunny corrected it with guarded validation and reports overlapping/disjoint synthetic fixtures passed. A first attempted correction indexed an empty overlap array; the passing-fixture check caught it and the guard fixed it. Luna source-confirmed no remaining blocker and delivered syntax-checked `scripts/train_first.py`. The helper was not run at that point; the user later ran it successfully as recorded below.

## Generation 002 — 2026-09-30 — First model training attempt

- Purpose: first supervised end-to-end model training and timing on Generation001's retained dataset; architecture/settings in docs/first-model-design.md.
- User executed venv/bin/python scripts/train_first.py. Dataset loaded: training48,321 rows/800 games, validation12,090 rows/200 games; CPU torch threads4 and interop4.
- Attempt failed before epoch1 at train.py:371: initial history path joined string output_dir using `/`, causing TypeError. Helper reported exit1, elapsed2.9s. Failed run retained at checkpoints/first-model/run-79060b47c8404d4a81b3084ffb56c404.
- No completed epoch, learned checkpoint or playing-strength result reported. This elapsed time is failed setup time, not training throughput.
- Luna confirmed only this join lacked existing Path conversion. I006 was dispatched as a narrow correction; the user reran after review, with failed evidence preserved.
- I006 correction: Bunny wrapped initial history path in Path, reports focused reproduction then JSON write/replace/import checks passed without training. Luna source-confirmed no remaining direct string-path joins. Failed directory preserved; existing helper ready for user rerun. Epoch loop past setup remains unexercised.
- Successful user rerun: checkpoints/first-model/run-2103bc51994e46a099f8b3d78618efd3/. Helper PASS; 4 completed epochs, best epoch1, patience3 stop. Training MSE epochs1–4: 0.197927,0.172432,0.137600,0.113117; validation: 0.212422,0.213875,0.231031,0.242892. Untrained validation0.236017 and constant-baseline validation0.235027; best is ~9.6% lower than constant. Trainer total2.3s, helper elapsed4.1s, epoch times~0.3s; user perceived~3s. Timing boundaries differ, not contradictory.
- Luna reviewed saved summary/history/helper report only (no repeated run/checkpoint load), report docs/first-training-results.md. Training and artifact pipeline now exercised under user supervision. Clear validation degradation after epoch1 despite falling training loss; retain best.pt for bot, not final last.pt. No evidence of playing strength or self-play improvement; next learned-bot integration and fresh balanced random-opponent matches.
- User selected max_bot scaffold before neural inference: evaluate each supplied legal move's engine after-action board and select highest deterministic own-perspective hash score. Bunny delivered bot with non-game checks; Luna source review no blocker. Luna prepared syntax-checked scripts/max_bot_smoke.py for user-run100games versus random, seed54321, alternating colours; requires normal completion and zero forfeits. Check remains unrun, artifacts planned under work/max-bot-smoke/. Placeholder scores carry no strategy or learned-strength claim.
- User max_bot smoke passed:100normal games,0forfeits,6draws,max_bot38wins/random56,seed54321alternatingcolours. Artifacts work/max-bot-smoke/run-f773586b35804dbb94798f863457bb6d/ and fixedrun-summary.txt. Luna read summary/metadata and formatted docs/max-bot-smoke-results.md, did not replay games; helper reported balanced assignments. Acceptance met: move-evaluation framework completed supervisedgames without crashes/forfeits. Win counts do not establish learnedstrength because scoring remains hashplaceholder. NN integration pending.
- NN bot integration: user requested separate nn_bot retaining max_bot. Bunny delivered import-time CPU checkpoint loader, strict version/state checks, actor-relative float32 input and no-gradient inference in existing max-picker loop; reports tiny checkpoint/encoding/error/argmax/pass/nonreload checks passed. Luna source review no blocker and prepared syntax-checked scripts/nn_bot_smoke.py. User-run100games versus random planned,seed67890alternatingcolours, checkpoint run-2103bc51994e46a099f8b3d78618efd3/best.pt explicitlyselected; fixedwork/nn-bot-smoke/match-check.txt will recordcheckpoint/WDL. No learnedbotmatch yet.
- Successful user NN match:100normal games0forfeits versus random,seed67890alternatingcolours; nn_bot78wins3draws19losses, winrate78%,draw-adjustedscore79.5%. Helper reports50Blackassignmentsperbot and record/summaryagreement. Checkpoint epoch1best.pt in run-2103bc51994e46a099f8b3d78618efd3. Rawmatch work/nn-bot-smoke/run-3ab2e0476c7643cdb1ec227fa291b9c2/, latestsummary and match-check.txt selector; permanent docs/nn-bot-smoke-results.md.
- Luna reviewed saved summary/metadata/selector only, no replay/checkpointload/rerun. End-to-end first baseline now works from collection to conversion/training/checkpoint/inference/matches; this singlebatch favours learnedbot against random. It does not demonstrate iterative self-play improvement, optimal strategy or an optimal architecture. User chooses next experiment; no extra run launched.
- Random-opening preparation: user requested prominent hardcodedSETTINGS/botcodeVERSION IDs RAND-001/MAX-001/NN-002-R2, with2uniformrandomownactualmoves pergame thenNNgreedy; passesexcluded. Bunny delivered botget_id/freshclosurefactory (T031) and CLI IDsconsole/summary/metadata plus perseatpergamefactory (T032). Rawrecordschema/NPZ unchanged, weightsstillsharedloadedonce. Mockedchecks reportedpassed; CLI shadowing bug found/fixed in fakebatchcheck and documented. Luna source review no blocker, prepared syntax-checked scripts/nn_opening_smoke.py for100gamesvsrandom seed78901 andID/normal0forfeitchecks. Rununexecuted; weightedselection deferred untilpass.
- User random-opening smoke passed: NN-002-R2vsRAND-001,100normal0forfeits77wins3draws20losses (78.5%drawadjustedscore),seed78901alternatingcolours andIDsvisible. Artifacts work/nn-opening-smoke/run-149bd65db0aa488f8e26a9d045fcbeea/ andfixedsummary/match-check. Currentepoch1best.pt unchanged. Priorgreedybatch78/3/19useddifferentseed; no causalopening-strengthcomparisonclaimed. Luna results formatting requested; nextweightedchoice temperature selection pending.
- Weighted-choice preparation: Bunny delivered NN-003-R2-T0.05, preserving two uniform opening moves, then stable softmax sampling with the runner's seeded RNG. Reports synthetic weights/settings/counter checks passed. First dispatch inherited Plan mode and made no edits; redispatched with explicit Build. Luna source review found no blocker and prepared syntax-checked scripts/nn_selfplay_smoke.py for user-run 100 NN-versus-NN games with seed 89012. Fixed diversity-summary.txt will report exact trace duplicates, opening-prefix concentration at 4/8/12 actions and cross-game position overlap after 12 actions; no arbitrary diversity threshold or independence claim. No weighted game or checkpoint load by Luna; next user execution.
- User weighted self-play completed: work/nn-selfplay-smoke/run-e19b28dea22144928689e6d1e083ddf8/, 100 normal/zero forfeits, IDs NN-003-R2-T0.05, seed89012 alternating colours. Outcome bot1 34wins/bot2 64/draw2. Diversity:100 unique traces,100 unique8/12-action prefixes,79 unique4-action prefixes, no exact cross-game late-board/to_play repeats among4,837rows after12actions. Diversity does not prove independent samples or spatially distinct games under symmetry.
- Luna parsed saved records and reviewed source without reruns/checkpoint load. Bot1 asBlack20/1/29 and asWhite14/1/35 (W/D/L); bot2 advantage in bothcolours. All200seeds matched derivation and pairs differed. Under conditional independentfair decisive-outcome hypothesis, two-sided binomial tail for64of98 is~0.00319; not proof ofbug or independence. No direct seat-specific state/identitybranch found. Imbalance unexplained; next supervised diagnosis proposed, no new experiment dispatched. Permanent review docs/nn-selfplay-results.md.
- User fresh-seed repeats: seed89013 saved run-fb91f4378ad149faac4d17d016dc3022 yielded36/59/5 (bot1/bot2/draw); seed89014 run-cca0c2775fd34a0e8433ee19299b0c16 yielded52/46/2. Both100normal0forfeits. Luna reviewed all3retainedbatches, each100unique traces; latest76four-action prefixes,100eight/twelve-action prefixes, no exact sharedlatepositions among4,842rows. Allrecords/reports agree; review docs/nn-selfplay-seed-review.md. Outcome reversal weakensfixedbot2advantage, but total122/169/9 stillfavoursbot2; selectedseedbatches neitherestablishformalprobabilities nor ruleoutbug. No agent rerun/checkpointload/training.
- Batched-inference preparation: user reported about23seconds/100selfplaygames and requested lowercost for5000collection. Bunny delivered NN-004-R2-T0.05 with one candidate batch forward and unchanged model/settings; reports tiny equivalence/forward-count checks passed. Luna source review no blocker and updated existing self-play helper for ID004 and explicit subprocess/helper timing plus linear5000estimate. User-run100games seed89014 ready; no speed result or parallelism yet. Bot version increment reminder explicit for every correction revision.
- User batched-inference timing passed: seed89014, NN-004-R2-T0.05,100normal0forfeits,52/46/2. Run work/nn-selfplay-smoke/run-6a61be6d34b1494b92af7db0f7ce3eec/. CLI16.257s includesstartup/import/checkpointload/games/logging, helper16.296s throughanalysis beforepublication. 6.151games/s, linear5000estimate812.9s(13.55min), not a measured5000run. Compared approximate user-reported23s baseline, elapsed down29.3%, throughput~1.415x; not controlledbenchmark. Luna compared savedrecords to NN003 seed89014 and all100physicalactiontraces matched; report docs/nn-batched-inference-results.md. No game rerun/training/parallelism/5000collection byagents.

## Generation 003 — 2026-10-01 — First 5,000-game NN self-play collection

- Purpose: collect outcomes from the existing learned bot for a second training batch and subsequent user-directed strength evaluation.
- Helper defaults: 5,000 sequential NN-004-R2-T0.05 versus itself, seed 90001, parent checkpoints/first-model/run-2103bc51994e46a099f8b3d78618efd3/best.pt, output runs/selfplay-5000/. Actual completed metadata has not yet been reviewed.
- User launched the helper and confirmed progress at 500 games. Collection completion, elapsed time, run directory and final outcomes are pending. No new model has been trained.
- User selected continuing parent model weights with a new Adam optimizer; trainer support remains a bounded future Bunny task. Parent artifacts must be preserved.
- During collection, user requested a four-core workflow and GitHub Actions route. Spec only prepared in docs/parallel-and-github-design.md; no parallel or hosted run, upload or performance result exists.

### Collection completion — 2026-10-01

- User reported successful completion; saved match/diversity reports confirm 5,000 normal games, zero forfeits, bot1/bot2/draw 2,397/2,424/179 and 2,500 Black assignments per seat. CLI elapsed 914.067s (15.23min). Run: runs/selfplay-5000/run-9ad69fb4e22d413c8905b2e392c33b36, seed90001, parent checkpoint unchanged.
- Helper reports no exact trace duplicates; 4/8/12-action unique-prefix counts244/4,789/4,998 (4,998 games reach12actions). Two shared late-position keys involve4 of241,823 late rows. Reports were read, no raw replay rerun. Luna concise saved-report review requested. Conversion and continued training remain unrun.
- User requested model in repository and multi-core coding. gh confirms PUBLIC; baseline copied to models/first-model.pt (original preserved), no commit/push. Bunny CLI-only task dispatch authorized; GitHub workflow remains next.

- T009 infrastructure delivered: --workers defaults1, >1 uses spawned processes with one inference thread each and ordered parent writing. Bunny reports syntax/import/help and argument checks; no game runtime or parallel performance result. Luna focused source review requested, helper worker pass-through separately dispatched. Saved collection summary is docs/selfplay-5000-results.md.

- I007 source-review finding: parallel initializer required optional torch for random-only core use. Bunny corrected to inspect loaded torch after bot imports; reports random/max initializer and torch-importing stub checks passed. No real pool, NN game or hosted runtime. T043 helper --workers delivered; T044 manual GitHub collection workflow dispatched separately.

- T044 infrastructure delivered: workflow_dispatch-only hosted collection, CPU dependencies, runtime provenance, artifact upload and summary; README launch/download instructions. Bunny reports YAML structure, extracted shell syntax and Python compilation checks passed; no remote job or parallel games run. Not committed/pushed. Hosted conversion and continued training remain outside this task.

- User authorized commit/push: 1e6e72f published to origin/master, including baseline model copy and manual workflow. No hosted dispatch or multi-core game runtime; these remain unproven and deferred until after second training. T041a weights-only initialization support dispatched to Bunny; conversion and training still unrun.

- User-run conversion completed: 5,000 eligible games (no forfeits skipped), seed12345 default80/20 whole-game split; training4,000games/241,396positions, validation1,000games/60,425positions, total301,821positions. Archives and conversion-summary.txt retained under runs/selfplay-5000/run-9ad69fb4e22d413c8905b2e392c33b36/dataset/. Counts are from user CLI output, no additional array checks run. Second training still unrun.

- T041a continuation infrastructure delivered: parent model weights loaded with CPU weights_only/strict state loading before starting losses, fresh Adam and reset epoch/early-stop state; initialization provenance in candidate checkpoints/history/report. Bunny reports synthetic load and rejection checks, no real checkpoint or epoch execution. User-run second training pending.

### Second training completion — 2026-10-01

- User executed training.train on converted self-play dataset with --initial-checkpoint parent best.pt; fresh Adam, agreed defaults, CPU threads4/interop4. Candidate output checkpoints/second-model/run-selfplay-5000/.
- Loaded-parent train/validationMSE0.202730/0.203582; constant validation baseline0.242034. Epoch1–4 training0.178482,0.163548,0.152865,0.143331; validation0.193218,0.197173,0.203736,0.209542. Four completed epochs, patience stop, best epoch1, total7.5s.
- Candidate best validation is ~5.1% lower than loaded parent on THIS same validation split. Later train/validation divergence suggests overfitting; this does not establish insufficient model capacity or improved playing strength. best.pt/last.pt/history/summary retained; parent preserved. Luna saved-report summary requested, no extra job run. Multi-core and GitHub proving runs still unperformed.

- User chose100candidate-vs-random and100candidate-vs-parent games, alternating colours and unchanged exploration settings. Candidate wrapper/shared selected model plumbing dispatched; no evaluation run yet.

### Candidate versus random — 2026-10-01

- User ran100games, seed91001, workers1, alternating colours. Throwaway candidate clone loads checkpoints/second-model/run-selfplay-5000/best.pt; unchanged NN-004-R2-T0.05 code/settings vs RAND-001. Code ID alone does not distinguish candidate weights; candidate module/checkpoint selection do.
- User CLI result:100normal,0forfeits,86candidate wins/5draws/9random wins (88.5% draw-adjusted score). Raw run runs/candidate-vs-random/run-0b05370177d245488ecbe22d77a6e309, fixed summary in output root.
- Original parent comparison78/3/19 used an earlier greedy bot and different seed; this is encouraging but not a controlled causal strength comparison. Parent/candidate head-to-head100 remains agreed and unrun. No extra games/checks by agents.

### Candidate versus parent — 2026-10-01

- User ran agreed100head-to-head games at seed91002, workers1, alternating colours. Candidate bots.nn_candidate_bot hardcodes second-model/run-selfplay-5000/best.pt; parent bots.nn_bot explicitly selects first-model/run-2103bc51994e46a099f8b3d78618efd3/best.pt through OTHELLO_NN_CHECKPOINT. Both NN-004-R2-T0.05 settings; copied code ID does not distinguish weights.
- User CLI result:100normal,0forfeits,62candidate wins/6draws/32parent wins, draw-adjusted score65%. Raw run runs/candidate-vs-parent/run-d97a51b8005a43f3bf3f8df5a1648a69; fixed root run-summary.txt. No independent replay or additional matches.
- Alongside candidate/random86/5/9 and same-split validation improvement, this batch supports improvement after first self-play continuation. It does not establish a plateau, repeated-seed robustness or maximal strength. Both agreed100-game evaluations completed. Further training/experiments are user decisions; local multi-core and hosted proving runs still unperformed.

## Generation 004 — 2026-10-01 — Latest-model four-worker self-play collection

- Purpose: exercise local4worker collection and gather fresh self-play data for continued training of latest selected model. User ran/monitored5000games, seed90002, four spawned workers with1numerical thread each, alternating colours. Both NN-004-R2-T0.05 seats selected checkpoints/second-model/run-selfplay-5000/best.pt.
- Retained run: runs/selfplay-5000-second/run-4930cc31f42e4534a4feaf919d672a78; fixed run-summary.txt/match-check.txt/diversity-summary.txt under output root. User CLI result5000normal,0forfeits,bot1/bot2/draw2459/2369/172, helperPASS.
- User fish wall-clock approximately250s (4m10s), compared with previous sequential CLI914.067s (~3.66x ratio, different timing boundaries/checkpoint/seed/game traces). Practical throughput gain observed, not a controlled scheduling-equivalence benchmark. Local parallel runtime now exercised successfully; GitHub execution still unrun.
- Next: user-run conversion with whole-game80/20 split seed12345, then continue generating-model weights with fresh Adam into separate candidate directory if collection review satisfactory. No conversion or next training run yet.

- Saved reports read: CLI249.131s (4m9.1s), versus prior CLI914.067s, observed~3.67x throughput/~72.7% less elapsed time.0exact duplicate traces;4/8/12-action unique prefixes244/4,815/4,996, with4,998games reaching12actions;3shared late-position keys across6 of241,935late rows. Descriptive diversity only. No new checks executed.

- User completed Generation004 conversion:5000eligible games,0skipped forfeits, seed12345 whole-game80/20 split. Training4000games/241,586positions, validation1000games/60,343positions, total301,929positions. Artifacts in runs/selfplay-5000-second/run-4930cc31f42e4534a4feaf919d672a78/dataset/. Counts from user output; no extra checks. Next user training starts from second-model/run-selfplay-5000/best.pt with new Adam, output checkpoints/third-model/run-selfplay-5000; not yet run.

### Third-model training completion — 2026-10-01

- User ran Generation004 dataset training with parent checkpoints/second-model/run-selfplay-5000/best.pt, fresh Adam and unchanged defaults. Output checkpoints/third-model/run-selfplay-5000/. Training241,586rows/4000games; validation60,343rows/1000games, CPUthreads4/interop4.
- Initial parent train/validationMSE0.201083/0.199267, constant validation0.240993. Epoch1–4 training0.176794,0.165259,0.155384,0.146419; validation0.186284,0.190043,0.196149,0.199544. Best epoch1; patience stop after4completed epochs; user CLI total7.1s.
- Best validation is ~6.5% lower than starting second model on THIS validation split. Later divergence again suggests overfitting. This is not a comparison of validation losses across rounds and does not establish improved playing strength. Third-model best.pt is latest selected checkpoint under user progression preference; prior models preserved. No evaluation of third model yet.

- User selected greedy evaluation against random (R0/T0). Bunny copied canonical bot to disposable nn_eval_bot selecting third-model best.pt, ID NN-EVAL-001-R0-T0; only header/settings/checkpoint edits. Syntax/source checks reported; actual import/match unrun. Canonical/self-play settings unchanged.

### Third-model greedy versus random — 2026-10-01

- User ran100games, seed92001, workers1, alternating colours. bots.nn_eval_bot NN-EVAL-001-R0-T0, hardcoded checkpoints/third-model/run-selfplay-5000/best.pt, no random opening/highest-score selection from first move, versus RAND-001.
- User CLI outcome100normal,0forfeits,97NNwins/2draws/1loss, draw-adjusted score98%. Raw run runs/third-model-greedy-vs-random/run-d5597b0937c542d6a73b4d26afc50c98; fixed run-summary.txt under output root. No replay or extra matches by agents.
- Strong performance against random in this batch. Previous candidate86/5/9 used second model, R2/T0.05 and different seed, so improvement cannot be attributed solely to third training or greedy settings. No third-vs-second match yet and no plateau conclusion.

### Third model versus second model — 2026-10-01

- User ran100head-to-head games at seed92002, workers1, alternating colours. Candidate disposable clone selects checkpoints/third-model/run-selfplay-5000/best.pt; parent canonical module explicitly selects second-model/run-selfplay-5000/best.pt. Both copied NN-004-R2-T0.05 settings (2randomownmoves,T0.05).
- User CLI result100normal,0forfeits,63third-model wins/4draws/33second-model wins, draw-adjusted score65%. Raw run runs/third-model-vs-parent/run-fb413356522944729cb509d5ad45df37; root run-summary.txt. No additional matches/replay by agents.
- Two successive user-run parent comparisons each yielded65%candidate score (second-vs-first62/6/32; third-vs-second63/4/33). This supports continued improvement in these batches; no observed plateau yet. It does not establish repeated-seed robustness, equal absolute strength gains or an eventual ceiling. No further collection/training automatically authorized.

### Hosted pipeline preparation — 2026-10-01

- Bunny extended existing workflow to collect, convert whole-game80/20 seed12345, train from selected parent weights with fresh Adam, and upload parent/candidate/data/reports. Latest third-model best.pt copied to models/best.pt; original retained. Reports static YAML/shell/interface checks passed. Hosted runtime unknown; primary preparing user-requested first remote5000run (seed90003/workers4). No remote evaluation or promotion.

## Generation 005 — 2026-10-01 — First GitHub-hosted self-play and training

- User requested first hosted5000latest-best collection, conversion, candidate training and downloads for local100parent comparison. Primary committed/pushed669a1fd (including prior local ff30fa2) and dispatched selfplay.yml on master.
- Run https://github.com/pajh/othello/actions/runs/36841281392, workflow_dispatch, seed90003,games5000,workers4,checkpointmodels/best.pt (copy of third-model selected best.pt). Status observed in_progress; results/timing unknown.
- Workflow stages: collect NN-004-R2-T0.05 vs itself, whole-game80/20 conversion seed12345, continued parent weights with new Adam/current defaults into checkpoints/github-candidate, upload parent/candidate/raw/data/reports. No remote evaluation or automatic promotion.
- Next after completion: download artifact, Luna saved-report review, local100candidate-vs-exact-parent with matching R2/T0.05. Hosted1000evaluation remains later desired stage. No downloads/local match yet.

### First hosted run completed/downloaded — 2026-10-01

- GitHub run36841281392 concluded success; collection/conversion/training/upload passed. Job09:13:16–09:17:30UTC (~254s inclusive setup). Downloaded artifactselfplay-36841281392-1 to runs/github-first/.
- Saved match report:5000normal0forfeits,seed90003,4workers/1numerical thread,2377/2444/179outcomes,CLI161.608s (2m41.6s). Split4000traininggames/241,811rows,1000validationgames/60,502rows.
- Saved training report:third-model parent weights/fresh Adam,initial validation0.205014,bestepoch1validation0.198206 (~3.3%lower same split),4epochs/patience,total5.693s,finalvalidation0.215063. No playing-strength conclusion yet.
- Exact downloaded parent runs/github-first/runs/github-selfplay/parent.pt, candidate runs/github-first/checkpoints/github-candidate/best.pt; originals preserved. Disposable clone recreated via copy+one path-line edit to hostedcandidate; local100candidate-parent command ready but unrun. Luna saved-report review requested. No promotion.

### Hosted candidate versus exact parent locally — 2026-10-01

- User ran100games,seed93001,workers1,alternating colours,matching NN-004-R2-T0.05. Candidate disposable clone selects runs/github-first/checkpoints/github-candidate/best.pt; canonical parent selected exact downloaded runs/github-first/runs/github-selfplay/parent.pt.
- User CLI result100normal,0forfeits,54candidate wins/4draws/42parent wins,draw-adjusted score56%. Raw run runs/github-candidate-vs-parent/run-2cc0170b01414cad97143493008d2925; root run-summary.txt. No extra matches or replay by agents.
- Successive parent-comparison scores65%,65%,56%. Latest batch favours candidate but is compatible with a smaller gain or sampling variation; no established plateau/definite slowing trend from these100-game batches. User described apparent tailing off. No additional run or repository-best replacement automatically performed.

### Hosted candidate greedy versus random — 2026-10-01

- User ran100games,seed93002,workers1,alternating colours. NN-EVAL-002-R0-T0 disposable greedy bot selects downloaded hostedcandidate runs/github-first/checkpoints/github-candidate/best.pt versus RAND-001.
- User CLI result100normal,0forfeits,100NNwins/0draws/0losses. Raw run runs/github-candidate-greedy-vs-random/run-69af4aeefd634e81b1a9b0ca0037b009; root run-summary.txt. No extra games or replay by agents.
- Random-bot milestone achieved in this100-game batch, not a universal win guarantee. Hostedcandidate parent result54/4/42 used matchingR2/T0.05. No model precision/export/C test yet.

## Generation 006 — 2026-10-01 — Random C interface proof of concept

- User selected random-first C bot, CG loop/random score(), Python subprocess adapter and make build; NN headers/export/decompression/combine deferred. Files c/bot.c, src/bots/c_random_bot.py, Makefile, docs/c-random-bot.md. No trained model in this infrastructure iteration.
- Bunny reports clean C11 build, one local game versus RAND-001 at seed94001: normal termination, draw, zero forfeits. Child handled31turns then reaped; no lingering C process reported. Raw smoke copied from disposable work/c-random-smoke to retained runs/c-random-smoke. No additional games by primary.
- Primary read CLI/wrapper: normal factory path keeps one C child per seat/game; module-level legacy play makes a temporary child per call. Referee Cell.java maps a+x/y+1; Referee.java sends increasing-y board rows. Confirms a1 top-left; earlier unverified note superseded. Exceptions from malformed child responses become rig forfeits (handoff wording implying otherwise was inaccurate).
- User-run100 alternating-colour games against Python random remains unrun; seed94001, workers1, runs/c-random-vs-random. Actual CG submission/timing unknown. No NN work or publication. User clarified future Bunny prompts must contain one concrete deliverable at a time.

### Quiet C logging — 2026-10-01

- User observed per-move terminal spam. Bunny T055 changed only c/bot.c (VERSION002): removed startup/player/turn/pass chatter, retained actual errors and stdout protocol. Python adapter unchanged C-RAND-001. Clean make bot reported, no game/probe rerun. No new strength result or CG execution.

### User local batch and actual CodinGame run — 2026-10-01

- User reports clean local random comparison49–44, no terminal spam; refers to agreed100games. Exact draw/forfeit totals not pasted, so not invented.
- User submitted self-contained c/bot.c to actual CG Othello IDE, Wood2. Screenshot shows normal full-board end result: PaulH14discs, BOSS1 50discs,60actions, and a BOSS1 forced pass before final moves. User confirms real-runner mechanics work. No timeout or invalid-action failure reported.
- This exercises C compilation/execution and ordinary CG stdin/stdout move protocol in one real game. It establishes the intended random-bot interface milestone, not strength or comprehensive game-rule validation. Future NN forward.h, decompress.h, generated model.h and combine remain unimplemented.

### Standalone C neural forward smoke — 2026-10-01

- T056 Bunny delivered header-only c/nn.h:49537float blob and3dense descriptors,128->256->64->1 ReLU/ReLU/sigmoid, element offsets matching PyTorch rows. setup allocates first input/per-layer outputs once, links buffers, leaves blob intact. forward copies input and uses descriptor loop/expf, no allocations. No production teardown or bot integration.
- Standalone c/test_nn.c random-data smoke reports256calls, min0.490070/max0.498135/mean0.495070, zero nonfinite/out-of-range values, exit0. Clean C11 ASan/UBSan build and detect_leaks=1 run reported no findings; test-only cleanup frees owned buffers once. Random parameters intentionally small; no numerical PyTorch agreement established.
- Next user-selected stage T057: actual trained-model export/load and10,000random-input C/PyTorch comparison. Not implemented/dispatched/run. No new trained model.

### Trained parameter blob export — 2026-10-01

- T057a exporter scripts/export_nn_blob.py reads CPU weights-only checkpoint; concatenates network.0/2/4 weight/bias arrays in agreed order, row-major output/input, writes raw NumPy< f4 (little-endianFP32; dtype `<f4`). Source runs/github-first/checkpoints/github-candidate/best.pt.
- Bunny reports one export to runs/c-model-export/model.bin and blob-layout.txt, actual size198148bytes matches49537elements. Size was the sole check. No C loading, numerical comparison, compression or generated header; numerical correctness remains untested.

### Real-board PyTorch reference corpus — 2026-10-01

- User chose actual valid replay-derived boards rather than arbitrary random vectors for next C comparison. Luna T057b implemented scripts/generate_nn_test_csv.py and explicitly user-authorized run selecting10000rows without replacement, seed12345, from runs/github-first/runs/github-selfplay/run-a618633805de46679deccb20377b348a/dataset/validation.npz. Reference checkpoint runs/github-first/checkpoints/github-candidate/best.pt, matching exported parameter blob.
- CSV inputs-and-scores.csv under runs/c-forward-corpus contains128row-major own/opponent inputs plus PyTorch score (.9g). Independent sanity check passed10000rows/129columns and matched selected dataset inputs/plane order; all binary, non-overlapping, scores finite0..1, range0.000384106941–0.999888301. Summary corpus-summary.txt retained. No new games or training.
- C blob load/CSV reading/numerical comparison is still next separate task, not run.

### C real-model comparison rig built — 2026-10-01

- T057c Bunny delivered c/test_nn_compare.c and isolated Make target. Exact blob read into Model.blob, setup after load, CSV inputs/expected scores, fixed absdiff<=1e-5+1e-5*abs(reference), summary/errors and test-only buffer cleanup.
- Clean sanitizer-enabled C11 build reported. Numerical10000position comparison and runtime sanitizer coverage explicitly unrun; no score agreement or PASS claimed. User launch command uses runs/c-model-export/model.bin and runs/c-forward-corpus/inputs-and-scores.csv, report runs/c-forward-check/forward-summary.txt.

### Comparison startup byte-order failure and correction — 2026-10-01

- First user run failed before blob load: host falsely rejected as not little-endian binary32. Primary source read found reversed byte test expected3f/80/00/00(big-endian). I008 Bunny corrected to00/00/80/3f with early4byte-size guard; one clean rebuild reported. Failed attempt preserved here; no numerical comparison reached and full rerun remains user-run/pending.

### Real-model C/PyTorch numerical comparison passed — 2026-10-01

- User reran sanitizer-enabled build/test-nn-compare after I008 byte-order correction, loading runs/c-model-export/model.bin (49537floats/198148bytes) and runs/c-forward-corpus/inputs-and-scores.csv. Report retained runs/c-forward-check/forward-summary.txt.
-10000rows read/compared; fixed tolerance absdiff<=1e-5+1e-5*abs(reference). Mean absolute error1.61441334e-8, maximum2.38418579e-7; worst row1874 C0.543397963/reference0.543397725. Zero outside tolerance, zero nonfinite/range failures, RESULT PASS. User output shows no sanitizer diagnostics with detect_leaks=1.
- Supports correctness of real FP32 export/layout/setup/forward on this corpus; small rounding differences observed. No C move application/neural-bot integration, compression, FP16 experiment or larger corpus executed. Future work remains separate user-selected tasks.

### Submission-size constraint and compression sizing — 2026-10-01

- User confirms CG source maximum100000characters. Primary read-only Python probe on exported current FP32 blob, zlib raw DEFLATE level9:198148rawbytes ->184328compressedbytes ->245772Base64characters (Base85230410). FP16 rounded weight-storage sizing only:99074rawbytes ->91799compressedbytes ->122400Base64characters (Base85114749). No generated payload/export change or inference/strength test.
- These sizes exclude C decoder/bot/header overhead. Proposed losslessFP32 and FP16+Base64 paths cannot fit this limit; compression/precision/encoding decision unresolved. No compression implementation has been dispatched.

## Generation 007 — 2026-10-01 — Shared256-value codebook quantization experiment

- User chose nonuniform256FP32table plus one-byte indices, weights/biases together; model75000/code25000character targets, hardtotal100000. Existing scikit-learn1.9.1 installed by primary into venv, no environment recreated. No retraining or original-weight changes.
- Bunny T058 scripts/quantize_nn_blob.py fit KMeans256clusters, seed12345,n_init1,max_iter300,algorithmlloyd on original exported blob. CentersFP32; nearest stored-center reassignment corrected3of49537differences versus fit labels.
- Artifacts runs/c-model-quantized/codebook.bin1024bytes, indices.bin49537bytes, expandedmodel.bin198148bytes, quantization-summary.txt. Combinedtable+indices50561bytes, Base6467416chars before header/compression. Weight MAE0.000450010535,max0.00786840916,MSE3.21645363e-7.
- One quantization run reported; original blob/CSV preserved. User existing Ccomparison against original10000real-board PyTorch scores remains unrun. Fixed FP32 tolerance unchanged; its failure count will measure quantization drift, not automatically decide acceptability. No Ctabledecoder or playing-strength result/adoption.

### Shared-codebook score drift measured — 2026-10-01

- User ran existing sanitizer Ccomparison on expanded quantized runs/c-model-quantized/model.bin against original10000real-board reference CSV.10000read/compared, meanabsolute error0.000824199575,max0.00866732001,worstrow5577 C0.452201247/reference0.460868567.9780outside unchanged1e-5+1e-5relative gate,0nonfinite/range failures, RESULT FAIL. No sanitizer diagnostics shown. Saved runs/c-quantized-check/forward-summary.txt.
- This gate measures FP32implementation parity, so lossy quantization fail was expected. Measured drift small on this corpus (~0.0824percentagepointmean/~0.8667pointmax), promising but move-ranking/playing-strength effect untested. No tolerance modified, quantized model adopted, further matches or Cdecoder implementation.

### Quantized payload compression decision evidence — 2026-10-01

- User reframed acceptance around strength of deployable quantizedbot, not oversizedFP32/hypothetical smaller model. Fullprecision comparison can be diagnostic if quantizedbot fails later; no such strength failure currently observed.
- Primary read-only zlib rawDEFLATE level9 probe of actual codebook+indices:50561rawbytes,67416Base64chars; compressed48557bytes,64744Base64chars. Saving2672chars(~3.96%) before added Cdecoder/format code. Individually codebook1024->1005bytes (28Base64char saving), indices49537->47451bytes (2784char saving); separate streams were sizing only, no format adoption.
- Plain quantized Base64payload already fits75000modelbudget with7584chars for header metadata/string syntax. Decoder would need below2672incrementalchars for net reduction using combinedstream. Startup not measured. Primary recommends omitting DEFLATE and retaining Base64+codebook expansion/length/checksum; not yet user-approved or implemented.

### Uncompressed Base64 header generated — 2026-10-01

- User agreed omitcompression. BunnyT059a scripts/embed_nn_codebook.py generated runs/c-model-embedded/model.h72959ASCIIcharacterswithin75000budget; Base64payload67416characters,50561decodedbytes(codebookthenindices). CRC32packeddca2a0e3/expandedFP322bce1e0e.
- OnePythonruncheckedactualheaderstringsdecodeexactsourcepayload; expansionbyteexactmatchespriorquantizedmodel198148bytes. No Cconsumptionyet. SeparateauthorizedT059b Cdecoder/reconstructiontask dispatchedafterhandoff, keeps bot.c/nn.h untouched.

### Embedded Base64 C reconstruction passed — 2026-10-01

- T059b Bunny delivered c/model_decode.h load_embedded_model(Model*,unsigned char**payload_storage), c/test_nn_embedded.c and isolatedMake target. One startupmalloc, Base64decode/lengthCRCchecks, memcpycodebookexpansionintoModel.blob, decodedCRC; setupcallerowned, no compression or productionteardown.
- FirstattemptrejectedpayloadbecausefinalBase64padding arithmetic reversed (one=means2bytes). Bunnycorrectedobservedbug and sanitizedcheckthenpassed:memcmpbyteidenticaltopriorquantizedmodel,50561payloadbytes/67416encodedchars/198148decodedbytes, CRC32packeddca2a0e3/expanded2bce1e0e. Outputruns/c-embedded-check/model.bin; noASanUBSan/leakfindings reported. Failurepreservedhere.
- Full10000score comparison notrun; usercommandexistingtest-nn-compare withnewreconstructedbloband originalcorpus. Expectsamequantizedmetrics. Bot/nn.h remainunchanged.

### Single-pass CG submission scrunch completed — 2026-10-01

- T060 scripts/scrunch.py implements userrule: mainquotedinclude list determines pastedheaderorder; quotedincludesremovedfromheaders,standardincludes/guardsretained. Lexicalcommentstrip preservesstring/charliteralcontents and separates tokens; nootherminification/recursion.
- Bunnyreportscurrentrandom c/bot.c submission3816ASCIIchars/bytes under100000, exactsource cleancompileandone-turnprotocolprobeexit0. Retained runs/c-submission/submission.c/size-summary.txt. Scratchall3realheadersexpansion81486chars,zeroquotedincludes,clean-lmcompile; scratchdeleted, noNNbotwired.
- Forum/GCCresearch recommends submissionprefix #pragma GCC optimize("O3,inline"). No specialcommentdirective established. CPUtune differs frommarch; noarchitecture/AVXassumptionorfast-math adopted. Pragmainjectionnotimplementedyet. Neuralmoveapplication/scoring remainsfuturetask.

### Greedy quantized neural C bot wired — 2026-10-01

- T061 bot.c C-NN003 includesnn.h/model.h/model_decode.h, modelstartupdecode/setup, retainsCGboard/applieseachcandidateincludingflips,actorown/opponentplanes,forwardgreedytiesearliest. Noopeningrandomness/sampling or perturnallocation. Makebotincludesmodelpath/links-lm,existingbuild/c-random-botfilename retainedforadapter.
- Bunnyreportsexplicitgcc-O2-Wall-Wextracleanbuildandoneintegrationgame seed95001:normal0forfeits,60positions,NNblack44vsrandomwhite20,childreaped. Run runs/c-neural-smoke/run-9f8f704fca994448a3acbea1756915c9/. No strengthclaimfromonegame. WrapperreportIDstaleC-RAND001, deliberatelyuntouchedthisscope.
- SeparateT062O3inlineprefix andactualneuralCGscrunch/size/exactgcccompile dispatched. NoCGneuralrunyet.

### Full neural submission packaged and compiled — 2026-10-01

- T062 scrunch.py prepends #pragma GCC optimize("O3,inline") afterexpansion/commentstrip andcountsitinfinalsize. Noarch/AVX/fastmathorotherminification. InitialscripteditlostnewlinecausingSyntaxError,correctedbeforegeneration.
- ActualgreedyC-NN003quantizedsubmission retained runs/c-submission/submission.c88256ASCIIcharacters/bytes,11744below100000limit; firstlinepragma,zeroquotedlocalincludes. Exactsourcegcc-C11-O2-Wall-Wextra-lmbuildclean, executablebuild/c-submission87184bytes perhandoff.
- No game/numericaltestofthisexactO3packagedbuildyet; T061neuralintegrationonegamepreviouslypassed. ActualCGneuralexecution/strengthunknown. Headerandmodeldecodedtestedpreviously. WrapperstillreportsC-RAND001andneedsseparateidentityrevisionbeforemeaningfullocalreports.

### Comment-only lines removed without other minification — 2026-10-01

- T063 scrunch lexicalstrip trackscomment/codeperline, dropscomment-onlylinesincludingnewlines, preservesintentionalblanklines/codeformat/literals. Firsteditdouble-emittedcode-line newlines, growingfile89196chars; focusedcheckcaughtbug, correctedbeforefinalgeneration.
- Regenerated actualneural runs/c-submission/submission.c88000ASCIIchars/bytes,12000belowlimit (previous88256). O3inlinefirstline/zeroquotedincludesremain; exactgcc-C11-O2-Wall-Wextra-lmcompileclean, executable87184bytes reported. No post-editgame/numericalrun orCGneuralresultyet.

### Actual comment-strip bug fixed and output inspected — 2026-10-01

- UsernoticedT063stilllookedsame. Primaryreadactual88000charfile/1388lines/321blank,first35linesblankafterpragma. SourcebugI009resetlinecommentflagwithoutremarkingblockinteriorlines, contradictingpriorhandoffclaim. NarrowBunnyfixmarkscommentstateeachbranchentry, preservescodeflags/intentionalblanklines/literals.
- Focusedactualmultilinechecksreportedpassed. Regeneratedsubmission87775chars/bytes,1163lines/96blank,zeroquotedincludes; exactGCCcompilecleanreported. Primaryindependentlyreadcurrentfilecounts/head:pragmafirstline,stdioincludeatline3,NNguardatline8, obsoleteblankheadgone. No newgame/numericaltest.

### Neural submission running in actual CG league — 2026-10-01

- Userconfirms packagedgreedyquantizedneuralbot isplayingCodinGameOthelloWood2. Unlikeearlierrandomproof,thisusesembeddedcodebookmodel/decoder/forward/candidateflips. No matchcounts/leaguepromotion/performancegiven; do notinferstrength. Userrequestsoneconsolidatedcommandguide; docs-onlyLuna reviewtaskT064started.

### Command guide and first neural arena placement — 2026-10-01

- T064 documentation consolidated in docs/command-guide.md and linked from README/documentation index. Current scripts/flags/Makefile/workflow checked; no jobs run. Current hosted candidate and older committed models/best.pt distinguished; historical helper IDs/paths and stale C wrapper identity documented.
- User reports quantized greedy neural submission rank 78 in Wood 2 and a convincing IDE boss win, without promotion. This is initial arena evidence, not a measured quantization-strength comparison. CodinGame describes promotion as ranking above the boss after arena matches, distinct from an IDE head-to-head win.

## Generation 008 — 2026-10-01 — hosted symmetry training and parent evaluation

- User authorized full commit/push and next hosted round: latest selected first-hosted candidate copied from runs/github-first/checkpoints/github-candidate/best.pt to models/best.pt. Prior parent/candidate artifacts remain retained.
- Plan:5000 self-play games, seed90004,4workers,R2/T0.05; whole-game80/20split seed12345, then all8board symmetries in each split; continue weights/newAdam/defaultlr/batch, patience1/max30epochs;1000 candidate-vs-exact-parent games alternating/R2/T0.05/workers4/evaluationseed190004. No automatic promotion.
- T065 synthetic transforms/labels/schema checks passed per handoff after correcting spatial-axis bug. T066 workflow static checks passed per handoff; primary review caught duplicateWORKERS key, correction requested before dispatch. Real augmented conversion, training and hosted evaluation unrun at this point.

- Full commit b9aea934eb357d3b747802d17d0a29b4ff2d3e53 pushed; hosted run36887079634 dispatched and observed in_progress: https://github.com/pajh/othello/actions/runs/36887079634. Duplicate YAML key corrected before commit; primary unique-key parse passed. Collection/augmented conversion/training/evaluation results pending.
