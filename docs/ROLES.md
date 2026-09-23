# ROLES.md — Joe CCASS Platform 分工憲章 v1.0

> **狀態:** 正式採納（Joe 批准，2026-09-22）
> **權威:** 分工爭議以本文件為準。接口數據合約見 `docs/interface.md`。

## 1. 角色

### GPT = Architect + Research Lead + QA
**負責：**
- 股票／財技研究、教材與案例研究
- Data requirements、Research Bundle 定義
- API / Schema / Data Contract 設計（Target Research Contract 起草）
- Database schema 建議
- Architecture review
- Acceptance criteria、Test case / edge case 設計
- Production evidence review
- Bug diagnosis / root-cause 假設（基於 ZCode 提供之 evidence）
- Code / PR review
- Parser / ETL 規格設計

**不負責：** 直接修改 production code、DB migration 執行、Render/deployment 操作、secrets/credentials、直接改 frontend/backend、修改研究側以外任何一方定義。

### ZCode = Implementation Engineer
**負責：**
- 實際寫 code：frontend / backend implementation
- Database migration 執行
- API implementation
- Source adapters / ETL / backfill
- Render / deployment
- Production fixes
- 真實環境測試與 Production Evidence
- Current Platform Facts 核實（見 §3）

**不負責：** GPT 嘅研究邏輯、分析框架、判斷規則、輸出定義。

### Joe = 業主 / 唯一整合者
- 審批規格與跨區請求、決定優先級、裁決 GAP/CONFLICT。

## 2. 協作流程

```
GPT 規格 + acceptance criteria → Joe 審批 → ZCode 實作 →
ZCode 交 Production Evidence → GPT QA 驗收 → 下一輪規格
```

## 3. interface.md 權責劃分

- **Current Platform Facts / Production Reality**：由 ZCode 核實及擁有最終事實認定權（「平台目前實際做到乜」）。
- **Target Research Contract / Research Requirements**：由 GPT 起草，包括研究所需欄位、schema、數據口徑及 acceptance criteria（「研究最終需要乜」）。
- 兩者有差異時，必須明確標記為 `GAP / CONFLICT`，**任何一方不得自行修改另一方定義**；由 Joe 決定是否開工程任務（「邊個 gap 值得做」）。

## 4. 補充規則

- **R1 緊急通道**：production 事故時 ZCode 可先修後報，24 小時內補交事故報告畀 Joe 同 GPT。
- **R2 小改快速通道**：不觸及 schema/API/數據口徑嘅小修（錯字、註釋、內部重構、補測試），Joe 一句話批准即做，免全流程。
- **R3 文件分類**：工程現況類文件（進度、部署狀態、evidence）由 ZCode 維護；規格合約類文件由 GPT 起草、ZCode 核對現實、Joe 批准。規格必須連 acceptance criteria 完整交付，不得半成品。

## 5. 設計前置義務（GPT）

設計任何 API/Schema/Contract 前，必須先讀 `PROJECT_PROGRESS_V3.md` 與 `docs/interface.md`；設計不得與已證實現實衝突（例：CCASS 缺口 `2025-12-25 → 2026-07-21`、Render 免費層限制）。ZCode 收到規格後有可行性回饋義務：規格與現實衝突時打回，不得靜默改規格。

## 6. 交接報告格式

- **ZCode →**：【平台變更改動】【對 GPT 輸出影響】【未滿足研究需求】【Production Evidence】【待確認 GAP/CONFLICT 清單】
- **GPT →**：【輸出合約】【對平台需求】【數據異常】【平台行為假設】【現況摘要】

## 變更日誌
| 版本 | 日期 | 變更 | 批准 |
|---|---|---|---|
| v1.0 | 2026-09-22 | 初版：角色、流程、權責、R1–R3 | Joe |
