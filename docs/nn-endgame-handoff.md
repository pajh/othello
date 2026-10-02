# NN exact endgame minimax handoff

Updated: 2026-10-02. T078, user-run verification later.

## Deliverable

Configurable exact endgame search added to `src/bots/nn_bot.py`; documented in
this handoff. No other bot, helper, workflow, engine, training or C file was
changed.

## Settings and identity

```
VERSION = '005'
RANDOM_MOVES = 2
TEMPERATURE = 0.05
COUNT_LEFT = 0            # 0 disables; allowed 0..60, bools rejected
ID = 'NN-005-R2-T0.05-C0'
```

A positive `COUNT_LEFT` activates the solver when the current board has at most
that many empty squares. `COUNT_LEFT = 0` (the default) disables it and takes
the previous code path unchanged. The cutoff is part of `get_id()`, so reports
distinguish `-C0` from a later `-C8` or `-C10`. The checkpoint is still chosen
by `OTHELLO_NN_CHECKPOINT` and loaded once per process.

## Behaviour

- Search is exact negamax with alpha-beta: every searched leaf is terminal
  (`rig.engine.is_terminal`); there is no NN leaf, depth/time/node cutoff or
  heuristic fallback. A forced pass switches player on the unchanged board and
  continues; a nonterminal position where only the player to move is stuck
  returns the negated opponent value.
- The value is the win/draw/loss outcome from the root player's perspective,
  `+1` / `0` / `-1`, with no disc-differential term.
- The root searches the supplied legal moves in their existing order and returns
  the **first** move that proves the best value, so proven outcomes are never
  temperature-sampled. A single legal move is returned directly.
- Rules are not duplicated: the solver uses `engine.legal_moves`, `apply_move`,
  `is_terminal` and `winner` only. No transposition table, move ordering or
  shared mutable cache; state is local to the search call.
- The solver is applied in both the module-level `play()` and the factory
  `create_player()` path. In the factory the random opening still takes
  priority: the first `RANDOM_MOVES` own moves are random and only later moves
  use the solver. A position with no legal moves still returns `None`, and the
  opening counter is not consumed by a pass.
- Outside the cutoff, scoring, batching, checkpoint loading and sampling are
  unchanged. `COUNT_LEFT = 0` short-circuits before any search work.

## Checks actually performed (`work/nn-endgame/check_endgame.py`, synthetic only)

No games or matches were run. `py_compile` and these focused checks pass:

- Identity is `NN-005-R2-T0.05-C0`; `get_id()` returns it.
- `COUNT_LEFT` validation rejects `True`, `False`, `1.0`, `-1`, `61` and `'3'`,
  and accepts `0`, `1`, `30`, `60`.
- Activation gates: 60 empties is inactive at `COUNT_LEFT = 0` and `59`, active
  at `60`.
- Terminal sign: black 40-24 win gives `+1` for Black and `-1` for White; a
  32-32 draw gives `0`.
- Forced pass: at a deterministic position where White has no move and Black
  does, `_negamax` matches an independent unpruned terminal-only reference for
  both players.
- Solver correctness: on 40 random small positions (2–4 empties, ≥2 legal
  moves) the chosen move matches an independently written unpruned reference in
  both value and tie ordering, and `_negamax` matches the reference value.
- `COUNT_LEFT = 0` bypass: with the solver replaced by a failure stub, `play()`
  still uses the batched scores and chooses the strictly highest-scoring move,
  proving the solver is not invoked.
- Positive cutoff: with the score path replaced by a failure stub, the cutoff
  makes the solver choose.
- Factory: the first two own moves are random and only the third uses the
  solver, confirming the opening precedes the endgame search.

## Notes for the later verification task

- **RNG-stream caveat:** because the bot ID is part of the derived per-seat RNG
  seeding, changing `COUNT_LEFT` changes the seeds a runner derives. Zero-cutoff
  equivalence must therefore compare with identical per-seat RNG streams, not
  the same CLI seed alone.
- Suggested comparison (separately scoped, not built here): `COUNT_LEFT = 0`
  equivalence, then `COUNT_LEFT = 8` or `10` versus `0`.
- No strength claim is made. A large cutoff makes exact search exponential, so
  keep later verification cutoffs small.

## Limitations

- No verification helper, match, benchmark or training was run in this chunk.
- The solver is single-threaded and has no transposition table by design for
  this first revision.
