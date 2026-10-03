Othello Z85 encoding trial — results
====================================

Updated: 2026-10-02. T083. Isolated trial; production Base64 untouched.

Success criterion (user-selected): reconstructed model bytes identical to the
reference quantized blob. Result: PASS for both encodings, byte-for-byte.

Trial artifacts: runs/c-z85-test/ (base64/, z85/, sha256.txt, sizes.txt)
Scratch: work/z85-test/

Payload and sizes (same exact quantized model)
----------------------------------------------
codebook 1024 bytes + indices 49537 bytes = 50561 true payload bytes
reconstructed float32 blob = 198148 bytes

                        Base64 (current)      Z85 (trial)
encoded text chars      67416                 63205
true/padded payload     n/a / 50561           50561 / 50564 (+3 zero pad)
generated header chars  72959                 68818
full submission chars   87775                 83574
net saving               —                    4201 characters (4.8%)

Both headers are under the 75000 model budget. The Z85 header is 68818.

Checksums (identical for both encodings)
----------------------------------------
payload CRC32 (true 50561 bytes):  0xbce3a986
decoded CRC32 (198148 fp32 bytes): 0x2205bf07
Reference blob sha256: 88579b35f6535e7d155454800baa9b067e3a5dc804ac07d8d36815dd10d6c187
Reconstructed sha256 (base64 and z85): identical to the reference.

C probe results (existing probe logic, real C CRC32)
----------------------------------------------------
Both the baseline and trial probes printed:
  payload CRC32:  actual 0xbce3a986 expected 0xbce3a986
  decoded CRC32:  actual 0x2205bf07 expected 0x2205bf07
  RESULT: PASS, reconstruction is byte identical to the reference
`cmp` confirms base64/trial/reference blobs are byte identical.

Builds
------
Baseline probe, trial probe, current base64 submission and trial z85
submission all compile cleanly with GCC C11 (-Wall -Wextra, no warnings in the
final state). ASan/UBSan build of the trial probe ran clean.

Notable finding — C trigraphs
-----------------------------
The Z85 alphabet contains `?`, and the encoded text contained the real trigraph
`??!` at offset 34469. Under C11 phase-1 trigraph translation this would become
`|` inside a string literal and silently corrupt the payload; GCC warned
`-Wtrigraphs`. The generator now breaks the string literal between the two `?`
characters (trigraph translation precedes string-literal concatenation), so the
bytes are unchanged and no trigraph survives. This adds 7 characters to the
header (68811 -> 68818) and is included in the reported sizes.

Ten-thousand-book-run-headroom (not built in this task)
-------------------------------------------------------
The user's 10000-book-run payload budget was 8000 characters. The binding
budget is the full submission, currently 83574 of 100000, leaving 16426
characters for a future opening book. This is headroom observation only; no book
was implemented, generated or sized here.

Files (trial siblings; nothing production changed)
--------------------------------------------------
scripts/embed_nn_z85.py    (new; not called by anything production)
c/model_decode_z85.h       (new; trial decoder, no dual-decode)
runs/c-z85-test/...        (artifacts)

Left unrun / untouched
----------------------
No game was played (byte identity is the success criterion). Production files
(c/bot.c, c/model_decode.h, scripts/embed_nn_codebook.py, the Makefile, the
current runs/c-submission and c-model dirs, models/ and checkpoints/) were not
modified. No commit, push, job, requantization, training or workflow change.
