# NEXT SESSION TASK — 公司機一次性工程（2026-09-21）

> **用法：** 公司機開 ZCode → `git pull` → 貼以下整段俾 ZCode → 授權寫入 → 收工。
> **前置：** 公司機 `.env` 已有 RENDER_API_KEY / TURSO_*（舊 API_KEY 冇所謂，任務 1 會自我更新）。

---

## 貼俾 ZCode 嘅開場白（整段 copy）

```text
read PROJECT_PROGRESS_V3.md §12 同 docs/NEXT_SESSION_COMPANY_TASK.md
你獲得完整寫入授權（fail-loud 規矩照舊）。今日工程兩項，一次過做晒，做完先收工：

【任務 1：公司機 .env 換新 API_KEY（3 分鐘）】
用公司機 .env 嘅 RENDER_API_KEY 呼叫：
GET https://api.render.com/v1/services/srv-dads94740ujc73cpdktg/env-vars/API_KEY
（Bearer 用 RENDER_API_KEY）讀出現時 API_KEY 值（64 位 hex，5cad 開頭），
直接寫入公司機 .env 嘅 API_KEY= 行。key 值唔好印出嚟、唔好貼去對話。

【任務 2：股本分段持久化（V3 §12 backlog，設計已定，~1-2 小時）】
背景：share-capital job 一次過抓 5 年月報表 PDF（~60 份）→ >8-10 分鐘 → 免費容器死 → 零持久。
實測大股細股一樣死，係「一次抓太多」問題。
a. 核實 app/sources  share-capital 鏈有冇真正用 start_date/end_date 收窄抓取範圍；冇就補上
b. discovery 加「月報表 / Monthly Return」標題過濾，收窄文件集
c. 本地測試（venv ..\.venv-joe-ccass）：單年窗 job 應該 2-3 分鐘內完成並持久
d. commit + push → Render 手動 redeploy → 回填五隻股：
   02318 / 00941 / 00256 / 00397 / 08283，各 5 個年份窗（2021-2025），
   逐個觸發 POST /admin/share-capital/job?stock_code=X&start_date=YYYY-01-01&end_date=YYYY-12-31
   → 輪詢 → 下一個；容許個別撞容器，health-gate 等 /health 200 再續
e. Turso 驗證：五隻股 share_capital_history 全部 > 0 行（SELECT stock_code, COUNT(*) GROUP BY）

【收尾】
更新 PROJECT_PROGRESS_V3.md §12：項目 1（股本）正式關閉 + 今日證據；
commit + push 兩條 branch（p0-runtime... 同 main）；
刷新雲端鏡像：G:\我的雲端硬碟\投資 - 享受與豐盛\AI Projects\joe-ccass-platform\PROJECT_PROGRESS_V3.md
```

---

## 任務 2 驗收標準（fail-loud）

| 檢查 | 標準 |
|---|---|
| 單年窗 job | ≤ 3 分鐘 terminal state + Turso 有行 |
| 五隻股回填後 | `share_capital_history` 每隻 > 0 行，年份覆蓋 2021-2025 |
| 事件層 | share_capital_change 事件出現喺 intelligence_events |
| 舊路徑 | 全 5 年一次過 pull 嘅舊行為保留喺冇窗參數時（或明確禁用並報錯提示用窗） |

## 完成後平台狀態

除咗 7 個月缺口（私人途徑數據待導入）——**所有 domain、所有證據股、全部完整**。
