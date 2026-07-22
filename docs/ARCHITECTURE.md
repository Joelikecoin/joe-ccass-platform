# Architecture

> 本文件定義系統邊界、資料流、元件責任、儲存模型及非功能設計。產品行為見 [PROJECT_SPEC.md](PROJECT_SPEC.md)，來源政策見 [DATA_SOURCE_GUIDE.md](DATA_SOURCE_GUIDE.md)。

## 1. 架構原則

- 一個 Repository、一套 domain/service logic、三個 delivery adapters（FastAPI、MCP、Streamlit）。
- Fetch、parse、normalize、validate、store、calculate、present 明確分層。
- Source adapters 可配置、可停用、可診斷；一個 parser/source 失敗不拖垮無關 sections。
- SQLite 是 canonical historical store；CSV/JSON/XLSX 是 import/export 或 last-known-good 載體，不是第二套 domain logic。
- Live query 和 historical query 分開；live 失敗時只可回明確標示的 last-known-good。
- 所有計算可由保存的 normalized records 重現；raw provenance 可追溯。
- Schema、migration、errors、i18n 和 source registry 集中管理。

## 2. 系統全圖

```text
Public/manual sources
  HKEXnews | HKEX DI | HKEX SDW | Webb-site mirrors
  audited supplements | CSV/XLSX/Google Drive imports
                         │
                  source registry
                         │
        fetch → content guard → source parser
                         │
             normalize → schema validate
                         │
       ┌─────────────────┴──────────────────┐
 raw provenance                      SQLite transactions
                                      + atomic CSV history
                                              │
             query/comparison ─ rainbow engine ─ report/export
                                              │
                                     shared service layer
                           ┌──────────────────┼──────────────────┐
                       FastAPI              MCP             Streamlit
```

分析推理屬 ChatGPT Projects／下游，位於平台邊界之外。

## 3. 基準架構（`8966229`）

```text
app/config.py                  env-backed settings
app/errors.py                  ErrorCode + PlatformError
app/core/normalizers.py        stock/number/date/category helpers
app/sources/webbsite.py        mirror fetch + HTML parser + memory page cache
app/sources/google_drive_csv.py secure CSV download, validation, cache/LKG
app/services/ccass.py          DATA_SOURCE routing + compatible CcassResponse
app/models.py                  Pydantic response models
app/api.py                     health + holdings + Markdown report routes
app/mcp_server.py              one MCP holdings tool
app/streamlit_ui.py            input, workflow, report/copy/download helpers
streamlit_app.py               single-stock CCASS analysis UI
ccass_core/collector.py        minimal JSON snapshot SQLite + CLI/export
ccass_core/compute.py          objective changes/concentration calculations
ccass_core/report.py           fixed nine-section Markdown report
tests/                         source, routing, collector, compute, report, UI/API
```

保留的優點：單次 stock-code holdings lookup 會核對頁內 code/issue ID；上游錯誤不再全部誤報 timeout；log 不記 query/API key；三出口使用同一 service。

已知結構債：

- `WebbsiteClient` 仍同時 fetch 與 parse，尚未真正拆 module；source routing 也未形成完整 registry。
- 已有最小 `snapshots` SQLite JSON store 與 collector，但未有 normalized tables、migrations、raw provenance、resumable backfill 或 batch isolation。
- 現有 `CcassResponse` 已可承載 Webb-site／CSV attribution，但完整跨 section source-neutral envelope 尚未落地。
- 核心仍以最新 Holdings 為主；changes 只可比較本地 previous snapshot，rainbow、announcements、price 等仍未實作。
- Webb-site 與 Google CSV cache／last-known-good 只存 process lifetime，尚未與 persistent historical store 統一。
- machine timestamp 可用 UTC，但 business date 解析／顯示使用 `Asia/Hong_Kong`。

## 4. 目標 package 邊界

```text
app/
  config/             registry, thresholds, settings, i18n config
  domain/             stable models and invariants
  sources/
    base.py           fetch/result interfaces
    webbsite/         fetch.py, parsers/*.py
    hkex_sdw/         adapter + parser/manual import
    hkexnews/         index/PDF adapters + parser
    imports/          CSV/XLSX/Google Drive adapters
    prices/           audited price adapters
  storage/            SQLite, migrations, provenance, atomic CSV
  services/           stock/report/source-status orchestration
  engines/            comparison, concentration, rainbow, report/export
  api/                routes, dependencies, error mapping
  mcp/                thin tools calling services
  ui/                 Streamlit views, state, i18n, charts
  collector.py        batch collection CLI
  backfill_ccass.py   resumable historical backfill CLI
```

此樹是責任規格，不要求一次建立空 package。只有真實功能與測試同時加入時才建立 module。

## 5. Source adapter contract

每個 adapter 概念上提供 `fetch`、`parse`、`normalize`、`validate` 和 `diagnostics`。Raw result 包含 source ID、safe identifier、status/content type/size、fetched_at、cache state、checksum、warnings；不包含 secrets 或完整 request dump。

Parser 不依賴 httpx、env 或 database。Network tests 使用 mock/respx；parser tests 使用 saved fixtures。

## 6. Domain model 與 metadata envelope

所有 section 使用共同 envelope；metadata 先於 data，至少包括 stock/company/issue identity、data dates、fetched_at/timezone、sources/safe identifiers、cached/stale/partial、schema/parser version、warnings、conflicts 和 partial sections。Numeric values 保持 number。原始 source text 與 localized labels 分離。

現有 `CcassResponse` keys 在兼容期保留；新增 source-neutral metadata 時不靜默改名。

## 7. SQLite historical model

安全擴充而不無必要重建 database。至少建立／確認：

| Table | 主要責任 |
|---|---|
| `stocks` | 五位 stock code、現／歷史名稱、market identifiers |
| `source_issue_mapping` | stock/security ↔ source issue ID、驗證時間與證據 |
| `ccass_snapshots` | stock/date/source 級 totals、完整性、issued-share basis |
| `ccass_holdings` | snapshot + participant 的 holdings/percentages |
| `ccass_changes` | 相鄰／指定 snapshot 的客觀差異 |
| `ccass_concentration` | Top 5/10、CCASS total、participant count 時序 |
| `participant_aliases` | 同一 participant ID 的原文名稱歷史 |
| `participant_colours` | 穩定 deterministic/persisted colour |
| `price_history` | dated OHLCV/turnover/source/adjustment |
| `announcements` | official announcement index/extraction metadata |
| `collector_runs` | batch/run/stock 狀態、safe diagnostics |
| `backfill_runs` | range、cursor、success/failed/skipped/resume state |
| `source_errors` | safe source error、時間、類型、retry/result |

Snapshot invariants：每日可追加；同 stock/date/source/participant 唯一；同日重跑 idempotent；驗證後 transaction upsert；raw 與 normalized 可追溯；participant ID 延續 rename，缺 ID 不以相似名稱合併；保存 issued-shares-as-of；>100% 保留；partial 不當完整 0；migration 有 transaction/tests 且不靜默 drop；CSV temporary + atomic replace。


## 8. Collector

目標 CLI：

```powershell
python -m app.collector --stocks 01592,00700
python -m app.collector --watchlist config/watchlist.txt
python -m app.collector --source auto
python -m app.collector --date latest
python -m app.collector --dry-run
```

Pipeline：normalize → resolve identity → fetch → guard → parse → normalize → validate → transaction store → atomic history export → run log。

- 一隻股票 failure 不拖垮整批；每隻輸出 `SUCCESS`／`PARTIAL`／`ERROR`。
- bounded retry、rate limit、sleep、timeout；不得無限重試。
- 同日重跑無 duplicate；dry-run 不持久化但仍 validation。
- source/stock/date/error log 不包含 secrets 或敏感 query。

可準備 Windows Task Scheduler script、PowerShell wrapper、watchlist template、log rotation 及安裝／移除說明；未有使用者提供完整路徑與時間前不得自行安裝排程。

## 9. Historical backfill

```powershell
python -m app.backfill_ccass --stock 01592 --from 2025-07-01 --to 2026-07-21
python -m app.backfill_ccass --stock 01592 --latest 250
python -m app.backfill_ccass --stock 01592 --resume
python -m app.backfill_ccass --stock 01592 --dry-run
```

Resume cursor 持久化；已有 snapshot 跳過；最大頁數／日期數 configurable；每 request sleep；單日 failure 不全批 rollback；保存 success/failed/skipped；失敗日可重試；不阻塞 Streamlit。只能取得部分歷史就如實保存再由 collector 累積；不插值、不造不存在日期。

## 10. Comparison、Concentration 與 Rainbow engines

Comparison 只接受已驗證 snapshot pairs，輸出 added/removed/increased/decreased、share delta、percentage-point delta、relative delta。Big-change thresholds 在 config 並記錄版本。Possible transfer matching 只作容差內客觀 pairing，輸出 difference/tolerance/disclaimer，不推斷 ownership/trade reason。

Concentration 以明確 denominator 計算 Top 5/10、total in CCASS、outside CCASS、participant count。完整 rows 不足、snapshot partial 或 denominator stale 時標 partial/warning；不得用 `holdings_limit` 切片計 totals。

Rainbow 流程：

1. 從完整 validated snapshots 選日期範圍。
2. 以最新日期選 Top N participant IDs，保留入選者整段真實歷史。
3. 完整 snapshot 缺 ID 可補 0；partial snapshot 保持 missing/null + warning。
4. 可聚合 Others，但不把 missing/partial 混入 Others。
5. 以 participant ID 決定固定顏色。
6. 輸出 chart-ready rows、legend、missing/partial matrix、source/date metadata。

## 11. Cache 與 last-known-good

三層 cache：request/process memory、persistent normalized latest-known-good（SQLite/import）、optional raw/source cache。

只有通過 content guard、parser、schema validation 和 identity checks 的資料可成為 last-known-good。新 fetch 失敗不能破壞舊 good record。回舊資料時標 `cached=true`、stale、原 data date、last fetch attempt/error；freshness 超限回 `DATA_STALE` 或明確 partial/error。

## 12. API、MCP 與 UI adapters

- API routes 只做 auth/input/dependency/error-to-HTTP mapping。
- MCP tools 只轉換參數與序列化 service results。
- Streamlit 將 query result 存 session state；語言、tab、chart controls 不重新 fetch。
- 三者不得直接 import source parser；只能呼叫 services。
- `/health` 公開；source diagnostics 與 data endpoints 可配置 auth。
- Query parameter API key 必須支援，亦可 Bearer/X-API-Key；logs/redaction 共享 security policy。

## 13. i18n 架構

中央 registry 以 stable message keys 對應 `zh_HK`/`en`。Domain data、API schema 與 source text 不翻譯。UI/report/export adapter 套用 labels；missing key 回 English fallback 並記 warning。切換 locale 只重 render session result。

## 14. Deployment 與 observability

- 設定全由 env/config；`.env.example` 只放 placeholder。
- `/health` 不依賴 live upstream；source status 分開顯示。
- 公開部署提供 `robots.txt`，允許 intended public health/API paths，並禁止非公開／管理路徑。
- Free-tier cold start 回 `COLD_START` 或讓 client 按文件重試，不能解讀為 no data。
- 《完整指南》以 Render free tier 說明風險，但 hosting provider 並非固定要求；任何平台都遵守相同 timeout、health、secrets 和 acceptance 規則。
- Uptime monitor 可監察 `/health`；keep-alive 需符合 hosting 條款。
- Logs/metrics 覆蓋 source latency、failure class、cache hit、freshness、run counts；不記 secrets/query。
- 部署後用公開 URL 驗收真實 data/UI/API，不只檢查頁面能開。

## 15. 架構決策原則

- 先讓 golden stock 真實 vertical slice 通過，再擴 source/feature。
- 不一次建大量 placeholder；新 abstraction 必須解決真實問題。
- Migration、public schema、source legality、credentials 按 [DEVELOPMENT_RULES.md](DEVELOPMENT_RULES.md) 處理。
