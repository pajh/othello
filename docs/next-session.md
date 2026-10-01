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
