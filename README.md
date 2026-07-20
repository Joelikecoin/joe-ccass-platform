# Joe CCASS Platform

一套供 AI 與人手使用的港股 CCASS 查詢 MVP，共用同一個 fetch／parse／normalize 核心，提供：

- FastAPI JSON：`/api/v1/ccass/{code}`
- 健康檢查：`/health`
- FastMCP Streamable HTTP：`/mcp`
- Streamlit 人手查詢與 JSON／CSV 匯出

## 核心原則

- 所有股票編號先正規化為五位數。
- 先由股票編號解析 Webb-site issue ID，絕不猜測 ID。
- 每份結果附來源、抓取時間、資料日期及 T+2 提示。
- 錯誤以結構化 error code 回傳；不以空陣列假裝沒有資料。
- 只自動存取容許使用的 Webb-site／Renavon 公開鏡像；HKEX SDW 僅供人手核對。
- 使用資料時必須標示：資料源自 Webb-site.com／Renavon，CC-BY 4.0。

## 本機啟動

```powershell
Copy-Item .env.example .env
python -m venv .venv
.venv\Scripts\pip install -e ".[dev]"
.venv\Scripts\uvicorn app.api:app --reload
```

另開終端啟動 Streamlit：

```powershell
.venv\Scripts\streamlit run streamlit_app.py
```

API key 可使用 query parameter `?key=`、`X-API-Key` 或 Bearer token。未設定 `API_KEY` 時，
只適合本機開發，API 不會要求認證。

## 資料限制

CCASS 是結算層面的代名人持倉資料，不等同實益擁有人。資料通常涉及 T+2；鏡像亦可能延遲、
中斷或改版。正式研究應以 HKEX 公告、權益披露及獲准的人手 SDW 查詢交叉核對。

