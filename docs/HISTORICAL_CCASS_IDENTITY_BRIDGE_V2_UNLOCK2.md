# HISTORICAL_CCASS_IDENTITY_BRIDGE_V2_UNLOCK2

## Source evidence inventory

- Webb CCASS issue map: `issues in CCASS holdings.csv`, `issueID=3`, `NEW WORLD DEVELOPMENT COMPANY LIMITED`, line 2509.
- Webb ASP source defines the authoritative relationship as `stocklistings(issueID, stockCode, firstTradeDate, deListDate)` and uses `stockCodeThen(issueID, atDate)` for point-in-time code lookup (`ccass/bigchangespart.asp`, `ccass/chistory.asp`).
- The accessible issue CSV contains no `stockCode`, `stocklistings`, canonical security ID, or validity dates for issue 3. External HKEX/HKEXnews evidence supplies the cross-source binding: the 2008 Annual Report identifies New World Development as stock code 00017, and the 2011/2012 Interim Report preserves the same listed identity.

## External evidence references

- HKEXnews 2008 Annual Report: https://www.hkexnews.hk/listedco/listconews/SEHK/2009/0423/LTN20090423560.pdf
- HKEXnews Interim Report 2011/2012: https://www.hkexnews.hk/listedco/listconews/SEHK/2012/0316/LTN20120316584.pdf
- HKEX DI notice identifying New World Development Co. Ltd., stock code 00017: https://di.hkex.com.hk/di/NSForm2.aspx?cid=0&cn=1&corpn=New+World+Development+Co.+Ltd.&ed=22%2F08%2F2024&fn=CS20240216E00386&lang=EN

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
MULTI_ERA_PROOF_PASS=YES
MULTI_ERA_SAMPLE_COUNT=4
MULTI_ERA_SAMPLE_RANGE=2007-07-04; 2008-01-15; 2009-01-02; 2012-01-03
CROSS_ERA_CONTINUITY_PASS=YES
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
PASS_FLAGS_DB_DERIVED=YES
FULL_19Y_BACKFILL_READY=NO
OWNER_CHAT_CONTINUATION_REQUIRED=NO
OWNER_ACTION_REQUIRED=NO
COMPLETED_TRACKS=source inventory; durable mapping schema; unresolved-safety; bounded 2007 canonical/readback proof; versioned run metadata
PARTIAL_TRACKS=full 19-year backfill readiness
BLOCKED_TRACKS=full 19-year readiness
MAPPING_STATUS=DATE_BOUNDED
MAPPING_EVIDENCE_COUNT=4
HISTORICAL_DATE_VALIDITY_PASS=YES for 2007-2012 evidence range
CANONICAL_SECURITY_ID_STABLE=YES
SOURCE_REFERENCE_TRACEABLE=YES
RAW_ROWS=4
CANONICAL_ROWS=4
READBACK_ROWS=4
FIELD_MATCH_PASS=YES
DUPLICATE_COUNT=0
LINEAGE_PASS=YES
REMAINING_BLOCKERS=Archive evidence currently proves four eras through 2012; no 2017, 2022, or 2026 holdings rows are present in this archived CCASS payload, so full 19-year readiness remains NO.
NEXT_BOTTLENECK=Obtain later-era CCASS holdings source coverage (2017 onward) before any 19-year backfill.


