# Opening prefix enumeration handoff

Updated: 2026-10-02. T073b, user-run.

## Deliverable

`scripts/generate_opening_prefixes.py` enumerates every legal move history from
the initial Othello board and writes it to a plaintext file. It uses only
`rig.engine.initial_board`, `legal_moves` and `apply_move`; no rules are
duplicated. There are no Edax calls, scores, symmetries, pruning, extension or
concurrency.

## Interface and semantics

```
python scripts/generate_opening_prefixes.py --depth 6 --output runs/opening-prefixes/prefixes.txt
```

- `--depth N` is the maximum number of recorded turn actions, **inclusive**:
  histories of length `0, 1, ..., N` are all written.
- `--output PATH` is created, and its parent directory is created if missing.
  An existing output path is refused, so raw data is never silently
  overwritten.
- Enumeration is depth-first in ascending `rig.engine.legal_moves` order.
- Every prefix is written exactly once, including the shorter ones.
- Row format: comma-separated lowercase coordinates (`f5,d6,c3`), one history
  per line, no boards/scores/metadata. The empty initial history is one blank
  line.
- A forced pass is written as the literal `pass`, the player switches, and the
  turn is counted. Terminal boards are not extended. No pass is expected in
  these small opening depths.
- On completion the script prints the row count per length and the total, and
  nothing larger.

Successful runs produce an exit code of 0. `--depth` must be a nonnegative
integer; anything else exits with a message.

## Checks actually performed

Only the allowed tiny check was run, into `work/opening-prefix/` (scratch); the
requested depth-6 run was **not** executed.

- `python scripts/generate_opening_prefixes.py --help` printed usage.
- `--depth 2` produced 17 rows: length 0 = 1 (blank line), length 1 = 4
  (`d3`, `c4`, `f5`, `e6`), length 2 = 12.
- Each row replayed legally through `rig.engine`: coordinates are lowercase,
  comma-separated, and the recorded histories match the enumeration order.
- Output refusal on an existing path and the nonnegative-integer guard were
  exercised.

## Relation to the later book reply stage

For the planned reply-coverage stage, histories of length `< 6` are the broad
prefixes whose opponent replies will be expanded through move 6; length-6
histories written here are endpoints reserved for later extension. This script
deliberately implements none of that.

## Limitations

- No Edax querying, move selection, book format or C integration.
- One full run of the requested depth is left to the user; no timing or size
  estimate is claimed.
