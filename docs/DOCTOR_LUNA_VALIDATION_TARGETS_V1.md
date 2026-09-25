# DOCTOR_LUNA_VALIDATION_TARGETS_V1

Machine-readable: `DOCTOR_LUNA_VALIDATION_TARGETS_V1.json` (schema v1, baseline 6bb5062).
minimum_case_count 一律為 method 未指定 → 不虛構統計確定性；由 Luna 按可得案例集報告實際 n。

## LT-01 (HIGH) → CAP-02 / RF-01
- CLAIM: 除權後大股東推高市價=供錢、壓住貼供股價橫行=供乾；供乾/供錢分類可由除權後價格路徑事前判定
- CASE_CHARACTERISTICS: 已完成供股除權; 有包銷安排; 除權後至少90個交易日價格
- EVIDENCE: 除權後日收盤序列; 供股價; R報告（大股東最終認購/包銷承接量）; 包銷商身份
- T0_FIELDS: rights_issue_record(ex_ratio, offer_price, ratio, underwriter_id); daily_close(ex_date, ex_date+90d); mkt_cap
- T1_FIELDS: final_subscription_result(underwriter_takeup_share, application_count); price_path_90d; markup_vs_range
- SUPPORT: 事前分類為供乾的案例，包銷商/大股東最終承接顯著高於供錢分類案例
- CONTRADICTION: 分類為供乾但包銷商最終棄認（承接低於上限）比例偏高
- CONTEXT_DEPENDENT: 大市系統性下跌期的橫行應剔除或另計
- FALSIFICATION_TRIGGER: 分類與包銷承接結果的關聯在≥可得的完整供股案例集中不成立
- MIN_CASES: method 未指定（不虛構）

## LT-02 (HIGH) → CAP-03 / RF-02
- CLAIM: 低位+大比例大折讓+配新股+≥6名匿名承配的配股，半個月至一個月內啟動的比例顯著高於高位/小比例/配舊股組
- CASE_CHARACTERISTICS: 配股公告（一般授權或特別授權）; 可判定公告時價格位置
- EVIDENCE: 公告條款; 公告前60日價格; 承配人人數與披露狀態; 其後60交易日價格
- T0_FIELDS: placement_record(form, ratio, discount, placee_count, disclosed); price_position_t0
- T1_FIELDS: launch_within_30d; return_1m/3m; timestop_mwould_triggered
- SUPPORT: 清單ACCUMULATION組的30日啟動率顯著高於DISTRIBUTION組
- CONTRADICTION: ACCUMULATION組其後表現與DISTRIBUTION組無差異
- CONTEXT_DEPENDENT: 市況急跌期啟動延遲應另計（時間止蝕失效屬環境非規則）
- FALSIFICATION_TRIGGER: 兩組30日啟動率差異不顯著
- MIN_CASES: method 未指定（不虛構）

## LT-03 (HIGH) → CAP-03 / RF-02
- CLAIM: GO結束後20/20配股組合的三至四個月回報分佈（課堂聲稱勝率八至九成、常見3-4倍）
- CASE_CHARACTERISTICS: GO已完成; 其後12個月內有配股公告; 配股比例≈20%且折讓≈20%
- EVIDENCE: GO完成日; 配股條款; 其後120交易日價格
- T0_FIELDS: go_completion_date; placement_record(ratio≈20%, discount≈20%)
- T1_FIELDS: return_3m/4m; win_rate; max_drawdown
- SUPPORT: 實際勝率與倍數與課堂聲稱同量級（八至九成/3-4倍）
- CONTRADICTION: 勝率顯著低於八成或倍數中位顯著低於3倍
- CONTEXT_DEPENDENT: 僅GO後配股；非GO後的20/20不屬本組合
- FALSIFICATION_TRIGGER: 可得的GO+20/20案例集統計與聲稱量級明顯背離
- MIN_CASES: method 未指定（不虛構）

## LT-04 (HIGH) → CAP-05 / RF-05
- CLAIM: GO結束後一個月守住GO價+成交配合的案例，其後回報顯著優於跌穿GO價未收復組（D階段分界）
- CASE_CHARACTERISTICS: 已完成GO; GO結束後至少一年價格
- EVIDENCE: GO價; GO結束日; 其後30日價格vs GO價; 其後一年價格
- T0_FIELDS: go_record(gO_price, go_end_date)
- T1_FIELDS: hold_above_go_30d; return_1y; max_drawdown_1y
- SUPPORT: 守GO價組1年回報分佈顯著優於跌穿組
- CONTRADICTION: 兩組回報無差異或跌穿組更佳
- CONTEXT_DEPENDENT: 股災期跌穿不算規則失敗（環境項）
- FALSIFICATION_TRIGGER: 分界與1年回報無統計相關
- MIN_CASES: method 未指定（不虛構）

## LT-05 (HIGH) → CAP-07 / RF-07
- CLAIM: 市價高於GO價的要約期內，異常高的接受比例與其後CCASS貨源流向新主關聯券商一致（暗倉過倉假設，01236型）
- CASE_CHARACTERISTICS: GO要約期內市價>GO價; R報告接受比例異常; 要約期後90日CCASS快照
- EVIDENCE: R報告接受比例; 市價/GO價對照; CCASS participant變化
- T0_FIELDS: go_offer(acceptance_ratio, mkt_vs_go)
- T1_FIELDS: ccass_transfer_destination(90d); controller_stake_change
- SUPPORT: 異常接受部份與新主關聯券商持倉增加方向一致
- CONTRADICTION: 接受部份流向無關聯散戶行或場外消失
- CONTEXT_DEPENDENT: 指數剔除等機械沽壓期另計
- FALSIFICATION_TRIGGER: CCASS流向與關聯券商假設不一致的案例佔多數
- MIN_CASES: method 未指定（不虛構）

## LT-06 (HIGH) → CAP-07 / RF-07
- CLAIM: 實物存入CCASS的位置判讀：高位存入（≥5%）其後派發/回撤風險高於低位存入組
- CASE_CHARACTERISTICS: 有實物存入事件; 可判定存入時價格位置; 排除公司行動假異動
- EVIDENCE: 存入比例與日期; 存入者身份; 其後180日價格與CCASS分佈
- T0_FIELDS: ccass_in_event(ratio, date, position_class)
- T1_FIELDS: return_180d; max_drawdown_180d; ccass_dispersion_change
- SUPPORT: HIGH組回撤顯著大於LOW組
- CONTRADICTION: 兩組風險無差異
- CONTEXT_DEPENDENT: LOW存入後遇市況急跌的下行使另計
- FALSIFICATION_TRIGGER: 位置分級與其後回撤無關
- MIN_CASES: method 未指定（不虛構）

## LT-07 (HIGH) → CAP-04 / RF-03
- CLAIM: 股價接近一仙宣布合股的案例，其後派發向下路徑（再合股/供股/續跌）比例顯著高於對照仙股
- CASE_CHARACTERISTICS: 合股公告時股價≤0.05; 有其後24個月資本行動與價格
- EVIDENCE: 合股公告; 公告時股價; 其後資本行動序列; 價格路徑
- T0_FIELDS: consolidation_record(ratio, price_at_announcement)
- T1_FIELDS: subsequent_capital_actions_24m; return_24m
- SUPPORT: 貼仙合股組的向下續作率顯著高於對照
- CONTRADICTION: 貼仙合股組回升/向上的比例不低於對照
- CONTEXT_DEPENDENT: 白武士重組配套的合股另計
- FALSIFICATION_TRIGGER: 兩組向下續作率無差異
- MIN_CASES: method 未指定（不虛構）

## LT-08 (HIGH) → CAP-06 / RF-06
- CLAIM: 券商鴻溝法估算歸邊與官方『股權高度集中』通告披露值的吻合度（平台已有134k行持倉可測）
- CASE_CHARACTERISTICS: 曾發股權高度集中通告的股票; 通告前後CCASS快照
- EVIDENCE: 通告披露的持股集中數字; 同期CCASS participant分佈; 總已發行股數
- T0_FIELDS: concentration_alert(disclosed_top_holders, date)
- T1_FIELDS: gap_method_estimate(same_date); estimate_error
- SUPPORT: 鴻溝法估算與披露值誤差在規則聲明的精度內（>90%即可用級）
- CONTRADICTION: 系統性背離且方向一致（高估或低估）
- CONTEXT_DEPENDENT: 非CCASS實體股比例大的股票誤差上限放寬
- FALSIFICATION_TRIGGER: 估算與披露值背離無法由實體股解釋
- MIN_CASES: method 未指定（不虛構）

## LT-09 (HIGH) → CAP-10 / RF-10
- CLAIM: 持股停駐法定門檻微下方（29-30%區）後續出現 Non-GO 路徑（配股/CB/供股包銷入主）的比例顯著高於隨機持股群
- CASE_CHARACTERISTICS: filer持股序列顯示貼門檻停駐≥60日; 其後24個月資本行動
- EVIDENCE: DI持股序列; 其後配股/供股/CB公告; 控制權變動記錄
- T0_FIELDS: di_series(filer_id, pct, date); threshold_hug_flag
- T1_FIELDS: subsequent_control_path_24m(nongo/go/none)
- SUPPORT: 停駐組Non-GO路徑比例顯著高於對照
- CONTRADICTION: 停駐組與隨機組後續路徑無差異
- CONTEXT_DEPENDENT: 財務投資者長期持股停駐另計
- FALSIFICATION_TRIGGER: 兩組路徑分佈無統計差異
- MIN_CASES: method 未指定（不虛構）

## LT-10 (HIGH) → CAP-08 / RF-08
- CLAIM: 七大出貨信號計分（尤其升幅校準後的CCASS減持+大成交金額）與其後30/60日回撤正相關
- CASE_CHARACTERISTICS: 升幅≥3倍的財技股; 有CCASS+DI+成交序列
- EVIDENCE: 信號觸發記錄; 其後30/60日價格
- T0_FIELDS: signal_score(date, components)
- T1_FIELDS: return_30d/60d; max_drawdown_30d/60d
- SUPPORT: 計分與回撤的等級相關顯著
- CONTRADICTION: 計分與回撤無關
- CONTEXT_DEPENDENT: 大市系統性回撤期個股信號貢獻需分離
- FALSIFICATION_TRIGGER: 相關係數不顯著
- MIN_CASES: method 未指定（不虛構）

## LT-11 (HIGH) → CAP-11 / RF-13
- CLAIM: 市值階梯狀態的GO機率優勢在含除牌股的獨立樣本中重現（原研究：11.2% vs 3.6%，p≈0.0325）
- CASE_CHARACTERISTICS: 含已除牌/清盤股票的樣本; 可重建歷史市值（須帶股本品質旗標）
- EVIDENCE: 歷史市值序列; GO公告記錄; 除牌/清盤結果
- T0_FIELDS: ladder_state(date); mcap_reconstruction_flag
- T1_FIELDS: go_within_36m; delisting_outcome
- SUPPORT: 含除牌樣本中階梯組GO率仍顯著高於從未入階梯組
- CONTRADICTION: 加入除牌股後優勢消失
- CONTEXT_DEPENDENT: 2018年前老股與新上市股票分層
- FALSIFICATION_TRIGGER: 生存偏差修正後優勢不復存在
- MIN_CASES: method 未指定（不虛構）

## LT-12 (MEDIUM) → CAP-12 / RF-12
- CLAIM: 急跌股中被迫斬倉型（同系多股同日急跌/大股東未減持）其後20日反彈率顯著高於莊家主動散貨型
- CASE_CHARACTERISTICS: 單日跌幅≥50%的細價股; 可取得同系/同戶口股票當日表現
- EVIDENCE: 急跌日全板塊表現; 大股東DI; 其後20日價格; 分鐘級成交量（可得時）
- T0_FIELDS: crash_record(date, pct_drop, same_group_drop_count, controller_di_change)
- T1_FIELDS: bounce_20d; return_20d
- SUPPORT: FORCED組反彈率/幅度顯著高於DELIBERATE組
- CONTRADICTION: 兩組反彈無差異
- CONTEXT_DEPENDENT: 停牌復牌個案的價格跳空另計
- FALSIFICATION_TRIGGER: 分類與反彈無關
- MIN_CASES: method 未指定（不虛構）

## LT-13 (MEDIUM) → CAP-05 / RF-05
- CLAIM: GO後舊主保留9.x%（貼10%下）的案例，其後12個月回報分佈優於全清倉案例（舊主留一手訊號）
- CASE_CHARACTERISTICS: 控制權轉移完成; 舊主轉移後持股披露清晰
- EVIDENCE: 舊主保留比例; 其後12個月價格
- T0_FIELDS: old_owner_stake(pct_band: 9.x/4.x/0)
- T1_FIELDS: return_12m
- SUPPORT: 9.x%組回報分佈優於0%組（4.x%居中或與0%無差異）
- CONTRADICTION: 保留組與清倉組無差異
- CONTEXT_DEPENDENT: 禁售期內被迫保留不算訊號
- FALSIFICATION_TRIGGER: 分組回報無統計差異
- MIN_CASES: method 未指定（不虛構）

## LT-14 (MEDIUM) → CAP-12 / RF-12
- CLAIM: 啤殼特徵（集資額不合理+七條件）篩出的半新股，上市後1.5-2.5年窗口的啟動/上升比例顯著高於對照半新股
- CASE_CHARACTERISTICS: 2020年後上市主板/創業板股票; 有集資額與CCASS初篩數據
- EVIDENCE: 集資額/上市費用/盈利; 上市後36個月價格; CCASS集中度序列
- T0_FIELDS: ipo_record(proceeds, listing_cost, prior_profit, mcap)
- T1_FIELDS: launch_in_window(18-30m); return_36m
- SUPPORT: 篩選組窗口內啟動率顯著高於對照
- CONTRADICTION: 兩組無差異
- CONTEXT_DEPENDENT: 股災期可把異常時間加回（規則自帶）
- FALSIFICATION_TRIGGER: 篩選與啟動無關
- MIN_CASES: method 未指定（不虛構）

