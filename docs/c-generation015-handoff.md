# Generation015 C rebuild handoff — 2026-10-02

Rebuilt the existing C submission using `runs/github-c8-retry/checkpoints/github-candidate/best.pt`. No C source or model checkpoint was edited or promoted. The previous active generated C assets were preserved under `runs/c-generation010/` before the active paths were replaced.

The exported FP32 blob is 198,148 bytes (49,537 parameters), SHA-256 `49a0838bcd81cfd133996379bfc6d9663710b45fd45748553a5cb8b4cfd09622`. Quantization used seed 12345 and one shared 256-center float32 codebook. Weight MAE was 0.00142061329, maximum absolute error 0.02498734, and MSE 3.6334236e-06. The packed payload is 50,561 bytes; Base64 payload is 67,416 characters. Payload CRC32 is `0xbce3a986`; reconstructed FP32 CRC32 is `0x2205bf07`.

The generated header is 72,959 characters, under its 75,000-character limit. `make bot test-nn-embedded` built the bot and reconstruction probe. The probe reconstructed all 198,148 bytes and reported byte-identical PASS against the quantizer's reconstructed blob. Leak detection was disabled (`ASAN_OPTIONS=detect_leaks=0`) due the previously recorded ptrace limitation. The one-file submission is 87,775 characters (SHA-256 `a4a028ad702c67e39410877448de636d878d3afe0a6fa5c33d7c7749c07979e6`), under the 100,000-character limit, and compiled cleanly with the prescribed GCC command and no diagnostics.

One supervised smoke game ran with seed 96003: C bot vs random, normal termination, 0 forfeits, C won. Run ID `75241f7173834d9886230c94696d322b`; raw game record and metadata are in `runs/c-generation015-smoke/run-7d975b742cbc469891482431db13e812/`. The wrapper still reports the historical ID `C-RAND-001`. This single smoke result does not measure playing strength. No quantized score-drift comparison, larger evaluation, CodinGame submission, checkpoint promotion, commit, or push was performed.

Logs are retained in `runs/c-generation015/logs/`; current generated assets remain at `runs/c-model-export/`, `runs/c-model-quantized/`, `runs/c-model-embedded/`, `runs/c-embedded-check/`, and `runs/c-submission/`.
