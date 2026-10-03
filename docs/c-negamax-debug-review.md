# T092 focused debug review

The VERSION 007 diagnostic accounting and search behavior look correct. The
per-turn reset clears nodes, timeout, terminal leaves, completed roots, and
proof state before candidate scoring. Terminal counts increment only at the
double-no-move WDL leaf; roots increment only after a completed search is
accepted before the deadline. The proof label tracks the strongest accepted
root value, including a win when the neural move itself is proven winning.
Timeout aborts remain separate from proof values, while any earlier completed
proof is retained. The 16-empty, 140 ms, and 256-node settings are unchanged.

`SEARCH_DEBUG` guards the diagnostic counters, reason/proof labels, elapsed
clock read, and stderr formatting. The retained `SEARCH_DEBUG 0` scratch build
and fixture output are consistent with that path producing no diagnostic
stderr. With debug enabled, the single diagnostic `fprintf` is immediately
before the existing stdout move and flush. The current assembled submission is
94,152 bytes, and its version and search settings match `c/bot.c`.

One actionable source-comment mismatch remains: `c/bot.c:42-43` still says
stderr contains errors only and that there is no per-move logging. With
`SEARCH_DEBUG` set to 1, the new diagnostic line is intentionally written for
each emitted move. Updating that stale comment would keep the file header
accurate. I found no search-choice, proof, or deadline behavior defect in this
review.

Checks reviewed: the handoff's three focused fixtures (cutoff, completed
endgame, and timeout fallback), the debug-off fixture, exact stdout-line and
legal-action checks, and current source/submission settings and size. No games,
matches, or benchmarks were run for this review.
