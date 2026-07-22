# Task Board

> 本檔是唯一的當前工作、狀態、驗收證據與下一步清單。長期產品要求見 [`docs/PROJECT_SPEC.md`](docs/PROJECT_SPEC.md)，phase 順序見 [`docs/ROADMAP.md`](docs/ROADMAP.md)。

## Working baseline

- Branch：`main`
- Original requested code baseline：`fad4411`
- Latest implementation reviewed：P1-02 completion commit（見 Git history）
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
- [x] `P1-01` 建立 source-neutral normalized historical snapshot foundation、transactional migrations、raw provenance、idempotent repository 及 legacy compatibility；commit `ec09374`。
- [x] `P1-02` 完成 source-neutral collector routing、dry-run、complete/partial honesty、batch/per-stock run/error accounting 及安全 atomic CSV；commit 見本次 Git history。

Phase 0 驗收 evidence：Ruff passed；完整 Pytest `51 passed`（使用非同步雲端目錄作 basetemp，避免 Google Drive filesystem race）；UTF-8 replacement scan、相對 Markdown links、`git diff --check` passed；參考網站唯讀檢查確認重導至 Streamlit login，未繞過登入；commit 以本次 documentation commit 的 Git history 為準。

## Audit summary

- Done：4 個功能單位。
- Partial：19 個功能單位。
- Not Started：10 個功能單位。
- 判定證據與逐項缺口只在 [`docs/ROADMAP.md`](docs/ROADMAP.md#repository-功能審核) 維護。
- 排序結論：P1-02 已完成；本輪不自動選擇下一項工作，等待使用者批准後才重新執行 Specification → Gap Analysis → TASK。


## 唯一最高優先工作

### [x] P1-02 — Source-neutral collector orchestration and persistent run accounting

優先理由（實作前狀態）：P1-01 已提供 normalized transaction store，但現有 collector 仍繞過 `CcassService` 直接建立 Webb-site client、以最多 100 列作 collection input，且未寫入既有 `collector_runs`／`source_errors`。在此缺口修正前開始 Backfill 或 historical engines，會把來源路由、完整性及失敗狀態的不一致放大至整段歷史。

目標：在不新增資料來源、不改公開 `CcassResponse`／API／MCP／UI contract 的前提下，讓一次性 collector 經現有核准 source modes 取得、驗證並以 normalized repository 保存可信 snapshot，同時持久化 batch/per-stock run evidence。

本工作範圍：

- source-neutral collector orchestration，重用既有 `auto|webbsite|google_drive_csv` routing；
- collector CLI 的 stocks/watchlist、source、`date=latest`、dry-run contract；
- complete／partial／truncated capture honesty；
- `collector_runs`、`source_errors` 及 per-stock result accounting；
- normalized idempotent persistence、raw provenance 與 atomic CSV compatibility；
- collector/storage/routing/CLI regression tests。

Acceptance：

- [x] Collector 不再硬接單一 Webb-site implementation；按既有 `DATA_SOURCE=auto|webbsite|google_drive_csv` 選擇 source，且 CSV-only 模式不建立或呼叫 Webb-site client。
- [x] CLI 保持現有用法相容，並支援規格所列 stocks/watchlist、`--source`、`--date latest`、`--dry-run`；本 task 不把 `--date` 擴成歷史 backfill。
- [x] Collection 與 presentation `holdings_limit` 分離；如來源只提供截斷 rows 或 row count 不完整，必須保存／回報 partial，不得當 complete snapshot 或以 missing rows 補 0。
- [x] 成功 snapshot 經 normalized repository transaction 保存 raw provenance；同 stock/date/source 重跑 idempotent，partial 不覆蓋已保存 complete snapshot。
- [x] Dry-run 仍執行 normalize、fetch、parse、schema/identity/completeness validation，但不寫 database、run/error records 或 CSV。
- [x] 每次 batch 建立可完成的 `collector_runs`；每股有 `SUCCESS`／`PARTIAL`／`ERROR` 結果，正確累計 success/partial/error、開始／完成時間及 safe details。
- [x] Source failure 寫入 `source_errors` 的 safe code/message/retry metadata；單股失敗不回滾其他成功股票，process exit status 能反映 batch 結果。
- [x] Latest CSV 保持 UTF-8-SIG、temporary + atomic replace 及現有 Google CSV compatibility，並補齊可安全輸出的 source/date/cache/partial/warnings metadata；失敗不得破壞上一份 good export。
- [x] 現有 `CcassResponse`、FastAPI holdings/report、MCP holdings、Streamlit report、Google CSV source 及 legacy database compatibility tests 全部保持通過，無 public field rename。
- [x] Offline tests 覆蓋 source modes、dry-run、duplicate run、complete/partial、mixed batch failure、run/error rollback、safe logging、atomic export；Ruff、完整 Pytest、`git diff --check`、secrets/private-path scan 通過後 commit/push `main`。

明確不在本工作：

- 不開始 Resumable Backfill、Changes/Big Changes service、Concentration History、Rainbow、Price、Announcements、i18n 或新 UI。
- 不新增 source adapter、FastAPI/MCP endpoint 或公開 schema。
- 不安裝 Windows scheduler、不部署、不執行未核准 live scraping 或 HKEX SDW automation。

Dependencies/risks：

- 只可重用已在 Repository 核准的 source modes；如遇來源條款／robots ambiguity，依 [`docs/DEVELOPMENT_RULES.md`](docs/DEVELOPMENT_RULES.md) 停下請示。
- Migration 只可 additive；不得破壞 P1-01 database 或 legacy `snapshots` table。
- 完整性無法證明時標 partial；不可為了讓 batch 成功而降低數據誠實要求。


## Decisions and constraints

- 平台只輸出客觀資料；不做投資評分、買賣建議、莊家／收貨／派貨結論。
- DisclosureTracker 只作 UI/功能參考，不是資料依賴。
- 參考 Streamlit 網站的程式、API、Cookie、憑證及非公開資料不使用。
- Cache/last-known-good 必須標 cached/stale/data date，不冒充 live。
- Google Drive/CSV adapter 已於 `4752183` 實作安全下載、validation、memory cache/last-known-good 與 source routing；持久化 import provenance 及跨來源 cache registry 仍待完成。
- Windows schedule、production credentials、付費服務、source legality ambiguity 必須停下請示。

## Evidence template

```text
Task: P1-01 — Source-neutral normalized historical snapshot foundation
Status: complete
Commit: `ec09374`
Tests: Ruff passed; Pytest 64 passed; git diff --check and repository secrets/private-path scan passed.
Files: app/domain/*, app/storage/*, ccass_core/collector.py, tests/test_history_storage.py, tests/fixtures/01592_ccass_response.json, docs/ROADMAP.md, TASK.md
Active sources: google_drive_csv and webbsite holdings routing unchanged; normalized repository is source-neutral.
Disabled/unverified sources: HKEX SDW automation and all unaudited supplemental sources remain disabled/not implemented.
Golden validation: legal offline synthetic 01592 contract fixture saved; explicitly labelled non-production; no live scraping performed.
Public acceptance: not part of P1-01; existing public API/MCP/UI contracts remain covered by the full regression suite.
Remaining manual step: none; P1-01 was approved by the user before this gap-analysis cycle.
```

```text
Task: P1-02 — Source-neutral collector orchestration and persistent run accounting
Status: complete
Commit: current P1-02 commit (Git history)
Tests: Ruff passed; Pytest 78 passed; git diff --check and repository secrets/private-path scan passed.
Files: app/domain/__init__.py, app/domain/history.py, app/storage/history.py, app/storage/migrations.py, ccass_core/collector.py, tests/test_collector.py, tests/test_history_storage.py, docs/ROADMAP.md, TASK.md
Active sources: auto, webbsite and google_drive_csv routing retained; collector now uses shared CcassService; CSV-only construction isolation has offline evidence.
Disabled/unverified sources: HKEX SDW automation and all unaudited supplemental sources remain disabled/not implemented.
Golden validation: synthetic offline 01592 fixtures covered complete/partial, duplicate, dry-run, mixed failure and export flows; no live scraping performed.
Public acceptance: not part of P1-02; existing FastAPI/MCP/Streamlit public contracts passed regression tests without field rename.
Remaining manual step: none; stop pending user approval before the next Specification → Gap Analysis → TASK cycle.
```

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
