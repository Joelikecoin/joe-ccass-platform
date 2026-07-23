# Task Board

> 本檔是唯一的當前工作、狀態、驗收證據與下一步清單。長期產品要求見 [`docs/PROJECT_SPEC.md`](docs/PROJECT_SPEC.md)，phase順序與完整Gap Analysis見 [`docs/ROADMAP.md`](docs/ROADMAP.md)。

## Working baseline

- Branch：`main`
- Original requested code baseline：`fad4411`
- Latest approved baseline：`03e7dc73b324a642aed39bb2500f5228a0473970`（P1-07；CTO approved）
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
- [x] P1-07：完整Latest Holdings產品驗證、canonical API、diagnostics、denominator metadata及limit invariant；commit `03e7dc73b324a642aed39bb2500f5228a0473970`，CTO approved。

## Post-P1-04 Gap Analysis（historical baseline）

- Done：6個功能單位。
- Partial：19個功能單位。
- Not Started：8個功能單位。
- Remaining Gaps：27個，已按Phase gate、前置依賴、風險及最小完整vertical slice重新排序，見 [`docs/ROADMAP.md`](docs/ROADMAP.md#remaining-gaps-優先序)。
- 本節是P1-04後的historical Gap Analysis，未因P1-08 delivery重算；目前產品證據以唯一Active Task為準，正式Phase狀態待CTO批准後另作Gap Analysis。
- P1-01至P1-07已由CTO批准；P1-08只完成Changes產品切片，不開始下一個TASK或其他section。

## 唯一最高優先工作

### [x] P1-08 — Complete Changes Vertical Slice

優先理由：P1-01至P1-07已提供approved source registry、完整Latest Holdings產品驗證、exact-date normalized snapshots及persistent storage；本工作只把兩個已保存完整snapshots之間的客觀participant changes收斂成可直接使用的產品切片。

本工作範圍：

- 重用既有source fetch／parser／normalize／validation／collector／backfill及normalized SQLite snapshot流程，不新增source或另一套ingestion infrastructure。
- 只比較同一approved active source的兩個exact-date snapshots；兩者必須完整、非stale、股票及issue identity一致，並通過Latest Holdings產品驗證。
- 輸出participant、shares before／after／change、percent before／after／percentage-point change、relative change、new／removed flags、compare／snapshot dates及安全source provenance。
- 提供canonical Changes JSON API及Changes專用Markdown report；既有Latest Holdings、legacy FastAPI、MCP及Streamlit contract保持不變。
- 加入deterministic offline product/API/report/fail-loud tests；fixtures只證明工程行為，不作production evidence。

Acceptance：

- [x] Source → Fetch → Parse → Normalize → Validate → Persist沿用已批准Holdings pipeline；Changes只讀取persisted exact snapshots，不臆造歷史資料。
- [x] 完整Changes產品輸出包含指定欄位、summary、diagnostics、percentage basis及兩邊source metadata。
- [x] Participant新增／移除只在兩邊均為完整snapshot時判定；partial snapshot不會把缺失rows當作零。
- [x] Missing pair、非正向日期、partial、stale、identity conflict及未通過product validation均fail loud並回傳structured `PlatformError`。
- [x] Canonical `GET /api/v1/stocks/{stock_code}/changes`及additive Markdown report endpoint可直接使用。
- [x] 沒有migration、Changes結果另存、source adapter、Big Changes、Concentration、generic comparison framework或其他scope drift。
- [x] Latest Holdings、legacy API、MCP及Streamlit regression保持通過。
- [x] Ruff、Full Pytest、`git diff --check`、Markdown links、UTF-8及secrets/private-path scans通過。

Completion evidence：

- Product contract：additive `ChangesResponse`以metadata-first形式公開兩個snapshot日期、issued-shares percentage basis、安全provenance、兩邊issued shares／as-of與source warnings、summary、participant changes及complete diagnostics。
- Validation：只選registry內approved active source；要求同source exact pair、完整、非stale、identity一致並重用`finalize_latest_holdings`完整產品驗證。Invalid／partial／stale資料不會產生Changes結果。
- Calculation：以stable participant ID作union；完整snapshot中真正缺席才標`new`／`removed`。輸出shares delta、percentage-point delta及有定義時的relative change；denominator變更只發warning，不作corporate-action歸因。
- Persistence：Not Changed；重用`ccass_snapshots`／`ccass_holdings`及raw provenance，Changes為deterministic read projection，不新增table或migration。
- API／report：新增canonical JSON endpoint及Changes專用Markdown endpoint；現有Holdings、legacy report、MCP及Streamlit contract未修改。
- Sources：沒有新增或啟用source；Webb-site仍只批准latest Holdings，Google Drive CSV仍只按既有配置／audit能力使用；HKEX SDW及未審核來源保持disabled／unregistered。
- Validation result：targeted Pytest 20 passed；Full Pytest 149 passed（1個既有Starlette/httpx deprecation warning）；Ruff及最終文件／安全scans通過。
- Product evidence：deterministic offline fixtures證明正常、new／removed、relative／percentage changes、missing pair、partial、stale、denominator及identity行為；不宣稱live／golden／production evidence。

明確不在本工作：

- 不實作Big Changes、Concentration、Rainbow、Price History、HKEX Announcements、Corporate Action、AI Analysis或UI。
- 不新增source adapter、generic event engine、generic comparison framework、migration或未來Milestone infrastructure。
- 不修改Product Direction、`docs/ROADMAP.md`，不開始P1-09或宣告Phase完成。

Dependencies/risks：

- 批准基準為`03e7dc73b324a642aed39bb2500f5228a0473970`；依賴P1-01至P1-07既有normalized complete snapshots。
- Production使用前必須已有同一approved active source的兩個exact-date、完整、非stale snapshots；API不會以latest、LKG、插值、fixture或跨source拼接補足缺口。
- issued-shares denominator若在兩日期間改變會明確warning；本Task不推測corporate action原因。
- 若需要新source、breaking contract、destructive migration、credentials或付費服務，必須停止並由CTO另行批准。

Remaining manual step：

- CTO Review／批准P1-08；批准前不開始P1-09、Gap Analysis或下一個TASK。

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
Status: complete; CTO approved
Commit: 03e7dc73b324a642aed39bb2500f5228a0473970
Tests: Ruff passed; targeted Pytest 95 passed; full Pytest 137 passed; diff, Markdown, UTF-8, secrets, private-path, scope and migration scans passed.
Files: Holdings public models/product validation, service/LKG/collector, approved source field mapping, canonical API, report/CSV template, ROADMAP/TASK and deterministic offline tests.
Active sources: Existing approved Webb-site latest Holdings and configured Google Drive CSV only; no source was added or enabled.
Disabled/unverified sources: HKEX SDW automation and all unreviewed sources remain disabled/unregistered.
Golden validation: Synthetic offline fixtures only; no live/golden or production multi-day claim.
Public acceptance: Latest Holdings is complete with additive fields and canonical API; legacy FastAPI, MCP and Streamlit usage remains compatible.
Remaining manual step: Complete; CTO approved.
```

```text
Task: P1-08 — Complete Changes Vertical Slice
Status: complete; awaiting CTO Review
Commit: P1-08 delivery commit containing this evidence
Tests: Ruff passed; targeted Pytest 20 passed; full Pytest 149 passed; diff, Markdown, UTF-8, secrets and private-path scans passed.
Files: additive Changes models/service/API/report and deterministic offline Changes acceptance tests; TASK evidence only.
Active sources: Existing approved Webb-site latest Holdings and configured Google Drive CSV only; Changes reads exact persisted pairs from one approved active source.
Disabled/unverified sources: No new source; HKEX SDW automation and all unreviewed sources remain disabled/unregistered.
Golden validation: Synthetic offline fixtures only; no live/golden or production-data claim.
Public acceptance: Canonical Changes JSON and Markdown delivery added; existing Holdings, legacy FastAPI, MCP and Streamlit contracts remain compatible.
Remaining manual step: CTO Review／批准P1-08.
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
