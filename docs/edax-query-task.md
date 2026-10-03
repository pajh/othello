STATUS: DEFERRED; userselectedenumerationfirst, docs/opening-prefix-task.md.

# T073a — one Edax query only

Implement scripts/edax_query.py and docs/edax-query-handoff.md only. No generator, concurrency, symmetry, timing study or Cbot changes.

CLI: --moves (coordinate sequence, default empty), --level (default14). Start existing tools/edax/lEdax-x86-64 with existing eval.dat/book.dat, bookusageoff,n-tasks1, automaticplayoff/ponderingoff. Send the requested moves, request hint1, wait for completed result, then quit. Output the first recommended move, actual depth/selectivity/score and elapsedwalltime; preserve raw output in userchosen --output file (optional). Standardlibrary only. A nonempty prefix must really be applied; returned move must be legal according to rig.engine. Do not queue quit before search completes.

Established facts: user has successfully run the executable; explicit bookpath works; existing tools/edax/data/book.dat loads without startupsearch and exitscleanly. Treat that file as setup precondition; fail clearly if absent. No nativebookcreation, repair or concurrentworkers.

Do not investigate historicalstartupbehaviour or read Edax Csource. Use its command help/knownprotocol. If protocol information needed to implement this interface remains missing, report the specific missing fact rather than widening research. Keep reads to relevant engineinterfaces and existing setuphandoff. No broadrepositoryonboarding.

Syntax/--help allowed; no Edaxexecution, analysis, bookgeneration, benchmark, training or hostedrun. Document exact user-run command at level14, with a nonempty legalprefix example. Short handoff lists implementedinterface and actualchecks; stop. No dependencies/systeminstall or projectrecordedits.
