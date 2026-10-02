# Collection identity correction handoff

Updated: 2026-10-02. T081. One-constant correction; no jobs, games or artifact
rewrites.

## What changed

In `scripts/nn_selfplay_collect.py`, the `BOT_ID` constant was stale:

```
-BOT_ID = 'NN-004-R2-T0.05'
+BOT_ID = 'NN-006-R2-T0.05-C8'
```

This is the only code change. There is no dynamic identity framework and no
unrelated refactor. Every existing use of `BOT_ID` now carries the corrected
value automatically:

- launch provenance and the derived-seed string (`SEED_DERIVATION` uses
  `{bot_id}`);
- the run-review checks that `metadata.json`'s `bot1_id`/`bot2_id` and the
  provenance `bot_id` equal the expected value;
- the reported `bot IDs:` lines and the recorded `bot_id` field.

## Observed failure this corrects

GitHub Actions run `37030679887` collected all 5,000 C8 self-play games
successfully and normally with zero forfeits in about 503 s. The collector's
review then **rejected the batch** because its hardcoded `BOT_ID` still said
`NN-004`, which did not match what the actual bots reported. Training was
skipped as a result; no candidate was produced by that run.

## Artifact provenance caveat (do not rewrite)

The retained artifacts from that run record the **wrong** identity in the
collector-authored provenance/summary text: they say `NN-004` there. However the
underlying `metadata.json` bot IDs and the actual game execution report
`NN-006-R2-T0.05-C8`. The two disagree only because the collector constant was
stale.

These retained artifacts are **not** being silently rewritten in this task; the
recorded mismatch is documented here instead so a later inspection can explain
it. Anyone reviewing that run should treat the metadata/execution identity
(`NN-006-R2-T0.05-C8`) as what actually played and the stale collector text as
the bug that caused the review rejection.

## Checks actually performed

- `python -m py_compile scripts/nn_selfplay_collect.py` succeeds.
- `python scripts/nn_selfplay_collect.py --help` prints usage.
- Grep confirms `BOT_ID` is defined once and referenced only through the
  corrected constant (lines 24, 154–155, 166, 244–245, 277, 308, 335).
- `git diff` shows exactly the one-line constant change; no other edit.
- No 5,000-game review was rerun, no model was imported, and no game, job,
  commit or push was performed.

## Status

- Collection itself succeeded for run `37030679887`; **no candidate was
  trained**.
- `--review-run` and future collections will now expect `NN-006-R2-T0.05-C8`,
  so a corrected rerun can pass review. Primary/Luna will inspect the retained
  failed artifacts separately.
