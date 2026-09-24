# Webb Negative Source Semantics Evidence

This note records the available local evidence reviewed for the 92 negative rows. It does not assign a meaning that the source does not document.

## Evidence for absolute-value semantics

- [`docs/WEBB_CHANGELOG_TO_POSITION_RECONSTRUCTION_V1.md`](WEBB_CHANGELOG_TO_POSITION_RECONSTRUCTION_V1.md:5) records the Webb schema mapping: `c1=partID`, `c2=issueID`, `c3=holding`, and `c4=atDate`.
- The same document states that `holding` is the absolute share balance after the change, not a delta, and that the sparse table is reconstructed with the latest `atDate` at or before the effective date.
- [`app/services/webb_sparse_holdings.py`](../app/services/webb_sparse_holdings.py:3) parses `c3` as the absolute holding and carries the latest value. It counts negative values but does not create or transform them.

## Evidence against an engine-generated sign

- The raw ledger contains the exact negative `c3` strings from `holdings`.
- Integer parsing reproduced all 92 values exactly.
- Independent latest-value SQL over each complete adjacent pair sequence reproduced all 92 values exactly.
- The full-corpus native-order scan found zero duplicate natural keys, zero conflicts, and zero source-order violations.

```text
SOURCE_NATIVE_NEGATIVE_COUNT=92
PARSER_GENERATED_NEGATIVE_COUNT=0
RECONSTRUCTION_GENERATED_NEGATIVE_COUNT=0
RAW_RECONSTRUCTION_MISMATCH_COUNT=0
```

## Native query behavior

The independent SQL equivalent of Webb's `chholdings.asp` query in [`app/services/webb_sparse_holdings.py`](../app/services/webb_sparse_holdings.py:208) selects the latest absolute value and filters active output with `CAST(h.c3 AS INTEGER) > 0`. This explains why negative rows do not become active participant holdings in the reconstructed output. It does not document whether a negative source value is a correction marker, a short position, a deletion, or an error.

## Import and canonical behavior

- [`app/import_webb_canonical.py`](../app/import_webb_canonical.py:63) preserves numeric holdings when constructing canonical snapshots; it contains no negative-value reinterpretation.
- [`app/canonical_historical_import.py`](../app/canonical_historical_import.py:180) rejects negative canonical holding shares. This is a canonical data-quality invariant, not evidence of source semantics.
- No local Webb/Enigma schema, query, import note, or old implementation reviewed defines a negative absolute holding as a valid special participant state.

## Determination

```text
NEGATIVE_SEMANTICS=UNKNOWN_SOURCE_ANOMALY
SAFE_AUTOMATIC_CORRECTION_COUNT=0
FORMAL_QUARANTINE_REQUIRED=YES
```

The correct safe disposition is lineage-preserving formal quarantine pending an authoritative source explanation or an explicitly approved correction policy.
