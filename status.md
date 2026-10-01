# Project status

Updated: 2026-10-01.

- Canonical pipeline: sequential/parallel rig, schema-v1 game logs, whole-game conversion, CPU outcome MLP/trainer with weights-only initialization. Bot NN-004-R2-T0.05: two random own moves then T0.05 weighted choice. Current selected model: checkpoints/third-model/run-selfplay-5000/best.pt.
- Generation003: first selfplay5000, parent first-model best.pt, seed90001, sequential914.067s. Second model bestepoch1; same-split validation0.203582 ->0.193218. Matches: candidate/random86/5/9, candidate/parent62/6/32.
- Generation004: next selfplay5000, parent second-model best.pt, seed90002,4workers249.131s,5000normal0forfeits. Third model bestepoch1; same-split validation0.199267 ->0.186284. Matches: greedy third/random97/2/1; R2/T0.05 third/second63/4/33. Both successive head-to-head batches yielded65%candidate score; no plateau established.
- Local multi-core collection has completed successfully; First GitHub collect/convert/train/upload completed successfully. Commits: origin/master1e6e72f; local ff30fa2 and later changes not yet pushed.
- User requests first hosted5000collection with latest best in both seats, conversion and candidate training, downloadable parent/candidate/logs, then local100candidate-parent evaluation. Bunny delivered collection/conversion/training extension of selfplay.yml; models/best.pt prepared from third-model best.pt. No hosted dispatch/training yet.
- Future desired github-train workflow adds1000candidate-parent evaluation and reports/downloads. This hosted evaluation is not in current implementation scope. No automatic candidate promotion.
- Disposable candidate/greedy NN copies are snapshots only; develop canonical nn_bot. Current candidate clone selects third-model/R2/T0.05, greedy copy third-model/R0/T0. Detailed artifacts/history in GENERATIONS.md and docs/next-session.md. Raw datasets/checkpoints remain local ignored artifacts except explicit models/ copies.
- Current visible Bunny session ses_f09b671eaffeJHQOKjugvgpYJR, notification route confirmed. Space Bunny Free implements, Luna reviews/summarises; no extra proof/fault-tolerance/test framework.

- T049 workflow extension delivered; Bunny reports YAML/shell/static checks passed. Primary preparing commit/push and first hosted5000dispatch, seed90003/workers4/models/best.pt. Hosted runtime remains unproven until job completion.

- Pushed669a1fd; hosted run36841281392 submitted and observed in_progress. Inputs5000/seed90003/workers4/models/best.pt. Results/downloads unknown/pending; https://github.com/pajh/othello/actions/runs/36841281392.

- User requested future C bot and generated compressed model header, in-memory decoder, Makefile and one-file CG combine/size checks. Staged plan docs/c-bot-plan.md prepared; no implementation or benchmark. Comprehensive200,000+position C/PyTorch parity check planned explicitly; platform contract/deployment settings pending.

- C target clarified: CodinGame multiplayer Othello; deployment greedy from first move. Actual starter protocol/platform limits still to obtain; plan updated.

- Hosted run36841281392 succeeded; downloaded runs/github-first/.5000normal0forfeits,collection161.608s; trainingbestepoch1validation0.198206vsparent0.205014,4epochs,total5.693s. Local100hostedcandidate-vs-exactparent prepared, unrun; no candidate promotion. FP32 C baseline and early FP16weight-storage comparison recorded in c-bot-plan.md.

- Hostedcandidate/exactparent local100 completed54/4/42 W/D/L (56%score),seed93001,alternatingR2/T0.05,zero forfeits. Prior candidate-parent batches65%,65%; possible smaller gain, not conclusive slowdown. Hosted pipeline and local artifact evaluation now exercised. No automatic promotion/new job.

- Greedy/random100 for hostedcandidate requested; disposable nn_eval_bot now selects downloaded candidate (VERSION002), R0/T0 unchanged. Match unrun.

- Hostedcandidate greedy/random100 completed100/0/0 W/D/L,seed93002,alternating colours,zero forfeits. NN-EVAL-002-R0-T0. Random-bot milestone achieved for this batch; C plan remains design-only.

- T054 user selected random-first C proof of concept: c/bot.c (CG loop/random score), Python per-game subprocess adapter, make bot, one initial smoke; user-run100 versus Python random follows. NN forward.h/decompress.h/generated model.h/combine deferred. Ordinary CG supplies complete board/legal moves; wrapper handles rig passes locally. Implementation being dispatched to verified Bunny session; no build/game/CG result yet.

- T054 delivered random c/bot.c, bots.c_random_bot and make bot. Bunny reports clean build and one normal smoke game (draw, zero forfeits), persistent child across31turns, child reaped afterward. Primary source inspection confirms CLI factory path reuses one process/game. Official referee confirms a1 top-left and row/column mapping; no code change. User100game match and real CG submission remain unrun. Smoke retained at runs/c-random-smoke/.

- User reports C bot seems alright but terminal move spam. Source shows per-move stderr logging plus startup messages. T055 dispatched: quiet normal C diagnostics, preserve errors/stdout/behaviour, C version002, build only. No new match result/counts inferred.

- T055 complete per Bunny handoff: C VERSION002 removes four routine stderr prints, preserves errors/stdout/game behaviour; make bot clean with warnings enabled. Wrapper unchanged C-RAND-001. No post-edit game run.

- T054 local user100game random comparison reported49Cwins/44Pythonwins, clean/no spam (remaining outcomes not explicitly supplied). User pasted c/bot.c into actual CodinGame Othello Wood2 runner; screenshot shows normal full-board result, PaulH14discs vs BOSS1 50discs,60actions and a boss pass. Real CG C build/input/output execution now observed successfully for this game. Random bot loss expected; no NN stage started.

- T056 user approved fixed blob plus Layer descriptors/pointers; setup allocates model-owned first input and per-layer outputs once, links buffers; forward copies input and loops dense descriptors. Current128/256/64/1 ReLU/ReLU/sigmoid hardcoded in standalone c/nn.h. No production teardown; test_nn.c alone frees owned allocations for sanitizer smoke. Bunny task being dispatched; no implementation/run yet. Next stage user requests real-model blob load and10,000random-input PyTorch comparison, deferred.

- T056 delivered c/nn.h agreed Model/Layer/setup/forward, c/test_nn.c and isolated make test-nn. Bunny reports256seeded-random forward calls, scores0.490070–0.498135, mean0.495070, no nonfinite/out-of-range values; clean ASan/UBSan/leak run exit0. Production setup allocates once/no teardown, test frees owned buffers. bot.c untouched. Real-model numerical agreement untested; T057 remains undispatched.

- T057a user requested Python checkpoint->raw FP32 blob plus text layout report only. Bunny export-only task dispatched: scripts/export_nn_blob.py, pure little-endian49537float/198148byte model.bin, blob-layout.txt, one export of hostedcandidate and size check. C load/numerical comparison deferred to separate task.

- T057a complete per Bunny handoff: scripts/export_nn_blob.py exported hostedcandidate into runs/c-model-export/model.bin (198148bytes/49537little-endianFP32elements) and blob-layout.txt with fixed six-tensor offsets. One export/size check only; no C loader or numerical agreement test yet.

- T057b user supersedes random-input parity corpus with real replay-derived boards. Luna generator task: scripts/generate_nn_test_csv.py, explicitly run10,000sampled rows from latest hosted validation.npz using hostedcandidate checkpoint matching blob. CSV128own/opponent inputs+PyTorch score, simple binary/non-overlap/CSV sanity checks. No C changes/comparison yet.

- T057b Luna delivered scripts/generate_nn_test_csv.py and ran10,000real hosted validation boards, seed12345, hostedcandidate checkpoint matching exported blob. Retained runs/c-forward-corpus/inputs-and-scores.csv and corpus-summary.txt. Independent sanity check passed10000rows/129columns, selected dataset inputs/order exact, binary/non-overlapping planes, finite0..1scores (0.000384106941–0.999888301). C comparison remains unimplemented/unrun.

- T057c user requests OpenCode C comparison rig using existing blob/10000real-board CSV. Bunny dispatched c/test_nn_compare.c plus isolated sanitizer Make target; tolerance absdiff<=1e-5+1e-5*abs(reference), report count/mean/max/worst row/failures. Build only; user-run numerical comparison next. No nn.h/bot changes.

- T057c complete per Bunny handoff: c/test_nn_compare.c reads exact raw FP32blob, setup once, parses CSV and compares with fixed1e-5absolute+1e-5relative tolerance. make test-nn-compare sanitizer build clean. Runtime/numerical agreement/sanitizer findings unknown until user run; no nn.h/bot edits.

- I008 observed first comparison run rejected x86_64 host before blob loading. Source bug: host_matches_blob_format compares1.0f bytes against big-endian3f800000 instead of little-endian0000803f. Narrow Bunny correction dispatched (plus sizeof(fp32)==4 guard), build only. Numerical agreement still unknown.

- I008 corrected per Bunny handoff:1.0f check now00/00/80/3f with early sizeof(fp32)==4 guard; clean rebuild. Corpus/runtime comparison remains unrun pending user rerun.

- T057 real-model C parity PASSED user rerun:10000read/compared, mean absolute error1.61441334e-8, max2.38418579e-7 (row1874 C0.543397963/ref0.543397725), zero tolerance/nonfinite/range failures; no sanitizer diagnostics shown. Retained runs/c-forward-check/forward-summary.txt. Export/blob layout and descriptor forward now exercised together on real boards. No bot integration/compression/quantization yet.

- User confirms CG maximum source length100000characters. Read-only sizing probe on current model: raw-DEFLATE FP32 payload184328bytes/Base64245772chars; rounded FP16 payload91799bytes/Base64122400chars/Base85114749chars, all before code/header overhead. Neither FP32 nor FP16 fits these encodings. No compression/quantization implementation or strength experiment dispatched; precision/encoding decision open.

- User agrees shared256FP32table plus byteindices for weights/biases, with Cexpansion into FP32array; wants compare against original real-model CSV. T058 Python KMeans quantization exporter dispatched, emits codebook/indices/reconstructedFP32blob; user existing Ctest can measure score drift without decoder changes first. Target75000model+25000code chars recorded; no adoption/playing-strength conclusion yet.

- T058 delivered scripts/quantize_nn_blob.py, one shared256FP32 KMeans codebook including biases, seed12345; quantized artifacts runs/c-model-quantized/. Table1024bytes+indices49537=50561packedbytes/Base6467416chars before overhead; reconstructed model.bin198148bytes. Weight MAE0.000450010535/max0.00786840916/MSE3.21645363e-7. Nearest stored FP32centers used (3fit-label discrepancies corrected). User10000board score comparison pending; original/model/CSV untouched; no Cdecoder/adoption.

- Generation007 user quantized-score comparison complete:10000rows, mean absolute drift0.000824199575,max0.00866732001,worstrow5577 C0.452201247/ref0.460868567,9780outside strictFP32tolerance,0nonfinite/range failures; RESULT FAIL under unchanged rounding gate. Retained runs/c-quantized-check/forward-summary.txt. Lossy drift measured, not arithmetic regression or playing-strength rejection. No tolerance/code/adoption change; move-selection/strength effects unknown.

- User prioritizes deployable quantized bot strength; hypothetical oversizedFP32 strength baseline not actionable now. Compression sizing of actual shared-codebook+indices:50561rawbytes/Base6467416chars; rawDEFLATE level9 ->48557bytes/Base6464744chars, saving2672sourcechars(~4%) before decoder/wrapper overhead. Primary recommendation: omit compression, retain Base64/table expansion/length+CRC32 checks; user decision pending. Startup cost not benchmarked, no compression implementation dispatched.

- User agrees no compression, authorizes Base64header plus Ccodebook expansion and checking against priorquantizedblob/results. T059a first boundedBunnytask dispatched: Pythonheadergenerator only, payloadcodebook+indices, lengths/CRC32 packed+expanded, generatedheaderunder75000chars; Pythonroundtripbytecheck. Cdecoder/reconstruction/parity separate after handoff.

- T059a delivered PythonBase64header: runs/c-model-embedded/model.h72959ASCIIchars,67416encodedchars; payload50561bytesCRC32dca2a0e3, expanded198148bytesCRC322bce1e0e. Actualheaderdecode+FP32expansion byteexactversusquantizedblob passed per Bunny. T059b separateCdecoder/checktask nowdispatched; no botintegration.

- T059b delivered model_decode.h/test_nn_embedded.c and isolatedMake target. Sanitizedreconstructioncheck byteidenticaltoquantizedreference, CRCpackeddca2a0e3/FP322bce1e0e, decoded198148bytes savedruns/c-embedded-check/model.bin, noASanUBSan/leaks reported. Initialone-paddingbytecount reversed, fixed beforepass. User10000score rerun pending; bot.c/nn.h untouched.

- T060 user agrees nonrecursive scrunch: mainbotlistsnn.h/model.h/model_decode.h in order; quotedincludesstrippedfrom pastedheaders, standardincludesretained. Bunnytask scripts/scrunch.py pluscommentstripping/charcount warning100000; no bot/header changes. Currentbotstillrandom; currentgeneratedsubmission will notyetembedNN. Focusedscratchincludecheck authorized.

- T060 scripts/scrunch.py delivered/nonrecursivequotedinclude expansion+commentstrip+charlimitwarning. Actualrandomsubmission3816chars/bytescompiledclean(one-turnprobe reported). Scratchall3headers81486chars,zeroquotedincludes,compiledwith-lm; notNNbotintegration. No source/header changes. O3inline pragma injection stillpending; researchedforumrecommendation, no march/AVXassumption adopted.

- T061 userauthorizesgreedyneuralCbotwiringnow. Bunnytaskbot.c/Makefileonly: list3headers, load/decode/setupstartup, retainCGboard/applycandidateflips/actorencoding/forward/highestscore; C-NN003, existingexecutablepathforwrapper. Buildgcc+oneuserauthorizedsmoke, no100matches. PythonwrapperIDunchangedpendingseparaterevision; scrunchpragma/package separate.

- T061 complete: C-NN003greedyembeddedmodelstartup/candidateflips/actorplanes/forward. Explicitgcc-O2buildclean; onesmoke normal0forfeits,44–20NNwin,60positions,childreaped. Retained runs/c-neural-smoke/run-9f8f704fca994448a3acbea1756915c9/. WrapperstillC-RAND001butlaunchesNN; identityfixseparate. T062 scrunchO3prefix+actualneuralpackagegcccompiletaskdispatched.

- T062 complete: actualgreedyquantizedNNsinglefile runs/c-submission/submission.c88256ASCIIchars/bytes,11744under100000; O3inlineprefix/zeroquotedincludes, exactGCC-O2-lmcompileclean. Earliermid-editSyntaxErrorcorrectedbeforegeneration. No postpackaginggame/numericalrerun; sourcealreadyneuralintegration-smoked. ReadyformanualCGtest, notyetobserved.

- T063 userclarifiescommentremoval: deletecomment-onlylineincludingnewline, preserveintentionalblanklines andallcodewhitespace/names. NarrowBunnyscrunchadjustment/regenerate/exactGCCcompile dispatched. No generalminification.

- T063 complete: comment-onlyline/newlineremoval preservesoriginalblanklines/codewhitespace/literals. Focusedcheckcaughtduplicatenewlinebug, correctedbeforefinalgeneration. Actualneural submission88000chars/bytes (12000belowlimit), prefix/noquotedincludes intact, exactGCCcompileclean. No newgames/numericalrun; readyformanualCGtest.

- I009 primaryreadactualT063file:88000chars/1388lines/321blanklines, first35linesblankafterpragma. Actualstripbugresetscommentflagafterblocknewlineanddoesnotmarksubsequentblocklines. Narrowfixdispatched; previousclaimblockinteriorremovalwasincorrect. Filewasnewbutbugremained.

- I009 fixed/actualfileprimarychecked:submission87775chars/bytes,1163lines/96blank; stdioincludeatline3,NNguardbyline8, blankcommentheadgone. Eachcommentbranchmarksperline; intentionalblanklines/literals/codepreserved. ExactGCCcompilecleanreported. ReadyformanualCGneuraltest, unknownuntiluserexecution.

- Userconfirms actualgreedyquantizedneuralCGsubmission nowplayingWood2league. Noresults/rankpromotion/timingreported. T064 Luna consolidating allcurrentcommands/scripts into docs/command-guide.md, coveringlocal/hostedtraining/evaluation/export/quantization/build/scrunch; codeunchanged.

- T064 complete: docs/command-guide.md consolidates local/hosted collection, conversion, continued training, evaluations, C export/quantization/embedding/tests/build/scrunch and helper inventory. Reviewed against current interfaces; latest hosted candidate distinguished from older repository models/best.pt. Documentation only; no jobs launched. User reports neural CG Wood 2 rank 78 and convincing IDE boss win; no promotion reported.

- User authorizes next hosted round: latest hosted candidate as parent; 5000 R2/T0.05 self-play games/workers4, eight-way augmentation of both splits after game split, continued weights/new Adam, stop at first validation non-improvement (patience1), then1000 matching-settings candidate-parent evaluation and downloadable logs/reports/checkpoints. Full commit/push and dispatch authorized; no automatic candidate promotion after results. T065 converter-only Bunny task first; T066 workflow/evaluation follows handoff.

- T065 delivered optional --symmetries: split first then independently expand each split eightfold, own/opponent planes and labels preserved, schema unchanged. Synthetic transform/label checks passed per handoff; initial axis bug corrected. No real augmented conversion/training yet. T066 workflow-only evaluation task dispatched next.

- T066 workflow delivered: symmetry conversion/patience1, disposable hosted candidate clone,1000 parent-candidate games with4workers/seed+100000, logs/reports/artifact. Review caught duplicate WORKERS YAML key; correction requested before push. Latest hosted candidate now copied to models/best.pt as explicitly selected next parent. T067 commit/push/dispatch remains pending.

- Duplicate WORKERS corrected; primary duplicate-key-rejecting YAML parse passed (12steps), git diff --check clean, models/best.pt byte-identical to selected hosted candidate (609112bytes). Commit/push and dispatch now proceeding.

- T067 complete: full implementation/model/docs commit b9aea93 pushed origin/master. Generation008 dispatched: https://github.com/pajh/othello/actions/runs/36887079634, observed in_progress,5000games/seed90004/workers4/models/best.pt. Expected eval1000games/seed190004. Runtime/results not yet known; retrieve artifact and review when complete.

- Generation008 completed successfully: GitHub36887079634, job8m49s; downloaded full artifact to runs/github-symmetry/. Collection5000normal/0forfeits,2374/2442/184 outcomes,seed90004/workers4. Original241974training/60448validation positions expanded8fold to1935792/483584, whole-game4000/1000split preserved per conversion report.
- Continued parent weights/newAdam/patience1: initial validationMSE0.196363, bestepoch2 MSE0.190112; epoch3 rose0.190593 and stopped; training41.319s. Actual trainedarchitecture unchanged128/256/64/1.
- Hosted evaluation1000normal/0forfeits: candidate633wins/37draws/330losses,65.15%score,seed190004,R2/T0.05bothseats/alternating/workers4. Strong evidence candidate beats this parent under tested settings; symmetry-specific causal effect not isolated. Candidate runs/github-symmetry/checkpoints/github-candidate/best.pt, exactparent runs/github-symmetry/runs/github-selfplay/parent.pt. No adoption or Cexport update performed.

- User authorizes promoting Generation008 candidate for another hosted5000game training/evaluation round and a newly quantized CGsubmission before travel. models/best.pt copied from runs/github-symmetry/checkpoints/github-candidate/best.pt; nextseed90005/eval190005/workers4/eight-way augmentation/patience1. Previous C artifacts copied to runs/c-generation007 before regeneration.

- T069 complete: Generation008 best epoch2 selected/copy to models/best.pt, commit b25322f pushed. Next hosted run36891605722 (https://github.com/pajh/othello/actions/runs/36891605722) observed in_progress,5000games/seed90005/workers4/symmetries/patience1/eval1000seed190005. Results pending.
- Regenerated Cpayload from runs/github-symmetry/checkpoints/github-candidate/best.pt: shared256codebook, weightMAE0.00090876695/max0.0161861777; payloadCRC02c7e88a/expandedCRCcc3ff2df, model.h72959chars, submission.c87775chars. ExactGCCcompileclean; embeddedreconstructionbyteexactPASS withASan/UBSan (detect_leaks=0). LeakSanitizer initially failed due sandbox ptrace; no leakcheckpassedclaim. One C-NNvsrandomgame seed96001 normal0forfeits/NNwin, runs/c-generation008-smoke/run-b2e203b8e93b435abca88e671a8d8cef. Quantizedstrengthnotmeasured. PreviousCassets preserved runs/c-generation007/. ReadyforuserCGpaste; actualCGnewmodelresultunobserved.

- Latest hosted run36891605722 success, downloaded runs/github-symmetry-second/.5000normal0forfeits,2456/2402/142 outcomes;302725positions, original242177train/60548val expanded1937416/484384. Continued weights/newAdam/patience1: bestepoch1 validation0.192371 vs loadedparent0.194623; epoch2 rose0.192742 and stopped,31.647s training.1000evalnormal0forfeits:577candidatewins/26draws/397losses,59%score,seed190005/R2T0.05/workers4/alternating. Job9m30s. Candidate runs/github-symmetry-second/checkpoints/github-candidate/best.pt; exactparent runs/github-symmetry-second/runs/github-selfplay/parent.pt. No newpromotion/export/jobs.
- Userreports priorGeneration008quantizedCGsubmission now17thWood2 versus78th earlier. Arenaevidence separatefromunquantizedhostedcandidate evaluation; no leaguepromotionreported.

- Userauthorizes next identical hostedround whileeating. Generation009candidate copied byteexact to models/best.pt; seed90006/workers4/eval190006. Push/dispatch proceeding; Csubmission unchanged, rebuild deferred until userreturns.
