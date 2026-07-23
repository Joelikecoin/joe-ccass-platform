# Task Board

> 本檔是唯一的當前工作、狀態、驗收證據與下一步清單。長期產品要求見 [`docs/PROJECT_SPEC.md`](docs/PROJECT_SPEC.md)，phase 順序見 [`docs/ROADMAP.md`](docs/ROADMAP.md)。

## Working baseline

- Branch：`main`
- Original requested code baseline：`fad4411`
- Latest approved implementation：`d8a480e`（P1-02；CTO approved）
- Current implementation：P1-03 completion commit（pending CTO Review）
- Specification baseline reviewed：`67e35e5`
- Functional audit：2026-07-22，見 [`docs/ROADMAP.md`](docs/ROADMAP.md#repository-功能審核)
- Current phase：Phase 1 — Data foundation and objective CCASS sections
- Golden stock：`01592`
- Status updated：2026-07-23 (Asia/Hong_Kong)

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
- [x] `P1-02` 完成 source-neutral collector routing、dry-run、complete/partial honesty、batch/per-stock run/error accounting 及安全 atomic CSV；commit `d8a480e`，CTO approved。
- [x] `P1-03` 完成 source-neutral requested-date backfill、persistent resume/per-date accounting、exact-date validation、bounded retry及 partial honesty；completion commit pending CTO Review。

Phase 0 驗收 evidence：Ruff passed；完整 Pytest `51 passed`（使用非同步雲端目錄作 basetemp，避免 Google Drive filesystem race）；UTF-8 replacement scan、相對 Markdown links、`git diff --check` passed；參考網站唯讀檢查確認重導至 Streamlit login，未繞過登入；commit 以本次 documentation commit 的 Git history 為準。

## Audit summary

- Done：4 個功能單位。
- Partial：19 個功能單位。
- Not Started：10 個功能單位。
- 總計：33 個功能單位；29 個 Remaining Gaps 已按 phase gate 與依賴在 [`docs/ROADMAP.md`](docs/ROADMAP.md#remaining-gaps-優先序) 完整排序。
- 上述統計及排序是 2026-07-22、P1-03 實作前的正式 Gap Analysis baseline。
- P1-03 已依 CTO 授權完成實作及離線驗證，正等待 CTO Review；本輪不自行進行下一輪 Gap Analysis、不重判功能統計或指定新 task。


## 唯一最高優先工作

### [x] P1-03 — Resumable source-neutral CCASS historical backfill

優先理由：P1-01 已建立 normalized historical repository，P1-02 已建立 source-neutral collector、idempotent snapshot save及 persistent run/error accounting。Phase 1 exit gate 下一個未滿足的直接依賴是可 resume、可隔離單日失敗且不製造日期的歷史 backfill；沒有可信多日 snapshots，不可提前展開 Changes/Concentration historical delivery 或 Rainbow。

目標：在不新增或啟用未核准來源、不改公開 `CcassResponse`／API／MCP／UI contract 的前提下，建立 source-neutral historical backfill CLI及持久化 resume evidence，按已驗證來源能力保存真實 snapshots，安全跳過已有日期並可重試失敗日期。

本工作範圍：

- `app.backfill_ccass` CLI：單一 stock、`--from/--to`、`--latest`、`--resume`、`--dry-run`及既有核准 source selection；
- source-neutral requested-date capability boundary，只接入 Repository 已核准且能誠實提供指定日期的 source/import flow；
- additive `backfill_runs`／per-date result persistence，包括 range、cursor、status、success/failed/skipped、safe errors及 resume state；
- configurable 最大日期數／頁數、request sleep、bounded retry與 fail-loud date availability；
- 已有 snapshot skip、同日重跑 idempotency、單日 failure isolation、failed-date retry及 partial snapshot honesty；
- backfill/storage/CLI/source-capability 的完整離線 tests及現有 regression suite。

Acceptance：

- [x] CLI 支援 `--stock 01592 --from YYYY-MM-DD --to YYYY-MM-DD`、`--latest N`、`--resume`、`--dry-run`；互斥／缺失／反向日期及超出 configurable bound 會在 network/write 前 fail loud。
- [x] Backfill 經 source-neutral requested-date interface；只使用 `DATA_SOURCE_GUIDE.md` 已核准的 source/import flow，來源不支援指定日期時回清晰 `DATE_UNAVAILABLE`／兼容 structured error，不靜默改抓 latest。
- [x] 不以插值、日曆填補或複製 latest 製造 snapshot；保存的 `snapshot_date` 必須由來源資料驗證，requested/returned stock code及日期不符時拒絕持久化。
- [x] Additive transactional migration 保存 run range、cursor、source、started/completed、status及 success/failed/skipped counters；每個 requested date 有 `SUCCESS`／`PARTIAL`／`ERROR`／`SKIPPED` safe result evidence。
- [x] 已存在相同 stock/date/source 的可信 snapshot 會 skip；重跑不 duplicate；partial 不覆蓋 complete；每個成功 snapshot保留 raw provenance。
- [x] Resume 由持久化 cursor/result state繼續，跳過已成功／已存在日期並重試失敗日期；中斷後不把未處理日期標 success或 skipped。
- [x] 單日 source/parse/storage failure 不回滾其他已提交日期；process/run status及 exit code正確反映 complete、partial及 error batch。
- [x] 最大日期數／頁數、request sleep、timeout及 bounded retry 可配置且有 deterministic offline tests；不得無限 retry或高頻 probe。
- [x] Dry-run 執行 normalize、range planning、source capability、fetch/parse/schema/identity/date/completeness validation，但不寫 database、run/error records、cursor或 CSV。
- [x] Log、error、run details 不包含完整 URL/query、API key、Cookie、authorization或私人路徑；safe source/date/error metadata 可追溯。
- [x] Offline tests 覆蓋 range/latest/resume、existing skip、failed retry、partial、date mismatch、bounds、dry-run、rollback/isolation、duplicate及 legacy migration；Ruff、完整 Pytest、`git diff --check`、secrets/private-path scan通過後才可 commit/push `main`。

明確不在本工作：

- 不新增或啟用 HKEX SDW automation、supplemental source、付費服務或未 audit adapter。
- 不實作 source diagnostics endpoint/UI、Changes/Big Changes service、Concentration History、Rainbow、Price、Announcements、i18n或新 exports。
- 不修改公開 FastAPI/MCP/Streamlit schema，不做 destructive migration。
- 不執行未核准 live scraping、Windows scheduler安裝或公開部署驗收。

Dependencies/risks：

- 依賴 P1-01 `ec09374` 與已批准 P1-02 `d8a480e`；migration 只可 additive、transactional、idempotent並保留 legacy database compatibility。
- 若現有核准來源／import flow無法合法、穩定且可驗證地提供 requested date，必須停止並回報；不得以 latest、synthetic fixture或未核准 HKEX SDW automation冒充可用歷史來源。
- Date planning 只代表待查要求，不代表該日存在資料；不存在／非交易日只能記錄 honest `DATE_UNAVAILABLE`／SKIPPED reason，不得生成 snapshot。
- Source terms/robots疑問、憑證、付費服務、破壞性 migration或公開 schema變更均依 [`docs/DEVELOPMENT_RULES.md`](docs/DEVELOPMENT_RULES.md) 立即停下請示。


## P1-03 completion evidence

```text
Task: P1-03 — Resumable source-neutral CCASS historical backfill
Status: complete; pending CTO Review
Commit: P1-03 completion commit（本次 commit；exact hash 以 Git history／push 回報為準）
Tests: Ruff passed; full Pytest 88 passed; CLI smoke, git diff --check, credential-pattern scan and private-path scan passed.
Files: app/backfill_ccass.py, app/config.py, app/errors.py, app/domain/*, app/storage/*, app/sources/google_drive_csv.py, ccass_core/collector.py, examples/ccass_template.csv, tests/test_backfill.py, tests/test_google_drive_csv.py, tests/test_history_storage.py, docs/ROADMAP.md, TASK.md
Active sources: Only the approved Google Drive/CSV import flow provides exact requested-date history; auto selects it only when CCASS_CSV_URL is configured. Existing latest holdings routing remains unchanged.
Disabled/unverified sources: Webb-site remains latest-only for backfill and returns DATE_UNAVAILABLE; HKEX SDW automation and all unaudited supplemental sources remain disabled/not implemented.
Golden validation: Synthetic offline 01592 contract fixtures cover range/latest/resume, unavailable dates, existing skip, retry/sleep, partial, mismatch, interruption, isolation, dry-run, duplicate and legacy migration; fixtures are non-production and no live scraping was performed.
Public acceptance: Existing FastAPI/MCP/Streamlit contracts were not modified; the full offline regression suite passed.
Remaining manual step: CTO Review/approval of this P1-03 completion; do not begin the next Gap Analysis until approved.
```

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
Commit: `d8a480e`
Tests: Ruff passed; Pytest 78 passed; git diff --check and repository secrets/private-path scan passed.
Files: app/domain/__init__.py, app/domain/history.py, app/storage/history.py, app/storage/migrations.py, ccass_core/collector.py, tests/test_collector.py, tests/test_history_storage.py, docs/ROADMAP.md, TASK.md
Active sources: auto, webbsite and google_drive_csv routing retained; collector now uses shared CcassService; CSV-only construction isolation has offline evidence.
Disabled/unverified sources: HKEX SDW automation and all unaudited supplemental sources remain disabled/not implemented.
Golden validation: synthetic offline 01592 fixtures covered complete/partial, duplicate, dry-run, mixed failure and export flows; no live scraping performed.
Public acceptance: not part of P1-02; existing FastAPI/MCP/Streamlit public contracts passed regression tests without field rename.
Remaining manual step: none; P1-02 was formally approved by the CTO before this gap-analysis cycle.
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
