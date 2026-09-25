# Webb 權威來源核對與選擇性重建 V1

日期：2026-09-25（Asia/Hong_Kong）

## 決定

Candidate A 已選為唯一權威 Webb 歷史來源。公司電腦的 G: 雲端檔與本機唯讀快取均重新計算為 SHA-256
`9CCDE356D068399BFBC931CA6E367E5944AFCF5C16C83D2FF240636995B0BE7C`，檔案大小
10,848,636,928 bytes，`PRAGMA integrity_check(1)=ok`。來源有 229,978,760 筆原始列，當中
225,071,295 筆為 canonical 可物化非零狀態、4,907,465 筆為明確零狀態；日期由
2007-06-26 至 2025-12-24。

Candidate A 對既有 forensic ledger 的自然鍵 `(issueID, partID, atDate)` 及負數值核對為
92/92，缺失 0、錯值 0、額外負數 0。重新產生 quarantine 後仍為 92 個原始負數、83 個合併
視窗及 1,372 個 issue trading-date policy states。

Candidate B 的精確 SQLite 在公司電腦及可見 G: 根目錄均不存在，因此無法重新產出
ADDED/REMOVED/CHANGED 三組逐自然鍵差異。已保存證據顯示該檔是在來源被並行修改期間凍結的
部分匯入：2011–2025 只有 48,970,050 筆可物化列，較 Candidate A 同期少 137,575,878 筆，
並只保留 34/92 個負數指紋。這個限制獨立標記為 `SOURCE_VERSION_DIFF_PASS=NO`，不會把
Candidate B 的缺檔誤當作 Candidate A 的完整性失敗。

## 選擇性重建

Batch 1 的來源 hash 已是 Candidate A，保留 38,525,367 筆。只重建來源版本不一致的
Batch 2–6；Batch 7 因權威來源沒有 2026 列，只重建空 schema 與來源 metadata。舊 Candidate B
證據未刪除，全部以 `SUPERSEDED_SOURCE_VERSION` 保留。

| Batch | 日期範圍 | canonical 列 | quarantine | 結果 |
|---|---|---:|---:|---|
| 1 | 2007–2010 | 38,525,367 | 34 | 保留，PASS |
| 2 | 2011–2014 | 45,185,475 | 17 | 重建，PASS |
| 3 | 2015–2018 | 54,552,724 | 25 | 重建，PASS |
| 4 | 2019–2022 | 52,165,386 | 12 | 重建，PASS |
| 5 | 2023–2024 | 21,066,731 | 2 | 重建，PASS |
| 6 | 2025 | 13,575,612 | 2 | 重建，PASS |
| 7 | 2026 | 0 | 0 | metadata-only，PASS |
| **總計** | **2007–2026** | **225,071,295** | **92** | **PASS** |

每個新批次均通過：row reconciliation、自然鍵／衝突安全、canonical 非負及 UNKNOWN 傳播、
readback checkpoint。Lineage 為 186,545,928/186,545,928；每批固定樣本重試新增 0。

## Parent gates

- `ALL_ACTIVE_BATCHES_USE_AUTHORITATIVE_SOURCE=YES`
- `RAW_NEGATIVE_LEDGER_MATCH=92/92`
- `GLOBAL_ROW_RECONCILIATION_PASS=YES`
- `GLOBAL_LINEAGE_PASS=YES`
- `GLOBAL_ANOMALY_LINEAGE_PASS=YES`
- `GLOBAL_IDEMPOTENCY_PASS=YES`
- `HISTORICAL_RESEARCH_SURFACES_PASS=YES`
- `HISTORICAL_CURRENT_BRIDGE_FINAL_PASS=YES`
- `2026_SOURCE_LAYERING_PASS=YES`

2014-09-18、2020-01-02、2025-01-02 的新 staging 實測均能讀取 stock/date holdings、
cross-stock participant、Top-10 input 及原始 Webb rowid lineage；三個樣本的 source hash 均為 Candidate A。

完整 repository regression 共 631 項：626 passed、5 failed。5 項失敗全部屬既有 baseline failure ID，
本工作新增 regression 為 0；新增的來源核對測試 5/5 passed。

## 安全狀態

原始 Webb 檔、G: 雲端檔及 Research Store 均未修改。所有新大型資料庫均位於 repo 已忽略的
`work/webb_authoritative_rebuild_v1*` 隔離路徑；可提交的證據位於 `docs/`。同一工作區另有流程
加入新 commit，本工作未 reset、rebase、discard 或覆蓋該等變更。

## 尚餘限制

Candidate B 精確檔缺失，故逐自然鍵 A/B `ADDED_ROWS`、`REMOVED_ROWS`、`CHANGED_ROWS` 仍不可重新
計算。安全後續是把 hash 為 `ADAAC9F...A29F0A` 的原凍結檔同步到公司電腦，再只執行唯讀 diff；
不得用其他檔案冒充。
