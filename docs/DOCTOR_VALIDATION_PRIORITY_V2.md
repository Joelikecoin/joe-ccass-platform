# DOCTOR_VALIDATION_PRIORITY_V2

Baseline f03d93a。排序準則：1 證據可得性 2 PIT 可行 3 來源獨立 4 實作成本 5 驗證價值。不按方法論重要性排序。

## 排名

1. **LT-09**（CAP-10/RF-10） likelihood=HIGH cost=LOW risk=LOW
   - blocker: 無結構性 blocker；單股樣本（n=1 個案）只支持 case-package 級驗證，非統計級
2. **LT-07**（CAP-04/RF-03） likelihood=MEDIUM cost=LOW risk=MEDIUM
   - blocker: 貼仙合股在 watchlist 範圍內的事件數未知；通告覆蓋決定樣本
3. **LT-04**（CAP-05/RF-05） likelihood=HIGH cost=MEDIUM risk=MEDIUM
   - blocker: GO 價/起止日為通告文本抽取（無現成結構欄位）——一次性 parser 工作量
4. **LT-02**（CAP-03/RF-02） likelihood=HIGH cost=MEDIUM risk=MEDIUM
   - blocker: placee_count/disclosed 欄位需文本抽取；watchlist 樣本量受 6,109 通告覆蓋限制
5. **LT-01**（CAP-02/RF-01） likelihood=MEDIUM cost=MEDIUM risk=MEDIUM
   - blocker: R報告結構化抽取是主要成本；除權日須從通告對齊
6. **LT-06**（CAP-07/RF-07） likelihood=LOW cost=MEDIUM risk=HIGH
   - blocker: 非CCASS→CCASS 轉換事件在現有 2 個月窗口內太稀疏；需要 19 年歷史庫（Codex gated）或累積 12+ 個月
7. **LT-03**（CAP-03/RF-02） likelihood=MEDIUM cost=MEDIUM risk=HIGH
   - blocker: GO+20/20 組合本身罕見——watchlist 範圍內案例數可能不足以支持任何結論（方法亦無指定最低 n）
8. **LT-12**（CAP-12/RF-12） likelihood=MEDIUM cost=MEDIUM risk=HIGH
   - blocker: 被迫斬倉 vs 主動散貨的分類依賴同系映射+DI，兩者覆蓋薄；急跌事件本身可全掃
9. **LT-13**（CAP-05/RF-05） likelihood=LOW cost=MEDIUM risk=HIGH
   - blocker: 需要歷史 GO 案例全集的易手+舊主持股——DI 歷史覆蓋是主要缺口
10. **LT-10**（CAP-08/RF-08） likelihood=LOW cost=HIGH risk=HIGH
   - blocker: media exposure 無結構來源；合約要求 7 組件齊備——不弱化語義則須人工輸入通道
11. **LT-05**（CAP-07/RF-07） likelihood=LOW cost=HIGH risk=HIGH
   - blocker: 同時需要 R報告抽取+關聯券商映射+CCASS 歷史——三項缺口疊加
12. **LT-14**（CAP-12/RF-12） likelihood=LOW cost=HIGH risk=HIGH
   - blocker: 無招股書/上市費用結構化來源；CCASS 自上市日起的序列不存在（歷史庫 gated）
13. **LT-08**（CAP-06/RF-06） likelihood=LOW cost=MEDIUM risk=HIGH
   - blocker: FAILURE_CLASS=A(缺來源攝取：證監會集中通告未入庫) + B(證據本質稀有：alert 事件本身低頻且日期回溯需歷史 CCASS)。非 C(合約過度具體——語義不改) 非 D(非暫時性 data gap——官方通告來源結構性缺席)
14. **LT-11**（CAP-11/RF-13） likelihood=LOW cost=HIGH risk=HIGH
   - blocker: BLOCKED_BY_CODEX_GATE：重跑需 19 年歷史庫（staging 87.5M 行未過 final parent gate）+ 除牌全集；ZC 不得繞過 gate

## 明細

### LT-09 → CAP-10 / RF-10
- T0: DION_DI_SERIES; THRESHOLD_HUG_FLAG
- T1: ANNOUNCEMENTS_CAPITAL_ACTIONS_24M; CONTROL_PATH_OUTCOME; SHARE_CAPITAL
- AVAILABLE: DION_DI_SERIES(02318 全史 696 events); ANNOUNCEMENTS(02318); SHARE_CAPITAL; PRICE_DAILY
- PARTIAL: —
- MISSING: —
- official=True date_align=False price=False ccass=False di=True share_cap=True
- source_indep=YES pit=YES cost=LOW risk=LOW likelihood=HIGH
- BLOCKER: 無結構性 blocker；單股樣本（n=1 個案）只支持 case-package 級驗證，非統計級

### LT-04 → CAP-05 / RF-05
- T0: GO_RECORD(go_price,end_date); ANNOUNCEMENTS
- T1: PRICE_1Y; HOLD_ABOVE_GO_30D
- AVAILABLE: ANNOUNCEMENTS(watchlist GO/易手通告); PRICE_DAILY
- PARTIAL: GO_PRICE/END_DATE 欄位需從通告文本抽取
- MISSING: —
- official=True date_align=True price=True ccass=False di=False share_cap=False
- source_indep=PARTIAL pit=YES cost=MEDIUM risk=MEDIUM likelihood=HIGH
- BLOCKER: GO 價/起止日為通告文本抽取（無現成結構欄位）——一次性 parser 工作量

### LT-02 → CAP-03 / RF-02
- T0: PLACEMENT_RECORD; PRICE_POSITION_T0
- T1: LAUNCH_30D; RETURN_1M_3M
- AVAILABLE: ANNOUNCEMENTS(配股公告); PRICE_DAILY
- PARTIAL: 承配人人數/披露狀態（通告文本抽取）
- MISSING: —
- official=True date_align=True price=True ccass=False di=False share_cap=False
- source_indep=PARTIAL pit=YES cost=MEDIUM risk=MEDIUM likelihood=HIGH
- BLOCKER: placee_count/disclosed 欄位需文本抽取；watchlist 樣本量受 6,109 通告覆蓋限制

### LT-01 → CAP-02 / RF-01
- T0: RIGHTS_ISSUE_RECORD; DAILY_CLOSE_90D
- T1: R_REPORT_TAKEUP; UNDERWRITER_ID
- AVAILABLE: ANNOUNCEMENTS(供股+結果通告); PRICE_DAILY; SHARE_CAPITAL
- PARTIAL: R報告承給/申請份數（文本抽取）; 包銷商身份（文本抽取）
- MISSING: —
- official=True date_align=True price=True ccass=False di=False share_cap=True
- source_indep=PARTIAL pit=YES cost=MEDIUM risk=MEDIUM likelihood=MEDIUM
- BLOCKER: R報告結構化抽取是主要成本；除權日須從通告對齊

### LT-03 → CAP-03 / RF-02
- T0: GO_COMPLETION; PLACEMENT_20_20
- T1: RETURN_3M_4M; WIN_RATE
- AVAILABLE: ANNOUNCEMENTS; PRICE_DAILY
- PARTIAL: GO完成狀態; 20/20 條款抽取
- MISSING: —
- official=True date_align=True price=True ccass=False di=False share_cap=False
- source_indep=PARTIAL pit=YES cost=MEDIUM risk=HIGH likelihood=MEDIUM
- BLOCKER: GO+20/20 組合本身罕見——watchlist 範圍內案例數可能不足以支持任何結論（方法亦無指定最低 n）

### LT-07 → CAP-04 / RF-03
- T0: CONSOLIDATION_RECORD(price≤0.05); PRICE
- T1: CAPITAL_ACTIONS_24M; RETURN_24M
- AVAILABLE: ANNOUNCEMENTS; PRICE_DAILY; SHARE_CAPITAL
- PARTIAL: —
- MISSING: —
- official=True date_align=False price=True ccass=False di=False share_cap=True
- source_indep=YES pit=YES cost=LOW risk=MEDIUM likelihood=MEDIUM
- BLOCKER: 貼仙合股在 watchlist 範圍內的事件數未知；通告覆蓋決定樣本

### LT-06 → CAP-07 / RF-07
- T0: CCASS_IN_EVENT(ratio,position); NON_CCASS_TRANSITIONS
- T1: RETURN_180D; CCASS_DISPERSION_180D
- AVAILABLE: CCASS_DAILY_HOLDINGS(watchlist, 2026-07-21→); SHARE_CAPITAL; PRICE_DAILY
- PARTIAL: 存入者身份（需 DI 交叉）
- MISSING: 更長歷史窗口（實物存入為低頻事件，2 個月窗口事件數不足）
- official=False date_align=True price=True ccass=True di=False share_cap=True
- source_indep=YES pit=YES cost=MEDIUM risk=HIGH likelihood=LOW
- BLOCKER: 非CCASS→CCASS 轉換事件在現有 2 個月窗口內太稀疏；需要 19 年歷史庫（Codex gated）或累積 12+ 個月

### LT-05 → CAP-07 / RF-07
- T0: GO_OFFER(acceptance_ratio,mkt_vs_go)
- T1: CCASS_DESTINATION_90D; CONTROLLER_STAKE_CHANGE
- AVAILABLE: ANNOUNCEMENTS; PRICE_DAILY
- PARTIAL: R報告接受比例（文本抽取）
- MISSING: 要約期後 90 日 CCASS（限 watchlist+窗口）; 新主關聯券商映射（ENTITIES 僅 9 行）
- official=True date_align=True price=True ccass=True di=True share_cap=False
- source_indep=PARTIAL pit=YES cost=HIGH risk=HIGH likelihood=LOW
- BLOCKER: 同時需要 R報告抽取+關聯券商映射+CCASS 歷史——三項缺口疊加

### LT-10 → CAP-08 / RF-08
- T0: SIGNAL_SCORE(7 components)
- T1: RETURN_30D_60D; DRAWDOWN
- AVAILABLE: ANNOUNCEMENTS; DI(watchlist); CCASS(watchlist); PRICE_DAILY+分鐘(當日)
- PARTIAL: CCASS 出貨程度（窗口短）; 歷史分鐘圖（僅當日）
- MISSING: MEDIA_EXPOSURE（無來源，需人工）
- official=False date_align=True price=True ccass=True di=True share_cap=False
- source_indep=PARTIAL pit=YES cost=HIGH risk=HIGH likelihood=LOW
- BLOCKER: media exposure 無結構來源；合約要求 7 組件齊備——不弱化語義則須人工輸入通道

### LT-12 → CAP-12 / RF-12
- T0: CRASH_RECORD; SAME_GROUP_MAP; CONTROLLER_DI
- T1: BOUNCE_20D
- AVAILABLE: PRICE_DAILY(可掃急跌); DION_DI(watchlist)
- PARTIAL: 同系/同戶口映射（ENTITIES 僅 9 行）; 非 watchlist 大股東 DI
- MISSING: BROAD_UNIVERSE_GROUP_MAP
- official=False date_align=True price=True ccass=False di=True share_cap=False
- source_indep=PARTIAL pit=YES cost=MEDIUM risk=HIGH likelihood=MEDIUM
- BLOCKER: 被迫斬倉 vs 主動散貨的分類依賴同系映射+DI，兩者覆蓋薄；急跌事件本身可全掃

### LT-13 → CAP-05 / RF-05
- T0: OLD_OWNER_STAKE_BAND
- T1: RETURN_12M
- AVAILABLE: ANNOUNCEMENTS(易手); PRICE_DAILY
- PARTIAL: 舊主轉移後持股（DI 僅 watchlist；DION 可按股開 job）
- MISSING: BROAD_HISTORICAL_DI
- official=True date_align=False price=True ccass=False di=True share_cap=False
- source_indep=PARTIAL pit=YES cost=MEDIUM risk=HIGH likelihood=LOW
- BLOCKER: 需要歷史 GO 案例全集的易手+舊主持股——DI 歷史覆蓋是主要缺口

### LT-14 → CAP-12 / RF-12
- T0: IPO_RECORD(proceeds,cost,profit,mcap)
- T1: LAUNCH_18_30M; RETURN_36M; CCASS_FROM_LISTING
- AVAILABLE: PRICE_DAILY
- PARTIAL: 招股結果（公告內文本）
- MISSING: IPO/PROSPECTUS_UNIVERSE; CCASS_FROM_LISTING_DATE
- official=True date_align=True price=True ccass=True di=False share_cap=True
- source_indep=PARTIAL pit=YES cost=HIGH risk=HIGH likelihood=LOW
- BLOCKER: 無招股書/上市費用結構化來源；CCASS 自上市日起的序列不存在（歷史庫 gated）

### LT-11 → CAP-11 / RF-13
- T0: LADDER_STATE; BROAD_HISTORICAL_MCAP; MCAP_RECONSTRUCTION_FLAG
- T1: GO_WITHIN_36M; DELISTING_OUTCOME
- AVAILABLE: GO 公告（部分）
- PARTIAL: SHARE_CAPITAL(watchlist)
- MISSING: BROAD_HISTORICAL_MCAP; DELISTED_UNIVERSE; HISTORICAL_CCASS_19Y(gated)
- official=True date_align=False price=True ccass=True di=False share_cap=True
- source_indep=NO pit=PARTIAL cost=HIGH risk=HIGH likelihood=LOW
- BLOCKER: BLOCKED_BY_CODEX_GATE：重跑需 19 年歷史庫（staging 87.5M 行未過 final parent gate）+ 除牌全集；ZC 不得繞過 gate

### LT-08 → CAP-06 / RF-06
- T0: SFC_CONCENTRATION_ALERT; CCASS_SNAPSHOT_SAME_DATE
- T1: GAP_METHOD_ESTIMATE; ESTIMATE_ERROR
- AVAILABLE: CCASS_DAILY_HOLDINGS(watchlist only)
- PARTIAL: 鴻溝法估算器（可實作）
- MISSING: SFC_CONCENTRATION_ALERTS（官方公開但未攝取）; ALERT_DATE_CCASS_HISTORY（alert 股票多在 watchlist 外；歷史快照 gated）
- official=True date_align=True price=False ccass=True di=False share_cap=True
- source_indep=PARTIAL pit=PARTIAL cost=MEDIUM risk=HIGH likelihood=LOW
- BLOCKER: FAILURE_CLASS=A(缺來源攝取：證監會集中通告未入庫) + B(證據本質稀有：alert 事件本身低頻且日期回溯需歷史 CCASS)。非 C(合約過度具體——語義不改) 非 D(非暫時性 data gap——官方通告來源結構性缺席)

