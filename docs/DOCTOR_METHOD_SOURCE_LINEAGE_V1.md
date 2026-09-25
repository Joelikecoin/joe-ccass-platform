# DOCTOR_METHOD_SOURCE_LINEAGE_V1

Answering 「呢條規則係邊度學返嚟？」: rule_candidate → methodology → source →
source section → case → observation → evidence chain. Generated from the dev
ingestion store; no orphan candidates (schema-enforced).

## Source units (13)
| source_id | title | methodology | type | status |
|---|---|---|---|---|
| CHAUHIN-COURSE-L1 | 周顯大師股票投資課程-第1堂_課程知識摘要 | CHAU_HIN | course_summary | INGESTED |
| CHAUHIN-COURSE-L2A | 周顯大師股票投資課程-第2A堂_課程知識摘要 | CHAU_HIN | course_summary | INGESTED |
| HILTON-CAIJI-2668CASE | 莊家佈局2668_課程摘要 | HILTON | case_study | INGESTED |
| HILTON-CAIJI-DIPBOUNCE | 急跌博反彈_課程摘要 | HILTON | course_summary | INGESTED |
| HILTON-CAIJI-L1 | 財技班第一堂_課程摘要 | HILTON | course_summary | INGESTED |
| HILTON-CAIJI-L2 | 財技班第二堂_課程摘要 | HILTON | course_summary | INGESTED |
| HILTON-CAIJI-L3 | 財技班第三堂_課程摘要 | HILTON | course_summary | INGESTED |
| HILTON-CAIJI-L4 | 財技班第四堂_課程摘要 | HILTON | course_summary | INGESTED |
| HILTON-CAIJI-L5 | 財技班第五堂_課程摘要 | HILTON | course_summary | INGESTED |
| HILTON-CAIJI-L6 | 財技班第六堂_課程摘要 | HILTON | course_summary | INGESTED |
| HILTON-CAIJI-L7 | 財技班第七堂_課程摘要 | HILTON | course_summary | INGESTED |
| HILTON-CAIJI-L8 | 財技班第八堂_課程摘要 | HILTON | course_summary | INGESTED |
| IVANL-LXING-COURSE | L型絕地_課程知識摘要 | IVAN_L | course_summary | INGESTED |

## Evidence chains (10) — intermediate steps preserved
- `CHAIN-H1-004` → OBS-H1-004: input_facts=0530第一次1供9@$0.67，170份申請（7%為安排人士）; 第二次2供5@$1.07（市價$1.7），35份，公眾持股約24%; 第三次10供11@$1.07（市價$1.05，市價<供股價=假供股），22份 → temporal_order=三次供股序列→等約三年→2015大市極佳才啟動 → calculation_or_comparison=三次後股本擴大73倍；大股東明面69%+安排7%≈控制76%；投入近100億 → author_reasoning=巨額資金鎖死需要極佳市況才能獲利離場；市值由百億級放大至約3000億 → author_conclusion=規模巨大的供乾項目會等待大市極佳才啟動，需要超長耐心
- `CHAIN-H2-011` → OBS-H2-011: input_facts=01236易手比例35%（有條件全購）; R報告：20%股份接受要約; 市價長期高於GO價 → temporal_order=GO結束後R報告揭示接受結構 → calculation_or_comparison=35%易手+20%接受=55%；接受者蝕價（市價>GO價）違反散戶理性 → author_reasoning=只有與交易相關的暗倉才會蝕價接受→20%為舊主暗倉過倉 → author_conclusion=實際控制約55%，成為歸邊線索（AUTHOR_INTERPRETATION，需CCASS佐證）
- `CHAIN-H3-003` → OBS-H3-003: input_facts=01250印股前市值約5億；一配四後約25億; 殼價約5億+NAV約1億=合理殼價6億; 舊主75%→Non-GO後約5%；新主約80%；散戶約1.5% → temporal_order=印股（一配四）→市值25億→其後六個月炒至$1.9 → calculation_or_comparison=舊主應得=6億×75%=4.5億；最低市值=4.5億÷5%=90億；25億→90億=三至四倍最低空間 → author_reasoning=舊主自願被攤薄的前提是餘下股份經炒高後≥正常GO應得金額 → author_conclusion=實際$0.14→$1.9（十多倍）遠超最低公式；公式只定下限，離場跟出貨訊號
- `CHAIN-H4-004` → OBS-H4-004: input_facts=0607於2008停牌；2010簡志堅以約350萬購舊主36%; 2013削債約3億+舊業務賣回舊主; Open Offer集資約4,000萬@0.05印約16億股，季昌群包銷取得約52%; 注資約5億地產項目以CB@0.05支付（可換約100億股） → temporal_order=停牌(2008)→購股(2010)→重組建議(2013)→CB兌換→復牌→四年炒至最高$4.5 → calculation_or_comparison=CB兌換後>90%持股，平均成本約一仙；$0.05復牌=5倍帳面；$4.5=90倍；市值5億→500億 → author_reasoning=成本約1億級白武士項目必須靠復牌後極高倍數回報；歸邊+歷史客源支撐炒作 → author_conclusion=『死殼邊有唔炒』：完成九成歸邊重組的白武士項目具有結構性炒作動機
- `CHAIN-H5-004` → OBS-H5-004: input_facts=市價$1；$0.90配發20股，認購人付$18; 上市公司以$18向資產賣方收購項目; 四方：上市公司/認購人/資產賣方/散戶 → temporal_order=配股→付款→收購資產→其後股價自由落體不影響已套現金 → calculation_or_comparison=$1時20股值$20帳面賺$2；$0.90打和；$0.80蝕$2——但賣方盈利=$18−真實成本，與股價無關 → author_reasoning=大股東/認購人/賣方同伙時帳面只是內部轉移；散戶承受攤薄+下跌 → author_conclusion=向下炒的盈利錨在資產交易差價，股價下跌不阻礙獲利——必須永久避開此類結構
- `CHAIN-H7-004` → OBS-H7-004: input_facts=8071法定股本$2億/面值$0.01/最多可發行200億股/已發行92億/未發行108億; 10合1後面值$0.10、最多20億、已發行9.2億; 削股+拆細未發行後面值$0.01、最多200億、已發行仍9.2億 → temporal_order=轉百慕達註冊（免法院審批）→10合1→削股→拆細未發行→其後可極折讓供股 → calculation_or_comparison=未發行=200−9.2=190.8億股；印股能力由1:1.5→1:20；向下空間×10×折讓×10×印股×10≈威力×2,000 → author_reasoning=三步組合的每一部份都有獨立通告依據，次序不可倒轉（先合股削股才有條件極折讓） → author_conclusion=見到ABC混合重組通告=向下炒終極結構，立即離場
- `CHAIN-H8-004` → OBS-H8-004: input_facts=莊家集中貨源>90%; 正常散貨量10-20%，極端上限約40%; 個案：升十倍沽約10%、升百倍沽約1%已回本 → temporal_order=出貨信號先於價格崩跌；DI減持→CCASS分散→大成交的常見序列 → calculation_or_comparison=升幅×沽出比例=套現額；升幅越高，套現所需沽出比例越小——微小CCASS減持在高位即致命 → author_reasoning=莊家毋須散清九成貨；以獲利倍數反推所需最小沽出量 → author_conclusion=CCASS出貨判讀必須以升幅校準敏感度，不能以固定比例為安全閾
- `CHAIN-H9-005` → OBS-H9-005: input_facts=2013-05-31: 25.56%鄭→詹轉讓; 2013-08-08: 20%配股；08-28吳良好14.13%; 2014-03-14: 一拆五; 2014-07-03: 詹21.35%→7.22%；07-29→0.15% → temporal_order=入主(避GO)→配股部署→歸邊→ED入局→出售受阻(兩路皆需炒高)→拆股出貨→DI清倉→換主席 → calculation_or_comparison=持貨50-60%合計；詹持股21.35%→7.22%→0.15%（跌穿5%申報線） → author_reasoning=每一步以SDI/通告/集中報告/公眾持股報告等公開資料獨立可驗證 → author_conclusion=完整莊家週期（等待→入主→部署→受阻推演→散貨）可用公開數據重組；前期貨源集中是部署訊號、後期拆股+DI減持是出貨訊號——同一事實的意義隨週期位置反轉
- `CHAIN-H10-001` → OBS-H10-001: input_facts=急跌股需判別來源：莊家主動散貨 vs 被迫斬倉; 謎網2017-06-27：同系十多隻單日跌50-90% → temporal_order=系統斬倉在單日內完成；同系多股同日急跌=大股東系統被斬的指紋 → calculation_or_comparison=多股同日同步急跌的相關性↑=系統性斬倉；單股獨跌=需查莊家是否主動 → author_reasoning=莊家主動散貨的下跌其派貨區貼合理殼價，撈底者=派貨對象；被迫斬倉者莊家亦痛苦，復原動機真實 → author_conclusion=急跌博反彈只做被迫斬倉型；判別線索=同系多股同日急跌+大股東持股未減（1428確認法）
- `CHAIN-I1-003` → OBS-I1-003: input_facts=L型候選：半新股+天生乾身+集資低; 歷史案例低位≈2.5-2.8億、約4.4億才開始炒上 → temporal_order=上市→跌穿招股價→沉底6-12月→市值分區逐步部署→其後於4.4億區啟動 → calculation_or_comparison=市值越低推動所需資金越少；分段注碼令大注集中在低市值區改善風險回報 → author_reasoning=不猜最低點；以市值為部署尺度、條件不變為加注前提 → author_conclusion=分段市值注碼法：3億留意→2-3億細注→1-2億中注→1億以下大注（條件未破壞時）

## Observations (103)
| obs | method | source | type | generalization | statement |
|---|---|---|---|---|---|
| OBS-Z1-001 | CHAU_HIN | CHAUHIN-COURSE-L1 | METHOD_PRINCIPLE | REPEATABLE_METHOD | 壞消息失效訊號：連續壞消息殺傷力遞減+好消息反應放大=流動性支撐的線索；分析單位是『消息+價格反應+資金環境』三合一，非消息本身。 |
| OBS-Z1-002 | CHAU_HIN | CHAUHIN-COURSE-L1 | METHOD_PRINCIPLE | REPEATABLE_METHOD | 實體經濟與資產市場可長期背離：低息大量資金無實體出口→流入資產；分析次序=大勢→資金因素（貨幣供應/利率/流向）→港股外部關係（美元聯匯/美股+人民幣/中國貿易 |
| OBS-Z1-003 | CHAU_HIN | CHAUHIN-COURSE-L1 | RISK_WARNING | REPEATABLE_METHOD | 方法衰減律：任何炒股方法隨參與者學習而優勢遞減；規則有效性須按當前市場環境重估，不可假設永久。（對本平台：Hilton規則亦是環境依賴，須持續驗證。） |
| OBS-Z1-004 | CHAU_HIN | CHAUHIN-COURSE-L1 | RISK_WARNING | REPEATABLE_METHOD | 槓桿前置條件：技術未成熟（基本交易+風險控制能力）不應使用孖展；槓桿不是獨立技巧，放大判斷也放大錯誤。 |
| OBS-Z2-001 | CHAU_HIN | CHAUHIN-COURSE-L2A | METHOD_PRINCIPLE | REPEATABLE_METHOD | 雙質數供股法：質數比例供股令散戶產生碎股→碎股不便即時沽出→減少即時沽壓/貨源流出，屬中長期偏多財技因素。但一宗交易可有多個平行動機（集資/股權安排/碎股），不 |
| OBS-Z2-002 | CHAU_HIN | CHAUHIN-COURSE-L2A | METHOD_PRINCIPLE | REPEATABLE_METHOD | 門檻精確數字追問法：股權停在29.99%（而非30%）=交易設計線索，聯結GO責任；習慣是見貼門檻精確數字即主動追問「為甚麼停在這裡」，從公告與交易結構找原因。 |
| OBS-Z2-003 | CHAU_HIN | CHAUHIN-COURSE-L2A | TIMING_RULE | REPEATABLE_METHOD | 供股時間尺度分離：短期——供股公布後先處理持倉（不賭高開低開，高開不改寫風險規則）；中長期——碎股減流通等財技效果另行研究。理論除權價（舊股總值+新股按供股價÷ |
| OBS-Z2-004 | CHAU_HIN | CHAUHIN-COURSE-L2A | METHOD_PRINCIPLE | REPEATABLE_METHOD | 股權前後對照法：股權重組分析必須比較交易前後的主要股東/參與者/被攤薄者/新增者/最終百分比/門檻接近度；再把人物角色放回事件脈絡。全部用公開資料（公告/招股書 |
| OBS-H9-001 | HILTON | HILTON-CAIJI-2668CASE | METHOD_PRINCIPLE | REPEATABLE_METHOD | 六條股權界線判讀：5%（SDI申報線）/10%（主要股東，可申請清盤，舊主防範線）/20%（超一般授權=自行入局或特別安排，莊家意味）/30%（強制GO線；20 |
| OBS-H9-002 | HILTON | HILTON-CAIJI-2668CASE | FACT_FROM_CASE | POTENTIALLY_GENERALIZABLE | 2668入主序列：2013-05-31異動通告25.56%股權轉讓（詹培忠入主避GO線）；轉手當日非買點（價已升、未有財技確認）；06-04低位20%大折讓配股 |
| OBS-H9-003 | HILTON | HILTON-CAIJI-2668CASE | FACT_FROM_CASE | REPEATABLE_METHOD | 部署確認序列：股權集中報告（聯交所散戶警告）對財技派=莊家控制確認；報告內16人射倉組別名單可作陣營線索（羅輝成與詹培忠公開同行記錄）；ED任命=派自己人查帳的 |
| OBS-H9-004 | HILTON | HILTON-CAIJI-2668CASE | AUTHOR_INTERPRETATION | REPEATABLE_METHOD | 受阻推演法：主要交易被監管否決（2668出售37.53%業務被現金公司條例阻止）後，計算莊家合計持貨，推演『繼續』與『離場』兩路——續玩需炒高注資、離場需炒高散 |
| OBS-H9-005 | HILTON | HILTON-CAIJI-2668CASE | FACT_FROM_CASE | POTENTIALLY_GENERALIZABLE | 2668出貨序列：2014-03-14一拆五（吸引散戶）→07-03詹培忠DI 21.35%→7.22%（出貨開始）→07-29降至0.15%（跌穿5%申報線= |
| OBS-H9-006 | HILTON | HILTON-CAIJI-2668CASE | METHOD_PRINCIPLE | REPEATABLE_METHOD | 方法次序：財技分析先行（確認個案+買入基礎），TA僅作輔助（止蝕位/加分）；財技觸發離場時凌駕圖形。以操盤成本推算最低升幅只提供安全邊際，後續倍數應參考同類項目 |
| OBS-H9-007 | HILTON | HILTON-CAIJI-2668CASE | CONDITION | POTENTIALLY_GENERALIZABLE | 鬥長命股模式：傳承失效（接班人無能力無意欲）→長期停滯→死殼候選；判讀=兩次盈警+市值1-2億 vs 殼價比較；此類股可能長期無人問津，必須等待真正股權/財技異 |
| OBS-H10-001 | HILTON | HILTON-CAIJI-DIPBOUNCE | METHOD_PRINCIPLE | REPEATABLE_METHOD | 急跌兩大來源判別：(1)莊家主動散貨——錨定撈底陷阱，跌八九成但低位市值貼合理殼價正是其派貨區，不應撈 (2)被迫斬倉——非自願，目標尋找此類；大股東被斬令同系 |
| OBS-H10-002 | HILTON | HILTON-CAIJI-DIPBOUNCE | TIMING_RULE | REPEATABLE_METHOD | 急跌博反彈三必要條件+操作：(1)非莊家安排（目標=被迫斬倉）(2)跌幅：細價股≥70%起步、85%希望、>90%最好（85與90%的剩餘市值是倍數差）；大價股 |
| OBS-H10-003 | HILTON | HILTON-CAIJI-DIPBOUNCE | FACT_FROM_CASE | REPEATABLE_METHOD | 分拆沽壓補充證據：被動基金強制沽壓——指數成分股分拆的子公司不自動入指數，被動基金必沽（中信電子案例：沽壓後估值一度僅5-6倍PE）。2121介紹上市沽壓後約1 |
| OBS-H1-001 | HILTON | HILTON-CAIJI-L1 | METHOD_PRINCIPLE | REPEATABLE_METHOD | 財技股評估五因素有嚴格次序：1話事人(M) 2財技面收貨/出貨 3大股東成本(Cost) 4乾度 5股票有沒有客；必須先通過M、財技面、成本三關，乾度數字不可單 |
| OBS-H1-002 | HILTON | HILTON-CAIJI-L1 | METHOD_PRINCIPLE | REPEATABLE_METHOD | 供乾/供錢分辨法：除權後若大股東推高市價吸引散戶付款認購=供錢；若壓住股價貼近供股價橫行令散戶放棄認購、包銷的大股東接收貨源=供乾。除權令流通市值大降，操作成本 |
| OBS-H1-003 | HILTON | HILTON-CAIJI-L1 | TIMING_RULE | REPEATABLE_METHOD | 供股復仇記（順勢賺供錢盤的推升）三項必須條件齊備才可參與：(a)真正大比例大折讓 (b)除權後市價與供股價非常接近（數個百分點內）(c)M非反覆供股慣犯且歷史清 |
| OBS-H1-004 | HILTON | HILTON-CAIJI-L1 | FACT_FROM_CASE | POTENTIALLY_GENERALIZABLE | 0530高銀金融三連供乾案例（1供9@0.67→2供5@1.07→10供11@1.07，申請170/35/22份，第三次市價低於供股價形成假供股）：股本擴大73 |
| OBS-H1-005 | HILTON | HILTON-CAIJI-L1 | FACT_FROM_CASE | POTENTIALLY_GENERALIZABLE | 反覆供股可令公眾持股降至遠低於25%上市最低（8198：55%→22%），甚至名義公眾持股100%由安排人士組成（8212，P=100%），真正控制者可隱藏在5 |
| OBS-H1-006 | HILTON | HILTON-CAIJI-L1 | AUTHOR_INTERPRETATION | POTENTIALLY_GENERALIZABLE | 錨定散貨套路（AUTHOR_INTERPRETATION）：炒高至$10過程中大股東借款對敲尚未獲利；之後壓回$3，散戶以最高價作錨覺得『跌七成很便宜』接貨，大 |
| OBS-H1-007 | HILTON | HILTON-CAIJI-L1 | METHOD_PRINCIPLE | REPEATABLE_METHOD | 古怪供股比例（匯豐12供5、渣打91供30、工行10供0.45）刻意製造碎股，散戶持股不足倍數時碎股剩餘價值被合法榨取；大股東持股龐大影響較小。 |
| OBS-H1-008 | HILTON | HILTON-CAIJI-L1 | TIMING_RULE | REPEATABLE_METHOD | R報告（供股結果）解讀：申請份數≤30=參與冷清、散戶沒跟供（偏好）；份數多=散戶跟供。時間規則：供股項目給約半年觀察期不啟動即離場；配股項目一至兩個月。 |
| OBS-H1-009 | HILTON | HILTON-CAIJI-L1 | RISK_WARNING | REPEATABLE_METHOD | 宣布日逃生規則：大比例大折讓（或複雜結構如40合1+1供15+送紅股，0149案例）宣布翌日第一口價立即沽出，不等反彈。複雜結構應還原為大比例大折讓本質處理。 |
| OBS-H1-010 | HILTON | HILTON-CAIJI-L1 | CONDITION | REPEATABLE_METHOD | 乾度門檻有條件放寬：一般M以90%歸邊為足夠；神級M可接受七成多；且CCASS表面數字低估實際控制（貨源集中首10-20券商時）。高乾度同時意味急升急跌雙向風險 |
| OBS-H1-011 | HILTON | HILTON-CAIJI-L1 | METHOD_PRINCIPLE | REPEATABLE_METHOD | 供股目的二分（供乾=要貨不要錢 / 供錢=要錢不要貨），一堂課明言兩者不會同時存在；供股目的判斷先於一切通告細節閱讀。 |
| OBS-H1-012 | HILTON | HILTON-CAIJI-L1 | RISK_WARNING | REPEATABLE_METHOD | 反覆供股慣犯排除規則：同一股票每兩三年重複供錢（8212五次）=慣犯，永久排除參與；M歷史不清（剛上市/剛轉手）同樣排除。 |
| OBS-H2-001 | HILTON | HILTON-CAIJI-L2 | FACT_FROM_CASE | REPEATABLE_METHOD | 強制全購觸發規則（法規事實）：(1)持股由低位增至>30% (2)持有30%-50%且一年內再增持>2%。觸發後須申報並向全體股東提出全購。 |
| OBS-H2-002 | HILTON | HILTON-CAIJI-L2 | CONDITION | REPEATABLE_METHOD | 無條件GO（新主已買>50%）確定性高；有條件GO（<50%）可因總接受不足50%而取消——失敗風險須定價。 |
| OBS-H2-003 | HILTON | HILTON-CAIJI-L2 | METHOD_PRINCIPLE | REPEATABLE_METHOD | GO項目五階段風險回報分層：A殼股潛伏(低風險50-200%)、B洽談易手(中高10-30%成敗約半)、C正式易手至GO結束(極低風險GO價包底)、D GO結束 |
| OBS-H2-004 | HILTON | HILTON-CAIJI-L2 | METHOD_PRINCIPLE | REPEATABLE_METHOD | 合理賣殼價 = 殼價 + 扣水NAV。扣水規則：商譽/收購合併價值歸零、內地物業廠房歸零、香港物業及現金100%。NAV越低殼越乾淨；現市值 vs 合理賣殼價的 |
| OBS-H2-005 | HILTON | HILTON-CAIJI-L2 | TIMING_RULE | REPEATABLE_METHOD | 春江鴨偵測：無公告背景下股價低位連升兩三日+成交量放大數十倍→知情資金入場線索。追入點=異動第二日收市前（確認量大過第一日）；第三日可能已升20-30%。成本控 |
| OBS-H2-006 | HILTON | HILTON-CAIJI-L2 | TIMING_RULE | REPEATABLE_METHOD | GO價包底套利：正式易手至GO結束期間市價貼近GO價；低於GO價時套利力量推回。買入原則=貼近或低於GO價；強制離場=GO結束前兩日（包底消失後可立即大跌）。C |
| OBS-H2-007 | HILTON | HILTON-CAIJI-L2 | CONDITION | REPEATABLE_METHOD | D階段（GO後炒作）兩項條件：(1)新主是個人（會肉痛）而非實業大集團——首三年受VSA/RTO限制只能先炒股回本 (2)新主有爆炒往績（黎亮3倍/紀曉波100 |
| OBS-H2-008 | HILTON | HILTON-CAIJI-L2 | SEQUENCE | REPEATABLE_METHOD | E階段注資路徑：首三年VSA/RTO限制→透過財技（如大比例供股洗太平地）擴大股本市值→約1:1比例注資（注50億資產需約50億市值平台）。最早線索=改名通告（ |
| OBS-H2-009 | HILTON | HILTON-CAIJI-L2 | METHOD_PRINCIPLE | REPEATABLE_METHOD | GO+20/20配股組合（約20%折讓+20%極限比例）歷史勝率約八至九成，常見三至四個月內三至四倍；10/10配股不算完整組合、效果較弱；再配爆炒往績新主評分 |
| OBS-H2-010 | HILTON | HILTON-CAIJI-L2 | AUTHOR_INTERPRETATION | REPEATABLE_METHOD | 舊主留一手訊號：正常情況舊主應在殼價最值錢時清倉；保留股份=深入了解新主及後續計劃的加分訊號。強度分級：9.x%（不越10%主要股東門檻的最大保留）>4.x%。 |
| OBS-H2-011 | HILTON | HILTON-CAIJI-L2 | AUTHOR_INTERPRETATION | POTENTIALLY_GENERALIZABLE | R報告暗倉偵測法：市價長期高於GO價時，接受要約者必蝕價——理性散戶不會接受；因此R報告中異常高的接受比例（01236案例20%）推斷為舊主暗倉過倉，實際控制≈ |
| OBS-H2-012 | HILTON | HILTON-CAIJI-L2 | METHOD_PRINCIPLE | REPEATABLE_METHOD | GO的本質=Clean Transaction：新主須證明資金完成100%全購；散戶獲按GO價退出的選擇權——市價低於GO價時GO價=包底，高於時散戶可不接受。 |
| OBS-H3-001 | HILTON | HILTON-CAIJI-L3 | METHOD_PRINCIPLE | REPEATABLE_METHOD | Non-GO結構：新主以遠低於GO成本（數千萬 vs 數億）認購大量新股取得控制權，資金進入自己控制的公司；舊主無現金離場、被攤薄成小股東——約95%案例要求新 |
| OBS-H3-002 | HILTON | HILTON-CAIJI-L3 | CONDITION | REPEATABLE_METHOD | 清洗豁免邏輯：Non-GO新主0%→>30%本觸發強制GO，故通常申請Whitewash Waiver；聯交所批准理由=舊主同被攤薄留在公司。無財困公司以極折讓 |
| OBS-H3-003 | HILTON | HILTON-CAIJI-L3 | METHOD_PRINCIPLE | REPEATABLE_METHOD | Non-GO最低市值公式：合理殼價×舊主持股比例=舊主應得金額；再÷完成後舊主餘下比例=最低合理總市值。01250北控清潔能源：25億→最低90億（三至四倍空間 |
| OBS-H3-004 | HILTON | HILTON-CAIJI-L3 | RISK_WARNING | REPEATABLE_METHOD | 期殼排除規則：上市約兩年內即賣殼/Non-GO的公司可能是預先安排的殼——幕後金主已檯底持有、上市後直接套殼價差額，毋須炒高補償舊主；且舊殼也可場外找數（高價垃 |
| OBS-H3-005 | HILTON | HILTON-CAIJI-L3 | METHOD_PRINCIPLE | REPEATABLE_METHOD | 送紅股除淨窗口機制：除淨至生效日流通量僅剩一成（1送9）→舞高弄低成本降約九成；股份暫用29XX代碼，臨時代碼循環再用使派貨成交歷史難以追查；新股生效前被鎖定。 |
| OBS-H3-006 | HILTON | HILTON-CAIJI-L3 | CONDITION | REPEATABLE_METHOD | 拆股位置判斷：低位拆股=降低入場費為將來炒作鋪路（起步Signal）；高位拆股=擴大散戶買家池直接派貨。與送紅股差異=無鎖倉空窗。同一項目可低位高位各拆一次；S |
| OBS-H3-007 | HILTON | HILTON-CAIJI-L3 | METHOD_PRINCIPLE | REPEATABLE_METHOD | 配股制度與形式：一般授權=年內≤20%配發+≤19.99%折讓（20/20），可分次用盡；超限走特別授權。形式優劣：配新股（承配人承受20-30日鎖倉→支持與M |
| OBS-H3-008 | HILTON | HILTON-CAIJI-L3 | CONDITION | REPEATABLE_METHOD | 優質配股（收貨Signal）七利好：(1)低位橫行零成交（承配人只能是自己人）(2)大比例大折讓（用盡20/20低價收貨）(3)配新股（鎖倉承擔）(4)≥6名不 |
| OBS-H3-009 | HILTON | HILTON-CAIJI-L3 | RISK_WARNING | REPEATABLE_METHOD | 散貨配股（利淡）六訊號：(1)高位配股（升2-4倍後）(2)小比例小折讓（貼市易派散戶）(3)配舊股（大股東套現）(4)<6名須披露身份（承接者可能是水魚）(5 |
| OBS-H3-010 | HILTON | HILTON-CAIJI-L3 | TIMING_RULE | REPEATABLE_METHOD | 配股時間止蝕：成立項目半個月至一個月內啟動（速度遠快於供股半年期）；一個月不動即離場換馬，即使微升打和。買前先有價格止蝕位；找不到止蝕位不買或只用可全輸小注。市 |
| OBS-H3-011 | HILTON | HILTON-CAIJI-L3 | AUTHOR_INTERPRETATION | REPEATABLE_METHOD | 流動性反訊號（作者方法論）：低位難買=莊家同步收貨（正面）；持倉>2-3%會被莊家從券商倉位辨認，須拆倉三四間行。高位易沽（買盤充足）=真正散貨期已到；升數倍但 |
| OBS-H3-012 | HILTON | HILTON-CAIJI-L3 | FACT_FROM_CASE | REPEATABLE_METHOD | 貼門檻持股偵測：新主持股停在29.97%（貼30%下）=刻意避開強制GO、安排Non-GO路徑的披露線索。同理須監察貼5%、貼10%等門檻位的異常停駐。 |
| OBS-H3-013 | HILTON | HILTON-CAIJI-L3 | METHOD_PRINCIPLE | REPEATABLE_METHOD | Signal思維總綱：財技通告（送紅股/拆股/配股）本身無好淡，位置+M+市值+成交+貨源+形式+承配人關係七項合併判斷；未能判斷便不參與。妖股由操作位置決定（ |
| OBS-H4-001 | HILTON | HILTON-CAIJI-L4 | METHOD_PRINCIPLE | REPEATABLE_METHOD | 白武士重組三步：債務+股本重組→Non-GO印新股取得控制權→剝離舊業務+注資。CB路徑：注資以CB支付（未兌換不動股本、易過25%公眾持股關），條件成熟兌換後 |
| OBS-H4-002 | HILTON | HILTON-CAIJI-L4 | CONDITION | REPEATABLE_METHOD | 白武士好壞判準：重組後歸邊≥90%+商業炒作動機（非政府/社會穩定要求）=好；六七成歸邊=無炒作動機不參與。特殊結合：死殼歷史累積大量股東（客多）+重組後極乾， |
| OBS-H4-003 | HILTON | HILTON-CAIJI-L4 | RISK_WARNING | REPEATABLE_METHOD | 白武士操作：復牌市值回落至殼價+0-20%時用閒錢分散買入；無固定啟動時間（等細價股牛市）、不可設一般價格止蝕、不可追升。公開目標價不作準（0931主席稱$2- |
| OBS-H4-004 | HILTON | HILTON-CAIJI-L4 | FACT_FROM_CASE | POTENTIALLY_GENERALIZABLE | 0607豐盛控股完整白武士鏈：停牌→低價購舊主股份→削債3億+賣回舊業務→Open Offer Non-GO（新主承諾不供、季昌群包銷52%）→5億CB@0.0 |
| OBS-H4-005 | HILTON | HILTON-CAIJI-L4 | AUTHOR_INTERPRETATION | POTENTIALLY_GENERALIZABLE | 0931中國天然氣：成本≤一仙+九成歸邊+概念包裝（MOU）推至數百億市值、最高約300倍。沽空機構以實業估值狙擊失敗——財技股的估值錨是貨源與財技控制，不是業 |
| OBS-H4-006 | HILTON | HILTON-CAIJI-L4 | METHOD_PRINCIPLE | REPEATABLE_METHOD | 啤殼主篩選：集資額不合理地低。雙比較：(1)集資額≈1-2年盈利 (2)集資額≈上市費用（淨所得相對放棄25%股權不對稱）。正常實業老闆不會為小額資金承受上市監 |
| OBS-H4-007 | HILTON | HILTON-CAIJI-L4 | METHOD_PRINCIPLE | REPEATABLE_METHOD | 半新啤殼篩選七條件：集資額低（主板<1.5億/創板<8,000萬）、市值貼最低要求（5億/1.5億）、Top5或Top10券商持股>90%（初篩法有盲點）、CC |
| OBS-H4-008 | HILTON | HILTON-CAIJI-L4 | TIMING_RULE | REPEATABLE_METHOD | 啤殼時間軸：0-6月禁售；6-12月可減持至51%；12月後可賣殼。啟動壓力遞增：半年班底未套現壓力始、一年壓力大、1.5-2年最容易啟動、>2-3年班底問題、 |
| OBS-H4-009 | HILTON | HILTON-CAIJI-L4 | CONDITION | REPEATABLE_METHOD | 啤殼三走勢對策：(1)即爆型95%+歸邊不追（風險最大）(2)橫行型止蝕於區間低位、跌穿可轉向下收貨 (3)向下收貨型=跌穿招股價折磨散戶收貨，CCASS歸邊> |
| OBS-H4-010 | HILTON | HILTON-CAIJI-L4 | AUTHOR_INTERPRETATION | REPEATABLE_METHOD | 損失規避結構（Prospect Theory 2-2.5倍痛感）：盈利時風險規避早沽、虧損時風險愛好死守→高位形成蟹貨區。返家鄉效應：股價回蟹貨區散戶打和沽出； |
| OBS-H4-011 | HILTON | HILTON-CAIJI-L4 | FACT_FROM_CASE | REPEATABLE_METHOD | 立基模式（啤殼派貨）：上市首口價即自己人控制→數日內推高→一路壓低以錨定心理派貨（成本≈零，$10跌至$1派貨仍巨利）。製殼班底可辨認：同一細型保薦人一年九隻相 |
| OBS-H5-001 | HILTON | HILTON-CAIJI-L5 | TIMING_RULE | REPEATABLE_METHOD | 分拆上市首輪沽壓機制：原股東無償收貨即沽+基金主題不合沽售+子公司的持倉規模不足以支持另聘團隊→策略不是首日追入而是等沽壓完成（通常≤2-3個月）。買仔唔買乸為 |
| OBS-H5-002 | HILTON | HILTON-CAIJI-L5 | METHOD_PRINCIPLE | REPEATABLE_METHOD | 介紹形式分拆結構：無新股東新資金、母公司自行定價→定價偏高會跌回市場價且大股東半年禁售不能套現→介紹形式天然偏向低定價（上市走勢較好）。0864案例：母公司保留 |
| OBS-H5-003 | HILTON | HILTON-CAIJI-L5 | METHOD_PRINCIPLE | REPEATABLE_METHOD | 向下炒兩個必要條件（缺一不可）：(1)股價數年至十年長期向下、累跌>90%且反覆再跌 (2)下跌過程中不斷印發大量極低價股票（配股/供股/CB）。排除向下炒股的 |
| OBS-H5-004 | HILTON | HILTON-CAIJI-L5 | METHOD_PRINCIPLE | REPEATABLE_METHOD | 向下炒四方結構：上市公司/大股東→認購人（$0.90配20股付$18）→資產賣方收$18。同伙時股價帳面只是內部轉移；真實盈利=出售價−項目真實成本（高價買入估 |
| OBS-H5-005 | HILTON | HILTON-CAIJI-L5 | AUTHOR_INTERPRETATION | POTENTIALLY_GENERALIZABLE | 向下炒兩路：(1)有集資=印平股派散戶賺集資額 (2)無集資=公司現有資金經高價資產交易轉出。與向上炒比較：向上炒上限無明顯（10億+）但難度最高、股災可全輸； |
| OBS-H5-006 | HILTON | HILTON-CAIJI-L5 | METHOD_PRINCIPLE | REPEATABLE_METHOD | 成交量=分歧度量（非買賣力量對比）：突破+大成交=正面（沽盤被承接）；升後大成交回歸=反轉首訊號；下跌途中極端大成交=反對再跌的資金進場（短線見底候選）。位置條 |
| OBS-H5-007 | HILTON | HILTON-CAIJI-L5 | CONDITION | REPEATABLE_METHOD | 1-2-3轉勢確認（僅適用成交充足大趨勢，不適用細價財技股）：(1)突破下降阻力線 (2)形成Higher Low (3)突破前高成Higher High=正式 |
| OBS-H5-008 | HILTON | HILTON-CAIJI-L5 | METHOD_PRINCIPLE | REPEATABLE_METHOD | 個案研究SOP（2668方法）：分析十倍升浪之前的佈局（追溯至故事完整）；產出三件套=(1)時間表（通告/財技/新聞/資產交易≥10-20項）(2)人物股權表（ |
| OBS-H5-009 | HILTON | HILTON-CAIJI-L5 | METHOD_PRINCIPLE | REPEATABLE_METHOD | 小成交≠出貨：大股東數億至數十億持貨的派發必須有足夠成交量承接；極低成交中的下跌不代表派貨完成。反過來（第三堂）高位買盤充足才是散貨環境。 |
| OBS-H6-001 | HILTON | HILTON-CAIJI-L6 | CONDITION | REPEATABLE_METHOD | 戰役柱判讀：大成交柱=多空激烈交戰位；其後價格站穩柱上方=買方勝（向上操作）、跌穿柱下方=賣方勝（向下操作）；或在柱底買入+2-3%止蝕。大市未完成1-2-3轉 |
| OBS-H6-002 | HILTON | HILTON-CAIJI-L6 | METHOD_PRINCIPLE | REPEATABLE_METHOD | 交易紀錄量化法：每筆記錄買入原因/金額/預期/沽出理由；按原因分類統計成功率；每因素累積7-10案例後建立因素分數與數據。訓練約半年後完整分析可由數小時濃縮至1 |
| OBS-H6-003 | HILTON | HILTON-CAIJI-L6 | METHOD_PRINCIPLE | REPEATABLE_METHOD | 炒股食物鏈四層：散戶（靈活/資訊DE級）→莊家/MM（承接項目、控制盤面造勢、向大股東取得一般授權約20%貨、單項目約兩年賺數千萬至兩三億、致命風險=被大股東反 |
| OBS-H6-004 | HILTON | HILTON-CAIJI-L6 | METHOD_PRINCIPLE | REPEATABLE_METHOD | 莊家派系名單法：每出現新十倍股→查找大股東/人物關係/過往個案→記錄至派系名單；辨認線索=收購、重組、改名、跨公司重複人物；名單隨案例累積，同一批人物多次出現即 |
| OBS-H6-005 | HILTON | HILTON-CAIJI-L6 | RISK_WARNING | REPEATABLE_METHOD | 資訊驗證原則：免費資訊先當可能陷阱；形容詞（乾/靚/有勢）不可用——必須還原為持股比例/通告/配股/收購等實際數字按財技流程重檢。界定量表差異範例：文章稱70% |
| OBS-H6-006 | HILTON | HILTON-CAIJI-L6 | AUTHOR_INTERPRETATION | INSUFFICIENT_EVIDENCE | 市場勝率結構（課堂估計）：約5%賺/10%打和/85%輸；完成課程後賺錢者約兩成但不輸錢可成多數（避開不適合的操作）。勝負=相對排名（領先約九成人），非絕對知識 |
| OBS-H7-001 | HILTON | HILTON-CAIJI-L7 | METHOD_PRINCIPLE | REPEATABLE_METHOD | 合股六原因前三：(1)減流通量——『一合即乾』僅數日盤面效應，實際收貨約2-3%（遠低於一般授權20%）非主要用途 (2)製造碎股——碎股難沽價差被迫長留，供股 |
| OBS-H7-002 | HILTON | HILTON-CAIJI-L7 | CONDITION | REPEATABLE_METHOD | 合股六原因後三：(4)增加向下空間——最低報價一仙，合股重製下跌空間（100合1：一仙→一元再跌90%+）；接近一仙宣布合股=向下路線結構性訊號，極差評級應離場 |
| OBS-H7-003 | HILTON | HILTON-CAIJI-L7 | METHOD_PRINCIPLE | REPEATABLE_METHOD | 削股會計本質：以減股本抵銷累計虧損，恢復派息能力（派息取決於累計盈利非現金）；不創造/毀滅現金。獨立削股=轉盈訊號（其後常有特別股息）；488麗新發展：中標酒店 |
| OBS-H7-004 | HILTON | HILTON-CAIJI-L7 | METHOD_PRINCIPLE | REPEATABLE_METHOD | 混合資本重組三路線：A只合股（向下空間×10，但面值升限制折讓）→B+削股（面值削回，折讓×10，威力×100；941：合股→削股→更改買賣單位→1供4折讓74 |
| OBS-H7-005 | HILTON | HILTON-CAIJI-L7 | FACT_FROM_CASE | POTENTIALLY_GENERALIZABLE | 616向下炒紀錄級案例：2003-2014經歷九次合股+一次送股+十四次供股，沙士低位六千多萬→約一元；損失=反覆-90%的複利。大老闆不會用相同手法破壞核心旗 |
| OBS-H7-006 | HILTON | HILTON-CAIJI-L7 | METHOD_PRINCIPLE | REPEATABLE_METHOD | CCASS主動歸邊計算法（雙法）：(1)非CCASS流通量——總股本−CCASS=實體股，先全數視為M貨（散戶實體股日後存回CCASS會現異動） (2)券商持股 |
| OBS-H7-007 | HILTON | HILTON-CAIJI-L7 | AUTHOR_INTERPRETATION | POTENTIALLY_GENERALIZABLE | CCASS券商類型輔助：Top5/10法有盲點（同一莊家可分散六七間行）；外資大行（高盛/摩根）偏M或大戶持倉、零售行（匯豐/一通/渣打）偏街貨——僅輔助線索， |
| OBS-H7-008 | HILTON | HILTON-CAIJI-L7 | AUTHOR_INTERPRETATION | POTENTIALLY_GENERALIZABLE | 派貨價位設計：散戶心理舒適區=幾元股（毫子股顯危險、幾百元顯貴）→莊家目標升十倍時布局買入區常設幾毫子。每手入場費亦是篩選工具：低入場費吸弱手（內銀長年橫行）、 |
| OBS-H8-001 | HILTON | HILTON-CAIJI-L8 | METHOD_PRINCIPLE | REPEATABLE_METHOD | CCASS In判讀：實物股票存入=股份取得市場沽售條件的高指向性訊號；位置決定路徑（高位存入→偏派貨；低位存入→可能先炒高再派貨，兩者終點同為沽售）；比例門檻 |
| OBS-H8-002 | HILTON | HILTON-CAIJI-L8 | METHOD_PRINCIPLE | REPEATABLE_METHOD | 收貨格/出貨格定義及局限：主要行 vs 分散倉的持倉走向判圖；清晰圖形僅少部分個案出現（1106屬十中無一的清晰案例）——看不到圖形≠無派貨。「乾」（交投疏落排 |
| OBS-H8-003 | HILTON | HILTON-CAIJI-L8 | RISK_WARNING | REPEATABLE_METHOD | DI三大盲點：(1)>100%持股=衍生工具（期權/CB）按股份數量申報的假象 (2)配偶/受控公司/實益擁有人同一批股份重複申報——百分比不可直接相加 (3) |
| OBS-H8-004 | HILTON | HILTON-CAIJI-L8 | METHOD_PRINCIPLE | REPEATABLE_METHOD | 七大出貨信號（程度+次數+組合判讀）：(1)散貨財技（合股/拆股/送紅股）——一次留意、兩次通常足夠離場，不等第三次 (2)DI大股東減持程度——首次減持提高警 |
| OBS-H8-005 | HILTON | HILTON-CAIJI-L8 | AUTHOR_INTERPRETATION | REPEATABLE_METHOD | 震倉目的=提高散戶平均持貨成本（非收平貨——貨源已歸邊時無平貨可收）；高成本持貨者損失規避被鎖死→派貨少競爭。幅度界線：正常≈30%、強烈≈50%、>70%=盤 |
| OBS-H8-006 | HILTON | HILTON-CAIJI-L8 | CONDITION | REPEATABLE_METHOD | 天花板規則：市值天花板=主板約100億/創業板約20億（再升性價比降而下跌空間大）；升幅警戒=3-4倍（莊家近零成本）。估算升幅四因素：莊家胃口/賣殼vs炒股/ |
| OBS-H8-007 | HILTON | HILTON-CAIJI-L8 | RISK_WARNING | REPEATABLE_METHOD | 假異動排除規則：供股除權/新股出爐/股本變動造成的持倉%突變=機制性假異動，不作收貨/出貨解讀。CCASS T+3延遲→最近三日變化不可即見，急跌一兩日內的場景 |
| OBS-H8-008 | HILTON | HILTON-CAIJI-L8 | TIMING_RULE | REPEATABLE_METHOD | 持倉紀律：無出貨信號時坐貨（避免小升即走）；升一倍收回本金；三倍必達零成本；天花板區用推高保護位（每日保護位=當日最低，跌穿前一日低位即離場）。下跌時按紀律止蝕 |
| OBS-I1-001 | IVAN_L | IVANL-LXING-COURSE | CONDITION | REPEATABLE_METHOD | L型絕地選股前置：半新股優先（歷史短/貨源可追溯，只需招股文件+招股結果兩份文件起步）；『天生乾身』=IPO公開發售有限+大部分貨在相關人手上→免長時間收貨；集 |
| OBS-I1-002 | IVAN_L | IVANL-LXING-COURSE | METHOD_PRINCIPLE | REPEATABLE_METHOD | 絕地定義：非跌得多=絕地，而是上市後快速跌穿招股價→長期沉底半年至一年→散戶在無希望中逐步離場；L型只是外觀，必須有內在條件（背景/市值/貨源/時間），存在變種 |
| OBS-I1-003 | IVAN_L | IVANL-LXING-COURSE | CONDITION | REPEATABLE_METHOD | 市值分段注碼（主板經驗區間）：>3億觀望；3億以下開始留意；2-3億細注；1-2億中注；1億以下大注。注碼按個人本金設計分級；前提=原篩選條件未破壞——條件改變 |
| OBS-I1-004 | IVAN_L | IVANL-LXING-COURSE | RISK_WARNING | REPEATABLE_METHOD | 向下炒風險排除邏輯：剛上市已完成集資→短期再向下財技合理性低；貨源高度集中→向下出貨需承接；極低市值→向下空間受限。風險非零——須主動檢查『向下條件』是否存在（ |
| OBS-I1-005 | IVAN_L | IVANL-LXING-COURSE | TIMING_RULE | REPEATABLE_METHOD | 炒高後分級警覺（主板）：≈3億=第一重要區域；5-6億=驗證推動力；7-8億=重點轉向街貨/散貨監察；≈20億=超高區需多條件齊備。市值階段不同，風險假設不同— |
| OBS-I1-006 | IVAN_L | IVANL-LXING-COURSE | CONDITION | REPEATABLE_METHOD | 超額認購非單一判準：無超購可以、幾百倍超購=大量散戶參與嫌疑（街外貨結構複雜化）；須看認購者結構而非表面倍數。 |
