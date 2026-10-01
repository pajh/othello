# C bot and single-file CG submission plan

Prepared 2026-10-01 at the user's request. Design only: no C implementation, model export or benchmark has run. Python training/self-play remains canonical. OpenCode Space Bunny implements bounded chunks; Luna prepares the requested comparison scripts and summarises results; the user executes and monitors large comparisons/matches and submits to CG.

## Intended result

A local C bot built with make, containing the existing network inference, board/move support and an in-memory model decoder/decompressor. Python generates a model-data header from an explicitly selected best.pt. A combine target pastes the required project files into one C submission, reports its size and compiles that exact combined file locally. The user submits it to CG.

Keep the same learned scoring function. No search, new game strategy, retraining or architecture change in this work. Model export can be repeated for a later selected checkpoint without editing C inference.

## Inputs still needed

- Target confirmed: CodinGame multiplayer bot challenge Othello. Still obtain its starter C I/O protocol, legal-action/pass conventions, compiler/libraries, memory/time limits and submission size rule (bytes versus characters).
- Deployment setting agreed: greedy from turn one (no random opening, highest score), matching the third-model97/2/1 random evaluation. R2/T0.05 remains the Python self-play setting.
- Compression/encoding choice after measuring exported data and the CG limit. Initial C implementation uses float32 weights/arithmetic. User requested an early local FP16 weight-quantisation comparison; measure its effect rather than adopting it implicitly.

These do not block defining/exporting/scoring a known model, but CG-specific integration and a submission-ready size target wait for the actual platform contract. Do not guess a generic CodinGame limit.

### Confirmed Othello statement

The [official multiplayer Othello page](https://www.codingame.com/multiplayer/bot-programming/othello-1) supplies player ID and board size initially, then board rows, legal-action count and legal-action strings on each turn. Empty/black/white are encoded '.', '0', '1'; moves are coordinates such as d3. It specifies 2,000ms on the first turn and150ms on later turns. The platform handles forced passes. Initial implementation uses ordinary mode, not optional EXPERT input.

Therefore reuse supplied legal moves: no C legal-move generator is needed for the first bot. Still implement candidate move flips and actor-relative encoding. Confirm coordinate mapping and zero-action behaviour against the starter/referee; source-size/compiler/library/memory constraints were not established from this statement.

## Model contract

Current network:128 ->256 ->64 ->1, biases on every layer, ReLU/ReLU/sigmoid,49,537 parameters. Raw float32 payload198,148bytes before compression, text encoding or source overhead. Export only model_state_dict weights/biases; no optimizer, RNG or training arrays.

Tensor order is explicit and fixed: network.0.weight[256][128], network.0.bias[256], network.2.weight[64][256], network.2.bias[64], network.4.weight[1][64], network.4.bias[1]. Linear rows are output neurons; columns are inputs. Input is128float32 values: row-major own8x8plane then opponent8x8plane, from the actor's perspective AFTER the candidate action. Score is sigmoid output, no perspective inversion.

Use defined little-endian IEEE754 binary32 payload encoding. Decoder reconstructs floats without aliasing tricks, e.g. through memcpy after byte assembly. Scratch arrays are fixed-size. No PyTorch/BLAS dependency in the submitted C. Start with ordinary float operations and expf; no fast-math or accuracy-changing optimisation before parity is established.

Generated header prominently identifies source checkpoint, model/encoding version, layout, codec, decoded length and payload hash. Keep a readable export report with actual sizes. Preserve the precise checkpoint used for parity beside retained results; do not silently use whichever model is newest when rerunning a comparison.

## Proposed files and make interface

| File | Responsibility |
| --- | --- |
| c/model_data.h | Python-generated packed model payload and constants; no handwritten edits |
| c/model_unpack.h | Decode/decompress payload into resident parameter storage once |
| c/nn_forward.h | Fixed MLP forward pass over the parameter layout |
| c/othello.h | Minimal board encoding and candidate move application; legal move generation only if CG requires it |
| c/bot.h | Select supplied legal move using chosen scoring/settings |
| c/main.c | Platform I/O and one-time model startup |
| c/forward_probe.c | Local numerical comparison executable; excluded from submission |
| scripts/export_c_model.py | Selected checkpoint -> generated header and fixed export report |
| scripts/compare_c_forward.py | Luna's large PyTorch/C comparison driver |
| scripts/combine_c.py | Literal ordered concatenation and final size report |
| Makefile | Small explicit build/export/combine/probe targets |

Keep support routines header-only using static functions/definitions suitable for one translation unit. Standard C/math headers remain normal includes. No build framework or dependency-discovery machinery. New C and Python files are a proposal, not permission to implement all stages.

Planned commands:make bot,make forward-probe,make export MODEL=/explicit/best.pt,make combine,make submission-check. Separate build outputs from generated reports. Reports use fixed latest filenames with the project's existing optional archive convention. Needed generated payload/submission/results belong in retained locations, not only work/. Build products may be disposable.

## Bite-sized implementation sequence

### C001 — freeze platform/model contract and measure size

Primary records supplied CG starter/protocol/limit, chosen deployment settings and an explicit known checkpoint. Bunny prepares a small export/size probe only; it reads weights, emits raw binary32 in fixed order and measures raw/lossless compressed/text-encoded sizes. Do not write a bot or decompressor yet.

Allowed implementation files: scripts/export_c_model.py (initial size-probe stage) and a short handoff. Retain payload/size report under runs/c-export/. Completion: actual size evidence and a concrete codec/encoding proposal with support-code overhead allowance. User selects encoding/compression. If it cannot fit, stop and explain; do not silently reduce precision/change the network.

### C002 — uncompressed reference C forward pass

Bunny implements c/nn_forward.h, c/forward_probe.c and minimal Makefile probe target. Probe accepts a simple local binary batch protocol (documented byte order/count/128float32 inputs) and outputs one float32 score per row. It loads a raw export for this local reference stage; no compression, game logic or CG I/O.

Interface:nn_forward(parameters,input128) ->float score. Completion:buildable probe and a short handoff. A few deliberately chosen input vectors may check plane/index interpretation; the comprehensive comparison is a separate user-run stage, not an implicit large job here.

### C003 — requested comprehensive PyTorch/C comparison

Luna prepares scripts/compare_c_forward.py, referencing one fixed retained checkpoint/export/probe. It selects at least200,000 real after-action positions from retained converted arrays with recorded sources/selection seed. Do not generate new games just to obtain inputs. Existing datasets contain enough rows. Preserve perspective exactly; include both actor perspectives and a range of game stages in the chosen corpus where represented.

Load PyTorch model once, C probe once; stream inputs/results in batches. No process per position. Compare the SAME float32 inputs against the SAME weights. Verify decoded parameter bytes/order independently so export errors and arithmetic differences can be distinguished. A tiny fixed layer-level diagnostic input set can expose wrong transpose/ReLU/bias placement if scores diverge.

Report count, source/game/ply selection, checkpoint/payload hash, compiler flags/library versions, timings, finite/range failures, maximum/mean/percentile absolute differences and count outside agreed tolerance. Retain worst-case input IDs/inputs and scores for diagnosis; do not dump200,000rows in the design chat. Fixed latest report under runs/c-forward-check/; raw comparison artifacts retained separately.

Proposed initial score acceptance rule:abs(C-PyTorch)<=1e-5 +1e-5*abs(PyTorch), for every sample, with all outputs finite and in[0,1]. This is a proposed gate for user agreement, not an observed error bound. No bit-identical score requirement; PyTorch CPU batched and scalar C reductions may round differently. Do not silently loosen thresholds after a failure. User runs the full200,000+comparison and Luna summarises actual results before C bot work continues.

### C003b — early local FP16 weight-storage comparison

User requested 2026-10-01: after FP32 reference parity, round the same checkpoint weights/biases to binary16 for storage, then decode to float32 and run the same C forward arithmetic. This isolates weight precision from changes in accumulation precision. Do not assume native C half types or hardware FP16 support. Initial C bot remains FP32; native FP16 arithmetic is a separate experiment, not included here.

Bunny prepares the small alternate export/decode option; Luna extends the existing comparison driver to use the SAME fixed model/inputs and report score drift versus original PyTorch/FP32 C, payload/submission sizes and changed move selections where candidate groups are available. Follow with user-selected balanced matches using identical behaviour settings to measure any playing-strength loss; score differences alone do not answer how much worse it plays. FP16 parity tolerances are not silently substituted for the FP32 correctness gate. Exact match count and acceptance criteria remain user choices. No quantisation or tests run yet.

### C004 — generated compressed header and in-memory decompressor

After codec selection and reference parity, Bunny finalises exporter into c/model_data.h and implements c/model_unpack.h. Choose a compact existing self-contained decoder when appropriate, preserving its required licence text; do not build a general compression library. No external linked decompression library may be assumed without CG support confirmation.

Interface:model_unpack(payload,length,parameter_storage) ->success/failure; decoded parameter layout/length must match C002. Decode/decompress ONCE at process startup, never per turn. Parameters thereafter read-only. Decompressor and textual encoding overhead count toward submission size. Compressed-data truncation/format failure reports startup failure; no extensive fault-tolerance framework.

Completion: generated header, resident parameter load and fixed export report. Reuse the SAME comprehensive comparison driver through the actual embedded-header/decompress path; user runs it. Lossless decoded parameter bytes must match the reference export, and score tolerance remains unchanged.

### C005 — C board and candidate-action support

Bunny ports only the board/move support needed to encode and apply candidate moves into c/othello.h. Mirror rig.engine coordinates, flips and actor perspective, without adding strategy. Reuse supplied legal moves when platform provides them; add legal move generation only if needed by actual CG protocol. Explicit pass semantics.

Completion: small documented support interface. Luna prepares focused Python-engine versus C candidate-board/encoding checks, especially row/column mapping, both colours and pass handling. User runs them. This stage checks game transformation, separate from neural arithmetic; do not assume200,000correct scores prove legal moves are correct.

### C006 — bot selection and local make build

Bunny implements c/bot.h/c/main.c and make bot with selected model/settings. Score AFTER every candidate action from acting player's perspective; greedy ties use the same supplied-move ordering as Python. No extra RNG/search when greedy is selected. If user selects R2/T0.05 deployment, scope its RNG/own-move/pass state separately rather than silently claiming Python seeded traces match a C RNG.

Use actual CG protocol when supplied. A minimal local adapter/harness can translate rig observations/actions if required; design that as its own small file/task, not a framework. Completion: local executable that takes a valid observation and emits a legal action. User-run local game/match checks follow; compare to Python bot using matching model/settings and record failures.

### C007 — literal combine and exact submission build

Bunny implements scripts/combine_c.py and make combine using a fixed ordered manifest: model_data.h,model_unpack.h,nn_forward.h,othello.h,bot.h,main.c. Literal paste in that order; remove ONLY internal project #include lines that point to already pasted files, retain standard-library includes/licence text. Do not add a minifier/code generator/clever dependency resolver. Emit clear file-boundary comments.

Publish the complete generated submission to a fixed retained path, e.g. runs/c-submission/submission.c. Print byte count and, if relevant, character count versus the confirmed CG limit. Include support code, encoded payload, comments and licences in that count. Exceeding the limit is a failure with actual size, not a claim of submission readiness.

make submission-check compiles the EXACT combined source with known CG-compatible compiler flags locally. Reuse numerical comparison through a probe mode built from that combined source or a minimal compile-time probe entry point; do not concatenate forward_probe.c into the CG main program. This checks that amalgamation didn't change parameter/scoring behavior. User submits manually after successful build/size checks.

### C008 — refresh from a newer selected model

After the first pipeline works:explicit checkpoint export ->make bot ->user-run parity comparison ->make combine/size/exact compile ->manual CG submission. Headers regenerated; C inference/support unchanged unless architecture changes. Keep model selection visible and preserve previous useful submission/report when requested.

## Boundaries and decisions

This user request explicitly authorises planning the comprehensive200,000+position forward-pass check. It does not authorise running it now, launching training or changing compression precision/architecture. Stage prompts specify allowed files and end with concise handoffs. No stage silently implements later ones.

The current hosted-training run remains separate and in progress/unknown at this plan's creation. Choose the known parity model explicitly once it is time to implement, rather than allowing a changing latest-model pointer to invalidate comparison evidence.

Reference:[PyTorch numerical accuracy](https://docs.pytorch.org/docs/main/notes/numerical_accuracy.html) explains floating-point/batched operation differences; proposed tolerances above remain our project choice requiring agreement.
