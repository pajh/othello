# Command guide

Commands below run from the repository root and use the existing `venv/`. They are reference commands: collection, training, evaluation batches and GitHub workflow dispatch are launched and monitored by the user. Use a new output directory for each new collection or training run. For the raw game directory, copy the actual `run-*` path printed by the collector. Training output names are yours to choose. The export examples below rebuild the current C artifacts at their existing paths; use separate directories if you want to preserve an earlier export. Variable-assignment examples use Bash syntax.

## 1. What is available

| File or target | Purpose and current caveat |
| --- | --- |
| `scripts/nn_selfplay_collect.py` | Maintained 5,000-game collector/reviewer. Supports `--games`, `--seed`, `--workers`, `--output-dir`, `--checkpoint`, and `--review-run`. Its defaults are historical (`first-model`, seed 90001, one worker); pass all choices explicitly. |
| `scripts/batch_smoke.py` | Two-game random/random CLI smoke in `work/batch-smoke/`; not a strength run. |
| `scripts/max_bot_smoke.py` | Historical 100-game max/random smoke in `work/max-bot-smoke/`. |
| `scripts/nn_bot_smoke.py`, `scripts/nn_opening_smoke.py`, `scripts/nn_selfplay_smoke.py` | Earlier fixed 100-game helpers. They hardcode first-model paths and/or earlier bot IDs/settings; `nn_opening_smoke.py` expects stale `NN-002-R2` while current NN is `NN-004-R2-T0.05`. Do not use them as current-model evaluation or current 5,000-game collection commands. |
| `scripts/dataset_smoke.py`, `scripts/train_first.py` | Historical checks for the original 1,000-game dataset and first training output, with fixed original run/checkpoint IDs. They do not convert or assess the latest run. |
| `scripts/smoke.py` | One direct random/random engine smoke, without the batch CLI. |
| `scripts/export_nn_blob.py` | Export a selected PyTorch checkpoint to a raw parameter blob and layout report. |
| `scripts/quantize_nn_blob.py` | Fit the selected shared 256-center codebook and write indices plus reconstructed float blob. Requires the already-installed scikit-learn in this environment. |
| `scripts/embed_nn_codebook.py` | Z85-encode codebook and indices into `model.h`, with payload and reconstructed-model CRC32 values. No compression. |
| `scripts/generate_nn_test_csv.py` | Produce replay-board inputs and matching PyTorch scores from an NPZ dataset/checkpoint. |
| `scripts/scrunch.py` | Assemble the listed local C headers into a one-file source and report its character count. |
| `scripts/notify_codex.sh` | Project-local OpenCode completion notification controls; details in [notification-workflow.md](notification-workflow.md). |

`make` and `make all` build the default target `bot`; `make bot` builds `build/c-random-bot` from `c/bot.c`. That current source is the greedy embedded neural C bot (C-NN-003); the executable filename is historical. The `bots.c_random_bot` rig wrapper launches that binary as one persistent child per seat/game. Its reported Python ID remains the stale `C-RAND-001`; reports therefore do not identify its actual C-NN-003 behavior. C plays greedily from its first move and has no random NN opening. `make test-nn`, `make test-nn-compare`, and `make test-nn-embedded` build probe executables only; running each is a separate explicit command. `make clean` removes these build outputs.

## 2. Collect self-play, convert, and train

The canonical rig CLI can run any modules and count. It alternates which bot is Black by game unless `--force-start` is given. `--workers 1` is sequential; larger values spawn worker processes, each with one numerical thread. Progress and the current run path are printed, and the run contains `games.jsonl` and `metadata.json`; the output root receives the latest `run-summary.txt`. For neural collection, the wrapper adds checkpoint provenance and collection/diversity reports.

For multiple batches, use a distinct seed and output root for every invocation. To run batches concurrently, start each as a separate user-controlled process and keep their output roots separate; do not point concurrent writers at the same summary path.

The latest model used for evaluation and the C submission is the downloaded hosted candidate, `runs/github-first/checkpoints/github-candidate/best.pt`. For another user-chosen collection, provide a unique output root and a new seed:

```sh
venv/bin/python scripts/nn_selfplay_collect.py \
  --games 5000 --seed YOUR_NEW_SEED --workers 4 \
  --checkpoint "$PWD/runs/github-first/checkpoints/github-candidate/best.pt" \
  --output-dir runs/NAME-YOU-CHOOSE
```

Replace the uppercase seed/name placeholders before running. After it finishes, set `RUN_DIR` to the actual `run-*` directory printed by the collector (do not type the example pattern literally). To review a saved run without collecting again:

```sh
RUN_DIR=runs/NAME-YOU-CHOOSE/run-PASTE-ACTUAL-ID
venv/bin/python scripts/nn_selfplay_collect.py \
  --review-run "$RUN_DIR"
```

For direct rig batches, set the checkpoint explicitly in the environment. `--workers 1` is the CLI default; choose the worker count explicitly when desired. Output roots can contain multiple unique `run-*` directories, but a fresh root makes the reports unambiguous.

```sh
OTHELLO_NN_CHECKPOINT="$PWD/runs/github-first/checkpoints/github-candidate/best.pt" \
venv/bin/python -m rig.cli \
  --bot1 bots.nn_bot --bot2 bots.nn_bot --games 100 --seed YOUR_NEW_SEED \
  --workers 1 --output-dir runs/NAME-YOU-CHOOSE
```

Convert a completed run directory (or its `games.jsonl`) into whole-game 80/20 training and validation NPZ files. `--seed` is required; `--train-fraction` defaults to `0.8`. Forfeits are excluded, and games are kept intact across the split. Add `--symmetries` to generate all eight orientations in each split (the GitHub workflow does this).

```sh
RUN_DIR=runs/NAME-YOU-CHOOSE/run-PASTE-ACTUAL-ID
venv/bin/python -m training.convert \
  --input "$RUN_DIR" \
  --output-dir "$RUN_DIR/dataset" \
  --seed 12345
```

Train into a fresh output directory. To continue the currently selected model, load its `best.pt` weights with the agreed fresh Adam optimizer; `last.pt` is the last epoch, not the selected best-validation checkpoint. The trainer starts a new epoch sequence and carries no optimizer/RNG/early-stopping state. Defaults: 30 maximum epochs, batch 256, Adam learning rate 0.001, seed 12345, patience 3. It prints epoch progress and writes `best.pt`, `last.pt`, `training-history.json`, and `training-summary.txt`.

```sh
RUN_DIR=runs/NAME-YOU-CHOOSE/run-PASTE-ACTUAL-ID
venv/bin/python -m training.train \
  --dataset-dir "$RUN_DIR/dataset" \
  --output-dir checkpoints/NAME-YOU-CHOOSE \
  --initial-checkpoint "$PWD/runs/github-first/checkpoints/github-candidate/best.pt"
```

Do not reuse a nonempty output directory for a new training run. Review training loss only alongside its dataset and validation split; match results are a separate evaluation.

## 3. Evaluate candidate and parent, or a greedy bot

For a same-process head-to-head, use the disposable candidate snapshot and the canonical parent through `OTHELLO_NN_CHECKPOINT`. The snapshot hardcodes the candidate path; recreate it only through the project's selected snapshot workflow if changing the candidate. This example uses the downloaded hosted candidate and its exact downloaded parent. Both use NN-004-R2-T0.05, two random own moves then seeded weighted selection; the CLI alternates colours.

```sh
OTHELLO_NN_CHECKPOINT="$PWD/runs/github-first/runs/github-selfplay/parent.pt" \
venv/bin/python -m rig.cli \
  --bot1 bots.nn_candidate_bot --bot2 bots.nn_bot --games 100 --seed 93001 \
  --workers 1 --output-dir runs/NAME-YOU-CHOOSE
```

`bots.nn_candidate_bot` is a disposable snapshot that currently hardcodes `runs/github-first/checkpoints/github-candidate/best.pt`. The canonical bot loads the exact parent from the environment above. For another candidate, ensure the disposable copy and its hardcoded checkpoint match the intended candidate before relying on this command. Reports show bot code IDs; record checkpoint paths beside the result because equal IDs do not imply equal model weights.

For greedy NN versus random, use the disposable `bots.nn_eval_bot`; it currently selects the hosted candidate and uses R0/T0 (greedy from the first move):

```sh
venv/bin/python -m rig.cli \
  --bot1 bots.nn_eval_bot --bot2 bots.random_bot --games 100 --seed 93002 \
  --workers 1 --output-dir runs/NAME-YOU-CHOOSE
```

For the C bot versus random, first build, then run the batch CLI. The wrapper launches the compiled process once per seat/game and keeps it alive for that game's turns; forced passes are handled by the rig. The C bot itself is greedy from its first move.

```sh
make bot
venv/bin/python -m rig.cli \
  --bot1 bots.c_random_bot --bot2 bots.random_bot --games 100 --seed YOUR_NEW_SEED \
  --workers 1 --output-dir runs/NAME-YOU-CHOOSE
```

This wrapper currently reports `C-RAND-001` even though `make bot` builds C-NN-003. Do not treat the label or one smoke game as evidence of measured strength. Larger evaluations are user-run and monitored.

## 4. Export, quantize, embed, and inspect the neural C payload

Choose the checkpoint deliberately. The current hosted candidate is `runs/github-first/checkpoints/github-candidate/best.pt`; the repo's `models/best.pt` now contains the newer symmetry-trained candidate at `runs/github-symmetry/checkpoints/github-candidate/best.pt`, selected after its 65.15% parent-match score. Promotion to `models/best.pt` is an explicit user decision; copying it changes the checkpoint supplied by a future GitHub run only after that file is committed and pushed.

The current export paths below feed the Makefile and scrunch commands. The FP32 export is headerless little-endian binary32, 49,537 parameters and 198,148 bytes, with `blob-layout.txt` describing tensor order and offsets:

```sh
venv/bin/python scripts/export_nn_blob.py \
  --checkpoint "$PWD/runs/github-first/checkpoints/github-candidate/best.pt" \
  --output-dir runs/c-model-export
```

Generate a 10,000-row replay-derived reference corpus from the matching validation archive and checkpoint. `--count` defaults to 10000 and `--seed` to 12345. It writes `inputs-and-scores.csv` and `corpus-summary.txt`:

```sh
venv/bin/python scripts/generate_nn_test_csv.py \
  --dataset runs/github-first/runs/github-selfplay/run-a618633805de46679deccb20377b348a/dataset/validation.npz \
  --checkpoint "$PWD/runs/github-first/checkpoints/github-candidate/best.pt" \
  --output-dir runs/c-forward-corpus --count 10000 --seed 12345
```

Build and run the original FP32 C/PyTorch comparison. `make test-nn-compare` builds only; the executable takes the blob and CSV paths:

```sh
make test-nn-compare
mkdir -p runs/c-forward-check
ASAN_OPTIONS=detect_leaks=1 ./build/test-nn-compare runs/c-model-export/model.bin \
  runs/c-forward-corpus/inputs-and-scores.csv \
  > runs/c-forward-check/forward-summary.txt
cat runs/c-forward-check/forward-summary.txt
```

Quantize the exact exported blob. This uses one shared 256-float32-value codebook for all weights and biases, plus one uint8 index per parameter. It writes `codebook.bin` (1,024 bytes), `indices.bin` (49,537 bytes), a reconstructed `model.bin`, and a summary. The packed payload is 50,561 bytes before Z85/header text.

```sh
venv/bin/python scripts/quantize_nn_blob.py \
  --input runs/c-model-export/model.bin \
  --output-dir runs/c-model-quantized --seed 12345
```

Measure score drift with the same corpus:

```sh
mkdir -p runs/c-quantized-check
ASAN_OPTIONS=detect_leaks=1 ./build/test-nn-compare \
  runs/c-model-quantized/model.bin runs/c-forward-corpus/inputs-and-scores.csv \
  > runs/c-quantized-check/forward-summary.txt
cat runs/c-quantized-check/forward-summary.txt
```

The strict FP32 tolerance is expected to fail after quantization; mean/max error measure the changed scores. The retained run measured mean absolute error 0.0008242 and maximum 0.0086673 with no invalid scores. Playing strength is measured separately.

Embed the quantized codebook and indices as Z85 (encoding only; no DEFLATE or other compression). Output is `model.h` plus `embedding-summary.txt`; the generated header contains payload and reconstructed-FP32 CRC32 checksums and enforces a 75,000-character header limit. Three zero padding bytes make the 50,561-byte true payload divisible by 4; the decoder checks and discards only those known bytes.

```sh
venv/bin/python scripts/embed_nn_codebook.py \
  --codebook runs/c-model-quantized/codebook.bin \
  --indices runs/c-model-quantized/indices.bin \
  --output-dir runs/c-model-embedded
```

Build and run the embedded reconstruction byte comparison against the quantizer's reconstructed blob:

```sh
make test-nn-embedded
mkdir -p runs/c-embedded-check
ASAN_OPTIONS=detect_leaks=1 ./build/test-nn-embedded \
  runs/c-model-quantized/model.bin runs/c-embedded-check/model.bin \
  > runs/c-embedded-check/reconstruction-summary.txt
cat runs/c-embedded-check/reconstruction-summary.txt
```

Replay the same score comparison on the reconstructed blob if desired:

```sh
ASAN_OPTIONS=detect_leaks=1 ./build/test-nn-compare \
  runs/c-embedded-check/model.bin runs/c-forward-corpus/inputs-and-scores.csv \
  > runs/c-embedded-check/forward-summary.txt
cat runs/c-embedded-check/forward-summary.txt
```

The reconstruction was byte-identical to the quantized blob, so score results should match the quantized comparison. This checks the payload reconstruction; it does not test quantized scores against the original as a pass gate. The existing FP32 comparison tolerance is expected to fail for quantized values. Read mean/max score drift in the comparison output as a measurement. `make test-nn` builds the small random-weight forward smoke; run it with `build/test-nn`. Sanitizer builds are already used for these isolated probes. A direct sanitizer build of the current standalone NN smoke is:

```sh
cc -std=c11 -O1 -g -Wall -Wextra -fsanitize=address,undefined \
  -fno-omit-frame-pointer -o build/test-nn c/test_nn.c \
  -fsanitize=address,undefined -lm
ASAN_OPTIONS=detect_leaks=1 build/test-nn
```

The current packed model payload is 50,561 bytes (1024-byte codebook plus 49,537-byte index stream), Z85-encoded as 63,205 characters. Z85 is not compressed; source text also includes C code and is subject to the separate 100,000-character CodinGame limit.

## 5. Build and scrunch the CodinGame submission

`make bot` needs the generated include directory `runs/c-model-embedded/model.h`; run the export/quantize/embed steps for the selected model first. It builds the ordinary executable from `c/bot.c` and the local headers with `-lm` for `expf`:

```sh
make bot
```

The scruncher follows only quoted includes listed in the main source, in their listed order. It does not recursively open includes inside pasted headers; it removes those quoted directives. It strips comments and comment-only lines, while preserving original blank lines and other whitespace. It prepends `#pragma GCC optimize("O3,inline")`; the pragma counts toward the size. Standard angle-bracket includes remain. The default limit is 100000 characters and an over-limit file is still written with a warning.

```sh
venv/bin/python scripts/scrunch.py \
  --input c/bot.c --output runs/c-submission/submission.c \
  --include-dir c --include-dir runs/c-model-embedded
```

The current retained submission is 87,775 characters. Compile the one-file artifact directly with the platform-compatible C compiler and math library:

```sh
gcc -std=c11 -O2 -Wall -Wextra \
  -o build/c-submission runs/c-submission/submission.c -lm
```

To submit, open the CodinGame Othello bot editor, replace its source with the complete contents of `runs/c-submission/submission.c`, and run the site's own compile/play controls. The user confirmed the neural submission is running in Wood 2, reported rank 78 and a convincing IDE win against the boss. No promotion has been reported. Arena placement and IDE boss matches are separate evidence. The current C source contains a stale comment saying coordinate orientation is unconfirmed; the primary record says the official referee source confirmed a1 is top-left.

## 6. GitHub hosted collection and training

`.github/workflows/selfplay.yml` is manual-only: collect self-play, convert with symmetry augmentation, train, evaluate against the exact parent, then upload the artifacts. It now evaluates the candidate remotely over 1,000 games with R2/T0.05 on both seats and alternating colours. It does not promote the candidate or update `models/best.pt`. Conversion enables all eight symmetries independently after the whole-game split; training uses patience 1, retaining best.pt at the first epoch without validation improvement. Evaluation uses the collection seed plus 100000. Before dispatch, commit and push the intended code and checkpoint to the selected ref; an uncommitted local checkpoint is unavailable to GitHub Actions. The selected `models/best.pt` is now the symmetry-trained candidate from run 36887079634, copied explicitly for the next round.

From the Actions page choose **NN self-play training** and run it manually, or use `gh` with explicit inputs:

```sh
gh workflow run selfplay.yml --ref master \
  -f games=5000 -f seed=YOUR_NEW_SEED -f workers=4 \
  -f checkpoint=models/best.pt
```

This dispatch command launches work. Check/watch it deliberately:

```sh
RUN_ID=PASTE_ACTUAL_RUN_ID
gh run list --workflow selfplay.yml --limit 5
gh run watch "$RUN_ID"
gh run view "$RUN_ID"
mkdir -p "runs/github-download-$RUN_ID"
gh run download "$RUN_ID" --dir "runs/github-download-$RUN_ID"
```

Downloaded paths are relative to the download directory:

- `runs/github-selfplay/parent.pt`: exact collection/training parent.
- `runs/github-selfplay/run-*/`: raw games, metadata and `dataset/` splits.
- `runs/github-selfplay/`: collection reports and workflow runtime provenance.
- `checkpoints/github-candidate/`: `best.pt`, `last.pt`, training history and summary.
- `runs/github-evaluation/`: 1,000-game records, evaluation log, run summary and candidate score report.
- `src/bots/nn_hosted_candidate_bot.py`: disposable snapshot generated for that evaluation.

The artifact contains raw games, converted NPZ data, summaries/provenance, the actual copied parent checkpoint when the selected input exists, and candidate checkpoints under `checkpoints/github-candidate/`. Keep the downloaded artifact and review its summaries before a local match. To use a downloaded parent/candidate, point the canonical bot to the parent through `OTHELLO_NN_CHECKPOINT`; the disposable candidate module currently hardcodes the known path `runs/github-first/checkpoints/github-candidate/best.pt`, so adjust/regenerate that snapshot for a differently located candidate. Promotion remains an explicit file-copy plus Git commit/push decision.

Current result for reference: GitHub run `36841281392` completed successfully with seed `90003`, 5,000 games, and four workers. Its artifacts were downloaded into `runs/github-first/`. That earlier run predates symmetry expansion and hosted evaluation; the next run will exercise those additions.

## 7. OpenCode and completion notifications

The identified Space Bunny Free conversation is `ses_f09b671eaffeJHQOKjugvgpYJR`. Confirm the visible session before routing work if the user's conversation changes. For implementation, explicitly select `--agent build`; the model is `opencode/space-bunny-free`. Keep tasks bounded and send one at a time. The exact registration/recovery procedure and limits are in [opencode-workflow.md](opencode-workflow.md) and [notification-workflow.md](notification-workflow.md). Notification controls are:

```sh
bash scripts/notify_codex.sh status
bash scripts/notify_codex.sh on
bash scripts/notify_codex.sh off
```

Notifications are project-local and currently enabled. Hook delivery was visibly confirmed after the design chat became idle; reliable delivery during an active turn remains unverified.
