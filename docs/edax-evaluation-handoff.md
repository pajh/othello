# Edax prefix evaluation handoff

Updated: 2026-10-02. T075 / T075a / T076, user-run.

## Deliverable

`scripts/evaluate_edax_prefixes.py` reads an existing prefix file and asks Edax
for the recommended reply at every history, writing one result line per input
row. Standard library only. It uses `rig.engine` for replay/legality and does
not enumerate, canonicalize or filter anything.

## Exact user command

```
venv/bin/python scripts/evaluate_edax_prefixes.py \
  --input runs/opening-prefixes/prefixes-canonical.txt \
  --output runs/edax-evaluation/evaluated-prefixes.txt \
  --cores 4 --depth 10
```

`--depth` is the Edax search **level**, not a full-width depth guarantee;
`--cores` defaults to 4 and `--depth` to 10. The local level-10 target of
roughly 20–40 seconds is a target, not a guarantee. Hosted level-38 execution
is a separate later task, still unprepared and unrun.

Additional flags (defaults in brackets), all validated to be positive:

- `--eta-check-after` [600] — seconds before the first runtime check.
- `--eta-check-interval` [150] — seconds between later checks.
- `--max-estimated-hours` [5] — stop after 3 consecutive checks estimate above
  this.
- `--max-hours` [5] — hard elapsed limit in hours.

Running the local test twice at different `--depth` values requires a **new
`--output` path**; the existing output is refused and levels are never mixed.

## Interface and behaviour

- Input rows are lowercase comma-separated coordinates; a blank line is the
  empty history. The blank line is preserved as an empty history.
- Output lines are exactly `<original history>=<recommended move>`; the empty
  history becomes `=d3` (for example). The original input order and original
  text are retained.
- `--output` is refused if it already exists; its parent directory is created.
  The input file is never modified.
- Rows are split into `--cores` contiguous near-equal chunks preserving the
  existing DFS order. Each chunk is handled by one persistent Edax process
  started with `-n-tasks 1`; processes are launched once and stopped once.
- The per-query position is reached with `undo` (one per excess action) plus a
  single `play` of the new suffix. `new`/`init`/`setboard` are never used, so
  cached hash tables are not cleared between queries.
- The result is taken from the final search row: the first PV coordinate is the
  recommended move, and the depth, selectivity, score (from the player to
  move), engine time and nodes are recorded. Human Edax output is preserved in
  the raw worker log.
- Prompt synchronisation is immediate: the command prompt is recognised as a
  bare `>` at the very end of the received output (after the preceding line's
  newline, or as the first output). A score bound `>` is preceded by a space and
  followed by digits, so it is never mistaken for completion. There is **no**
  quiet/settle wait after a prompt.
- The chosen move is replayed through `rig.engine` and rejected if illegal for
  the player to move.
- Failures (missing assets, protocol/prompt error, book creation, no result,
  illegal reply) abort visibly; a partial output is never published.

### Side files (fixed names derived from the output stem)

For the command above (`stem = evaluated-prefixes`):

- `runs/edax-evaluation/evaluated-prefixes.worker0.log` … `.worker3.log` — raw
  Edax stdout+stderr per worker.
- `runs/edax-evaluation/evaluated-prefixes.results.jsonl` — one JSON object per
  input row: `index`, `history`, `move`, `depth`, `selectivity`, `score`,
  `nodes`, `time`, `seconds`, `worker`.
- `runs/edax-evaluation/evaluated-prefixes.partial.results.jsonl` — snapshot of
  the **completed** records only, in original index order, refreshed about
  every 5 seconds and before any stop. It may remain after a normal completion.
- `runs/edax-evaluation/evaluated-prefixes.runtime-summary.txt` — final status:
  requested level/cores, total/completed, elapsed seconds, reason
  (`COMPLETE` / `STOPPED_ESTIMATE` / `STOPPED_TIME` / `FAILED`), last estimate
  in hours and per-worker `completed/assigned`.
- `runs/edax-evaluation/evaluated-prefixes.txt.part` — temporary stitch file,
  renamed to the final output only on full success.

## Runtime feedback, stopping rule and partial results

- The coordinator tracks completed counts and elapsed time per worker under a
  lock and reports at `--eta-check-after`, then every `--eta-check-interval`
  seconds (default 600, 750, 900, …), independently of whether results arrived
  recently.
- At each check the provisional total estimate is
  `elapsed + max over workers of (worker_remaining / worker_rate)`. Finished
  workers contribute zero remaining; an active worker with no completions
  makes the estimate unknown, is reported as unknown, and never triggers a
  stop. Estimates are provisional, based on completed queries, not guarantees.
- If the estimate exceeds `--max-estimated-hours` on 3 consecutive checks
  (resetting whenever the estimate is below the limit or unknown), the run stops
  with `STOPPED_ESTIMATE` (by default within ~15 minutes). The hard
  `--max-hours` limit stops the run regardless, with `STOPPED_TIME`.
- On a planned stop the coordinator sets cancellation; each worker's prompt
  reader polls stop every 0.5 s while keeping the existing 900 s no-byte timeout
  via a monotonic deadline, so routine polling never delays normal output. In-
  flight queries are cancelled, processes are quit/terminated and reaped
  without the 900 s timeout or multiple 30 s waits, and completed records are
  retained.
- The complete `<output>` and `<stem>.results.jsonl` are published **only** when
  every row is complete. A stopped run leaves the partial snapshot, the runtime
  summary and the worker logs, and returns a non-zero exit status. Unexpected
  errors also retain the completed snapshot with an honest `FAILED` reason.
- The analysis level is never changed automatically.

## Edax invocation

```
<bin> -eval-file tools/edax/data/eval.dat -book-file tools/edax/data/book.dat \
      -book-usage off -level <N> -n-tasks 1 -mode 3 -ponder off \
      -auto-store off -verbose 0
```

`stdbuf -oL` is prefixed when available; otherwise Edax's own flushes at the
prompt and result line make a pipe reader work. The existing 84-byte
`tools/edax/data/book.dat` must be present and load validly; if Edax reports
`New book` at startup, the run fails before any parallel query rather than
repairing or regenerating it.

**Deviation from the task text:** the task listed `-mode0`, but Edax's mode
table is `{"human/edax","edax/human","edax/edax","human/human"}`, so mode 0
makes Edax auto-play White and would corrupt the board between queries. Mode 3
(`human/human`, no automatic play) is used instead. `-verbose 0` is added so
`hint 1` emits a single clean result line.

## Checks actually performed

No Edax query and no full-file analysis was run. Only syntax/`--help` and a
synthetic check with stubbed results (`work/edax-evaluation/check_evaluator.py`)
were performed:

- `py_compile` and `--help` succeed.
- LCP: empty/equal/divergent prefixes behave as expected.
- Chunking: 2479 rows over 4 cores gives contiguous sizes `[620, 620, 620,
  619]`; empty chunks are dropped when cores exceed rows.
- `parse_result` on a typical verbose-0 line yields depth/selectivity/score/
  time/nodes and the first PV move, including the `38@73%` form.
- Ordering/stitch: a stub 3-row result set produces
  `=d3\nd3=c3\nd3,c3=f5\n` and metadata indices `0,1,2` in input order.
- The built command contains the expected flags and `-mode 3`.
- A `pass` token is rejected with a clear unsupported-input error.
- An initial bug (the stitch helpers read the actions list instead of the
  history text) was caught by this check and corrected.

### T075a prompt-delay correction and check

The first version waited `0.25` seconds of silence after a `>` before treating
it as a prompt, which alone would have cost roughly `2479 / 4 * 0.25 ≈ 155`
seconds and defeated the 20–40 second target. `_QUIET` and that select-wait are
removed; a completed prompt is returned immediately.

Added synthetic stub byte-reader checks (no Edax execution):

- Prompt predicate: `b">"` and `b"...\n>"` are prompts; a bare bound char
  (`b"  6  >+02"`) and book text (`b"...done>"`) are not.
- A result line and the prompt delivered as separate pipe chunks returns in
  ~0.05 s, and a bound `>` split from its digits returns in ~0.10 s — both well
  under the removed 0.25 s wait — and the final result still parses to `d3`.

### T076 runtime/stopping/partial checks

All synthetic (simulated progress/time and stub byte readers; no Edax run and no
10-minute wait):

- Runtime policy with slowing progress breaches 3 consecutive checks
  (estimates ~16.7 h, ~17.4 h, ~17.9 h against a 5 h limit) and stops with
  `STOPPED_ESTIMATE`.
- A fast check below the limit resets the streak to 0; a later slow check
  restarts it at 1.
- An active worker with 0 completions yields an unknown estimate, resets the
  streak and never breaches.
- A finished worker contributes 0 remaining seconds.
- `hard_limit_reached` is true at exactly `max-hours` and false one second
  before.
- No automatic depth change: the Edax command keeps `-level 10` (no `-depth`),
  and the runtime summary reports the requested `level: 10`.
- Partial snapshot keeps original index/order and all metadata keys with holes;
  the complete output text is unchanged when all rows are present.
- Stub cancellation: with no Edax output at all, a stop set after 0.3 s ends the
  prompt read in ~0.5 s with a `cancelled` error rather than the 900 s timeout.
- CLI validation rejects non-positive `--eta-check-after`, `--eta-check-interval`,
  `--max-estimated-hours` and `--max-hours`.

## Limitations

- `pass` handling is not implemented; such input fails visibly rather than
  guessing Edax syntax. The canonical depth-6 file contains no passes.
- No resume/retry/culling framework: a stopped or failed run leaves its partial
  snapshot and must be rerun to a new output path, at the same level.
- No timing, size or strength claims; the user runs the actual local test. Hosted
  level-38 execution remains unprepared and unrun.
