# T079 — disposable cutoff comparison bots for the existing runner

Implement only this bounded task. User wants multiple-game strength/runtime comparisons at several cutoffs before a later 5,000-game GitHub collection. Do not launch games or hosted jobs.

Allowed files only:
- src/bots/nn_c6_bot.py
- src/bots/nn_c8_bot.py
- src/bots/nn_c10_bot.py
- docs/nn-cutoff-comparison-handoff.md
No project-memory edits; primary maintains records.

Create three prominently marked disposable snapshots of CURRENT src/bots/nn_bot.py (NN005, exact terminal negamax). Copy its implementation; change only COUNT_LEFT to 6/8/10 respectively and add a prominent disposable-copy comment. Preserve VERSION005 as snapshot provenance and let existing IDs embed C6/C8/C10. No imports that mutate canonical settings, no new configuration abstraction. Keep the same required OTHELLO_NN_CHECKPOINT environment selection in every copy, so both seats load the same explicitly selected weights. Canonical stays C0 unchanged. Random opening R2 and temperature0.05 unchanged.

Handoff: exact existing `venv/bin/python -m rig.cli` commands for C6/C8/C10 against bots.nn_bot, 100 games each, workers4, alternating colours (default), seeds98006/98008/98010, distinct output roots runs/nn-c6-vs-c0 etc. Explicit checkpoint models/best.pt (retained selected Generation010). Use shell `time` for batch wall time; refer to existing summary elapsed field if present. Also give a C0 versus C0 100-game baseline command, same worker count/weights, seed98000. Explain runtime comparison is practical throughput across different game traces, not a controlled per-node benchmark. Mention IDs change derived RNG streams, which is expected for strength matches, unlike the completed equivalence check.

Give the user a matching C8-vs-C8 collection timing command as an OPTIONAL later user-run command (same existing runner,100games,workers4,seed98108,distinct output). This measures both-seat solver throughput relevant to 5,000 self-play games; rough estimate walltime*50 only if same hardware/workers/settings, not a guaranteed GitHub runtime. No training or workflow modification in this task.

Checks only py_compile and inspect diffs to canonical to verify cutoff/comment-only differences. No imports that load models, games, benchmarking, Edax, commit or push. No need to reread unrelated source. Stop after a concise handoff describing what was actually checked and that matches remain unrun.
