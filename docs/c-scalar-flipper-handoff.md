# C scalar bitboard flipper handoff

T086 is complete. `c/bot.c` is VERSION 005 and now exposes `static inline u64 flip_discs(u64 mine, u64 theirs, int square)`. Given a legal empty square in the 0–63 row-major bit mapping (0 is top-left), it returns only captured opponent bits. The table-free scalar ray scan does not mutate its inputs. The current neural chooser is unchanged and does not use the primitive. No upstream source was borrowed.

The focused comparison passed 31,172 mask and board-update checks against `src/rig/engine.py`, covering 32 seeded legal trajectories and targeted corner, edge, diagonal, six-disc ray, and multi-direction cases. See [report](../runs/c-scalar-flipper/report.txt); the verifier and C driver are in ignored `work/c-scalar-flipper/`.

`make bot` and a clean GCC build of the exact assembled source passed. The regenerated submission is 85,648 characters, up 881 from the preserved 84,767-character source at `runs/c-scalar-flipper/prior-submission.c`. Headroom is 14,352 characters, or 4,352 after a hypothetical 10,000-character book. No game, benchmark, search, model change, or chooser change was performed.
