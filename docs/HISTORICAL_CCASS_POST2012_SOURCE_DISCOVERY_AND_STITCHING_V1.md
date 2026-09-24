# HISTORICAL_CCASS_POST2012_SOURCE_DISCOVERY_AND_STITCHING_V1

## Source discovery

`webbsite_selective.sqlite` is present at two H: locations. Both copies are byte-identical (SHA-256 `a470fa2d0e8d9b1b610a19b5bdf7bfa460a5490e155ed7ac212c16c7ca19fc52`). The verified schema is `rows(table_name, issue_id, part_id, shares, row_date, raw_json)`, with 15,048 rows, 3 issue IDs, and dates 2007-06-26 through 2025-12-24.

For issue 2516 / stock 0388, actual rows exist in every year 2007–2025. For issue 3452 / stock 01211, actual rows exist in every year 2007–2025. For issue 26628 / stock 01810, actual rows exist from 2018–2025.

These are `dailylog` aggregate rows. `part_id` and `shares` are NULL; they are not participant-level holdings and are not promoted as participant evidence.

## Coverage classification

- 2007–2025: PARTIAL — verified aggregate selective coverage; participant detail unavailable.
- 2026: MISSING from this archive; current production data is a separate source and is not treated as historical archive coverage.
- Full 19-year participant-level coverage: UNVERIFIED.

## Post-2012 bounded stitching proof

For HKEX / issue 2516 / stock 0388, real rows were selected from 2014-01-02, 2017-01-03, 2020-01-02, and 2023-01-03. Each row was transformed through the provenance-preserving stitching model with source system, source record ID, source issue ID, canonical security ID, normalized code, point-in-time date, nullable participant/share fields, source reference, and ingestion timestamp.

RAW_ROWS=4
CANONICAL_ROWS=4
READBACK_ROWS=4
FIELD_MATCH_PASS=YES
DUPLICATE_COUNT=0
REPEAT_WRITE_ROWS=0
LINEAGE_PASS=YES
PARTICIPANT_DETAIL_AVAILABLE=NO

Because the discovered post-2012 source is aggregate-only, participant-level historical-to-current continuity is not certified.

## Final handoff

RESULT=PARTIAL_SOURCE_DISCOVERY_AND_AGGREGATE_STITCHING
SOURCE_COVERAGE_MATRIX_PASS=NO
EARLIEST_HOLDINGS_DATE=2007-06-26
LATEST_HOLDINGS_DATE=2025-12-24
POST_2012_HOLDINGS_SOURCE_FOUND=YES
YEARS_FULL=
YEARS_PARTIAL=2007,2008,2009,2010,2011,2012,2013,2014,2015,2016,2017,2018,2019,2020,2021,2022,2023,2024,2025
YEARS_SUMMARY_ONLY=
YEARS_MISSING=2026
YEARS_UNVERIFIED=2013-2025 participant-level detail
SOURCE_COUNT=2
ARCHIVE_COUNT=2
SCHEMA_COUNT=2
MULTI_SOURCE_STITCHING_PASS=YES_AGGREGATE_ONLY
OVERLAP_VALIDATION_PASS=NO_NOT_APPLICABLE_NO_SECOND_INDEPENDENT_POST2012_SOURCE
SOURCE_CONFLICT_COUNT=0
POST_2012_MULTI_ERA_PROOF_PASS=YES_AGGREGATE_ONLY
POST_2012_MULTI_ERA_SAMPLE_COUNT=4
POST_2012_MULTI_ERA_SAMPLE_RANGE=2014-01-02; 2017-01-03; 2020-01-02; 2023-01-03
HISTORICAL_CURRENT_BRIDGE_PASS=NO_PARTICIPANT_DETAIL_MISSING
HISTORICAL_LINEAGE_PASS=YES
HISTORICAL_IDEMPOTENT_PASS=YES
FULL_19Y_BACKFILL_READY=NO
OWNER_CHAT_CONTINUATION_REQUIRED=NO
OWNER_ACTION_REQUIRED=NO
REMAINING_BLOCKERS=No discovered post-2012 participant-level CCASS source; 2026 historical archive coverage is not present in the verified artifact.
NEXT_BOTTLENECK=Locate a post-2012 participant-level CCASS holdings export or archive and validate overlap against the aggregate dailylog source before any bulk import.
