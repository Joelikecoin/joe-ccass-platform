# Webb Full Corpus Validation and Historical Backfill V1

Generated: 2026-09-24 (Asia/Hong_Kong)

## Decision

The bounded reconstruction proof has been extended to corpus-level validation. Reconstruction, date resolution, identity handling, canonical staging, readback, idempotency, the three-security historical/current bridge, and historical research surfaces all passed their checks.

The full 229,978,760-row holdings scan found 92 negative absolute holdings. These values conflict with the accepted absolute-position model and may not be silently removed, clamped, or interpreted as deltas. `CORPUS_DATA_QUALITY_PASS` is therefore `NO`. The full backfill readiness gate remains closed and no production or Research Store backfill was started.

## Validation evidence

### Stratified reconstruction

- Securities: 30
- Issue/date cases: 60, split evenly across small, medium, and large participant-count strata
- Years represented: 2007, 2008, 2010, 2011, 2013, 2014, 2016, 2017, 2019, 2020, 2022, 2023, 2024, 2025
- Row mismatches: 0
- Participant mismatches: 0
- Share quantity mismatches: 0

### First observation and date semantics

Focused tests prove that no holding is invented before a participant's first observation, an observed absolute value carries forward, zero closes a position, and a later positive observation reopens it.

For Webb issue 1088, date resolution produced:

| Request type | Requested date | Resolved date |
|---|---:|---:|
| Trading day | 2013-03-19 | 2013-03-19 |
| Weekend | 2013-03-23 | 2013-03-22 |
| Public holiday | 2013-04-01 | 2013-03-28 |
| Before source range | 2000-01-01 | `OUT_OF_RANGE` |
| After source range | 2026-01-01 | `OUT_OF_RANGE` |

### Identity

The observed holdings corpus contains 3,861 source issues and 1,236 source participants. Issue mappings are 2,864 exact, 76 date bounded, 921 ambiguous, and 0 unresolved. Ambiguous issue identities remain explicitly bounded and do not prevent source-level reconstruction.

Participant mappings are 852 canonical and 384 source-ID-only, with 0 ambiguous. The Webb `partID` remains the authoritative historical identity where a canonical mapping is unavailable. No beneficial ownership is inferred.

### Canonical chain

An isolated acceptance database on H: was used; Research Store was not mutated. The chain covered 10 securities and 20 dates:

- Source change rows examined: 166,422
- Canonical rows written/read back: 1,824 / 1,824
- Field mismatch groups: 0
- Duplicate canonical rows: 0
- Lineage-covered rows: 1,824
- Idempotent repeat additional rows: 0
- Explicitly unresolved security cases: 8
- Source-ID-only participant rows: 10

### Corpus quality

The one-pass read-only scan examined every holdings row in native `(issueID, partID, atDate)` order.

| Check | Count |
|---|---:|
| Source rows | 229,978,760 |
| Duplicate natural keys | 0 |
| Conflicting natural keys | 0 |
| Negative holdings | 92 |
| Invalid dates | 0 |
| Unknown/orphan issue rows | 0 |
| Unknown/orphan participant rows | 0 |
| Extreme values over 1 trillion | 0 |
| Zero transitions | 4,907,424 |
| Re-entry after zero | 4,014,343 |

The 92 anomalies span 74 issues and 59 participants, from 2008-10-31 through 2025-10-24. Context inspection found 76 isolated negatives between other states, 2 negative first observations, 5 starts of negative runs, and 9 repeated rows within negative runs. None has a safe automatic disposition. Their exact source rows and adjacent observations are preserved in `WEBB_NEGATIVE_HOLDINGS_V1.csv` and `WEBB_NEGATIVE_HOLDINGS_FORENSIC_V1.csv`.

### Coverage and bridge

Coverage is characterized for every year from 2007 through the available 2026-07-31 gap package. The Webb years are classified `IDENTITY_PARTIAL` because ambiguous historical issue identities are preserved; the available 2026 period is `RECONSTRUCTABLE_PARTIAL`.

The historical/current bridge passed for 00003, 00005, and 00006 across Webb history, the 2025-12 through 2026-07 participant package, and production Longbridge snapshots. Security continuity, participant semantics, share semantics, date semantics, and lineage were retained.

### Regression

- Focused historical suite: 6 passed
- Full repository suite: 622 tests; 614 passed; 8 failed
- New regressions: 0
- Pre-existing/environmental failures: 8

The eight failures match the baseline categories: one dependency expectation, one pre-existing portal route inspection failure, one missing local fixture-data failure, and five Streamlit/UI environment failures.

## Evidence files

- `WEBB_STRATIFIED_VALIDATION_V1.csv`
- `WEBB_STRATIFIED_VALIDATION_SUMMARY_V1.json`
- `WEBB_OBSERVED_ISSUE_IDENTITY_V1.csv`
- `WEBB_OBSERVED_PARTICIPANT_IDENTITY_V1.csv`
- `WEBB_OBSERVED_IDENTITY_SUMMARY_V1.json`
- `WEBB_CANONICAL_CHAIN_SUMMARY_V1.json`
- `WEBB_FULL_CORPUS_QUALITY_SCAN_V2.json`
- `WEBB_NEGATIVE_HOLDINGS_V1.csv`
- `WEBB_NEGATIVE_HOLDINGS_FORENSIC_V1.csv`
- `WEBB_YEAR_COVERAGE_V1.csv`
- `HISTORICAL_CURRENT_BRIDGE_V2.json`
- `HISTORICAL_RESEARCH_SURFACES_V1.json`
- `FULL_REPOSITORY_REGRESSION_V1.txt`
- `WEBB_FULL_CORPUS_ARTIFACT_MANIFEST_V1.csv`

The 20 evidence artifacts were checkpointed to the dedicated H: historical CCASS acceptance directory. Local-to-H SHA-256 comparison found 0 mismatches; the per-file hashes are recorded in the artifact manifest.

## Final handoff

```text
RESULT=PARTIAL_VALIDATION_COMPLETE_BACKFILL_BLOCKED

STRATIFIED_CORPUS_VALIDATION_PASS=YES
VALIDATED_SECURITY_COUNT=30
VALIDATED_CASE_COUNT=60

REFERENCE_ROW_MISMATCH_COUNT=0
REFERENCE_SHARE_MISMATCH_COUNT=0
REFERENCE_PARTICIPANT_MISMATCH_COUNT=0

FIRST_OBSERVATION_SAFETY_PASS=YES
DATE_RESOLUTION_PASS=YES

TOTAL_ISSUES=3861
EXACT_MAPPED_ISSUES=2864
DATE_BOUNDED_MAPPED_ISSUES=76
AMBIGUOUS_ISSUES=921
UNRESOLVED_ISSUES=0

TOTAL_PARTICIPANTS=1236
CANONICAL_PARTICIPANT_MAPPED=852
SOURCE_ID_ONLY_PARTICIPANTS=384
AMBIGUOUS_PARTICIPANTS=0

CANONICAL_RECONSTRUCTION_CHAIN_PASS=YES

CORPUS_DUPLICATE_COUNT=0
CORPUS_CONFLICT_COUNT=0
CORPUS_NEGATIVE_COUNT=92
CORPUS_ORPHAN_ISSUE_COUNT=0
CORPUS_ORPHAN_PARTICIPANT_COUNT=0

HISTORICAL_CURRENT_PARTICIPANT_BRIDGE_V2_PASS=YES

FULL_19Y_PARTICIPANT_BACKFILL_READY=NO

STAGED_BACKFILL_STARTED=NO
BACKFILL_COMPLETED_BATCHES=0
BACKFILL_LAST_COMPLETED_DATE=NONE
BACKFILL_NEXT_BATCH=SOURCE_ANOMALY_RESOLUTION_NEGATIVE_HOLDINGS

BACKFILL_SOURCE_CHANGE_ROWS=0
BACKFILL_RECONSTRUCTED_POSITION_ROWS=0
BACKFILL_CANONICAL_ROWS=0
BACKFILL_READBACK_ROWS=0

BACKFILL_ROW_RECONCILIATION_PASS=NOT_STARTED
HISTORICAL_LINEAGE_PASS=YES_ACCEPTANCE_CHAIN
HISTORICAL_IDEMPOTENT_PASS=YES_ACCEPTANCE_CHAIN

HISTORICAL_RESEARCH_SURFACES_PASS=YES_ACCEPTANCE_STAGING

FULL_REPOSITORY_TEST_COUNT=622
FULL_REPOSITORY_TEST_PASS_COUNT=614
NEW_REGRESSION_COUNT=0
PRE_EXISTING_FAILURE_COUNT=8

RESEARCH_STORE_MUTATED=NO

OWNER_CHAT_CONTINUATION_REQUIRED=NO
OWNER_ACTION_REQUIRED=NO

REMAINING_BLOCKERS=92 source-native negative absolute holdings are formally quarantined pending authoritative semantics or an approved lineage-preserving quarantine policy
NEXT_EXECUTABLE_STAGE=Obtain authoritative semantics or approve the quarantine policy, then rerun the corpus data-quality and readiness gates
```
