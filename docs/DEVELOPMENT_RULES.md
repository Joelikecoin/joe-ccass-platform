# Development Rules

> 本文件是工程工作方式、資料安全、測試、Git、部署與回報的唯一規範。當前工作只在 [`TASK.md`](../TASK.md) 維護；產品要求見 [PROJECT_SPEC.md](PROJECT_SPEC.md)。

## 1. 工作模式

本專案採長期持續開發。預設順序：

```text
Architecture → Data → Engine → API → UI → Tests → Deployment → Public Acceptance
```

每次改動應形成小而完整的 vertical slice：真實資料可用、離線測試、文件、可部署、commit。不得因單一功能畫出 UI 或建立 placeholder endpoint 就宣稱完成，也不得一次建立大量沒有真實資料與測試的空殼。

在 scope 清楚且安全時，工程代理可自行完成現況審核、規劃、實作、migration、fixtures、tests、修正、README/CHANGELOG、commit、push、部署與驗收，不要求使用者逐檔批准。

### Architecture Guard — Discussion ≠ Decision

- 聊天、brainstorm、例子、參考截圖或未批准建議不等於Architecture／Specification decision，不得據此自行改變產品方向、phase、source或public contract。
- 只有CTO明確批准並寫入Repository Single Source of Truth的內容，才可成為後續實作依據；當前`TASK.md`的Scope、Acceptance、Out of Scope及risks是該輪唯一執行邊界。
- 實作發現、測試結果或現況差異只形成evidence／gap，不會自動改寫Specification；需要改規格時必須另行明確批准。
- 若聊天要求、task、code與正式文件衝突，停止擴大scope，保留證據並請CTO裁決；不得以「順便改善」名義refactor、rename、reformat或提前實作下一個Gap。
## 2. 必須停下取得使用者指示的情況

- 需要密碼、API key、token、真實憑證或登入批准。
- 需要未知的本機完整路徑、排程時間或外部帳戶選擇。
- 需要修改 Windows 系統或實際安裝排程。
- 可能刪除、覆蓋、遷移真實資料，且安全範圍未獲明確授權。
- 需要付費服務。
- 來源條款、robots、授權或合法性不能安全判斷。
- 必須登入、處理 CAPTCHA、繞過 access control/anti-bot/paywall。
- 需要大幅／破壞性修改公開 API schema。
- 自動部署或外部發布需要使用者本人確認。

除此之外應用合理假設持續完成，不把一般工程判斷轉嫁給使用者。

## 3. 每個任務的標準流程

1. 讀 [`TASK.md`](../TASK.md) 及相關正式文件，確認 scope/acceptance。
2. 檢查 `AGENTS.md`（如有）、branch、status、remote、最新 baseline；保留不相關使用者變更。
3. 審核現有 code/tests/config/history，不重做已完成工作。
4. 更新 `TASK.md`：active task、acceptance、依賴、風險。
5. 先補失敗／回歸測試或明確 fixtures，再實作最小完整 slice。
6. 執行 formatter/lint/unit/integration/smoke/secrets checks（按風險）。
7. 核對 diff、schema、docs、migration、secrets、generated files。
8. 只 stage 任務相關檔案；使用意圖清楚的 commit message。
9. Push 指定 branch；部署屬 scope 時等待並公開驗收。
10. 更新 `TASK.md` status/evidence/commit，保持工作樹乾淨並按標準格式回報。

## 4. 資料與程式規則

- Fail loud, never fake；不回空 array 掩蓋 source/parser failure。
- Fetch 與 parse 分離；parser 不發 network request。
- 所有 source URL/status/timeout/retry/rate/cache/parser policy 進 registry/config。
- 五位 stock code、香港 business date、穩定 participant ID、明確 denominator。
- 原始 holding 不任意改寫；不插值 holdings；partial 不補 0。
- Schema 改動要 migration/compatibility/changelog/tests；欄位 rename 視為 breaking change。
- Migration transactional、idempotent、有 upgrade tests，不靜默刪資料。
- CSV 用標準 parser；寫檔 temporary + atomic replace；中文 Excel 輸出按需要用 UTF-8-SIG。
- 同一天 collector 重跑不 duplicate；batch 中一股 failure 不拖垮全部。
- source adapter failure 必須可隔離；非核心補充 source 不應令核心報告失敗。
- 計算 threshold、tolerance、freshness、Top N 等全進 config 並可追溯版本。

## 5. Security、privacy 與 logging

- Secrets 只放 env/secret store；`.env.example` 只用明顯 placeholder。
- 不 commit `.env`、token、cookie、private key、私人檔案路徑或 production data dump。
- Log/error/report 不記完整 API key、Google Drive URL、query parameters、authorization headers、cookies；只記 safe source ID／hostname/status/error type。
- 測試使用假 token，並 assert 假 token 不出現在 log。
- 不透過 browser profile、cookie store 或私人 API 取得資料。
- 外部 fetch 有 timeout、size limit、content-type/login-page/challenge guard、bounded retry、rate limit。
- 每次提交前執行 secrets scan（專案已有工具則使用；否則以 repository grep + diff review 作最低要求）。

## 6. Test strategy

### 6.1 分層

- **Unit**：normalizers、domain invariants、engines、i18n、exports。
- **Parser fixtures**：saved HTML/JSON/CSV/PDF metadata，完全離線。
- **Network adapter**：`respx`/mock，驗 timeout/status/content/size/redaction/cache/fallback。
- **Storage/migration**：temporary DB/files，transactions/idempotency/resume/atomicity。
- **API/MCP/UI smoke**：共用 service、schema、error mapping、基本 render。
- **Live/golden acceptance**：獨立、低頻、非預設 unit suite；記錄來源與日期。

Live source 不能成為 parser unit tests 的必要條件。

### 6.2 必須覆蓋的功能矩陣

1. 股票代號 normalize。
2. issue ID resolution。
3. 錯誤 issue ID 不可靜默返回另一股票。
4. Holdings parser。
5. Changes parser。
6. Big Changes parser。
7. Concentration parser。
8. Price parser。
9. HKEX announcements parser。
10. 單日 snapshot。
11. 多日 snapshot。
12. participant added/removed。
13. missing participant 在完整 snapshot 補 0。
14. partial snapshot 不可錯補 0。
15. fixed participant colour。
16. Top N rainbow。
17. Others aggregation。
18. >100% warning。
19. T+2 metadata。
20. duplicate collector run。
21. backfill resume。
22. malformed HTML/content。
23. source timeout。
24. source changed。
25. stale cache/last-known-good。
26. partial response。
27. CSV exports/imports。
28. Excel exports/imports。
29. JSON exports。
30. Markdown report。
31. Copy for ChatGPT。
32. API schema/auth/errors。
33. MCP tools 共用 service。
34. Streamlit smoke + i18n state。
35. secrets/redaction scan。

來源 adapter 另需測 403/429/5xx/challenge、content type、oversize、login HTML、schema drift、cache hit、fallback、last-known-good 不被壞下載覆蓋。

## 7. Golden stock 與驗收

Golden stock 優先 `01592`。先讓它完成 fetch → parse → normalize → store → API/UI/export 的 end-to-end，再擴第二隻股票或下一 phase。

與 Webb-site 原頁及 HKEX SDW 抽樣核對時記錄：

- stock code、issue ID、data date；
- participant ID/name、holding、percentage、percentage basis；
- source URL/identifier、fetch time、warnings；
- 差異與可解釋原因。

不得只驗證頁面／endpoint 能開。公開驗收還要檢查真實資料、mobile layout、language toggle、copy/download、errors/cache/source status。

## 8. Quality gates

每個 commit 最低要求：

- `python -m ruff check .` 通過。
- `python -m pytest` 通過。
- `git diff --check` 通過。
- 相關 offline fixtures/tests 新增或更新。
- 無 secrets、真實 key、私人路徑、無意 generated files。
- 公開 schema/migration/docs 與 code 同步。

如專案已有 type checker、coverage、Streamlit/FastAPI/MCP smoke 或 deployment check，必須一併通過。Live tests 若因來源不可用而未執行，需明確回報，不可混稱全部驗收通過。

## 9. Git 與檔案安全

- 預設在使用者指定 branch；長期開發依使用者要求可直接 push `main`。
- 未經要求不使用 `git reset --hard`、`git checkout --` 或破壞性清理。
- dirty worktree 中的既有／新變更視為使用者所有；只 stage 任務檔案。
- 不 amend/rebase 已發布歷史，除非明確授權。
- Commit message 描述 outcome，例如 `docs: establish project specification`。
- Push 前再次確認 HEAD、branch、staged diff 和 test evidence。
- Repository 文件用相對 links；README 指向 docs/TASK，不複製完整規格。

## 10. 文件治理

- [PROJECT_SPEC.md](PROJECT_SPEC.md)：產品行為、scope、UI、API/MCP contract、完成定義。
- [DATA_SOURCE_GUIDE.md](DATA_SOURCE_GUIDE.md)：來源、欄位、優先序、fetch/cache/conflict。
- [ARCHITECTURE.md](ARCHITECTURE.md)：技術邊界、DB、flows、engines、deployment。
- 本文件：工程、安全、測試、Git、回報。
- [ROADMAP.md](ROADMAP.md)：phase、順序、exit gates。
- [`TASK.md`](../TASK.md)：唯一 current work/status/evidence 清單。

避免重複：規格變更只修改擁有該責任的主文件；其他位置更新 link/summary。若 code 與 docs 不符，先在 `TASK.md` 記錄 gap，再以測試和 migration 修正，不靜默改寫規格迎合現況。

外部 Master Prompt 從本版起 retired；若收到新需求，直接更新這組文件和 `TASK.md`，不建立第二份大型 prompt。

## 11. Deployment 與 Windows 排程

- 未有使用者登入批准，不自行建立 production deployment 或修改 secrets。
- 可準備 deployment config/docs，但不得假稱 adapter/MCP/公開站已部署。
- Push 後若平台自動 deploy，任務 scope 包含公開驗收時要等待完成並測試。
- Windows scheduler scripts 可準備但不安裝；安裝／移除需明確 target path、schedule、log location 和使用者批准。
- Uptime monitor 只監察公開 `/health`；keep-alive 須符合供應商規則。

## 12. Phase 回報格式

完成一個 phase 時簡潔回報：

1. Phase 名稱。
2. 已完成內容。
3. 尚未完成內容。
4. Commit hash。
5. Tests/lint/smoke 結果。
6. 主要新增／修改檔案。
7. Active data sources。
8. Disabled/unverified sources 及原因。
9. Golden stock 核對結果。
10. 公開 Streamlit 驗收結果。
11. 唯一需要使用者手動處理的下一步。

若沒有人工下一步，明確寫「無」。
