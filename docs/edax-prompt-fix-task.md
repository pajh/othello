# T075a — remove artificial per-prompt quarter-second delay

Allowededits scripts/evaluate_edax_prefixes.py and docs/edax-evaluation-handoff.md only. Nootherchanges/runs/research.

Observedsource _QUIET=0.25 and read_until_prompt does select.wait0.25afterbufferendsb">". With2479rows/4workers hintpromptsalonecost~155seconds, navigationadds more. This defeats20–40secondtargetregardlessofsearchtime.

Remove _QUIET and thequiet-select delay. Treat receivedEdaxcommandprompt ascompletionimmediately. Matchactualprompt atendofbuffer (bare > afternewline or knownobservedboardoutput); handlechunkedreads/multiplebytes withoutblockingaftercompleteprompt. ExistingEdaxflushesatprompt. Preservecommandsequencing, bytebuffer/logging/errorhandling; no transportframework or otherrefactor. Finalsearchrow score cancontain > prefix so avoidmatching arbitrary interior > ascompletion. Onlyend-of-outputprompt.

Syntheticstubbyte-readercheck: splitpromptacrosschunks; completedpromptreturnswithout0.25select; finalresultplusprompt parses correctly. NoactualEdaxexecution. Syntaxcheck. Document correctionandchecks in existinghandoff. Stop.
