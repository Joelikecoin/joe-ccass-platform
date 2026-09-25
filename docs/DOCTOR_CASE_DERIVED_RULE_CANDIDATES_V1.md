# DOCTOR_CASE_DERIVED_RULE_CANDIDATES_V1

Machine-readable source of truth: dev store `app/data/doctor/doctor_ingestion.sqlite`
(table `rule_candidates`, full payload in `payload_json`). This doc is the human index.

All candidates are method_status=CASE_DERIVED — none promoted. Every candidate carries
origin_source_ids + origin_observation_ids + falsification_conditions (schema-enforced).

## CAND-CHAUHIN-BADNEWS-DECAY-001 — 壞消息失效=流動性支撐線索
- methodology: CHAU_HIN | family: EVENT_SEQUENCE | generalization: REPEATABLE_METHOD | dedup: NEW_RULE
- description: 連續壞消息的價格殺傷力遞減、好消息反應放大→推斷流動性/貨幣支撐；大勢判斷以價格反應為準而非消息數量。此為大市層訊號，不直接適用個股。
- required_inputs: 壞消息序列及其後價格反應; 好消息反應幅度
- trigger: 連續壞消息而市場不再新低
- falsification: 壞消息失效期後的市場表現與流動性指標無關
- lineage: observations=['OBS-Z1-001'] sources=['CHAUHIN-COURSE-L1'] cases=[]

## CAND-CHAUHIN-PRIME-RATIO-001 — 雙質數供股比例=碎股減流通的中長期偏多因素
- methodology: CHAU_HIN | family: RIGHTS_ISSUE | generalization: REPEATABLE_METHOD | dedup: RULE_VARIANT
- description: 質數類供股比例製造碎股→碎股難即時沽出→減少即時沽壓與貨源流出；屬中長期財技偏好因素，須與短期供股風險（公布後先處理持倉）分開判斷；一宗交易多動機並存，碎股只是其中一個可能動機。
- required_inputs: 供股比例（是否質數/非整除）; 每手股數
- trigger: 供股比例與常見持股量非整除
- falsification: 質數比例與整除比例供股的其後沽壓/回報無統計差異
- lineage: observations=['OBS-Z2-001'] sources=['CHAUHIN-COURSE-L2A'] cases=[]

## CAND-CHAUHIN-THRESHOLD-ASK-001 — 門檻精確數字追問法（29.99%型）
- methodology: CHAU_HIN | family: CONTROL_CHANGE | generalization: REPEATABLE_METHOD | dedup: RULE_VARIANT
- description: 主要股東持股停在重要門檻的精確微下方（29.99% vs 30% GO線）→主動追問交易設計原因，從公告與結構找動機（避GO/避主要股東地位/避申報）。股權百分比是設計線索不是資料抄寫。
- required_inputs: 持股%精確值; 門檻列表（5/10/30/50/75）
- trigger: 持股停駐門檻−ε精確值
- falsification: 門檻停駐樣本的後續交易設計解釋率不顯著高於對照
- lineage: observations=['OBS-Z2-002'] sources=['CHAUHIN-COURSE-L2A'] cases=['CASE-CHAUHIN-29.99']

## CAND-HILTON-2668-SEQUENCE-001 — 莊家完整週期序列模板（2668型）
- methodology: HILTON | family: EVENT_SEQUENCE | generalization: REPEATABLE_METHOD | dedup: NEW_RULE
- description: 鬥長命股等待→大手股權轉讓避GO（20-30%停駐）→低位大比例折讓配股（可終止後重推）→股權集中報告+射倉組別=歸邊確認→ED入局→（受阻則兩路推演）→高位拆股/散貨財技→DI大幅減持→跌穿5%申報線=清倉→換主席=項目終結。前期部署訊號與後期出貨訊號可為同一類事實，意義隨週期位置反轉。
- required_inputs: 股權轉讓序列; 配股公告（比例/折讓/位置/終止）; 董事任命; DI百分比序列; 拆股/送股公告; 公眾持股/集中報告
- trigger: 大手股權轉讓停駐20-30%區間（入主避GO線索）
- falsification: 以序列模板回測歷史十倍股：階段命中率不顯著高於隨機對齊
- lineage: observations=['OBS-H9-002', 'OBS-H9-003', 'OBS-H9-004', 'OBS-H9-005'] sources=['HILTON-CAIJI-2668CASE'] cases=['CASE-HILTON-2668']

## CAND-HILTON-7SIGNALS-EXIT-001 — 七大出貨信號掃描器（程度×次數×組合）
- methodology: HILTON | family: CCASS_DISTRIBUTION | generalization: REPEATABLE_METHOD | dedup: NEW_RULE
- description: 出貨判斷掃描七信號：散貨財技(2次即足)/DI減持(程度)/CCASS出貨(10-20%正常、40%上限、以升幅校準敏感度：升幅越高微小減持越致命)/震倉(第三次近極限；縮量vs散貨大成交)/發水資產/媒體大幅曝光/大成交(細市值股用實際金額+一分鐘圖分辨射倉vs承接)。單一輕微訊號不作結論；大成交可單獨觸發離場。
- required_inputs: 財技通告序列; DI序列; CCASS持倉序列; 成交量（含分鐘級）; 媒體曝光（人工）
- trigger: 任一信號出現→按程度計分；大成交→可直接觸發
- falsification: 七信號計分與事後30日回撤無統計相關
- lineage: observations=['OBS-H8-004'] sources=['HILTON-CAIJI-L8'] cases=['CASE-HILTON-124', 'CASE-HILTON-1246', 'CASE-HILTON-1332']

## CAND-HILTON-ADJECTIVE-DECOMPOSE-001 — 形容詞分解：乾/靚/有勢必須還原為量化數字
- methodology: HILTON | family: SCENARIO | generalization: REPEATABLE_METHOD | dedup: NEW_RULE
- description: 任何文字評論（免費資訊尤其）中的形容詞須還原為可驗證數字：「乾」=歸邊約90%（課堂標準；70%不算乾）；「靚」=五因素通過；「有勢」=量價位置符合。免費資訊先當可能陷阱，按財技流程重檢後才可採信。
- required_inputs: 歸邊%數字; 五因素狀態; 量價數據
- trigger: 出現未量化的好淡形容詞
- falsification: 此規則僅為內部紀律，不適用傳統證偽——以『還原後數字與文章結論矛盾率』監察
- lineage: observations=['OBS-H6-005'] sources=['HILTON-CAIJI-L6'] cases=[]

## CAND-HILTON-ANCHOR-DUMP-001 — 錨定散貨：炒高未獲利→壓回途中真散貨
- methodology: HILTON | family: CCASS_DISTRIBUTION | generalization: POTENTIALLY_GENERALIZABLE | dedup: NEW_RULE
- description: （AUTHOR_INTERPRETATION級）十倍升幅過程以借款對敲維持，推高者尚未獲利；其後由高位壓回，散戶以最高價為錨覺得便宜接貨，大股東在下跌途中完成真正散貨。
- required_inputs: 高位與現價距離; 成交分佈
- trigger: 高位回落後散戶承接增加而大戶貨源下降
- falsification: 下跌途中CCASS大戶持股不降反升的案例比例過高
- lineage: observations=['OBS-H1-006'] sources=['HILTON-CAIJI-L1'] cases=[]

## CAND-HILTON-BLOCKED-BOTHWAYS-001 — 受阻兩路推演：續玩與離場皆需炒高=持有邏輯不變
- methodology: HILTON | family: SCENARIO | generalization: REPEATABLE_METHOD | dedup: NEW_RULE
- description: 主要交易被監管否決後，計算莊家合計持貨：續玩（注資推進）需炒高、離場（散50-60%貨）亦需炒高→兩路皆需推高時，終止本身不構成離場理由。僅當持貨結構支持兩路皆需炒高時成立；不可脫離持股/監管/承接力套用。
- required_inputs: 終止公告; 陣營合計持股%
- trigger: 交易終止公告發布
- falsification: 交易終止後60日回報：被標記股票與一般終止公告股無差異
- lineage: observations=['OBS-H9-004'] sources=['HILTON-CAIJI-2668CASE'] cases=['CASE-HILTON-2668']

## CAND-HILTON-BONUS-SHARE-29XX-001 — 送紅股除淨窗口：流通-90%+29XX轉碼掩藏派貨
- methodology: HILTON | family: CCASS_DISTRIBUTION | generalization: REPEATABLE_METHOD | dedup: NEW_RULE
- description: 送紅股除淨至生效日流通量大減（1送9剩一成）令操控成本降約九成；29XX臨時代碼循環再用使該窗口成交歷史難追查=派貨痕跡掩藏。送紅股通常屬高位散貨工具。
- required_inputs: 送股比例; 除淨日; 生效日; 公告時股價位置
- trigger: 除淨日進入流通縮減窗口
- falsification: 29XX窗口的CCASS大戶持股變化顯示無派發
- lineage: observations=['OBS-H3-005'] sources=['HILTON-CAIJI-L3'] cases=[]

## CAND-HILTON-CAPREORG-MAGNITUDE-001 — 混合資本重組威力計算：ABC組合=立即離場
- methodology: HILTON | family: SHARE_CONSOLIDATION | generalization: REPEATABLE_METHOD | dedup: NEW_RULE
- description: 計算混合重組（合股+削股+拆細未發行股份）的向下威力倍數：向下空間放大×配股折讓放大×可印股數放大。威力≥100倍（B路線級）已屬極端；約2,000倍（8071型）=立即離場。注意通告『未發行』三字與通告次序邏輯。
- required_inputs: 合股比例; 削股前後面值; 拆細比例; 法定/已發行/未發行股數（月報表核對）
- trigger: 公告序列：合股→削股→(拆細未發行)→供股
- falsification: 高威力重組標記的樣本群後續回升率不低於對照組
- lineage: observations=['OBS-H7-004'] sources=['HILTON-CAIJI-L7'] cases=['CASE-HILTON-8071', 'CASE-HILTON-941', 'CASE-HILTON-616']

## CAND-HILTON-CCASS-DRYNESS-CALC-001 — CCASS主動歸邊計算：非CCASS全記M貨+券商鴻溝斷層法
- methodology: HILTON | family: CCASS_CONCENTRATION | generalization: REPEATABLE_METHOD | dedup: NEW_RULE
- description: 歸邊%=（非CCASS股份全額+CCASS內鴻溝以上大行持倉）/總股本。非CCASS=總股本−CCASS總量（先全視為M貨，實體股回存會現異動）；鴻溝=持倉排序中由散戶級(≤0.2%)跳升至大戶級(≥2%)的數量級斷層。精度：>90%即足夠（91%vs98%無策略差異）。Top5/10法僅初篩（同莊可散六七間行）。
- required_inputs: CCASS總量/總股本比; participant持股排序
- trigger: 日常歸邊監察
- falsification: 鴻溝法估算與後續官方『股權高度集中』通告披露值系統性背離
- lineage: observations=['OBS-H7-006', 'OBS-H7-007'] sources=['HILTON-CAIJI-L7'] cases=['CASE-HILTON-75-15-90例']

## CAND-HILTON-CCASS-PARTCOUNT-001 — CCASS參與者數目下降=貨源收集中訊號
- methodology: HILTON | family: CCASS_CONCENTRATION | generalization: REPEATABLE_METHOD | dedup: NEW_RULE
- description: CCASS參與券商數目持續下降（100→90、150→90多間）=持貨券商減少、貨源集中中；與Top5/10集中度互補。參與者數降至低位+歸邊>90%=具備炒作條件（啟動日仍不可測）。
- required_inputs: CCASS參與者數序列; Top5/10集中度
- trigger: 參與者數持續下降且集中度同步上升
- falsification: 行數下降樣本群與行數穩定樣本群的後續炒作率無差異
- lineage: observations=['OBS-H4-009'] sources=['HILTON-CAIJI-L4'] cases=['CASE-HILTON-向下收貨型']

## CAND-HILTON-CCASSIN-POSITION-001 — CCASS In位置判讀：高位存入偏派貨、低位存入先炒後派
- methodology: HILTON | family: CCASS_TRANSFER | generalization: REPEATABLE_METHOD | dedup: NEW_RULE
- description: 實物存入CCASS=沽售條件成立的指向性訊號；判讀必先定價格位置：高位存入→派貨風險；低位大量存入→可能先炒高再派貨（對應更大炒高空間與後續派貨）。門檻：≥5%留意、≥10%強。屬風險定位訊號，非買賣指令。
- required_inputs: 存入者身份（是否只能是大股東）; 存入比例; 當前價格位置（週期高位/低位）
- trigger: 單次或累計存入≥5%
- falsification: 高位存入樣本群其後派發率不顯著高於對照
- lineage: observations=['OBS-H8-001'] sources=['HILTON-CAIJI-L8'] cases=[]

## CAND-HILTON-CEILING-GUARD-001 — 天花板與推高保護位：市值100億/20億、升幅3-4倍警戒
- methodology: HILTON | family: RISK_WINDOW | generalization: REPEATABLE_METHOD | dedup: NEW_RULE
- description: 風險天花板：主板市值≈100億、創業板≈20億；升幅3-4倍=莊家近零成本警戒區（即使無出貨信號亦加強風管）。持倉管理：升一倍收回本金、三倍必零成本；天花板區每日保護位=當日最低，跌穿前一日低位即離場。
- required_inputs: 當前市值; 入場後升幅倍數; 每日最低價序列
- trigger: 市值/升幅觸及天花板 或 每日滾動保護位被跌穿
- falsification: 3-4倍警戒離場策略的事後總回報顯著劣於持有至出貨信號
- lineage: observations=['OBS-H8-006', 'OBS-H8-008'] sources=['HILTON-CAIJI-L8'] cases=['CASE-HILTON-0530（反例）']

## CAND-HILTON-CHIP-BREAKOUT-001 — 蟹貨區：返家鄉沽壓+大戶全接=目標更高；突破後才是買點
- methodology: HILTON | family: CCASS_DISTRIBUTION | generalization: REPEATABLE_METHOD | dedup: NEW_RULE
- description: （作者解讀）高位蟹貨區因損失規避鎖死散戶；股價返家鄉時散戶打和沽出——大戶願全接蟹貨=目標更高。高效買點=大戶食清蟹貨並突破確認後，而非下跌途中估底（跌穿箱體常再跌1-2箱、每箱橫行6-9月）。
- required_inputs: 歷史價格成交量分佈; 當前價格位置
- trigger: 股價重返蟹貨區 / 突破蟹貨區
- falsification: 突破蟹貨區樣本與假突破樣本的後續回報無統計差異
- lineage: observations=['OBS-H4-010'] sources=['HILTON-CAIJI-L4'] cases=[]

## CAND-HILTON-CONSOL-INTENT-001 — 合股意圖判讀：貼一仙合股=向下路線極差評級
- methodology: HILTON | family: SHARE_CONSOLIDATION | generalization: REPEATABLE_METHOD | dedup: NEW_RULE
- description: 合股六原因判讀（減流通/碎股/攤薄/加向下空間/重印平股/吸基金），以四、五為主導：股價接近一仙宣布合股=結構性向下訊號（極差、離場）；合股後配供股（合不離供）=印平股前奏；合至兩位數+獨立正面證據才可考慮吸基金解讀（比例極低，不懂分辨先當負面）。
- required_inputs: 合股比例; 公告時股價（相對一仙距離）; 其後通告序列（供股/CB）
- trigger: 合股公告
- falsification: 貼一仙合股樣本群的後續表現不差於一般仙股
- lineage: observations=['OBS-H7-001', 'OBS-H7-002'] sources=['HILTON-CAIJI-L7'] cases=['CASE-HILTON-1492', 'CASE-HILTON-天行國際']

## CAND-HILTON-CUTPAR-POSITIVE-001 — 獨立削股=轉盈恢復派息訊號（對比混合重組）
- methodology: HILTON | family: CAPITAL_STRUCTURE | generalization: REPEATABLE_METHOD | dedup: NEW_RULE
- description: 單獨出現的削減股本（不與合股/拆細並列）=管理層讀取訊號：清累虧恢復派息能力，預示轉盈/特別股息。加權訊號=削股金額≈累計虧損金額+發生在重大正面事件（中標/新項目）同期。其後供股完成為入場確認（488模式）。
- required_inputs: 削股金額; 當期累計虧損; 同期公司事件; 其後資本行動序列
- trigger: 削股金額≈累計虧損且無合股/拆細伴隨
- falsification: 獨立削股樣本群其後特別股息/盈利改善率不顯著高於對照
- lineage: observations=['OBS-H7-003'] sources=['HILTON-CAIJI-L7'] cases=['CASE-HILTON-488']

## CAND-HILTON-DI-ARTIFACT-001 — DI三大盲點排除：>100%/重複申報/包銷商假持股
- methodology: HILTON | family: CONTROL_CHANGE | generalization: REPEATABLE_METHOD | dedup: NEW_RULE
- description: DI解讀前置排除：(1)>100%=衍生工具股份制申報假象 (2)配偶/受控公司/實益擁有人同一批股份重複申報——不可相加 (3)供股包銷商短暫大量持股≠入主。排除後才評估真實增減持程度。
- required_inputs: 申報方身份關係; 申報性質（股份/衍生工具/權益種類）; 事件類型（是否供股包銷）
- trigger: DI出現異常值（>100%、多人同批股、包銷事件期）
- falsification: 被標記artifact的申報事後證實為真實持股變動的比例偏高
- lineage: observations=['OBS-H8-003'] sources=['HILTON-CAIJI-L8'] cases=[]

## CAND-HILTON-DIPBOUNCE-001 — 急跌博反彈：被迫斬倉三條件+買盤回流確認
- methodology: HILTON | family: RISK_WINDOW | generalization: REPEATABLE_METHOD | dedup: NEW_RULE
- description: 僅針對非自願急跌（被迫斬倉）的短線反彈策略。三必要條件：(1)非莊家安排——判別線索：同系多股同日急跌/大股東持股未減 (2)跌幅：細價股≥70%（85-90%+理想）(3)市值極低（隨殼價環境更新）。進場=一分鐘圖成交縮→停→由細轉大；離場=1-2倍/跌幅一半阻力/盤路信號。理想個案一年約三四次，細注。
- required_inputs: 跌幅%（高點至現價）; 急跌後市值; 同系/同戶口股票同日表現; 分鐘級成交量序列
- trigger: 三條件同時成立+買盤回流形態
- falsification: 符合三條件的樣本群其後反彈率/幅度不顯著高於隨機急跌股
- lineage: observations=['OBS-H10-001', 'OBS-H10-002'] sources=['HILTON-CAIJI-DIPBOUNCE'] cases=['CASE-HILTON-1428', 'CASE-HILTON-謎網2017', 'CASE-HILTON-大發地產']

## CAND-HILTON-DOWNWARD-PLAY-001 — 向下炒辨識：長期陰跌+反覆印平股兩必要條件→永久避開
- methodology: HILTON | family: CAPITAL_STRUCTURE | generalization: REPEATABLE_METHOD | dedup: NEW_RULE
- description: 向下炒=股價數年至十年長期向下（累跌>90%反覆再跌）+不斷印發大量極低價股票（配股/供股/CB）兩條件同時成立；盈利結構=同伙人以高價關連資產交易套出公司/散戶資金。辨識後永久避開；股權分散僅加分線索，M歷史仍排第一。
- required_inputs: 長期價格序列（累計跌幅）; 配股/供股/CB歷史序列; 關連資產收購記錄（收購價 vs 後續減值）
- trigger: 兩必要條件同時成立
- falsification: 被標記公司的關連收購後續表現（減值/回報）與正常公司無差異
- lineage: observations=['OBS-H5-003', 'OBS-H5-004'] sources=['HILTON-CAIJI-L5'] cases=['CASE-HILTON-1222-宏安系', 'CASE-HILTON-1338', 'CASE-HILTON-11年13次']

## CAND-HILTON-DRYNESS-90-001 — 乾度90%門檻+M質素補足+券商集中低估
- methodology: HILTON | family: CCASS_CONCENTRATION | generalization: REPEATABLE_METHOD | dedup: NEW_RULE
- description: 一般M以90%歸邊為足夠（92%與96%不區分）；神級M可放寬至七成多；CCASS表面歸邊低估實際控制（貨源集中首10-20券商）。乾度只排五因素第四，不可單獨觸發參與。
- required_inputs: 歸邊百分比; M身份與往績
- trigger: 歸邊≥90%（一般M）或≥70%+神級M
- falsification: 90%門檻案例群與70-90%案例群的事後升幅無統計差異（在M質素分層後）
- lineage: observations=['OBS-H1-010', 'OBS-H1-001'] sources=['HILTON-CAIJI-L1'] cases=['CASE-HILTON-8198', 'CASE-HILTON-0926', 'CASE-HILTON-0122']

## CAND-HILTON-FACTION-NETWORK-001 — 莊家派系名單：跨公司重複人物/收購/重組/改名線索累積
- methodology: HILTON | family: CONTROL_CHANGE | generalization: REPEATABLE_METHOD | dedup: NEW_RULE
- description: 以新十倍股為觸發，追溯大股東→人物關係→過往個案，累積派系名單（莊家/相關人物/曾炒股票/背後大股東）；辨認線索=跨公司重複人物、收購、重組、改名。名單隨案例生長，同一批人物重複出現即派系確認。
- required_inputs: 公司股權披露; 董事/高管名單; 改名與重組歷史; 歷史炒作倍數
- trigger: 新十倍股出現 或 同一人物跨公司重複出現
- falsification: 派系關聯預測的後續項目成功率不高於隨機人物組合
- lineage: observations=['OBS-H6-004'] sources=['HILTON-CAIJI-L6'] cases=['CASE-HILTON-1462', 'CASE-HILTON-1222-鄧清河']

## CAND-HILTON-FAKE-MOVE-EXCLUDE-001 — 假異動排除：公司行動造成的CCASS持倉%突變
- methodology: HILTON | family: CCASS_TRANSFER | generalization: REPEATABLE_METHOD | dedup: NEW_RULE
- description: 供股除權/新股出爐/股本變動/供股權過戶造成的持倉百分比突變=機制性假異動；須與公司行動日曆核對後排除，不作收貨/出貨解讀。配合T+3結算延遲：觀察窗口計算須容忍最近三日不可見。
- required_inputs: 公司行動日曆（除權日/生效日/結果日）; CCASS突變日期
- trigger: 突變日±窗口內有公司行動
- falsification: 被排除的假異動中人工複核證實含真實派發的比例偏高
- lineage: observations=['OBS-H8-007'] sources=['HILTON-CAIJI-L8'] cases=[]

## CAND-HILTON-GO-2020-001 — GO+20/20配股高分組合（勝率約八至九成）
- methodology: HILTON | family: PLACEMENT | generalization: REPEATABLE_METHOD | dedup: NEW_RULE
- description: GO結束後出現約20%折讓、20%比例配股=極高分組合；課堂觀察勝率約八至九成，常見三至四個月內三至四倍。10/10不算完整組合；疊加爆炒往績新主更高分。
- required_inputs: 配股比例; 配股折讓; GO完成狀態
- trigger: GO後配股比例≈20%且折讓≈20%
- falsification: 獨立回測中GO+20/20的勝率或倍數顯著低於八至九成/三至四倍
- lineage: observations=['OBS-H2-009'] sources=['HILTON-CAIJI-L2'] cases=['CASE-HILTON-1143']

## CAND-HILTON-GO-STAGE-MATRIX-001 — GO五階段風險回報矩陣與分階段退出規則
- methodology: HILTON | family: STAGE_CLASSIFICATION | generalization: REPEATABLE_METHOD | dedup: NEW_RULE
- description: GO項目按時間線分A(潛伏)/B(洽談)/C(GO包底)/D(GO後炒作)/E(三年注資)五階段，每階段有獨立風險回報與退出規則；值博率最高A/C/D。C階段強制GO結束前兩日離場；D階段以GO後一個月守GO價為分界。
- required_inputs: 3.7/3.8通告日; 正式易手日; GO起止日; GO價; 新主身份
- trigger: 階段轉換事件：洽談公布/正式易手/GO開始/GO結束/三年期滿
- falsification: C階段『GO結束前兩日離場』規則在回測中劣於持有越過GO結束; D階段一個月守GO價與後續回報無相關
- lineage: observations=['OBS-H2-003', 'OBS-H2-006', 'OBS-H2-007'] sources=['HILTON-CAIJI-L2'] cases=['CASE-HILTON-1143', 'CASE-HILTON-1957', 'CASE-HILTON-0102']

## CAND-HILTON-LIQUIDITY-PHASE-001 — 流動性反訊號：低位難買=收貨中；高位易沽=散貨期
- methodology: HILTON | family: CCASS_ACCUMULATION | generalization: POTENTIALLY_GENERALIZABLE | dedup: NEW_RULE
- description: （作者解讀）細價股低位買盤稀少=莊家同步收貨；升數倍仍沽不出=大股東散貨期未到；高位買盤異常充足=散貨殺戮期。持倉>2-3%會被莊家辨認，須拆倉多行。
- required_inputs: 日成交量; 買賣盤深度; 價格位置
- trigger: 低位持續買不到貨 / 高位持續輕易沽出
- falsification: 低位難買樣本群與流動性正常樣本群的後續回報無差異
- lineage: observations=['OBS-H3-011'] sources=['HILTON-CAIJI-L3'] cases=['CASE-HILTON-1367']

## CAND-HILTON-NONGO-FLOOR-001 — Non-GO最低市值=舊主應得殼價÷餘下比例
- methodology: HILTON | family: NON_GO | generalization: REPEATABLE_METHOD | dedup: NEW_RULE
- description: Non-GO後最低合理總市值=（合理殼價×舊主原持股比例）÷完成後舊主餘下比例。商業邏輯：舊主餘下股份炒高後價值≥其原應得殼價才合理。公式只定下限；預設不參與，僅在著名新主+上市多年舊殼+排除期殼時考慮。
- required_inputs: 殼價; 扣水NAV; 舊主原持股%; 完成後舊主餘下%; 現市值
- trigger: Non-GO事件辨識（大量印股/供股包銷/CB/認股權/押股致控制權轉移）
- falsification: 已知Non-GO案例的實際市值路徑系統性低於公式下限
- lineage: observations=['OBS-H3-003', 'OBS-H3-001'] sources=['HILTON-CAIJI-L3'] cases=['CASE-HILTON-01250', 'CASE-HILTON-0241', 'CASE-HILTON-1143', 'CASE-HILTON-0112']

## CAND-HILTON-OLD-OWNER-STAKE-001 — 舊主留一手：保留9.x%>4.x%加分訊號
- methodology: HILTON | family: CONTROL_CHANGE | generalization: REPEATABLE_METHOD | dedup: NEW_RULE
- description: GO後舊主不清倉而保留少數股權=知悉新主後續計劃的加分訊號（作者解讀）。強度：9.x%（貼10%主要股東門檻下最大保留）>4.x%。判斷只用已披露持股，不猜背後協議。
- required_inputs: 舊主轉移後持股披露
- trigger: 舊主保留4.x%-9.x%
- falsification: 保留9.x%的GO項目後續表現與全清倉項目無統計差異
- lineage: observations=['OBS-H2-010'] sources=['HILTON-CAIJI-L2'] cases=['CASE-HILTON-2183', 'CASE-HILTON-0848']

## CAND-HILTON-PLACEMENT-CHECKLIST-001 — 配股七利好六利淡位置判斷清單
- methodology: HILTON | family: PLACEMENT | generalization: REPEATABLE_METHOD | dedup: NEW_RULE
- description: 配股Signal好淡由七利好（低位零成交/大比例大折讓/配新股/≥6名匿名承配/殼底乾/M有往績/低市值集中）對六利淡（高位/小比例小折讓/配舊股/<6名披露/知名基金承接/位置模糊）計分；知名基金承接=離場訊號。
- required_inputs: 股價位置（高低位）; 配股形式（新/舊/先舊後新）; 比例與折讓; 承配人人數與披露狀態
- trigger: 配股通告（一般授權≤20%/19.99%或特別授權）
- falsification: 清單分類與事後價格路徑（啟動/派貨）無統計相關
- lineage: observations=['OBS-H3-008', 'OBS-H3-009'] sources=['HILTON-CAIJI-L3'] cases=['CASE-HILTON-8218', 'CASE-HILTON-0007', 'CASE-HILTON-2346', 'CASE-HILTON-0476']

## CAND-HILTON-PLACEMENT-TSTOP-001 — 配股時間止蝕：半個月至一個月不啟動即離場
- methodology: HILTON | family: PLACEMENT | generalization: REPEATABLE_METHOD | dedup: NEW_RULE
- description: 優質配股項目半個月至一個月內啟動（快於供股半年期約12倍）；到期不動即時間止蝕換馬，不把等待合理化。短炒型（貨源七成）一兩日內完成只宜小注。
- required_inputs: 配股完成日; 持倉入場日
- trigger: 入場後滿一個月未啟動
- falsification: 回測顯示一個月未啟動項目的其後表現不差於已啟動項目
- lineage: observations=['OBS-H3-010'] sources=['HILTON-CAIJI-L3'] cases=['CASE-HILTON-8218', 'CASE-HILTON-8452', 'CASE-HILTON-1327']

## CAND-HILTON-REPEAT-DILUTE-001 — 反覆供股慣犯排除+低於5%隱藏控制偵測
- methodology: HILTON | family: CAPITAL_STRUCTURE | generalization: REPEATABLE_METHOD | dedup: NEW_RULE
- description: 每兩三年重複供錢的股票（8212五次）列為慣犯永久排除；反覆供股可令公眾持股遠低於25%甚至名義100%（安排人士），真正控制者隱藏在5%申報線下——披露持股嚴重低估控制度。
- required_inputs: 歷史供股日期序列; 公眾持股比例
- trigger: 供股間隔≤3年重複發生; 公眾持股<25%或名義100%
- falsification: 反覆供股但公眾持股維持>25%且隨後出現正向回報的案例群
- lineage: observations=['OBS-H1-012', 'OBS-H1-005'] sources=['HILTON-CAIJI-L1'] cases=['CASE-HILTON-8212', 'CASE-HILTON-8198']

## CAND-HILTON-REVENGE-TIMING-001 — 供股復仇記三條件+時間窗
- methodology: HILTON | family: RIGHTS_ISSUE | generalization: REPEATABLE_METHOD | dedup: NEW_RULE
- description: 順勢賺供錢盤：須同時滿足(1)真正大比例大折讓(2)除權後市價貼近供股價（數個百分點）(3)M非反覆供股慣犯且歷史清楚。止蝕供股價微下方；Last Pay Day前一至兩日必須離場。
- required_inputs: 供股比例與折讓; 除權後市價; 供股價; M歷史; Last Pay Day日期
- trigger: 三必須條件同時成立
- falsification: Last Pay Day前離場規則系統性劣於持有至新股日（回測）; 三條件外的案例大量成功
- lineage: observations=['OBS-H1-003'] sources=['HILTON-CAIJI-L1'] cases=['CASE-HILTON-0149']

## CAND-HILTON-RREPORT-COUNT-001 — R報告申請份數≤30=散戶冷清
- methodology: HILTON | family: RIGHTS_ISSUE | generalization: REPEATABLE_METHOD | dedup: NEW_RULE
- description: 供股結果(R報告)申請份數是散戶參與度代理：≤30份偏好（散戶沒跟供）；配合供乾判讀。觀察期規則：供股項目半年、配股項目一至兩個月不啟動即離場。
- required_inputs: 申請份數
- trigger: 申請份數≤30
- falsification: 份數≤30與>30的後續表現無差異
- lineage: observations=['OBS-H1-008'] sources=['HILTON-CAIJI-L1'] cases=['CASE-HILTON-0926', 'CASE-HILTON-0122', 'CASE-HILTON-1626', 'CASE-HILTON-0530']

## CAND-HILTON-RREPORT-DARK-001 — R報告異常接受比例=暗倉過倉線索
- methodology: HILTON | family: CCASS_TRANSFER | generalization: POTENTIALLY_GENERALIZABLE | dedup: NEW_RULE
- description: 市價長期高於GO價時接受要約者必蝕價，理性散戶不會接受；R報告中異常高的接受比例（如01236的20%）推斷為舊主暗倉過倉→實際控制≈易手比例+異常接受比例。屬作者解讀，需CCASS佐證。
- required_inputs: R報告接受比例; 市價/GO價對照; 易手比例
- trigger: 接受比例顯著高於蝕價接受所能解釋的散戶行為
- falsification: CCASS數據顯示異常接受部分並非流向新主關聯券商
- lineage: observations=['OBS-H2-011'] sources=['HILTON-CAIJI-L2'] cases=['CASE-HILTON-01236']

## CAND-HILTON-SHELL-PRICE-001 — 合理賣殼價=殼價+扣水NAV
- methodology: HILTON | family: SHELL_VALUE | generalization: REPEATABLE_METHOD | dedup: NEW_RULE
- description: 殼價（隨年份/主板創業板變動）+扣水NAV（商譽歸零、內地物業廠房歸零、香港物業現金100%）=合理賣殼價；現市值對合理賣殼價的折讓=A階段潛在利潤空間。NAV越低殼越乾淨。
- required_inputs: 殼價; NAV明細（商譽/物業所在地/現金）; 已發行股數; 現市值
- trigger: 市值顯著低於合理賣殼價
- falsification: 實際GO成交價系統性偏離(殼價+扣水NAV)公式超出殼價行情誤差
- lineage: observations=['OBS-H2-004'] sources=['HILTON-CAIJI-L2'] cases=['CASE-HILTON-1143']

## CAND-HILTON-SHELLFARM-IPO-001 — 啤殼篩選：集資額不合理+七條件半新股初篩
- methodology: HILTON | family: SHELL_VALUE | generalization: REPEATABLE_METHOD | dedup: NEW_RULE
- description: 主判準=集資額相對盈利/上市費用不合理地低；輔以七條件（集資低/市值貼底/Top5-10券商>90%/CCASS參與者數下降/日成交<50-100萬/橫行≤30%/排除內資H股）篩出啤殼，小注分散持有，兩年（可放寬三年）時間框架。
- required_inputs: 集資額; 過往盈利; 上市費用; 上市市值; CCASS Top5/10集中度; CCASS參與者數序列; 日成交額
- trigger: 集資額≈1-2年盈利 或 淨集資≈上市費用
- falsification: 符合篩選的樣本群三年內升幅分佈與隨機半新股無差異
- lineage: observations=['OBS-H4-006', 'OBS-H4-007'] sources=['HILTON-CAIJI-L4'] cases=['CASE-HILTON-1496']

## CAND-HILTON-SHELLFARM-TIMING-001 — 啤殼啟動時間窗：1.5-2年最易啟動；>3年模型失效
- methodology: HILTON | family: RISK_WINDOW | generalization: REPEATABLE_METHOD | dedup: NEW_RULE
- description: 啤殼時間壓力模型：上市0-6月禁售；6-12月可減持至51%；12月後可賣殼。班底套現壓力遞增→1.5-2年最易啟動；>2-3年=班底問題；3-5年不動=不再以原模型等待。股災期可把異常時間加回。
- required_inputs: 上市日期
- trigger: 上市後月齡跨越6/12/18/24/36月界
- falsification: 啟動日分佈與2年壓力模型預測無關
- lineage: observations=['OBS-H4-008'] sources=['HILTON-CAIJI-L4'] cases=['CASE-HILTON-夜場殼-一年零三日']

## CAND-HILTON-SPINOFF-PRESSURE-001 — 分拆沽壓：被動基金強制沽售為主要沽壓源（證據增補）
- methodology: HILTON | family: EVENT_SEQUENCE | generalization: REPEATABLE_METHOD | dedup: SAME_RULE_NEW_EVIDENCE
- description: 【SAME_RULE_NEW_EVIDENCE】補強 CAND-HILTON-SPINOFF-PRESSURE-001：第一輪沽壓的最大來源除散戶無償沽售與基金主題不合外，明確加入被動基金強制沽售——指數成分股分拆的子公司不自動入指數（中信電子案例沽壓後估值一度5-6倍PE）。同一操盤者連續分拆均十倍（0015→1372）為重點留意線索。
- required_inputs: 母公司是否指數成分股; 分拆形式; 上市日期
- trigger: 母公司屬指數成分股的分拆（被動沽壓加權）
- falsification: 指數成分股分拆與非成分股分拆的首輪沽壓深度無統計差異
- lineage: observations=['OBS-H10-003'] sources=['HILTON-CAIJI-DIPBOUNCE'] cases=['CASE-HILTON-2121', 'CASE-HILTON-中信電子', 'CASE-HILTON-0015-1372']

## CAND-HILTON-SPRING-DUCK-001 — 春江鴨異動：低位連升+量爆→第二日收市前追入
- methodology: HILTON | family: EVENT_SEQUENCE | generalization: REPEATABLE_METHOD | dedup: NEW_RULE
- description: 公告前的異常量價（低位連升兩三日+成交量放大數十倍）=知情資金線索；追入點=第二日收市前（確認量大於第一日），成本控制在異動前價+10%內；3.8通告提升確定性。追錯則跌回原位，須止蝕。
- required_inputs: 日成交量序列; 日收盤價序列
- trigger: 連續2日升+量較平日放大一個數量級
- falsification: 第二日收市前追入法的事後統計不優於隨機低位買入
- lineage: observations=['OBS-H2-005'] sources=['HILTON-CAIJI-L2'] cases=['CASE-HILTON-1143']

## CAND-HILTON-SUPPLY-INTENT-001 — 除權後市價 vs 供股價 = 供乾/供錢分辨器
- methodology: HILTON | family: RIGHTS_ISSUE | generalization: REPEATABLE_METHOD | dedup: NEW_RULE
- description: 供股除權後：大股東推高市價吸引散戶付款=供錢；壓住股價貼近供股價橫行令散戶放棄=供乾（包銷大股東收貨）。判斷先於一切其他通告分析。
- required_inputs: 除權後市價序列; 供股價; 包銷商身份
- trigger: 除權後市價走向：向上推 vs 貼供股價橫行
- falsification: 除權後走勢與目的分類系統性不符（如供乾案例大股東認購結果低於包銷上限）
- lineage: observations=['OBS-H1-002', 'OBS-H1-011'] sources=['HILTON-CAIJI-L1'] cases=['CASE-HILTON-0530', 'CASE-HILTON-0926', 'CASE-HILTON-0122', 'CASE-HILTON-1626']

## CAND-HILTON-THRESHOLD-HUG-001 — 貼門檻持股=路徑意圖線索（29.97%避GO）
- methodology: HILTON | family: CONTROL_CHANGE | generalization: REPEATABLE_METHOD | dedup: NEW_RULE
- description: 披露持股異常停駐在法定門檻微下方（29.97%貼30%強制GO線）=刻意選擇交易路徑的線索（此例：避GO走Non-GO）。平台層面同樣監察貼5%/10%/30%/50%的停駐。
- required_inputs: 持股%序列; 門檻值列表（5/10/30/50）
- trigger: 持股持續停駐門檻−ε且無自然解釋
- falsification: 貼門檻停駐樣本的後續路徑與隨機持股群無差異
- lineage: observations=['OBS-H3-012'] sources=['HILTON-CAIJI-L3'] cases=['CASE-HILTON-81XX-JIANZHIJIAN']

## CAND-HILTON-VOLUME-DIVERGENCE-001 — 大成交=分歧度量：極端位置才可解讀反轉
- methodology: HILTON | family: EVENT_SEQUENCE | generalization: REPEATABLE_METHOD | dedup: NEW_RULE
- description: 成交量量度市場分歧而非買賣力量：突破+大成交正面；趨勢中大成交回歸=反轉首訊號；極端位置（遠離箱體）的極端大成交+急跌=短線見底候選（博1-2日反彈，非趨勢轉好）。箱體中間的大成交不作見底解讀。
- required_inputs: 成交量異常偵測（相對近期均值）; 價格位置（相對箱體）
- trigger: 成交爆量+位置極端
- falsification: 極端位置爆量後的1-2日反彈率不顯著高於基準
- lineage: observations=['OBS-H5-006'] sources=['HILTON-CAIJI-L5'] cases=['CASE-HILTON-TQQQ-期權260%']

## CAND-HILTON-WHITEKNIGHT-CB-001 — 白武士CB路徑：兌換後>90%歸邊+成本≤一仙=炒作動機判準
- methodology: HILTON | family: COST_REPAIR | generalization: REPEATABLE_METHOD | dedup: NEW_RULE
- description: 白武士重組經削債→Non-GO→CB注資→兌換後歸邊≥90%、平均成本攤至≤一仙。判準：兌換後歸邊≥90%+商業炒作動機=好項目；六七成歸邊（政府型重組）=不參與。『死殼邊有唔炒』。
- required_inputs: CB條款（換股價/規模）; 兌換後持股比例; 白武士平均成本
- trigger: CB兌換完成/復牌事件
- falsification: ≥90%歸邊白武士樣本群復牌後長期（>5年）無炒作的比例顯著偏高
- lineage: observations=['OBS-H4-001', 'OBS-H4-002'] sources=['HILTON-CAIJI-L4'] cases=['CASE-HILTON-0607', 'CASE-HILTON-0931', 'CASE-HILTON-2326', 'CASE-HILTON-1220']

## CAND-IVANL-LADDER-STAKE-001 — 市值階梯注碼與炒高後分級警覺
- methodology: IVAN_L | family: RISK_WINDOW | generalization: REPEATABLE_METHOD | dedup: NEW_RULE
- description: 部署階梯（主板）：3億留意→2-3億細注→1-2億中注→1億以下大注（條件不變前提）。持有階梯：≈3億第一重要區→5-6億驗證推動力→7-8億轉散貨/街貨監察→≈20億超高區。兩方向都以市值為尺度、非價格；條件破壞即停加注。
- required_inputs: 即時市值; 市值區間邊界; 篩選條件狀態
- trigger: 市值跨越階梯邊界
- falsification: 階梯注碼法的事後資金加權回報不優於一次性等額
- lineage: observations=['OBS-I1-003', 'OBS-I1-005'] sources=['IVANL-LXING-COURSE'] cases=['CASE-IVANL-2.8億-4.4億案例']

## CAND-IVANL-LXING-SCREEN-001 — L型絕地篩選器：半新股+天生乾身+集資低+絕地形態
- methodology: IVAN_L | family: SHELL_VALUE | generalization: REPEATABLE_METHOD | dedup: NEW_RULE
- description: 候選篩選四支柱：(1)半新股（1-3年內，貨源/人物可由招股文件+招股結果追溯）(2)天生乾身（公開發售有限、街貨低）(3)集資額低（主板≈1億以下；主動少集=保貨源集中）(4)絕地形態（快速跌穿招股價+沉底6-12月）。條件不足即不買；形態變種存在，不機械套圖。
- required_inputs: 上市日期; 集資額; 公開發售/配售結構; 招股結果認購結構; 上市後價格歷史（vs 招股價）
- trigger: 四支柱初篩通過
- falsification: 通過篩選的候選池與隨機半新股的後續回報無統計差異
- lineage: observations=['OBS-I1-001', 'OBS-I1-002'] sources=['IVANL-LXING-COURSE'] cases=['CASE-IVANL-2.8億-4.4億案例']

