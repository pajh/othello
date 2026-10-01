# Project status

Updated: 2026-10-01.

- Canonical pipeline: sequential/parallel rig, schema-v1 game logs, whole-game conversion, CPU outcome MLP/trainer with weights-only initialization. Bot NN-004-R2-T0.05: two random own moves then T0.05 weighted choice. Current selected model: checkpoints/third-model/run-selfplay-5000/best.pt.
- Generation003: first selfplay5000, parent first-model best.pt, seed90001, sequential914.067s. Second model bestepoch1; same-split validation0.203582 ->0.193218. Matches: candidate/random86/5/9, candidate/parent62/6/32.
- Generation004: next selfplay5000, parent second-model best.pt, seed90002,4workers249.131s,5000normal0forfeits. Third model bestepoch1; same-split validation0.199267 ->0.186284. Matches: greedy third/random97/2/1; R2/T0.05 third/second63/4/33. Both successive head-to-head batches yielded65%candidate score; no plateau established.
- Local multi-core collection has completed successfully; GitHub runtime remains untested. Commits: origin/master1e6e72f; local ff30fa2 and later changes not yet pushed.
- User requests first hosted5000collection with latest best in both seats, conversion and candidate training, downloadable parent/candidate/logs, then local100candidate-parent evaluation. Bunny delivered collection/conversion/training extension of selfplay.yml; models/best.pt prepared from third-model best.pt. No hosted dispatch/training yet.
- Future desired github-train workflow adds1000candidate-parent evaluation and reports/downloads. This hosted evaluation is not in current implementation scope. No automatic candidate promotion.
- Disposable candidate/greedy NN copies are snapshots only; develop canonical nn_bot. Current candidate clone selects third-model/R2/T0.05, greedy copy third-model/R0/T0. Detailed artifacts/history in GENERATIONS.md and docs/next-session.md. Raw datasets/checkpoints remain local ignored artifacts except explicit models/ copies.
- Current visible Bunny session ses_f09b671eaffeJHQOKjugvgpYJR, notification route confirmed. Space Bunny Free implements, Luna reviews/summarises; no extra proof/fault-tolerance/test framework.

- T049 workflow extension delivered; Bunny reports YAML/shell/static checks passed. Primary preparing commit/push and first hosted5000dispatch, seed90003/workers4/models/best.pt. Hosted runtime remains unproven until job completion.
