# Four-worker collection and GitHub Actions

Prepared 2026-10-01 at the user's request while the first 5,000-game collection runs locally. This is a design spec, not implemented code or permission to launch another experiment. Keep the active collection untouched. No additional verification infrastructure, retry system, resume support or exhaustive tests.

## Goal and scope

Run independent games on four CPU workers, then run the same collector on GitHub-hosted hardware so the laptop need not do the computation. First remote milestone is collection only. Conversion and weight-continuation training can be added in separate bounded tasks after their local interfaces are ready and the user chooses to include them.

Preserve NN-004-R2-T0.05, its selected checkpoint, game rules, opening and sampling settings, bot lifecycle, schema-v1 records and whole-game dataset contract. Four workers is an execution setting, not a new bot or training hypothesis. No predicted fourfold speedup; timing is measured by the user.

## Local execution interface

Add `--workers N` to `python -m rig.cli`, default 1. `--workers 4` selects four worker processes; positive integers only. Existing invocations retain their sequential path. Expose the same option in `scripts/nn_selfplay_collect.py`, default 1, so the user can choose it explicitly. Record requested/effective worker count and inference thread count in metadata and summaries.

Proposed future command, from the project root:

```sh
venv/bin/python scripts/nn_selfplay_collect.py --workers 4 --seed <user-selected-seed>
```

Seed 90001 belongs to the current collection. The user chooses whether a later run repeats it for comparison or uses another seed for new data.

## Process ownership and game identity

- Use a standard-library process pool with an explicit spawn context. A worker initializer sets CPU thread limits and imports/loads each requested bot once. Each worker has its own read-only model copy; no GPU or shared-model machinery.
- Set OMP/MKL thread limits before importing numerical libraries in spawned workers, and set PyTorch intra-op/inter-op threads to 1 before inference starts. Apply this execution configuration in the worker setup, without editing bot SETTINGS or architecture.
- The parent owns run-directory creation, metadata, the only games.jsonl writer, tallies and terminal output. Avoid loading an extra NN in the parent just to obtain IDs; return loaded bot IDs from workers along with results and use them for parent metadata/startup output.
- A worker handles one complete game: create fresh per-seat players, call the existing runner, and construct the existing record. Return the record and bot IDs to the parent. Keep the same callable interface for legacy stateless bots.
- Every task receives the global game index, master seed, module names, colour mode and one shared run ID. Derive seeds exactly as today from master seed, global index and bot identity. Never derive seeds from worker number or task arrival order. Colours also use the global index.
- Write records in global game-index order. Use a small bounded window of outstanding tasks/results, roughly two games per worker, rather than queueing or retaining the entire collection. Wait for the next index when necessary. This keeps existing conversion and helpers compatible without a sorting stage.
- Parent progress counts records written: first game and each existing one-tenth interval (500 for 5,000). Worker output must not produce competing progress lines. Include total wall time through collection/logging; model loads and process startup count toward it.
- Preserve ordinary bot-forfeit handling. A worker/setup failure stops the run visibly; stop outstanding work and publish the existing failed/interrupted summary where possible. Keep records already written. No retry, rescheduling or resume feature.

## GitHub Actions interface

Add a single manually triggered workflow, `.github/workflows/selfplay.yml`, using `workflow_dispatch`. No scheduled, push or pull-request collection triggers. Workflow inputs: games (default 5,000), master seed (explicit), workers (default appropriate to runner), and an explicit repository checkpoint path (default models/first-model.pt). User starts and monitors the job from GitHub Actions.

Steps:

1. Check out the selected code revision and set up Python matching the current local major/minor (3.14, subject to available CPU wheels at implementation). Install the project, NumPy and CPU-only PyTorch; record resolved versions. Do not add GPUs, containers or a dependency-cache project.
2. Select the explicitly named checkpoint supplied by checkout. Export OTHELLO_NN_CHECKPOINT or pass the helper's checkpoint option. Never choose a newest model implicitly.
3. Run the existing collection helper with supplied count, seed, worker count, checkpoint and output directory. Terminal progress is visible in the Actions log.
4. Upload collection output as one downloadable workflow artifact: metadata, raw games, checkpoint-selection provenance, run-summary.txt and helper reports. A simple upload step after a failed collection may retain completed records; no custom recovery workflow.
5. Add a brief job summary pointing to the artifact and reporting checkpoint, bot IDs, games, seed, worker count, time and outcomes. Artifact identity may use GitHub run ID/attempt; reports inside retain their fixed filenames.

Use GitHub-hosted runners; running a self-hosted runner on the laptop would not meet the goal. Start with ubuntu-24.04. Public repositories currently receive four CPUs on the standard Linux runner; private repositories receive two. For a public repo, use one job with four workers. For a private repo, initially use one job with two workers unless the user selects another runner arrangement. A multi-job shard/merge workflow is a later choice, not part of this minimal design. Repository confirmed public; use four workers on this runner.

## Getting the model onto GitHub

User selected adding the model to the repository, and gh confirmed pajh/othello is PUBLIC on 2026-10-01. A copy of the selected parent checkpoint is prepared at models/first-model.pt with a narrow .gitignore exception; the original remains untouched. Once the user chooses to commit/push the prepared changes, checkout supplies the checkpoint directly. Use that repository-relative path as the default workflow checkpoint input, with no release-download step or release asset needed. The model is about 609 KB; ordinary Git storage is sufficient for this baseline copy.

No commit or push has occurred. Record the checked-out code revision and selected checkpoint path in remote provenance. Do not implicitly replace this parent model with future candidates.

Workflow artifacts are temporary retained outputs, not the project's permanent archive. User downloads useful raw collections into runs/ and checkpoints into checkpoints/ before configured retention expires. Use repository-default retention initially. Raw data and weights stay out of Git. No automatic commits, pushes or release creation by the workflow.

## Bounded implementation sequence

1. **T009 — parallel collector:** Bunny edits src/rig/cli.py and a small src/rig/parallel.py only if needed. Add --workers, process setup, game tasks and parent writing; preserve the default sequential path. Handoff documents exact interface and any checks actually performed. Do not edit bots, engine, converter, trainer or current artifacts.
2. **T043 — collection helper option:** Bunny edits scripts/nn_selfplay_collect.py only to pass --workers and retain that setting in provenance/reports. No new analysis features. Short handoff before the next task.
3. **T044 — hosted collection:** on the confirmed public four-CPU runner, Bunny edits .github/workflows/selfplay.yml and adds a short README run/download section. No training steps or deployment/publishing action. The workflow becomes runnable only after the user chooses to commit/push its code with models/first-model.pt included.

The primary design chat maintains project records. Luna reviews or formats results only when an explicit focused check is chosen. No benchmark, game comparison or larger job runs automatically. Any timing/trace comparison between sequential and parallel execution is an explicit user decision, not an additional test suite in this spec.

## Decisions and limits

- Agreed: prepare four-core collection and GitHub Actions route; user runs and monitors experiments.
- Selected: four spawned workers, one inference thread each, single parent writer, manual remote collection workflow and repository model input.
- Confirmed: public repository with standard four-CPU Linux runner; model copy prepared in models/first-model.pt.
- Continuing training from parent weights with a new Adam optimizer remains separately agreed; it is not yet implemented or folded into this collection spec.
- T009 implementation authorized and being dispatched. No hosted run, speed result, commit or push has occurred.

## GitHub references checked 2026-10-01

- [Hosted runner resources](https://docs.github.com/en/actions/reference/runners/github-hosted-runners)
- [Manually running a workflow](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/manually-run-a-workflow)
- [Workflow artifacts and retention](https://docs.github.com/en/actions/concepts/workflows-and-actions/workflow-artifacts)
- [Official upload-artifact action](https://github.com/actions/upload-artifact)
