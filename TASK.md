# Task Board

> 本檔是唯一的當前工作、狀態、驗收證據與下一步清單。長期產品要求見 [`docs/PROJECT_SPEC.md`](docs/PROJECT_SPEC.md)，phase 順序見 [`docs/ROADMAP.md`](docs/ROADMAP.md)。

## Working baseline

- Branch：`main`
- Original requested code baseline：`fad4411`
- Latest implementation reviewed：`8966229`
- Specification baseline：建立本文件的 documentation commit（以 Git history 為準）
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

## Active task

### [-] P1-01 — Source audit、source-neutral schema 與 migration plan

目標：在不破壞 `CcassResponse` 兼容性的前提下，建立 Phase 1 可落地的 source registry、domain envelope、SQLite schema/migration 及 golden-stock fixture plan。

Acceptance：

- [ ] 盤點 Webb-site endpoints、HKEX SDW 後備／人工 import 邊界及 source status。
- [ ] 把 Webb-site fetch 與 holdings parser 分離，保留現有錯誤分類與 tests。
- [ ] 定義 source-neutral metadata、snapshot/holding models 與 compatibility tests。
- [ ] 建立第一版 SQLite migration，涵蓋 `stocks`、`source_issue_mapping`、`ccass_snapshots`、`ccass_holdings`、run/error provenance 最小集合。
- [ ] Migration transaction、unique constraints、idempotent upsert、no-silent-delete tests 通過。
- [ ] 為 golden stock `01592` 保存合法 fixture；live 核對與離線 test 分開。
- [ ] Ruff、Pytest、diff/secrets check 通過；更新 docs/TASK；commit/push `main`。

Dependencies/risks：

- Source terms/robots audit 若無法安全判斷，標 `[!]` 並停止 active parser 擴充。
- HKEX SDW 自動化若需不安全繞過，改走 manual CSV import。
- Public schema 只 additive 擴充；breaking change 需使用者批准。

## Phase 1 queue

- [ ] `P1-02` Historical repositories、raw provenance、atomic CSV history。
- [ ] `P1-03` 將既有最小 collector 完整化：normalized persistence、idempotent upsert、dry-run、batch isolation。
- [ ] `P1-04` Resumable CCASS backfill + failed-date retry。
- [ ] `P1-05` Holdings vertical slice 完整化及 golden validation。
- [ ] `P1-06` Changes + objective comparison engine。
- [ ] `P1-07` Big Changes + configurable thresholds。
- [ ] `P1-08` Concentration + denominator/partial rules。
- [ ] `P1-09` Phase 1 integration/smoke/public deployment gate。

## Later phases

- [ ] Phase 2：Rainbow、fixed colours、Concentration/Price history、aligned bilingual responsive UI。
- [ ] Phase 3：HKEX announcements、Company、Raw Previews、all exports/copy/report。
- [ ] Phase 4：complete FastAPI/MCP、source diagnostics、cache/fallback/import adapters。
- [ ] Phase 5：golden/public acceptance、operations docs、scheduler scripts（不自行安裝）。

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
