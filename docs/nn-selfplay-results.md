# Weighted NN self-play review (T035)

The retained run completed 100/100 normal games with no forfeits or unexpected bot IDs. Metadata and summary identify both seats as `NN-003-R2-T0.05`, seed `89012`, alternating colours; the helper reports 50 Black games per seat. Artifacts are in `/home/paul/dev/othello/work/nn-selfplay-smoke/run-e19b28dea22144928689e6d1e083ddf8/`. This review read the summary, metadata and helper report, and parsed the saved JSONL records; it did not rerun a game or load the checkpoint.

## Outcome asymmetry

Bot 1 won 34, bot 2 won 64, with 2 draws. The difference persists in each colour and index-parity group:

| Seat and colour | Wins | Draws | Losses |
| --- | ---: | ---: | ---: |
| Bot 1 as Black (50 games) | 20 | 1 | 29 |
| Bot 1 as White (50 games) | 14 | 1 | 35 |
| Bot 2 as Black (50 games) | 35 | 1 | 14 |
| Bot 2 as White (50 games) | 29 | 1 | 20 |

Overall winning colour was Black in 55 games and White in 43, with 2 draws. By index, bot 1/bot 2/draw outcomes were 20/29/1 on even indices and 14/35/1 on odd indices, so bot 2's advantage is not confined to one assigned colour or parity. The saved diversity report's exact-trace count was 100 unique of 100 (no duplicate groups; duplicate excess 0); all 100 prefixes were unique at lengths 8 and 12, while 79 of 100 were unique at length 4. It found no repeated exact `(pre-action board, to_play)` keys across games among 4,837 positions after the first 12 actions.

All 200 per-seat seeds matched the recorded SHA-256 derivation and the two seeds differed within every game. As a conditional reference only, under an illustrative hypothesis of 98 independent, fair decisive outcomes, 64 wins for either designated seat gives a two-sided binomial probability of approximately `0.00319`. This is not evidence that games are independent, that the bot IDs represent different models, or that a bug exists.

Source inspection found that `rig.cli` creates separate player closures per seat/game, derives RNG seeds per bot ID, and passes those seeds to the corresponding Black/White seats. `rig.runner` then constructs separate seeded RNGs for Black and White. `nn_bot` shares one read-only model but uses the RNG supplied on each call; no direct seat-specific model state or identity branch was found. The bot-2 asymmetry remains unexplained. The smallest discriminating follow-up is a paired source-level experiment: hold the physical Black and White seeds fixed, swap only the identical bot's identity labels, and check whether the physical move trace stays identical. Do not infer a cause from this single batch.
