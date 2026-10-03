# T088 focused correctness review

Review result: no actionable correctness defects found in the VERSION 006
terminal-only negamax. Perspective changes, forced passes, terminal WDL,
root proof handling, timeout propagation, and supplied-move publication are
consistent with the task contract.

The recursive move path flips the selected discs, swaps the resulting boards
so the opponent is side to move, and negates the returned score
(`c/bot.c:475-500`). Forced passes swap perspective without placing a disc;
terminality checks both sides before comparing disc counts
(`c/bot.c:451-468`). The root uses the full three-outcome window for every
candidate and only accepts a completed win or draw. Timeout propagates as a
separate flag, and a previously completed draw remains eligible after a later
timeout (`c/bot.c:540-582`). The final output uses the original referee-provided
move string (`c/bot.c:745-758`).

Checks run for this review:

- Rebuilt the focused scratch test; result: PASS. It compared 240 near-terminal
  positions against its exact minimax oracle, including 23 forced-pass nodes,
  checked root selection on 60 positions, terminal win/loss/draw cases, and
  immediate timeout fallback.
- `make bot`: already up to date; the delivered handoff records the clean
  warning-enabled build.
- Regenerated the exact scrunched submission: 91,245 bytes, under the 100,000
  byte limit; compiled it with C11, `-O2 -Wall -Wextra`, and `-lm` successfully.

This was a focused source and scratch-test review. It does not establish a
wall-clock deadline guarantee, prove search results on positions beyond the
tested corpus, or include a full game or strength evaluation.
