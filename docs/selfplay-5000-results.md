# 5,000-game self-play collection

The collection completed on 2026-10-01 with 5,000 normal terminations and no forfeits. Both seats used `NN-004-R2-T0.05` (`bots.nn_bot`) with checkpoint `checkpoints/first-model/run-2103bc51994e46a099f8b3d78618efd3/best.pt`. Bot 1 was Black on even game indices; each bot had 2,500 Black assignments. Master seed: 90001, with per-game seeds derived as SHA-256 first eight bytes, big-endian, of `{master_seed}:{game_index}:{bot_id}`. The CLI elapsed time was 914.067 seconds.

Results were 2,397 bot 1 wins, 2,424 bot 2 wins, and 179 draws. Diversity checks reported no exact action-trace duplicate groups. The first-four-action prefix count was 244 unique (largest group 61); the first-eight count was 4,789 (largest group 4); after twelve actions all 4,998 observed prefixes were unique. Among 241,823 late-position rows, two absolute-colour `(board, to_play)` keys were shared across games, covering four rows. Position counts used no symmetry canonicalisation.

These are descriptive self-play counts, not independent samples or evidence of strength improvement. The collection metadata records the checkpoint and configuration; the run metadata reports the bot IDs, count, seed, outcomes, alternating starts, and elapsed time. No new training was run. The selected next training setup is to continue from the existing weights with a new Adam optimizer.
