# Identity carry-through handoff

Updated: 2026-10-02. T082. Synthetic checks only; no games, jobs, commit or
push.

## Why

T081 fixed a stale hardcoded `BOT_ID` in the collector, but the duplicate name
still existed as a constant that could drift again. This change removes the
duplicated identity so the canonical bot is the single source, and makes review
and reporting read identities from the retained records instead of current code.

The T081 handoff and its retained failed artifacts are untouched. The active
hosted retry `37032114143` (fixed `NN-006-R2-T0.05-C8`) was not interrupted or
altered.

## Changes — `scripts/nn_selfplay_collect.py`

- Removed the `BOT_ID` constant. The collection identity now comes from
  `bots.nn_bot.get_id()` via a new small helper `launch_bot_id(checkpoint)` that
  sets `OTHELLO_NN_CHECKPOINT` first and imports the module only on the
  collection path. `--help` never imports the model.
- `collect()` resolves `bot_id = launch_bot_id(checkpoint)` once, uses it for the
  saved launch provenance, and prints it. The runner launches the same module,
  so recorded IDs match launch provenance by construction.
- `review_run()` no longer compares against a fixed expected ID. It takes
  `bot1_id`/`bot2_id` from the run's `metadata.json`, requires them to be equal
  (this self-play helper plays one bot against itself) and requires the CLI
  `run-summary.txt` to contain `bot 1 ID: <bot1_id>` / `bot2 ID: <bot2_id>` and
  what it did before. Reports print the retained IDs.
- A saved launch provenance whose `bot_id` disagrees with the retained run ID
  still fails clearly; old failed runs are not silently rewritten.
- Engine-derived per-game seeds are unchanged: the runner derives them from
  `bot1_id`/`bot2_id` from the same module, which the metadata check confirms.

## Changes — `.github/workflows/selfplay.yml`

- The evaluation summary no longer asserts a fixed code ID or settings string.
  It parses `bot 1 ID:` / `bot 2 ID:` from `runs/github-evaluation/run-summary.txt`
  with the existing simple regex style (`def bot_id(text, seat)`) and reports
  them as `bot IDs (from run-summary.txt): bot 1=…; bot 2=…`, falling back to
  `unknown` when absent. No model is imported.
- Checkpoint paths remain prominent, with the note that equal code IDs do not
  imply equal weights.
- The candidate-module comment text that mentioned `R2/T0.05/C8` was left as a
  descriptive comment only (no identity constant was added there).

## Checks actually performed (`work/nn-identity-flow/check_identity.py`)

No model was loaded, no game was played, and no 5,000-game review was rerun.

- Importing the collector for tests does **not** put `bots.nn_bot` in
  `sys.modules`, and the module no longer defines `BOT_ID`.
- An arbitrary future ID `NN-099-XY-R3-T0.07-C11` placed in synthetic
  metadata/`run-summary.txt` flows into `match-check.txt` and
  `diversity-summary.txt` (twice each), proving review is not tied to a fixed
  expected ID; `NN-006` does not appear.
- Historical review independence: the arbitrary ID is absent from the current
  `src/bots/nn_bot.py`, and the review still reports it.
- Saved provenance `NN-004-R2-T0.05` against a run whose retained ID differs is
  rejected with a clear disagreement message; matching provenance is accepted.
- Split `bot1_id != bot2_id` is rejected for this self-play helper.
- Workflow summary parsing on synthetic summaries: normal (both
  `NN-006-R2-T0.05-C8`), split (`NN-007-A` / `NN-008-B`) and absent
  (`unknown` / `unknown`).
- `selfplay.yml` still parses and the changed summary block passes `bash -n`;
  `py_compile` passes on the collector; `--help` runs without a checkpoint.
- Grep confirms no `NN-006-R2-T0.05-C8` / `NN R2/T0.05/C8` / `NN-004` hardcoded
  identity remains in the workflow.

## Limitations

- The synthetic checks use tiny fake runs, not a real 5,000-game batch.
- Historical (`--review-run`) records that predate these fields are unaffected:
  review still requires the recorded metadata and summary IDs to agree.
- No commit or push was made; Primary handles that.
