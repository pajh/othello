# Z85 production promotion and source-cleanup estimates

Updated: 2026-10-02. T084. Z85 adopted; old Base64 model path removed.

## Promotion

The T083-tested Z85 encoder and decoder were promoted into the canonical names;
the redundant trial siblings `scripts/embed_nn_z85.py` and
`c/model_decode_z85.h` were deleted after the production replacement verified.

- `scripts/embed_nn_codebook.py` — now emits Z85 text (`model_z85`,
  `MODEL_Z85_LENGTH`, `MODEL_PAYLOAD_PADDED_BYTES`); same CLI
  (`--codebook --indices --output-dir`); same true/padded lengths, both CRC32s,
  zero-pad check and trigraph-safe literal splitting.
- `c/model_decode.h` — now the Z85 decoder. `load_embedded_model(Model *,
  unsigned char **)` API, CRC byte-identity checks and zero-pad handling are
  unchanged. There is no dual decode and no Base64 fallback.
- `c/test_nn_embedded.c` — probe now reports `z85 chars` and points at
  `model_decode.h`; no source-shortening or renaming was applied.

Canonical `c/bot.c` still includes `model_decode.h`; the Makefile is unchanged.

## Old-artifact preservation

Current working Base64 artifacts were copied to `runs/c-base64-final/` before
regeneration, together with the superseded source copies for provenance
(documentation only — no old decoder in the active bot):

- `submission.c`, `size-summary.txt` (Base64 build, 87,775 chars)
- `model-base64.h`, `embedding-summary-base64.txt`
- `embed_nn_codebook_base64.py`, `model_decode_base64.h`,
  `test_nn_embedded_base64.c`

## Regeneration and verification

```sh
venv/bin/python scripts/embed_nn_codebook.py \
  --codebook runs/c-model-quantized/codebook.bin \
  --indices runs/c-model-quantized/indices.bin \
  --output-dir runs/c-model-embedded
make bot test-nn-embedded
ASAN_OPTIONS=detect_leaks=0 ./build/test-nn-embedded \
  runs/c-model-quantized/model.bin runs/c-embedded-check/model.bin
venv/bin/python scripts/scrunch.py --input c/bot.c \
  --output runs/c-submission/submission.c \
  --include-dir c --include-dir runs/c-model-embedded --limit 100000
cc -std=c11 -O2 -Wall -Wextra -lm -o build/c-z85-promotion-bot \
  runs/c-submission/submission.c
```

Results:
- Generated header: 68,815 chars (limit 75,000).
- C probe: `RESULT: PASS, reconstruction is byte identical to the reference`;
  payload CRC32 `0xbce3a986`, decoded CRC32 `0x2205bf07` (both expected values).
- Prior quantized weights re-used unchanged; no requantization.
- Scrunch: **83,566** characters (was 87,775 with Base64; net saving 4,209).
- Exact single-file compile clean (`-Wall -Wextra`).
- Smoke: one supervised game vs `bots.random_bot`, seed 96004,
  `runs/c-z85-promotion-smoke/` — 1/1 normal, 0 forfeits, NN won.

Expected 83,574 vs actual 83,566: the small difference is the canonical
`render_header`/summary/probe comment wording (the trial banner said "TRIAL"
and had a slightly longer comment block). Payload and decoder text are the same
63,205 Z85 characters in both, so the difference is comments only.

## Source-cleanup estimates (read-only; not implemented)

Measured on `runs/c-submission/submission.c` (83,566 chars):

- removable leading indentation (spaces/tabs at line start): **5,272**
- removable trailing whitespace per line: 10
- removable blank/whitespace-only lines: 0
- **readily-removable lower bound: ~5,282 characters** (~6.3% of the file)

Whitespace inside string literals is excluded (the model data is a literal and
is not touched). This is a lower bound, not a promise that the file compiles
after only these removals.

Optional private-identifier shortening (token-aware, read-only count excluding
strings and comments): 193 distinct identifiers, 8,495 identifier characters.
Representative long names and the characters saved if renamed to 3 chars —
`board_size` x33 (231), `MODEL_PAYLOAD_PADDED_BYTES` x10 (230), `BOARD_CELLS`
x9 (72), `action_count` x8 (72), `MODEL_LAYER_COUNT` x5 (70),
`MODEL_CODEBOOK_COUNT` x4 (68), `MODEL_PAYLOAD_BYTES` x4 (64). Renaming
interfaces or preprocessor macros globally is explicitly **not** done here.

## New canonical commands

The embed/scrunch/compile commands above are the current canonical ones;
`docs/command-guide.md` now describes Z85 instead of Base64. Run the promoted
probe with `ASAN_OPTIONS=detect_leaks=0` (the retained ptrace/leak-sanitizer
limitation).

## Status and limits

- Production model path is now Z85 only; no Base64 decoder remains.
- No game beyond the one authorized smoke; no strategy/opening-book features.
- Cleanup estimates are measurements only; no minification implemented.
- No commit or push; Primary handles that.
