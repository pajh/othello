# Opening prefix symmetry reduction handoff

Updated: 2026-10-02. T074, user-run.

## Deliverable

`scripts/canonicalize_opening_prefixes.py` reads an existing comma-separated
coordinate prefix file and writes one canonical representative per symmetry
orbit, preserving first-encounter order. Standard library only; it uses simple
functions and does not touch `rig.engine`, Edax or the prefix generator.

## Interface and semantics

```
python scripts/canonicalize_opening_prefixes.py \
  --input runs/opening-prefixes/prefixes.txt \
  --output runs/opening-prefixes/prefixes-canonical.txt
```

- Input rows are lowercase comma-separated coordinates (`f5,d6,c3`); a blank
  line is the empty history.
- Each **whole** history is transformed by all four colour-preserving maps and
  the lexicographically smallest transformed tuple of row-major square indices
  `0..63` is kept:
  - identity,
  - `(r,c) -> (7-r,7-c)` (180-degree rotation),
  - `(r,c) -> (c,r)` (main-diagonal reflection),
  - `(r,c) -> (7-c,7-r)` (anti-diagonal reflection).
- Duplicate canonical histories are dropped; the first-encounter order is
  preserved. Output is lowercase comma-separated coordinates.
- The literal `pass` is unchanged by every transform.
- `--output` is created and its parent directory is created if missing; an
  existing output path is refused. The input file is never modified.
- Counts by length and the total are printed.

## Checks actually performed

Only the allowed synthetic check was run, into `work/opening-prefix/`; the full
input file was **not** reduced.

- `python scripts/canonicalize_opening_prefixes.py --help` printed usage.
- A synthetic file containing the empty history plus the four legal first moves
  (`d3`, `c4`, `f5`, `e6`) produced exactly **2** canonical rows: the blank
  empty history and one representative (`d3`) for the four symmetrically
  equivalent openings.
- The four transforms were confirmed to map the opening set `{d3, c4, f5, e6}`
  into one orbit of size 4, and every single-move opening canonicalizes to
  `d3`. Canonicalization was idempotent, and `pass`/empty histories were
  unchanged.
- An initial implementation bug (the transform returned a `(row, col)` pair
  that was stored instead of its square index) was caught by this synthetic
  check and corrected before the check passed.

## Known full-input expectation (not executed here)

`runs/opening-prefixes/prefixes.txt` has 9913 rows with length-0..6 counts
`1, 4, 12, 56, 244, 1396, 8200`. The user-run reduction is expected to give
canonical counts `1, 1, 3, 14, 61, 349, 2050`, total **2479**. This is real
per-history transformation of every complete row, not file slicing or periodic
sampling.

## Limitations

- No Edax, policy filtering, book format or future reply-coverage features.
- No timing or full-run result is claimed; the user executes the documented
  command.
