# Webb quarantine staged backfill final parent acceptance V1

Generated: 2026-09-25 (Asia/Hong_Kong)

## Decision

The bounded parent gates passed for idempotency, all ten historical research
surfaces, the three-security historical/current bridge, 2026 source layering,
and representative staged-row lineage. The full repository regression repeated
the same eight known failures and introduced no new regression.

Production acceptance remains closed because the persisted batch evidence does
not reconcile to the frozen handoff denominator. The reported `48,970,050`
rows are Batches 2-7 only. The accepted Batch 1 evidence contains another
`38,525,367` rows, so all persisted batches total `87,495,417` rows. Batch 1
uses source SHA-256 `9CCDE356D068399BFBC931CA6E367E5944AFCF5C16C83D2FF240636995B0BE7C`;
Batches 2-7 use `ADAAC9F609F4AB0495ACA5F141C5D65ECFC3AE32F7B2C9C0CF667A2431A29F0A`.

The source-version break also affects quarantine continuity. Of 92 negative
observations in the audited original source, all 34 from 2007-2010 are present
in Batch 1, but only 22 of 58 from 2011-2025 are present in Batches 2-7. The
frozen source itself contains 34 negative rows: 12 from 2009-2010 and 22 from
2011-2022. The 36 absent post-2010 observations are listed in
`WEBB_FINAL_PARENT_GATES_EVIDENCE_V1.json`. This prevents global anomaly
lineage acceptance.

## Quarantine denominator reconciliation

| Count | Exact meaning |
|---:|---|
| 92 | Source-native negative holding observations in the original audited Webb source. |
| 83 | Overlapping or adjacent anomaly intervals merged by issue and participant. |
| 1,372 | Issue trading-date position states inside those 83 windows. These are daily policy states, not source event rows. |
| 22 | `UNKNOWN_SOURCE_ANOMALY` source-event rows in the frozen 2011-2026 staging databases only. |
| 34 | `UNKNOWN_SOURCE_ANOMALY` source-event rows in the accepted 2007-2010 Batch 1. |
| 56 | Total source-event anomaly rows currently present across all seven staged batches. |

Every staged anomaly row checked preserves a NULL share quantity,
`UNKNOWN_SOURCE_ANOMALY`, `SOURCE_ANOMALY`, anomaly IDs, and source lineage.
The denominator semantics are explicit, but the semantic gate fails because
36 original negative observations have no row in the currently combined staged
corpus.

## Bounded acceptance evidence

### Idempotency

The isolated acceptance database used 76 actual canonical rows across an early
period, a middle period, a late period, and a quarantine case. The first write
inserted 76 rows; the repeat inserted 0. The natural key is
`(source_issue_id, source_participant_id, holdings_date)` and duplicate keys
were 0.

### Historical research surfaces

Actual read-only queries passed for holdings by stock/date, participant history,
participant changes, cross-stock participant search, Top 5 inputs, Top 10
inputs, concentration inputs, broker history, broker fingerprint inputs, and
the historical CCASS timeline. Representative event dates were 2007-06-26,
2020-01-02, and 2025-01-02. The anomaly query returned
`UNKNOWN_SOURCE_ANOMALY` and `SOURCE_ANOMALY` for issue 1, participant 28 on
2014-09-18.

### Historical/current bridge and 2026 layering

The existing accepted readback evidence passes for 00003, 00005, and 00006
through Webb history, the gap package, and current production. It preserves
security identity, source-scoped participant semantics, absolute-share
semantics, dates, and lineage.

`BATCH_7=YES_NO_AVAILABLE_2026_ROWS` means the frozen Webb source has no 2026
rows. The separate gap package supplies validated data through 2026-07-31, and
the existing production readback supplies verified September 2026 snapshots.

### Global row and lineage evidence

Persisted validation files reconcile within each source version:

| Scope | Source rows | Canonical rows | Quarantined source-event rows |
|---|---:|---:|---:|
| Batch 1, 2007-2010 | 38,525,367 | 38,525,367 | 34 |
| Batches 2-7, 2011-2026 | 48,970,050 | 48,970,050 | 22 |
| Combined persisted evidence | 87,495,417 | 87,495,417 | 56 |

Duplicate, conflict, and canonical-negative counts are all zero. Normal and
quarantine row drilldowns matched canonical keys to Webb issue, participant,
date, and source references. Global staged-row lineage passes. Global anomaly
lineage fails because the current source-version combination omits 36 audited
negative observations.

## Regression

The full repository suite ran once:

- Tests: 626
- Passed: 618
- Failed: 8
- New regressions: 0
- Pre-existing failures: 8
- Environment-related failures within the pre-existing set: 6

The eight failed test IDs exactly match `FULL_REPOSITORY_REGRESSION_V1.txt`.

## Final handoff

```text
RESULT=NOT_COMPLETED_SOURCE_VERSION_AND_DENOMINATOR_RECONCILIATION_FAILED

QUARANTINE_COUNT_SEMANTICS_PASS=NO

RAW_NEGATIVE_COUNT=92
MERGED_QUARANTINE_WINDOW_COUNT=83
AFFECTED_POSITION_STATE_COUNT=1372
CANONICAL_QUARANTINED_STATE_COUNT=22

GLOBAL_IDEMPOTENCY_PASS=YES

HISTORICAL_RESEARCH_SURFACES_PASS=YES
HISTORICAL_CURRENT_BRIDGE_FINAL_PASS=YES
2026_SOURCE_LAYERING_PASS=YES

GLOBAL_ROW_RECONCILIATION_PASS=NO
GLOBAL_LINEAGE_PASS=YES
GLOBAL_ANOMALY_LINEAGE_PASS=NO

FULL_REPOSITORY_TEST_COUNT=626
FULL_REPOSITORY_TEST_PASS_COUNT=618
NEW_REGRESSION_COUNT=0
PRE_EXISTING_FAILURE_COUNT=8
ENVIRONMENTAL_FAILURE_COUNT=6

FULL_19Y_PARTICIPANT_BACKFILL_COMPLETE=NO
HISTORICAL_CCASS_PRODUCTION_READY=NO
DOCTOR_CCASS_DATA_LAYER_READY=NO

RAW_SOURCE_MUTATED=NO
H_DRIVE_SOURCE_MUTATED=NO
RESEARCH_STORE_MUTATED=NO

OWNER_CHAT_CONTINUATION_REQUIRED=YES
OWNER_ACTION_REQUIRED=YES

REMAINING_BLOCKERS=The 48,970,050 handoff denominator excludes Batch 1; the seven persisted batches total 87,495,417 rows across two source hashes; 36 of the 92 original negative observations are absent from the post-2010 frozen-source staging.
NEXT_EXECUTABLE_STAGE=Select one complete authoritative source version, freeze it transactionally, reconcile its year and negative-observation counts to the original audit, then rebuild only the source-version-inconsistent batches under a separately authorized correction package.
```

## Artifacts

- `WEBB_FINAL_PARENT_GATES_EVIDENCE_V1.json`
- `FULL_REPOSITORY_REGRESSION_FINAL_V1.txt`
- `scripts/validate_webb_final_parent_gates_v1.py`

