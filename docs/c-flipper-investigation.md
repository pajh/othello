# Bitboard flipper source-budget investigation — 2026-10-02

Current submission 84,767 characters; headroom15,233; hypothetical10,000-characterbook leaves5,233 for flipper/search/lookup. Whitespace cleanup estimated earlier~5,282+ (not applied).

Official Edax master source downloaded read-only to work/edax-flipper-research/. Entire-file sizes after existing scrunch comment removal (not optimized standalone extractions):
- flip_avx_ppseq.c:7,791 characters, AVX2 intrinsics and 66-entry four-lane masktable; simd.h type/support adaptation needed.
- flip_bmi2.c:11,301 characters PLUS externallydefined MASK_X table from flip.c; requires PEXT/PDEP/BEXTR instructions and lookup tables.
- flip_bitscan.c:52,436 characters.
- flip_carry_64.c:79,804 characters.
- flip_kindergarten.c:137,239 characters.
- flip_roxane.c:72,734 characters.
- flip_sse.c:71,452 characters.
These figures include variants/wrappers present in eachfile, exclude requiredsharedheaders/tablesunlessalreadyinfile; not netsubmissiondeltas. CPU support/performanceonCG unmeasured.

Edax flip_slow.c has a small scalar reference flipper. Extracted function (including eightedge masks) 670 characters before standalone adaptation; uses x_to_bit and PASS requiring smalladaptation. It scans atmosta boundedboardray ineachdirection, suitable correctnessreference but upstreamnamesitslow, notspeedclaim. A compact table-free fixedshift/propagation implementation estimated1–2KB is likely betterbudgetfit; implementation/correctness/performance unmeasured. Updateboards via flippedmask then swapplayerperspective, inexpensive.

Recommendation: start with a table-free portable scalar flipper, verify against engine/reference, then user-runrolloutbenchmark. Do not spend current5,233afterbook budget on fullAVX2tables before measuring requireddepth/deadline. Could revisit generated-at-startup masks/SIMD if performance provesinsufficient. No implementation or benchmark authorized/run inthisinvestigation.

Primarysources: https://github.com/abulmo/edax-reversi/blob/master/src/flip_avx_ppseq.c ; https://github.com/abulmo/edax-reversi/blob/master/src/flip_bmi2.c ; https://github.com/abulmo/edax-reversi/blob/master/src/flip_slow.c . GPLv3 sourceprovenance applies to direct reuse.
