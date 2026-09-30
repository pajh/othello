# NN self-play runs by seed

I read the metadata and parsed the saved game records in all three completed `run-*` directories currently under `/home/paul/dev/othello/work/nn-selfplay-smoke/`. All runs used `NN-003-R2-T0.05`, 100 games, alternating colours, 100 normal terminations and zero forfeits; each saved set had 100 unique full traces.

| Seed | Run directory | Bot 1 wins | Bot 2 wins | Draws |
| ---: | --- | ---: | ---: | ---: |
| 89012 | `run-e19b28dea22144928689e6d1e083ddf8` | 34 | 64 | 2 |
| 89013 | `run-fb91f4378ad149faac4d17d016dc3022` | 36 | 59 | 5 |
| 89014 | `run-cca0c2775fd34a0e8433ee19299b0c16` | 52 | 46 | 2 |

The latest `run-summary.txt` and metadata match seed 89014 and run `run-cca0c2775fd34a0e8433ee19299b0c16`. Its `diversity-summary.txt` names the same run and seed: 100/100 unique full traces, zero duplicate groups, 76 unique four-action prefixes (largest group 3), 100 unique prefixes at lengths 8 and 12, and no exact `(pre-action board, to_play)` key shared across games in 4,842 positions after the first 12 actions.

The later seed reverses the initial bot-2 lead, so that one result does not show a stable bot-2 advantage. These are only three 100-game batches selected and run by seed, not a sampling design for formal probabilities; the traces and outcomes also do not prove a lack of implementation bug. The summary, metadata, helper diversity report, and game records agree on the latest batch counts. No games were rerun, and no checkpoint or training data was loaded for this review.
