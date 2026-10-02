# Hosted Edax opening-book evaluation handoff

Updated: 2026-10-02. T077, manual workflow only.

## Deliverable

`.github/workflows/edax-book.yml` — a manual (`workflow_dispatch`) workflow that
runs the existing `scripts/evaluate_edax_prefixes.py` on a GitHub-hosted runner
against the retained canonical prefix file, then uploads everything it produced.
The evaluator, the retained inputs and every other workflow are unchanged.

## Inputs

| Input | Type | Default | Meaning |
| --- | --- | --- | --- |
| `depth` | number | 34 | Edax search **level**, not a full-width depth guarantee |
| `cores` | number | 4 | Independent one-thread Edax workers (`-n-tasks 1`) |

No other trigger exists: no push, pull request, schedule or repository event.

## Runner and steps

- `ubuntu-24.04`, `timeout-minutes: 330` (leaves upload margin beyond the
  evaluator's 5-hour cap), `permissions: contents: read`.
- Checkout with `persist-credentials: false`; Python `3.14` via `setup-python`.
- `python -m pip install --no-deps -e .` — engine only; no torch/numpy/sklearn.
- Download the pinned official package into `tools/edax` and verify
  `sha256 = 7ca52cb0ccf591ad9690e7d21861d4a6f04b900c686346db98ea26dd30cd966a`
  (`edax-4.6-linux-x86.tar.gz`). The archive is extracted and the directory
  holding `lEdax-x86-64` is copied in, so a wrapped or flat archive both work.
  Only the baseline executable and `data/eval.dat` are used; no CPU-specific
  variant is selected.
- `data/opening-book/startup-book.dat` (valid 84-byte Edax book) is copied to
  `tools/edax/data/book.dat`, so Edax loads it instead of creating and running a
  new book at startup.
- Evaluation command (unbuffered, streamed to the Actions log through `tee`,
  with `pipefail` so a planned stop or error fails the step):

  ```
  python -u scripts/evaluate_edax_prefixes.py \
    --input data/opening-book/prefixes-canonical.txt \
    --output runs/edax-evaluation/evaluated-prefixes.txt \
    --cores "$CORES" --depth "$DEPTH" \
    --eta-check-after 600 --eta-check-interval 150 \
    --max-estimated-hours 5 --max-hours 5
  ```

- The artifact `edax-book-<run_id>-<run_attempt>` always uploads
  `runs/edax-evaluation/` (complete output if finished, otherwise the partial
  snapshot, raw worker logs, `evaluation.log` and the runtime summary). The job
  summary always shows the requested level/cores, run link and artifact name,
  plus the runtime summary when present.

## Exact commands (user/design launch separately)

```
gh workflow run edax-book.yml --ref master -f depth=34 -f cores=4
gh run list --workflow edax-book.yml --limit 5
gh run watch <run-id>
gh run download <run-id> -n edax-book-<run-id>-<attempt> -D runs/hosted-edax
```

## Status

- Workflow and this handoff only. **No commit, push, dispatch or Edax query**
  was performed; the hosted run is prepared but **unrun**.
- The evaluator and retained inputs were not modified or regenerated.
- Prerequisite verified by inspection: `data/opening-book/prefixes-canonical.txt`
  has 2479 rows with a blank first row, and `startup-book.dat` is 84 bytes. Both
  exist locally. **They are currently untracked in Git** (`git status` shows
  `?? data/opening-book/`), as is `scripts/evaluate_edax_prefixes.py`. All of
  them must be added to the revision that is dispatched, or the checkout will
  not contain the invoker, the input or the startup book.

## Checks actually performed (static only)

- YAML parses with the system PyYAML (`yaml.safe_load`), including the
  `workflow_dispatch` inputs and defaults (`depth=38`, `cores=4`).
- Only `workflow_dispatch` is present as a trigger; `permissions: contents: read`;
  `timeout-minutes: 330`.
- Referenced paths match the existing evaluator and retained assets:
  `scripts/evaluate_edax_prefixes.py`, `data/opening-book/prefixes-canonical.txt`,
  `data/opening-book/startup-book.dat`, and output stem
  `runs/edax-evaluation/evaluated-prefixes` (so the runtime summary read by the
  job summary is `evaluated-prefixes.runtime-summary.txt`).
- Evaluator flags and defaults used by the workflow match the script's current
  interface, and the pinned SHA-256 matches the setup handoff value.
- Shell blocks use `set -euo pipefail` where needed; no tabs.

## Limitations

- The workflow has not been run; runner behaviour and real Edax timings are
  unverified. A non-zero job status on a stop is expected and is not a completed
  result.
- No resume: a stopped run must be dispatched again to a new artifact; the
  evaluator refuses an existing output path on the same runner.
- No strength, size or timing claims. Hosted level-38 execution is unrun.

## Level-34 retry — 2026-10-02

User authorized commit, push and a four-worker level-34 retry after level 38
stopped at the ETA guard (61/2479 rows, latest estimate 11.93 hours). The workflow
default is now 34; retained input and five-hour limits are unchanged. The original
status/checks above describe the initial T077 handoff, not the later hosted run.
