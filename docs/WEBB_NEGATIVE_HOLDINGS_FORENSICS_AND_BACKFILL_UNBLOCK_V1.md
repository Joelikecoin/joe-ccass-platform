# Webb Negative Holdings Forensics and Backfill Decision V1

## Decision

`NEGATIVES_ARE_SOURCE_ANOMALIES_WITH_NO_SAFE_CORRECTION` applies. The result is outcome **C: formal quarantine**. The negative values are present in the raw Webb `holdings` table, are reproduced by independent SQL reconstruction, and have no authoritative correction or alternate source semantics in the available source documentation and import logic. No row is silently clamped, dropped, converted to a delta, or promoted to a valid short-position state.

Production backfill remains blocked until a documented quarantine policy or authoritative source correction is approved. Research Store was not changed.

## Raw-to-engine proof

The source is `webbsite_full.sqlite`, table `holdings`, with source SHA-256:

`9CCDE356D068399BFBC931CA6E367E5944AFCF5C16C83D2FF240636995B0BE7C`

All 92 rows were checked directly against the raw `c3` value, parsed as an integer, and reconstructed from the complete adjacent source sequence using the independent latest-absolute-value SQL rule.

```text
NEGATIVE_LEDGER_ROW_COUNT=92
SOURCE_NATIVE_NEGATIVE_COUNT=92
PARSER_GENERATED_NEGATIVE_COUNT=0
RECONSTRUCTION_GENERATED_NEGATIVE_COUNT=0
RAW_RECONSTRUCTION_MISMATCH_COUNT=0
SAME_DAY_DUPLICATE_COUNT=0
SOURCE_SEQUENCE_ORDER_VERIFIED=YES
```

This rules out a parser or reconstruction sign-generation defect. The current reconstruction semantics remain valid and were not reopened.

## Context and clusters

```text
NEGATIVE_SECURITY_COUNT=74
NEGATIVE_PARTICIPANT_COUNT=59
NEGATIVE_DATE_COUNT=89
NEGATIVE_YEAR_COUNT=17
CONTEXT_ROWS=591
CONTEXT_WINDOWS_WITH_AT_LEAST_3_PRECEDING=77
CONTEXT_WINDOWS_WITH_AT_LEAST_3_FOLLOWING=73
```

The available sequence patterns are:

| Pattern | Rows |
|---|---:|
| `POSITIVE_NEGATIVE_POSITIVE` | 34 |
| `ZERO_NEGATIVE_ZERO` | 33 |
| `REPEATED_NEGATIVE_RUN` | 9 |
| `ZERO_NEGATIVE_POSITIVE` | 5 |
| `NEGATIVE_RUN_START` | 5 |
| `POSITIVE_NEGATIVE_ZERO` | 4 |
| `NEGATIVE_FIRST_OBSERVATION` | 2 |

The rows span 2008 through 2025. They are distributed across 74 securities, 59 participants, and 89 dates; this is not one isolated source-date or one participant artifact. The largest repeated magnitude signatures are still ordinary negative integers (including 2,000, 20,000, 2,144, 4,000, and 47,272,000), with no single correction rule supported by the sequence evidence.

## Source-semantics review

The available authoritative local reconstruction specification says that `holdings.c3` is the absolute share balance after a change; it is not a raw delta. The source table has no documented negative marker, deletion flag, short-position field, or correction-event field. The import path preserves the source value; it does not generate or reinterpret negative values. The canonical historical import rejects negative holding shares as invalid canonical input. No available Webb/Enigma schema, query, old code, or data note authorizes treating these values as shorts, deletion markers, or sign inversions.

Therefore:

```text
NEGATIVE_SEMANTICS=UNKNOWN_SOURCE_ANOMALY
SAFE_AUTOMATIC_CORRECTION_COUNT=0
FORMAL_QUARANTINE_REQUIRED=YES
```

## Files

- `WEBB_NEGATIVE_HOLDINGS_FORENSIC_LEDGER_V2.csv`: all 92 ledger rows, identity and lineage fields, raw/parser/reconstruction comparison, and disposition.
- `WEBB_NEGATIVE_HOLDINGS_CONTEXT_V2.csv`: up to three preceding and three following observations per negative row where available.
- `WEBB_NEGATIVE_HOLDINGS_CLUSTERS_V2.csv`: issue/year/transition clusters.
- `WEBB_NEGATIVE_HOLDINGS_FORENSIC_SUMMARY_V2.json`: machine-readable counts and source hash.
- `WEBB_NEGATIVE_SOURCE_SEMANTICS_EVIDENCE_V1.md`: local schema, query, importer, and canonical-invariant evidence.

## Final handoff

```text
OUTCOME=C_NEGATIVES_ARE_SOURCE_ANOMALIES_WITH_NO_SAFE_CORRECTION
NEGATIVE_LEDGER_ROW_COUNT=92
SOURCE_NATIVE_NEGATIVE_COUNT=92
PARSER_GENERATED_NEGATIVE_COUNT=0
RECONSTRUCTION_GENERATED_NEGATIVE_COUNT=0
NEGATIVE_SEMANTICS=UNKNOWN_SOURCE_ANOMALY
SAFE_AUTOMATIC_CORRECTION_COUNT=0
FORMAL_QUARANTINE_REQUIRED=YES
FULL_19Y_PARTICIPANT_BACKFILL_READY=NO
STAGED_BACKFILL_STARTED=NO
RESEARCH_STORE_MUTATED=NO
BACKFILL_DECISION=BLOCKED_PENDING_APPROVED_QUARANTINE_POLICY_OR_AUTHORITATIVE_SOURCE_CORRECTION
NEXT_EXECUTABLE_STAGE=Obtain authoritative semantics or approve a lineage-preserving quarantine policy, then rerun the corpus quality gate
```
