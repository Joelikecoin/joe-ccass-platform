# CCASS Boundary and Portable Workstate Handoff

WORK_PACKAGE=END_OF_DAY_CCASS_HANDOFF_20260917
DOCUMENTATION_ONLY=true

## Verified repository

EXPECTED_HEAD=29c257835ea3f8950ecd2c5f1bb3a3f905333940

## WEBBSITE archive

SOURCE_ARCHIVE=H:\NamFung Drive\投資 - 享受與豐盛\AI Projects\joe-ccass-platform\docs_reference_evidence\David_Webb_CCASS_Research_Pack\Webb-site repository Old Data\CCASS schema\ccass251227.7z
ARCHIVE_SIZE=1,501,056,439 bytes
SQL_MEMBER=ccassData-2025-12-27- 600.sql
SQL_MEMBER_LOGICAL_SIZE=17,059,800,013 bytes
LOCAL_EXTRACTION=D:\WEBBSITE_CCASS_EXTRACT\ccassData-2025-12-27- 600.sql
EXTRACTION_SECONDS=75.03

## Selective index

LOCAL_QUERY_ENGINE=SQLite
LOCAL_INDEX=D:\WEBBSITE_CCASS_EXTRACT\webbsite_selective.sqlite
INDEX_BUILD_SECONDS=3621.47
INDEX_SIZE=2674688 bytes
QUERY_READY=PASS
PORTABLE_INDEX=H:\NamFung Drive\投資 - 享受與豐盛\AI Projects\joe-ccass-platform\docs_reference_evidence\latest_reference_updates\WEBBSITE_CCASS_WORKSTATE\webbsite_selective.sqlite

## WEBBSITE row-level proof

00388: EARLIEST_DATE=2007-06-26; LATEST_DATE=2025-12-24; DAILYLOG_ROWS=4563; BIGCHANGES_ROWS=1289
01211: EARLIEST_DATE=2007-06-26; LATEST_DATE=2025-12-24; DAILYLOG_ROWS=4563; BIGCHANGES_ROWS=2351
01810: EARLIEST_DATE=2018-07-09; LATEST_DATE=2025-12-24; DAILYLOG_ROWS=1840; BIGCHANGES_ROWS=392

WEBBSITE_LAST_VALID_CCASS_DATE=2025-12-24
WEBBSITE_BOUNDARY_PROOF=PASS
5Y_HISTORY_AVAILABLE=YES
10Y_HISTORY_AVAILABLE=YES
BIGCHANGES_ROW_LEVEL_PROOF=PASS

## Unresolved WEBBSITE items

HOLDINGS_ROWS=0 in current selective extraction
PARTHOLD_ROWS=0 in current selective extraction
ISSUEDSHARES_ROWS=0
FULL_SNAPSHOT_RECONSTRUCTION=FAIL
CANONICAL_CONVERSION=FAIL
CHANGES_ENGINE_ACCEPTED=FAIL

These zero extracted rows are not proof that the WEBBSITE archive lacks holdings/parthold. They remain unresolved extraction/table-location evidence.

## Longbridge observed boundary

Tested stocks: 00388, 01211, 01810, 06182.

For each: DATA_TYPE=broker_holding_daily; RETURNED_ROWS=40; EARLIEST_RETURNED_DATE=2026-07-22; LATEST_RETURNED_DATE=2026-09-15.

broker_holding_daily is a single-broker daily-history endpoint. Its available interface exposes no start date, end date, count, or pagination parameters.

LONGBRIDGE_OBSERVED_EARLIEST_DATE=2026-07-22
LONGBRIDGE_TRUE_SOURCE_EARLIEST_DATE=NOT_PROVEN

Do not state that Longbridge history begins on 2026-07-22.

## Zhipu gap status

ZHIPU_CANDIDATE_RANGE=2025-12-25 → 2026-07-21
ZHIPU_RANGE_LOCKED=NO

Longbridge 2026-07-22 is only an observed 40-row single-broker boundary, not a proven true source coverage start. Do not start Zhipu retrieval yet.

## Next action

From another computer: git pull; read this handoff; confirm cloud workstate is synced; do not repeat the 17GB extraction or rebuild the selective index; continue coverage-gap / historical snapshot investigation.

Priority: determine the earliest authoritative date for a complete participant-level snapshot available from Joe current/persistent sources and/or Longbridge, then define the actual middle gap requiring Zhipu.

Do not delete D:\WEBBSITE_CCASS_EXTRACT tonight; it contains the extracted SQL and local SQLite index.

PRODUCTION_CODE_CHANGED=NO
PRODUCTION_DEPLOYED=NO
