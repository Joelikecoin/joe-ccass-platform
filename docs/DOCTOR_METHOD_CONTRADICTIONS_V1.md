# DOCTOR_METHOD_CONTRADICTIONS_V1

> Registry of intra-methodology contradictions found during ingestion.
> Policy (package §12): both sides preserved, status=UNRESOLVED, never silently
> reconciled. Cross-methodology differences are NOT contradictions — they stay in
> their own namespaces.

## Contradiction records

```text
CONTRADICTION_RECORD_COUNT=0
```

No intra-methodology conflict was found between the 13 ingested source units so far.
Candidate near-conflicts examined and classified (not contradictions):

| Item | Analysis | Outcome |
|---|---|---|
| Hilton「大比例供股用作洗太平地/鋪注資」(L2 E階段) vs Hilton「反覆供股慣犯排除」(L1) | Context differs: single strategic dilution in a controlled E-stage plan vs repeated retail-cash extraction. Same source methodology, different conditions. | Not a contradiction; both carry explicit preconditions. Watch if future Hilton material states them as unconditional. |
| 周顯「碎股減流通=中長期偏多」vs Hilton「碎股回收街貨榨取價值」 | Cross-methodology wording overlap; mechanisms differ (流通收縮 vs 被迫留存). Per §11/§12 rules, NOT merged and NOT logged as contradiction (different namespaces). | Both kept in own namespace (CAND-CHAUHIN-PRIME-RATIO-001 / OBS-H1-007). |
| Hilton 拆股「低位準備炒作/高位直接派貨」vs 周顯供股「短期利淡/中長期偏好」 | Same time-scale separation principle, no conflict. | — |

## Re-evaluation trigger

If any future source unit within HILTON / CHAU_HIN / IVAN_L states a rule that
conflicts with an existing candidate **under the same conditions**, create a
ContradictionRecord (rule_a, rule_b, source_a, source_b, context_difference,
possible_resolution, status=UNRESOLVED) via `IngestionStore.add_contradiction`.
