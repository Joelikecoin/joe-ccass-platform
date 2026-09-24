# Historical CCASS Identity Bridge and Multi-Era Proof V1

## Evidence boundary

The Webb CCASS issue map records `issueID=3` as `NEW WORLD DEVELOPMENT COMPANY LIMITED` (`issues in CCASS holdings.csv`, line 2509). The available issue map contains no HK stock code, effective code interval, canonical security identifier, or source reference that binds issue 3 to a code. No code was inferred from the company name.

The bounded historical raw proof remains source-backed for `issue:3`, 2007-07-04 through 2007-07-11: 3 raw rows, 3 canonical rows, 3 readback rows, field match PASS, and DB-derived lineage PASS.

## Durable model

`DoctorLocalStore` now creates an append-only `identity_mappings` table with:
`source_system`, `source_issue_id`, `canonical_security_id`, `hk_stock_code`, `security_name`, `valid_from`, `valid_to`, `mapping_status`, `mapping_confidence`, and `source_reference`.

Allowed statuses are `EXACT`, `DATE_BOUNDED`, `AMBIGUOUS`, and `UNRESOLVED`; the natural key is idempotent even when date bounds are NULL.

## Final handoff

RESULT=BLOCKED_IDENTITY_EVIDENCE
ISSUE_IDENTITY_MAPPING_PASS=NO
ISSUE_3_CANONICAL_SECURITY=UNRESOLVED
ISSUE_3_HK_CODE=UNRESOLVED
CANONICAL_SECURITY_IDENTITY_PASS=NO
POINT_IN_TIME_NAME_CODE_PASS=NO
AMBIGUOUS_MAPPING_SAFETY_PASS=YES
MULTI_ERA_PROOF_PASS=NO
MULTI_ERA_SAMPLE_COUNT=1
MULTI_ERA_SAMPLE_RANGE=2007-07-04..2007-07-11 only
CROSS_ERA_CONTINUITY_PASS=NO
HISTORICAL_CANONICAL_CHAIN_PASS=YES_BOUNDED_LOCAL
HISTORICAL_LINEAGE_PASS=YES_BOUNDED_LOCAL
HISTORICAL_IDEMPOTENT_PASS=YES_BOUNDED_LOCAL
FULL_REPOSITORY_TEST_COUNT=615
FULL_REPOSITORY_TEST_PASS_COUNT=607
FULL_REPOSITORY_TEST_FAIL_COUNT=8
REGRESSION_FAILURE_COUNT=0
PRE_EXISTING_FAILURE_COUNT=8
FULL_19Y_BACKFILL_READY=NO
OWNER_CHAT_CONTINUATION_REQUIRED=NO
OWNER_ACTION_REQUIRED=YES
REMAINING_BLOCKERS=Authoritative Enigma/Webb evidence binding issue 3 to a canonical security and point-in-time HK code is not present in the accessible issue map; multi-era samples cannot be certified without that binding.
NEXT_BOTTLENECK=Obtain or expose a source-backed Enigma security/listing history relation for issue 3, then run four or more real era samples and field-match/readback checks.

