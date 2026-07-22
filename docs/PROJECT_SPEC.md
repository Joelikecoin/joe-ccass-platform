# Joe CCASS Platform — Project Specification

> 狀態：正式、規範性（normative）
> 生效日期：2026-07-22
> 原始指定基準：`fad4411`；文件整合時最新實作：`8966229`
> Repository：`Joelikecoin/joe-ccass-platform`

## 1. 文件地位與規格來源

本文件與同目錄文件及根目錄 [`TASK.md`](../TASK.md) 共同構成本專案唯一的 Single Source of Truth。從本版開始，不再維護或依賴單一外部 Master Prompt；外部原稿、指南、截圖及參考網站的有效要求已整理並納入這組文件。

規格來源共有四類：

1. Repository 自原始指定基準 `fad4411` 至文件整合時最新 commit `8966229` 的程式、README、測試、設定與 Git 歷史。
2. 《AI 港股財技數據平台｜由零開始完整指南》Markdown。
3. 使用者提供的 9 張功能、UI、圖表及教學參考截圖。
4. [參考 Streamlit 網站](https://webbsite-ccass-tool-r3ntrqvqx9w2k3xffasgwf.streamlit.app/)。

2026-07-22 的唯讀驗證顯示參考網站會重導至 Streamlit 登入流程，連 health path 亦受相同保護；本專案不得繞過登入。故已提供的 9 張截圖是目前可保存的 UI／功能證據，網站 URL 保留作日後獲授權時的人工比對，受保護頁面的當前隱藏行為不得猜測。

解讀順序如下：

- 最新明確使用者指示優先。
- 本組文件是整理後的規範性要求；Repository 現況只是實作基線，不能以「目前未支援」否定目標規格。
- 參考網站與截圖只定義功能、資料內容、資訊架構和視覺行為，不授權複製私人程式碼、API、Cookie、憑證或非公開資料。
- 正式來源資料與參考畫面衝突時，以合法取得的正式來源、資料日期、完整性及本文件的「數據誠實」原則為準。
- 未能在公開環境重新驗證的參考網站狀態不得猜測；已提供截圖所呈現的功能則按本文件明文化。

相關文件：

- 資料來源、優先次序與欄位：[DATA_SOURCE_GUIDE.md](DATA_SOURCE_GUIDE.md)
- 現況與目標技術設計：[ARCHITECTURE.md](ARCHITECTURE.md)
- 實作、測試、安全與 Git 規則：[DEVELOPMENT_RULES.md](DEVELOPMENT_RULES.md)
- 階段及完成門檻：[ROADMAP.md](ROADMAP.md)
- 唯一執行佇列與目前工作：[../TASK.md](../TASK.md)

## 2. 產品使命

建立一套完全由本 Repository 控制、可測試、可維護、可部署並可持續擴充的港股客觀數據平台。平台應在功能、資料內容和使用流程上高度接近參考網站，但所有圖表及輸出必須由本平台從合法公開來源收集、解析、驗證及保存的資料生成。

最終目標不是複製參考網站，而是提供比參考網站更穩定、可追溯、容易維護及容易擴充的資料基礎設施。

### 2.1 平台負責範圍

- 公開資料 fetch、parse、normalize、validate、enrich。
- 股票代號與 Webb-site issue ID 的可驗證 mapping。
- 歷史 snapshot、collector、backfill、SQLite／CSV 保存。
- Holdings、Changes、Big Changes、Concentration、Price、Announcements 等客觀資料。
- 客觀差異、集中度與 possible transfer pattern 計算。
- FastAPI、MCP、Streamlit 共用 domain/service logic。
- 客觀圖表、報告、複製及下載。
- 完整 source/date/cache/partial/warning/error metadata。
- cache、fallback、source diagnostics 與部署／公開驗收。

### 2.2 明確不負責範圍

平台不得輸出或暗示：

- 投資評分、買入／賣出建議、股價預測。
- 莊家判斷、收貨／派貨結論、大戶建倉或市場意圖。
- 財技班主觀規則或 AI 股票分析。
- 即時交易、下單或已確認的實益擁有人轉移。

財技及投資分析由 ChatGPT Projects 或其他下游分析層使用本平台的客觀輸出後處理。平台必須清楚分隔事實、限制與下游推理。

## 3. 不可妥協的產品原則

1. **Fail loud, never fake**：失敗必須結構化回報。
2. 舊 cache 不得冒充最新資料；cached/stale/last-known-good 必須帶日期和標記。
3. 空 array 不得冒充「沒有資料」或「沒有變化」。
4. partial data 必須列出缺少的 sections／rows／日期，不得當完整 snapshot。
5. 每項資料必須帶 source、source identifier／URL、data date、fetched_at、cached 和 warnings。
6. Schema 穩定；欄位改名視為 schema change，必須提供兼容期。
7. Streamlit、FastAPI、MCP 共用同一 service/domain logic，MCP 不得另寫 parser。
8. Network fetch 與 parser 分離；parser 可只靠 fixture 離線測試。
9. 網絡／live 驗收與離線 fixture tests 分開。
10. 不 commit secrets、token、cookie、私人路徑或真實 key。
11. 遵守條款、robots、合理 rate、sleep、timeout、bounded retry。
12. 不繞過登入、CAPTCHA、付費牆、存取控制或反爬保護。
13. 不可合法、穩定取得的來源要停用並說明原因。
14. 數據衝突必須明列，不可靜默選擇。
15. 內部時區統一 `Asia/Hong_Kong`；日期統一 `YYYY-MM-DD`。
16. 股票代號內部統一為五位數字字串。
17. CCASS 是結算層 nominee data，不等同實益擁有人；T+2 必須出現在 metadata、UI 和報告。
18. 原始 holding 不得任意改寫；不得以插值製造 holdings 或 snapshot dates。

## 4. 使用者與出口

採「一個核心、三個出口」：

- **MCP**：AI connector 的主要機器接口。
- **FastAPI JSON**：程式及 AI fetch 工具的後備接口。
- **Streamlit**：人手查詢、視覺核對、Copy 及 Download 的兜底接口。

三個出口必須呈現相同 normalized facts、metadata、warnings 和 errors。語言切換只改 display/export layer，不可觸發重新抓取或改變底層數值。

## 5. 功能規格

### 5.1 查詢與 Fetch Summary

- 接受 stock code；進階模式可接受已驗證的 Webb-site issue ID。
- stock code 輸入支援 1–5 位數並 normalize 為五位數。
- 不得猜 issue ID，亦不得因錯誤 ID 靜默回傳另一股票。
- 顯示每個 section 的 SUCCESS／PARTIAL／ERROR、source、data date、fetch time、cache/fallback status 和 warnings。
- 一個非核心補充來源失敗，不得令已成功的核心 sections 被丟棄；partial response 必須明確列出。

### 5.2 Company

提供公司正式名稱、股票代號、issue ID、基本公開識別資料、名稱歷史（可取得時）、來源與日期。公司改名不得破壞舊公告或歷史資料搜尋。

### 5.3 Holdings

至少包括：

- `participant_id`、原文 `participant_name`、rank。
- holding/shares、last change date。
- `pct_of_issued`、`pct_of_ccass`（來源／分母支持時）。
- cumulative percentage、participant category（如屬客觀分類）。
- issued shares、issued-shares-as-of、total in CCASS、outside/non-CCASS、participant count。
- Top 5／Top 10，以百分比基準明確區分。
- stock split、bonus/rights issue、placement、consolidation/subdivision、participant rename/missing、duplicate、source date mismatch 等 warnings。
- `pct_of_issued > 100%` 不得刪除；保留原值並警告股本基數可能滯後。

`holdings_limit` 只限制回傳／顯示列數，不得改變以完整 snapshot 計算的 totals、participant count 或 Top 5／10。

### 5.4 Changes 與 Big Changes

客觀比較至少支援：participant added/removed、holding increased/decreased、share change、percentage-point change、relative change。Big Changes 門檻必須 configuration-driven，輸出資料日、比較日、基準、來源與 warnings。

### 5.5 Possible Transfer Patterns

只可描述同期間相近增減的數據配對，例如「A 減少約 X 股，B 增加約 Y 股，差額在設定容許範圍內」，並固定顯示：

- possible pattern only；
- not a confirmed transfer；
- CCASS cannot prove beneficial ownership or trade reason。

不得使用「肯定轉倉、莊家收貨、派貨、大戶建倉、利好、利淡」。

### 5.6 Concentration 與歷史

提供 Top 5、Top 10、Total in CCASS、non-CCASS/outside CCASS（可支持時）、participant count 和 historical timeline。所有百分比欄明示分母，集中度改變不得自動翻譯為投資結論。

### 5.7 Rainbow Data Engine

Rainbow 必須由本地保存的真實 snapshots 生成，不依賴 DisclosureTracker 圖表、API 或私人資料。

- X 軸只用真實 `snapshot_date`，不製造非交易日。
- Y 軸可切換 `pct_of_issued`／`pct_of_ccass`。
- 每層代表一個 participant；`participant_id` 是穩定 key，name 只作顯示。
- 支援 Top N、Others、日期範圍、最近 N 個 snapshots、participant 搜尋／篩選、legend、tooltip、CSV、JSON。
- Top N 預設按最新 snapshot 排序，但入選 participant 在整段範圍保留完整歷史，避免每日排名造成顏色跳動。
- 同 participant 在完整 snapshot 缺失可在生成矩陣時補 0；必須區分真正 0、該日不存在與 partial snapshot。partial 不得錯補 0，不得插值。
- 顏色由 participant ID deterministic hash 或持久 mapping 決定；重新部署、日期範圍或 Top N 改變後保持不變。Others 固定中性色。

### 5.8 Price History

提供 `price_date`、source、adjusted/unadjusted 狀態、open/high/low/close、volume、turnover（如有）及 missing-date warning。不得加入即時交易或下單。

### 5.9 HKEX Announcements

公告區至少提供：查詢期間、總數、publish time、category、官方 title、file info/size、official URL、中／英文版本、日期排序、客觀 event tags、CSV／JSON。

Event tags 可包括月報表、年報、中期報告、配售、供股、合股、拆股、更換董事／核數師、全面收購／GO、股本變動、公司改名；只作分類。

PDF extraction 必須有檔案大小及文字長度限制；單份失敗不拖垮列表；保留官方 URL 與 extraction status；摘要不得取代公告原文。

### 5.10 Raw Previews、Reports、Copy 與 Downloads

目標輸出：

- All Data CSV、Holdings CSV、Changes CSV、Big Changes CSV、Concentration CSV。
- Rainbow CSV/JSON、Price CSV、Announcements CSV。
- Excel All Sections、Raw Tables JSON、Markdown Report。
- Copy for ChatGPT、Copy Report。

所有輸出須帶 stock code、data date、source metadata、warnings，採安全檔名，按用途使用 UTF-8 或 UTF-8-SIG，並有離線測試。JSON 預設維持穩定英文 schema；localized export 必須清楚標示。

Copy for ChatGPT 首段固定包含資料來源、資料日期、T+2、warnings，以及「以下是客觀數據，不包含投資建議」。

## 6. Streamlit UX 與語言

### 6.1 資訊架構

Sidebar 至少包括：

- Input Type（Stock Code／Webb-site Issue ID）。
- Stock Code／Issue ID。
- Timeout、Announcement Period、Source Mode。
- Data Date、History Range、Top N、Percentage Basis、Fetch。

主頁至少提供可跳轉導航：Fetch Summary、All Tables、DT Rainbow、HKEX Announcements、Company、Holdings、Changes、Big Changes、Concentration、Price、Raw Previews、Copy for ChatGPT、Downloads。

### 6.2 截圖所確立的 UI 行為

- Holdings 表使用 participant、stake/percentage、holding 等清楚欄位。
- Announcements 顯示股票、期間、總數、官方搜尋連結與 publish/category/title/file info/URL 表。
- Rainbow 為 stacked area chart，提供顯示 participant 數、歷史日期數、生成按鈕、固定顏色 legend、實際 fetched dates／missing-row 說明。
- Concentration History 另以客觀時間序列呈現；Concentration 與 Price 亦有可下載／檢視的歷史表。
- Copy Report 提供可複製文字；下載區提供合併 CSV、內容預覽、各 section CSV、Markdown、Excel、raw JSON。
- 桌面寬畫面和手機窄畫面均需可讀；圖表、legend、sidebar/navigation 不可在手機上無法使用。
- 參考畫面的 Playwright/headless 控制屬參考網站實作細節，不是本平台必須暴露給終端使用者的產品功能；本平台只需提供安全、可配置的 source mode 與 timeout。

### 6.3 圖表教學內容的規格化界線

參考教學圖確立以下客觀讀圖說明，可用於 help text：

- X 軸是日期，Y 軸是持股百分比；總高度反映所顯示參與者的合計比例，每種顏色代表一個 participant，色帶厚度反映其比例。
- 可描述「穩定、回落、回升、突然集中」等可觀察形態，但不能直接下投資結論。
- 單日急升可能與配股／供股／收購、股本重整或 settlement timing 有關；必須聯同成交量、價格、公告、Top 5／10、Big Changes 檢視。
- CCASS 只見 participant/custodian 層，不見最終客戶；T+2；單點不足，需連續日期。
- 「轉倉不等於真正買入」、「入 CCASS 不一定利好」；所有情境只可作研究提示。

參考教學圖的四種情境只可作 cross-check checklist：集中度上升且特定 participant 色帶持續增厚可描述為「集中／增持形態」；一方減少、另一方增加可描述為「可能轉移形態」；公告配售／大股東入倉與單一 participant 增加可並列；高成交量、集中度下降及更多 retail participants 接貨可並列為「分散形態」。每種情境都必須同時檢查 holding date、相鄰 participant 變化、成交量／股價、正式公告、Top 5／10 和 Big Changes，且不得自動命名為收貨、轉倉、配售入倉或派貨結論。

### 6.4 i18n

預設為繁體中文（香港用語），提供 English 即時切換。中央 translation registry 至少有 `zh_HK`、`en`；文案不得散落 hard-code。缺翻譯時顯示 English fallback 並記錄 warning，不顯示空白。

語言必須涵蓋 UI、sidebar、navigation、按鈕、表頭、圖表、legend、tooltip、所有 sections、warnings/errors、stale/partial、reports、copy、CSV/Excel 顯示欄及 JSON optional labels。原始 participant/company/announcement/source text、IDs、URLs、日期、數值不得翻譯或改寫。切換語言不重新 fetch；API schema keys 不變。

中央詞彙至少採以下對照：

| English key/term | `zh_HK` |
|---|---|
| Holdings | 持股分布 |
| Changes | 持股變動 |
| Big Changes | 重大持股變動 |
| Concentration | 持股集中度 |
| Concentration History | 持股集中度歷史 |
| Rainbow | CCASS 彩虹圖 |
| Participant | CCASS 參與者 |
| Holding | 持股量 |
| Percentage of Issued Shares | 佔已發行股份百分比 |
| Percentage of CCASS | 佔 CCASS 股份百分比 |
| Snapshot Date | 資料日期 |
| Previous Snapshot | 上一個資料日 |
| Source | 資料來源 |
| Cached | 快取資料 |
| Stale Data | 資料可能過時 |
| Partial Data | 資料不完整 |
| Possible Transfer Pattern | 可能的持股轉移形態 |
| Fetch Summary | 資料擷取摘要 |
| Raw Preview | 原始資料預覽 |
| Download | 下載 |
| Copy for ChatGPT | 複製給 ChatGPT |
| Copy Report | 複製報告 |

## 7. API 與 MCP 合約

### 7.1 FastAPI 目標 endpoints

- `GET /health`
- `GET /api/v1/stocks/{stock_code}`
- `GET /api/v1/stocks/{stock_code}/holdings`
- `GET /api/v1/stocks/{stock_code}/changes`
- `GET /api/v1/stocks/{stock_code}/big-changes`
- `GET /api/v1/stocks/{stock_code}/concentration`
- `GET /api/v1/stocks/{stock_code}/rainbow`
- `GET /api/v1/stocks/{stock_code}/announcements`
- `GET /api/v1/stocks/{stock_code}/prices`
- `GET /api/v1/stocks/{stock_code}/report`
- `GET /api/v1/sources/status`

要求：metadata 先行、numeric values 是 number、participant 帶 ID、warnings 是 array、partial sections 明列、structured errors、OpenAPI 正常、optional API key（query parameter、Bearer、X-API-Key）、不 commit key、共用 service layer。

### 7.2 MCP 目標 tools

- `get_stock_summary`
- `get_ccass_holdings`
- `get_ccass_changes`
- `get_ccass_concentration`
- `get_rainbow_data`
- `get_announcements`
- `get_price_history`
- `get_full_report`

如 hosting／套件限制令 MCP 無法安全公開，仍須完成 adapter、離線測試及本機／部署啟動文件，但不得宣稱已公開可用。

## 8. 錯誤與部分成功合約

至少支援：`COLD_START`、`SOURCE_TIMEOUT`、`SOURCE_CHANGED`、`PARSE_ERROR`、`TOO_LARGE`、`INVALID_CODE`、`AUTH_FAILED`、`RATE_LIMITED`、`SOURCE_DISABLED`、`DATA_STALE`、`PARTIAL_DATA`、`INVALID_SCHEMA`、`DATE_UNAVAILABLE`。現況已有更細的 `SOURCE_FORBIDDEN`、`SOURCE_RATE_LIMITED`、`SOURCE_UNAVAILABLE`，應保留或以兼容 mapping 擴充。

每個 error 至少包括：`error_code`、safe message、source、`retry_recommended`、可選 `retry_after_seconds`、warnings、safe details。不得在錯誤、log 或 UI 暴露 API key、Cookie、完整敏感 URL/query。

## 9. 現況基線（`8966229`）

目前已有可運行的單一股票 CCASS 分析流程：

- Python、FastAPI、FastMCP、Streamlit、httpx、BeautifulSoup、Pydantic Settings。
- `GET /health`、JSON holdings API、Markdown report API、MCP holdings tool，以及 Streamlit 查詢流程。
- Webb-site primary/fallback adapter 保留 code／issue identity 驗證、timeout、size/rate limits、memory cache 及結構化 upstream error。
- `DATA_SOURCE=auto|webbsite|google_drive_csv`；CSV-only 模式不建立或呼叫 Webb-site client。
- Google Drive CSV 支援一般分享、direct-download 及 Google Sheets URL；有 timeout、串流大小上限、HTML／登入頁偵測、required/duplicate/row schema 驗證、UTF-8-SIG、memory cache、last-known-good 與安全 URL logging。
- `ccass_core.collector` 提供最小 SQLite JSON snapshot store、watchlist、latest/previous、原子 CSV export、CLI 與 scheduler 安裝器。
- `compute` 提供客觀 changes、big changes、transfer-like patterns、concentration 與 warnings；`report` 輸出固定九節 Markdown、ChatGPT payload 與下載檔名。
- Streamlit 已有輸入驗證、holdings limit／threshold 控制、進度、diagnostics、rendered/raw Markdown、copy 與下載；deployment 設定已加入。
- 離線 tests 已擴至 Google CSV、routing、collector、compute、report、UI、deployment 與 report API。

尚未完成的目標包括完整 normalized SQLite schema/migrations、resumable historical backfill、多 section 歷史資料、真正 DT rainbow、announcements、price、完整 i18n／exports／API／MCP／source diagnostics 及公開部署驗收。現有 collector/analysis/UI 是 Phase 1–4 的局部交付，不代表相關 phase gate 已完成；狀態以 [ROADMAP.md](ROADMAP.md) 與 [`TASK.md`](../TASK.md) 為準。

### 9.1 Git 歷史基線

- `bff99d8`：Initial CCASS platform MVP。
- `7722bf2`：以單次可驗證 stock-code holdings 查詢降低上游 timeout；timeout budget 收斂。
- `fad4411`：分類 upstream mirror failures、加入安全 browser-like headers、避免把 403/429/5xx 誤報為 timeout，並增加測試。
- `4752183`：新增 Google Drive CSV data source、安全下載、schema validation、memory cache/last-known-good 與 routing tests。
- `cbeee7f`：新增 collector、客觀分析、九節報告、Streamlit workflow、deployment assets 與擴充 API/tests。
- `8966229`：抑制 collector request 完整 URL logging，避免洩漏 query parameters。

## 10. 完成定義

不得以空 UI、mock-only、單日圖、無 fixture parser、無日期／來源、placeholder API/MCP、空 array、未驗證 DisclosureTracker、插值歷史或僅最新 snapshot 宣稱完成。

整體完成必須同時滿足：

- 真實合法公開來源可取數且核心數字與 golden stock 抽樣核對。
- 歷史可保存、collector 可 idempotent、backfill 可 resume。
- Rainbow 由真實 snapshots 生成且顏色穩定。
- 所有 downloads、共用 API/MCP/service、結構化 errors 可用。
- 離線與適當 live tests 通過；Git 工作樹乾淨；已 commit/push。
- 公開 Streamlit 實際驗收通過，資料日期、來源、warnings、T+2 和 mobile usability 均已檢查。

詳細 gate 見 [ROADMAP.md](ROADMAP.md)。

## 11. 規格追溯索引

| 原始內容 | 正式落點 |
|---|---|
| Master Prompt 1–3（工作方式、分工、最高原則） | 本文件 §§2–4；[DEVELOPMENT_RULES.md](DEVELOPMENT_RULES.md) |
| Master Prompt 4–5（來源架構與優先序） | [DATA_SOURCE_GUIDE.md](DATA_SOURCE_GUIDE.md) |
| Master Prompt 6–11（DB、collector、backfill、rainbow、顏色、異常） | [ARCHITECTURE.md](ARCHITECTURE.md) |
| Master Prompt 12–17（比較、集中度、公告、功能、UI、語言、下載） | 本文件 §§5–6 |
| Master Prompt 18–20（API、MCP、errors） | 本文件 §§7–8；[ARCHITECTURE.md](ARCHITECTURE.md) |
| Master Prompt 21–22（tests、自動執行） | [DEVELOPMENT_RULES.md](DEVELOPMENT_RULES.md) |
| Master Prompt 23–25（phase、完成、回報） | [ROADMAP.md](ROADMAP.md)；[DEVELOPMENT_RULES.md](DEVELOPMENT_RULES.md) |
| 完整指南 0、4、6（核心／三出口／JSON） | 本文件 §§3–4、7；[ARCHITECTURE.md](ARCHITECTURE.md) |
| 完整指南 1–5（來源、衝突、flow、實戰守則） | [DATA_SOURCE_GUIDE.md](DATA_SOURCE_GUIDE.md) |
| 完整指南 7（golden stock、fixtures、secrets、格式、時區、changelog、monitor） | [DEVELOPMENT_RULES.md](DEVELOPMENT_RULES.md) |
| 截圖 1、4、5（holdings、announcements、tables、navigation、controls） | 本文件 §§5–6 |
| 截圖 2（copy/downloads） | 本文件 §5.10 |
| 截圖 3、8（desktop/mobile rainbow） | 本文件 §§5.7、6.2 |
| 截圖 6、7、9（讀圖、時段、情境、限制、checklist） | 本文件 §6.3 |
| 參考網站 | 本文件 §§1、6；只作功能／UX 參考，不作資料或程式依賴 |
