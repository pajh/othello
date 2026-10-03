STATUS: CANCELLED2026-10-02; retaineddesigncontext only. Do notredispatch thiscombinedtask. Nextboundedtask docs/edax-query-task.md (notdispatched).

# Edax opening-book generator — bounded implementation task

Prepared2026-10-02. Authorized for OpenCode implementation; user runs the local check.

## Deliverable

One user-run standard-library Python generator scripts/generate_edax_book.py, plus concise docs/edax-book-generation-handoff.md. Read relevant engine interfaces, docs/opening-book-plan.md and docs/edax-setup-handoff.md; no broad repository onboarding. User selects OpenCode model/reasoning; submission must not override them. Implementation agent build.

## Allowed files

scripts/generate_edax_book.py and docs/edax-book-generation-handoff.md only. Scratch under work/edax-generator allowed. No bots, C files, engine, Edax binary/source, workflows, model/data files, project-memory edits, dependencies, commits or pushes.

## Coverage owned by our generator

Use rig.engine initial_board/legal_moves/apply_move and row-major square0..63. Build separate policies from initial board for our Black and our White. History includes both players; lengths count total actual placements, not own moves.

Defaults broad horizon6, final horizon8, Edax level14, workers1. Parameters --branch-plies, --total-plies, --level, --workers (1or4), --output-dir. Horizons satisfy0<=branch<=total; total8 default. No general plugin/framework.

At a node with n moves already played and n<total:
- If actor is our policy colour, obtain Edax's best legal move, record history->move, and recurse only on that move.
- If actor is opponent and n<branch, recurse over every legal opponent move.
- If actor is opponent and n>=branch, obtain Edax's best legal move and recurse only on it.
- Stop at n==total. Broad expansion therefore covers both policies' replies through move6; remaining moves7and8 follow one best-vs-best continuation at each endpoint.
- Early pass handling need not invent a0..63move. If encountered in these short horizons, explicitly stop with explanatory error rather than fabricate prefix parity. No general pass-book format.

Canonicalize the complete history using exactly identity,180degree rotation,main-diagonal reflection,anti-diagonal reflection (these preserve initial colours). Use one transformation consistently; transform stored reply with it. Deterministic transform order resolves symmetry ties. Canonicalization/dedup must not combine Black/White policy restrictions incorrectly. At each prefix length both policies' recorded entries have the actor implied by parity. One reply per canonical history; detect conflicting replies as an error, do not arbitrarily overwrite. Choose lowest square among equivalent equal-score answers only if engine interface exposes ties; otherwise deterministic Edax result is sufficient.

Edax chooses moves; our generator enumerates branches. Do NOT ask Edax's native book expansion to determine coverage. Memoize analysed canonical histories within one invocation to avoid repeated analyses; retain chosen move and raw returned analysis. Record actual Edax level/depth/selectivity output (38is selective, not exhaustive38ply). Position at each prefix is replayed from initial board; coordinate mapping must agree with rig. Actual Edax startup book causes warm search effects: use existing tools/edax/data/book.dat as read-only common startup book, book usageoff, disable auto-store; prevent concurrent writes (confirm source that loading unchanged book doesn't set need_saving). No expensive bookcreation per query. If missing startupbook, document preparation requirement rather than silently launch expensive creation.

## Edax interface

Pinned executable tools/edax/lEdax-x86-64 and tools/edax/data/eval.dat. Each active engine has -n-tasks1. Source-inspect interactive mode/book settings and prompt completion; queued quit can interrupt search, so do not assume subprocess.communicate with commands plus immediatequit is valid. Keep protocol ordinary/minimal. Disable automatic game play and pondering. Validate returned move is legal for queried position before recording it. Wrong/partial result must fail visibly.

Support1or4independent engine workers, at most4simultaneous one-thread searches. Standard-library concurrency only. Keep scheduling bounded/simple, avoid analysing our unused alternatives. Report progress as completed query count, elapsed time, current prefix length, active workers; ETA only when remaining count is actually known. Do not claim fixed total upfront when policy choices determine tree. Capture per-query elapsedwalltime and startup overhead distinctly where practical; state cache/process reuse policy in report.

## Retained outputs

Use output directory under runs/ selected by user; raw per-query JSONL retains canonical history, chosen move, actual output/depth/selectivity, time, level and executable provenance. Final book has arrays grouped by history length; use64printableASCIIcharacters (choose alphabet with no C escape requirements), onecharacter per square, each fixed-width entry history+reply. Write book-data.json with alphabet, counts, concatenated entries per length and settings; this is data for later C integration, NOT a Cbot/header implementation. Report exact move payload character count and compare8000budget; never silently truncate/prune. Final complete summary book-summary.txt follows report atomic temporary publication convention. Save outputs incrementally; no elaborate resume/recovery framework. Mark partial generation honestly if interrupted; do not publish partial as complete.

## Checks and stopping point

No Edax analysis, full generation, benchmarks, matches or hosted runs by implementer. Allowed: Python syntax/--help and small deterministic synthetic checks of four transforms, encode/decode and traversal using a stubbestmove callback. No exhaustive test suite. User-run actual initial invocation documented in handoff with --branch-plies6 --total-plies8 --level14 --workers1 --output-dir runs/edax-book; user can choose4workers later. Include observed implementation limitations and exact checks actually performed. Finish handoff and stop.

## Exclusions

No C integration, changes to Python R2/T0.05, training/model decisions, competition deployment, GitHub workflow or job, Edax recompilation, external tournament opening import, dependency installation, or automatic strength claims. No artificial timing repetitions. No performance estimate without user-run evidence.

## User execution progression

User first runs6broad/8total at level14 locally on one thread, targeting roughly one minute (unmeasured; no guarantee). Review output/process/coverage/size before separate hostedworkflow preparation and level38execution. Do not launch either run automatically. Edax levels14and38are selective analysis settings; do not label them exhaustiveplydepths.
