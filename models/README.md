# Retained baseline model

`first-model.pt` is a copy of the selected epoch-1 best checkpoint from
`checkpoints/first-model/run-2103bc51994e46a099f8b3d78618efd3/best.pt`.
The user requested this copy in the repository on 2026-10-01 for GitHub-hosted collection.
The original checkpoint remains untouched.

It uses the outcome MLP/encoding documented in `docs/first-model-design.md`.
Select this file explicitly with `OTHELLO_NN_CHECKPOINT`; bot settings are unchanged.
Keep this baseline separate from future candidate models.

`best.pt` is the current selected model for hosted self-play: a copy of
`runs/github-first/checkpoints/github-candidate/best.pt`, the epoch-1 candidate
from successful GitHub run 36841281392. Selected for the next hosted round on
2026-10-01 after local evaluation: 54 wins / 4 draws / 42 losses against its
parent and greedy 100 wins / 0 draws / 0 losses against random.
The next workflow retains this exact parent separately from its new candidate.
