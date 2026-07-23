# Task Board

> 本檔是唯一的當前工作、狀態、驗收證據與下一步清單。長期產品要求見 [`docs/PROJECT_SPEC.md`](docs/PROJECT_SPEC.md)，phase順序與完整Gap Analysis見 [`docs/ROADMAP.md`](docs/ROADMAP.md)。

## Working baseline

- Branch：`main`
- Original requested code baseline：`fad4411`
- Latest approved implementation：`f9fcf02`、`6152135`（P1-03；CTO approved）
- Specification baseline reviewed：`67e35e5`
- Functional audit：2026-07-23，見 [`docs/ROADMAP.md`](docs/ROADMAP.md#repository-功能審核)
- Current phase：Phase 1 — Data foundation and objective CCASS sections
- Golden stock：`01592`
- Status updated：2026-07-23 (Asia/Hong_Kong)

## Status rules

- `[ ]` pending
- `[-]` in progress
- `[x]` complete，有tests／commit／acceptance evidence
- `[!]` blocked，必須寫明阻塞原因與所需使用者動作

同一時間只保留一個最高優先主要任務。完成任務時記錄tests、commit、source/acceptance evidence；不要在README或其他文件建立第二份task list。

## Completed foundation

- [x] `P0-01`–`P0-06`：建立並核對Single Source of Truth、匯入有效指南／截圖規格、retire外部Master Prompt，納入Google CSV、collector/UI及URL redaction基線。
- [x] `P1-01`：source-neutral normalized historical snapshot foundation、transactional migrations、raw provenance、idempotent repository及legacy compatibility；commit `ec09374`。
- [x] `P1-02`：source-neutral collector routing、dry-run、complete/partial honesty、batch/per-stock run/error accounting及安全atomic CSV；commit `d8a480e`，CTO approved。
- [x] `P1-03`：source-neutral exact-date backfill、range/latest/resume、persistent per-date accounting、existing skip、failed-date retry、bounded retry、partial honesty及dry-run完整validation零寫入；commits `f9fcf02`、`6152135`，CTO approved。

## Audit summary

- Done：5個功能單位。
- Partial：19個功能單位。
- Not Started：9個功能單位。
- 總計：33個功能單位；28個Remaining Gaps已按phase gate與依賴在 [`docs/ROADMAP.md`](docs/ROADMAP.md#remaining-gaps-優先序)重新排序。
- Phase 1維持In Progress：collector idempotency與backfill resume/retry gate已滿足；合法真實多日source/golden證據及Holdings／Changes／Big Changes／Concentration完整vertical slices仍未滿足。
- 排序結論：下一個唯一最高優先工作是P1-04；本輪只完成Gap Analysis與文件更新，不開始實作。

## 唯一最高優先工作

### [ ] P1-04 — Configuration-driven source registry and capability/audit metadata

優先理由：P1-01至P1-03已建立normalized persistence、collector及backfill，但source ID/status/capability/date coverage、limits、cache/fallback及audit metadata仍分散在settings、services及adapters。Phase 1必須先有誠實、可配置的registry，才可安全拆分Webb-site adapter、統一routing/cache、評估合法歷史能力及完成真實vertical slice；Phase 4公開source diagnostics不是本任務範圍。

目標：為Repository現有且已核准的source/import flows建立單一configuration-driven registry與內部capability/audit read model，讓latest holdings、exact-date import、collector及backfill依同一份誠實metadata選擇／拒絕source，同時保持現有公開FastAPI、MCP、Streamlit與`DATA_SOURCE` contract不變。

本工作範圍：

- 集中source ID、display name、configured status/enabled、priority、supported sections、latest/requested-date coverage、fallback eligibility及known limitations；
- 集中timeout、size、bounded retry、rate/minimum sleep、cache/LKG policy、parser/schema version、safe attribution及terms/robots audit metadata；
- 只登記現有`webbsite`與`google_drive_csv`／import flow，準確標示Webb-site latest-only及CSV verified exact-date能力；
- 讓`CcassService`、collector與backfill的source selection/capability checks使用registry，同時保留`auto|webbsite|google_drive_csv`兼容行為；
- 提供不發network probe的內部safe diagnostics/read model及完整離線tests。

Acceptance：

- [ ] Registry由集中domain/config model建立；同一source的identity、status、capabilities、limits、cache/fallback及audit metadata不再在service/collector/backfill重複定義。
- [ ] `webbsite`只宣稱目前已驗證的latest Holdings能力；不得宣稱requested-date history、Changes、Concentration或Price已可用。
- [ ] `google_drive_csv`只在配置有效URL時提供已驗證CSV latest/exact-date import能力；source status、imported/cached限制及known limitations誠實可查。
- [ ] `auto|webbsite|google_drive_csv`現有env/public config兼容；auto holdings仍按既有mirror→configured CSV fallback，CSV-only仍不構造Webb-site client。
- [ ] Collector及Backfill由registry capability判斷可用source；latest-only source用於requested date時fail loud `DATE_UNAVAILABLE`／兼容structured error，不fallback到latest。
- [ ] Timeout、size、retry、rate/minimum sleep及cache policy由settings/registry可配置並有validation；不得引入無限retry或高頻diagnostic probe。
- [ ] Internal diagnostics只輸出safe source ID/status/capabilities/parser/schema/audit/disabled reason；不含完整URL/query、API key、Cookie、authorization或私人路徑。
- [ ] Unknown、disabled、unconfigured或capability不符的source有deterministic structured failure；一個disabled/unavailable source不拖垮不相關source。
- [ ] Offline tests覆蓋registry validation、accurate capability matrix、routing compatibility、CSV isolation、collector/backfill selection、disabled/unconfigured及redaction；現有regression全部通過。
- [ ] 不修改公開FastAPI/MCP/Streamlit response schema或新增endpoint/UI；Ruff、完整Pytest、`git diff --check`及secrets/private-path scan通過後才可commit/push `main`。

明確不在本工作：

- 不新增、啟用或audit HKEX SDW、HKEXnews、DI/SDI、price或其他supplemental adapter。
- 不實作`/api/v1/sources/status`、Streamlit diagnostics、source metrics dashboard或高頻health probe。
- 不拆完Webb-site fetch/parser、不新增historical endpoint，不實作persistent LKG/conflict resolver。
- 不實作Holdings/Changes/Big Changes/Concentration/Rainbow/Price/Announcements/i18n/exports的新功能。
- 不修改公開schema、不做destructive migration、不執行live scraping、scheduler安裝或deployment acceptance。

Dependencies/risks：

- 依賴已批准P1-01 `ec09374`、P1-02 `d8a480e`及P1-03 `f9fcf02`／`6152135`；現有source routing及backfill exact-date語義必須保持兼容。
- Registry metadata不得把「已寫adapter」「configured」「可合法active」「有live/golden證據」混為一談；未驗證能力必須disabled/unavailable。
- 如需要新的來源條款判斷、憑證、付費服務、公開schema變更或破壞性migration，依 [`docs/DEVELOPMENT_RULES.md`](docs/DEVELOPMENT_RULES.md)立即停止請示。
- 未獲CTO批准前不得開始實作P1-04；完成後亦不得自行開始下一個Gap。

## Decisions and constraints

- 平台只輸出客觀資料；不做投資評分、買賣建議、莊家／收貨／派貨結論。
- DisclosureTracker只作UI/功能參考，不是資料依賴。
- 參考Streamlit網站的程式、API、Cookie、憑證及非公開資料不使用。
- Cache/last-known-good必須標cached/stale/data date，不冒充live。
- Webb-site目前只驗證latest Holdings；Google Drive/CSV是已核准的安全import flow及P1-03 exact-date來源能力，不等於已有production history/golden驗收。
- Windows schedule、production credentials、付費服務、source legality ambiguity必須停下請示。

## Approved task evidence

```text
Task: P1-01 — Source-neutral normalized historical snapshot foundation
Status: complete; CTO approved
Commit: ec09374
Tests: Ruff passed; Pytest 64 passed; git diff --check and repository secrets/private-path scan passed.
```

```text
Task: P1-02 — Source-neutral collector orchestration and persistent run accounting
Status: complete; CTO approved
Commit: d8a480e
Tests: Ruff passed; Pytest 78 passed; git diff --check and repository secrets/private-path scan passed.
```

```text
Task: P1-03 — Resumable source-neutral CCASS historical backfill
Status: complete; CTO approved
Commits: f9fcf02, 6152135
Tests: Ruff passed; full Pytest 88 passed; CLI smoke, git diff --check, credential-pattern scan and private-path scan passed.
Active sources: Only approved Google Drive/CSV import flow provides exact requested-date history; Webb-site remains latest-only.
Golden validation: Synthetic offline 01592 fixtures only; no live scraping or production-data claim.
Public acceptance: Existing FastAPI/MCP/Streamlit contracts were unchanged and passed regression tests.
Remaining manual step: none; P1-03 is formally approved.
```

完成active task時附加：

```text
Task:
Status: complete | blocked
Commit:
Tests:
Files:
Active sources:
Disabled/unverified sources:
Golden validation:
Public acceptance:
Remaining manual step:
```