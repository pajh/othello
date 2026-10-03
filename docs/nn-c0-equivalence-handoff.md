# NN COUNT_LEFT=0 equivalence handoff

The user-run helper `scripts/check_nn_c0_equivalence.py` compares current
NN-005 (`COUNT_LEFT = 0`) with the pre-edit NN-004 source read from Git commit
`07ed0ae`. Both modules load the same checkpoint. For each seat, separate old
and new player closures receive the same observations and paired RNG streams;
the helper compares both move and RNG state before applying the single agreed
move. It also compares both stateless greedy `play` functions at every
encountered position. IDs are reported and are not used to derive seeds.

From the project root, run:

```bash
venv/bin/python scripts/check_nn_c0_equivalence.py
```

This defaults to `models/best.pt` and seed `97001`. To select another retained
checkpoint or explicit seed, pass `--checkpoint PATH --seed INTEGER`.

On the helper, `py_compile` and `--help` completed successfully. `--help` exits
before importing either NN module or loading a checkpoint. The equivalence game
has not been run; no game, benchmark, or training job was launched here.

- User-run NN C0 equivalence passed: seed97001/models/best.pt, NN-004-R2-T0.05 versus NN-005-R2-T0.05-C0, 61 plies, 61 stateful and 61 greedy comparisons with matched RNG streams; terminal White41–23. This establishes unchanged choices/RNG on this one game with solver disabled; C8/C10 strength comparisons remain unrun.
