# Retained baseline model

`first-model.pt` is a copy of the selected epoch-1 best checkpoint from
`checkpoints/first-model/run-2103bc51994e46a099f8b3d78618efd3/best.pt`.
The user requested this copy in the repository on 2026-10-01 for GitHub-hosted collection.
The original checkpoint remains untouched.

It uses the outcome MLP/encoding documented in `docs/first-model-design.md`.
Select this file explicitly with `OTHELLO_NN_CHECKPOINT`; bot settings are unchanged.
Keep this baseline separate from future candidate models.

`best.pt` is the selected hosted self-play parent: a copy of
`runs/github-symmetry/checkpoints/github-candidate/best.pt`, the best epoch-2
checkpoint from GitHub run 36887079634. Selected 2026-10-01 after its
1,000-game parent evaluation: 633 wins, 37 draws, 330 losses (65.15% score).
The next hosted round preserves this parent alongside its new candidate.
