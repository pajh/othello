# C timed terminal-only negamax handoff

T088 is complete. `c/bot.c` is VERSION 006 and adds a timed terminal-only endgame
negamax on top of the existing greedy embedded-network chooser. The network
choice is still computed first and remains the fallback; nothing about the model,
the input protocol, pass handling or the supplied action strings changed.

## SETTINGS added

- `SEARCH_MAX_EMPTIES 16` — search runs only when the number of empty squares is
  at most this. Set it to `0` to disable search for focused comparisons.
- `SEARCH_BUDGET_MS 140` — whole-turn budget in milliseconds, measured from the
  turn's first board row and shared by network scoring and search. It stays 10ms
  below the platform's 150ms turn limit for the final output.
- `SEARCH_CLOCK_INTERVAL 256u` — visited search nodes between monotonic clock
  reads.

Clock is POSIX `clock_gettime(CLOCK_MONOTONIC)`; `_POSIX_C_SOURCE 200809L` is
defined before the standard headers (guarded, so an existing definition is kept).

## Behaviour

- Timed turn: `turn_start_ms` is taken immediately after the first board row is
  read, so the wait for input is not charged to the budget; `deadline_ms =
  turn_start_ms + 140`.
- The greedy network choice is computed first, exactly as before, and is kept as
  `best`.
- If `board_size == 8`, there is more than one supplied move, the clock is
  still inside budget, and empties ≤ 16, the search runs. Otherwise the network
  move is played unchanged (turn one included: 60 empties, so no search).
- Root order is the network move first, then every remaining supplied move in
  its original order.
- Terminal-only negamax with alpha/beta: leaf values are the final disc-count
  result from the side to move, +1 win / 0 draw / -1 loss. No heuristic, no
  depth limit, no transposition table and no search move ordering.
- Forced passes swap the boards without filling a square; when neither side can
  move the disc count decides even if empty squares remain.
- Proof versus bounds: the root searches every move across the full `(-1, +1)`
  window, which spans the whole three-value domain, so a completed value is
  exact. A completed `+1` is a proven win and is returned at once; a completed
  `0` is a proven nonloss and is retained while later moves are tried for a win;
  a completed `-1` is never selected. Inside the tree, alpha/beta only bound and
  prune — they are never interpreted as a root proof.
- Timeout is a separate status (`search_timed_out`), never a score. A subtree
  that hits the deadline is abandoned; its move and all later moves are left
  unproven, and any proof already completed is kept. A value finished after the
  deadline is not published either. If no move proves a win or draw, the
  network move stands — including when every completed alternative is a proven
  loss.
- Time is amortised: a cheap node counter trips one clock read every 256 visited
  nodes, so a single large subtree cannot consume the budget unnoticed. The root
  also checks the clock before each candidate and before publishing a result.
  The overshoot between two checks is bounded by at most 255 nodes plus one
  node's work (each node is a `valid_moves` plus, per move, a `flip_discs`); no
  wall-clock guarantee is claimed.

## Checks actually performed

- `make bot` (gcc `-std=c11 -O2 -Wall -Wextra`, `-lm`): clean, no warnings.
- `scripts/scrunch.py --input c/bot.c --output runs/c-submission/submission.c
  --include-dir runs/c-model-embedded`: exact assembled submission is
  **91,245 characters / bytes**, within the 100,000 limit (8,755 headroom),
  zero remaining quoted local includes, `#pragma GCC optimize("O3,inline")`
  first line. It compiles clean with `gcc -std=c11 -O2 -Wall -Wextra ... -lm`.
- Focused scratch test `work/c-negamax/test_search.c` (includes `bot.c` with
  `main` renamed), all PASS:
  - absolute terminal outcomes on full boards: 40–24 win, 24–40 loss, 32–32 draw;
  - 240 real near-terminal positions (≤6 empties) reached by random legal play,
    negamax value versus a plain untimed exact minimax oracle — all equal, with
    23 forced-pass nodes exercised;
  - root contract on 60 positions: the returned move equals the first move in
    order proving a win, else the first proving a draw, else "keep network";
  - immediate timeout (deadline in the past) returns "keep network" and does not
    emit a timeout-derived proof.
- End-to-end: a generated 12-empty turn fed to both `build/c-random-bot` and the
  exact `build/c-submission` produced one of the supplied moves (`c3`), exit 0,
  empty stderr.
- Timing observation (desktop, not a benchmark): a 14–16 empty turn takes about
  0.15 s of whole-process wall time, i.e. the search runs to and stops at its
  budget and falls back to the network move on that position; a no-search turn
  is a few milliseconds.

## Size / limitations

- The submission grew from 85,648 to 91,245 characters (+5,597). The previous
  file is preserved at `runs/c-negamax/prior-submission.c`.
- Headroom is now 8,755 characters. A hypothetical 10,000-character opening
  book no longer fits as-is (it would be 1,245 over); the previously estimated
  ~5,282 characters of unapplied whitespace cleanup would more than cover that,
  but no cleanup is applied here.
- Search is final-phase only (≤16 empties) and never runs on the first move; a
  single legal move returns immediately. No search at >16 empties, so most
  mid-game strength is unchanged.
- Numerical behaviour of the network path is untouched; the search consumes the
  same bitboard primitives already verified against `src/rig/engine.py`
  (`valid_moves`, `flip_discs`).
- During development the first draft forgot to swap the side-to-move perspective
  in the negamax recursion; the scratch oracle comparison caught it and it was
  fixed before any check passed. No actual full game, league match, benchmark or
  numerical parity rerun was performed here.
