# T073b — enumerate move prefixes only

One deliverable: scripts/generate_opening_prefixes.py and concise docs/opening-prefix-handoff.md. Userrunsit. No Edaxcalls/sourceinspection, chosenmoves, branchpruning, symmetries, extension, concurrency, Cchanges or otherfeatures.

Interface: --depth N --output PATH. Enumerate EVERY legal movehistory from initial board at lengths0throughNinclusive. DFS ascending rig.engine.legal_moves order. Use rig.engine.initial_board/apply_move; do not duplicate rules. Everyprefix writtenonce, including shorterones. Rowformat plaintext comma-separated lowercasecoordinates (e.g.f5,d6,c3); emptyinitialprefix is oneblankline. No boards/scores/metadata in rows. Depth is numberofrecordedturnactions; if forcedpass encountered write literalpass, switchplayer, and countthatturn; terminalnodes do not extend. For initial smallopeningdepths no pass expected. Validate nonnegativeintegerdepth; no generalframework.

Stream rows to output; print concise countbylength and total on completion. Output is userchosen retainedpathunder runs/, not work/. Existingoutput should be refused (no accidentalrawdataoverwrite). No enormouslog output.

Allowedfiles scripts/generate_opening_prefixes.py and docs/opening-prefix-handoff.md only; scratch work/opening-prefix allowed. Read only relevant rig.engineinterfaces and this task. No broadonboarding/repositoryhistory; no Edax or unrelatedsources/dependencies. No status/TODO/GENERATIONSedits, jobs, commits/push.

Checks: syntax/--help plus tinydepth2 enumeration allowed, because this is smallnon-gamehelpercheck, notanalysis/benchmark/training. Confirm counts1empty+4firstmoves+12twomoves=17rows, legalreplay and lowercasecoordinateformat. Save tinycheck only in work/opening-prefix. No full requesteddepthrun. Usercommand documented with --depth6 --output runs/opening-prefixes/prefixes.txt (create parentdirectory in helper). State inclusive semantics; laterbookreplystage useshistorieslength<6 for broadreplycoverage throughmove6. Depth6 historiesare endpoints for laterextension. No speculativeextras. Finishshorthandoff andstop.
