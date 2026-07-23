# Development Roadmap

> 路線圖只定義 phase、順序、依賴與 exit gates；每日執行狀態在 [`TASK.md`](../TASK.md)。所有 phase 受 [PROJECT_SPEC.md](PROJECT_SPEC.md) 與 [DEVELOPMENT_RULES.md](DEVELOPMENT_RULES.md) 約束。

實作盤點基準：程式至 P1-02 完成 commit `d8a480e`；規格基準 `67e35e5`。以下審核以 2026-07-22 的 Repository、78 個通過的離線測試及 Project Specification 為證據。局部 module、UI 骨架或 mock-only test 不等於功能完成。


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
| Google Drive CSV holdings source | `DATA_SOURCE=google_drive_csv`、一般分享／direct-download／Sheets URL、timeout、串流大小限制、HTML/login guard、CSV/schema/row validation、按 code/limit 查詢、memory cache、last-known-good、safe logging 及 CSV-only 不建立 Webb-site client 均有測試。 |
| Normalized schema, migrations and raw provenance | Stable source-neutral models、兩版 transactional SQLite migrations、normalized snapshot/holding/run/error/per-stock run-item tables、raw checksum/reference、unique constraints、idempotent repository 及舊 `SnapshotStore` 非破壞相容路徑已建立；離線 upgrade/rollback/storage/compatibility tests 通過。 |

### Partial

| 功能 | 已有 | 仍欠 Project Specification 要求 |
|---|---|---|
| Holdings | Webb-site／Google CSV 可回 `CcassResponse`、summary、Top 5/10、T+2、`holdings_limit`；normalized persistence 保存 per-row `pct_of_ccass`、issued-shares-as-of、partial/duplicate/rename invariants；有 identity/parser/source/storage tests。 | Public `HoldingRow` 尚未輸出 `pct_of_ccass`，`CcassResponse` 尚未公開 issued-shares-as-of；缺 corporate-action invariants 及合法 golden live 核對。 |
| Changes | `compute_analysis` 可比較 supplied previous snapshot，識別 new/exited/increased/decreased、shares 及 percentage-point delta。 | 無 Changes source/parser、relative change、日期／完整性 pair validation、正式 service/API/MCP/table/download；比較可能基於截斷 holdings。 |
| Big Changes | 有 shares threshold 及排序。 | 只支援單一 absolute-shares 門檻；無集中 config/version、percentage/relative basis、正式 endpoint/export 及完整 snapshot 保證。 |
| Possible Transfer Patterns | 有 deterministic tolerance pairing 與報告免責字句。 | tolerance 未集中設定／版本化；沒有 dates/source metadata、完整 pair audit 或獨立交付接口。 |
| Concentration | 最新 response 有 participant count、Top 5/10 issued/CCASS；report 可呈現。 | 無 historical timeline、outside/denominator freshness/partial rules engine、service/API/MCP/download；未保證計算永遠基於完整 snapshot。 |
| Historical Snapshot | Source-neutral normalized tables、raw provenance、unique/idempotent save、latest/previous/date-range、complete/partial invariants 及 legacy JSON migration boundary 已完成。 | 尚無合法 live source 多日真實 snapshot 驗收、backfill/resume 及正式 history delivery surface。 |
| Collector | 經 `CcassService` 重用 `auto|webbsite|google_drive_csv` routing；CSV-only 不建立 Webb-site client；支援 stocks/watchlist、source、`date=latest`、dry-run、complete/partial honesty、normalized idempotent save、batch/per-stock run/error accounting、明確 exit codes及帶安全 metadata 的 UTF-8-SIG atomic latest CSV。 | 尚無 historical date collection、resumable backfill、history export、failed-date retry、完整 retry policy exposure 或合法 live/golden batch 驗收。 |
| Webb-site source adapter | 有 primary/fallback、timeout/rate interval、cache、5 MB limit、browser headers、identity safety及 403/429/5xx/challenge/network classification。 | 只支援 Holdings；fetch/parser 仍耦合；無 content-type guard、persistent LKG、registry diagnostics、parser/schema version 或其他 Webb-site sections。 |
| Source routing, fallback and cache | `auto|webbsite|google_drive_csv` routing；mirror failure 可 fallback CSV；兩 source 有 process cache，CSV 有 process-memory LKG。 | 無 configuration-driven registry、persistent normalized LKG、freshness/stale age/error metadata、cross-source conflict handling 或統一 cache policy。 |
| Company | Holdings metadata 可帶 name、code、issue ID。 | 無 Company model/section/endpoint、正式 identifiers、name history、日期及 source merge。 |
| Reports and Copy | 固定九節 Markdown、error report、Copy Report、Copy for ChatGPT safety header 及安全 UTF-8 clipboard encoding。 | 報告未涵蓋完整 sections；Copy 首段未以結構化方式固定列出實際 source/date/T+2/warnings；無 bilingual/localized export。 |
| Downloads | Streamlit 可下載 Markdown；collector 可輸出 latest holdings CSV。 | 缺 All Data/section/Rainbow/Price/Announcements CSV、JSON、Excel All Sections、Raw Tables JSON、內容預覽及完整 metadata/warning export tests。 |
| FastAPI | `/health`、holdings JSON、Markdown report；query/Bearer/X-API-Key auth；共用 holdings service；OpenAPI 由 FastAPI 產生。 | Project Specification 的 stock/holdings/changes/big-changes/concentration/rainbow/announcements/prices/report/source-status versioned routes 大多未有；partial/error envelope 及 query-key log redaction 未完整驗證。 |
| MCP | 一個 holdings tool 共用 `CcassService`。 | tool 名稱及集合未符合八個目標 tools；無 changes/concentration/rainbow/announcements/price/full report、error/schema 及 deployment tests。 |
| Streamlit UX | 有 stock input、holdings limit、big-change threshold、local previous option、progress、diagnostic Markdown、copy 及 Markdown download；基本 AppTest。 | 無規格 sidebar controls/navigation/tables/rainbow/concentration/price/announcements/company/raw previews/source diagnostics、session-state re-render、mobile evidence及完整錯誤/partial呈現。 |
| Error and partial-success contract | 有 `PlatformError` 及主要 upstream/auth/CSV errors；API 結構化回應；失敗報告不回空 array；Collector 已持久化 safe source error/retry metadata、per-stock `SUCCESS|PARTIAL|ERROR` 及 batch counters。 | 其他 service/API 尚缺多個規定 error codes、source/warnings/safe details/partial sections envelope、stale semantics 與跨 section partial success。 |
| Security and logging | env/secrets placeholders、source hostname/status/error type logging、Google URL/key redaction tests、collector 抑制 httpx/httpcore URL logs；P1-02 repository grep/diff scan 無發現 secret 或私人路徑。 | 無自動化 repository secrets scan、自訂 API access-log query redaction、auth failure 矩陣、raw/report sensitive-field policy tests。 |
| Tests | 78 個離線 tests 覆蓋 normalize、identity、upstream failures、Google CSV、三種 source routing、collector CLI/dry-run/partial/mixed batch/run accounting/atomic export、normalized history/migrations/idempotency/rollback/legacy compatibility、compute、report、API report、Streamlit validation 及 deployment files。 | Project Specification 矩陣仍缺 backfill/rainbow/i18n/完整 API/MCP/exports/golden live/visual tests。 |
| Deployment and operations | 有 requirements、Streamlit headless/XSRF/theme config、secrets example及帶 `ShouldProcess` 的 Windows scheduler installer。 | 無 `robots.txt`、source status/metrics、cold-start drill、recovery/log rotation/remove script、已核准 scheduler install、公開 URL desktop/mobile/data/API/MCP acceptance。 |

### Not Started

| 功能 | 缺口 |
|---|---|
| Resumable Backfill | 無 CLI、date/latest range、resume cursor、skip existing、failed-date retry、bounded history 或 run records。 |
| Rainbow Data Engine | 無 historical matrix、Top N latest selection、Others、complete-vs-partial missing semantics、stable participant colours、CSV/JSON 或 chart。 |
| Price History | 無 audited source、parser/model/store/API/UI/export。 |
| HKEX Announcements | 無 HKEXnews index/PDF adapter、limits、languages、event tags、store/API/UI/export。 |
| HKEX SDW and manual official import | 無 adapter、manual CSV flow 或 golden cross-check evidence；目前只有合規說明。 |
| Source registry and diagnostics | 無 source status model/registry、audit state、last success/failure/freshness/latency、`/api/v1/sources/status` 或 UI diagnostics。 |
| i18n | 無 `zh_HK`／English translation registry、香港繁中預設、fallback warning 或 non-refetch language state。 |
| Raw Previews and full Excel/JSON exports | 無 Raw Previews、Excel All Sections、Raw Tables JSON 及各 section structured export。 |
| Supplemental source audits | HKEX DI/SDI、同花順、price fallbacks、AAStocks 等仍未 audit/adapter；DisclosureTracker 正確保持非依賴。 |
| Golden and public acceptance | 只有 synthetic `01592` fixture；無合法 live source/HKEX SDW 數字核對、公開 Streamlit/mobile/language/download/API/MCP 驗收。 |

### P1-02 批准後完整 Gap Analysis（2026-07-22）

- Done：4；Partial：19；Not Started：10；總計 33 個功能單位。
- CTO 已正式批准 P1-02 commit `d8a480e`。其 source-neutral collector orchestration、complete/partial capture、dry-run 零寫入、`collector_run_items` migration、batch/per-stock accounting、exit status及安全 atomic CSV metadata 均有離線證據。
- 批准代表 P1-02 task 完成，不會把 Project Specification 中未交付的 historical-date collection、resume、failed-date retry、history export 或合法 live/golden batch 驗收視為完成；故 Collector 維持 Partial，獨立 Resumable Backfill 維持 Not Started。
- P1-01/P1-02 已移除 Backfill 的 normalized persistence、idempotency、source routing 與 run-accounting 前置缺口。依 Phase 1 exit gate，下一個唯一最高優先工作是 `P1-03 — Resumable source-neutral CCASS historical backfill`。

### P1-03 實作證據（2026-07-23；待 CTO Review）

- 已按核准 task 完成 source-neutral requested-date backfill CLI、Google Drive/CSV 多日期 exact lookup、additive v3 run/per-date migration、resume、existing skip、failed-date retry、partial honesty、bounds/sleep/retry、dry-run及 safe error evidence。
- Webb-site latest adapter 未被宣稱或啟用為 historical source；range 中不存在的日期只記錄 `DATE_UNAVAILABLE`／`SKIPPED`，requested/returned code/date mismatch 會拒絕保存；未執行 live scraping或製造 synthetic production snapshot。
- 完整離線 regression 為 88 passed；Ruff、CLI smoke、`git diff --check`、credential-pattern及私人路徑 scan 均通過。公開 FastAPI、MCP、Streamlit contract 未修改。
- 本段只記錄已批准 P1-03 的實作事實，不構成下一輪 Gap Analysis；下列 2026-07-22 統計與 Remaining Gaps 排序維持原 audit baseline，待 CTO Review／另行批准後才重判。

### Remaining Gaps 優先序

排序先遵守 phase gate，再按 Architecture → Data → Engine → API → UI → Tests → Deployment → Acceptance 的依賴次序。同一功能的後續完整化保留其現有 Partial／Not Started 判定；此表不把下一 phase 提前變成 active scope。

| 優先 | 功能 | 現況 | 排序依據／下一完成門檻 |
|---:|---|---|---|
| 1 | Resumable Backfill | Not Started | P1-01/P1-02 已提供 store 與 collector 前置；Phase 1 必須先有 range/latest/resume、skip、failed-date retry及 bounded run evidence，才能建立可信多日資料。 |
| 2 | Source registry and diagnostics | Not Started | 先完成 Phase 1 所需 configuration-driven registry、capability/date coverage 與 audit metadata；公開 status endpoint/UI diagnostics 留待 Phase 4。 |
| 3 | Webb-site source adapter | Partial | 拆分 fetch/parser、補 content guard、parser/schema version及核准的 historical capability，為多日資料與完整 sections 提供可測 adapter。 |
| 4 | Source routing, fallback and cache | Partial | 統一 persistent LKG、freshness/stale、conflict及 cross-source policy，避免歷史與 latest 語義分裂。 |
| 5 | Historical Snapshot | Partial | 以合法 active source 保存並驗證多日真實 snapshots，補正式 history delivery evidence。 |
| 6 | Holdings | Partial | 補 public `pct_of_ccass`、issued-shares-as-of、corporate-action invariants及 golden live 核對。 |
| 7 | Changes | Partial | 只用已驗證完整 snapshot pair，補 relative delta、pair completeness、service及 tests。 |
| 8 | Big Changes | Partial | 將 threshold/basis/version 移入 config，補 percentage/relative basis與完整 snapshot保證。 |
| 9 | Possible Transfer Patterns | Partial | 補可追溯 tolerance/version、dates/source metadata、pair audit及固定免責。 |
| 10 | Concentration | Partial | 補 denominator freshness、partial rules、outside CCASS及基於完整 snapshots的歷史時序。 |
| 11 | HKEX SDW and manual official import | Not Started | 只在 source audit/授權允許下提供官方抽樣或 manual import；不得未核准自動化。 |
| 12 | Collector | Partial | 一次性 latest orchestration已完成；待 Backfill/history export、retry policy exposure及合法 live/golden batch證據後再重判。 |
| 13 | Tests | Partial | 先補 Phase 1 backfill、多日、malformed/partial、source failure、migration及 golden 分層證據。 |
| 14 | Error and partial-success contract | Partial | 補 Phase 1 service 的 date unavailable、stale、safe details及 partial sections語義，再擴至全平台。 |
| 15 | Security and logging | Partial | 補自動 secrets scan、access-log query redaction與 raw/report sensitive-field policy tests。 |
| 16 | Rainbow Data Engine | Not Started | 依賴可信多日 snapshots及 Phase 1 gate；完成 matrix、Top N/Others、partial missing及 stable colours。 |
| 17 | Price History | Not Started | Phase 2 audit adapter、model/store、adjustment/missing warnings、API/UI/export。 |
| 18 | Streamlit UX | Partial | Phase 2 對齊 navigation、tables、rainbow/concentration/price controls及 desktop/mobile evidence。 |
| 19 | i18n | Not Started | Phase 2 建立 `zh_HK`/English registry、fallback warning及不重新 fetch 的 language state。 |
| 20 | HKEX Announcements | Not Started | Phase 3 官方 index/PDF limits、languages、event tags、failure isolation及 delivery surfaces。 |
| 21 | Company | Partial | Phase 3 補正式 section、identifiers、name history、日期及 source merge。 |
| 22 | Raw Previews and full Excel/JSON exports | Not Started | Phase 3 完成 Raw Preview、Excel All Sections、Raw Tables JSON與 structured exports。 |
| 23 | Downloads | Partial | 補所有 section CSV/JSON/Excel、preview、metadata/warnings、encoding及安全檔名 tests。 |
| 24 | Reports and Copy | Partial | 納入完整 sections，固定實際 source/date/T+2/warnings首段及 localized exports。 |
| 25 | FastAPI | Partial | Phase 4 完成 versioned endpoints、stable envelope、auth/redaction/OpenAPI tests。 |
| 26 | MCP | Partial | Phase 4 完成八個 thin tools，共用 service並補 error/schema/deployment tests。 |
| 27 | Supplemental source audits | Not Started | 核心來源穩定後才 audit；未核准來源維持 disabled/unverified。 |
| 28 | Deployment and operations | Partial | 補 source metrics、cold-start/recovery、log rotation/remove scripts及 scheduler文件；不自行安裝。 |
| 29 | Golden and public acceptance | Not Started | Phase 5 才執行合法 live數字核對及公開 Streamlit/API/MCP/mobile/language/download驗收。 |


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
