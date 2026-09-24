# Webb Quarantine Policy and Staged Backfill V1

## Frozen source and forensic basis

SOURCE_DB = `C:\Users\Joe Lau\.zcode\workspace\default\webbsite_full.sqlite`
SOURCE_SHA256 = `9CCDE356D068399BFBC931CA6E367E5944AFCF5C16C83D2FF240636995B0BE7C`
SOURCE_NEGATIVE_ROWS = 92
SOURCE_NATIVE_NEGATIVE_ROWS = 92
PARSER_GENERATED_NEGATIVE_ROWS = 0
RECONSTRUCTION_GENERATED_NEGATIVE_ROWS = 0
RAW_RECONSTRUCTION_MISMATCH_ROWS = 0

## Policy materialization

RAW_NEGATIVE_ROWS = 92
RAW_QUARANTINE_WINDOWS = 92
MERGED_QUARANTINE_WINDOWS = 83
ALL_NEGATIVES_CLASSIFIED = YES
UNHANDLED_NEGATIVE_ROWS = 0
QUARANTINED_SECURITIES = 74
QUARANTINED_PARTICIPANTS = 59
QUARANTINED_TRADING_DAYS = 1372
QUARANTINED_POLICY_POSITION_STATES = 1372
CORRECTED_NEGATIVE_ROWS = 0

The raw source rows remain immutable. A negative absolute holding is retained
as a source anomaly and is represented as `UNKNOWN_SOURCE_ANOMALY` with a NULL
canonical quantity for the quarantine interval. It is never converted to zero,
and a missing observation is never inferred to be zero. The quarantine starts
on the negative observation date and ends immediately before the next valid
non-negative observation, when one exists.

## Engine and query gates

QUARANTINE_POLICY_PASS = YES
ANOMALY_LINEAGE_PASS = YES
CANONICAL_UNKNOWN_STATE_PASS = YES
QUERY_UNKNOWN_PROPAGATION_PASS = YES
FOCUSED_ENGINE_TESTS = `10 passed`

## Staged backfill

STAGING_ROOT = `work/webb_quarantine_backfill_sql_v1_local_retry1`
STAGED_BACKFILL_STARTED = YES
ISOLATED_STAGING_ONLY = YES
BATCH_1_TARGET_MATERIALIZED = YES
BATCH_1_VALIDATION = NOT_COMPLETED
BATCHES_COMPLETED_AND_VALIDATED = 0
BATCHES_REMAINING = 7

The set-based writer created the isolated BATCH_1 SQLite target. Its post-write
full-table readback and integrity scan were stopped after the target had
committed, because the 24.5 GB target scan exceeded the execution window. No
H: checkpoint was attempted and no Research Store file was opened for write.

## Readiness and handoff

READINESS = PENDING_STAGED_VALIDATION
AVAILABLE_CORPUS_COMPLETE = NO
SOURCE_LEVEL_COMPLETENESS_VERIFIED = YES
CORPUS_LEVEL_COMPLETENESS_VERIFIED = NO
NO_FURTHER_DIGESTION_REQUIRED = NO
RESEARCH_STORE_MUTATED = NO
STATUS = PARTIAL

NEXT_EXACT_ACTION = Resume validation of the committed local BATCH_1 target
with a streaming count/integrity pass, then run BATCH_2 through BATCH_7 in the
same isolated staging workflow. Only after every batch passes may the staged
artifacts be checkpointed to the designated H: acceptance directory.
