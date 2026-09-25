# DOCTOR_CASE_DERIVED_INGESTION_STATUS_V1

> Work package `DOCTOR_CASE_DERIVED_KNOWLEDGE_INGESTION_V1`. Baseline = ZC Method
> Intelligence V1 commit `4e4b23d` (42/42 tests preserved). Storage = dev-only
> `app/data/doctor/doctor_ingestion.sqlite` (never the Research Store).
> Date: 2026-09-25.

## Pipeline

```text
SOURCE UNIT → OBSERVATION (fact / interpretation separated)
            → EVIDENCE CHAIN (data→comparison→reasoning→conclusion, steps preserved)
            → CASE_DERIVED RULE CANDIDATE (lineage + falsification mandatory)
            → [STOP — human review gate; no auto-promotion]
```

Schema module: `app/doctor/ingestion.py` (SourceUnit / Observation / EvidenceChain /
RuleCandidate / ContradictionRecord / IngestionCheckpoint + IngestionStore).
Seeds: `scripts/zc_ingest_case_knowledge_v1.py` (idempotent, per-source-unit
checkpoints for token-efficient resume).

## Batch accounting

```text
BATCH_1_HILTON: 10 source units processed
BATCH_2_CHAU_HIN: 2 of 9 source units processed (L1, L2A) — 7 remaining (L2B/3A/3B/4/5A/5B/102)
BATCH_3_IVAN_L: 2 of 4 source units processed (課程摘要 + L型研究I版GO兌現機制[量化]); 完整結果總表/現況檢查 pending
TOTAL sources_processed=14 / discovered≈23
OBSERVATION_COUNT=110
RULE_CANDIDATE_COUNT=48 (all CASE_DERIVED)
FALSIFICATION_INCOMPLETE_COUNT=0 (schema enforces)
CONTRADICTION_RECORD_COUNT=0 (none found between ingested sources; near-conflicts classified in DOCTOR_METHOD_CONTRADICTIONS_V1.md)
```

Generalization split of observations: REPEATABLE_METHOD 79 / POTENTIALLY_GENERALIZABLE 21 /
CASE_SPECIFIC 0 / INSUFFICIENT_EVIDENCE 3 (kept as observations only, e.g. 5/10/85
勝率口述估計 OBS-H6-006; 絕不強制成 rule).

Dedup ledger: NEW_RULE=43, SAME_RULE_NEW_EVIDENCE=1
(CAND-HILTON-SPINOFF-PRESSURE-001 re-recorded from 急跌博反彈 with passive-fund
evidence), RULE_VARIANT=2 (CAND-CHAUHIN-THRESHOLD-ASK-001 vs Hilton 29.97% line —
same structure, different methodology, **kept separate** per namespace isolation),
CONTRADICTING_RULE=0, POSSIBLE_DUPLICATE=0.
Notable near-dupes NOT created: 急跌博反彈分拆沽壓章節 deliberately did not spawn a
second copy of the spin-off rule.

## Temporal rules captured (Step 6 examples)

供股復仇記 Last-Pay-Day 前一至兩日離場；C階段 GO 結束前兩日離場；配股半個月至一個月
時間止蝕；啤殼 1.5-2年啟動窗 / >3年模型失效；分拆首輪沽壓 ≤2-3個月；L型沉底
6-12月；絕地跌穿招股價後沉底期；白武士四級週期；市差回報延遲 10-20日。
Each is stored as `trigger_conditions` / `TIMING_RULE` observation, separate from
ordinary conditions.

## CCASS-specific safety carried into candidates (Step 8)

- CAND-HILTON-CCASS-DRYNESS-CALC-001: participant≠beneficial owner preserved;
  >90% threshold (91% vs 98% no strategy difference); 非CCASS全記M貨為估計法。
- CAND-HILTON-FAKE-MOVE-EXCLUDE-001: company-action mechanical moves excluded.
- CAND-HILTON-DI-ARTIFACT-001: >100% / duplicate declarations / underwriter
  phantom stakes excluded.
- CAND-HILTON-CCASSIN-POSITION-001: T+3 visibility window explicit.
- 周顯『乾』（交投疏落）vs『貨源集中』區分 (OBS-H8-002) — matches platform's
  no-auto-concentration-conclusion contract.

## Ingestion checkpoints

All 13 sources have `ingestion_checkpoints` rows (processed sections,
observation ids, candidate ids, open questions, last_position=EOF) — resume
without re-reading page 1.

## Open questions (per checkpoint)

- Hilton: 乾度首10-20券商集中度門檻未量化；GO+20/20勝率須以本站GO名單獨立重算；
  殼價數字須外部更新；309射倉日期待補。
- 周顯: 29.99%案例公司名辨識失真；L1屬大勢框架課（規則密度低）。
- Ivan: 逐字稿辨識失真術語（MIMA）不採用；人物名單不建。

## Remaining backlog (resume points)

1. 周顯 L2B/3A/3B/4/5A/5B/102（7 units）
2. 股票案例/L型研究I版_最終版_GO兌現機制_20260731.md + L型研究_完整結果總表
   （IVAN_L quantitative, high priority next batch）
3. 財技班-Hilton/筆記 PDF 8 份（高成本，課堂摘要已覆蓋主幹）
4. 20260906 Hilton GO全購買殼學 五階段完整教材.md（113KB，最大單一來源）

## Test evidence

`tests/test_doctor_ingestion.py` (18) + existing doctor suites (42) = 60 passed (14 source units, 110 observations, 48 candidates).
