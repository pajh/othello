# C endgame timing comparison results

The saved 100-game run completed normally in 19.000 seconds: seed 99016,
single worker, alternating colours. C-NN-006 won 93 games; NN-006-R2-T0.05-C8
won 7; there were no draws or forfeits. The bots split Black assignments 50/50.

I checked the saved artifacts without rerunning games. All 6,105 timing rows
match the 6,105 recorded actions. Replaying all 100 game records through the
engine reproduced each saved position sequence and final board, so the
recorded moves were legal. The raw timing file and games are retained in
`runs/c-turn-timing/run-3865c60b97ba4d428ca1e55ce41e8a8c/`.

| Decision group | C-NN-006 | Python NN |
| --- | ---: | ---: |
| First actual move, n=100 each (mean; max; >2,000 ms) | 5.549 ms; 9.261 ms; 0 | 0.008 ms; 0.033 ms; 0 |
| Later actual moves (n; mean; p95; max; >150 ms) | 2,944; 1.626 ms; 1.499 ms; 140.084 ms; 0 | 2,855; 3.774 ms; 6.651 ms; 206.028 ms; 1 |
| Later moves at ≤16 empties with >1 legal move (n; mean; p95; max; >150 ms) | 783; 4.071 ms; 16.200 ms; 140.084 ms; 0 | 556; 7.360 ms; 40.098 ms; 206.028 ms; 1 |

Across all actual moves, including each bot's first actual move, measured
call time summed to **5.341 seconds for C** and **10.775 seconds for Python**.
Forced passes were timed in the raw log but excluded from those totals: C had
5 passes taking 0.0054 ms in total; Python had 101 taking 0.0854 ms.

The slowest C decision was game 60, Black, ply 44: 16 empties, 6 legal moves,
not the first move, 140.084 ms. The slowest Python decision was game 37, Black,
ply 52: 8 empties, 5 legal moves, not the first move, 206.028 ms. This was the
only Python later actual move above 150 ms. No first actual move exceeded the
2,000 ms opening allowance.

The C wrapper measurement includes Python serialization, pipe exchange, child
startup on its first actual move, and response validation; Python measures only
its callable. It is conservative for local wrapper-inclusive latency, but it
does not isolate negamax runtime. C plays greedily from the first move and uses
the embedded quantized Generation 016 model with a 16-empty, 140 ms terminal
search. Python uses the full-precision checkpoint, two random own opening
moves, temperature 0.05, and an 8-empty solver cutoff. The outcome difference
therefore does not measure negamax's isolated playing-strength gain. Local
timings also do not guarantee behavior on CodinGame hardware or under its exact
runtime limits.

Saved summary: `runs/c-turn-timing/timing-summary.txt`. No further games or
benchmarks were run for this review.
