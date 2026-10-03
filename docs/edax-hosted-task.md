# T077 — manual GitHub Edax evaluation workflow only

Create .github/workflows/edax-book.yml and docs/edax-hosted-handoff.md only. Do notedit evaluator/otherworkflows/assets/projectrecords. Nojobs/commits/push/Edaxqueries/dependencieslocally.

Preparedtrackedassets data/opening-book/prefixes-canonical.txt (2479rows,firstrowblank) and startup-book.dat (valid84byteEdaxbook) copiedbyprimary; noinputregeneration/canonicalization. Useexisting scripts/evaluate_edax_prefixes.py unchanged.

Workflow manual workflow_dispatchonly. Inputs depth(default38),cores(default4). ubuntu24.04,Python3.14. Installproject --no-deps -e . (engine only,stdlibrary; donotinstalltorch/numpy/sklearn). Downloadpinnedofficial https://github.com/abulmo/edax-reversi/releases/download/v4.6/edax-4.6-linux-x86.tar.gz into tools/edax; SHA2567ca52cb0ccf591ad9690e7d21861d4a6f04b900c686346db98ea26dd30cd966a. Inspectarchivepathbyexistingsetuphandoff/standardtarlist(notdownload/runlocallyifunneeded). Copytrackedstartup-book.dat totools/edax/data/book.dat afterextract; nohighlevelstartupcreation. Baseline lEdax-x86-64/eval.dat frompackage. NoCPU-specificvariant.

Run python -u scripts/evaluate_edax_prefixes.py --input data/opening-book/prefixes-canonical.txt --output runs/edax-evaluation/evaluated-prefixes.txt --cores "$CORES" --depth "$DEPTH" --eta-check-after600 --eta-check-interval150 --max-estimated-hours5 --max-hours5 (properseparatespacesinactualcommand). tee runs/edax-evaluation/evaluation.log withpipefail; streamprogress inActionslog. Jobtimeout330minutes leavesuploadmarginbeyond5hours. Readonlycontentspermissions. Alwaysupload runs/edax-evaluation/ includingpartialrecords/rawlogs/runtime-summary.txt onstop/error, uniquenameedax-book-${run_id}-${run_attempt}. Preserve evaluatornonzero/failureonplannedstop; donotclaimcomplete. Alwaysjobsummaryshowrequestedlevel/cores,runlink,artifactname andruntime-summaryifexists; nochatnotification/schedule.

StaticYAML/shell/interfacechecks only, nojobdispatch. Handoffrecordsactualchecks,prepared/unrunstatus,exact ghworkflowdispatch/downloadcommands (user/designwilllaunchseparately). Onetimeworkflowdeliverable; noframework/refactor. Stop.
