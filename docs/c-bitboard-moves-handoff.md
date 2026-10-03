# C legal-move bitboard handoff

Completed 2026-10-02. `c/bot.c` is now VERSION 004 and exposes the standalone `static inline u64 valid_moves(u64 mine, u64 theirs)` function, with its scalar helper. It uses row-major bit numbering (`row * 8 + column`, a1 top-left). The function is not used by the current neural chooser, so move selection remains unchanged.

The scalar one-stage parallel-prefix helper and four-direction combination are adapted from Richard Delorme's Edax 4.6 `src/board.c`, especially lines 666–686 and 763–783 in the upstream source: [board.c](https://raw.githubusercontent.com/abulmo/edax-reversi/master/src/board.c). The source is distributed under [GNU GPLv3](https://github.com/abulmo/edax-reversi/blob/master/LICENSE); attribution and license links are recorded next to the implementation in `c/bot.c`.

The focused C/Python engine comparison passed for 4,004 masks: both initial-board sides, explicit corner edge/vertical/diagonal rays, a no-move position, and both players across 32 seeded legal trajectories (1,999 positions). See [report.txt](../runs/c-bitboard-moves/report.txt) and [mask-check.txt](../runs/c-bitboard-moves/mask-check.txt). The scratch driver and comparison harness are in ignored `work/c-bitboard-moves/`.

`make bot` passed cleanly. The exact assembled `runs/c-submission/submission.c` compiled cleanly with `gcc -std=c11 -O2 -Wall -Wextra -lm`. The archived source was 83,566 characters; the regenerated submission is 84,767 (+1,201), leaving 15,233 under the 100,000-character limit, or 5,233 after a hypothetical 10,000-character book. Current size details are in `runs/c-submission/size-summary.txt`; the old source is preserved at `runs/c-bitboard-moves/prior-submission.c`.

No game, search, flipper, opening-book logic, model export, or model decoder change was included or run.
