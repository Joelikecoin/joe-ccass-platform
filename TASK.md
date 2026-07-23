# Task Board

> 本檔是唯一的當前工作、狀態、驗收證據與下一步清單。長期產品要求見 [`docs/PROJECT_SPEC.md`](docs/PROJECT_SPEC.md)，phase順序與完整Gap Analysis見 [`docs/ROADMAP.md`](docs/ROADMAP.md)。

## Working baseline

- Branch：`main`
- Original requested code baseline：`fad4411`
- Latest approved baseline：`5e3485383a88a168544324530669649cb1f17a55`（Post-P1-04 Gap Analysis；CTO approved）
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

## Post-P1-04 Gap Analysis

- Done：5個功能單位。
- Partial：20個功能單位。
- Not Started：8個功能單位。
- Remaining Gaps：28個，已按Phase gate、前置依賴、風險及最小完整vertical slice重新排序，見 [`docs/ROADMAP.md`](docs/ROADMAP.md#remaining-gaps-優先序)。
- Phase 1維持In Progress：registry、normalized persistence、collector idempotency及backfill resume/retry已完成；合法active source多日真實snapshots、golden核對及Holdings／Changes／Big Changes／Concentration完整vertical slices仍未滿足。
- P1-05已完成既有Webb-site latest Holdings guarded fetch／純parser邊界及離線vertical integration；功能仍維持Partial並等待CTO Review，不提前擴展新sections或進行golden live驗收。

## 唯一最高優先工作

### [x] P1-05 — Guarded and parser-separated Webb-site latest Holdings adapter

優先理由（實作前）：Webb-site是目前唯一approved、active的live CCASS來源，但`WebbsiteClient`當時把network fetch、content handling、identity resolution及Holdings parsing耦合在同一module，亦未在parse前完整驗證content type／login或error HTML。這是Phase 1真實Holdings、多日collector、persistent LKG及golden核對的共同資料誠信前置。先完成這個小而完整的既有latest Holdings adapter slice，可降低source drift、challenge page及oversize response被誤解析的風險；不新增來源或能力。

目標：把既有Webb-site latest Holdings路徑整理為有明確guarded fetch result及純離線parser的source boundary，讓單一stock-code request在不改公開contract的前提下，安全產生與目前兼容的`CcassResponse`，並由registry/config提供實際operational metadata與限制。

Product Impact：

- Latest Holdings現可由stock code經單次受保護request、頁內code + hidden issue ID驗證、純parser及normalized output完整流入collector。
- 現可可信提供participant name／ID、rank、shares、source percentage、snapshot date、issue ID、source reference、retrieved timestamp、cache狀態及limitations，並保持完整snapshot totals／Top 5／Top 10先於`holdings_limit`切片。
- 完整Holdings產品頁仍欠public `pct_of_ccass`、issued-shares-as-of、persistent LKG/freshness、合法live/golden evidence及後續UI交付；本任務沒有把Holdings功能改判Done。

本工作範圍：

- 分離Webb-site network fetch/content guard與Holdings／identity parser；parser不得依賴httpx、env、database或自行發network request；
- 保留目前stock-code route的一次上游request及頁內stock code + hidden issue ID雙重identity驗證，避免重新引入兩次serial request／`SOURCE_TIMEOUT`風險；
- 在parse前驗證HTTP status、允許的HTML content type、declared/actual size、login/challenge/error page及空／不完整body；
- 保留並集中現有403、429、5xx、challenge、timeout、network、source-changed、parse及too-large structured errors，不把失敗回空Holdings；
- 讓adapter實際使用registry/config的timeout、size、bounded retry／mirror fallback、minimum interval、cache及parser/schema metadata，不在fetch/parser重複定義capability；
- 保持完整snapshot計算先於`holdings_limit`切片，並維持現有identity、summary、Top 5/10、T+2、warnings及source attribution語義；
- 加入deterministic offline parser fixtures／tests及mocked network guard tests，覆蓋正常、malformed、wrong identity、wrong content type、challenge/login HTML、oversize及mirror failure isolation。

Acceptance：

- [x] Webb-site latest Holdings parser是純函式／純元件，可只靠saved fixture及明確context離線執行；parser內沒有network、settings、env或database存取。
- [x] Fetch層在parser前完成status、content type、declared/actual size、challenge/login/error page及body完整性guard；錯誤保持deterministic `PlatformError`。
- [x] 正常查詢仍只作一次stock-code Holdings上游request，並核對requested code與hidden issue ID；不得猜issue ID或靜默接受另一股票頁。
- [x] Primary/fallback mirror、timeout、rate/minimum interval、bounded attempts、cache及安全logging保持兼容；不得新增高頻probe或無限retry。
- [x] Registry繼續只宣稱`webbsite`的latest Holdings能力；parser/schema version與實際adapter一致，不新增requested-date、historical、Changes、Concentration或Price capability。
- [x] `holdings_limit`只影響回傳列數；participant count、totals及Top 5/10仍由完整已解析rows計算。
- [x] `auto|webbsite|google_drive_csv` routing、CSV-only isolation、collector及backfill現有行為全部通過regression。
- [x] 不記錄完整source URL/query、API key、Cookie、authorization或私人路徑；safe errors/logging tests通過。
- [x] 不修改公開FastAPI、MCP、Streamlit或`CcassResponse` contract，不新增endpoint/UI或migration。
- [x] Ruff、完整Pytest、`git diff --check`、Markdown/UTF-8、secrets及private-path scans全部通過後才可commit/push。

Completion evidence：

- Parser：新增純`app.sources.webbsite_parser`，只接收HTML及requested code，嚴格驗證identity、summary/table欄位、row數值、snapshot date、duplicates及>100%保留規則。
- Adapter：`WebbsiteClient`使用registry policy執行status/content-type/declared+streamed size/body/login/challenge/error guards、bounded retries、mirror isolation、minimum interval及process cache，再組裝既有`CcassResponse`。
- Identity：latest route維持一次`sc=` request；不得猜issue ID，缺少、無效、衝突或stock mismatch均Fail Loud。
- Fixtures／tests：4個明確標示synthetic的offline HTML fixtures；新增26個tests，targeted 61 passed，Full Pytest 120 passed；包含adapter → parser → normalized result → collector vertical integration。
- Registry：`webbsite`仍只宣稱latest Holdings；parser version升至`2`，HKEX SDW及未審核來源沒有新增或啟用。
- Public contract：`app/api.py`、`app/models.py`、`app/mcp_server.py`及`app/streamlit_ui.py`沒有修改；沒有migration。
- Limitations：snapshot date缺失時保留`None`並明確warning；來源percentage只保留頁面issued-share basis；無persistent LKG、history或live/golden claim。
- Validation：Ruff passed；targeted Pytest 61 passed；Full Pytest 120 passed（1個既有deprecation warning）；`git diff --check`、Markdown links、UTF-8/replacement character、secrets、private-path、Scope Drift及public contract scans全部通過。

明確不在本工作：

- 不新增或啟用HKEX SDW、HKEXnews、DI/SDI、price、supplemental source或任何新adapter。
- 不新增Webb-site requested-date/history、Changes、Big Changes、Concentration、Company或Price parser/capability。
- 不實作persistent SQLite LKG、freshness/stale/conflict resolver、source status endpoint或UI diagnostics。
- 不修改Holdings public schema、FastAPI/MCP/Streamlit contract，不新增Rainbow、i18n、exports或其他產品功能。
- 不做database migration、live scraping/golden acceptance、deployment、scheduler安裝或下一個Gap。
- 不作與Webb-site latest Holdings fetch/parser boundary無關的refactor、rename或formatting。

Dependencies/risks：

- 依賴已批准P1-01 `ec09374`、P1-02 `d8a480e`、P1-03 `f9fcf02`／`6152135`及P1-04 `7b69316`；registry及現有routing contract不可繞過。
- 需保持`7722bf2`建立的一次stock-code request策略；任何額外serial lookup均可能重新造成gateway timeout。
- 現有source只批准latest Holdings。若工作需要新endpoint、requested-date能力、條款／robots重新判斷、登入、CAPTCHA、Cookie或反爬繞過，立即停止請示。
- Parser分離不得藉機改公開schema或計算規則；如發現fixture顯示source schema已實際改變，只記錄`SOURCE_CHANGED`證據並停下，不猜新欄位。
- 本任務完成後仍不等於Phase 1 exit gate或golden live驗收完成；必須等待CTO批准後才進下一輪。


Remaining manual step：

- CTO Review／批准P1-05；批准前不建立或實作下一個TASK。

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
