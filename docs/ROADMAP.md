# Development Roadmap

> 路線圖只定義 phase、順序、依賴與 exit gates；每日執行狀態在 [`TASK.md`](../TASK.md)。所有 phase 受 [PROJECT_SPEC.md](PROJECT_SPEC.md) 與 [DEVELOPMENT_RULES.md](DEVELOPMENT_RULES.md) 約束。

實作盤點基準：已批准 P1-01 `ec09374`、P1-02 `d8a480e`、P1-03 `f9fcf02`／`6152135`、P1-04 `7b69316`、Post-P1-04 Gap Analysis `5e34853`及P1-05 `9e83321`；規格基準 `67e35e5`。P1-06 persistent LKG／freshness已完成實作並等待CTO Review；局部module、UI骨架或mock-only test不等於功能完成。


## 狀態

- ✅ Complete：exit gate 有測試／驗收證據。
- 🚧 In progress：目前 active phase。
- ⏳ Pending：未開始或前置 gate 未通過。
- ⛔ Blocked：需使用者授權、外部狀態或 source audit 結果。

## Repository 功能審核

### Done

| 功能 | 完成證據 |
|---|---|
| Specification governance | 五份 `docs`、根 `TASK.md`、README 引用、追溯索引及文件治理已建立，外部 Master Prompt 已 retired。 |
| Stock code normalization and issue identity safety | 支援 1–5 位代號正規化；Webb-site stock-code holdings route 會核對頁內 code 與 hidden issue ID；錯配頁面 fail loud；有離線測試。 |
| Google Drive CSV holdings source | `DATA_SOURCE=google_drive_csv`、一般分享／direct-download／Sheets URL、timeout、串流大小限制、HTML/login guard、CSV/schema/row validation、按 code/limit 查詢、memory cache、last-known-good、safe logging、CSV-only 不建立 Webb-site client，以及多日期 exact requested-date lookup／partial metadata round-trip 均有測試。 |
| Normalized schema, migrations and raw provenance | Stable source-neutral models、三版 additive transactional SQLite migrations、normalized snapshot/holding/collector/backfill run/error tables、raw checksum/reference、unique constraints、idempotent repository及舊 `SnapshotStore` 非破壞相容路徑已建立；離線 upgrade/rollback/storage/compatibility tests 通過。 |
| Resumable Backfill | `app.backfill_ccass` 支援 range/latest/resume/dry-run、exact-date capability、bounds/sleep/bounded retry、existing skip、failed-date retry、partial honesty、per-date persistent evidence及安全 exit status；dry-run 即使 snapshot 已存在仍 fetch/validate且 database byte-for-byte 不變。 |

### Partial

| 功能 | 已有 | 仍欠 Project Specification 要求 |
|---|---|---|
| Holdings | Webb-site guarded fetch + 純offline parser及Google CSV可回`CcassResponse`、summary、Top 5/10、T+2、`holdings_limit`；P1-06加入完整驗證後的persistent normalized LKG，以及`FRESH`／`STALE_LKG`／`UNAVAILABLE`、age、original error及restart-safe service/collector flow。 | Public `HoldingRow`尚未輸出`pct_of_ccass`，`CcassResponse`尚未公開issued-shares-as-of；缺corporate-action invariants及合法golden live核對。 |
| Changes | `compute_analysis` 可比較 supplied previous snapshot，識別 new/exited/increased/decreased、shares 及 percentage-point delta。 | 無 Changes source/parser、relative change、日期／完整性 pair validation、正式 service/API/MCP/table/download；比較可能基於截斷 holdings。 |
| Big Changes | 有 shares threshold 及排序。 | 只支援單一 absolute-shares 門檻；無集中 config/version、percentage/relative basis、正式 endpoint/export 及完整 snapshot 保證。 |
| Possible Transfer Patterns | 有 deterministic tolerance pairing 與報告免責字句。 | tolerance 未集中設定／版本化；沒有 dates/source metadata、完整 pair audit 或獨立交付接口。 |
| Concentration | 最新 response 有 participant count、Top 5/10 issued/CCASS；report 可呈現。 | 無 historical timeline、outside/denominator freshness/partial rules engine、service/API/MCP/download；未保證計算永遠基於完整 snapshot。 |
| Historical Snapshot | Source-neutral normalized tables、raw provenance、unique/idempotent save、latest/previous/date-range、complete/partial invariants、legacy JSON migration boundary，以及核准 CSV exact-date backfill/resume 已完成。 | 尚無合法 live source 多日真實 snapshot／golden 驗收及正式 history delivery surface。 |
| Collector | 經 `CcassService` 重用 `auto|webbsite|google_drive_csv` routing；支援dry-run、complete/partial honesty、normalized idempotent save、batch/per-stock run/error accounting及atomic CSV；P1-06把stale LKG記作`PARTIAL`並保存原source error，且不重寫snapshot。 | 尚無 history export、完整 retry policy exposure或合法 live/golden batch 驗收；historical backfill 已由獨立 P1-03 CLI 完成。 |
| Webb-site source adapter | P1-05已分離guarded streaming fetch與純Holdings parser；P1-06在service層加入source-neutral persistent normalized LKG、freshness及保守transient fallback，registry仍為latest-only parser v2。 | 仍只支援latest Holdings；無requested-date/history、其他Webb-site sections或合法live/golden驗收。 |
| Source routing, fallback and cache | Registry統一`auto|webbsite|google_drive_csv` routing/capability；P1-06以normalized repository提供restart-safe persistent LKG、config age、stale/error metadata及transient allowlist，integrity/date/disabled errors禁止fallback。 | 尚無cross-source conflict handling；Phase 4公開source status及UI diagnostics仍未實作。 |
| Source registry and diagnostics | 集中registry已登記既有`webbsite`與`google_drive_csv`，提供configured/enabled/priority、latest/requested-date/historical/manual-import capabilities、limits/cache/fallback、parser/schema、audit/terms/robots及安全無network diagnostics；service/collector/backfill routing有離線測試。 | 尚無last success/failure/freshness/latency、公開`/api/v1/sources/status`或UI diagnostics；這些維持Phase 4範圍。 |
| Company | Holdings metadata 可帶 name、code、issue ID。 | 無 Company model/section/endpoint、正式 identifiers、name history、日期及 source merge。 |
| Reports and Copy | 固定九節 Markdown、error report、Copy Report、Copy for ChatGPT safety header 及安全 UTF-8 clipboard encoding。 | 報告未涵蓋完整 sections；Copy 首段未以結構化方式固定列出實際 source/date/T+2/warnings；無 bilingual/localized export。 |
| Downloads | Streamlit 可下載 Markdown；collector 可輸出 latest holdings CSV。 | 缺 All Data/section/Rainbow/Price/Announcements CSV、JSON、Excel All Sections、Raw Tables JSON、內容預覽及完整 metadata/warning export tests。 |
| FastAPI | `/health`、holdings JSON、Markdown report；query/Bearer/X-API-Key auth；共用 holdings service；OpenAPI 由 FastAPI 產生。 | Project Specification 的 stock/holdings/changes/big-changes/concentration/rainbow/announcements/prices/report/source-status versioned routes 大多未有；partial/error envelope 及 query-key log redaction 未完整驗證。 |
| MCP | 一個 holdings tool 共用 `CcassService`。 | tool 名稱及集合未符合八個目標 tools；無 changes/concentration/rainbow/announcements/price/full report、error/schema 及 deployment tests。 |
| Streamlit UX | 有 stock input、holdings limit、big-change threshold、local previous option、progress、diagnostic Markdown、copy 及 Markdown download；基本 AppTest。 | 無規格 sidebar controls/navigation/tables/rainbow/concentration/price/announcements/company/raw previews/source diagnostics、session-state re-render、mobile evidence及完整錯誤/partial呈現。 |
| Error and partial-success contract | 有 `PlatformError` 及主要 upstream/auth/CSV errors；API 結構化回應；失敗報告不回空 array；Collector／Backfill 已持久化 safe error/retry metadata、per-item status及 batch counters；`DATE_UNAVAILABLE` exact-date 語義有測試。 | 其他 service/API 尚缺多個規定 error codes、source/warnings/safe details/partial sections envelope、stale semantics與跨 section partial success。 |
| Security and logging | env/secrets placeholders、source hostname/status/error type logging、Google URL/key redaction tests、collector抑制httpx/httpcore URL logs；P1-01至P1-04提交均有credential-pattern及私人路徑scan證據。 | 無自動化repository secrets scan、自訂API access-log query redaction、auth failure矩陣、raw/report sensitive-field policy tests。 |
| Tests | 130個離線tests；P1-06新增persistent restart LKG、fresh/stale/unavailable、age、transient/integrity guards、partial/storage failure及collector stale accounting tests，並保留P1-05及全部regression。 | Project Specification矩陣仍缺rainbow/i18n/完整API/MCP/exports/golden live/visual tests。 |
| Deployment and operations | 有 requirements、Streamlit headless/XSRF/theme config、secrets example及帶 `ShouldProcess` 的 Windows scheduler installer。 | 無 `robots.txt`、source status/metrics、cold-start drill、recovery/log rotation/remove script、已核准 scheduler install、公開 URL desktop/mobile/data/API/MCP acceptance。 |

### Not Started

| 功能 | 缺口 |
|---|---|
| Rainbow Data Engine | 無 historical matrix、Top N latest selection、Others、complete-vs-partial missing semantics、stable participant colours、CSV/JSON 或 chart。 |
| Price History | 無 audited source、parser/model/store/API/UI/export。 |
| HKEX Announcements | 無 HKEXnews index/PDF adapter、limits、languages、event tags、store/API/UI/export。 |
| HKEX SDW and manual official import | 無 adapter、manual CSV flow 或 golden cross-check evidence；目前只有合規說明。 |
| i18n | 無 `zh_HK`／English translation registry、香港繁中預設、fallback warning 或 non-refetch language state。 |
| Raw Previews and full Excel/JSON exports | 無 Raw Previews、Excel All Sections、Raw Tables JSON 及各 section structured export。 |
| Supplemental source audits | HKEX DI/SDI、同花順、price fallbacks、AAStocks 等仍未 audit/adapter；DisclosureTracker 正確保持非依賴。 |
| Golden and public acceptance | 只有 synthetic `01592` fixture；無合法 live source/HKEX SDW 數字核對、公開 Streamlit/mobile/language/download/API/MCP 驗收。 |

### Post-P1-04 完整 Gap Analysis（2026-07-23）

- Done：5；Partial：20；Not Started：8；總計33個功能單位；Remaining Gaps共28個。
- CTO已批准P1-01 `ec09374`、P1-02 `d8a480e`、P1-03 `f9fcf02`／`6152135`及P1-04 `7b69316`；normalized persistence、collector、backfill及internal source registry的證據均納入本輪審核。
- P1-04的批准不改變功能統計：`Source registry and diagnostics`仍是Partial，因last success/failure、freshness/latency、公開`/api/v1/sources/status`及UI diagnostics尚未完成。
- Phase 1仍未通過：合法active source的多日真實snapshots／golden evidence及Holdings、Changes、Big Changes、Concentration完整vertical slices仍欠缺；Phase 2不得提前開始。
- `P1-05 — Guarded and parser-separated Webb-site latest Holdings adapter`已由CTO批准；`P1-06 — Persistent LKG and Freshness for Latest Holdings`已完成實作並等待CTO Review，本輪不重排Remaining Gaps或選取下一個TASK。

### Remaining Gaps 優先序

排序先遵守 phase gate，再按 Architecture → Data → Engine → API → UI → Tests → Deployment → Acceptance 的依賴次序。同一功能的後續完整化保留其現有 Partial／Not Started判定；此表不把下一 phase提前變成 active scope。

| 優先 | 功能 | 現況 | 排序依據／下一完成門檻 |
|---:|---|---|---|
| 1 | Webb-site source adapter | Partial | `P1-05`已批准，`P1-06`已補persistent LKG/freshness；仍欠其他sections及live/golden驗收，所以不改判Done。 |
| 2 | Holdings | Partial | 在可信adapter boundary後補public `pct_of_ccass`、issued-shares-as-of、full-snapshot／`holdings_limit` invariants、corporate-action warnings及service tests，形成第一個Phase 1 section vertical slice。 |
| 3 | Source routing, fallback and cache | Partial | `P1-06`已完成persistent LKG、freshness/stale age及last source error；仍欠cross-source conflict policy及Phase 4公開diagnostics，只可使用registry批准來源。 |
| 4 | Historical Snapshot | Partial | 由合法active flow保存並驗證多日真實snapshots，補正式history query／delivery及golden evidence；不得用latest、插值或synthetic冒充。 |
| 5 | Changes | Partial | 只比較已驗證完整snapshot pair，補relative delta、日期／source／completeness metadata、service及tests。 |
| 6 | Big Changes | Partial | 在Changes pair contract上把threshold/basis/version集中config，補percentage/relative basis及完整snapshot保證。 |
| 7 | Concentration | Partial | 依完整snapshot補denominator freshness、partial rules、outside CCASS及historical timeline；不得以截斷holdings計算。 |
| 8 | Possible Transfer Patterns | Partial | 依已驗證Changes補可追溯tolerance/version、dates/source metadata、pair audit及固定免責。 |
| 9 | Collector | Partial | 核心idempotency/run accounting及stale LKG accounting已完成；待history export、完整retry policy exposure及合法live/golden batch evidence。 |
| 10 | Error and partial-success contract | Partial | 隨Phase 1 services補`DATA_STALE`／`PARTIAL_DATA`／`INVALID_SCHEMA`、safe details、partial sections及stale語義，不先建立空envelope。 |
| 11 | Tests | Partial | 隨上述slice補純parser/content guards、完整snapshot pair、四sections、service/API及合法多日/golden evidence。 |
| 12 | Security and logging | Partial | 補自動secrets scan、API access-log query redaction、auth failure矩陣及raw/report sensitive-field policy tests。 |
| 13 | HKEX SDW and manual official import | Not Started | Phase 1 golden抽樣前先取得明確source audit／批准；只可低頻官方或manual import，不得未核准自動化。 |
| 14 | Rainbow Data Engine | Not Started | 依賴Phase 1可信多日完整snapshots；完成matrix、Top N/Others、partial missing及stable colours。 |
| 15 | Price History | Not Started | Phase 2才audit adapter並完成model/store、adjustment/missing warnings、API/UI/export。 |
| 16 | Streamlit UX | Partial | Phase 2對齊navigation、tables、rainbow/concentration/price controls及desktop/mobile evidence；不得以UI先行冒充資料完成。 |
| 17 | i18n | Not Started | Phase 2建立`zh_HK`／English registry、fallback warning及不重新fetch的language state。 |
| 18 | HKEX Announcements | Not Started | Phase 3官方index/PDF limits、languages、event tags、failure isolation及delivery surfaces。 |
| 19 | Company | Partial | Phase 3補正式section、identifiers、name history、日期及source merge。 |
| 20 | Raw Previews and full Excel/JSON exports | Not Started | Phase 3完成Raw Preview、Excel All Sections、Raw Tables JSON及各section structured exports。 |
| 21 | Downloads | Partial | 依已完成sections補CSV/JSON/Excel、preview、metadata/warnings、encoding及安全檔名tests。 |
| 22 | Reports and Copy | Partial | 依完整sections固定實際source/date/T+2/warnings首段及localized exports。 |
| 23 | Source registry and diagnostics | Partial | Phase 4補runtime last success/failure、freshness/latency/cache telemetry及source-status service；P1-04 internal registry已完成，不重做。 |
| 24 | FastAPI | Partial | Phase 4依真實services完成versioned endpoints、stable envelope、auth/redaction及OpenAPI tests。 |
| 25 | MCP | Partial | Phase 4完成八個thin tools，共用service並補error/schema/deployment tests。 |
| 26 | Supplemental source audits | Not Started | 核心來源及sections穩定後才audit；HKEX DI/SDI、同花順、price fallbacks、AAStocks維持disabled/unverified。 |
| 27 | Deployment and operations | Partial | Phase 5補source metrics、cold-start/recovery、log rotation/remove scripts及scheduler文件；不自行安裝。 |
| 28 | Golden and public acceptance | Not Started | 最後執行合法live數字核對及公開Streamlit/API/MCP/mobile/language/download驗收；不得以offline fixture代替。 |

## Phase 0 — Specification baseline

**狀態：✅ Complete**

目標：把 Repository、完整指南、9 張截圖及參考網站整理成唯一正式規格來源。

Exit gate：

- `docs/PROJECT_SPEC.md`、`DATA_SOURCE_GUIDE.md`、`ARCHITECTURE.md`、`DEVELOPMENT_RULES.md`、`ROADMAP.md` 及根 `TASK.md` 建立。
- 需求按內容歸屬、去重、互相引用；原始 Master Prompt 25 節與截圖有追溯索引。
- README 指向 Single Source of Truth。
- Markdown links／格式、Ruff、Pytest 通過；commit/push `main`；工作樹乾淨。

## Phase 1 — Data foundation and objective CCASS sections

**狀態：🚧 In progress**

Scope：

1. 現有架構及 source audit；configuration-driven source registry。
2. Stable source-neutral schema、SQLite migrations、raw provenance。
3. Historical snapshot engine 與 idempotent repositories。
4. Collector CLI、dry-run、batch isolation、run logs。
5. Resumable CCASS backfill。
6. 真實 Holdings、Changes、Big Changes、Concentration vertical slice。
7. Offline fixtures、malformed/partial/source failure/migration tests。
8. Golden stock `01592` 與 Webb-site + HKEX SDW 抽樣核對。

Exit gate：

- 至少一個合法 active CCASS source 可由 code 解析 identity，保存多日真實 snapshots。
- 同日 collector 重跑無 duplicates；backfill resume/failed-date retry 通過。
- 四個 section 有真實資料、stable metadata/errors、API/service tests；無 placeholder。
- Partial、T+2、>100%、rename/missing identity 的規則有測試。
- Ruff/Pytest/smoke/secrets scan 通過；commit/push；部署保持可用。

最新gate判定（2026-07-23）：

| Exit gate | 狀態 | 已有證據／尚欠條件 | 阻塞原因與依賴次序 |
|---|---|---|---|
| 合法active CCASS source可解析identity並保存多日真實snapshots | ❌ 未完成 | Webb-site可由code核對identity但只提供latest；Google CSV exact-date只有批准import flow及offline fixtures，未有production多日／golden evidence。 | P1-05 guarded parser及P1-06 persistent LKG已完成；下一依賴是完整Holdings contract與合法多日資料。多日資料只能由日常collector累積或另行獲批的真實import，不能造數。 |
| Collector同日重跑無duplicate；Backfill resume／failed-date retry | ✅ 完成 | P1-02及P1-03離線tests覆蓋idempotency、batch isolation、resume、failed-date retry、existing skip及dry-run零寫入。 | 無工程阻塞；仍欠合法live batch evidence，歸入後續golden acceptance。 |
| Holdings／Changes／Big Changes／Concentration有真實資料、stable metadata/errors及API/service tests | ❌ 未完成 | Holdings只有部分public contract；其餘主要是對supplied、可能截斷的responses作compute，沒有完整snapshot pair service或目標API。 | complete Holdings slice及persistent complete snapshots → Changes/Big Changes/Concentration services → Phase 1 API/service tests。 |
| Partial、T+2、>100%、rename/missing identity規則有測試 | ✅ 完成（offline） | Storage、collector、compute及source tests已覆蓋partial honesty、T+2、>100%、rename、added/removed及identity mismatch。 | 仍須在合法golden data核對，但不阻塞下一個工程task。 |
| Ruff／Pytest／smoke／secrets及部署可用性 | ✅ 目前通過 | P1-06基準為130個offline tests；Ruff及Full Pytest通過，最終diff、Markdown、UTF-8、安全、database、Scope及public contract scans列入提交gate。 | 不等於公開部署或live source驗收；公開acceptance維持Phase 5。 |

Phase 1已完成條件：configuration-driven registry、normalized schema/migrations/raw provenance、collector run accounting/idempotency、resumable exact-date backfill，以及主要offline invariants。

Phase 1尚未完成條件：完整Holdings contract、多日真實snapshots、三個比較／集中度sections及其service/API tests、合法golden抽樣。

依賴次序：complete Holdings vertical slice（persistent LKG／freshness已完成）→ legal multi-day snapshots → Changes／Big Changes／Concentration → Phase 1 service/API tests → 獲批golden cross-check。任何HKEX SDW automation、source legality、credential或公開breaking schema需要CTO另行批准。

## Phase 2 — Historical visualization and aligned Streamlit UX

**狀態：⏳ Pending；依賴 Phase 1**

Scope：

1. Rainbow Data Engine。
2. DT-style stacked area chart。
3. Fixed participant colours、Top N、Others、完整／partial missing matrix。
4. Concentration History。
5. Price History 與 audited adapter/fallback。
6. Streamlit 對齊參考網站：sidebar、anchors、tables、desktop/mobile chart controls。
7. `zh_HK` default + English i18n，不重新 fetch。

Exit gate：

- Rainbow 只由真實 historical snapshots 生成；日期無插值。
- 同 participant 顏色跨 deploy/range/Top N 穩定。
- Y basis 切換、Top N、Others、search/filter、tooltip、legend、downloads 可用。
- Mobile/desktop、language switch、missing/partial 行為有離線/視覺 smoke evidence。
- Price source/date/adjustment/missing warnings 完整。

## Phase 3 — Announcements, company context and exports

**狀態：⏳ Pending；依賴 Phase 2**

Scope：

1. HKEXnews announcement index、official links/languages/event tags。
2. PDF extraction limits/status/failure isolation。
3. Company section、name history、basic identifiers。
4. Raw Previews。
5. All required CSV/JSON/Excel/Markdown exports。
6. Copy for ChatGPT、Copy Report、downloads UI。

Exit gate：

- 公告 period/count/table/filter/download 由官方真實資料驅動。
- 單 PDF failure 不拖垮列表；正式 URL 永遠保留。
- 每個 export 帶 stock/date/source/warnings，encoding/safe filename/golden tests 通過。
- Copy 首段包含 source/date/T+2/warnings/objective-data disclaimer。

## Phase 4 — Complete delivery surfaces and source operations

**狀態：⏳ Pending；依賴 Phase 3**

Scope：

1. 完整 versioned FastAPI endpoints。
2. 完整 MCP tools，共用 service layer。
3. `/api/v1/sources/status`、source diagnostics。
4. Cache/fallback/stale/last-known-good policies。
5. API auth/redaction/OpenAPI、partial/error compatibility。
6. 如獲核准，Google Drive/CSV import adapter 與 manual import workflows。

Exit gate：

- Project Specification 所列 endpoints/tools 均有真實 service implementation 和 tests。
- UI/API/MCP 對同一 query 的 facts/metadata 一致。
- Source status 不洩 secrets，cache/fallback/stale scenarios 有 tests。
- Hosting 不支援公開 MCP 時，adapter + offline tests + honest deployment docs 完成。

## Phase 5 — Golden acceptance, operations and public release

**狀態：⏳ Pending；依賴 Phase 4**

Scope：

1. Golden stock 數據與 Webb-site/HKEX SDW 核對。
2. 全量 regression、schema compatibility、migration、secrets scan。
3. 公開 Streamlit desktop/mobile、API、MCP（如部署）實際驗收。
4. Source/fallback/cold-start/partial/error drills。
5. README、CHANGELOG、操作／部署／recovery 文件。
6. Windows scheduler scripts、watchlist、log rotation 與安裝／移除說明（只準備，不自行安裝）。

Exit gate：

- 所有整體完成定義滿足；無 mock/placeholder 冒充完成。
- 公開站以真實 query 核對 data date/source/T+2/warnings/download/mobile。
- API/MCP schema 與 docs 一致；collector/backfill 恢復演練通過。
- Git 工作樹乾淨、commit/push 完成；只剩明確列出的人工 credential/scheduler 步驟。

## 跨 Phase 規則

- 前一 phase 未通過 exit gate，不展開下一 phase 的大規模實作。
- 可提早做必要 discovery/spike，但不得把 spike/placeholder 算完成。
- 每個 phase 內按 Architecture → Data → Engine → API → UI → Tests → Deployment → Acceptance 執行。
- Source legality、credentials、Windows scheduling、destructive migration、public schema breaking changes 必須按 [DEVELOPMENT_RULES.md](DEVELOPMENT_RULES.md) 暫停取得指示。
- 每個 phase 完成後按規定 11 項格式回報，並把 evidence/commit 寫回 [`TASK.md`](../TASK.md)。
