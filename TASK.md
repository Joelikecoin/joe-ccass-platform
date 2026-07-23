# Task Board

> 本檔是唯一的當前工作、狀態、驗收證據與下一步清單。長期產品要求見 [`docs/PROJECT_SPEC.md`](docs/PROJECT_SPEC.md)，phase順序與完整Gap Analysis見 [`docs/ROADMAP.md`](docs/ROADMAP.md)。

## Working baseline

- Branch：`main`
- Original requested code baseline：`fad4411`
- Latest approved baseline：`9e833214f634f42e8e64d8a149d57976b5c1b1aa`（P1-05；CTO approved）
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

## Post-P1-04 Gap Analysis

- Done：5個功能單位。
- Partial：20個功能單位。
- Not Started：8個功能單位。
- Remaining Gaps：28個，已按Phase gate、前置依賴、風險及最小完整vertical slice重新排序，見 [`docs/ROADMAP.md`](docs/ROADMAP.md#remaining-gaps-優先序)。
- Phase 1維持In Progress：registry、normalized persistence、collector idempotency及backfill resume/retry已完成；合法active source多日真實snapshots、golden核對及Holdings／Changes／Big Changes／Concentration完整vertical slices仍未滿足。
- P1-05已由CTO批准；本輪只完成P1-06 persistent LKG／freshness，不重排Remaining Gaps或提前實作其他section。

## 唯一最高優先工作

### [x] P1-06 — Persistent LKG and Freshness for Latest Holdings

優先理由（實作前）：P1-05已建立可信latest Holdings fetch/parser boundary，但process-memory cache不能跨process restart，亦不足以在來源暫時失敗時提供可稽核的資料日期、retrieval time、served time、age及原始錯誤。P1-06只補上source-neutral persistent normalized LKG與freshness語義，讓collector及既有service在不改公開contract下形成穩定latest Holdings vertical slice。

本工作範圍：

- 以既有`NormalizedSnapshotRepository`保存完整、identity/schema/parser驗證通過的latest Holdings normalized snapshot；沒有migration。
- `CcassService`及collector共用persistent LKG wrapper；公開dependency使用`CCASS_SQLITE_PATH`對應的既有SQLite store。
- 以既有`CcassResponse.metadata.cached`及structured warnings區分`FRESH`、`STALE_LKG`、`UNAVAILABLE`，保留原snapshot date／retrieved timestamp並另列served time、age及原始source error。
- 只有`SOURCE_TIMEOUT`、`SOURCE_UNAVAILABLE`、`SOURCE_RATE_LIMITED`及暫時`SOURCE_FORBIDDEN`可回退；HTML/login、schema/parser、identity、corrupt/incompatible、disabled、historical/date及其他integrity errors一律fail loudly。
- 完整已驗證live snapshot才可更新LKG；partial、stale、validation failure及transaction failure不可覆寫舊good snapshot。
- Collector把`STALE_LKG`記作`PARTIAL`，保留source error record，CSV清楚輸出cached/freshness/error/date；stale服務不新增snapshot。
- Google CSV將timeout、403、429、5xx／network failure分類為transient；HTML/login、size、URL、CSV/schema/row failure仍是禁止LKG回退的`DATA_SOURCE_ERROR`。

Acceptance：

- [x] Process restart後可由normalized SQLite讀取同一完整LKG；無LKG時保留原error code並標`UNAVAILABLE`。
- [x] Fresh success標`FRESH`；stale fallback標`STALE_LKG`及cached，保留原data date、retrieved time、served time、age、source error code/message。
- [x] Freshness age由timezone-aware `served_at - fetched_at`計算，使用config/registry的`HOLDINGS_LKG_MAX_AGE_SECONDS`；過期回`DATA_STALE`。
- [x] 只有完整、非partial、registered source identity、目前parser及schema驗證通過的snapshot可成為LKG。
- [x] Parser/schema/identity/source-changed/corrupt/incompatible/disabled/historical errors不使用LKG；partial及storage failure不promote。
- [x] Collector stale run為`PARTIAL`、snapshot count不變、source error及CSV freshness evidence完整；batch isolation及既有atomic export保持。
- [x] Historical requested-date/backfill flow沒有接入latest LKG；沒有新增source、endpoint、UI、migration或公開schema欄位。
- [x] FastAPI、MCP、Streamlit及`CcassResponse`欄位contract不變；API response只使用既有metadata/warnings表達freshness。
- [x] 全部測試完全離線；Ruff、Full Pytest、diff、docs、安全、database及public-contract scans須全通過後才提交。

Completion evidence：

- Persistence：直接重用P1-01 transactional normalized repository及完整snapshot invariants，無schema migration；完整live response先以registry source ID/parser version驗證，再以full collection limit保存，最後才按caller `holdings_limit`切片。
- Freshness：新增internal `PersistentLatestHoldingsSource`及`FreshnessStatus`；stale warning帶`SOURCE_ERROR_CODE`、`SOURCE_ERROR_MESSAGE`、`LKG_RETRIEVED_AT`、`LKG_AGE_SECONDS`及`SERVED_AT`，沒有新增公開model欄位。
- Failure policy：transient allowlist固定為timeout/unavailable/rate-limited/temporarily-forbidden；`DATA_SOURCE_ERROR`及所有integrity/date/disabled errors禁止fallback。Stored LKG需source identity、parser version、schema v1、complete/non-stale及age全部通過。
- Collector：service在non-dry-run共用collector repository；stale response不save，run/item記`PARTIAL`並另存原source error；atomic CSV以本輪response overlay只呈現已明確標記的stale資料。
- Restart／atomicity：offline tests以新repository instance證明跨process-style restart；partial與模擬transaction failure均沒有LKG row，舊good snapshot不被改寫。
- Public contract：`app/models.py`、`app/api.py`、`app/mcp_server.py`及`app/streamlit_ui.py`沒有修改；沒有migration或新source。
- Validation：Ruff passed；targeted Pytest 49 passed；Full Pytest 130 passed（1個既有Starlette/httpx deprecation warning）；`git diff --check`、Markdown links、UTF-8/replacement character、secrets、private-path、database/migration、Scope Drift及public-contract scans全部通過。
- Limitations：仍無cross-source conflict resolver、public source status、Holdings新欄位、history UI、合法live/golden或多日production evidence；這些不在P1-06。

明確不在本工作：

- 不實作Holdings UI、新public `pct_of_ccass`／issued-shares-as-of欄位、Changes、Big Changes、Concentration、Rainbow、Price、Announcements或downloads擴展。
- 不新增source、requested-date/multi-day adapter、HKEX SDW automation、login/CAPTCHA/cookie或反爬繞過。
- 不新增FastAPI/MCP endpoint、Streamlit control、public source status或cross-source conflict UI。
- 不作migration、live scraping、production data／golden驗收、scheduler/deployment或下一輪Gap Analysis。

Dependencies/risks：

- 依賴已批准P1-01至P1-05；P1-05批准commit為`9e833214f634f42e8e64d8a149d57976b5c1b1aa`。
- `fetched_at`是LKG retrieval time，不得改成serve time；data date不得因fallback而更新。
- SQLite write failure必須保持transactional；可服務已驗證live response但須明確`LKG_PERSISTENCE_ERROR`，不可假稱已持久化。
- `SOURCE_FORBIDDEN`只按目前registry approved source的暫時403分類使用；disabled/audit failure仍禁止fallback。
- 若需breaking public schema、destructive migration、新source條款判斷、credentials或付費服務，必須停下請示；本實作沒有觸發。

Remaining manual step：

- CTO Review／批准P1-06；批准前不開始Gap Analysis或下一個TASK。
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
Status: complete; awaiting CTO Review
Commit: current P1-06 commit
Tests: Ruff passed; targeted Pytest 49 passed; full Pytest 130 passed; diff, Markdown, UTF-8, secrets, private-path, database/migration, scope and public-contract scans passed.
Active sources: Existing approved Webb-site latest Holdings and configured Google Drive CSV only; persistent LKG is source-neutral normalized storage, not a new source.
Disabled/unverified sources: No new source; HKEX SDW automation and all unreviewed sources remain disabled/unregistered.
Golden validation: Synthetic offline fixtures only; no live/golden or production multi-day claim.
Public acceptance: Public FastAPI, MCP, Streamlit and CcassResponse field contracts remain unchanged.
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
