# Edax 4.6 local setup handoff

Updated: 2026-10-02.

The official Edax 4.6 Linux x86 release is unpacked under ignored `tools/edax/`. The archive URL was `https://github.com/abulmo/edax-reversi/releases/download/v4.6/edax-4.6-linux-x86.tar.gz`; downloaded archive size was 9,524,288 bytes and SHA-256 was `7ca52cb0ccf591ad9690e7d21861d4a6f04b900c686346db98ea26dd30cd966a`.

Use `tools/edax/lEdax-x86-64` (ELF x86-64 baseline) and `tools/edax/data/eval.dat` (13,952,436 bytes, SHA-256 `f8b2299612d9fa4414157e70e932636e33111c2600d2cfc382a7d90ef21b792`). The archive also provides `lEdax-x86-64-v2` and `lEdax-x86-64-v3`; this setup does not assume those CPU-specific variants are supported. The generic binary is dynamically linked to the system `libc` and `libm`. The included evaluation file avoids the separate v4.4 weights archive.

From the project root, substitute a legal Edax move sequence for `F5D6C3` (or another desired prefix) and choose a level. This example asks for one best move at level 10:

```bash
printf 'play F5D6C3\nhint 1\nquit\n' | ./tools/edax/lEdax-x86-64 \
  -eval-file tools/edax/data/eval.dat -book-file tools/edax/data/book.dat \
  -book-usage off -level 10 -n-tasks 1
```

The v4.6 source maps levels 1–10 to the requested depth with selectivity 5, whose table entry is 100% (no selectivity). For positions with more than 20 empty squares, level 10 therefore searches exactly 10 plies at full selectivity. At 20 or fewer empties, the level table searches all remaining empties, potentially solving the position; `-level 10` is not an exact ten-ply cap there. Check the emitted `search` result depth when using the command. `hint 1` prints one best-line analysis and returns to the command loop; `quit` ends normally. The book is disabled with `-book-usage off`.

This command was prepared for the user to run. Edax was not executed, and no position analysis, game, benchmark, generator, hosted job, or training run was launched. Installation readiness here means the archive contents were inspected, extracted, and the baseline executable format/dependencies and artifact hashes were inspected; runtime behavior remains unverified.

References: [official v4.6 release](https://github.com/abulmo/edax-reversi/releases/tag/v4.6), [v4.6 `edax.c` command reference](https://github.com/abulmo/edax-reversi/blob/v4.6/src/edax.c), [v4.6 `options.c`](https://github.com/abulmo/edax-reversi/blob/v4.6/src/options.c), [v4.6 `search.c` level/selectivity table](https://github.com/abulmo/edax-reversi/blob/v4.6/src/search.c), [v4.6 `play.c` hint behavior](https://github.com/abulmo/edax-reversi/blob/v4.6/src/play.c).

## User runtime check — 2026-10-02

User ran initial position level6/n-tasks1/book-usageoff. Startup printed New book6 12 and depth6/score-04/nodes2525; hint1 printed depth6/score-04/nodes401/PVd3 C5 f6 E3; both displayed0:00.000. Analysis worked. Millisecond display does not establish zero cost; hint followed startup search, so this is not an independent cold timing measurement. On quit default data/book.dat save failed ENOENT because launched from project root with no data/ directory. Set -book-file tools/edax/data/book.dat (existing ignored directory) to give Edax a valid local persistence path. Official edax.c initializes book unconditionally and saves it when need_saving even if move selection book usage is disabled. No generated deployment book or generator yet.

## User single-thread initial-position timings — 2026-10-02

User increased Edax levels manually (no helper dispatched). Level34 startup New book search:34@73%,13.692s,265652518nodes; subsequent hint0.044s/231511nodes after same-process startup search. Explicit book-file tools/edax/data/book.dat fixed quit save error. Later fresh process loaded saved book without startup search: level36 hint36@73%,23.701s,470920021nodes; next fresh-process level38 hint38@73%,41.851s,820332319nodes. Both score-02 and PVd3 C5 f6 F5 e6 E3 d6 F7 g6, normal quit. Level38 meets user30–60second single-thread target on initial board. These are selective Edax levels, not exhaustive depths; other book positions and GitHub hardware unmeasured. Level36→38 elapsed ratio1.766. No openingbookgenerator or batch analysis run. Original6/8/10proposal superseded for immediate timing by these manual higher-level probes.
