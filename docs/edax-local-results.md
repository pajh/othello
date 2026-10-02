# Local Edax prefix evaluation

Updated: 2026-10-02. User-run, 4 workers at Edax level 10; reported elapsed time 30.0 seconds.

- Input: `runs/opening-prefixes/prefixes-canonical.txt` (2,479 rows).
- Output: `runs/edax-evaluation/evaluated-prefixes.txt` (2,479 rows).
- Metadata: `runs/edax-evaluation/evaluated-prefixes.results.jsonl` (2,479 rows); raw logs: `runs/edax-evaluation/evaluated-prefixes.worker0.log` through `...worker3.log`.
- Read-only consistency checks: output histories match all input rows exactly and in order; output moves match metadata; metadata indices are 0–2478. Every record reports depth 10 and selectivity 100. Worker distribution is 620/620/620/619.
- Compared the first and last result for each worker against its raw log: depth, score, node count, and recommended move matched in all eight sampled rows.

This confirms the recorded evaluation output is internally consistent for the checks above. It does not establish playing strength; no strength comparison was made here.
