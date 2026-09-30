# Batched NN self-play timing and trace check (T038)

The seed-89014 `NN-004-R2-T0.05` run completed 100/100 normal games with zero forfeits: bot 1 won 52, bot 2 won 46, and 2 were draws. Metadata selects the retained [best.pt](/home/paul/dev/othello/checkpoints/first-model/run-2103bc51994e46a099f8b3d78618efd3/best.pt); both bot IDs, seed and alternating-colour mode agree with the summary. The run is retained at `/home/paul/dev/othello/work/nn-selfplay-smoke/run-6a61be6d34b1494b92af7db0f7ce3eec/`.

Parsing the 100 saved records and comparing ordered absolute-colour `(to_play, action)` traces by `game_index` with the prior NN-003 run `run-cca0c2775fd34a0e8433ee19299b0c16` found all 100 traces identical. The current diversity report records 100 unique traces, 76 unique four-action prefixes, all 100 prefixes unique at lengths 8 and 12, and no shared exact late-position key among 4,842 rows after the first 12 actions. This one same-seed comparison does not promise identical traces for other seeds or versions.

The helper measured CLI time at 16.257 seconds, or 6.151 games/second. This boundary includes process startup, import and checkpoint load, game execution, logging and CLI work. Total helper time through diversity analysis, before report publication, was 16.296 seconds. Its 5,000-game estimate is 812.9 seconds (13.55 minutes), a simple linear extrapolation rather than a runtime promise. Against the user's approximate 23-second-per-100-game baseline, this run took about 29.3% less time, or about 1.415× the speed. That baseline is not a controlled benchmark, so the comparison is indicative only.

Review was limited to the fixed reports, metadata and current/previous saved records; no games were rerun, and no checkpoint or training data was loaded.
