# interface.md — ZCode（工程側）↔ GPT（研究側）資料合約

> **狀態:** v0.1 DRAFT（2026-09-22）— 待 GPT 做 Research Base Completeness Review，待業主批准
> **權威:** 本文件是兩側唯一數據合約。衝突時以本文件 + `PROJECT_PROGRESS_V3.md` 為準。
> **規則:** 任何一方要改本文件內容（欄位、格式、口徑），必須先向業主提出，批准後由擁有方修改，**不得靜默變更**。
> **分工:** ZCode 擁有 §1–4（平台側合約）；GPT 擁有 §5（研究側輸出合約，現為佔位，待 GPT 申報）。

---

## 0. 角色與邊界

| | ZCode（工程側） | GPT（研究側） |
|---|---|---|
| 負責 | 前端、後端、DB、API、MCP、部署、數據管道 | 教材研究、股票分析、財技框架、案例、證據鏈 |
| 不得修改 | 研究邏輯、分析框架、判斷規則、輸出定義 | 平台代碼、DB、API、部署 |
| 取數方式 | — | 只透過平台 API / 匯出數據 |
| 跨區請求 | 一律經業主審批，不得直接派對方執行 | 同左 |

---

## 1. 通用口徑（Global Conventions）

### 1.1 時區
- 所有**交易日/日期**（`price_date`、`announcement_date`、snapshot date 等）為 **香港日期**（`Asia/Hong_Kong`），存儲為 `date`（無時間成分）。
- 涉及**時間戳**的欄位（如 `fetched_at`）為 UTC（ISO 8601，帶時區標記）。研究側比較「幾時攞嘅數」用呢個，比較「邊個交易日」用香港日期。
- HKEX/CCASS 公佈嘅持股資料反映嘅係香港交易日收市後狀態。

### 1.2 幣別
- 港股平台，價格與成交額預設 **HKD**。
- 欄位 `currency` 會明確標示（見 `PriceHistoryMetadata.currency`）；`currency: null` = 未確認，**不得假設**。
- 如未來引入非 HKD 數據（如美元計價公告金額），會喺欄位層級標明，唔會混在同一欄。

### 1.3 複權（Price Adjustment）
- 價格數據帶 `adjustment_state`，只有兩個值：`"adjusted"` / `"unadjusted"`（見 `PriceHistoryMetadata.adjustment_state`，預設 `adjusted`）。
- `close` / `open` / `high` / `low` / `vwap` = 原始（未複權）價；`adjusted_close` = 複權收市價。
- 複權方法與細節記錄在 `adjustment_note`；`adjustment_note: null` = 無特別註記。
- ⚠️ 研究側做長期價格比較必須用 `adjusted_close`；用原始 `close` 前必須檢查 `adjustment_state`。

### 1.4 缺失值語義（Missing Semantics）
| 表示法 | 含義 | 研究側處理 |
|---|---|---|
| `null` / 欄位缺省 | 該數據點不存在（未採集/來源無提供） | 當缺失，不得推算 |
| `[]`（空陣列） | 查詢成功但無記錄（可能該日無數據） | 當缺失，唔等於「持股為零」 |
| `DEFERRED_DATA_GAP` 標記 | **已知人為缺口**：CCASS `2025-12-25 → 2026-07-21`（Webb 最後有效 2025-12-24，Longbridge 觀察最早 2026-07-21/22） | 必須當缺失；**禁止插值、禁止造假補數**；缺口日待業主由私人途徑補數 |
| `*_est` 欄位（`turnover_est`、`vwap_est`） | 平台**估算值**（非來源原始數） | 可用但須標明係估算 |
| `data_quality_warnings` | 回應中列出的品質警示 | 出現時必須讀取並納入分析限制說明 |

⚠️ **「無記錄 ≠ 零持股」**：CCASS/Longbridge 缺一日數據唔代表股東沽清，只代表嗰日無觀察。

### 1.5 股票代碼格式
- 路徑參數 `stock_code` / `code`：HKEX 5 位數字代碼（如 `00388`、`01810`），保留前導零。
- B轉/人民幣櫃台等特殊後綴（如有）以平台回應嘅 `ticker` 為準。

---

## 2. 現有 API 端點總覽（ZCode 維護）

生產環境：`https://joe-ccass-api.onrender.com`（Render，commit `3324d86`，production branch `p0-runtime-api-key-fingerprint-proof`）
部分端點需 API key（`verify_api_key`）。系統端點：`GET /health`。

### 2.1 股票數據（`/api/v1/stocks/{stock_code}/...`）
| 端點 | 內容 |
|---|---|
| `/` | 股票基本資料 |
| `/prices` | 價格歷史（§1.2–1.4 口徑，`PriceHistoryResponse`） |
| `/fundamentals` | 基本面 |
| `/holdings` | CCASS 持股 |
| `/big-changes` / `/big-changes/report` | 大變動 + 報告 |
| `/changes` / `/changes/report` | 變動 + 報告 |
| `/concentration` / `/concentration/evidence` / `/concentration/report` | 集中度 + 證據 + 報告 |
| `/announcements` | 公告 |
| `/corporate-timeline` | 公司時間線 |
| `/stock-events` | 股票事件 |
| `/capital-information` / `/share-capital-history` | 股本資料 / 歷史 |
| `/disclosure-interests` | 内部人士披露（DI） |
| `/officers` | 董事/高管 |
| `/document-entities` | 文件實體抽取 |
| `/history` / `/history/snapshots` | 歷史快照 |
| `/historical-intelligence` | 歷史 intelligence |
| `/rainbow` | Rainbow 視圖數據 |
| `/report` | 綜合報告 |
| `/raw-previews` | 原始數據預覽 |
| `/download/{section}/{kind}` | 下載 |

### 2.2 CCASS 專項（`/api/v1/ccass/{code}/...`）
`/`（快照）、`/ai-read-model`（AI 讀取模型）、`/report`

### 2.3 Longbridge 專項（`/api/v1/longbridge/{stock_code}/...`）
`/holdings`、`/holding/{period}`、`/holding-daily/{broker_id}`、`/static-info`

### 2.4 系統/來源
`/api/v1/sources/status`（各數據源狀態）

> 精確 request/response schema 以 `app/models.py` Pydantic model 為準；本表只做導航。研究側如需某端點完整 schema 文檔，提出需求，ZCode 可導出 OpenAPI spec。

---

## 3. 已知缺口與限制（研究側必讀）

1. **CCASS 缺口** `2025-12-25 → 2026-07-21`：已 row-level 證實。標記 `DEFERRED_DATA_GAP`，禁止插值。
2. **Workstate 限制**：當前索引只有 dailylog + bigchanges，**無 holdings/parthold/issuedshares** 完整快照；本地完整重建暫不可行（勿重跑全量抽取）。
3. **Render Free 持久化未驗證**：缺真實 PostgreSQL `DATABASE_URL`；重啟後數據存活未證明。
4. **產品定位**：5 年財技故事線 Data Layer，預設回看 5 年（年輕股由上市日起），證據驅動可延至 10 年。
5. Branch 現況：以 production branch 續接；`main`（Gate 20, 09-14）已過時。

---

## 4. 變更流程

1. 任何一方想改 §1 口徑、§2 端點行為、或自己嘅輸出合約 → 向業主提出 + 影響說明。
2. 業主批准 → 擁有方修改平台/分析 → 更新本文件（版本號 +1，記錄變更）。
3. ZCode 每次工程交付按固定格式出交接報告：【平台變更】【對 GPT 輸出影響】【未滿足研究需求】【Production Evidence】。
4. GPT 每輪交付出：【輸出合約】【對平台需求】【數據異常】【平台行為假設】【現況摘要】。

### 變更日誌
| 版本 | 日期 | 變更 | 批准 |
|---|---|---|---|
| v0.1 | 2026-09-22 | 初版：口徑 + 端點總覽 + 缺口清單 | 待業主 |

---

## 5. GPT 研究輸出合約（GPT 擁有，現為佔位）

> **待 GPT 申報**：請 GPT 按其報告格式第 1 項【輸出合約】，提供分析結果嘅完整欄位清單（名稱、格式、單位），填入此節。ZCode 收到後核對平台側可承接性，完成 v0.2。

| 欄位 | 格式/單位 | 說明 |
|---|---|---|
| （待 GPT 填寫） | | |
