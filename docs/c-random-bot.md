# Random C bot

`c/bot.c` is a self-contained C11 program that plays CodinGame's multiplayer
Othello in **ordinary mode** by picking the supplied legal move with the highest
random score. It is version 001 of the C proof of concept: no flips, no neural
network, no legal-move generator. The full intended plan, including the later
export/forward-pass/combine stages, is in [c-bot-plan.md](c-bot-plan.md).

## Build

```sh
make bot
```

That produces `build/c-random-bot`. `CC`, `CFLAGS` and `LDFLAGS` are honoured as
ordinary make conventions, so `make bot CC=clang CFLAGS='-std=c11 -O3 -Wall'`
works. The default is `-std=c11 -O2 -Wall -Wextra`. Only a C11 compiler and the
C standard library are required: no threads, no allocation, no platform headers,
and no second source file. `c/bot.c` as written is what gets submitted to
CodinGame; there is no combine step yet.

## Protocol

Ordinary mode only, no EXPERT input. On startup the program reads, once:

| field | meaning |
| --- | --- |
| player ID | `0` Black, `1` White |
| board size | `8` |

Then, per turn:

| field | meaning |
| --- | --- |
| 8 row strings | top row first; `.` empty, `0` Black, `1` White |
| action count | number of legal moves |
| that many coordinate strings | e.g. `d3` |

It writes **one** coordinate plus a newline to stdout and flushes. Nothing else
ever goes to stdout. Diagnostics go to stderr. EOF on stdin ends the program
normally. A forced pass is the platform's business: the local wrapper never asks
the child to move when it has no legal move, and if an action count of 0 arrives
anyway the program notes it on stderr and waits for the next board instead of
inventing a move.

The RNG is seeded once: from `argv[1]` when a seed is supplied, which makes a
local wrapper run reproducible, otherwise from the clock as CodinGame does. The
random sequence is not expected to match the Python bots' traces.

## Coordinate mapping — confirmed from referee

`a1` is the top-left square; `square = row * 8 + column`.
The official [Cell.java](https://github.com/MultiStruct/Othello/blob/master/src/main/java/com/codingame/game/othello/Cell.java)
serializes coordinates as column letter `a + x` and row number `y + 1`.
[Referee.java](https://github.com/MultiStruct/Othello/blob/master/src/main/java/com/codingame/game/Referee.java)
sends board rows in increasing `y`, columns in increasing `x`. Primary checked
these sources after Bunny's handoff; its earlier unconfirmed-mapping note is
superseded. No code change was needed. Actual CG execution remains unrun.

Timings from the statement: 2,000 ms on the first turn, 150 ms afterwards.

## Playing it through the rig

`src/bots/c_random_bot.py` is a thin adapter with the normal bot interface
(`get_id()`, `play()`, `create_player()`; ID `C-RAND-001`). It starts one child
process per seat per game on that seat's first actual move, sends the one-time
header, then writes a fresh board and legal-move list each call and reads back
one coordinate. It closes and reaps the child when the seat player is released,
which the runner does at the end of every game. There is no build or subprocess
work at import time; if the executable is missing, the error says to run
`make bot`.

## Commands

One smoke game (this has been run once; see the handoff in `work/`):

```sh
venv/bin/python -m rig.cli --bot1 bots.c_random_bot --bot2 bots.random_bot \
  --games 1 --seed 94001 --output-dir work/c-random-smoke
```

The 100-game comparison the user runs, alternating colours by default:

```sh
venv/bin/python -m rig.cli --bot1 bots.c_random_bot --bot2 bots.random_bot \
  --games 100 --seed 94001 --workers 1 --output-dir runs/c-random-vs-random
```

Both bots choose uniformly at random, so the result should be roughly balanced
but 100 games need not split 50/50. Treat any split as noise rather than a
measurement of either bot.
