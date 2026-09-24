# Webb change log to position reconstruction V1

## Source semantics

Webb's schema notes and `choldings.asp` establish that `holdings` is a sparse
change log. Its imported generic columns are:

| Native meaning | Imported column | Semantics |
|---|---|---|
| `partID` | `c1` | Source participant identifier |
| `issueID` | `c2` | Source security issue identifier |
| `holding` | `c3` | Absolute share balance after the change; it is not a delta |
| `atDate` | `c4` | Effective CCASS holding date |

The natural change key is `(issueID, partID, atDate)`. Webb's native query
selects `MAX(atDate)` per participant at or before the effective date. The
effective date is the latest `dailylog` date at or before the requested date.
No change row means the last absolute balance carries forward. A zero balance
closes the position.

`share_delta` is derived only as the difference between two consecutive
absolute values for the same issue and participant. The `holdings` table does
not store a raw share-delta field. A source row ID is retained for audit, but it
does not replace the natural key.

## Engine

`app/services/webb_sparse_holdings.py` provides:

- deterministic reconstruction for one issue and date;
- a one-pass multi-date reconstruction;
- source-date resolution through `dailylog`;
- duplicate, conflict, negative-value, zero-position and total-share accounting;
- an independent SQL expression of Webb's native query for validation.

`app/reconstruct_webb_positions.py` is a read-only command-line interface. It
opens SQLite with `mode=ro` and emits JSON summaries or participant rows.

## Validation

The ordered engine was compared with the independent native-query equivalent
at an early, middle and late corpus date:

| issueID | Date | Engine rows | Reference rows | Engine shares | Reference shares | Exact match |
|---:|---|---:|---:|---:|---:|---|
| 1 | 2008-01-15 | 334 | 334 | 983,968,689 | 983,968,689 | YES |
| 1088 | 2013-03-19 | 518 | 518 | 5,621,367,584 | 5,621,367,584 | YES |
| 348 | 2025-12-24 | 362 | 362 | 9,681,669,158 | 9,681,669,158 | YES |

All three cases had zero duplicate change keys, zero conflicting change keys,
and zero negative values. The issue and participant column interpretation was
also reconciled against the full imported identity domains: all 3,861 observed
issue IDs have a `shortnames` entry and all 1,236 observed participant IDs have
a `participants` entry.

## Result

RESULT=COMPLETED
WEBB_COLUMN_ORDER_CORRECTED=YES
OLD_REVERSED_PROOF_INVALIDATED=YES
CHANGE_LOG_SEMANTICS_VERIFIED=YES
HOLDING_VALUE_TYPE=ABSOLUTE_SHARE_VALUE
RAW_SHARE_DELTA_PRESENT=NO
NATURAL_CHANGE_KEY=issueID+partID+atDate
SOURCE_ORDERING=atDate+numeric_partID+partID+source_rowid_tiebreaker
SOURCE_DATE_RESOLUTION=LATEST_DAILYLOG_DATE_AT_OR_BEFORE_REQUEST
POSITION_RECONSTRUCTION_ENGINE_READY=YES
MULTI_DATE_RECONSTRUCTION_READY=YES
INDEPENDENT_REFERENCE_CASES=3
INDEPENDENT_REFERENCE_CASES_PASS=3
DUPLICATE_CHANGE_KEYS_IN_VALIDATION=0
CONFLICTING_CHANGE_KEYS_IN_VALIDATION=0
NEGATIVE_VALUES_IN_VALIDATION=0
ISSUE_DIRECTORY_COVERAGE=3861/3861
PARTICIPANT_DIRECTORY_COVERAGE=1236/1236
SOURCE_DATABASE_MUTATED=NO
RESEARCH_STORE_MUTATED=NO
