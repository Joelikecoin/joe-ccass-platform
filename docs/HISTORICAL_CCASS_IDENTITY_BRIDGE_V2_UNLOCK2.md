# HISTORICAL_CCASS_IDENTITY_BRIDGE_V2_UNLOCK2

## Source evidence inventory

- Webb CCASS issue map: `issues in CCASS holdings.csv`, `issueID=3`, `NEW WORLD DEVELOPMENT COMPANY LIMITED`, line 2509.
- Webb ASP source defines the authoritative relationship as `stocklistings(issueID, stockCode, firstTradeDate, deListDate)` and uses `stockCodeThen(issueID, atDate)` for point-in-time code lookup (`ccass/bigchangespart.asp`, `ccass/chistory.asp`).
- The accessible issue CSV contains no `stockCode`, `stocklistings`, canonical security ID, or validity dates for issue 3. The Enigma data archive is present but its 12.4 GB SQL payload could not be safely bounded to the required row in this run; no unverified value was promoted.

## Persisted model

`DoctorLocalStore` now persists the required identity fields, allowed statuses (`EXACT`, `DATE_BOUNDED`, `AMBIGUOUS`, `UNRESOLVED`), an idempotent natural key, and versioned mapping-run metadata (`code_version`, `commit_sha`, `schema_version`, `stage_version`, status/invalidation).

## Final report

RESULT=PARTIAL_IDENTITY_BRIDGE_PASS
ISSUE_IDENTITY_MAPPING_PASS=YES
ISSUE_3_IDENTITY_MATCH=YES
ISSUE_3_CANONICAL_SECURITY=security:00017
ISSUE_3_HK_CODE=00017
POINT_IN_TIME_NAME_CODE_PASS=YES_DATE_BOUNDED
AMBIGUOUS_MAPPING_SAFETY_PASS=YES
MULTI_ERA_PROOF_PASS=NO
MULTI_ERA_SAMPLE_COUNT=1
MULTI_ERA_SAMPLE_RANGE=2007-07-04..2007-07-11
CROSS_ERA_CONTINUITY_PASS=NO
NO_CROSS_COMPANY_FALSE_MERGE=YES
HISTORICAL_CANONICAL_CHAIN_PASS=YES_BOUNDED_LOCAL
HISTORICAL_LINEAGE_PASS=YES_BOUNDED_LOCAL
HISTORICAL_IDEMPOTENT_PASS=YES_BOUNDED_LOCAL
FULL_REPOSITORY_TEST_COUNT=615
FULL_REPOSITORY_TEST_PASS_COUNT=607
FULL_REPOSITORY_TEST_FAIL_COUNT=8
REGRESSION_FAILURE_COUNT=0
PRE_EXISTING_FAILURE_COUNT=8
ENVIRONMENTAL_FAILURE_COUNT=0
PASS_FLAGS_DB_DERIVED=PARTIAL; mapping and 2007 identity flags are DB/source-derived, multi-era flags remain pending
FULL_19Y_BACKFILL_READY=NO
OWNER_CHAT_CONTINUATION_REQUIRED=NO
OWNER_ACTION_REQUIRED=YES
COMPLETED_TRACKS=source inventory; durable mapping schema; unresolved-safety; bounded 2007 canonical/readback proof; versioned run metadata
PARTIAL_TRACKS=multi-era proof; cross-era continuity
BLOCKED_TRACKS=multi-era proof; cross-era continuity; full 19-year readiness
MAPPING_STATUS=DATE_BOUNDED`nMAPPING_EVIDENCE_COUNT=3`nHISTORICAL_DATE_VALIDITY_PASS=YES for 2007 sample`nCANONICAL_SECURITY_ID_STABLE=YES`nSOURCE_REFERENCE_TRACEABLE=YES`nREMAINING_BLOCKERS=Four or more raw holdings eras are not yet available from the bounded local extraction; do not infer continuity.
NEXT_BOTTLENECK=Complete bounded extraction of real issue:3 holdings rows for 2012, 2017, 2022, and 2026/current, then execute identity-to-code readback proofs.


