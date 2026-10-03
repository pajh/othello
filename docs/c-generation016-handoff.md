# Generation016 C model embedding handoff — 2026-10-03

Rebuilt the generated C model and one-file submission from `runs/github-c8-second/checkpoints/github-candidate/best.pt`. No source, bot, script, workflow, model pointer, or project-record files were changed. The prior active generated assets were preserved under `runs/c-generation015-negamax/` before replacement.

The selected checkpoint SHA-256 is `19edfd4f69789a1c50025b2dd71199b07007ebccdf21a91ba8e0904f12440041`. Export produced 49,537 little-endian FP32 values (198,148 bytes; exported blob SHA-256 `64decce07edcda479e02e98d9e0f9f17c3bf07dcb598428b3ed7241ea31b792c`). The exported architecture is 128→256→64→1 with ReLU, ReLU and sigmoid.

Quantization used the existing shared 256-center KMeans tool with seed 12345. Weight MAE was `0.00154476004`, maximum absolute error `0.0359053612`, and MSE `3.99810423e-06`. The summary reports one KMeans label disagreement after converting centers to float32; assignments use the nearest stored float32 center, as specified by the exporter. The packed payload is 50,561 bytes (1,024-byte codebook plus 49,537 indices). Z85 embedding produced a 68,808-character header, below its 75,000-character limit; payload CRC32 is `0x1f072be6` and reconstructed FP32 CRC32 is `0x4b81c32f`.

The embedded reconstruction probe passed with byte-identical output against the quantizer’s reconstructed FP32 blob: 198,148 bytes, verified CRCs, `cmp` exit 0. It was built with the existing ASan/UBSan target and run with `ASAN_OPTIONS=detect_leaks=0`, retaining the known leak-check ptrace limitation.

Build checks completed:

- `make -B bot CFLAGS='-std=c11 -O3 -Wall -Wextra'` completed without diagnostics.
- `make -B test-nn-embedded` completed without diagnostics; the reconstruction probe passed as above.
- `scripts/scrunch.py` assembled `runs/c-submission/submission.c` at 91,238 ASCII characters/bytes, 8,762 below the 100,000 limit.
- The exact submission compiled with `gcc -std=c11 -O3 -Wall -Wextra -o build/c-submission runs/c-submission/submission.c -lm` using GCC 16.2.1, without diagnostics.

Submission SHA-256 is `8368875504c3506feec4732b262e22ee0b2490ac43e0f45013b0a025fe65ef43`. The wrapper-used `build/c-random-bot` was replaced with an exact copy of the compiled one-file submission; both binaries have SHA-256 `e9db2a9a6e579a452fa0379699006e7ad93260f46f2e708d3a7c3a8215983205` (87,496 bytes). This prepares the match executable; no game, timing, numerical-corpus comparison, or strength evaluation was run in this task.

Current generated assets are under `runs/c-model-export/`, `runs/c-model-quantized/`, `runs/c-model-embedded/`, `runs/c-embedded-check/`, and `runs/c-submission/`. Archived Generation015 assets are under `runs/c-generation015-negamax/`.
