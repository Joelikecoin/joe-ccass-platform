# Task Board

> 本檔是唯一的當前工作、狀態、驗收證據與下一步清單。長期產品要求見 [`docs/PROJECT_SPEC.md`](docs/PROJECT_SPEC.md)，phase 順序見 [`docs/ROADMAP.md`](docs/ROADMAP.md)。

## Working baseline

- Branch：`main`
- Original requested code baseline：`fad4411`
- Latest implementation reviewed：`8966229`
- Specification baseline reviewed：`67e35e5`
- Functional audit：2026-07-22，見 [`docs/ROADMAP.md`](docs/ROADMAP.md#repository-功能審核)
- Current phase：Phase 1 — Data foundation and objective CCASS sections
- Golden stock：`01592`
- Status updated：2026-07-22 (Asia/Hong_Kong)

## Status rules

- `[ ]` pending
- `[-]` in progress
- `[x]` complete，有 tests／commit／acceptance evidence
- `[!]` blocked，必須寫明阻塞原因與所需使用者動作

同一時間只應有一個主要 `[-]` 任務。完成任務時記錄 tests、commit、source/acceptance evidence；不要在 README 或其他文件建立第二份 task list。

## Completed foundation

- [x] `P0-01` 審核 Repository、README、設定、tests 與三個 baseline commits。
- [x] `P0-02` 匯入《AI 港股財技數據平台｜由零開始完整指南》的有效規格。
- [x] `P0-03` 將 9 張截圖的 holdings、announcements、rainbow、concentration、price、copy/download、mobile 及教學限制轉成文字規格。
- [x] `P0-04` 建立五份 `docs` 文件、互相引用、追溯索引及本 Task Board。
- [x] `P0-05` 將外部 Master Prompt retired；README 改指 Single Source of Truth。
- [x] `P0-06` 審核並納入 `4752183`（Google Drive CSV）、`cbeee7f`（collector/analysis/Streamlit）及 `8966229`（URL log redaction）。

Phase 0 驗收 evidence：Ruff passed；完整 Pytest `51 passed`（使用非同步雲端目錄作 basetemp，避免 Google Drive filesystem race）；UTF-8 replacement scan、相對 Markdown links、`git diff --check` passed；參考網站唯讀檢查確認重導至 Streamlit login，未繞過登入；commit 以本次 documentation commit 的 Git history 為準。

## Audit summary

- Done：3 個功能單位。
- Partial：19 個功能單位。
- Not Started：11 個功能單位。
- 判定證據與逐項缺口只在 [`docs/ROADMAP.md`](docs/ROADMAP.md#repository-功能審核) 維護。
- 排序結論：normalized historical foundation 是 Collector idempotency、Backfill、Changes、Concentration、Rainbow 與後續 delivery surfaces 的共同前置條件。


## 唯一最高優先工作

### [-] P1-01 — Source-neutral normalized historical snapshot foundation

優先理由：目前的 JSON snapshot store 不能提供 idempotent、完整性、provenance 與 date-range 保證；若先擴 Collector、Backfill、Changes、Concentration、Rainbow、API 或 UI，會把同一資料債擴散到所有出口。

目標：在保持現有 `CcassResponse`、Google Drive CSV 及 Webb-site Holdings 相容的前提下，建立可 migration、可追溯、可 idempotent 保存的 normalized historical foundation。

本工作範圍：

- source-neutral snapshot/holding metadata envelope；
- 第一版 SQLite migration 與 normalized repositories；
- raw provenance reference/checksum；
- existing JSON snapshot compatibility/migration boundary；
- golden fixture、storage/migration/compatibility tests。

Acceptance：

- [ ] 定義 stable source-neutral stock、source identity、snapshot、holding、run/error metadata；numeric values 保持 number，保存 source/date/cached/stale/partial/warnings/parser/schema version。
- [ ] 第一版 transactional migration 至少建立 `stocks`、`source_issue_mapping`、`ccass_snapshots`、`ccass_holdings`、`collector_runs`、`source_errors` 及 raw provenance reference。
- [ ] `stock/date/source/participant` unique constraints 與 idempotent upsert 生效；同日重跑不 duplicate，不靜默刪除已保存資料。
- [ ] Snapshot 保存 complete/partial 狀態、issued-shares-as-of、denominator、participant identity；partial/missing 不得被轉成 0。
- [ ] Repository 支援 save、latest、previous 及 date-range query；transaction failure 不留下半套 snapshot。
- [ ] 現有 `CcassResponse`、FastAPI holdings、MCP holdings、Streamlit report、Google CSV/Webb-site routing 保持 compatibility，無 public field rename。
- [ ] 既有最小 `SnapshotStore` 有明確 migration/compatibility path；不破壞現有資料，不以 destructive rebuild 取代 migration。
- [ ] 使用合法保存的 `01592` fixture；live/golden source 核對與預設離線 tests 分離。
- [ ] migration upgrade、idempotency、rollback、partial、duplicate participant、rename、>100%、T+2、compatibility tests 通過。
- [ ] Ruff、完整 Pytest、`git diff --check`、secrets/private-path scan 通過；只更新相關 docs/TASK；commit/push `main`。

明確不在本工作：

- 不開始 Backfill、Rainbow、Price、Announcements、i18n 或新 UI。
- 不擴大 FastAPI/MCP endpoints。
- 不安裝 Windows scheduler、不部署、不執行未核准 live scraping。

Dependencies/risks：

- Migration 必須 additive、transactional、可測試；任何可能破壞真實資料的操作先停下請示。
- Source terms/robots ambiguity、HKEX SDW 自動化、credential 或公開 schema breaking change 依 [`docs/DEVELOPMENT_RULES.md`](docs/DEVELOPMENT_RULES.md) 停下請示。
- 其他所有未完成工作只保留在 [`docs/ROADMAP.md`](docs/ROADMAP.md)，不得在本檔建立第二個 pending queue。

## Decisions and constraints

- 平台只輸出客觀資料；不做投資評分、買賣建議、莊家／收貨／派貨結論。
- DisclosureTracker 只作 UI/功能參考，不是資料依賴。
- 參考 Streamlit 網站的程式、API、Cookie、憑證及非公開資料不使用。
- Cache/last-known-good 必須標 cached/stale/data date，不冒充 live。
- Google Drive/CSV adapter 已於 `4752183` 實作安全下載、validation、memory cache/last-known-good 與 source routing；持久化 import provenance 及跨來源 cache registry 仍待完成。
- Windows schedule、production credentials、付費服務、source legality ambiguity 必須停下請示。

## Evidence template

完成 active task 時在此附加：

```text
Task:
Status: complete | blocked
Commit:
Tests:
Files:
Active sources:
Disabled/unverified sources:
Golden validation:
Public acceptance:
Remaining manual step:
```
