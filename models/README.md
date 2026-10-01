# Retained baseline model

`first-model.pt` is a copy of the selected epoch-1 best checkpoint from
`checkpoints/first-model/run-2103bc51994e46a099f8b3d78618efd3/best.pt`.
The user requested this copy in the repository on 2026-10-01 for GitHub-hosted collection.
The original checkpoint remains untouched.

It uses the outcome MLP/encoding documented in `docs/first-model-design.md`.
Select this file explicitly with `OTHELLO_NN_CHECKPOINT`; bot settings are unchanged.
Keep this baseline separate from future candidate models.

`best.pt` is the selected hosted self-play parent: a copy of
`runs/github-symmetry-second/checkpoints/github-candidate/best.pt`, the best
epoch-1 checkpoint from GitHub run 36891605722. Selected 2026-10-01 after
577 wins, 26 draws and 397 losses against its parent in 1,000 games (59% score).
The next round retains this parent separately from its new candidate.
