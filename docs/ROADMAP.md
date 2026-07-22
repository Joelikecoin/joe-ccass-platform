# Development Roadmap

> 路線圖只定義 phase、順序、依賴與 exit gates；每日執行狀態在 [`TASK.md`](../TASK.md)。所有 phase 受 [PROJECT_SPEC.md](PROJECT_SPEC.md) 與 [DEVELOPMENT_RULES.md](DEVELOPMENT_RULES.md) 約束。

實作盤點基準 `8966229` 已提前交付 Google Drive CSV、最小 collector/SQLite snapshots、客觀 changes/concentration、九節報告與 Streamlit workflow；這些是後續 phase 的局部能力，未滿足 normalized history、backfill、完整 sections、source diagnostics 或 public acceptance 等 exit gates，因此不把整個 phase 標為完成。


## 狀態

- ✅ Complete：exit gate 有測試／驗收證據。
- 🚧 In progress：目前 active phase。
- ⏳ Pending：未開始或前置 gate 未通過。
- ⛔ Blocked：需使用者授權、外部狀態或 source audit 結果。

## Phase 0 — Specification baseline

**狀態：✅ Complete**

目標：把 Repository、完整指南、9 張截圖及參考網站整理成唯一正式規格來源。

Exit gate：

- `docs/PROJECT_SPEC.md`、`DATA_SOURCE_GUIDE.md`、`ARCHITECTURE.md`、`DEVELOPMENT_RULES.md`、`ROADMAP.md` 及根 `TASK.md` 建立。
- 需求按內容歸屬、去重、互相引用；原始 Master Prompt 25 節與截圖有追溯索引。
- README 指向 Single Source of Truth。
- Markdown links／格式、Ruff、Pytest 通過；commit/push `main`；工作樹乾淨。

## Phase 1 — Data foundation and objective CCASS sections

**狀態：⏳ Pending**

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
