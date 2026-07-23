# Task Board

> 本檔是唯一的當前工作、狀態、驗收證據與下一步清單。長期產品要求見 [`docs/PROJECT_SPEC.md`](docs/PROJECT_SPEC.md)，phase順序與完整Gap Analysis見 [`docs/ROADMAP.md`](docs/ROADMAP.md)。

## Working baseline

- Branch：`main`
- Original requested code baseline：`fad4411`
- Latest approved baseline：`172e50f0fd367af62343b1125c0da3fd729cfd39`（P1-06；CTO approved）
- Specification baseline reviewed：`67e35e5`
- Functional audit：2026-07-23，見 [`docs/ROADMAP.md`](docs/ROADMAP.md#repository-功能審核)
- Current phase：Phase 1 — Data foundation and objective CCASS sections
- Golden stock：`01592`
- Status updated：2026-07-23 (Asia/Hong_Kong)

## Status rules

- `[ ]` pending
- `[-]` in progress
- `[x]` complete，有tests／commit／acceptance evidence
- `[!]` blocked，必須寫明阻塞原因與所需使用者動作

同一時間只保留一個最高優先主要任務。完成任務時記錄tests、commit、source/acceptance evidence；不要在README或其他文件建立第二份task list。

## Completed foundation

- [x] `P0-01`–`P0-06`：建立並核對Single Source of Truth、匯入有效指南／截圖規格、retire外部Master Prompt，納入Google CSV、collector/UI及URL redaction基線。
- [x] `P1-01`：source-neutral normalized historical snapshot foundation、transactional migrations、raw provenance、idempotent repository及legacy compatibility；commit `ec09374`，CTO approved。
- [x] `P1-02`：source-neutral collector routing、dry-run、complete/partial honesty、batch/per-stock run/error accounting及安全atomic CSV；commit `d8a480e`，CTO approved。
- [x] `P1-03`：source-neutral exact-date backfill、range/latest/resume、persistent per-date accounting、existing skip、failed-date retry、bounded retry、partial honesty及dry-run完整validation零寫入；commits `f9fcf02`、`6152135`，CTO approved。
- [x] `P1-04`：configuration-driven source registry、truthful capability/audit metadata、安全internal diagnostics及service/collector/backfill selection；commit `7b69316`，CTO approved。
- [x] P1-05：guarded streaming Webb-site latest Holdings adapter、純offline parser、identity/content/body/size guards及registry parser v2；commit 9e833214f634f42e8e64d8a149d57976b5c1b1aa，CTO approved。
- [x] P1-06：persistent normalized LKG、freshness semantics、transient-only fallback及collector stale accounting；commit `172e50f0fd367af62343b1125c0da3fd729cfd39`，CTO approved。

## Post-P1-04 Gap Analysis

- Done：6個功能單位。
- Partial：19個功能單位。
- Not Started：8個功能單位。
- Remaining Gaps：27個，已按Phase gate、前置依賴、風險及最小完整vertical slice重新排序，見 [`docs/ROADMAP.md`](docs/ROADMAP.md#remaining-gaps-優先序)。
- Phase 1維持In Progress：Latest Holdings已成為第一個完整核心vertical slice；合法active source多日真實snapshots、golden核對及Changes／Big Changes／Concentration仍未滿足。
- P1-05及P1-06已由CTO批准；P1-07只完成Latest Holdings產品切片，不開始下一個TASK或其他section。

## 唯一最高優先工作

### [x] P1-07 — Complete Latest Holdings Vertical Slice

優先理由：P1-01至P1-06已提供可信latest fetch/parser、normalized persistence、collector、persistent LKG、freshness及diagnostics；目前剩餘缺口是把既有能力收斂成符合Project Specification、可由API直接使用及可明確驗收的完整Latest Holdings產品切片。

本工作範圍：

- 只修補Latest Holdings現有產品缺口：公開`participant_name`／`pct_of_ccass`、`issued_shares_as_of`、完整snapshot與`holdings_limit`不變量、metadata／diagnostics及產品驗證。
- 讓既有source → parser → normalize → collector／LKG → service → API流程以完整snapshot先驗證，再只切片回傳rows；summary、participant count及Top 5／Top 10保持全snapshot口徑。
- 提供Project Specification所列canonical latest Holdings API路徑，同時保留legacy FastAPI contract。
- 對可觀察的source-date、denominator及大於100%異常發出清晰warning；不臆測corporate action。
- 加入deterministic offline product/API acceptance tests，覆蓋fresh、LKG、limit、欄位round-trip、diagnostics及legacy compatibility。

Acceptance：

- [x] Latest Holdings公開資料包含原participant identity/name、`pct_of_issued`、`pct_of_ccass`、累計百分比及完整summary denominator metadata。
- [x] `issued_shares_as_of`有誠實、可驗證的來源日期語義；缺失或日期不一致不會靜默當作完整。
- [x] Product validation核對identity、日期、rank、duplicate、participant count、denominator及完整度，錯誤／warning均可稽核。
- [x] `holdings_limit`只切片rows；summary、participant count、Top 5／Top 10維持完整snapshot計算結果。
- [x] Canonical Holdings API可直接使用，legacy endpoint保持相容；沒有breaking FastAPI、MCP或Streamlit contract。
- [x] Freshness、persistent LKG及source diagnostics回歸測試通過。
- [x] 沒有新source、Changes、Big Changes、Concentration、generic framework、UI美化或下一階段功能。
- [x] Ruff、Full Pytest、`git diff --check`、Markdown links、UTF-8、secrets及private-path scans全部通過。

Completion evidence：

- Product contract：`HoldingRow`以additive方式公開canonical `participant_name`及`pct_of_ccass`；`HoldingsSummary`公開`issued_shares_as_of`，legacy `participant`及既有endpoint保持可用。
- Validation：新增只限Latest Holdings的product validator；核對code、verified date、timezone、rank、duplicate、participant count、完整rows總數、issued／CCASS／non-CCASS arithmetic、row/cumulative/Top 5/Top 10 percentage basis及denominator date。缺失／不一致／>100%明確標`PARTIAL`或`INVALID_SCHEMA`，不臆測corporate action。
- Limit invariant：`CcassService`及collector先取完整snapshot並驗證，最後才切`holdings_limit` rows；summary、participant count及Top 5／Top 10保持完整snapshot口徑。
- Persistence/freshness：public欄位經normalized SQLite round-trip；`PRODUCT_VALIDATION: PARTIAL`不可promote為完整LKG或collector `SUCCESS`；既有`FRESH`／`STALE_LKG`／`UNAVAILABLE`語義保持。
- API／delivery：新增canonical `GET /api/v1/stocks/{stock_code}/holdings`並保留`GET /api/v1/ccass/{code}`；OpenAPI及JSON有additive欄位測試。Collector CSV、Google CSV optional import、範本及Markdown Holdings report均帶新欄位。
- Sources／scope：沒有新增source、migration、MCP tool、Streamlit control或其他section；Webb-site仍只批准latest Holdings，Google Drive CSV仍是核准configured import flow；HKEX SDW automation及未審核來源保持disabled／unverified。
- Validation result：Ruff passed；targeted Pytest 95 passed；Full Pytest 137 passed（1個既有Starlette/httpx deprecation warning）；`git diff --check`及文件／安全scans通過。
- Product impact：Repository可宣告`Latest Holdings Completed`；合法live/golden及多日production evidence仍屬Phase 1／最終acceptance，不以synthetic fixture冒充。

明確不在本工作：

- 不實作Changes、Big Changes、Concentration、Rainbow、Price History、HKEX Announcements、ChatGPT Project、AI分析或UI美化。
- 不新增source adapter、HKEX SDW automation、credentials、付費服務、migration或generic cross-feature framework。
- 不預先設計下一個功能、不修改Product Direction、不開始P1-08或下一輪Gap Analysis。

Dependencies/risks：

- 依賴已批准P1-01至P1-06；P1-06批准commit為`172e50f0fd367af62343b1125c0da3fd729cfd39`。
- `pct_of_ccass`只可在`total_in_ccass_shares`有效時產生；`issued_shares_as_of`不可由latest serve time或未證實日期冒充。
- Corporate-action diagnostics只依可觀察的denominator日期／百分比異常，不作事件歸因。
- 公開欄位及canonical endpoint只可additive；legacy response語義、MCP及Streamlit既有使用方式必須保持。
- 若發現需要breaking schema、destructive migration、新來源條款、credentials或付費服務，立即停止並回報。

Remaining manual step：

- CTO Review／批准P1-07；批准前不開始P1-08、Gap Analysis或下一個TASK。

## Decisions and constraints

- 平台只輸出客觀資料；不做投資評分、買賣建議、莊家／收貨／派貨結論。
- DisclosureTracker只作UI/功能參考，不是資料依賴。
- Cache/last-known-good必須標cached/stale/data date，不冒充live。
- Webb-site目前只驗證latest Holdings；Google Drive/CSV是已核准的安全import flow及exact-date來源能力，不等於已有production history/golden驗收。
- HKEX SDW automation及所有未審核來源維持未註冊／disabled／unverified；不得自行啟用。
- Windows schedule、production credentials、付費服務、source legality ambiguity及破壞性／公開schema變更必須停下請示。

## Approved task evidence

```text
Task: P1-01 — Source-neutral normalized historical snapshot foundation
Status: complete; CTO approved
Commit: ec09374
Tests: Ruff passed; Pytest 64 passed; git diff --check and repository secrets/private-path scan passed.
```

```text
Task: P1-02 — Source-neutral collector orchestration and persistent run accounting
Status: complete; CTO approved
Commit: d8a480e
Tests: Ruff passed; Pytest 78 passed; git diff --check and repository secrets/private-path scan passed.
```

```text
Task: P1-03 — Resumable source-neutral CCASS historical backfill
Status: complete; CTO approved
Commits: f9fcf02, 6152135
Tests: Ruff passed; full Pytest 88 passed; CLI smoke, git diff --check, credential-pattern scan and private-path scan passed.
Active sources: Only approved Google Drive/CSV import flow provides exact requested-date history; Webb-site remains latest-only.
Golden validation: Synthetic offline 01592 fixtures only; no live scraping or production-data claim.
Public acceptance: Existing FastAPI/MCP/Streamlit contracts were unchanged and passed regression tests.
```

```text
Task: P1-04 — Configuration-driven source registry and capability/audit metadata
Status: complete; CTO approved
Commit: 7b6931679912525f429b06ac5fc033adb9bc2456
Tests: Ruff passed; targeted Pytest 31 passed; full Pytest 94 passed; git diff --check, Markdown links, UTF-8/replacement-character, secrets and private-path scans passed.
Active sources: Webb-site is approved for latest Holdings only. Google Drive CSV is approved only as a configured import flow with truthful latest/requested-date/historical/manual-import capabilities.
Disabled/unverified sources: HKEX SDW, HKEXnews, DI/SDI, price and supplemental sources remain unregistered or disabled/unverified; no automation was added.
Golden validation: Synthetic offline 01592 fixtures only; no live scraping, production history or golden-data claim.
Public acceptance: FastAPI, MCP and Streamlit contracts were unchanged.
```

```text
Task: P1-05 — Guarded and parser-separated Webb-site latest Holdings adapter
Status: complete; CTO approved
Commit: 9e833214f634f42e8e64d8a149d57976b5c1b1aa
Tests: Ruff passed; full Pytest 120 passed; diff, Markdown, UTF-8, secrets, private-path, scope and public-contract scans passed.
Active sources: Webb-site remains approved for latest Holdings only; Google Drive CSV remains the approved configured import flow.
Disabled/unverified sources: No new source; HKEX SDW automation and unreviewed sources remain disabled/unregistered.
Golden validation: Synthetic offline fixtures only; no live/golden claim.
Public acceptance: Existing FastAPI, MCP and Streamlit contracts were unchanged.
```

```text
Task: P1-06 — Persistent LKG and Freshness for Latest Holdings
Status: complete; CTO approved
Commit: 172e50f0fd367af62343b1125c0da3fd729cfd39
Tests: Ruff passed; targeted Pytest 49 passed; full Pytest 130 passed; diff, Markdown, UTF-8, secrets, private-path, database/migration, scope and public-contract scans passed.
Active sources: Existing approved Webb-site latest Holdings and configured Google Drive CSV only; persistent LKG is source-neutral normalized storage, not a new source.
Disabled/unverified sources: No new source; HKEX SDW automation and all unreviewed sources remain disabled/unregistered.
Golden validation: Synthetic offline fixtures only; no live/golden or production multi-day claim.
Public acceptance: Public FastAPI, MCP, Streamlit and CcassResponse field contracts remain unchanged.
```

```text
Task: P1-07 — Complete Latest Holdings Vertical Slice
Status: complete; awaiting CTO Review
Commit: current P1-07 commit
Tests: Ruff passed; targeted Pytest 95 passed; full Pytest 137 passed; diff, Markdown, UTF-8, secrets, private-path, scope and migration scans passed.
Files: Holdings public models/product validation, service/LKG/collector, approved source field mapping, canonical API, report/CSV template, ROADMAP/TASK and deterministic offline tests.
Active sources: Existing approved Webb-site latest Holdings and configured Google Drive CSV only; no source was added or enabled.
Disabled/unverified sources: HKEX SDW automation and all unreviewed sources remain disabled/unregistered.
Golden validation: Synthetic offline fixtures only; no live/golden or production multi-day claim.
Public acceptance: Latest Holdings is complete with additive fields and canonical API; legacy FastAPI, MCP and Streamlit usage remains compatible.
Remaining manual step: CTO Review／批准P1-07.
```

完成active task時附加：

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
