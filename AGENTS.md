# Collaboration workflow

## Project records

Read AGENTS.md, status.md and TODO.md when starting a task, followed by the relevant task/design document. Consult GENERATIONS.md for experimental history. These files are shared project memory.

The current next-session handover is docs/next-session.md: current artifacts/results, the user-selected5,000gamecollection/secondtraining plan, open training choices and exact OpenCode/hook recovery instructions. Read it when resuming; the requested experiments are for the next session, not automatic jobs.

- status.md: concise current snapshot, implemented components, verification actually performed, current work, blockers and next step. Update after meaningful changes/handoffs. Distinguish plans from completed work and unrun checks from passed checks.
- TODO.md: separate actionable backlog and observed issues. Use stable identifiers (T001, I001), mark completed items and distinguish agreed tasks from open decisions. Record actual issues with evidence; no hypothetical issue list or exhaustive test plan.
- GENERATIONS.md: permanent chronological history, with headings such as `Generation 006 — YYYY-MM-DD — description`. Record purpose, changes/configuration, what actually ran, results/evidence, conclusions and next decisions. Explicitly mark unrun work and unknown results. Append entries, preserve failures/negative results and correct mistakes transparently. Generation 000 covers setup. Allocate later numbers to distinct agreed experimental iterations, not individual edits or tool calls. Infrastructure entries do not imply a trained model exists.
- work/: disposable scratch space for temporary files, conversions and transient tool logs. Contents are ignored by Git. Never store the only copy of a needed dataset, checkpoint, result or decision here. Promote useful summaries to docs/ or project records and retained artifacts to runs/ or checkpoints/ before cleanup. Do not delete files needed by active jobs.
- runs/ and checkpoints/: retained experiment records and model/resume artifacts, distinct from work/. Large generated artifacts stay out of Git; written conclusions and artifact paths remain in GENERATIONS.md.

The primary design agent maintains these records from concise coder/Luna handoffs. Each delegated task specifies which records, if any, it may edit, preventing conflicting updates. Leave status and backlog accurate at task completion; record meaningful experiments in the permanent history. No automated cleanup or issue-management framework is required.

## Report filenames

Generated reports use a fixed filename for the latest version, for example runs/run-summary.txt. If history is wanted, move the existing report to the next unused numbered sibling before writing its replacement: run-summary.1.txt, run-summary.2.txt, etc. Insert the number before the extension and never overwrite an existing archive. The latest version always keeps the unsuffixed name; do not use timestamps or run IDs as its filename. Write a complete replacement to a temporary file before rotating/publishing it so failed generation does not destroy the previous report. Avoid concurrent writers to the same report. Preserve raw artifacts separately. Numbered report archives are not generation numbers. Apply this convention to generated reports, not to status.md/TODO.md/GENERATIONS.md or raw per-game data. History is optional; do not archive every update by default unless the task asks for history.

The agreed layout and staged plan are in docs/project-plan.md. The scaffold stage is complete: engine.py has moved unchanged to src/rig/engine.py, and the local virtual environment directory is venv/ (ignored by Git). Do not set up/recreate environments or implement later stages without an explicit bounded task. Previous flat-layout instructions are superseded.

This is a personal learning project. The user chooses hypotheses, model architectures, training methods, and experiments. Do not supply game strategy or broaden scope unasked.

User clarification 2026-10-01: keep small tasks small. Do not add proof work, fault tolerance, recovery features or exhaustive tests by default. Choose explicit checks together where needed; avoid broadening helpers with optional verification infrastructure.

Bot SETTINGS/version convention agreed 2026-09-30: each bot exposes `get_id()`, with prominent hardcoded SETTINGS and a three-digit VERSION. Increment that file's VERSION on each future completed edit revision. IDs belong prominently in run reports/metadata, not training arrays. The current NN identity is `NN-004-R2-T0.05`: two uniformly random own actual moves (passes do not count), then seeded weighted selection; candidate-board inference is batched. The model remains loaded once and read-only. A fresh `create_player()` callable per seat/game is the minimal state mechanism; keep legacy stateless `play` bots compatible. Changes to these user-selected settings or methods require a bounded task.

The primary Codex chat is for design, supervision, review, and brainstorming. Keep code and large/raw logs out of that chat; deliver short summaries and file links.

Implementation is delegated to OpenCode. Use `opencode/space-bunny-free` (Space Bunny Free) for the next coding task, as requested by the user after the initial LongCat tasks were slow. Do not silently substitute another model. Keep tasks small with the same scope limits regardless of model.

For implementation prompts explicitly pass `--agent build`: the T034 prompt inherited Plan mode and returned only a plan, with no file changes. An explicit model flag does not select the implementation agent. Retain Plan mode for planning-only requests when intended.

Current user-identified Bunny session (2026-10-01): `ses_f09b671eaffeJHQOKjugvgpYJR`, titled `Overview of Python files, rig, NN bot, and training rig`. User identified this conversation after a hello mistakenly went to yesterday's session. BUNNY-LIVE-HELLO-02 has been dispatched here; visible delivery awaits user confirmation. Use this ID for future bounded Bunny tasks. Yesterday's verified session `ses_f0cb2b2e1ffe7wbI0MsfT217MO` is no longer the intended conversation. Send only one task at a time; if the user's visible conversation changes, confirm its identity before claiming live delivery.

Reusable OpenCode and notification workflows are documented in [docs/opencode-workflow.md](docs/opencode-workflow.md) and [docs/notification-workflow.md](docs/notification-workflow.md). Use `opencode session list` from the project directory to find IDs, confirm which conversation the user is viewing, then validate delivery with a distinctive read-only marker if needed. Do not infer the visible session from recency or model name. Use the verified ID with `opencode run --session ... --file ...` to inject future authorised tasks.

For the completion-notification workflow, refresh the registered target from this design chat's CODEX_THREAD_ID before dispatching OpenCode work, preserving the user's manual enabled/disabled setting. The intended completion trigger is an automatic OpenCode V2 event plugin, not an instruction for the coding model to remember. Forward the full final summary text once per completed response in the registered session. Direct codex queue delivery from the user's shell was verified with CODEX-QUEUE-CHECK-01; daemon-version preflight is not a valid prerequisite for that route. Script/hook delivery must be separately verified before claiming automatic notifications work.

Local hook configuration uses the directory `./plugins/codex-notify`, not its entry-file path. This installed build emits `session.execution.succeeded` with `data.sessionID`; runtime diagnostics established that interface. Automatic delivery was visibly confirmed with OPENCODE-HOOK-IDLE-03 after the design chat became idle. An earlier notification accepted while this chat was active did not visibly arrive; reliable delivery during active turns remains unverified. Dispatch work and end the design turn instead of looping to monitor completion. Manual controls: `bash scripts/notify_codex.sh on|off|status`. Notifications currently enabled. No global installation has been made.

Use a Luna subagent for verification/benchmark scripts and for scrubbing, sorting, and formatting results before primary-chat review. The user executes and monitors larger runs, benchmarks, and training. Prepare scripts and finish; do not execute those jobs automatically. The small smoke-game exception below is authorised. Preserve raw results on disk and report failures honestly.

Do not launch training, change experimental decisions, commit, push, or publish without the user's instruction.

Delegate in small bounded chunks. Each task must specify allowed files, exact interfaces, exclusions, and a completion criterion. The overall spec is context, not permission to implement every stage. Prefer standard-library solutions and ordinary functions; no plugin framework, general-purpose abstraction layer, or new dependencies without a concrete need. Finish each chunk with a short on-disk handoff before another chunk begins.

Initial verification is deliberately minimal: one supervised smoke game between two random bots reaching normal game termination without crashes is enough. Do not build an exhaustive test suite or plan. Add focused regression tests only when an observed failure or suspicious behaviour warrants one. A small smoke run is authorised; larger runs, benchmarks and training remain for the user to execute and monitor.
