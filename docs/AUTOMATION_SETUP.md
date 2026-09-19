# AUTOMATION SETUP — GitHub Actions 排程（零成本，§8.0）

> 建立日期：2026-09-19。兩條 workflow 已在 repo 內，**只需喺 GitHub 加一個 secret 就啟動**。

## 要跑乜

| Workflow | 排程 | 做乜 |
|---|---|---|
| `daily-ccass-snapshot` | 週一至五 08:15 HKT | 喚醒 Render → 觸發 52 股 watchlist CCASS 快照 job → 輪詢到完成 |
| `keepalive` | 每 10 分鐘 | ping `/health`，防免費層瞓覺（HKT 交易時段保持暖機）|

## 你要做嘅一步（約 2 分鐘）

1. 開 https://github.com/Joelikecoin/joe-ccass-platform → **Settings** → **Secrets and variables** → **Actions**
2. **New repository secret**
   - Name：`API_KEY`
   - Secret：貼上 `.env` 入面嗰條 `API_KEY`（64 位 hex，Render Environment 都見到）
3. 完成後去 **Actions** 分頁 → 揀 `daily-ccass-snapshot` → **Run workflow** 手動行一次測試 → 見到綠剔 + job terminal state 就成

## 安全

- `API_KEY` 只會喺 GitHub secret 入面，唔會出現喺 log 或 code
- Render 嘅 admin 路由本身已經要 key（fail-loud），secret 洩漏就去 Render 換

## 未來隊列（未實作，記錄用）

- 每日 DI / announcements / fundamentals 累積（watchlist 全批，用 `/admin/*` 異步 job）— 事件層「累積歷史庫」嘅主糧
- corporate-timeline 5y 異步 job
- RTSS Layer-1 收市榜（獨立項目，規格已喺 `latest_reference_updates/20260912 技術規格書`）
