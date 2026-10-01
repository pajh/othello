# NN self-play collection helper handoff

T040 helper is ready for the user to launch. It defaults to 5,000 sequential `NN-004-R2-T0.05` versus `NN-004-R2-T0.05` games, master seed `90001`, output `runs/selfplay-5000`, and the selected checkpoint `checkpoints/first-model/run-2103bc51994e46a099f8b3d78618efd3/best.pt`.

From the repository root, launch with:

```sh
venv/bin/python scripts/nn_selfplay_collect.py
```

The helper writes checkpoint, bot, seed, and count provenance atomically before launching the CLI, then copies that record into the new run directory as soon as it appears. The CLI retains completed game records and its ordinary `run-summary.txt`; the helper checks metadata and summary against streamed game records, including IDs, seed derivations, alternating seats, normal/forfeit counts, and outcomes. It writes latest `match-check.txt` and `diversity-summary.txt` under `runs/selfplay-5000/`.

Diversity is descriptive: exact action-trace duplicates; unique and largest-group counts for 4/8/12-action prefixes; and exact absolute-colour `(board, to_play)` overlap across games after the first 12 actions. No threshold or independence claim is made. The raw games are read one record at a time; only trace/prefix counters and distinct late-position keys are retained.

If a complete collection finishes but report analysis fails, rerun the reviewer against the retained run without recollecting:

```sh
venv/bin/python scripts/nn_selfplay_collect.py --review-run runs/selfplay-5000/run-<actual-run-id>
```

After a successful review, the reviewer removes the pending provenance marker. If a run is interrupted, the checkpoint selection remains in that run's `collection-provenance.json` and the pending copy remains in the output directory; `--review-run` expects a complete batch and completed CLI summary. Do not delete either before recovery.

`python -m py_compile`, `--help`, `git diff --check`, and source inspection passed. No games were run, and no checkpoint was loaded or inspected. Conversion, training, and larger follow-on work remain unrun and user-supervised.
