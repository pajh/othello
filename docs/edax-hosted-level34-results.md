# Edax level-34 opening data review

The hosted run completed all 2,479 canonical prefixes in 7,233.6 seconds (2 h 00 m 33.6 s) using four one-thread workers. Every result recorded Edax level 34 and selectivity 73%; these are selective-search settings, not a full-width guarantee. The retained results contain scores, nodes, and elapsed search time, but no explicit bound flags. The combined per-position search-time field sums to 27,478.5 seconds; this is worker search time, not wall time.

Replay verification used `src/rig/engine.py` on each history from the initial board. The saved analysis count and output-line count both equal 2,479. Result indices and serialized `history=reply` lines match the original input order exactly; all 2,479 replies are legal. No pass occurs in these prefixes. The input prefix counts are:

| Moves in prefix | Analyses |
|---:|---:|
| 0 | 1 |
| 1 | 1 |
| 2 | 3 |
| 3 | 14 |
| 4 | 61 |
| 5 | 349 |
| 6 | 2,050 |

The broad six-move policy uses histories of lengths 0–5: those 429 analyses prescribe replies that reach length 1–6, while opponent branches are retained as offline provenance and for the later own-policy filter. Only own-turn histories need entries in a deployed side-specific lookup. The 2,050 analyses at length 6 prescribe Black replies that reach length 7; they are the first extension ply beyond that broad horizon. The data has no length-7 histories, so it supplies no White reply at ply 8. The earlier depth-6 enumeration contained length-6 endpoints; the hosted analysis has now filled in their Black length-6-to-7 replies.

For a read-only size estimate, I filtered histories by each side’s earlier prescribed moves. At each earlier turn for that side, the recorded move had to equal the policy reply at that parent history, after aligning both through the same one of the four initial-board-preserving transforms. All opponent moves remain eligible. The input is already symmetry-canonical, so the compact estimate stores each eligible canonical key and its reply once; an explicit four-orientation expansion is shown separately. With one character per square and no delimiters, headers, indexes, or decoder:

| Own-policy filter | Entries by prefix length 0–6 | All eligible rows (both turns) | All-row compact chars | Own-turn lookup entries | Own-turn compact chars | Own-turn chars if four orientations stored explicitly |
|---|---|---:|---:|---:|---:|---:|
| Black | 1, 1, 3, 3, 10, 10, 49 | 77 | 477 | 63 (lengths 0/2/4/6) | 403 | 1,612 |
| White | 1, 1, 1, 5, 5, 26, 26 | 65 | 389 | 32 (lengths 1/3/5) | 178 | 712 |

The all-eligible counts include opponent-turn rows used as offline provenance and policy-filter aids; those rows are not deployable entries for that side. Own-turn counts are the deployed lookup candidates under the stated filtering rule. Counts are measured over saved rows; character sizes are hypothetical payload arithmetic, not an implemented exporter or runtime measurement. Four-transform lookup can keep one canonical payload; explicit expansion multiplies its own-turn character subtotal by four. The agreed 10,000-character budget appears ample for these filtered level-34 entries, although integration overhead and exact encoding remain unmeasured. For comparison, the complete evaluated-prefix text file is 50,452 bytes including line breaks (47,973 content characters); it is not a compact C payload. The compact unfiltered one-character key-plus-reply subtotal would be 16,817 characters, also before any encoding overhead.

No result establishes optimal or perfect play, or a playing-strength gain. This review measures data coverage, replay legality, and a simple payload estimate only.

Raw artifacts: `runs/edax-hosted-level34/edax-book-37027471923-1/` (`evaluated-prefixes.txt`, `.results.jsonl`, runtime summary, worker logs). Canonical input: `runs/opening-prefixes/prefixes-canonical.txt`.
