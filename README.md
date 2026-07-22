# HK CCASS Shareholding Analysis Tool
## Project specification

本 Repository 的唯一規格來源（Single Source of Truth）是：

- [Project Specification](docs/PROJECT_SPEC.md)
- [Data Source Guide](docs/DATA_SOURCE_GUIDE.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Development Rules](docs/DEVELOPMENT_RULES.md)
- [Roadmap](docs/ROADMAP.md)
- [Current Task Board](TASK.md)

外部 Master Prompt 已被上述文件取代。新需求、規格變更與目前進度只更新這組文件及 `TASK.md`，不再維護另一份單一 Master Prompt。

Streamlit-first 香港 CCASS 研究工具，共用同一套正規化、低頻 fetch/parse、計算及 Markdown
報告核心，並保留 FastAPI、MCP、Google Drive CSV snapshot 與本機 collector。

> CCASS 是結算層面的代名人持倉資料，不等同實益擁有人，通常亦涉及 T+2。工具不會把缺失
> 數據補成估算值；無資料的報告章節會明確顯示 `DATA NOT AVAILABLE — 原因`。

## Streamlit 功能

- 接受一至五位數字的股票代碼，例如 `1592` 會正規化為 `01592`；`abc` 會顯示 validation error。
- `Fetch`、sidebar holdings limit／big-change threshold、階段式 progress。
- 報告固定包含：AI Analysis Ready Summary、Fetch Summary、Metadata、Holdings Summary、
  Holdings、Changes、Big Changes、Concentration、Data Quality Warnings。
- 同時提供 rendered Markdown、Raw Markdown、Copy for ChatGPT、Copy report 及 Download `.md`。
- 網絡或來源失敗仍會產生完整九章診斷報告，不會靜默省略章節。

## 架構

```text
ccass_core/
  normalize.py       股票代碼正規化
  fetch_webb.py      共用低頻 Webb-site/Renavon fetch/parse adapter
  compute.py         diff、big changes、transfer-like pattern、concentration、warnings
  report.py          固定九章 Markdown 與 ChatGPT copy payload
  collector.py       一次性本機 snapshot collector、SQLite、原子 CSV export
app/
  sources/           安全鏡像 client 與 Google Drive CSV source
  services/          auto/webbsite/google_drive_csv 選擇
  api.py             既有 JSON API 與共用 Markdown report endpoint
streamlit_app.py     Streamlit Community Cloud 入口
```

所有測試 fixture 均標示為測試資料；repository 不包含虛構的正式 CCASS snapshot。

## 資料來源策略

`DATA_SOURCE` 支援：

- `auto`（預設）：低頻 Webb-site/Renavon 公開鏡像優先；如已配置 `CCASS_CSV_URL`，鏡像失敗
  才使用 collector 產生的 Google Drive CSV snapshot。
- `webbsite`：只使用鏡像。
- `google_drive_csv`：只使用 CSV，程式不會建立或呼叫鏡像 client。

鏡像設有 browser navigation headers、timeout、rate limit、記憶體 cache、安全錯誤分類與 attribution。
CSV 支援 Google Drive 一般分享、直接下載及 Google Sheets 分享連結，並設 timeout、串流大小上限、
UTF-8/schema/row 驗證、記憶體 cache 與 last-known-good。日誌不記錄完整 Google Drive URL、URL
參數、API key、Authorization 或 Cookie。

CSV 欄位見 [`examples/ccass_template.csv`](examples/ccass_template.csv)。範本只有 header；使用者不需
手工建立完整 CSV，本機 collector 可自動輸出符合 schema 的 snapshot。

## HKEX SDW 合規界線（2026）

本專案**沒有亦不會啟用 HKEX SDW 自動 GET/POST、scraper、browser automation、Cloudflare/CAPTCHA
繞過或 access-control 規避**。HKEX CCASS shareholding search 的現行條款第 2.3 項禁止在未獲明確
書面許可下，以 programmatic、scripted 或其他機械方式存取該設施或資料；HKEX 一般網站條款亦
禁止未獲許可的 automated scraping／text and data mining。官方條款：

- [HKEX CCASS Shareholding Search Terms of Use](https://www.hkexnews.hk/homeCCASSSearch.html)
- [HKEX Website Terms of Use](https://www2.hkexnews.hk/Global/Exchange/Terms-of-Use?sc_lang=en)

SDW 在本工具中只列為人手核對來源。未來只有在取得適用的 HKEX 明確書面許可後，才可另行設計
adapter；不得把本 repository 現有程式改作繞過存取限制。

## 本機啟動

```powershell
Copy-Item .env.example .env
python -m venv .venv
.venv\Scripts\pip install -e ".[dev]"
.venv\Scripts\streamlit run streamlit_app.py
```

另開終端啟動 FastAPI：

```powershell
.venv\Scripts\uvicorn app.api:app --reload
```

端點：

- JSON：`GET /api/v1/ccass/{code}`
- Markdown：`GET /api/v1/ccass/{code}/report`
- 健康檢查：`GET /health`
- FastMCP Streamable HTTP：`/mcp`

API key 可使用 `?key=`、`X-API-Key` 或 Bearer token。未設定 `API_KEY` 時只適合本機開發。

## Streamlit Community Cloud 部署

1. 把 repository 的 `main` branch 連接到 Streamlit Community Cloud。
2. App entrypoint 選 `streamlit_app.py`；依 `requirements.txt` 安裝依賴。
3. 在 Advanced settings > Secrets 貼入所需 TOML。最少可只設 `DATA_SOURCE="auto"`；如要使用
   collector fallback，再加入可公開下載的 `CCASS_CSV_URL`。格式參考
   [`.streamlit/secrets.toml.example`](.streamlit/secrets.toml.example)。
4. Deploy。應用不需要 HKEX 登入資料，也不應加入任何 HKEX cookie、CAPTCHA token 或 SDW secret。

`.streamlit/config.toml` 已啟用 headless 與 XSRF protection。部署後請先用 `01592` 做低頻 smoke
test；實際數字必須來自當次來源，不能以 fixture 數字代替。

## 本機低頻 collector

Collector 是一次性命令，預設 watchlist 為 golden stock `01592`。它只使用共用公開鏡像核心，
不存取 HKEX SDW；每次成功結果寫入 SQLite 歷史，再以同目錄 temporary file + `os.replace` 原子
更新 CSV。輸出包含 snapshot timestamp、source cached flag、holdings date 與 T+2 settlement note。

```powershell
.venv\Scripts\python -m ccass_core.collector `
  --watchlist "01592,00700" `
  --sqlite "data\ccass_snapshots.db" `
  --output "C:\Users\you\Google Drive\CCASS\ccass_snapshot.csv"
```

亦可用 `CCASS_WATCHLIST`、`CCASS_SQLITE_PATH`、`CCASS_CSV_OUTPUT_PATH` 配置。建議每日只執行一次，
並保持 `MIN_REQUEST_INTERVAL_SECONDS`。collector 不會自行常駐或建立排程。

Windows 排程安裝腳本位於 [`scripts/install_collector_task.ps1`](scripts/install_collector_task.ps1)。
先用 `-WhatIf` 檢查；只有使用者明確確認並手動執行時才建立系統排程：

```powershell
.\scripts\install_collector_task.ps1 `
  -RepositoryPath $PWD `
  -PythonExecutable "$PWD\.venv\Scripts\python.exe" `
  -CsvOutputPath "C:\Users\you\Google Drive\CCASS\ccass_snapshot.csv" `
  -WhatIf
```

移除 `-WhatIf` 時，腳本因 `ConfirmImpact='High'` 會要求確認。本專案安裝／部署流程不會自動執行它。

## 測試與品質檢查

```powershell
.venv\Scripts\python -m ruff check .
.venv\Scripts\python -m pytest -q
```

測試不使用 live network；HTTP 行為以 mock，報告與 collector 使用明確標示的 fixture。正式研究仍應
以獲准的人手 SDW 查詢、HKEX 公告及權益披露交叉核對。
