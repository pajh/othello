# C search diagnostics handoff

T092 is complete. `c/bot.c` is VERSION 007 and writes one compact stderr line
per turn when `SEARCH_DEBUG` is non-zero. The terminal search, the 16-empty /
140ms / 256-node settings, and all choice/proof/deadline logic are unchanged;
stdout still carries exactly the one move plus newline.

## Instrumentation

- `#define SEARCH_DEBUG 1` in SETTINGS. `0` removes the diagnostic.
- The line is emitted immediately before the existing `printf`/`fflush`, with a
  single `fprintf(stderr, ... "\n")`. No extra stdout and no per-node I/O.
- Per-turn counters are file-static and reset by `reset_search_diag()` at the
  start of every turn (right after the deadline is set), so a turn that never
  invokes the search reports zeros, never the previous turn's state.

Fields: `turn`, `empties`, `search=on/off`, `reason`, `nn`, `played`, `nodes`,
`terminals`, `roots`, `proof`, `timeout`, `elapsed`.

Counter semantics:

- `nodes` — the existing `search_nodes` visited-node counter.
- `terminals` — cheap counter incremented only in the existing double-no-move
  terminal branch; it counts WDL leaves and never network candidate scorings.
- `roots` — root moves whose exact value was accepted before the deadline.
  Includes completed losses, which are counted but can never override the move.
- `proof` — best completed proof among accepted root moves: `win` / `draw` /
  `loss`, or `none` when nothing completed (and always `none` when search is
  off).
- `timeout` — `yes` when the search abandoned work at the deadline (amortised
  check or a root budget break), `no` otherwise. The root budget break now sets
  this flag for the diagnostic only; fallback selection is unchanged.
- `reason` — for skipped turns: `cutoff`, `single_move`, `non8board`, `budget`,
  or `disabled` (only when `SEARCH_MAX_EMPTIES` is compiled as 0); `active`
  when the search ran.
- `elapsed` — one extra final `now_ms()` read minus the existing `turn_start_ms`.

Debug off is compiled out with `#if SEARCH_DEBUG`: no counters, no reason
formatting, no elapsed clock read and no `fprintf`. The per-node addition while
enabled is the single terminal-branch increment; the node clock amortisation is
untouched. Printing adds a modest, unmeasured cost inside the existing 10ms
margin, so the budget was not lowered or changed.

## Commands and checks actually performed

- Preserved the prior current submission (never overwriting an existing
  archive): `runs/c-negamax-debug/prior-submission.c`, 91,238 chars, VERSION 006,
  no `SEARCH_DEBUG`, budget 140.
- `make -B bot CFLAGS='-std=c11 -O3 -Wall -Wextra'` — clean, no warnings
  (`build/c-random-bot`).
- `venv/bin/python scripts/scrunch.py --input c/bot.c --output
  runs/c-submission/submission.c --include-dir runs/c-model-embedded` —
  94,152 characters / bytes, within the 100,000 limit (5,848 headroom), zero
  remaining quoted local includes, `#pragma GCC optimize("O3,inline")` first.
- Exact submission `gcc -std=c11 -O3 -Wall -Wextra -o build/c-submission
  runs/c-submission/submission.c -lm` — clean. `build/c-random-bot` and
  `build/c-submission` give identical output and diagnostic on the fixture.
- Focused single-turn fixtures (no full games, no 100-game rerun), reusing the
  T088 scratch turns in `work/c-negamax/`:

  Pre-cutoff turn (`turn-open.txt`, 60 empties), stdout `c4` (a supplied move):

  ```
  [DBG] turn=0 empties=60 search=off reason=cutoff nn=c4 played=c4 nodes=0 terminals=0 roots=0 proof=none timeout=no elapsed=0ms
  ```

  Near-endgame turn (`turn-input.txt`, 12 empties), stdout `c3`:

  ```
  [DBG] turn=0 empties=12 search=on reason=active nn=c3 played=c3 nodes=37365 terminals=9900 roots=6 proof=loss timeout=no elapsed=4ms
  ```

  Timeout with a retained prior proof (a generated 16-empty turn), stdout `h4`:
  the search stopped at the deadline after completing 8 roots, all losses, and
  kept the network move:

  ```
  [DBG] turn=0 empties=16 search=on reason=active nn=h4 played=h4 nodes=1925888 terminals=457414 roots=8 proof=loss timeout=yes elapsed=140ms
  ```

- Debug-off check: a scratch copy of the exact submission with
  `SEARCH_DEBUG 0` (`work/c-negamax-debug/submission-nodebug.c`) compiled clean
  and produced stdout `c3` with empty stderr on the near-endgame turn.
- stdout was exactly one coordinate line for every fixture (`wc -l` = 1), and
  each played move was one of the supplied legal moves.

## Size / limitations

- Submission grew from 91,238 to 94,152 characters (+2,914).
- Diagnostics go to stderr, which CodinGame captures; they do not affect stdout
  or game choice. No inference is drawn here about league rank movement.
- `reason=disabled` is only reachable when `SEARCH_MAX_EMPTIES` is compiled as
  0. Scratch diagnostics for this task live under `work/c-negamax-debug/` and
  the timeout fixture under `work/c-negamax-debug/timeout-0x5555555555555555.txt`;
  no model, wrapper, project record, commit or push was touched.
