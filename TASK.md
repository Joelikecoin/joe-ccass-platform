# Task Board

> 本檔是唯一的當前工作、狀態、驗收證據與下一步清單。長期產品要求見 [`docs/PROJECT_SPEC.md`](docs/PROJECT_SPEC.md)，phase順序與完整Gap Analysis見 [`docs/ROADMAP.md`](docs/ROADMAP.md)。

## Working baseline

- Branch：`main`
- Original requested code baseline：`fad4411`
- Latest approved baseline：`9800d7a6ed46893bcffecc8e604eb23c23eb4acf`（P1-08；CTO approved）
- Specification baseline reviewed：`67e35e5`
- Functional audit：2026-07-23，見 [`docs/ROADMAP.md`](docs/ROADMAP.md#repository-功能審核)
- Current phase：Phase 1 — Data foundation and objective CCASS sections
- Golden stock：`01592`
- Status updated：2026-07-24 (Asia/Hong_Kong)

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
- [x] P1-08：完整Changes產品、exact-pair validation、canonical API、diagnostics及Markdown report；commit `9800d7a6ed46893bcffecc8e604eb23c23eb4acf`，CTO approved。

## Post-P1-04 Gap Analysis（historical baseline）

- Done：6個功能單位。
- Partial：19個功能單位。
- Not Started：8個功能單位。
- Remaining Gaps：27個，已按Phase gate、前置依賴、風險及最小完整vertical slice重新排序，見 [`docs/ROADMAP.md`](docs/ROADMAP.md#remaining-gaps-優先序)。
- 本節是P1-04後的historical Gap Analysis，未因P1-08 delivery重算；目前產品證據以唯一Active Task為準，正式Phase狀態待CTO批准後另作Gap Analysis。
- P1-01至P1-08已由CTO批准；P1-09只完成Big Changes產品切片，不開始下一個TASK或其他section。

## 唯一最高優先工作

### [x] P1-09 — Complete Big Changes Vertical Slice

優先理由：P1-08已提供approved active source exact-pair selection、完整validation、participant comparison、metadata、provenance、diagnostics及warnings；P1-09只需把既有Changes結果依configuration-driven絕對shares門檻篩選成完整產品能力。

本工作範圍：

- 新增薄的`BigChangesService`，只呼叫一次`ChangesService.get_changes()`並篩選其結果；不重新讀取snapshots、不複製participant comparison。
- 使用inclusive規則`abs(shares_change) >= threshold_shares`，並排除零變化；預設值由`BIG_CHANGES_THRESHOLD_SHARES`／`Settings`提供，API可作positive query override。
- 完整保留P1-08 metadata、provenance、diagnostics、source warnings、denominator dates及settlement note。
- 提供canonical Big Changes JSON API及專用Markdown report。
- 加入deterministic offline product、threshold、fail-loud、report及API regression tests。

Acceptance：

- [x] Big Changes以P1-08 `ChangesResponse`為唯一comparison輸入，沒有重算participant union／delta／status。
- [x] Default threshold由configuration提供，程式service／API沒有寫死產品門檻；query override為positive且boundary inclusive。
- [x] 正常、empty result及threshold boundary均有deterministic tests。
- [x] Partial、stale、identity conflict及missing pair errors由Changes原樣fail loud傳遞。
- [x] JSON及Markdown endpoints為additive，既有Holdings、Changes、legacy API、MCP及Streamlit contracts保持相容。
- [x] 沒有storage schema、migration、source、background job或generic analytics framework。
- [x] Ruff、Full Pytest、`git diff --check`、Markdown links、UTF-8及secrets/private-path scans通過。

Completion evidence：

- Reuse：`BigChangesService`委派P1-08 `ChangesService`取得完整結果，再只執行threshold filter；spy test證明每次產品查詢只呼叫一次Changes。
- Configuration：新增`Settings.big_changes_threshold_shares`及`BIG_CHANGES_THRESHOLD_SHARES`範例；Settings要求positive。API `threshold_shares`為optional positive override。
- Product contract：additive `BigChangesResponse`重用`ChangesMetadata`、`ChangeRow`及`ChangesDiagnostics`，另提供threshold及filtered status counts。
- Validation／honesty：P1-08 partial、stale、date及identity validation完全保留；沒有結果時回傳完整metadata／diagnostics及空list，不把fixture或missing data冒充產品結果。
- API／report：新增`GET /api/v1/stocks/{stock_code}/big-changes`及`.../big-changes/report`；Markdown列明absolute inclusive threshold、exact dates、source、denominator及warnings。
- Persistence：Not Changed；Big Changes為read-only projection，沒有table、migration或結果另存。
- Sources：沒有新增或啟用source；HKEX SDW及未審核來源保持disabled／unregistered。
- Validation result：targeted Pytest 30 passed；Full Pytest 159 passed（1個既有Starlette/httpx deprecation warning）；Ruff及最終文件／安全scans通過。
- Product evidence：只使用deterministic offline fixtures證明工程行為，不宣稱live／golden／production evidence。

明確不在本工作：

- 不實作Concentration、Rainbow、Charts、Trend、multi-date comparison、corporate-action inference或cross-source merge。
- 不新增storage、migration、background job、source、generic analytics framework或未批准infrastructure。
- 不修改`docs/ROADMAP.md`，不開始P1-10或宣告Phase完成。

Dependencies/risks：

- 批准基準為`9800d7a6ed46893bcffecc8e604eb23c23eb4acf`；完全依賴P1-08 Changes的exact-pair及fail-loud語義。
- Threshold只按absolute `shares_change`篩選，不作百分比、成交、公告或corporate-action推論。
- Production仍必須預先具備同一approved active source的兩個完整、非stale exact-date snapshots。
- 若需要new source、breaking contract、destructive migration、credentials或付費服務，必須停止並由CTO另行批准。

Remaining manual step：

- CTO Review／批准P1-09；批准前不開始P1-10、Gap Analysis或下一個TASK。

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
Status: complete; CTO approved
Commit: 9800d7a6ed46893bcffecc8e604eb23c23eb4acf
Tests: Ruff passed; targeted Pytest 20 passed; full Pytest 149 passed; diff, Markdown, UTF-8, secrets and private-path scans passed.
Files: additive Changes models/service/API/report and deterministic offline Changes acceptance tests; TASK evidence only.
Active sources: Existing approved Webb-site latest Holdings and configured Google Drive CSV only; Changes reads exact persisted pairs from one approved active source.
Disabled/unverified sources: No new source; HKEX SDW automation and all unreviewed sources remain disabled/unregistered.
Golden validation: Synthetic offline fixtures only; no live/golden or production-data claim.
Public acceptance: Canonical Changes JSON and Markdown delivery added; existing Holdings, legacy FastAPI, MCP and Streamlit contracts remain compatible.
Remaining manual step: Complete; CTO approved.
```

```text
Task: P1-09 — Complete Big Changes Vertical Slice
Status: complete; awaiting CTO Review
Commit: P1-09 delivery commit containing this evidence
Tests: Ruff passed; targeted Pytest 30 passed; full Pytest 159 passed; diff, Markdown, UTF-8, secrets and private-path scans passed.
Files: threshold setting/example, additive Big Changes models/service/API/report and deterministic offline acceptance tests; TASK evidence only.
Active sources: Existing approved Webb-site latest Holdings and configured Google Drive CSV only; Big Changes delegates exact-pair retrieval to P1-08 Changes.
Disabled/unverified sources: No new source; HKEX SDW automation and all unreviewed sources remain disabled/unregistered.
Golden validation: Synthetic offline fixtures only; no live/golden or production-data claim.
Public acceptance: Canonical Big Changes JSON and Markdown delivery added; existing Holdings, Changes, legacy FastAPI, MCP and Streamlit contracts remain compatible.
Remaining manual step: CTO Review／批准P1-09.
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
