# T080 — select canonical C8 for the authorized hosted round
Allowed edits only src/bots/nn_bot.py and .github/workflows/selfplay.yml. No records, handoff file, games, jobs, commit or push. This is a tiny SETTINGS/report text correction, not new implementation.
1. Canonical current NN005 already has exact terminal solver. Set COUNT_LEFT from0 to8, increment VERSION005 to006 once. Preserve all other code/settings/checkpoint selection.
2. Existing hosted workflow copies canonical for candidate, so collection and both evaluation seats will automatically use C8. Correct its stale summary text NN-004-R2-T0.05 to NN-006-R2-T0.05-C8 and settings text to include C8. No workflow behavior change, dependencies or new features.
Check py_compile and diff only, no model import. Finish with concise final summary. Primary will verify, copy selected Generation012 best, commit/push/dispatch5000games then end turn. User has explicitly selected latestGen012 and C8; do not reconsider experiment.
