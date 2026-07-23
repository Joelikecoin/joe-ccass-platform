# Data Source Guide

> 本文件是資料來源、資料優先序、fetch 安全、欄位與衝突處理的唯一規範。產品範圍見 [PROJECT_SPEC.md](PROJECT_SPEC.md)，元件設計見 [ARCHITECTURE.md](ARCHITECTURE.md)。

## 1. 資料策略

平台只把可合法、穩定、低頻取得且可驗證的公開資料源加入 active fetch flow。來源註冊必須 configuration-driven，以下設定不可散落 hard-code：

- source ID、display name、base URL、enabled/status、priority；
- timeout、bounded retry、rate limit、minimum sleep；
- cache policy、stale/last-known-good policy；
- parser ID/version、支援 sections、date coverage；
- attribution、terms/robots audit date、known limitations；
- fallback eligibility、warnings、diagnostic health。

Source status 至少分為：`active`、`fallback`、`manual_import`、`experimental`、`unverified`、`disabled`。未完成 audit 的來源不得預設 active。

## 2. 通用 fetch 與資料誠信規則

1. 每個 request 有 connect/read/total timeout、檔案大小限制、合理 User-Agent、rate limit 和 bounded retry；不無限重試。
2. HTML/PDF/CSV parser 與 network fetch 分離；parser 接受 bytes/text/fixture，不自行上網。
3. 回應先檢查 HTTP status、content type、size、登入／challenge／error page，再 parse schema。
4. 不繞過登入、CAPTCHA、Cloudflare challenge、付費牆、Cookie 或 access control。
5. 不把私人 API、憑證、完整敏感 URL/query 或 API key 寫入 log、error、fixture、report。
6. Log 只保留 source ID／hostname、safe path label、status、latency、size、error type、request ID；query values 預設 redact。
7. live source 失敗不可回空資料；使用 cache/fallback 時清楚標示來源版本、資料日、cache age 和 warning。
8. last-known-good 可維持服務可用性，但永遠不能冒充 live/latest；超過 freshness policy 回 `DATA_STALE` 或明確 partial/stale response。
9. 同一事實有衝突時保留候選值、來源與日期，列出 conflict warning，不靜默覆蓋。
10. 時區使用 `Asia/Hong_Kong`；日期輸出 `YYYY-MM-DD`，並分清 data/snapshot date、announcement publish date、effective date、fetched_at。

## 3. 各類資料的優先序

### 3.1 CCASS

1. Webb-site mirror（正常日常主來源）。
2. 本地 SQLite latest-known-good，必須 `cached=true` 並顯示 snapshot date。
3. 經驗證的 Google Drive／CSV history，必須標示 cached/imported、來源 identifier 和匯入時間。
4. HKEX SDW 官方單日 snapshot，用作後備、補充和抽樣核對。
5. 結構化失敗。

### 3.2 Announcements

1. HKEXnews 正式公告／索引。
2. 本地公告索引 cache，標示 cached 和 cache date。
3. 結構化失敗。

新聞摘要只可協助發現文件，不可取代正式公告。

### 3.3 Price

1. Webb-site price history。
2. 已 audit 並核准的公開 price adapter。
3. cached price history。
4. 結構化失敗。

### 3.4 Conflict authority

當數字／條款互相衝突，按以下證據權威排序，但仍要列出衝突：

1. 最新 HKEXnews 正式公告。
2. HKEX 法定權益披露（DI/SDI）。
3. HKEX SDW／Webb-site 最新 CCASS 實際數據。
4. 公司官網／財務報告。
5. 同花順等整理型來源。
6. AAStocks／新聞。
7. Investing.com／Yahoo 等行情來源。

「較高權威」不等於可忽略日期或百分比基準；比較前必須先確認同一證券、同一日期／事件和同一 denominator。

## 4. Webb-site mirrors

### 4.1 角色與 endpoints

Primary：`https://webbsite.0xmd.com/`。可配置 fallback mirror；不得假設各 mirror 所有 endpoints 行為一致。

目標用途：Company、Holdings、Changes、Big Changes、Concentration History、CCASS history、可用時的 Price History、人物／董事及企業事件輔助資料。

典型 endpoints：

- company／issue mapping：`/dbpub/orgdata.asp?code={stock_code}&Submit=current`
- latest holdings：`/ccass/choldings.asp?i={issue_id}`，或經驗證的 stock-code route
- changes：`/ccass/chldchg.asp?i={issue_id}`
- big changes：`/ccass/bigchangesissue.asp?i={issue_id}`
- concentration history：`/ccass/cconchist.asp?i={issue_id}`

### 4.2 Identity safety

- 股票代號不等於 issue ID。所有 issue ID 必須由精確 stock-code security block 解析，或由回傳頁內 code + hidden issue ID 雙重核對。
- 同一公司多種貨幣／證券（例如五位 code 不同）不得混用 issue ID。
- mapping 可長期 cache，但要保存 first/last verified time、source 和驗證證據；公司行動或來源矛盾時重新核對。
- 找不到或多個 candidate 時回 `NOT_FOUND`／`SOURCE_CHANGED`，不可選第一個猜測。

### 4.3 Holdings 欄位

至少解析並保存：`participant_id`、原文 name、holding、`pct_of_issued`、`pct_of_ccass`（可支持時）、cumulative percentage、issued shares、issued-shares-as-of、snapshot date、totals、concentration、source metadata、warnings。

必須處理 stock split、bonus/rights issue、placement、consolidation/subdivision、股本基數更新滯後、>100%、participant rename/missing/duplicate、T+2、partial data、HTML 改版和 parser failure。

### 4.4 現況與限制

在 `8966229`，此來源仍是 `auto`／`webbsite` 模式的 live adapter；已有 primary/fallback、12 秒 timeout、1 秒最小 interval、5 MB limit、memory cache，以及 403/429/5xx/challenge/timeout/network 的分類。現況只有最新 Holdings，不代表其他 sections 已完成。

## 5. HKEX SDW

URL：`https://www3.hkexnews.hk/sdw/search/searchsdw.aspx`

角色：官方單日 CCASS snapshot、抽樣核對 Webb-site、Webb-site 故障時後備、collector 指定日期補充及有限歷史補充。

限制與要求：

- 只作合理低頻，不能大量高頻抓取。
- 正確處理官方 POST form，但不得繞過網站限制、登入或驗證。
- 官方可查歷史有限，不得因此刪除本地已保存 snapshots。
- 若無法穩定安全自動化，保留 `manual_import` CSV 流程。
- Golden stock 核對必須記錄 stock code、data date、participant、holding、percentage、basis、official URL/identifier。

## 6. HKEXnews

URLs：

- `https://www.hkexnews.hk/`
- `https://www1.hkexnews.hk/search/titlesearch.xhtml`

角色：公司正式公告的權威錨點。需要保存 publish time、category、official title、PDF URL、中／英文版本、file size、event tags、extraction status。

PDF 常見 path 可按官方列表取得；不得假設或只靠拼 URL。SEHK/GEM 路徑及 `_c.pdf`／`_e.pdf` 語言差異要保留。外籍人名／BVI 公司名可能只在英文版準確，正式 title 不自行翻譯。

PDF fetch/extraction：

- 設定 timeout、bytes 和 extracted-text length limit。
- 單一 PDF failure 不拖垮公告列表。
- 永遠保留 official PDF URL 和 extraction status。
- 摘要／新聞轉載不得代替公告原文。

## 7. HKEX DI／SDI

URL：`https://di.hkex.com.hk/`

角色：5% 以上大股東和董事法定披露，用於實益擁有人、增減持、平均價與日期的客觀資料。它補充 CCASS participant/custodian 層，但不能把兩者自動等同。

在 source audit、條款、query stability、schema 和 fixtures 完成前，保持 `unverified`／`experimental`，不得阻塞核心 CCASS。

## 8. 同花順港股

候選入口：`https://q.10jqka.com.cn/hk/`；完整指南亦記錄個股頁 `https://stockpage.10jqka.com.cn/`。

候選用途：股本變動、已發行股本、回購、公司基本資料。只有公開、免登入、無 CAPTCHA／私人 Cookie、terms/robots 無明確禁止、低頻穩定、欄位與日期清楚時才可 active。

不適合自動化時：建立 disabled adapter、記錄原因、提供人工 CSV/XLSX import。它只屬整理型補充；與 HKEXnews 衝突以正式公告為權威，且失敗不可令核心 CCASS 報告失敗。

## 9. DisclosureTracker

候選入口：`https://www.disclosuretracker.com/`。

只作 UI／功能／視覺參考，不是必要依賴。安全 discovery 只可確認網站用途、是否與香港披露／CCASS 有關、是否需登入／訂閱／API key／付費、公開 terms/robots/API/download、欄位／日期／限制。

除非公開、合法、穩定且直接相關已被清楚證實，必須標成 `experimental`／`unverified`／`disabled`，不得進正式 fetch、不得用私人 API/Cookie、不得繞過登入。Rainbow 不得依賴此來源。

## 10. Price adapters

優先 audit Webb-site price history。不可用時才評估可插拔 fallback：

- Yahoo Finance：港股 ticker 如 `0700.HK`；容易自動化但細價股可能缺日。
- hk.investing.com：可作 OHLC/volume 後備，但互動頁與反爬限制較高；不得當即時價。
- 任何 adapter 均需標 adjusted/unadjusted、source、date、OHLC、volume、可選 turnover、missing dates。

未完成 terms/robots/stability audit 前不可 active。不得建立即時報價保證或交易功能。

## 11. AAStocks 與新聞

AAStocks／新聞只可作 source discovery、快速人工核實和正式文件 fetch 失敗時的線索。摘要不代替公告，關鍵條款回到 HKEXnews。若日後自動化，須先獨立 audit；它不是核心資料依賴。

## 12. Google Drive、CSV、XLSX 與人工匯入

人工整理事件庫、官方 SDW export、歷史 snapshots 可經 CSV/XLSX 匯入。Google Drive 只是一種檔案傳輸／保存位置，不提升資料權威。

所有匯入 adapter 必須：

- 對 URL／檔案設定 timeout、最大 bytes、content type 與 schema validation。
- Google Drive 一般分享 URL 只可轉成官方 direct-download 形式；登入頁、權限頁或 HTML 回 `DATA_SOURCE_ERROR`／兼容的 structured error。
- 不 log 完整 Drive URL、file token、query parameters、API key。
- 使用 memory cache；下載成功且 schema valid 才更新 last-known-good。失敗時可回明確標記的 last-known-good，不得標最新。
- CSV 用正式 parser，正確處理 UTF-8/UTF-8-SIG、引號、逗號、空值；不可用簡單字串 split。
- schema version、required columns、stock code、snapshot date、participant identity、source/date/warnings 全部驗證。
- 原子寫檔：temporary file + atomic replace；transactional database import；同日重跑 idempotent。
- 缺資料不得補造；正式資料與人工整理衝突時列 warning。

`8966229` 已實作 `DATA_SOURCE=google_drive_csv`、`CCASS_CSV_URL`、上述下載防護、schema validation、memory cache、安全 logging，以及 CSV-only 不呼叫 Webb-site。P1-06再把latest Holdings的完整、已驗證last-known-good統一至normalized SQLite store；`HOLDINGS_LKG_MAX_AGE_SECONDS`控制最大age，HTML/login/schema/identity/date/disabled等integrity failures不可回退。任務狀態以 [`TASK.md`](../TASK.md) 為準。

## 13. Canonical normalized records

### 13.1 Snapshot/Holding

- stock code、issue ID、snapshot date；
- participant ID、原文 name、holding；
- `pct_of_issued`、`pct_of_ccass`；
- issued shares、issued-shares-as-of；
- source ID、safe source identifier/URL、fetched_at；
- cached/stale/partial flags、warnings、parser/schema version；
- raw provenance reference/checksum。

### 13.2 Announcement

- stock code、publish time、category、official title/language；
- official document URL、file size、event tags；
- extraction status、fetched_at、source、warnings。

### 13.3 Price

- stock code、price date、OHLC、volume、可選 turnover；
- adjusted state、source、fetched_at、missing-date warnings。

數字欄必須是 number，不把格式化字串當 canonical value。原始值可另存作 provenance。

## 14. Source diagnostics

`/api/v1/sources/status` 與 UI diagnostics 最終應顯示：source ID/status、last success/failure、safe error class、latency、data freshness、cache availability、parser version、audit state、disabled reason。不得發出對所有來源的高頻 probe；diagnostics 也受 rate limit。

## 15. Audit checklist

每個新 source adapter 上線前回答：

- 是否公開、免登入、無 CAPTCHA／付費牆／私人憑證？
- terms/robots 是否允許此低頻用途？audit 日期？
- identifiers、日期、timezone、denominator 是否清楚？
- timeout、size、rate、retry、cache、fallback 是否有設定？
- login/challenge/HTML error 是否 fail loud？
- parser 是否有 saved fixture、malformed fixture、schema drift test？
- 是否會洩露 URL query、key、cookie、私人路徑？
- 是否有 attribution、warnings、source/date metadata？
- 是否能被停用而不拖垮不相關 sections？
