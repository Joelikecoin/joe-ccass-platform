# Webb Quarantine Query Plan Diagnostic V1

RESULT = PASS_WITH_QUERY_REWRITE

TARGET_TABLE = canonical_historical_holdings
TARGET_DB = work/webb_quarantine_backfill_sql_v1_local_retry1/webb_quarantine_batch_1.sqlite
VALIDATION_RANGE = 2007-01-01 <= holdings_date < 2008-01-01

## Index inventory

- `canonical_date_idx(holdings_date)`, non-unique
- `sqlite_autoindex_canonical_historical_holdings_1(source_issue_id, source_participant_id, holdings_date)`, unique primary key

No index was added. The date index exists and is selected for all date-bounded
validation queries. The primary key structurally prevents duplicate and
conflicting natural keys.

## Diagnosis

SLOW_QUERY_COUNT = 9
FULL_TABLE_SCAN_QUERY_COUNT = 0
INDEXED_QUERY_COUNT = 8
TEMP_B_TREE_QUERY_COUNT = 1
MISSING_INDEX_COUNT = 0
INDEXES_ADDED = 0
QUERIES_REWRITTEN = 6_TO_1_AGGREGATE

The annual validator repeatedly traversed the same 6,674,040-row index range.
The status-count query also built a temporary B-tree for `GROUP BY`. The rewrite
uses one date-indexed aggregate pass for row, status, negative, lineage, anomaly
lineage, and unknown/null propagation checks. Duplicate and conflict counts are
zero by the unique composite primary key, avoiding redundant grouped scans.

## Benchmark and validation

BEFORE_QUERY_PLAN = indexed searches plus one temporary B-tree
AFTER_QUERY_PLAN = SEARCH canonical_historical_holdings USING INDEX canonical_date_idx
BEFORE_RUNTIME_MS = GREATER_THAN_180000 (original validator exceeded the measured execution window)
AFTER_RUNTIME_MS = 83293.004
PERFORMANCE_IMPROVEMENT_FACTOR = GREATER_THAN_2.16

STAGING_ROW_COUNT = 6674040
READBACK_ROW_COUNT = 6674040
CANONICAL_ROW_COUNT = 6674040
RECONSTRUCTED_VALID_POSITION_COUNT = 6674040
QUARANTINE_STATE_COUNT = 0
DUPLICATE_COUNT = 0
CONFLICT_COUNT = 0
CANONICAL_NEGATIVE_COUNT = 0
LINEAGE_COVERAGE = 6674040
ANOMALY_LINEAGE_COVERAGE = 0_OF_0
UNKNOWN_SOURCE_ANOMALY_PROPAGATION = PASS
IDEMPOTENT_REPEAT_ADDITIONAL_ROWS = 0

QUERY_PLAN_DIAGNOSTIC_PASS = YES
BATCH_1_2007_VALIDATION_STATUS = PASS
BATCH_1_PASS = NO (2008-2010 pending)
OWNER_CHAT_CONTINUATION_REQUIRED = NO
OWNER_ACTION_REQUIRED = NO
NEXT_EXECUTABLE_STAGE = Resume BATCH_1_2008 at shard 2008_03 using the single-pass aggregate validator.
