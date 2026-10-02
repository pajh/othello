# C opening book — agreed approach and open generation choices

Updated 2026-10-02.

## Agreed

- C deployment only; Python training/evaluation retain NN R2/T0.05.
- Prefix history includes both players. Each canonical prefix has one prescribed next move; no runtime move choice within the book.
- Group entries by number of moves already played. Square indices0..63; initially one source-string character per move, exact alphabet to choose.
- Use four spatial transformations preserving the initial coloured board. Transform the full history consistently and inverse-transform the prescribed reply.
- Match history, not board positions. Supplied boards allow recovery of the opponent placement and NN fallback. No continuation means off book.
- Current submission87775ASCIIcharacters leaves12225characters for data and integration.

## Edax generation proposal — not yet implemented or run

Official engine: https://github.com/abulmo/edax-reversi
Official command reference: https://github.com/abulmo/edax-reversi/blob/master/src/edax.c

Edax requires a suitable executable and evaluation weights data/eval.dat. It provides book new/load/save/export and expansion commands, and play/hint/go for position analysis. Its native book is position-based, so it needs offline extraction into our prefix format; it is not a drop-in C payload.

A bounded custom generator could use Edax to prescribe one reply at each covered prefix. Coverage must include opponent alternatives, not merely one best-versus-best line. Build Black and White policies separately offline, then combine the needed entries; a reply generated for one side does not restrict the opponent during generation for the other side. Share equivalent prefixes using the agreed four transformations, with deterministic tie resolution.

Still to choose: book horizon in total plies, Edax analysis level/time, which opponent alternatives to cover, and source-character budget. Horizon and Edax search depth are separate quantities. No duration estimate without a small user-selected timing run. Retain raw analysis and extracted lines outside work/.

No Edax installation/download, generation run, integration or OpenCode task has started.

## Deferred idea

Python bots might later sample randomly from a3–4move opening book. This is an idea only, not a change to current exploration.

## Mini experiment selected — 2026-10-02

User selected fixed four-total-ply opening coverage (two moves each), compare Edax analysis at6/8/10additionalplies from each analysed position; collect elapsed/positions/progress/encodedsize to estimate depth within about3hoursGitHubcompute. Generator not yet implemented or run. Luna setup complete tools/edax; one user-run position check remains next.

## User single-thread initial-position timings — 2026-10-02

User increased Edax levels manually (no helper dispatched). Level34 startup New book search:34@73%,13.692s,265652518nodes; subsequent hint0.044s/231511nodes after same-process startup search. Explicit book-file tools/edax/data/book.dat fixed quit save error. Later fresh process loaded saved book without startup search: level36 hint36@73%,23.701s,470920021nodes; next fresh-process level38 hint38@73%,41.851s,820332319nodes. Both score-02 and PVd3 C5 f6 F5 e6 E3 d6 F7 g6, normal quit. Level38 meets user30–60second single-thread target on initial board. These are selective Edax levels, not exhaustive depths; other book positions and GitHub hardware unmeasured. Level36→38 elapsed ratio1.766. No openingbookgenerator or batch analysis run. Original6/8/10proposal superseded for immediate timing by these manual higher-level probes.

## Selected generation coverage — 2026-10-02

Broad horizon6totalmoves, final horizon8totalmoves, initialEdaxlevel38. SeparateBlack/Whitepolicies: ownturnoneprescribedmove; opponentturnalllegalreplies beforebroadhorizon, oneEdaxbestreplyafterward. Canonicalhistory/replyunderfourcolour-preservingtransforms. Ourgeneratorcontrolscoverage;Edaxquerieschoosemoves. Taskprepared docs/edax-book-generation-task.md, notdispatched/nojob. Earlierfourmovecoverageproposal superseded by thisuserselection.

## Userselected decomposition — 2026-10-02

1. Enumeratealllegalhistories0..PARAMdepthinclusive, savecomma-separatedmoves only; noEdax/symmetry/pruning. Task docs/opening-prefix-task.md.
2. Separatefuturetask: queryEdax and appendonebestreply to relevantprefixes. Own-policypruningmustthenremovehistoriesinconsistentwithourearlierprescribedmoves; retainallopponentbranches in broadsection. Explicitstartupbookpath and wait-for-search-before-quit guidance required; nohistoricalstartupresearch.
3. Separatefuturetask: extendlongestretainedpaths to finalhorizon using successiveEdaxcalls withno furtherbranching.

Generatedrowspreservehistories, boardsreconstructedofflineusingrig.engine. Adepth6enumeration includeslength6endpoints; broadreplies throughmove6 are obtained fromlength0..5histories. Laterstagepolicyfilter/symmetryencodingremainseparatelyscoped.

- 2026-10-02 usercompleteddepth6enumeration: lengths0..6=1,4,12,56,244,1396,8200,total9913. Retainedinput runs/opening-prefixes/prefixes.txt. Useragreesgenerateonce; Edaxevaluatorreadsthisfilewithoutregenerationormutation. Evaluatinglength0..5 broadreplyhistories gives1713rawrowsbeforelaterfour-symmetry/ownpolicyfiltering;8200length6endpoints retainedforlaterstage. NoEdaxbatchrun.

- 2026-10-02 userranT074fullreduction: canonicalcounts0..6=1,1,3,14,61,349,2050,total2479matchprediction. Retained runs/opening-prefixes/prefixes-canonical.txt readyasread-onlyEdaxinput; original9913prefixfilepreserved. Length0..5=429replycandidates, length6=2050endpoints; own-policyfilteringstillpending. NoEdaxbatchrun.

## Evaluationstage selected

Evaluateentire2479canonicalinputunchanged, includinglength6->move7replies; culllaterseparately. Retainallanalysedtoreusewithdifferentcullingrules. Cores4independentpersistent1-threadprocesses, contiguousinputchunks, longest-common-prefixundo/replay to retainsearchtables, stitchresultsbyoriginalindex. Locallevel10first;level38GitHubafterreview,separateworkflow. Task docs/edax-evaluation-task.md.

- UsercompletedT075localfullfileevaluation:2479/2479 in30.0s,cores4/Edaxlevel10; target20–40smet. Output runs/edax-evaluation/evaluated-prefixes.txt and results.jsonl/4workerlogs retained. Luna read-onlysavedoutputcheck dispatched; nolevel38 orhostedEdaxjobyet. Runtime doesnotmeasurestrength/deepsearchcost.
