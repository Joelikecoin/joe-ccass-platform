# Recent CCASS targeted SDW closure gate V1

GIT_HEAD=f5d6eb4e4af8693637bbce86a855ade53ab7b08e

Targeted SDW requests: 14; successes: 14; failures: 0. Requests covered each unresolved stock at 2026-07-31 and 2026-09-24. Raw request results are retained in the ignored runtime evidence file work/targeted_sdw.json; the committed gate records the adjudication only.

## Adjudication

- RESOLVED_ZERO_EXIT: 7 cases (00550/B01161, 00550/B01555, 06182/B01555, 00700/B01110, 00700/B01555, 00700/B01824, 00700/B01914). Each was present on 2026-07-31 and absent in the 2026-09-24 SDW snapshot; no zero was inferred from Longbridge absence.
- RESOLVED_SOURCE_MISMATCH: 1 case (00700/B01714). SDW showed 42,500 on 2026-07-31 and 47,200 on 2026-09-24, while Longbridge detail/daily returned no row. This is an explicit source-surface mismatch and remains a required lineage exception.
- RESOLVED_PARTICIPANT_ABSENT_AFTER_EXIT: 0.
- RESOLVED_TRANSFER_OR_IDENTITY_CHANGE: 0.
- UNRESOLVED: 0.

At the targeted participant level, SDW had 8/8 participants on the baseline snapshot and 1/8 on the recent snapshot; Longbridge was missing all 8 from current detail, and missing all 8 from the targeted daily calls. The single continuing SDW positive is the documented 00700/B01714 source mismatch. No interpolation or missing-to-zero conversion was used.

The production algorithm remains: 2026-07-31 baseline union + existing rescue reuse + current Longbridge detail + broker_holding_daily reconstruction + targeted SDW only for historical-only/disappeared participants. CHG_ZERO_SAFE_TO_SKIP=NO remains unchanged. No full-market run was started.

RECENT_GAP_RECONSTRUCTION_COMPLETE=YES for the eight-case completeness gate, with the explicit source mismatch retained as UNKNOWN for Longbridge rather than overwritten.
