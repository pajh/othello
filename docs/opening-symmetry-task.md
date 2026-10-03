# T074 — canonicalize existing prefix file only

Create scripts/canonicalize_opening_prefixes.py and docs/opening-symmetry-handoff.md only. No otheredits, Edax, generatorchanges, policyfiltering, futurefeatures or broadreads.

CLI --input PATH --output PATH. Read existingcomma-separatedcoordinatehistories (blankline=emptyhistory). Transformwholehistory consistently under identity,(r,c)->(7-r,7-c),(r,c)->(c,r),(r,c)->(7-c,7-r). Canonicalrepresentative=mintransformedtupleofrow-major0..63squareindices. Deduplicatecanonicalhistories; preservefirstencounterorder, write lowercasecomma-separatedcoordinates. Pass literal remains unchanged under transforms. Refuseexistingoutput; createparentdir; keepinputunchanged. Printcountsbylengthandtotal. Standardlibraryonly, simplefunctions.

Knownfullinput runs/opening-prefixes/prefixes.txt has9913rows,length0..6counts1,4,12,56,244,1396,8200. Expectedcanonicalcounts1,1,3,14,61,349,2050,total2479. This is not arbitraryeveryfourthrow or quarterfile slicing; actuallytransformeachcompletehistory. NoEdax or sourceinvestigation.

Allowedtinycheck: syntheticempty+4legalfirstmoves ->2canonicalrows; confirmfourtransforms/idempotence. Syntax/--help allowed. DoNOTexecute fullfile reduction: userruns --input runs/opening-prefixes/prefixes.txt --output runs/opening-prefixes/prefixes-canonical.txt. Shorthandoff with exactcommand/actualchecks thenstop. No projectmemoryedits/commits/push/jobs.
