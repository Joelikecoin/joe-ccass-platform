"""DOCTOR_CASE_DERIVED_KNOWLEDGE_INGESTION_V1 — source-unit ingestion seeds.

Batch 1: Hilton 財技班 course summaries (methodology HILTON).
Each SOURCE block preserves: observations (fact vs author-interpretation
separated), evidence chains with intermediate steps, and CASE_DERIVED rule
candidates that stop at CASE_DERIVED with mandatory falsification conditions.

Idempotent; writes ONLY the dev ingestion store app/data/doctor/.
Run: python -m scripts.zc_ingest_case_knowledge_v1
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.doctor.ingestion import (
    ContradictionRecord, DedupClassification, EvidenceChain, GeneralizationClass,
    IngestionCheckpoint, IngestionStore, Observation, ObservationType, RuleCandidate,
    SourceUnit,
)
from app.doctor.models import RuleFamily

HILTON_DIR = "細價股-財技軍火庫/財技班-Hilton/知識提煉-財技班"
CASE_DIR = "AI學習內容/股票案例"


def source(sid: str, title: str, scope: str, date=None, mtype="course_summary", mid="HILTON", loc=HILTON_DIR):
    return SourceUnit(
        source_id=sid, source_title=title, source_type=mtype, methodology_id=mid,
        source_location=loc, source_date_if_known=date, source_scope=scope,
        ingestion_status="PROCESSING",
    )


# ============================================================ HILTON lesson 1
S_H1 = source(
    "HILTON-CAIJI-L1", "財技班第一堂_課程摘要", "五大因素框架(M/財技面/Cost/乾度/有客)；供股全流程(SOP/供乾供錢/供股復仇記)；錨定效應散貨",
    date="課程日期未知(摘要提2018-07-03規則)",
)

OBS_H1 = [
    Observation(
        observation_id="OBS-H1-001", methodology_id="HILTON", source_id=S_H1.source_id,
        source_section="核心觀念", source_quote_or_paraphrase_reference="財技股選擇必須比較五大因素…有先後次序…乾度只排第四",
        observation_statement="財技股評估五因素有嚴格次序：1話事人(M) 2財技面收貨/出貨 3大股東成本(Cost) 4乾度 5股票有沒有客；必須先通過M、財技面、成本三關，乾度數字不可單獨作參與理由。",
        observation_type=ObservationType.METHOD_PRINCIPLE,
        supporting_evidence="課程以新手常犯錯誤（只看乾度）作反面教材，明言五項有先後次序",
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
    ),
    Observation(
        observation_id="OBS-H1-002", methodology_id="HILTON", source_id=S_H1.source_id,
        source_section="操作流程 6", source_quote_or_paraphrase_reference="除權後…向上炒：供錢…壓住供股價橫行：供乾",
        observation_statement="供乾/供錢分辨法：除權後若大股東推高市價吸引散戶付款認購=供錢；若壓住股價貼近供股價橫行令散戶放棄認購、包銷的大股東接收貨源=供乾。除權令流通市值大降，操作成本同步下降。",
        observation_type=ObservationType.METHOD_PRINCIPLE,
        supporting_evidence="除權後流通市值大跌(例一億→一千八百萬)令畫圖成本下降的機制說明",
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
    ),
    Observation(
        observation_id="OBS-H1-003", methodology_id="HILTON", source_id=S_H1.source_id,
        source_section="操作流程 7", source_quote_or_paraphrase_reference="供股復仇記必須條件…離場必須在Last Pay Day前一至兩日",
        observation_statement="供股復仇記（順勢賺供錢盤的推升）三項必須條件齊備才可參與：(a)真正大比例大折讓 (b)除權後市價與供股價非常接近（數個百分點內）(c)M非反覆供股慣犯且歷史清楚。止蝕=供股價微下方；離場=Last Pay Day前一至兩日。",
        observation_type=ObservationType.TIMING_RULE,
        supporting_evidence="買入價遠高於供股價時大股東毋須炒高即可完成供錢→無利可圖的機制推理",
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
    ),
    Observation(
        observation_id="OBS-H1-004", methodology_id="HILTON", source_id=S_H1.source_id,
        source_section="重要案例 0530", source_quote_or_paraphrase_reference="0530高銀金融三次供股…170份→35份→22份…股本擴大73倍…等三年至2015大時代",
        observation_statement="0530高銀金融三連供乾案例（1供9@0.67→2供5@1.07→10供11@1.07，申請170/35/22份，第三次市價低於供股價形成假供股）：股本擴大73倍、大股東投入近百億後，項目等待約三年至大市極佳才啟動，由起步位升至約$30。巨型項目會等待大市極佳才開車。",
        observation_type=ObservationType.FACT_FROM_CASE,
        supporting_evidence="三次供股的比例/價格/申請份數/公眾持股數字及最終升幅均在案例中列出",
        generalization_class=GeneralizationClass.POTENTIALLY_GENERALIZABLE,
    ),
    Observation(
        observation_id="OBS-H1-005", methodology_id="HILTON", source_id=S_H1.source_id,
        source_section="重要案例 8212/8198", source_quote_or_paraphrase_reference="公眾持股P達100%…真正控制者可隱藏於低於5%披露門檻；8198公眾持股55%→22%低於25%上市最低",
        observation_statement="反覆供股可令公眾持股降至遠低於25%上市最低（8198：55%→22%），甚至名義公眾持股100%由安排人士組成（8212，P=100%），真正控制者可隱藏在5%申報線之下。表面披露持股嚴重低估實際控制度。",
        observation_type=ObservationType.FACT_FROM_CASE,
        supporting_evidence="8212(2010/2012/2014/2015/2017五次供股)及8198(2012)的公眾持股數字",
        generalization_class=GeneralizationClass.POTENTIALLY_GENERALIZABLE,
    ),
    Observation(
        observation_id="OBS-H1-006", methodology_id="HILTON", source_id=S_H1.source_id,
        source_section="重要案例 錨定效應", source_quote_or_paraphrase_reference="由$10壓回$9…$3，散戶以$10作錨覺得便宜而接貨，大股東才在下跌途中真正散貨",
        observation_statement="錨定散貨套路（AUTHOR_INTERPRETATION）：炒高至$10過程中大股東借款對敲尚未獲利；之後壓回$3，散戶以最高價作錨覺得『跌七成很便宜』接貨，大股東在下跌途中才真正散貨。見十倍股不應只看升幅，要看推高過程的資金壓力。",
        observation_type=ObservationType.AUTHOR_INTERPRETATION,
        supporting_evidence="作者對散戶錨定心理與大股東獲利路徑的推理（非直接數據證明）",
        generalization_class=GeneralizationClass.POTENTIALLY_GENERALIZABLE,
    ),
    Observation(
        observation_id="OBS-H1-007", methodology_id="HILTON", source_id=S_H1.source_id,
        source_section="重要案例 匯豐渣打工行", source_quote_or_paraphrase_reference="質數供股或古怪比例會刻意製造碎股…剩餘價值被合法榨取",
        observation_statement="古怪供股比例（匯豐12供5、渣打91供30、工行10供0.45）刻意製造碎股，散戶持股不足倍數時碎股剩餘價值被合法榨取；大股東持股龐大影響較小。",
        observation_type=ObservationType.METHOD_PRINCIPLE,
        supporting_evidence="三大行供股比例案例",
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
    ),
    Observation(
        observation_id="OBS-H1-008", methodology_id="HILTON", source_id=S_H1.source_id,
        source_section="操作流程 8 / 注意事項", source_quote_or_paraphrase_reference="R報告主要看申請份數，偏好30份以下…供股後橫行超過半年仍不炒會離場",
        observation_statement="R報告（供股結果）解讀：申請份數≤30=參與冷清、散戶沒跟供（偏好）；份數多=散戶跟供。時間規則：供股項目給約半年觀察期不啟動即離場；配股項目一至兩個月。",
        observation_type=ObservationType.TIMING_RULE,
        supporting_evidence="0926碧生源23份/0122鱷魚恤76份/1626 16份對照",
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
    ),
    Observation(
        observation_id="OBS-H1-009", methodology_id="HILTON", source_id=S_H1.source_id,
        source_section="操作流程 4 / 注意事項", source_quote_or_paraphrase_reference="大比例大折讓…供又死唔供又死…最佳逃生策略是第二日第一口價立即沽出",
        observation_statement="宣布日逃生規則：大比例大折讓（或複雜結構如40合1+1供15+送紅股，0149案例）宣布翌日第一口價立即沽出，不等反彈。複雜結構應還原為大比例大折讓本質處理。",
        observation_type=ObservationType.RISK_WARNING,
        supporting_evidence="0149中國農產品案例；翌日裂口低開大陰燭的常規走勢",
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
    ),
    Observation(
        observation_id="OBS-H1-010", methodology_id="HILTON", source_id=S_H1.source_id,
        source_section="核心觀念 乾度", source_quote_or_paraphrase_reference="90%門檻主要用於不知名的M。若M是曾炒百倍股的神級人物…七成多也可接受…部分貨源可能集中在首十至二十間券商",
        observation_statement="乾度門檻有條件放寬：一般M以90%歸邊為足夠；神級M可接受七成多；且CCASS表面數字低估實際控制（貨源集中首10-20券商時）。高乾度同時意味急升急跌雙向風險。",
        observation_type=ObservationType.CONDITION,
        supporting_evidence="92%與96%不需過度區分；CCASS歸邊計算的結構性局限說明",
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
    ),
    Observation(
        observation_id="OBS-H1-011", methodology_id="HILTON", source_id=S_H1.source_id,
        source_section="操作流程 1", source_quote_or_paraphrase_reference="供乾：要貨不要錢；供錢：要錢不要貨…兩者目的只會有一個",
        observation_statement="供股目的二分（供乾=要貨不要錢 / 供錢=要錢不要貨），一堂課明言兩者不會同時存在；供股目的判斷先於一切通告細節閱讀。",
        observation_type=ObservationType.METHOD_PRINCIPLE,
        supporting_evidence="課程SOP次序：先確定目的→再讀七項基本資料",
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
    ),
    Observation(
        observation_id="OBS-H1-012", methodology_id="HILTON", source_id=S_H1.source_id,
        source_section="重要案例 8212", source_quote_or_paraphrase_reference="每兩三年重複供股…2010、2012、2014、2015、2017…反覆供錢的慣犯不應參與",
        observation_statement="反覆供股慣犯排除規則：同一股票每兩三年重複供錢（8212五次）=慣犯，永久排除參與；M歷史不清（剛上市/剛轉手）同樣排除。",
        observation_type=ObservationType.RISK_WARNING,
        supporting_evidence="8212 供股年份序列",
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
    ),
]

CHAIN_H1_004 = EvidenceChain(
    chain_id="CHAIN-H1-004", observation_id="OBS-H1-004",
    input_facts=["0530第一次1供9@$0.67，170份申請（7%為安排人士）",
                 "第二次2供5@$1.07（市價$1.7），35份，公眾持股約24%",
                 "第三次10供11@$1.07（市價$1.05，市價<供股價=假供股），22份"],
    temporal_order="三次供股序列→等約三年→2015大市極佳才啟動",
    calculation_or_comparison="三次後股本擴大73倍；大股東明面69%+安排7%≈控制76%；投入近100億",
    author_reasoning="巨額資金鎖死需要極佳市況才能獲利離場；市值由百億級放大至約3000億",
    author_conclusion="規模巨大的供乾項目會等待大市極佳才啟動，需要超長耐心",
)

CAND_H1 = [
    RuleCandidate(
        rule_candidate_id="CAND-HILTON-SUPPLY-INTENT-001", rule_family=RuleFamily.RIGHTS_ISSUE,
        methodology_id="HILTON", rule_name="除權後市價 vs 供股價 = 供乾/供錢分辨器",
        description="供股除權後：大股東推高市價吸引散戶付款=供錢；壓住股價貼近供股價橫行令散戶放棄=供乾（包銷大股東收貨）。判斷先於一切其他通告分析。",
        preconditions=["已完成供股除權", "流通市值已大幅下降"],
        required_inputs=["除權後市價序列", "供股價", "包銷商身份"],
        optional_inputs=["R報告申請份數"],
        trigger_conditions=["除權後市價走向：向上推 vs 貼供股價橫行"],
        supporting_evidence=["OBS-H1-002", "OBS-H1-011"],
        output_semantics="供股目的分類：SUPPLY_FOR_CASH / SUPPLY_FOR_DRY",
        false_positive_conditions=["大市系統性下跌被誤讀為壓價收貨"],
        false_negative_conditions=["先橫行後突然推升的混合路徑"],
        falsification_conditions=["除權後走勢與目的分類系統性不符（如供乾案例大股東認購結果低於包銷上限）"],
        origin_case_ids=["CASE-HILTON-0530", "CASE-HILTON-0926", "CASE-HILTON-0122", "CASE-HILTON-1626"],
        origin_source_ids=[S_H1.source_id], origin_observation_ids=["OBS-H1-002", "OBS-H1-011"],
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
        dedup_classification=DedupClassification.NEW_RULE,
    ),
    RuleCandidate(
        rule_candidate_id="CAND-HILTON-REVENGE-TIMING-001", rule_family=RuleFamily.RIGHTS_ISSUE,
        methodology_id="HILTON", rule_name="供股復仇記三條件+時間窗",
        description="順勢賺供錢盤：須同時滿足(1)真正大比例大折讓(2)除權後市價貼近供股價（數個百分點）(3)M非反覆供股慣犯且歷史清楚。止蝕供股價微下方；Last Pay Day前一至兩日必須離場。",
        preconditions=["供股宣布", "已判斷屬供錢盤"],
        required_inputs=["供股比例與折讓", "除權後市價", "供股價", "M歷史", "Last Pay Day日期"],
        optional_inputs=["R報告申請份數"],
        trigger_conditions=["三必須條件同時成立"],
        supporting_evidence=["OBS-H1-003", "OBS-H1-009"],
        output_semantics="參與/不參與決策 + 止蝕位 + 強制離場日",
        false_positive_conditions=["市價看似貼近供股價但M是慣犯", "複雜結構未還原為大比例大折讓本質"],
        false_negative_conditions=["符合條件但大股東選擇橫行完成供錢（無升幅）"],
        falsification_conditions=["Last Pay Day前離場規則系統性劣於持有至新股日（回測）", "三條件外的案例大量成功"],
        origin_case_ids=["CASE-HILTON-0149"],
        origin_source_ids=[S_H1.source_id], origin_observation_ids=["OBS-H1-003"],
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
        dedup_classification=DedupClassification.NEW_RULE,
    ),
    RuleCandidate(
        rule_candidate_id="CAND-HILTON-DRYNESS-90-001", rule_family=RuleFamily.CCASS_CONCENTRATION,
        methodology_id="HILTON", rule_name="乾度90%門檻+M質素補足+券商集中低估",
        description="一般M以90%歸邊為足夠（92%與96%不區分）；神級M可放寬至七成多；CCASS表面歸邊低估實際控制（貨源集中首10-20券商）。乾度只排五因素第四，不可單獨觸發參與。",
        preconditions=["已有CCASS歸邊計算"],
        required_inputs=["歸邊百分比", "M身份與往績"],
        optional_inputs=["首N券商集中度", "券商行數"],
        trigger_conditions=["歸邊≥90%（一般M）或≥70%+神級M"],
        supporting_evidence=["OBS-H1-010", "OBS-H1-001"],
        output_semantics="乾度評級：PASS / PASS_WITH_ELITE_M / FAIL；永遠附M關卡未過=不參與",
        false_positive_conditions=["歸邊高但財技面正散貨（三關未過）"],
        false_negative_conditions=["實際控制>表面數字（券商集中）被誤判FAIL"],
        falsification_conditions=["90%門檻案例群與70-90%案例群的事後升幅無統計差異（在M質素分層後）"],
        origin_case_ids=["CASE-HILTON-8198", "CASE-HILTON-0926", "CASE-HILTON-0122"],
        origin_source_ids=[S_H1.source_id], origin_observation_ids=["OBS-H1-010", "OBS-H1-001"],
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
        dedup_classification=DedupClassification.NEW_RULE,
    ),
    RuleCandidate(
        rule_candidate_id="CAND-HILTON-RREPORT-COUNT-001", rule_family=RuleFamily.RIGHTS_ISSUE,
        methodology_id="HILTON", rule_name="R報告申請份數≤30=散戶冷清",
        description="供股結果(R報告)申請份數是散戶參與度代理：≤30份偏好（散戶沒跟供）；配合供乾判讀。觀察期規則：供股項目半年、配股項目一至兩個月不啟動即離場。",
        preconditions=["供股結果公布"],
        required_inputs=["申請份數"],
        optional_inputs=["促使安排人士佔比", "公眾持股變化"],
        trigger_conditions=["申請份數≤30"],
        supporting_evidence=["OBS-H1-008", "OBS-H1-004"],
        output_semantics="散戶參與度分類 + 項目觀察時限",
        false_positive_conditions=["大額集資項目份數天然偏少"],
        false_negative_conditions=["份數多但每份極小"],
        falsification_conditions=["份數≤30與>30的後續表現無差異"],
        origin_case_ids=["CASE-HILTON-0926", "CASE-HILTON-0122", "CASE-HILTON-1626", "CASE-HILTON-0530"],
        origin_source_ids=[S_H1.source_id], origin_observation_ids=["OBS-H1-008"],
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
        dedup_classification=DedupClassification.NEW_RULE,
    ),
    RuleCandidate(
        rule_candidate_id="CAND-HILTON-ANCHOR-DUMP-001", rule_family=RuleFamily.CCASS_DISTRIBUTION,
        methodology_id="HILTON", rule_name="錨定散貨：炒高未獲利→壓回途中真散貨",
        description="（AUTHOR_INTERPRETATION級）十倍升幅過程以借款對敲維持，推高者尚未獲利；其後由高位壓回，散戶以最高價為錨覺得便宜接貨，大股東在下跌途中完成真正散貨。",
        preconditions=["股價曾大幅炒高後回落"],
        required_inputs=["高位與現價距離", "成交分佈"],
        optional_inputs=["CCASS券商變化（下跌途中）"],
        trigger_conditions=["高位回落後散戶承接增加而大戶貨源下降"],
        supporting_evidence=["OBS-H1-006"],
        contradicting_evidence=["尚未有本站CCASS下跌途中券商變化的獨立驗證"],
        alternative_explanations=["單純獲利回吐", "莊家資金鏈斷裂被迫沽售"],
        output_semantics="散貨階段標記（DISTRIBUTION_VIA_ANCHORING），屬作者解讀非平台事實",
        false_positive_conditions=["跌勢由基本面惡化驅動"],
        false_negative_conditions=["大股東在上升途中已完成派貨"],
        falsification_conditions=["下跌途中CCASS大戶持股不降反升的案例比例過高"],
        origin_case_ids=[],
        origin_source_ids=[S_H1.source_id], origin_observation_ids=["OBS-H1-006"],
        generalization_class=GeneralizationClass.POTENTIALLY_GENERALIZABLE,
        dedup_classification=DedupClassification.NEW_RULE,
    ),
    RuleCandidate(
        rule_candidate_id="CAND-HILTON-REPEAT-DILUTE-001", rule_family=RuleFamily.CAPITAL_STRUCTURE,
        methodology_id="HILTON", rule_name="反覆供股慣犯排除+低於5%隱藏控制偵測",
        description="每兩三年重複供錢的股票（8212五次）列為慣犯永久排除；反覆供股可令公眾持股遠低於25%甚至名義100%（安排人士），真正控制者隱藏在5%申報線下——披露持股嚴重低估控制度。",
        preconditions=["有歷史供股序列", "有公眾持股/CCASS數據"],
        required_inputs=["歷史供股日期序列", "公眾持股比例"],
        optional_inputs=["5%申報線 filer 名單"],
        trigger_conditions=["供股間隔≤3年重複發生", "公眾持股<25%或名義100%"],
        supporting_evidence=["OBS-H1-012", "OBS-H1-005"],
        output_semantics="標記 REPEAT_DILUTION_OFFENDER 與 HIDDEN_CONTROL_SUSPECT",
        false_positive_conditions=["白武士拯救式多次供股（財困特批路徑）"],
        false_negative_conditions=["慣犯改用配股/CB等其他攤薄工具"],
        falsification_conditions=["反覆供股但公眾持股維持>25%且隨後出現正向回報的案例群"],
        origin_case_ids=["CASE-HILTON-8212", "CASE-HILTON-8198"],
        origin_source_ids=[S_H1.source_id], origin_observation_ids=["OBS-H1-012", "OBS-H1-005"],
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
        dedup_classification=DedupClassification.NEW_RULE,
    ),
]


def ingest(store: IngestionStore) -> None:
    for s in [S_H1]:
        store.register_source(s)
    for o in OBS_H1:
        store.add_observation(o)
    store.add_observation(OBS_H1[3], CHAIN_H1_004)
    for c in CAND_H1:
        store.add_candidate(c)
    store.mark_source_status(S_H1.source_id, "INGESTED")
    store.save_checkpoint(IngestionCheckpoint(
        source_id=S_H1.source_id,
        processed_sections=["核心觀念", "老師重點", "操作流程", "重要案例", "注意事項", "本課總結"],
        observation_ids=[o.observation_id for o in OBS_H1],
        candidate_rule_ids=[c.rule_candidate_id for c in CAND_H1],
        open_questions=["乾度首10-20券商集中度門檻未量化（課程只說『可能集中』）",
                        "供股復仇記『數個百分點』貼近程度未精確定義"],
        last_position="EOF",
    ))


# ============================================================ HILTON lesson 2
S_H2 = source(
    "HILTON-CAIJI-L2", "財技班第二堂_課程摘要", "全購買賣殼(GO)：強制/自願、有條/無條、A-E五階段風險回報、殼價+扣水NAV、春江鴨、GO價包底、D階段炒作、E階段注資、GO+20/20配股、舊主留一手",
)

OBS_H2 = [
    Observation(
        observation_id="OBS-H2-001", methodology_id="HILTON", source_id=S_H2.source_id,
        source_section="全購的法律與結構", source_quote_or_paraphrase_reference="強制性全購兩個觸發條件：30%；30-50%一年內增2%",
        observation_statement="強制全購觸發規則（法規事實）：(1)持股由低位增至>30% (2)持有30%-50%且一年內再增持>2%。觸發後須申報並向全體股東提出全購。",
        observation_type=ObservationType.FACT_FROM_CASE,
        supporting_evidence="收購守則門檻描述",
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
    ),
    Observation(
        observation_id="OBS-H2-002", methodology_id="HILTON", source_id=S_H2.source_id,
        source_section="無條件與有條件全購", source_quote_or_paraphrase_reference="新主買入少於50%屬有條件全購…不足50%可取消；操作上較偏好無條件全購",
        observation_statement="無條件GO（新主已買>50%）確定性高；有條件GO（<50%）可因總接受不足50%而取消——失敗風險須定價。",
        observation_type=ObservationType.CONDITION,
        supporting_evidence="31%+8%=39%可取消 vs 51%必須完成的數字例子",
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
    ),
    Observation(
        observation_id="OBS-H2-003", methodology_id="HILTON", source_id=S_H2.source_id,
        source_section="五大階段", source_quote_or_paraphrase_reference="A風險低回報50-200%；B風險中高10-30%成敗各半；C風險極低GO價包底；D風險高回報極高判錯輸一半判啱10-40倍；E三年後質變",
        observation_statement="GO項目五階段風險回報分層：A殼股潛伏(低風險50-200%)、B洽談易手(中高10-30%成敗約半)、C正式易手至GO結束(極低風險GO價包底)、D GO結束後(高風險判錯-50%判對10-40倍)、E約兩三年後注資質變(中風險可觀回報)。值博率最高=A/C/D，但三者入場理由與退出規則完全不同。",
        observation_type=ObservationType.METHOD_PRINCIPLE,
        supporting_evidence="課程階段定義與倍數區間",
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
    ),
    Observation(
        observation_id="OBS-H2-004", methodology_id="HILTON", source_id=S_H2.source_id,
        source_section="A階段", source_quote_or_paraphrase_reference="合理賣殼價=殼價+NAV；商譽及收購合併價值歸零；內地物業廠房歸零；香港物業及現金按100%",
        observation_statement="合理賣殼價 = 殼價 + 扣水NAV。扣水規則：商譽/收購合併價值歸零、內地物業廠房歸零、香港物業及現金100%。NAV越低殼越乾淨；現市值 vs 合理賣殼價的差距即潛在利潤空間（例：2億市值 vs 6億賣殼價→約200%）。",
        observation_type=ObservationType.METHOD_PRINCIPLE,
        supporting_evidence="主板殼價5億+NAV1億=6億的換算例子",
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
    ),
    Observation(
        observation_id="OBS-H2-005", methodology_id="HILTON", source_id=S_H2.source_id,
        source_section="A2春江鴨", source_quote_or_paraphrase_reference="股價低位連續兩三日上升，成交量由十萬二十萬增至數百萬千多萬…最佳追入點通常是第二日收市前",
        observation_statement="春江鴨偵測：無公告背景下股價低位連升兩三日+成交量放大數十倍→知情資金入場線索。追入點=異動第二日收市前（確認量大過第一日）；第三日可能已升20-30%。成本控制目標=異動前價+10%內。3.8通告（與特定對象洽談）確定性高於3.7。",
        observation_type=ObservationType.TIMING_RULE,
        supporting_evidence="1143低位$1橫行兩年後成交爆升的實戰案例",
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
    ),
    Observation(
        observation_id="OBS-H2-006", methodology_id="HILTON", source_id=S_H2.source_id,
        source_section="C階段", source_quote_or_paraphrase_reference="必須在GO結束前兩日沽出；結束後包底消失，股價可立即大跌",
        observation_statement="GO價包底套利：正式易手至GO結束期間市價貼近GO價；低於GO價時套利力量推回。買入原則=貼近或低於GO價；強制離場=GO結束前兩日（包底消失後可立即大跌）。C階段是各種財技中最安全時段之一。",
        observation_type=ObservationType.TIMING_RULE,
        supporting_evidence="$0.97 vs GO價$1的折讓例子；1957跌穿GO價未收復的反例",
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
    ),
    Observation(
        observation_id="OBS-H2-007", methodology_id="HILTON", source_id=S_H2.source_id,
        source_section="D階段", source_quote_or_paraphrase_reference="新主最好是一個會因投入幾億買殼而肉痛的個人…必須有強悍瘋狂炒作往績…GO結束後先觀察約一個月，企穩GO價之上並有成交配合才跟隨",
        observation_statement="D階段（GO後炒作）兩項條件：(1)新主是個人（會肉痛）而非實業大集團——首三年受VSA/RTO限制只能先炒股回本 (2)新主有爆炒往績（黎亮3倍/紀曉波100倍級）。確認訊號=GO結束後約一個月守住GO價+成交配合；長期跌穿GO價=失敗。",
        observation_type=ObservationType.CONDITION,
        supporting_evidence="1367黎亮、023博華太平洋紀曉波往績案例",
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
    ),
    Observation(
        observation_id="OBS-H2-008", methodology_id="HILTON", source_id=S_H2.source_id,
        source_section="E階段", source_quote_or_paraphrase_reference="聯交所較易接受約1:1收購比例…先透過財技把市值擴大十倍再注入50億…判斷最早的注資線索是改名通告",
        observation_statement="E階段注資路徑：首三年VSA/RTO限制→透過財技（如大比例供股洗太平地）擴大股本市值→約1:1比例注資（注50億資產需約50億市值平台）。最早線索=改名通告（6123先達物流→圓通速遞國際案例），改名早於正式注資通告。",
        observation_type=ObservationType.SEQUENCE,
        supporting_evidence="6123改名首日大升、0102凱升E階段25倍案例",
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
    ),
    Observation(
        observation_id="OBS-H2-009", methodology_id="HILTON", source_id=S_H2.source_id,
        source_section="高分財技組合 GO+20/20", source_quote_or_paraphrase_reference="GO結束後再出現20/20配股屬非常高分的組合，歷史勝率約八至九成，常見三至四個月內三至四倍",
        observation_statement="GO+20/20配股組合（約20%折讓+20%極限比例）歷史勝率約八至九成，常見三至四個月內三至四倍；10/10配股不算完整組合、效果較弱；再配爆炒往績新主評分更高。屬課堂觀察統計，非保證。",
        observation_type=ObservationType.METHOD_PRINCIPLE,
        supporting_evidence="1143案例（A2入場→D階段+20/20配股→$9-11）",
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
    ),
    Observation(
        observation_id="OBS-H2-010", methodology_id="HILTON", source_id=S_H2.source_id,
        source_section="舊主留一手", source_quote_or_paraphrase_reference="最理想是舊主保留9.x%。持股超過10%會成為主要股東…9.x%已是不越過10%門檻下可保留的最大份額，訊號最強；4.x%也可加分但較弱",
        observation_statement="舊主留一手訊號：正常情況舊主應在殼價最值錢時清倉；保留股份=深入了解新主及後續計劃的加分訊號。強度分級：9.x%（不越10%主要股東門檻的最大保留）>4.x%。判斷以已披露事實為基礎，不猜測背後協議。",
        observation_type=ObservationType.AUTHOR_INTERPRETATION,
        supporting_evidence="2183保留9.x%、0848保留4.x%對照案例",
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
    ),
    Observation(
        observation_id="OBS-H2-011", methodology_id="HILTON", source_id=S_H2.source_id,
        source_section="案例 01236", source_quote_or_paraphrase_reference="表面只有35%易手屬有條件全購；但R報告顯示20%股份接受GO。市價長期高於GO價，正常散戶不會蝕價接受，推斷該20%是舊主暗倉，實際控制約55%",
        observation_statement="R報告暗倉偵測法：市價長期高於GO價時，接受要約者必蝕價——理性散戶不會接受；因此R報告中異常高的接受比例（01236案例20%）推斷為舊主暗倉過倉，實際控制≈易手35%+20%=55%。R報告接受結構是歸邊線索。",
        observation_type=ObservationType.AUTHOR_INTERPRETATION,
        supporting_evidence="01236國農控股R報告數字+市價/GO價對照推理",
        generalization_class=GeneralizationClass.POTENTIALLY_GENERALIZABLE,
    ),
    Observation(
        observation_id="OBS-H2-012", methodology_id="HILTON", source_id=S_H2.source_id,
        source_section="核心觀念", source_quote_or_paraphrase_reference="GO是乾淨交易…新主須證明有足夠資金完成100%全購…散戶有權按同一價格賣給新主",
        observation_statement="GO的本質=Clean Transaction：新主須證明資金完成100%全購；散戶獲按GO價退出的選擇權——市價低於GO價時GO價=包底，高於時散戶可不接受。GO股同一項目提供多次獲利機會（五階段各有玩法）。",
        observation_type=ObservationType.METHOD_PRINCIPLE,
        supporting_evidence="課程結構性說明",
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
    ),
]

CHAIN_H2_011 = EvidenceChain(
    chain_id="CHAIN-H2-011", observation_id="OBS-H2-011",
    input_facts=["01236易手比例35%（有條件全購）", "R報告：20%股份接受要約", "市價長期高於GO價"],
    temporal_order="GO結束後R報告揭示接受結構",
    calculation_or_comparison="35%易手+20%接受=55%；接受者蝕價（市價>GO價）違反散戶理性",
    author_reasoning="只有與交易相關的暗倉才會蝕價接受→20%為舊主暗倉過倉",
    author_conclusion="實際控制約55%，成為歸邊線索（AUTHOR_INTERPRETATION，需CCASS佐證）",
)

CAND_H2 = [
    RuleCandidate(
        rule_candidate_id="CAND-HILTON-GO-STAGE-MATRIX-001", rule_family=RuleFamily.STAGE_CLASSIFICATION,
        methodology_id="HILTON", rule_name="GO五階段風險回報矩陣與分階段退出規則",
        description="GO項目按時間線分A(潛伏)/B(洽談)/C(GO包底)/D(GO後炒作)/E(三年注資)五階段，每階段有獨立風險回報與退出規則；值博率最高A/C/D。C階段強制GO結束前兩日離場；D階段以GO後一個月守GO價為分界。",
        preconditions=["已識別GO事件"],
        required_inputs=["3.7/3.8通告日", "正式易手日", "GO起止日", "GO價", "新主身份"],
        optional_inputs=["R報告接受結構", "新主往績倍數"],
        trigger_conditions=["階段轉換事件：洽談公布/正式易手/GO開始/GO結束/三年期滿"],
        supporting_evidence=["OBS-H2-003", "OBS-H2-006", "OBS-H2-007"],
        output_semantics="階段標籤 + 該階段風險等級 + 離場規則；階段間規則不可互借用",
        false_positive_conditions=["有條件GO被當成必然完成（B/C階段安全性高估）"],
        false_negative_conditions=["非典型時間線（GO延長/縮短）"],
        falsification_conditions=["C階段『GO結束前兩日離場』規則在回測中劣於持有越過GO結束", "D階段一個月守GO價與後續回報無相關"],
        origin_case_ids=["CASE-HILTON-1143", "CASE-HILTON-1957", "CASE-HILTON-0102"],
        origin_source_ids=[S_H2.source_id], origin_observation_ids=["OBS-H2-003", "OBS-H2-006", "OBS-H2-007"],
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
        dedup_classification=DedupClassification.NEW_RULE,
    ),
    RuleCandidate(
        rule_candidate_id="CAND-HILTON-SHELL-PRICE-001", rule_family=RuleFamily.SHELL_VALUE,
        methodology_id="HILTON", rule_name="合理賣殼價=殼價+扣水NAV",
        description="殼價（隨年份/主板創業板變動）+扣水NAV（商譽歸零、內地物業廠房歸零、香港物業現金100%）=合理賣殼價；現市值對合理賣殼價的折讓=A階段潛在利潤空間。NAV越低殼越乾淨。",
        preconditions=["已取得當期殼價行情"],
        required_inputs=["殼價", "NAV明細（商譽/物業所在地/現金）", "已發行股數", "現市值"],
        trigger_conditions=["市值顯著低於合理賣殼價"],
        supporting_evidence=["OBS-H2-004"],
        output_semantics="合理GO價估算 + 利潤空間百分比",
        false_positive_conditions=["殼價行情過時", "NAV水分扣除不足（或有隱藏負債）"],
        false_negative_conditions=["特大型注資預期令市值合理地高於殼價公式值"],
        falsification_conditions=["實際GO成交價系統性偏離(殼價+扣水NAV)公式超出殼價行情誤差"],
        origin_case_ids=["CASE-HILTON-1143"],
        origin_source_ids=[S_H2.source_id], origin_observation_ids=["OBS-H2-004"],
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
        dedup_classification=DedupClassification.NEW_RULE,
    ),
    RuleCandidate(
        rule_candidate_id="CAND-HILTON-SPRING-DUCK-001", rule_family=RuleFamily.EVENT_SEQUENCE,
        methodology_id="HILTON", rule_name="春江鴨異動：低位連升+量爆→第二日收市前追入",
        description="公告前的異常量價（低位連升兩三日+成交量放大數十倍）=知情資金線索；追入點=第二日收市前（確認量大於第一日），成本控制在異動前價+10%內；3.8通告提升確定性。追錯則跌回原位，須止蝕。",
        preconditions=["無正式公告", "股價處於低位"],
        required_inputs=["日成交量序列", "日收盤價序列"],
        optional_inputs=["3.7/3.8通告狀態"],
        trigger_conditions=["連續2日升+量較平日放大一個數量級"],
        supporting_evidence=["OBS-H2-005"],
        alternative_explanations=["純市場情緒波動", "其他不相關消息洩漏"],
        output_semantics="春江鴨嫌疑標記 + 建議入場日（第二日收市前）",
        false_positive_conditions=["炒房對倒製造假異動"],
        false_negative_conditions=["極度隱蔽的收貨（無量價異動）"],
        falsification_conditions=["第二日收市前追入法的事後統計不優於隨機低位買入"],
        origin_case_ids=["CASE-HILTON-1143"],
        origin_source_ids=[S_H2.source_id], origin_observation_ids=["OBS-H2-005"],
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
        dedup_classification=DedupClassification.NEW_RULE,
    ),
    RuleCandidate(
        rule_candidate_id="CAND-HILTON-GO-2020-001", rule_family=RuleFamily.PLACEMENT,
        methodology_id="HILTON", rule_name="GO+20/20配股高分組合（勝率約八至九成）",
        description="GO結束後出現約20%折讓、20%比例配股=極高分組合；課堂觀察勝率約八至九成，常見三至四個月內三至四倍。10/10不算完整組合；疊加爆炒往績新主更高分。",
        preconditions=["GO已結束", "隨後出現配股公告"],
        required_inputs=["配股比例", "配股折讓", "GO完成狀態"],
        optional_inputs=["新主往績"],
        trigger_conditions=["GO後配股比例≈20%且折讓≈20%"],
        supporting_evidence=["OBS-H2-009"],
        output_semantics="組合評分：HIGH（附勝率為課堂觀察統計，非平台驗證）",
        false_positive_conditions=["把10/10誤判為20/20", "配股後市況系統性轉差"],
        false_negative_conditions=["非整數比例但實質等效的組合"],
        falsification_conditions=["獨立回測中GO+20/20的勝率或倍數顯著低於八至九成/三至四倍"],
        origin_case_ids=["CASE-HILTON-1143"],
        origin_source_ids=[S_H2.source_id], origin_observation_ids=["OBS-H2-009"],
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
        dedup_classification=DedupClassification.NEW_RULE,
    ),
    RuleCandidate(
        rule_candidate_id="CAND-HILTON-OLD-OWNER-STAKE-001", rule_family=RuleFamily.CONTROL_CHANGE,
        methodology_id="HILTON", rule_name="舊主留一手：保留9.x%>4.x%加分訊號",
        description="GO後舊主不清倉而保留少數股權=知悉新主後續計劃的加分訊號（作者解讀）。強度：9.x%（貼10%主要股東門檻下最大保留）>4.x%。判斷只用已披露持股，不猜背後協議。",
        preconditions=["控制權轉移完成"],
        required_inputs=["舊主轉移後持股披露"],
        trigger_conditions=["舊主保留4.x%-9.x%"],
        supporting_evidence=["OBS-H2-010"],
        alternative_explanations=["交易條款強制保留", "稅務/技術原因未能即時沽出"],
        output_semantics="訊號強度分級 STRONG(9.x%)/MODERATE(4.x%)",
        false_positive_conditions=["舊主沽售受限制（禁售期）而非自願看好"],
        false_negative_conditions=["舊主清倉但以場外協議參與"],
        falsification_conditions=["保留9.x%的GO項目後續表現與全清倉項目無統計差異"],
        origin_case_ids=["CASE-HILTON-2183", "CASE-HILTON-0848"],
        origin_source_ids=[S_H2.source_id], origin_observation_ids=["OBS-H2-010"],
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
        dedup_classification=DedupClassification.NEW_RULE,
    ),
    RuleCandidate(
        rule_candidate_id="CAND-HILTON-RREPORT-DARK-001", rule_family=RuleFamily.CCASS_TRANSFER,
        methodology_id="HILTON", rule_name="R報告異常接受比例=暗倉過倉線索",
        description="市價長期高於GO價時接受要約者必蝕價，理性散戶不會接受；R報告中異常高的接受比例（如01236的20%）推斷為舊主暗倉過倉→實際控制≈易手比例+異常接受比例。屬作者解讀，需CCASS佐證。",
        preconditions=["GO結束且R報告已發布", "要約期內市價高於GO價"],
        required_inputs=["R報告接受比例", "市價/GO價對照", "易手比例"],
        trigger_conditions=["接受比例顯著高於蝕價接受所能解釋的散戶行為"],
        supporting_evidence=["OBS-H2-011"],
        contradicting_evidence=["個別散戶誤操作或須急售亦可產生少量接受"],
        alternative_explanations=["機構套盤（如指數剔除強制沽出）"],
        output_semantics="暗倉嫌疑標記 + 實際控制估算（帶AUTHOR_INTERPRETATION標籤）",
        false_positive_conditions=["市價僅短暫高於GO價", "稅務或強制性沽售壓力"],
        false_negative_conditions=["暗倉以場外方式轉移不經GO要約"],
        falsification_conditions=["CCASS數據顯示異常接受部分並非流向新主關聯券商"],
        origin_case_ids=["CASE-HILTON-01236"],
        origin_source_ids=[S_H2.source_id], origin_observation_ids=["OBS-H2-011"],
        generalization_class=GeneralizationClass.POTENTIALLY_GENERALIZABLE,
        dedup_classification=DedupClassification.NEW_RULE,
    ),
]

INGEST_BLOCKS = []


def _register_h2(store):
    store.register_source(S_H2)
    for o in OBS_H2:
        store.add_observation(o)
    store.add_observation(OBS_H2[10], CHAIN_H2_011)
    for c in CAND_H2:
        store.add_candidate(c)
    store.mark_source_status(S_H2.source_id, "INGESTED")
    store.save_checkpoint(IngestionCheckpoint(
        source_id=S_H2.source_id,
        processed_sections=["核心觀念", "大市觀察", "全購的法律與結構", "五大階段", "操作流程", "老師重點", "高分財技組合", "重要案例", "注意事項", "本課總結"],
        observation_ids=[o.observation_id for o in OBS_H2],
        candidate_rule_ids=[c.rule_candidate_id for c in CAND_H2],
        open_questions=["GO+20/20『八至九成勝率』無法從課程還原樣本清單——須以本站GO名單獨立重算",
                        "殼價行情數字隨時間變動，公式保留但殼價須外部更新"],
        last_position="EOF",
    ))


# ============================================================ HILTON lesson 3
S_H3 = source(
    "HILTON-CAIJI-L3", "財技班第三堂_課程摘要", "非全購(Non-GO)/清洗豁免/最低市值公式；送紅股+29XX轉碼；拆股高低位；配股利好利淡清單/三形式/時間止蝕；細價股收貨沽貨流動性訊號",
)

OBS_H3 = [
    Observation(
        observation_id="OBS-H3-001", methodology_id="HILTON", source_id=S_H3.source_id,
        source_section="非全購買賣殼", source_quote_or_paraphrase_reference="非全購：公司印發大量新股給新主…舊主沒有直接收取殼價…預設是不參與；95%正常案例中新舊主必須極度信任",
        observation_statement="Non-GO結構：新主以遠低於GO成本（數千萬 vs 數億）認購大量新股取得控制權，資金進入自己控制的公司；舊主無現金離場、被攤薄成小股東——約95%案例要求新舊主極度信任（檯底承諾）。散戶無GO價保障，預設不參與。",
        observation_type=ObservationType.METHOD_PRINCIPLE,
        supporting_evidence="100股印300股→新主75%的結構例子",
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
    ),
    Observation(
        observation_id="OBS-H3-002", methodology_id="HILTON", source_id=S_H3.source_id,
        source_section="清洗豁免", source_quote_or_paraphrase_reference="聯交所容許豁免的原因是舊主並未收取出售股份的現金…若公司並無財困卻讓新主以遠低於市價取得大量新股…是監管機構主要打擊的買殼方式",
        observation_statement="清洗豁免邏輯：Non-GO新主0%→>30%本觸發強制GO，故通常申請Whitewash Waiver；聯交所批准理由=舊主同被攤薄留在公司。無財困公司以極折讓Non-GO入主=監管重點打擊對象，散戶須警覺。",
        observation_type=ObservationType.CONDITION,
        supporting_evidence="白武士財困拯救 vs 無財困極折讓印股的對照",
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
    ),
    Observation(
        observation_id="OBS-H3-003", methodology_id="HILTON", source_id=S_H3.source_id,
        source_section="合理市值公式 / 01250", source_quote_or_paraphrase_reference="最低合理總市值=舊主原本應得殼價÷完成後舊主持股比例；01250:合理殼價6億×75%=4.5億，Non-GO後餘5%，最低市值90億，實際$0.14→$1.9十多倍",
        observation_statement="Non-GO最低市值公式：合理殼價×舊主持股比例=舊主應得金額；再÷完成後舊主餘下比例=最低合理總市值。01250北控清潔能源：25億→最低90億（三至四倍空間），實際六個月十多倍。公式只證明最低空間，離場仍跟出貨訊號。",
        observation_type=ObservationType.METHOD_PRINCIPLE,
        supporting_evidence="01250一配四、新主80%、舊主75%→5%、印股後市值25億的完整數字",
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
    ),
    Observation(
        observation_id="OBS-H3-004", methodology_id="HILTON", source_id=S_H3.source_id,
        source_section="應避開的情況 / 期殼", source_quote_or_paraphrase_reference="上市約兩年內的半新股或一至三年內快速賣殼的公司，可能是期殼…幕後金主賺的是期殼與正式上市殼價的差額，不需炒高股價補償舊主",
        observation_statement="期殼排除規則：上市約兩年內即賣殼/Non-GO的公司可能是預先安排的殼——幕後金主已檯底持有、上市後直接套殼價差額，毋須炒高補償舊主；且舊殼也可場外找數（高價垃圾資產交易）。無著名新主+非上市多年舊殼+無法證明炒高補償邏輯=不參與。",
        observation_type=ObservationType.RISK_WARNING,
        supporting_evidence="期殼51%檯底安排成本數千萬的結構說明",
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
    ),
    Observation(
        observation_id="OBS-H3-005", methodology_id="HILTON", source_id=S_H3.source_id,
        source_section="送紅股/除淨日效應", source_quote_or_paraphrase_reference="1送9時市場暫時只有原本一成股份可流通，流通市值大減約九成…股票暫時轉用29XX交易代碼…成交歷史可能難以追查，令高位派貨痕跡消失",
        observation_statement="送紅股除淨窗口機制：除淨至生效日流通量僅剩一成（1送9）→舞高弄低成本降約九成；股份暫用29XX代碼，臨時代碼循環再用使派貨成交歷史難以追查；新股生效前被鎖定。送紅股不創造價值，通常屬高位散貨Signal。",
        observation_type=ObservationType.METHOD_PRINCIPLE,
        supporting_evidence="1送9→$1拆成10股@0.1的價值守恆計算+散戶額外成本",
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
    ),
    Observation(
        observation_id="OBS-H3-006", methodology_id="HILTON", source_id=S_H3.source_id,
        source_section="拆股", source_quote_or_paraphrase_reference="低位拆股代表先降低入場費準備炒高；高位拆股通常毋須再經歷炒高，可直接配合派貨",
        observation_statement="拆股位置判斷：低位拆股=降低入場費為將來炒作鋪路（起步Signal）；高位拆股=擴大散戶買家池直接派貨。與送紅股差異=無鎖倉空窗。同一項目可低位高位各拆一次；Signal須放完整炒作週期理解。",
        observation_type=ObservationType.CONDITION,
        supporting_evidence="1拆10≡1送9（無鎖倉差異）的等價說明",
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
    ),
    Observation(
        observation_id="OBS-H3-007", methodology_id="HILTON", source_id=S_H3.source_id,
        source_section="配股基礎", source_quote_or_paraphrase_reference="一般授權一年內配發不超過約20%，折讓不超過19.99%…對散戶的優劣次序：配新股最好、先舊後新其次、配舊股最差",
        observation_statement="配股制度與形式：一般授權=年內≤20%配發+≤19.99%折讓（20/20），可分次用盡；超限走特別授權。形式優劣：配新股（承配人承受20-30日鎖倉→支持與M同船推論）>先舊後新（無鎖倉）>配舊股（大股東直接減持套現=明確派貨）。代價發行不屬配股玩法。",
        observation_type=ObservationType.METHOD_PRINCIPLE,
        supporting_evidence="三種形式的資金流向差異（入公司 vs 入大股東口袋）",
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
    ),
    Observation(
        observation_id="OBS-H3-008", methodology_id="HILTON", source_id=S_H3.source_id,
        source_section="利好條件", source_quote_or_paraphrase_reference="低位橫行無成交…零成交或每日數千至十萬元時，陌生人不會無故承接數千萬新股，承配人較可能是自己人…六人以上/不披露身份：較適合安排人頭或自己人",
        observation_statement="優質配股（收貨Signal）七利好：(1)低位橫行零成交（承配人只能是自己人）(2)大比例大折讓（用盡20/20低價收貨）(3)配新股（鎖倉承擔）(4)≥6名不披露身份承配人（匿名安排）(5)殼底已乾（之前已完成大部分收貨）(6)M有往績（高低位以M歷史倍數校準）(7)低市值貨源集中。",
        observation_type=ObservationType.CONDITION,
        supporting_evidence="8218低位20/20一個月十倍、0007一個月$4→$24（19名股東控九成）等案例",
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
    ),
    Observation(
        observation_id="OBS-H3-009", methodology_id="HILTON", source_id=S_H3.source_id,
        source_section="利淡條件", source_quote_or_paraphrase_reference="高位配股多數是炒作尾聲散貨Signal…配舊股明確表示派貨…少於六名承配人須披露姓名…高位由Blackstone紅杉高瓴等基金承接，視為接火棒訊號，應離場",
        observation_statement="散貨配股（利淡）六訊號：(1)高位配股（升2-4倍後）(2)小比例小折讓（貼市易派散戶）(3)配舊股（大股東套現）(4)<6名須披露身份（承接者可能是水魚）(5)知名基金承接=接火棒、離場（基金用客戶資金風險結構不同）(6)位置模糊不參與。",
        observation_type=ObservationType.RISK_WARNING,
        supporting_evidence="2346瀛海集團低位起步後高位再配的完整對照案例",
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
    ),
    Observation(
        observation_id="OBS-H3-010", methodology_id="HILTON", source_id=S_H3.source_id,
        source_section="操作與風控", source_quote_or_paraphrase_reference="靚配股通常半個月至一個月內啟動…一個月仍不動便作時間止蝕…找不到合理止蝕位就不買",
        observation_statement="配股時間止蝕：成立項目半個月至一個月內啟動（速度遠快於供股半年期）；一個月不動即離場換馬，即使微升打和。買前先有價格止蝕位；找不到止蝕位不買或只用可全輸小注。市差時短炒型配股（貨源僅七成）翌日一兩日升一兩倍即完，只宜小注。",
        observation_type=ObservationType.TIMING_RULE,
        supporting_evidence="8452十五日2.5倍、1327十日兩倍、8223快速案例",
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
    ),
    Observation(
        observation_id="OBS-H3-011", methodology_id="HILTON", source_id=S_H3.source_id,
        source_section="細價股買賣技巧", source_quote_or_paraphrase_reference="低位難買通常是正面訊號，代表莊家也在收貨…到合適的散貨高位，買盤會非常充足，散戶低一兩個價位便可成交",
        observation_statement="流動性反訊號（作者方法論）：低位難買=莊家同步收貨（正面）；持倉>2-3%會被莊家從券商倉位辨認，須拆倉三四間行。高位易沽（買盤充足）=真正散貨期已到；升數倍但沽不出=大股東散貨期未到（1367案例$5沽不出持到$15）。低位用限價GTC掛盤於二三十隻等貨。",
        observation_type=ObservationType.AUTHOR_INTERPRETATION,
        supporting_evidence="1367中滔環保$5→$15流動性對照；GTC掛盤操作細節",
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
    ),
    Observation(
        observation_id="OBS-H3-012", methodology_id="HILTON", source_id=S_H3.source_id,
        source_section="81XX 案例", source_quote_or_paraphrase_reference="配股後持股29.97%，刻意低於30%，明顯是避開GO門檻、安排Non-GO的線索",
        observation_statement="貼門檻持股偵測：新主持股停在29.97%（貼30%下）=刻意避開強制GO、安排Non-GO路徑的披露線索。同理須監察貼5%、貼10%等門檻位的異常停駐。",
        observation_type=ObservationType.FACT_FROM_CASE,
        supporting_evidence="81XX簡志堅案例披露持股數字",
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
    ),
    Observation(
        observation_id="OBS-H3-013", methodology_id="HILTON", source_id=S_H3.source_id,
        source_section="核心觀念", source_quote_or_paraphrase_reference="送紅股、拆股和配股都屬Signal，同一財技可在低位代表收貨或起步，在高位代表派貨或炒作尾聲",
        observation_statement="Signal思維總綱：財技通告（送紅股/拆股/配股）本身無好淡，位置+M+市值+成交+貨源+形式+承配人關係七項合併判斷；未能判斷便不參與。妖股由操作位置決定（低買高沽=發達股），不由股票本身決定。",
        observation_type=ObservationType.METHOD_PRINCIPLE,
        supporting_evidence="課程總綱及2346雙相位案例",
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
    ),
]

CHAIN_H3_003 = EvidenceChain(
    chain_id="CHAIN-H3-003", observation_id="OBS-H3-003",
    input_facts=["01250印股前市值約5億；一配四後約25億", "殼價約5億+NAV約1億=合理殼價6億",
                 "舊主75%→Non-GO後約5%；新主約80%；散戶約1.5%"],
    temporal_order="印股（一配四）→市值25億→其後六個月炒至$1.9",
    calculation_or_comparison="舊主應得=6億×75%=4.5億；最低市值=4.5億÷5%=90億；25億→90億=三至四倍最低空間",
    author_reasoning="舊主自願被攤薄的前提是餘下股份經炒高後≥正常GO應得金額",
    author_conclusion="實際$0.14→$1.9（十多倍）遠超最低公式；公式只定下限，離場跟出貨訊號",
)

CAND_H3 = [
    RuleCandidate(
        rule_candidate_id="CAND-HILTON-NONGO-FLOOR-001", rule_family=RuleFamily.NON_GO,
        methodology_id="HILTON", rule_name="Non-GO最低市值=舊主應得殼價÷餘下比例",
        description="Non-GO後最低合理總市值=（合理殼價×舊主原持股比例）÷完成後舊主餘下比例。商業邏輯：舊主餘下股份炒高後價值≥其原應得殼價才合理。公式只定下限；預設不參與，僅在著名新主+上市多年舊殼+排除期殼時考慮。",
        preconditions=["Non-GO交易完成或公布", "已有當期殼價與扣水NAV"],
        required_inputs=["殼價", "扣水NAV", "舊主原持股%", "完成後舊主餘下%", "現市值"],
        optional_inputs=["新主身份/往績", "上市年資"],
        trigger_conditions=["Non-GO事件辨識（大量印股/供股包銷/CB/認股權/押股致控制權轉移）"],
        supporting_evidence=["OBS-H3-001", "OBS-H3-003"],
        output_semantics="最低合理市值 + 最低空間倍數（下限估值，非目標價）",
        false_positive_conditions=["期殼（毋須炒高補償舊主）", "場外找數（高價資產交易）令公式前提失效"],
        false_negative_conditions=["舊主實際已檯底收費，公式高估"],
        falsification_conditions=["已知Non-GO案例的實際市值路徑系統性低於公式下限"],
        origin_case_ids=["CASE-HILTON-01250", "CASE-HILTON-0241", "CASE-HILTON-1143", "CASE-HILTON-0112"],
        origin_source_ids=[S_H3.source_id], origin_observation_ids=["OBS-H3-003", "OBS-H3-001"],
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
        dedup_classification=DedupClassification.NEW_RULE,
    ),
    RuleCandidate(
        rule_candidate_id="CAND-HILTON-PLACEMENT-CHECKLIST-001", rule_family=RuleFamily.PLACEMENT,
        methodology_id="HILTON", rule_name="配股七利好六利淡位置判斷清單",
        description="配股Signal好淡由七利好（低位零成交/大比例大折讓/配新股/≥6名匿名承配/殼底乾/M有往績/低市值集中）對六利淡（高位/小比例小折讓/配舊股/<6名披露/知名基金承接/位置模糊）計分；知名基金承接=離場訊號。",
        preconditions=["配股公告已發布"],
        required_inputs=["股價位置（高低位）", "配股形式（新/舊/先舊後新）", "比例與折讓", "承配人人數與披露狀態"],
        optional_inputs=["M往績", "市值", "歸邊度", "承配人身份"],
        trigger_conditions=["配股通告（一般授權≤20%/19.99%或特別授權）"],
        supporting_evidence=["OBS-H3-008", "OBS-H3-009", "OBS-H3-007", "OBS-H3-013"],
        output_semantics="配股分類：ACCUMULATION_SIGNAL / DISTRIBUTION_SIGNAL / UNCLASSIFIED(不參與)",
        false_positive_conditions=["低位大折讓但實際財困強制集資"],
        false_negative_conditions=["多種財技疊加（拆股+配股）時清單訊號互相掩蓋"],
        falsification_conditions=["清單分類與事後價格路徑（啟動/派貨）無統計相關"],
        origin_case_ids=["CASE-HILTON-8218", "CASE-HILTON-0007", "CASE-HILTON-2346", "CASE-HILTON-0476"],
        origin_source_ids=[S_H3.source_id], origin_observation_ids=["OBS-H3-008", "OBS-H3-009"],
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
        dedup_classification=DedupClassification.NEW_RULE,
    ),
    RuleCandidate(
        rule_candidate_id="CAND-HILTON-PLACEMENT-TSTOP-001", rule_family=RuleFamily.PLACEMENT,
        methodology_id="HILTON", rule_name="配股時間止蝕：半個月至一個月不啟動即離場",
        description="優質配股項目半個月至一個月內啟動（快於供股半年期約12倍）；到期不動即時間止蝕換馬，不把等待合理化。短炒型（貨源七成）一兩日內完成只宜小注。",
        preconditions=["已按清單判定為收貨Signal並參與"],
        required_inputs=["配股完成日", "持倉入場日"],
        trigger_conditions=["入場後滿一個月未啟動"],
        supporting_evidence=["OBS-H3-010"],
        output_semantics="離場指令（時間止蝕）",
        false_positive_conditions=["巨型項目（高銀型）等待期天然較長"],
        false_negative_conditions=["一月內啟動但隨即失敗——時間止蝕不代替價格止蝕"],
        falsification_conditions=["回測顯示一個月未啟動項目的其後表現不差於已啟動項目"],
        origin_case_ids=["CASE-HILTON-8218", "CASE-HILTON-8452", "CASE-HILTON-1327"],
        origin_source_ids=[S_H3.source_id], origin_observation_ids=["OBS-H3-010"],
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
        dedup_classification=DedupClassification.NEW_RULE,
    ),
    RuleCandidate(
        rule_candidate_id="CAND-HILTON-BONUS-SHARE-29XX-001", rule_family=RuleFamily.CCASS_DISTRIBUTION,
        methodology_id="HILTON", rule_name="送紅股除淨窗口：流通-90%+29XX轉碼掩藏派貨",
        description="送紅股除淨至生效日流通量大減（1送9剩一成）令操控成本降約九成；29XX臨時代碼循環再用使該窗口成交歷史難追查=派貨痕跡掩藏。送紅股通常屬高位散貨工具。",
        preconditions=["送紅股公告已發布"],
        required_inputs=["送股比例", "除淨日", "生效日", "公告時股價位置"],
        trigger_conditions=["除淨日進入流通縮減窗口"],
        supporting_evidence=["OBS-H3-005"],
        output_semantics="DISTRIBUTION_WINDOW標記（除淨日至生效日）+ 數據完整性警示（29XX成交歷史可能斷裂）",
        false_positive_conditions=["低位送紅股作啟動鋪墊"],
        false_negative_conditions=["派貨經場外/對敲完成不經窗口"],
        falsification_conditions=["29XX窗口的CCASS大戶持股變化顯示無派發"],
        origin_case_ids=[],
        origin_source_ids=[S_H3.source_id], origin_observation_ids=["OBS-H3-005"],
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
        dedup_classification=DedupClassification.NEW_RULE,
    ),
    RuleCandidate(
        rule_candidate_id="CAND-HILTON-LIQUIDITY-PHASE-001", rule_family=RuleFamily.CCASS_ACCUMULATION,
        methodology_id="HILTON", rule_name="流動性反訊號：低位難買=收貨中；高位易沽=散貨期",
        description="（作者解讀）細價股低位買盤稀少=莊家同步收貨；升數倍仍沽不出=大股東散貨期未到；高位買盤異常充足=散貨殺戮期。持倉>2-3%會被莊家辨認，須拆倉多行。",
        preconditions=["鎖定財技股標的"],
        required_inputs=["日成交量", "買賣盤深度", "價格位置"],
        optional_inputs=["CCASS歸邊度", "媒體宣傳強度"],
        trigger_conditions=["低位持續買不到貨 / 高位持續輕易沽出"],
        supporting_evidence=["OBS-H3-011"],
        alternative_explanations=["單純流動性枯竭（項目死掉）", "做市規則變化"],
        output_semantics="階段線索：ACCUMULATING / NOT_YET_DISTRIBUTING / DISTRIBUTING",
        false_positive_conditions=["長期零成交的僵屍殼（無後續炒作）"],
        false_negative_conditions=["莊家以市場盤低調派貨"],
        falsification_conditions=["低位難買樣本群與流動性正常樣本群的後續回報無差異"],
        origin_case_ids=["CASE-HILTON-1367"],
        origin_source_ids=[S_H3.source_id], origin_observation_ids=["OBS-H3-011"],
        generalization_class=GeneralizationClass.POTENTIALLY_GENERALIZABLE,
        dedup_classification=DedupClassification.NEW_RULE,
    ),
    RuleCandidate(
        rule_candidate_id="CAND-HILTON-THRESHOLD-HUG-001", rule_family=RuleFamily.CONTROL_CHANGE,
        methodology_id="HILTON", rule_name="貼門檻持股=路徑意圖線索（29.97%避GO）",
        description="披露持股異常停駐在法定門檻微下方（29.97%貼30%強制GO線）=刻意選擇交易路徑的線索（此例：避GO走Non-GO）。平台層面同樣監察貼5%/10%/30%/50%的停駐。",
        preconditions=["有 filer 持股披露序列"],
        required_inputs=["持股%序列", "門檻值列表（5/10/30/50）"],
        trigger_conditions=["持股持續停駐門檻−ε且無自然解釋"],
        supporting_evidence=["OBS-H3-012"],
        output_semantics="THRESHOLD_HUG標記 + 推斷路徑意圖（避GO/保主要股東地位/避申報）",
        false_positive_conditions=["湊巧的市場買賣平衡"],
        false_negative_conditions=["多帳戶分散隱藏真實門檻位置"],
        falsification_conditions=["貼門檻停駐樣本的後續路徑與隨機持股群無差異"],
        origin_case_ids=["CASE-HILTON-81XX-JIANZHIJIAN"],
        origin_source_ids=[S_H3.source_id], origin_observation_ids=["OBS-H3-012"],
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
        dedup_classification=DedupClassification.NEW_RULE,
    ),
]


def _register_h3(store):
    store.register_source(S_H3)
    for o in OBS_H3:
        store.add_observation(o)
    store.add_observation(OBS_H3[2], CHAIN_H3_003)
    for c in CAND_H3:
        store.add_candidate(c)
    store.mark_source_status(S_H3.source_id, "INGESTED")
    store.save_checkpoint(IngestionCheckpoint(
        source_id=S_H3.source_id,
        processed_sections=["核心觀念", "非全購買賣殼", "非全購的估值與操作", "送紅股", "拆股", "配股基礎", "配股判斷流程", "重要案例", "細價股買賣技巧", "心態與紀律", "注意事項", "本課總結"],
        observation_ids=[o.observation_id for o in OBS_H3],
        candidate_rule_ids=[c.rule_candidate_id for c in CAND_H3],
        open_questions=["95%信任比例為課堂經驗估計，無法獨立驗證",
                        "2-3%拆倉門檻為實務經驗值，隨個股成交額變化"],
        last_position="EOF",
    ))


# ============================================================ HILTON lesson 4
S_H4 = source(
    "HILTON-CAIJI-L4", "財技班第四堂_課程摘要", "白武士重組(削債/Non-GO/CB注資/九成歸邊/0607+0931案例)；啤殼(集資額不合理篩選/保薦人班底/三種走勢/兩年時間壓力)；損失規避與蟹貨區",
)

OBS_H4 = [
    Observation(
        observation_id="OBS-H4-001", methodology_id="HILTON", source_id=S_H4.source_id,
        source_section="白武士三步重組+CB", source_quote_or_paraphrase_reference="削債、股本重組→Non-GO印新股→剝離舊業務注資；直接配巨量新股會令公眾持股跌穿25%，CB未兌換前屬債券…兌換後白武士可取九成以上，平均成本攤薄至一仙或以下",
        observation_statement="白武士重組三步：債務+股本重組→Non-GO印新股取得控制權→剝離舊業務+注資。CB路徑：注資以CB支付（未兌換不動股本、易過25%公眾持股關），條件成熟兌換後取>90%股份，平均成本攤至≤一仙；復牌數仙已數倍帳面，炒至數元=數十至數百倍。",
        observation_type=ObservationType.METHOD_PRINCIPLE,
        supporting_evidence="表面成本約1億（削傷+專業費2,000萬+營運證明3,000萬）與回報結構",
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
    ),
    Observation(
        observation_id="OBS-H4-002", methodology_id="HILTON", source_id=S_H4.source_id,
        source_section="六大優勢", source_quote_or_paraphrase_reference="判斷好壞的核心是完成CB兌換及重組後能否達到約九成以上歸邊；不足便不參與…乾度與客源的特殊結合：重組後街貨一成以下分散在十萬計歷史小股東手中",
        observation_statement="白武士好壞判準：重組後歸邊≥90%+商業炒作動機（非政府/社會穩定要求）=好；六七成歸邊=無炒作動機不參與。特殊結合：死殼歷史累積大量股東（客多）+重組後極乾，流動性與派貨環境同時最佳。復牌審批謹慎→假數風險相對低。",
        observation_type=ObservationType.CONDITION,
        supporting_evidence="2326公眾持股56.62%→8.2%的攤薄數字",
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
    ),
    Observation(
        observation_id="OBS-H4-003", methodology_id="HILTON", source_id=S_H4.source_id,
        source_section="白武士操作方法", source_quote_or_paraphrase_reference="理想是在復牌後市值跌至接近正常殼價或只高一至兩成時分散買入…只可用完全不需取回的閒錢…不能設一般價格止蝕…主席公開預測$2至$3，結果仍可完全未兌現",
        observation_statement="白武士操作：復牌市值回落至殼價+0-20%時用閒錢分散買入；無固定啟動時間（等細價股牛市）、不可設一般價格止蝕、不可追升。公開目標價不作準（0931主席稱$2-3未兌現）——出貨訊號凌駕人為目標價。",
        observation_type=ObservationType.RISK_WARNING,
        supporting_evidence="2309復牌高市值不可追案例；0931目標價未兌現",
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
    ),
    Observation(
        observation_id="OBS-H4-004", methodology_id="HILTON", source_id=S_H4.source_id,
        source_section="案例 0607", source_quote_or_paraphrase_reference="2008停牌→2010簡志堅350萬購36%→2013削債3億+Open Offer印16億股@0.05，季昌群包銷52%→5億CB@0.05→九成以上、成本一仙→最高$4.5約90倍歷時四年",
        observation_statement="0607豐盛控股完整白武士鏈：停牌→低價購舊主股份→削債3億+賣回舊業務→Open Offer Non-GO（新主承諾不供、季昌群包銷52%）→5億CB@0.05→兌換後>90%成本一仙→復牌$0.05即五倍帳面→最高$4.5（約90倍/四年）。",
        observation_type=ObservationType.FACT_FROM_CASE,
        supporting_evidence="各步驟金額/股數/價格/比例數字完整",
        generalization_class=GeneralizationClass.POTENTIALLY_GENERALIZABLE,
    ),
    Observation(
        observation_id="OBS-H4-005", methodology_id="HILTON", source_id=S_H4.source_id,
        source_section="案例 0931", source_quote_or_paraphrase_reference="平均成本不足一仙，貨源九成以上歸邊…以中國天然氣概念及MOU包裝，實質員工及業務很少…海外沽空機構以實業價值狙擊，忽略貨源及財技控制，未能把價格壓回其估值",
        observation_statement="0931中國天然氣：成本≤一仙+九成歸邊+概念包裝（MOU）推至數百億市值、最高約300倍。沽空機構以實業估值狙擊失敗——財技股的估值錨是貨源與財技控制，不是業務價值。",
        observation_type=ObservationType.AUTHOR_INTERPRETATION,
        supporting_evidence="簡志堅1,600萬購股+3,000萬買債轉CB+5,000萬重組金，總成本約1億的序列",
        generalization_class=GeneralizationClass.POTENTIALLY_GENERALIZABLE,
    ),
    Observation(
        observation_id="OBS-H4-006", methodology_id="HILTON", source_id=S_H4.source_id,
        source_section="啤殼第一特徵", source_quote_or_paraphrase_reference="集資額越低，越不像真正為業務集資…集資額對過去盈利：只等於一兩年盈利毋須冒上市風險；對上市費用：集資3,300萬費用2,000萬實收1,300萬卻放棄四分一公司，商業上不合理",
        observation_statement="啤殼主篩選：集資額不合理地低。雙比較：(1)集資額≈1-2年盈利 (2)集資額≈上市費用（淨所得相對放棄25%股權不對稱）。正常實業老闆不會為小額資金承受上市監管成本→目的偏向殼價。",
        observation_type=ObservationType.METHOD_PRINCIPLE,
        supporting_evidence="1496集資7,000萬≈過往盈利的案例",
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
    ),
    Observation(
        observation_id="OBS-H4-007", methodology_id="HILTON", source_id=S_H4.source_id,
        source_section="半新股篩選條件", source_quote_or_paraphrase_reference="Top 5或Top 10券商持股其中一項超過九成可先視作90%以上歸邊；CCASS參與者數目下降（100間→90間）代表貨源正在集中；排除內資股/H股",
        observation_statement="半新啤殼篩選七條件：集資額低（主板<1.5億/創板<8,000萬）、市值貼最低要求（5億/1.5億）、Top5或Top10券商持股>90%（初篩法有盲點）、CCASS參與者數目下降（貨源集中中）、成交極低（<50-100萬/日）、橫行≤30%波幅、排除內資股/H股。",
        observation_type=ObservationType.METHOD_PRINCIPLE,
        supporting_evidence="篩選數十隻三年內僅極少數未升一倍的課堂統計",
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
    ),
    Observation(
        observation_id="OBS-H4-008", methodology_id="HILTON", source_id=S_H4.source_id,
        source_section="啤殼時間表/時間壓力", source_quote_or_paraphrase_reference="上市半年禁售→半年至一年可減持不可失控制權→一年後可賣殼；一年半至兩年通常是較容易啟動的區間；超過兩至三年不炒可能班底出問題；三至五年不動不宜再以原模型等待",
        observation_statement="啤殼時間軸：0-6月禁售；6-12月可減持至51%；12月後可賣殼。啟動壓力遞增：半年班底未套現壓力始、一年壓力大、1.5-2年最容易啟動、>2-3年班底問題、3-5年不動=模型失效。股災可把異常時間加回。",
        observation_type=ObservationType.TIMING_RULE,
        supporting_evidence="夜場殼上市一年零三日賣殼（貼最短控制權期限）案例",
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
    ),
    Observation(
        observation_id="OBS-H4-009", methodology_id="HILTON", source_id=S_H4.source_id,
        source_section="啤殼三種走勢", source_quote_or_paraphrase_reference="約少數新股上市時已達95%以上歸邊，上市後立即炒高，風險最大；橫行=九成歸邊等班底，止蝕設於橫行區低位；向下收貨=跌穿招股價令散戶失去耐性，貨源升至九成以上、CCASS參與者由150間降至90多間便具備炒作條件",
        observation_statement="啤殼三走勢對策：(1)即爆型95%+歸邊不追（風險最大）(2)橫行型止蝕於區間低位、跌穿可轉向下收貨 (3)向下收貨型=跌穿招股價折磨散戶收貨，CCASS歸邊>90%+參與者150→90多間即具備炒作條件，啟動日不可測，分散下注等大數定律。",
        observation_type=ObservationType.CONDITION,
        supporting_evidence="三種走勢的分類結構",
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
    ),
    Observation(
        observation_id="OBS-H4-010", methodology_id="HILTON", source_id=S_H4.source_id,
        source_section="損失規避/蟹貨區", source_quote_or_paraphrase_reference="失去一筆錢的痛苦約是獲得同額快樂的兩至二點五倍…大戶若願意在原價接走全部蟹貨，表示其目標更高…剛跌穿一個箱體時不要估底，通常可再跌一至兩個箱體",
        observation_statement="損失規避結構（Prospect Theory 2-2.5倍痛感）：盈利時風險規避早沽、虧損時風險愛好死守→高位形成蟹貨區。返家鄉效應：股價回蟹貨區散戶打和沽出；大戶願全接蟹貨=目標更高。跌穿箱體勿估底（再跌1-2個箱體、每箱橫行6-9月）；高效買點=大戶食清蟹貨並突破後。",
        observation_type=ObservationType.AUTHOR_INTERPRETATION,
        supporting_evidence="Prospect Theory實驗數字+箱體操作規則",
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
    ),
    Observation(
        observation_id="OBS-H4-011", methodology_id="HILTON", source_id=S_H4.source_id,
        source_section="啤殼概念/立基模式", source_quote_or_paraphrase_reference="上市首口價已由自己人控制…數日內推高再一路壓低，利用散戶錨定心理派貨，大股東成本接近零…同一細型保薦人一年完成九隻相似建築股，配合同一法律顧問及走勢",
        observation_statement="立基模式（啤殼派貨）：上市首口價即自己人控制→數日內推高→一路壓低以錨定心理派貨（成本≈零，$10跌至$1派貨仍巨利）。製殼班底可辨認：同一細型保薦人一年九隻相似建築股+同一法律顧問+相似走勢。",
        observation_type=ObservationType.FACT_FROM_CASE,
        supporting_evidence="九隻相似建築股/一年/同一保薦人的班底辨認案例",
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
    ),
]

CHAIN_H4_004 = EvidenceChain(
    chain_id="CHAIN-H4-004", observation_id="OBS-H4-004",
    input_facts=["0607於2008停牌；2010簡志堅以約350萬購舊主36%", "2013削債約3億+舊業務賣回舊主",
                 "Open Offer集資約4,000萬@0.05印約16億股，季昌群包銷取得約52%", "注資約5億地產項目以CB@0.05支付（可換約100億股）"],
    temporal_order="停牌(2008)→購股(2010)→重組建議(2013)→CB兌換→復牌→四年炒至最高$4.5",
    calculation_or_comparison="CB兌換後>90%持股，平均成本約一仙；$0.05復牌=5倍帳面；$4.5=90倍；市值5億→500億",
    author_reasoning="成本約1億級白武士項目必須靠復牌後極高倍數回報；歸邊+歷史客源支撐炒作",
    author_conclusion="『死殼邊有唔炒』：完成九成歸邊重組的白武士項目具有結構性炒作動機",
)

CAND_H4 = [
    RuleCandidate(
        rule_candidate_id="CAND-HILTON-WHITEKNIGHT-CB-001", rule_family=RuleFamily.COST_REPAIR,
        methodology_id="HILTON", rule_name="白武士CB路徑：兌換後>90%歸邊+成本≤一仙=炒作動機判準",
        description="白武士重組經削債→Non-GO→CB注資→兌換後歸邊≥90%、平均成本攤至≤一仙。判準：兌換後歸邊≥90%+商業炒作動機=好項目；六七成歸邊（政府型重組）=不參與。『死殼邊有唔炒』。",
        preconditions=["白武士重組已公布或進行中"],
        required_inputs=["CB條款（換股價/規模）", "兌換後持股比例", "白武士平均成本"],
        optional_inputs=["復牌後市值 vs 殼價", "重組參與者往績"],
        trigger_conditions=["CB兌換完成/復牌事件"],
        supporting_evidence=["OBS-H4-001", "OBS-H4-002", "OBS-H4-004"],
        output_semantics="白武士項目評級：HIGH_MOTIVE(≥90%) / NO_MOTIVE(<90%)",
        false_positive_conditions=["兌換後沽空機構狙擊/市場長期不配合"],
        false_negative_conditions=["歸邊略低但場外暗倉補足"],
        falsification_conditions=["≥90%歸邊白武士樣本群復牌後長期（>5年）無炒作的比例顯著偏高"],
        origin_case_ids=["CASE-HILTON-0607", "CASE-HILTON-0931", "CASE-HILTON-2326", "CASE-HILTON-1220"],
        origin_source_ids=[S_H4.source_id], origin_observation_ids=["OBS-H4-001", "OBS-H4-002"],
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
        dedup_classification=DedupClassification.NEW_RULE,
    ),
    RuleCandidate(
        rule_candidate_id="CAND-HILTON-SHELLFARM-IPO-001", rule_family=RuleFamily.SHELL_VALUE,
        methodology_id="HILTON", rule_name="啤殼篩選：集資額不合理+七條件半新股初篩",
        description="主判準=集資額相對盈利/上市費用不合理地低；輔以七條件（集資低/市值貼底/Top5-10券商>90%/CCASS參與者數下降/日成交<50-100萬/橫行≤30%/排除內資H股）篩出啤殼，小注分散持有，兩年（可放寬三年）時間框架。",
        preconditions=["標的為半新股（上市約半年至一年）"],
        required_inputs=["集資額", "過往盈利", "上市費用", "上市市值", "CCASS Top5/10集中度", "CCASS參與者數序列", "日成交額"],
        optional_inputs=["保薦人往績", "法律顧問/非執董重疊"],
        trigger_conditions=["集資額≈1-2年盈利 或 淨集資≈上市費用"],
        supporting_evidence=["OBS-H4-006", "OBS-H4-007"],
        output_semantics="啤殼嫌疑評分 + 組合配置建議（小注分散幾十隻）",
        false_positive_conditions=["真實小型集資項目", "集資數據不包括同時進行的私人配售"],
        false_negative_conditions=["大額集資型啤殼", "Top10初篩盲點（貨在CCASS以外）"],
        falsification_conditions=["符合篩選的樣本群三年內升幅分佈與隨機半新股無差異"],
        origin_case_ids=["CASE-HILTON-1496"],
        origin_source_ids=[S_H4.source_id], origin_observation_ids=["OBS-H4-006", "OBS-H4-007"],
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
        dedup_classification=DedupClassification.NEW_RULE,
    ),
    RuleCandidate(
        rule_candidate_id="CAND-HILTON-SHELLFARM-TIMING-001", rule_family=RuleFamily.TIMING_RULE if False else RuleFamily.RISK_WINDOW,
        methodology_id="HILTON", rule_name="啤殼啟動時間窗：1.5-2年最易啟動；>3年模型失效",
        description="啤殼時間壓力模型：上市0-6月禁售；6-12月可減持至51%；12月後可賣殼。班底套現壓力遞增→1.5-2年最易啟動；>2-3年=班底問題；3-5年不動=不再以原模型等待。股災期可把異常時間加回。",
        preconditions=["標的已按啤殼篩選入組合"],
        required_inputs=["上市日期"],
        optional_inputs=["上市後市場異常休市期"],
        trigger_conditions=["上市後月齡跨越6/12/18/24/36月界"],
        supporting_evidence=["OBS-H4-008"],
        output_semantics="啟動壓力等級 + 模型失效標記",
        false_positive_conditions=["股災延後被誤判為班底問題"],
        false_negative_conditions=["即爆型（95%歸邊）不受此窗約束"],
        falsification_conditions=["啟動日分佈與2年壓力模型預測無關"],
        origin_case_ids=["CASE-HILTON-夜場殼-一年零三日"],
        origin_source_ids=[S_H4.source_id], origin_observation_ids=["OBS-H4-008"],
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
        dedup_classification=DedupClassification.NEW_RULE,
    ),
    RuleCandidate(
        rule_candidate_id="CAND-HILTON-CCASS-PARTCOUNT-001", rule_family=RuleFamily.CCASS_CONCENTRATION,
        methodology_id="HILTON", rule_name="CCASS參與者數目下降=貨源收集中訊號",
        description="CCASS參與券商數目持續下降（100→90、150→90多間）=持貨券商減少、貨源集中中；與Top5/10集中度互補。參與者數降至低位+歸邊>90%=具備炒作條件（啟動日仍不可測）。",
        preconditions=["有CCASS participant 分佈時間序列"],
        required_inputs=["CCASS參與者數序列", "Top5/10集中度"],
        trigger_conditions=["參與者數持續下降且集中度同步上升"],
        supporting_evidence=["OBS-H4-009", "OBS-H4-007"],
        output_semantics="收集中程度標記：COLLECTING / READY(歸邊>90%+行數低) — 不含啟動時點預測",
        false_positive_conditions=["券商行業整合/退場造成的行數下降"],
        false_negative_conditions=["貨轉入非CCASS途徑（紙股票/場外）"],
        falsification_conditions=["行數下降樣本群與行數穩定樣本群的後續炒作率無差異"],
        origin_case_ids=["CASE-HILTON-向下收貨型"],
        origin_source_ids=[S_H4.source_id], origin_observation_ids=["OBS-H4-009"],
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
        dedup_classification=DedupClassification.NEW_RULE,
    ),
    RuleCandidate(
        rule_candidate_id="CAND-HILTON-CHIP-BREAKOUT-001", rule_family=RuleFamily.CCASS_DISTRIBUTION,
        methodology_id="HILTON", rule_name="蟹貨區：返家鄉沽壓+大戶全接=目標更高；突破後才是買點",
        description="（作者解讀）高位蟹貨區因損失規避鎖死散戶；股價返家鄉時散戶打和沽出——大戶願全接蟹貨=目標更高。高效買點=大戶食清蟹貨並突破確認後，而非下跌途中估底（跌穿箱體常再跌1-2箱、每箱橫行6-9月）。",
        preconditions=["存在明顯歷史高位成交密集區"],
        required_inputs=["歷史價格成交量分佈", "當前價格位置"],
        optional_inputs=["CCASS大戶持股在返家鄉區間的變化"],
        trigger_conditions=["股價重返蟹貨區 / 突破蟹貨區"],
        supporting_evidence=["OBS-H4-010"],
        alternative_explanations=["返家鄉沽壓由指數/被動資金驅動"],
        output_semantics="蟹貨區標記 + 突破確認買點（非預測）",
        false_positive_conditions=["無大戶參與的自然阻力位反彈失敗"],
        false_negative_conditions=["大戶直接在低位收集不經蟹貨區"],
        falsification_conditions=["突破蟹貨區樣本與假突破樣本的後續回報無統計差異"],
        origin_case_ids=[],
        origin_source_ids=[S_H4.source_id], origin_observation_ids=["OBS-H4-010"],
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
        dedup_classification=DedupClassification.NEW_RULE,
    ),
]


def _register_h4(store):
    store.register_source(S_H4)
    for o in OBS_H4:
        store.add_observation(o)
    store.add_observation(OBS_H4[3], CHAIN_H4_004)
    for c in CAND_H4:
        store.add_candidate(c)
    store.mark_source_status(S_H4.source_id, "INGESTED")
    store.save_checkpoint(IngestionCheckpoint(
        source_id=S_H4.source_id,
        processed_sections=["核心觀念", "大市與投資心態", "白武士重組", "六大優勢", "白武士操作方法", "白武士重要案例", "啤殼概念", "啤殼的主要特徵", "啤殼常見行業與班底", "啤殼時間表", "半新股篩選條件", "啤殼三種走勢", "啤殼的時間壓力", "損失規避", "蟹貨區與大戶操作", "注意事項", "本課總結"],
        observation_ids=[o.observation_id for o in OBS_H4],
        candidate_rule_ids=[c.rule_candidate_id for c in CAND_H4],
        open_questions=["殼價數字（主板5-6億/創板8千萬-1億）為課堂時點行情，須外部更新",
                        "『三年內僅極少數未升一倍』為課堂口述統計，無樣本清單"],
        last_position="EOF",
    ))


# ============================================================ HILTON lesson 5
S_H5 = source(
    "HILTON-CAIJI-L5", "財技班第五堂_課程摘要", "分拆上市(介紹/IPO形式/首輪沽壓/買仔唔買乸/0864案例)；向下炒(兩必要條件/四方獲利結構/有集資vs無集資)；大成交意義；1-2-3轉勢法則",
)

OBS_H5 = [
    Observation(
        observation_id="OBS-H5-001", methodology_id="HILTON", source_id=S_H5.source_id,
        source_section="第一輪沽壓", source_quote_or_paraphrase_reference="原股東無償收到子公司股份，第一反應是沽出；基金沽售不符合主題的子公司；沽壓通常不應持續超過兩三個月",
        observation_statement="分拆上市首輪沽壓機制：原股東無償收貨即沽+基金主題不合沽售+子公司的持倉規模不足以支持另聘團隊→策略不是首日追入而是等沽壓完成（通常≤2-3個月）。買仔唔買乸為一般原則（母公司本身是靚殼時例外，0864案例母公司升幅反而更高）。",
        observation_type=ObservationType.TIMING_RULE,
        supporting_evidence="0868分拆0968的基金主題邏輯；0864永利地產案例",
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
    ),
    Observation(
        observation_id="OBS-H5-002", methodology_id="HILTON", source_id=S_H5.source_id,
        source_section="介紹形式", source_quote_or_paraphrase_reference="母公司保留X%，餘下按原股東比例分派；沒有新資金流入；定價過高上市後仍會跌回…因此介紹形式通常偏向定價較低",
        observation_statement="介紹形式分拆結構：無新股東新資金、母公司自行定價→定價偏高會跌回市場價且大股東半年禁售不能套現→介紹形式天然偏向低定價（上市走勢較好）。0864案例：母公司保留17%=公眾持股25%下限下大股東可控制的最高比例，新殼貨源天生乾燥。",
        observation_type=ObservationType.METHOD_PRINCIPLE,
        supporting_evidence="0864一股分一股/保留17%/合計控制75%的數字",
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
    ),
    Observation(
        observation_id="OBS-H5-003", methodology_id="HILTON", source_id=S_H5.source_id,
        source_section="向下炒定義", source_quote_or_paraphrase_reference="股價數年甚至十年長期向下可累跌九成以上+不斷印發大量極低價股票——只有兩者同時存在才是向下炒，不能把普通失敗公司混為一談",
        observation_statement="向下炒兩個必要條件（缺一不可）：(1)股價數年至十年長期向下、累跌>90%且反覆再跌 (2)下跌過程中不斷印發大量極低價股票（配股/供股/CB）。排除向下炒股的價值=避免人生投資損失中可能佔三至五成的重大錯誤。",
        observation_type=ObservationType.METHOD_PRINCIPLE,
        supporting_evidence="宏安系長期反覆合股供股系列；世界級案例11年13次合股供股",
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
    ),
    Observation(
        observation_id="OBS-H5-004", methodology_id="HILTON", source_id=S_H5.source_id,
        source_section="向下炒獲利結構", source_quote_or_paraphrase_reference="若大股東、認購人及資產賣方是同一伙，股票帳面升跌只是內部轉移，真正盈利來自高價出售低成本資產",
        observation_statement="向下炒四方結構：上市公司/大股東→認購人（$0.90配20股付$18）→資產賣方收$18。同伙時股價帳面只是內部轉移；真實盈利=出售價−項目真實成本（高價買入估值彈性大的關連資產：礦業/IT/概念）。散戶承受下跌+攤薄，不在保障結構內。",
        observation_type=ObservationType.METHOD_PRINCIPLE,
        supporting_evidence="配股買資產的$18/20股/三種價位情景數字",
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
    ),
    Observation(
        observation_id="OBS-H5-005", methodology_id="HILTON", source_id=S_H5.source_id,
        source_section="向下炒兩條路/與向上炒比較", source_quote_or_paraphrase_reference="向下炒單次通常賺數千萬至約兩億，但可重複進行，穩定及操作簡單，因此即使牛市，多數財技股仍偏向向下炒",
        observation_statement="向下炒兩路：(1)有集資=印平股派散戶賺集資額 (2)無集資=公司現有資金經高價資產交易轉出。與向上炒比較：向上炒上限無明顯（10億+）但難度最高、股災可全輸；向下炒單次數千萬至2億、可重複、穩定——故多數莊家偏向下炒。",
        observation_type=ObservationType.AUTHOR_INTERPRETATION,
        supporting_evidence="兩條路的風險收益對照",
        generalization_class=GeneralizationClass.POTENTIALLY_GENERALIZABLE,
    ),
    Observation(
        observation_id="OBS-H5-006", methodology_id="HILTON", source_id=S_H5.source_id,
        source_section="成交量的真正意義", source_quote_or_paraphrase_reference="大成交表示兩批人對當前價格極不同意…橫行突破大成交是正面；上升後突然大成交回歸是可能反轉首訊號；極端大成交必須出現在遠離原箱體的極端位置",
        observation_statement="成交量=分歧度量（非買賣力量對比）：突破+大成交=正面（沽盤被承接）；升後大成交回歸=反轉首訊號；下跌途中極端大成交=反對再跌的資金進場（短線見底候選）。位置條件：必須在遠離箱體的極端位置；箱體中間的大成交方向可相反。",
        observation_type=ObservationType.METHOD_PRINCIPLE,
        supporting_evidence="趨勢中三種成交情境",
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
    ),
    Observation(
        observation_id="OBS-H5-007", methodology_id="HILTON", source_id=S_H5.source_id,
        source_section="1-2-3轉勢法則", source_quote_or_paraphrase_reference="向下轉向上三條件：突破下降阻力線→回調形成Higher Low→再突破前高形成Higher High；買入點在第三項，止蝕設於Higher Low下方",
        observation_statement="1-2-3轉勢確認（僅適用成交充足大趨勢，不適用細價財技股）：(1)突破下降阻力線 (2)形成Higher Low (3)突破前高成Higher High=正式確認。買入=第三項時，止蝕=Higher Low下方。買不到最低但買在最確定；股王見頂後等約半年+向下1-2-3才是沽空位。",
        observation_type=ObservationType.CONDITION,
        supporting_evidence="趨勢結構定義（HH/HL vs LH/LL）",
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
    ),
    Observation(
        observation_id="OBS-H5-008", methodology_id="HILTON", source_id=S_H5.source_id,
        source_section="2668 Case Study 方法", source_quote_or_paraphrase_reference="時間表至少十項理想約二十項；人物及股權表追蹤每名主要人物在不同階段的持股變化；所有事件標示在圖上…買入沽出位置必須用當時已知資料解釋，不能以事後最高低位作答案",
        observation_statement="個案研究SOP（2668方法）：分析十倍升浪之前的佈局（追溯至故事完整）；產出三件套=(1)時間表（通告/財技/新聞/資產交易≥10-20項）(2)人物股權表（每人各階段持股）(3)事件標註股價圖。買賣點結論只能用當時已知資料——禁止事後偏差。",
        observation_type=ObservationType.METHOD_PRINCIPLE,
        supporting_evidence="研究任務的三份成果規格",
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
    ),
    Observation(
        observation_id="OBS-H5-009", methodology_id="HILTON", source_id=S_H5.source_id,
        source_section="核心觀念", source_quote_or_paraphrase_reference="小成交不等於出貨。出貨必須有足夠成交量承接，大股東大量持貨不可能在極低成交中完成派發",
        observation_statement="小成交≠出貨：大股東數億至數十億持貨的派發必須有足夠成交量承接；極低成交中的下跌不代表派貨完成。反過來（第三堂）高位買盤充足才是散貨環境。",
        observation_type=ObservationType.METHOD_PRINCIPLE,
        supporting_evidence="與第三堂流動性反訊號互補",
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
    ),
]

CHAIN_H5_004 = EvidenceChain(
    chain_id="CHAIN-H5-004", observation_id="OBS-H5-004",
    input_facts=["市價$1；$0.90配發20股，認購人付$18", "上市公司以$18向資產賣方收購項目", "四方：上市公司/認購人/資產賣方/散戶"],
    temporal_order="配股→付款→收購資產→其後股價自由落體不影響已套現金",
    calculation_or_comparison="$1時20股值$20帳面賺$2；$0.90打和；$0.80蝕$2——但賣方盈利=$18−真實成本，與股價無關",
    author_reasoning="大股東/認購人/賣方同伙時帳面只是內部轉移；散戶承受攤薄+下跌",
    author_conclusion="向下炒的盈利錨在資產交易差價，股價下跌不阻礙獲利——必須永久避開此類結構",
)

CAND_H5 = [
    RuleCandidate(
        rule_candidate_id="CAND-HILTON-DOWNWARD-PLAY-001", rule_family=RuleFamily.CAPITAL_STRUCTURE,
        methodology_id="HILTON", rule_name="向下炒辨識：長期陰跌+反覆印平股兩必要條件→永久避開",
        description="向下炒=股價數年至十年長期向下（累跌>90%反覆再跌）+不斷印發大量極低價股票（配股/供股/CB）兩條件同時成立；盈利結構=同伙人以高價關連資產交易套出公司/散戶資金。辨識後永久避開；股權分散僅加分線索，M歷史仍排第一。",
        preconditions=["有多年價格與資本行動歷史"],
        required_inputs=["長期價格序列（累計跌幅）", "配股/供股/CB歷史序列", "關連資產收購記錄（收購價 vs 後續減值）"],
        optional_inputs=["M過往手法（向上/向下傾向）", "股權分散度"],
        trigger_conditions=["兩必要條件同時成立"],
        supporting_evidence=["OBS-H5-003", "OBS-H5-004", "OBS-H5-005"],
        output_semantics="標記 DOWNWARD_PLAY_SUSPECT / CONFIRMED → 排除名單",
        false_positive_conditions=["普通經營失敗公司（無印股獲利結構）", "白武士拯救前的財困下跌"],
        false_negative_conditions=["單次大型高價關連收購（未及形成長期形態）"],
        falsification_conditions=["被標記公司的關連收購後續表現（減值/回報）與正常公司無差異"],
        origin_case_ids=["CASE-HILTON-1222-宏安系", "CASE-HILTON-1338", "CASE-HILTON-11年13次"],
        origin_source_ids=[S_H5.source_id], origin_observation_ids=["OBS-H5-003", "OBS-H5-004"],
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
        dedup_classification=DedupClassification.NEW_RULE,
    ),
    RuleCandidate(
        rule_candidate_id="CAND-HILTON-SPINOFF-PRESSURE-001", rule_family=RuleFamily.EVENT_SEQUENCE,
        methodology_id="HILTON", rule_name="分拆上市：等首輪沽壓完成（≤2-3月）再評估買仔",
        description="分拆上市後首輪沽壓來自原股東無償沽售+基金主題不合+持倉規模不足；等沽壓完成（通常≤2-3個月）後以子公司為主要對象（買仔唔買乸，母公司本身是靚殼時例外）。介紹形式天然低定價、IPO形式定價較實。",
        preconditions=["分拆上市公告/完成"],
        required_inputs=["分拆形式（介紹/IPO）", "母公司保留比例", "上市日期"],
        optional_inputs=["基金持股分佈", "母公司自身殼股屬性"],
        trigger_conditions=["上市後首2-3個月沽壓期"],
        supporting_evidence=["OBS-H5-001", "OBS-H5-002"],
        output_semantics="沽壓期標記 + 子公司/母公司研究優先級",
        false_positive_conditions=["定價極低或已有承接→沽壓不明顯下跌"],
        false_negative_conditions=["沽壓因市況延長超過3個月"],
        falsification_conditions=["上市首日買入組合的事後回報不差於沽壓後買入"],
        origin_case_ids=["CASE-HILTON-0864", "CASE-HILTON-0868-0968", "CASE-HILTON-1222"],
        origin_source_ids=[S_H5.source_id], origin_observation_ids=["OBS-H5-001", "OBS-H5-002"],
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
        dedup_classification=DedupClassification.NEW_RULE,
    ),
    RuleCandidate(
        rule_candidate_id="CAND-HILTON-VOLUME-DIVERGENCE-001", rule_family=RuleFamily.EVENT_SEQUENCE,
        methodology_id="HILTON", rule_name="大成交=分歧度量：極端位置才可解讀反轉",
        description="成交量量度市場分歧而非買賣力量：突破+大成交正面；趨勢中大成交回歸=反轉首訊號；極端位置（遠離箱體）的極端大成交+急跌=短線見底候選（博1-2日反彈，非趨勢轉好）。箱體中間的大成交不作見底解讀。",
        preconditions=["有日成交量與價格序列"],
        required_inputs=["成交量異常偵測（相對近期均值）", "價格位置（相對箱體）"],
        optional_inputs=["指數層級確認（個股不可套用博反彈）"],
        trigger_conditions=["成交爆量+位置極端"],
        supporting_evidence=["OBS-H5-006"],
        output_semantics="VOLUME_EXTREME標記 + 位置分級 + 建議動作（觀察/短線反彈/反轉候選）",
        false_positive_conditions=["單一大宗交易（對敲/配股交收）造成的量異常"],
        false_negative_conditions=["無量陰跌中的持續派發"],
        falsification_conditions=["極端位置爆量後的1-2日反彈率不顯著高於基準"],
        origin_case_ids=["CASE-HILTON-TQQQ-期權260%"],
        origin_source_ids=[S_H5.source_id], origin_observation_ids=["OBS-H5-006"],
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
        dedup_classification=DedupClassification.NEW_RULE,
    ),
]


def _register_h5(store):
    store.register_source(S_H5)
    for o in OBS_H5:
        store.add_observation(o)
    store.add_observation(OBS_H5[3], CHAIN_H5_004)
    for c in CAND_H5:
        store.add_candidate(c)
    store.mark_source_status(S_H5.source_id, "INGESTED")
    store.save_checkpoint(IngestionCheckpoint(
        source_id=S_H5.source_id,
        processed_sections=["核心觀念", "分拆上市", "分拆的兩種形式", "第一輪沽壓", "分拆股權與案例", "向下炒定義", "向下炒獲利結構", "向下炒兩條路", "向下炒重要案例", "2668 Case Study 方法", "成交量的真正意義", "極端跌市博反彈", "1-2-3轉勢法則", "注意事項", "本課總結"],
        observation_ids=[o.observation_id for o in OBS_H5],
        candidate_rule_ids=[c.rule_candidate_id for c in CAND_H5],
        open_questions=["向下炒單次獲利『數千萬至兩億』為課堂估計", "132X案例為課堂故事，身份未確認，僅作觀察不入案例庫"],
        last_position="EOF",
    ))


# ============================================================ HILTON lesson 6
S_H6 = source(
    "HILTON-CAIJI-L6", "財技班第六堂_課程摘要", "戰役柱判讀；2668 Case Study檢討；炒股食物鏈(散戶/莊家MM/大股東/金主四層角色與制衡)；莊家派系名單法；財演橋樑角色與資訊驗證",
)

OBS_H6 = [
    Observation(
        observation_id="OBS-H6-001", methodology_id="HILTON", source_id=S_H6.source_id,
        source_section="大成交量戰役柱", source_quote_or_paraphrase_reference="若其後升穿戰役柱上方並站穩可視為買方勝出；跌穿下方視為賣方勝出；另一方法是在戰役柱底部附近買入以約2%至3%作止蝕",
        observation_statement="戰役柱判讀：大成交柱=多空激烈交戰位；其後價格站穩柱上方=買方勝（向上操作）、跌穿柱下方=賣方勝（向下操作）；或在柱底買入+2-3%止蝕。大市未完成1-2-3轉勢前主調仍是博反彈。",
        observation_type=ObservationType.CONDITION,
        supporting_evidence="戰役柱三種處理法",
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
    ),
    Observation(
        observation_id="OBS-H6-002", methodology_id="HILTON", source_id=S_H6.source_id,
        source_section="交易紀錄方法", source_quote_or_paraphrase_reference="每次買賣寫下買入原因、投入金額、預期發展、何時及為何沽出；每個因素最少累積七至十個案例才可比較哪個條件更重要，並為不同因素建立分數與數據",
        observation_statement="交易紀錄量化法：每筆記錄買入原因/金額/預期/沽出理由；按原因分類統計成功率；每因素累積7-10案例後建立因素分數與數據。訓練約半年後完整分析可由數小時濃縮至10-20分鐘。",
        observation_type=ObservationType.METHOD_PRINCIPLE,
        supporting_evidence="2668功課檢討流程（官方買點8月8日回報約十倍/另一位置約五倍）",
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
    ),
    Observation(
        observation_id="OBS-H6-003", methodology_id="HILTON", source_id=S_H6.source_id,
        source_section="炒股食物鏈", source_quote_or_paraphrase_reference="莊家不管理上市公司，主要控制買賣、股價、成交量、節奏及盤面…通常向大股東取得一般授權約20%的貨；金主以約五至六成控股權作抵押，還款失敗可接管公司",
        observation_statement="炒股食物鏈四層：散戶（靈活/資訊DE級）→莊家/MM（承接項目、控制盤面造勢、向大股東取得一般授權約20%貨、單項目約兩年賺數千萬至兩三億、致命風險=被大股東反枱出貨）→大股東（定方向選主題、出財技通告、單項可賺百億級、借款數億月息兩三厘）→金主（控股權50-60%抵押借錢、斬倉可接管公司、借款估值按殼價不按炒高市值）。大股東可兼金主；莊家與大股東通常分離。",
        observation_type=ObservationType.METHOD_PRINCIPLE,
        supporting_evidence="四層角色的工作/收益/風險對照",
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
    ),
    Observation(
        observation_id="OBS-H6-004", methodology_id="HILTON", source_id=S_H6.source_id,
        source_section="莊家派系研究", source_quote_or_paraphrase_reference="建立香港莊家派系名單，記錄莊家、相關人物、曾炒股票及背後大股東。每當出現新的十倍股，便查找大股東、人物關係及過往個案…收購、重組、改名及不同公司間的重複人物都是辨認派系的線索",
        observation_statement="莊家派系名單法：每出現新十倍股→查找大股東/人物關係/過往個案→記錄至派系名單；辨認線索=收購、重組、改名、跨公司重複人物；名單隨案例累積，同一批人物多次出現即派系成型。",
        observation_type=ObservationType.METHOD_PRINCIPLE,
        supporting_evidence="1462等分拆殼連續十倍新殼案例",
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
    ),
    Observation(
        observation_id="OBS-H6-005", methodology_id="HILTON", source_id=S_H6.source_id,
        source_section="財演/資訊驗證", source_quote_or_paraphrase_reference="免費且不用付出便取得的資訊先當成可能的陷阱…不要只看『乾』、『靚』、『有勢』等形容詞，要回到持股比例、通告、配股、收購及實際數字",
        observation_statement="資訊驗證原則：免費資訊先當可能陷阱；形容詞（乾/靚/有勢）不可用——必須還原為持股比例/通告/配股/收購等實際數字按財技流程重檢。界定量表差異範例：文章稱70%集中為「乾」，課堂標準要約90%。媒體影響約九成散戶而市場約九成輸錢→主流傳播≠盈利資訊。",
        observation_type=ObservationType.RISK_WARNING,
        supporting_evidence="有牌財演薪酬結構（佣金/銷售而非炒股盈利）與無牌財演被莊家收編路徑",
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
    ),
    Observation(
        observation_id="OBS-H6-006", methodology_id="HILTON", source_id=S_H6.source_id,
        source_section="散戶勝率", source_quote_or_paraphrase_reference="課堂估計一般港股投資者約5%賺、10%打和、85%輸…勝負不是知識的絕對水平，而是相對排名",
        observation_statement="市場勝率結構（課堂估計）：約5%賺/10%打和/85%輸；完成課程後賺錢者約兩成但不輸錢可成多數（避開不適合的操作）。勝負=相對排名（領先約九成人），非絕對知識水平。",
        observation_type=ObservationType.AUTHOR_INTERPRETATION,
        supporting_evidence="課堂經驗估計，非統計研究",
        generalization_class=GeneralizationClass.INSUFFICIENT_EVIDENCE,
    ),
]

CAND_H6 = [
    RuleCandidate(
        rule_candidate_id="CAND-HILTON-FACTION-NETWORK-001", rule_family=RuleFamily.CONTROL_CHANGE,
        methodology_id="HILTON", rule_name="莊家派系名單：跨公司重複人物/收購/重組/改名線索累積",
        description="以新十倍股為觸發，追溯大股東→人物關係→過往個案，累積派系名單（莊家/相關人物/曾炒股票/背後大股東）；辨認線索=跨公司重複人物、收購、重組、改名。名單隨案例生長，同一批人物重複出現即派系確認。",
        preconditions=["存在新十倍股或可疑重複人物"],
        required_inputs=["公司股權披露", "董事/高管名單", "改名與重組歷史", "歷史炒作倍數"],
        optional_inputs=["保薦人/法律顧問重疊（第四堂班底線索）"],
        trigger_conditions=["新十倍股出現 或 同一人物跨公司重複出現"],
        supporting_evidence=["OBS-H6-004"],
        output_semantics="派系圖譜節點/邊 + 人物-公司關聯強度累積",
        false_positive_conditions=["同名不同人（平台已有 IDENTITY_AMBIGUOUS 合約）"],
        false_negative_conditions=["隱身人物（名單有系統性遺漏）"],
        falsification_conditions=["派系關聯預測的後續項目成功率不高於隨機人物組合"],
        origin_case_ids=["CASE-HILTON-1462", "CASE-HILTON-1222-鄧清河"],
        origin_source_ids=[S_H6.source_id], origin_observation_ids=["OBS-H6-004"],
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
        dedup_classification=DedupClassification.NEW_RULE,
    ),
    RuleCandidate(
        rule_candidate_id="CAND-HILTON-ADJECTIVE-DECOMPOSE-001", rule_family=RuleFamily.SCENARIO,
        methodology_id="HILTON", rule_name="形容詞分解：乾/靚/有勢必須還原為量化數字",
        description="任何文字評論（免費資訊尤其）中的形容詞須還原為可驗證數字：「乾」=歸邊約90%（課堂標準；70%不算乾）；「靚」=五因素通過；「有勢」=量價位置符合。免費資訊先當可能陷阱，按財技流程重檢後才可採信。",
        preconditions=["存在文字評論或摘要"],
        required_inputs=["歸邊%數字", "五因素狀態", "量價數據"],
        trigger_conditions=["出現未量化的好淡形容詞"],
        supporting_evidence=["OBS-H6-005"],
        output_semantics="形容詞→量化判準映射表；未通過=UNVERIFIED（不作依據）",
        false_positive_conditions=["數字正確但上下文（如M身份）不同"],
        false_negative_conditions=["評論暗含未寫出的重要條件"],
        falsification_conditions=["此規則僅為內部紀律，不適用傳統證偽——以『還原後數字與文章結論矛盾率』監察"],
        origin_case_ids=[],
        origin_source_ids=[S_H6.source_id], origin_observation_ids=["OBS-H6-005"],
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
        dedup_classification=DedupClassification.NEW_RULE,
    ),
]


def _register_h6(store):
    store.register_source(S_H6)
    for o in OBS_H6:
        store.add_observation(o)
    for c in CAND_H6:
        store.add_candidate(c)
    store.mark_source_status(S_H6.source_id, "INGESTED")
    store.save_checkpoint(IngestionCheckpoint(
        source_id=S_H6.source_id,
        processed_sections=["核心觀念", "市況、情緒與操作", "2668百德國際Case Study", "炒股食物鏈", "散戶", "莊家與操盤手", "大股東", "金主", "莊家派系研究", "財演的角色", "資訊驗證與散戶責任", "本課總結"],
        observation_ids=[o.observation_id for o in OBS_H6],
        candidate_rule_ids=[c.rule_candidate_id for c in CAND_H6],
        open_questions=["5/10/85勝率與單項目獲利區間為口述估計（OBS-H6-006 INSUFFICIENT_EVIDENCE）",
                        "莊家派系名單目前僅有方法，名單本體待平台人物網絡數據累積"],
        last_position="EOF",
    ))


# ============================================================ HILTON lesson 7
S_H7 = source(
    "HILTON-CAIJI-L7", "財技班第七堂_課程摘要", "合股六原因/一合即乾/碎股財技；削股會計本質(488案例)；混合資本重組ABC路線(941/8071)；CCASS主動歸邊計算法(非流通量+券商鴻溝)；高息迷思；達克效應",
)

OBS_H7 = [
    Observation(
        observation_id="OBS-H7-001", methodology_id="HILTON", source_id=S_H7.source_id,
        source_section="合股原因一至三", source_quote_or_paraphrase_reference="一合即乾只表示合股後數日成交減少，實際收貨效果通常只有約2%至3%；碎股價值通常很低…供股可刻意採用令散戶產生碎股的比例回收少量街貨",
        observation_statement="合股六原因前三：(1)減流通量——『一合即乾』僅數日盤面效應，實際收貨約2-3%（遠低於一般授權20%）非主要用途 (2)製造碎股——碎股難沽價差被迫長留，供股比例可刻意設計碎股回收街貨；碎股≠零碎股份（不足一手vs不足一股）(3)攤薄——非整除比例小數股處理，效果通常不大。",
        observation_type=ObservationType.METHOD_PRINCIPLE,
        supporting_evidence="3合1→1.67股實剩1股的攤薄例子",
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
    ),
    Observation(
        observation_id="OBS-H7-002", methodology_id="HILTON", source_id=S_H7.source_id,
        source_section="合股原因四至六", source_quote_or_paraphrase_reference="接近一仙的股票宣布合股，若真想向上本可直接炒升，毋須合股；合股通常反映它要走向下路線…吸引基金是唯一較正面的合股理由，但實際案例比例很低",
        observation_statement="合股六原因後三：(4)增加向下空間——最低報價一仙，合股重製下跌空間（100合1：一仙→一元再跌90%+）；接近一仙宣布合股=向下路線結構性訊號，極差評級應離場 (5)重新印平股——配股價不能低於面值，合股抬高面值後配合削股恢復大折讓印股（1492：40合1+1供5+送紅股） (6)吸引基金——合至兩位數股價符合基金最低股價要求，唯一較正面理由但比例極低；不懂分辨先當負面。",
        observation_type=ObservationType.CONDITION,
        supporting_evidence="1492同一通告40合1→1供5→送紅股的結構判讀",
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
    ),
    Observation(
        observation_id="OBS-H7-003", methodology_id="HILTON", source_id=S_H7.source_id,
        source_section="削減股本/488案例", source_quote_or_paraphrase_reference="削股只是會計財技，以減少股本抵銷累計虧損…獨立削股通常出現在由虧轉盈準備重新派息的階段；488中標翌日削股$57億≈累計虧損$56.95億，17年從未削股今次立即清掉",
        observation_statement="削股會計本質：以減股本抵銷累計虧損，恢復派息能力（派息取決於累計盈利非現金）；不創造/毀滅現金。獨立削股=轉盈訊號（其後常有特別股息）；488麗新發展：中標酒店翌日削股$57億≈累虧$56.95億，讀取管理層真實信心，等其後2供1供股訊號完成再入場，約賺50%。財技賺預期差，不等項目落成驗證。",
        observation_type=ObservationType.METHOD_PRINCIPLE,
        supporting_evidence="四年會計數字序列（股本/累計盈利/真實資金）+488案例金額對應",
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
    ),
    Observation(
        observation_id="OBS-H7-004", methodology_id="HILTON", source_id=S_H7.source_id,
        source_section="混合資本重組ABC", source_quote_or_paraphrase_reference="8071重組後未發行股份由108億增至190.8億股，由原本不足1印1.5變成可約1印20；合股、削股與拆細未發行股份把向下炒威力合共放大約2,000倍；見到這種通告應立即離場",
        observation_statement="混合資本重組三路線：A只合股（向下空間×10，但面值升限制折讓）→B+削股（面值削回，折讓×10，威力×100；941：合股→削股→更改買賣單位→1供4折讓74%）→C+拆細未發行股份（可印股數暴增；注意『未發行』三字）。8071：10合1+削股+拆細→可印1:20，合共威力約2,000倍=立即離場。通告次序有意義：先合股削股才有條件極折讓供股。",
        observation_type=ObservationType.METHOD_PRINCIPLE,
        supporting_evidence="8071法定股本/面值/已發行/未發行的完整數字鏈（含百慕達註冊免法院審批細節）",
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
    ),
    Observation(
        observation_id="OBS-H7-005", methodology_id="HILTON", source_id=S_H7.source_id,
        source_section="616案例", source_quote_or_paraphrase_reference="若在2003年沙士低位投入六千多萬元，至2014年可只剩約一元。期間經歷九次合股、一次送股及十四次供股…損失是反覆下跌九成的複利結果",
        observation_statement="616向下炒紀錄級案例：2003-2014經歷九次合股+一次送股+十四次供股，沙士低位六千多萬→約一元；損失=反覆-90%的複利。大老闆不會用相同手法破壞核心旗艦，卻可在二三線細價股向下炒；散戶最實際策略=識別結構避開（不便隨意沽空）。",
        observation_type=ObservationType.FACT_FROM_CASE,
        supporting_evidence="九合股/一送股/十四供股的完整序列計數",
        generalization_class=GeneralizationClass.POTENTIALLY_GENERALIZABLE,
    ),
    Observation(
        observation_id="OBS-H7-006", methodology_id="HILTON", source_id=S_H7.source_id,
        source_section="貨源歸邊主動方法", source_quote_or_paraphrase_reference="把非CCASS部分先視為M/大股東貨；把CCASS參與者按持股排列找由0.2%突跳至2%或8%的鴻溝，界線以下為散戶街貨；75%實體股+CCASS內行15%≈90%歸邊；91%與98%對策略沒有實質分別",
        observation_statement="CCASS主動歸邊計算法（雙法）：(1)非CCASS流通量——總股本−CCASS=實體股，先全數視為M貨（散戶實體股日後存回CCASS會現異動） (2)券商持股鴻溝——持倉排序找數量級跳升斷層（0.2%→2%/8%），斷層以下=街貨、以上=M貨。總歸邊=非CCASS+CCASS大行。精度要求：>90%即足夠（91% vs 98%無策略差異）。被動法（股權高度集中通告）精確但滯後。",
        observation_type=ObservationType.METHOD_PRINCIPLE,
        supporting_evidence="70%/8%/6%/3%/2%/0.1%/0.01%的分佈例子及75%+15%=90%計算",
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
    ),
    Observation(
        observation_id="OBS-H7-007", methodology_id="HILTON", source_id=S_H7.source_id,
        source_section="CCASS輔助判斷", source_quote_or_paraphrase_reference="只看Top 5或Top 10有盲點，因同一莊家可把貨分散在六七間券商；高盛摩根等大行通常偏向M或大戶持倉；匯豐一通渣打等零售行較偏向街貨。這只是輔助線索，不可只按券商名字下結論",
        observation_statement="CCASS券商類型輔助：Top5/10法有盲點（同一莊家可分散六七間行）；外資大行（高盛/摩根）偏M或大戶持倉、零售行（匯豐/一通/渣打）偏街貨——僅輔助線索，須配合鴻溝與比例。CCASS基本限制：只認券商不認個人、T+2/3交收、實體股OTC不影響場內報價。",
        observation_type=ObservationType.AUTHOR_INTERPRETATION,
        supporting_evidence="券商分類的經驗性對照",
        generalization_class=GeneralizationClass.POTENTIALLY_GENERALIZABLE,
    ),
    Observation(
        observation_id="OBS-H7-008", methodology_id="HILTON", source_id=S_H7.source_id,
        source_section="股價心理與入場費", source_quote_or_paraphrase_reference="財技股常在毫子區啟動並非偶然，而是按散戶最願意接貨的價格倒推設計；新股若刻意把每手入場費設至約兩萬元，可在上市之初篩走大量散戶，減少日後收貨需要",
        observation_statement="派貨價位設計：散戶心理舒適區=幾元股（毫子股顯危險、幾百元顯貴）→莊家目標升十倍時布局買入區常設幾毫子。每手入場費亦是篩選工具：低入場費吸弱手（內銀長年橫行）、高入場費（約兩萬）上市初篩走散戶減收貨需要。",
        observation_type=ObservationType.AUTHOR_INTERPRETATION,
        supporting_evidence="內銀vs騰訊/一號仔的股東結構對照",
        generalization_class=GeneralizationClass.POTENTIALLY_GENERALIZABLE,
    ),
]

CHAIN_H7_004 = EvidenceChain(
    chain_id="CHAIN-H7-004", observation_id="OBS-H7-004",
    input_facts=["8071法定股本$2億/面值$0.01/最多可發行200億股/已發行92億/未發行108億",
                 "10合1後面值$0.10、最多20億、已發行9.2億", "削股+拆細未發行後面值$0.01、最多200億、已發行仍9.2億"],
    temporal_order="轉百慕達註冊（免法院審批）→10合1→削股→拆細未發行→其後可極折讓供股",
    calculation_or_comparison="未發行=200−9.2=190.8億股；印股能力由1:1.5→1:20；向下空間×10×折讓×10×印股×10≈威力×2,000",
    author_reasoning="三步組合的每一部份都有獨立通告依據，次序不可倒轉（先合股削股才有條件極折讓）",
    author_conclusion="見到ABC混合重組通告=向下炒終極結構，立即離場",
)

CAND_H7 = [
    RuleCandidate(
        rule_candidate_id="CAND-HILTON-CONSOL-INTENT-001", rule_family=RuleFamily.SHARE_CONSOLIDATION,
        methodology_id="HILTON", rule_name="合股意圖判讀：貼一仙合股=向下路線極差評級",
        description="合股六原因判讀（減流通/碎股/攤薄/加向下空間/重印平股/吸基金），以四、五為主導：股價接近一仙宣布合股=結構性向下訊號（極差、離場）；合股後配供股（合不離供）=印平股前奏；合至兩位數+獨立正面證據才可考慮吸基金解讀（比例極低，不懂分辨先當負面）。",
        preconditions=["合股公告已發布"],
        required_inputs=["合股比例", "公告時股價（相對一仙距離）", "其後通告序列（供股/CB）"],
        optional_inputs=["基金持股結構", "M身份"],
        trigger_conditions=["合股公告"],
        supporting_evidence=["OBS-H7-001", "OBS-H7-002"],
        output_semantics="合股意圖分類：DOWNWARD_RELOAD(貼仙) / REPRINT_PRELUDE(前後有供股) / FUND_FACING(兩位數+獨立證據) / NEGATIVE_DEFAULT",
        false_positive_conditions=["兩位數合股確為吸基金而誤判負面（比例低）"],
        false_negative_conditions=["已乾殼的高位合股（罕見）"],
        falsification_conditions=["貼一仙合股樣本群的後續表現不差於一般仙股"],
        origin_case_ids=["CASE-HILTON-1492", "CASE-HILTON-天行國際"],
        origin_source_ids=[S_H7.source_id], origin_observation_ids=["OBS-H7-001", "OBS-H7-002"],
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
        dedup_classification=DedupClassification.NEW_RULE,
    ),
    RuleCandidate(
        rule_candidate_id="CAND-HILTON-CAPREORG-MAGNITUDE-001", rule_family=RuleFamily.SHARE_CONSOLIDATION,
        methodology_id="HILTON", rule_name="混合資本重組威力計算：ABC組合=立即離場",
        description="計算混合重組（合股+削股+拆細未發行股份）的向下威力倍數：向下空間放大×配股折讓放大×可印股數放大。威力≥100倍（B路線級）已屬極端；約2,000倍（8071型）=立即離場。注意通告『未發行』三字與通告次序邏輯。",
        preconditions=["資本重組公告含≥2項工具組合"],
        required_inputs=["合股比例", "削股前後面值", "拆細比例", "法定/已發行/未發行股數（月報表核對）"],
        optional_inputs=["註冊地（百慕達免法院審批加速）"],
        trigger_conditions=["公告序列：合股→削股→(拆細未發行)→供股"],
        supporting_evidence=["OBS-H7-004", "OBS-H7-003"],
        output_semantics="威力倍數估算 + 離場/迴避指令",
        false_positive_conditions=["重組後實際走白武士/向上路線（罕見例外）"],
        false_negative_conditions=["分多次通告逐步執行，單看一次公告低估"],
        falsification_conditions=["高威力重組標記的樣本群後續回升率不低於對照組"],
        origin_case_ids=["CASE-HILTON-8071", "CASE-HILTON-941", "CASE-HILTON-616"],
        origin_source_ids=[S_H7.source_id], origin_observation_ids=["OBS-H7-004"],
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
        dedup_classification=DedupClassification.NEW_RULE,
    ),
    RuleCandidate(
        rule_candidate_id="CAND-HILTON-CCASS-DRYNESS-CALC-001", rule_family=RuleFamily.CCASS_CONCENTRATION,
        methodology_id="HILTON", rule_name="CCASS主動歸邊計算：非CCASS全記M貨+券商鴻溝斷層法",
        description="歸邊%=（非CCASS股份全額+CCASS內鴻溝以上大行持倉）/總股本。非CCASS=總股本−CCASS總量（先全視為M貨，實體股回存會現異動）；鴻溝=持倉排序中由散戶級(≤0.2%)跳升至大戶級(≥2%)的數量級斷層。精度：>90%即足夠（91%vs98%無策略差異）。Top5/10法僅初篩（同莊可散六七間行）。",
        preconditions=["有CCASS participant持股快照", "有總已發行股數"],
        required_inputs=["CCASS總量/總股本比", "participant持股排序"],
        optional_inputs=["券商類型標籤（外資大行vs零售行）", "歷史快照序列"],
        trigger_conditions=["日常歸邊監察"],
        supporting_evidence=["OBS-H7-006", "OBS-H7-007"],
        output_semantics="歸邊%估算 + 鴻溝界線位置 + HIGH(>90%)/MEDIUM/LOW分級",
        false_positive_conditions=["散戶實體股被全記M貨（少量高估）", "外資行持倉實為託管客戶而非M"],
        false_negative_conditions=["貨藏於場外OTC/衍生工具對沖倉"],
        falsification_conditions=["鴻溝法估算與後續官方『股權高度集中』通告披露值系統性背離"],
        origin_case_ids=["CASE-HILTON-75-15-90例"],
        origin_source_ids=[S_H7.source_id], origin_observation_ids=["OBS-H7-006", "OBS-H7-007"],
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
        dedup_classification=DedupClassification.NEW_RULE,
    ),
    RuleCandidate(
        rule_candidate_id="CAND-HILTON-CUTPAR-POSITIVE-001", rule_family=RuleFamily.CAPITAL_STRUCTURE,
        methodology_id="HILTON", rule_name="獨立削股=轉盈恢復派息訊號（對比混合重組）",
        description="單獨出現的削減股本（不與合股/拆細並列）=管理層讀取訊號：清累虧恢復派息能力，預示轉盈/特別股息。加權訊號=削股金額≈累計虧損金額+發生在重大正面事件（中標/新項目）同期。其後供股完成為入場確認（488模式）。",
        preconditions=["削股公告獨立出現"],
        required_inputs=["削股金額", "當期累計虧損", "同期公司事件", "其後資本行動序列"],
        trigger_conditions=["削股金額≈累計虧損且無合股/拆細伴隨"],
        supporting_evidence=["OBS-H7-003"],
        output_semantics="POSITIVE_RESTRUCTURE標記 + 等待確認（其後供股/派息公告）",
        false_positive_conditions=["為後續向下炒鋪路的『先轉盈』假象"],
        false_negative_conditions=["削股與混合工具同月公告（應走威力計算規則）"],
        falsification_conditions=["獨立削股樣本群其後特別股息/盈利改善率不顯著高於對照"],
        origin_case_ids=["CASE-HILTON-488"],
        origin_source_ids=[S_H7.source_id], origin_observation_ids=["OBS-H7-003"],
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
        dedup_classification=DedupClassification.NEW_RULE,
    ),
]


def _register_h7(store):
    store.register_source(S_H7)
    for o in OBS_H7:
        store.add_observation(o)
    store.add_observation(OBS_H7[3], CHAIN_H7_004)
    for c in CAND_H7:
        store.add_candidate(c)
    store.mark_source_status(S_H7.source_id, "INGESTED")
    store.save_checkpoint(IngestionCheckpoint(
        source_id=S_H7.source_id,
        processed_sections=["核心觀念", "合股", "股價心理與入場費", "獨立合股策略", "拆股", "削減股本", "488麗新發展案例", "混合資本重組", "向下炒案例", "CCASS中央結算系統", "貨源歸邊分析", "個股課堂跟進", "高息股迷思", "公司質素與派息決策", "達克效應", "本課總結"],
        observation_ids=[o.observation_id for o in OBS_H7],
        candidate_rule_ids=[c.rule_candidate_id for c in CAND_H7],
        open_questions=["券商鴻溝界線（0.2%→2%）為經驗值，實作須按個股持倉分佈自適應",
                        "券商類型標籤（外資大行=M偏）須以本站134k行持倉數據獨立驗證"],
        last_position="EOF",
    ))


# ============================================================ HILTON lesson 8
S_H8 = source(
    "HILTON-CAIJI-L8", "財技班第八堂_課程摘要", "CCASS兩大異動(實物存入CCASS In/射倉)；收貨格出貨格；DI三大盲點；七大出貨信號；震倉目的與30/50/70%界線；市值與升幅天花板；坐貨與推高保護位",
)

OBS_H8 = [
    Observation(
        observation_id="OBS-H8-001", methodology_id="HILTON", source_id=S_H8.source_id,
        source_section="CCASS兩大異動", source_quote_or_paraphrase_reference="實物存入代表股份已具備沽售條件…高位存入偏派貨、低位存入可能先炒高再派貨；5%為值得留意水平，10%以上較有幅度；射倉不只一次且可能愈來愈頻密，頻密程度增加代表部署可能愈接近啟動",
        observation_statement="CCASS In判讀：實物股票存入=股份取得市場沽售條件的高指向性訊號；位置決定路徑（高位存入→偏派貨；低位存入→可能先炒高再派貨，兩者終點同為沽售）；比例門檻=5%留意、10%+有幅度，低位大量存入對應更大炒高空間、高位大量存入對應更大下跌風險。射倉=大手單宗跨行轉移，通常多次且頻密化=部署接近啟動；方向不可由單次射倉判斷（可為交貨予莊家/人頭轉移/層級分配）。",
        observation_type=ObservationType.METHOD_PRINCIPLE,
        supporting_evidence="124十倍前跨三行連續射倉；309世達3.3%金利豐→金英的雙向對照",
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
    ),
    Observation(
        observation_id="OBS-H8-002", methodology_id="HILTON", source_id=S_H8.source_id,
        source_section="CCASS圖形", source_quote_or_paraphrase_reference="收貨格=主要行持倉持續增加其他分散下降；出貨格=主要行下降分散增加…直觀出貨格約只在少部分個案出現，不能因看不到圖形便認定沒有派貨。『乾』真正指交投疏落排盤穿窿；『貨源集中』指股份集中一方——兩者經常同時出現但不能混為一談",
        observation_statement="收貨格/出貨格定義及局限：主要行 vs 分散倉的持倉走向判圖；清晰圖形僅少部分個案出現（1106屬十中無一的清晰案例）——看不到圖形≠無派貨。「乾」（交投疏落排盤穿窿）與「貨源集中」（股份歸邊）是兩個概念，不可混用。",
        observation_type=ObservationType.METHOD_PRINCIPLE,
        supporting_evidence="1106股災中倍數升幅的收貨格案例；全配售散貨圖案例（模式已過時）",
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
    ),
    Observation(
        observation_id="OBS-H8-003", methodology_id="HILTON", source_id=S_H8.source_id,
        source_section="DI三個盲點", source_quote_or_paraphrase_reference="DI顯示超過100%通常與期權或CB以股份數量申報有關；配偶、受控公司與實益擁有人可能就同一批股份重複申報，不能直接相加；供股包銷商短暫被視為大量持股，不等於真正入主",
        observation_statement="DI三大盲點：(1)>100%持股=衍生工具（期權/CB）按股份數量申報的假象 (2)配偶/受控公司/實益擁有人同一批股份重複申報——百分比不可直接相加 (3)供股包銷商及其大股東短暫大量持股≠入主，供股股份出爐後權益可能消失。董事/CEO一股變動亦須申報；>5%人士須披露。",
        observation_type=ObservationType.RISK_WARNING,
        supporting_evidence="DI制度結構說明",
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
    ),
    Observation(
        observation_id="OBS-H8-004", methodology_id="HILTON", source_id=S_H8.source_id,
        source_section="七大出貨信號", source_quote_or_paraphrase_reference="散貨財技連續兩次通常已足夠離場；正常散貨約10%-20%、極端上限約40%…升十倍沽約10%、升一百倍沽約1%，升幅越高微小減持也不能忽視；第三次震倉已接近極限；大成交是最簡單直接快速的出貨信號，有時即使沒有其他信號亦要離場",
        observation_statement="七大出貨信號（程度+次數+組合判讀）：(1)散貨財技（合股/拆股/送紅股）——一次留意、兩次通常足夠離場，不等第三次 (2)DI大股東減持程度——首次減持提高警覺 (3)CCASS出貨10-20%正常、上限約40%——莊家毋須散清：升10倍沽10%、升100倍沽1%即回本，升幅越高微小減持越致命 (4)震倉1-2次正常、第三次近極限；震倉縮量vs散貨大成交 (5)高位買入發水資產（1332：1億現金買9,000萬4%無控制權股）(6)媒體大幅曝光（1246：升5倍後連兩週3-4頁報道→再升至10倍完) (7)大成交——最直接，細市值股以實際成交金額衡量（2億市值日沽5,000萬+3,000萬=散貨已足），一分鐘圖分辨射倉vs零散承接。",
        observation_type=ObservationType.METHOD_PRINCIPLE,
        supporting_evidence="124/1246/1332/大成交市值換算案例",
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
    ),
    Observation(
        observation_id="OBS-H8-005", methodology_id="HILTON", source_id=S_H8.source_id,
        source_section="震倉真正目的", source_quote_or_paraphrase_reference="主要目的是提高場內散戶的平均持貨成本…高成本散戶因損失規避不願止蝕，派貨更順利。一般震倉約30%，強烈可達50%；超過70%已不是正常震倉而是炒散咗個盤",
        observation_statement="震倉目的=提高散戶平均持貨成本（非收平貨——貨源已歸邊時無平貨可收）；高成本持貨者損失規避被鎖死→派貨少競爭。幅度界線：正常≈30%、強烈≈50%、>70%=盤已散（炒散咗），信心受損散戶不回。未回升前不可事後斷言是震倉。",
        observation_type=ObservationType.AUTHOR_INTERPRETATION,
        supporting_evidence="與損失規避（L4）及錨定（L1）的理論閉環",
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
    ),
    Observation(
        observation_id="OBS-H8-006", methodology_id="HILTON", source_id=S_H8.source_id,
        source_section="升幅與風險天花板", source_quote_or_paraphrase_reference="主板市值天花板約100億、創業板約20億；一般升至三至四倍便要非常小心，因莊家可能已達零成本狀態；一般市況下多以三至四倍作警戒區",
        observation_statement="天花板規則：市值天花板=主板約100億/創業板約20億（再升性價比降而下跌空間大）；升幅警戒=3-4倍（莊家近零成本）。估算升幅四因素：莊家胃口/賣殼vs炒股/乾度/市況——僅作警覺估算非目標價。",
        observation_type=ObservationType.CONDITION,
        supporting_evidence="莊家成本結構（L6單項目數千萬至兩三億）對照",
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
    ),
    Observation(
        observation_id="OBS-H8-007", methodology_id="HILTON", source_id=S_H8.source_id,
        source_section="異動辨識與核對", source_quote_or_paraphrase_reference="若異動由供股除權、新股出爐等公司行動造成，屬假異動，不當作大股東主動存入或沽貨；CCASS有T+3延遲，最近三天實際變化無法即時看見…以即日盤路作補充",
        observation_statement="假異動排除規則：供股除權/新股出爐/股本變動造成的持倉%突變=機制性假異動，不作收貨/出貨解讀。CCASS T+3延遲→最近三日變化不可即見，急跌一兩日內的場景須以即日盤路補充；人頭戶不可辨認，只能以一致方法降低誤差。",
        observation_type=ObservationType.RISK_WARNING,
        supporting_evidence="操作流程第4-5步的核對程序",
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
    ),
    Observation(
        observation_id="OBS-H8-008", methodology_id="HILTON", source_id=S_H8.source_id,
        source_section="操作流程 持倉管理", source_quote_or_paraphrase_reference="升一倍後可收回本金；到三倍時一定要零成本…觸及天花板後可每日把保護位推至當日最低位，其後跌穿前一日低位便離場",
        observation_statement="持倉紀律：無出貨信號時坐貨（避免小升即走）；升一倍收回本金；三倍必達零成本；天花板區用推高保護位（每日保護位=當日最低，跌穿前一日低位即離場）。下跌時按紀律止蝕，上升未見出貨才保留氣魄。",
        observation_type=ObservationType.TIMING_RULE,
        supporting_evidence="坐貨與推高保護位的操作規則",
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
    ),
]

CHAIN_H8_004 = EvidenceChain(
    chain_id="CHAIN-H8-004", observation_id="OBS-H8-004",
    input_facts=["莊家集中貨源>90%", "正常散貨量10-20%，極端上限約40%", "個案：升十倍沽約10%、升百倍沽約1%已回本"],
    temporal_order="出貨信號先於價格崩跌；DI減持→CCASS分散→大成交的常見序列",
    calculation_or_comparison="升幅×沽出比例=套現額；升幅越高，套現所需沽出比例越小——微小CCASS減持在高位即致命",
    author_reasoning="莊家毋須散清九成貨；以獲利倍數反推所需最小沽出量",
    author_conclusion="CCASS出貨判讀必須以升幅校準敏感度，不能以固定比例為安全閾",
)

CAND_H8 = [
    RuleCandidate(
        rule_candidate_id="CAND-HILTON-CCASSIN-POSITION-001", rule_family=RuleFamily.CCASS_TRANSFER,
        methodology_id="HILTON", rule_name="CCASS In位置判讀：高位存入偏派貨、低位存入先炒後派",
        description="實物存入CCASS=沽售條件成立的指向性訊號；判讀必先定價格位置：高位存入→派貨風險；低位大量存入→可能先炒高再派貨（對應更大炒高空間與後續派貨）。門檻：≥5%留意、≥10%強。屬風險定位訊號，非買賣指令。",
        preconditions=["CCASS快照序列顯示新增存入"],
        required_inputs=["存入者身份（是否只能是大股東）", "存入比例", "當前價格位置（週期高位/低位）"],
        optional_inputs=["存入頻率", "隨後射倉序列"],
        trigger_conditions=["單次或累計存入≥5%"],
        supporting_evidence=["OBS-H8-001"],
        output_semantics="CCASS_IN標記 + 位置分級(LOW→WATCH_FOR_MARKUP / HIGH→DISTRIBUTION_RISK)",
        false_positive_conditions=["假異動：供股除權/新股出爐的機制性變化（必須先排除）"],
        false_negative_conditions=["分批小額存入累計"],
        falsification_conditions=["高位存入樣本群其後派發率不顯著高於對照"],
        origin_case_ids=[],
        origin_source_ids=[S_H8.source_id], origin_observation_ids=["OBS-H8-001"],
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
        dedup_classification=DedupClassification.NEW_RULE,
    ),
    RuleCandidate(
        rule_candidate_id="CAND-HILTON-7SIGNALS-EXIT-001", rule_family=RuleFamily.CCASS_DISTRIBUTION,
        methodology_id="HILTON", rule_name="七大出貨信號掃描器（程度×次數×組合）",
        description="出貨判斷掃描七信號：散貨財技(2次即足)/DI減持(程度)/CCASS出貨(10-20%正常、40%上限、以升幅校準敏感度：升幅越高微小減持越致命)/震倉(第三次近極限；縮量vs散貨大成交)/發水資產/媒體大幅曝光/大成交(細市值股用實際金額+一分鐘圖分辨射倉vs承接)。單一輕微訊號不作結論；大成交可單獨觸發離場。",
        preconditions=["持有或監察財技股"],
        required_inputs=["財技通告序列", "DI序列", "CCASS持倉序列", "成交量（含分鐘級）", "媒體曝光（人工）"],
        optional_inputs=["市值對照天花板"],
        trigger_conditions=["任一信號出現→按程度計分；大成交→可直接觸發"],
        supporting_evidence=["OBS-H8-004", "OBS-H8-006"],
        output_semantics="出貨風險評分（0-7信號×強度）+ 建議動作",
        false_positive_conditions=["市場系統性下跌被誤計為個股出貨"],
        false_negative_conditions=["場外/暗倉派發不經七信號"],
        falsification_conditions=["七信號計分與事後30日回撤無統計相關"],
        origin_case_ids=["CASE-HILTON-124", "CASE-HILTON-1246", "CASE-HILTON-1332"],
        origin_source_ids=[S_H8.source_id], origin_observation_ids=["OBS-H8-004"],
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
        dedup_classification=DedupClassification.NEW_RULE,
    ),
    RuleCandidate(
        rule_candidate_id="CAND-HILTON-DI-ARTIFACT-001", rule_family=RuleFamily.CONTROL_CHANGE,
        methodology_id="HILTON", rule_name="DI三大盲點排除：>100%/重複申報/包銷商假持股",
        description="DI解讀前置排除：(1)>100%=衍生工具股份制申報假象 (2)配偶/受控公司/實益擁有人同一批股份重複申報——不可相加 (3)供股包銷商短暫大量持股≠入主。排除後才評估真實增減持程度。",
        preconditions=["DI申報序列"],
        required_inputs=["申報方身份關係", "申報性質（股份/衍生工具/權益種類）", "事件類型（是否供股包銷）"],
        trigger_conditions=["DI出現異常值（>100%、多人同批股、包銷事件期）"],
        supporting_evidence=["OBS-H8-003"],
        output_semantics="DI_RECORD標記 + ARTIFACT_SUSPECTED旗（不可計入真實持股）",
        false_positive_conditions=["規則本身錯殺真實增持（需人工複核）"],
        false_negative_conditions=["未申報的場外權益"],
        falsification_conditions=["被標記artifact的申報事後證實為真實持股變動的比例偏高"],
        origin_case_ids=[],
        origin_source_ids=[S_H8.source_id], origin_observation_ids=["OBS-H8-003"],
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
        dedup_classification=DedupClassification.NEW_RULE,
    ),
    RuleCandidate(
        rule_candidate_id="CAND-HILTON-FAKE-MOVE-EXCLUDE-001", rule_family=RuleFamily.CCASS_TRANSFER,
        methodology_id="HILTON", rule_name="假異動排除：公司行動造成的CCASS持倉%突變",
        description="供股除權/新股出爐/股本變動/供股權過戶造成的持倉百分比突變=機制性假異動；須與公司行動日曆核對後排除，不作收貨/出貨解讀。配合T+3結算延遲：觀察窗口計算須容忍最近三日不可見。",
        preconditions=["CCASS持倉出現突變"],
        required_inputs=["公司行動日曆（除權日/生效日/結果日）", "CCASS突變日期"],
        trigger_conditions=["突變日±窗口內有公司行動"],
        supporting_evidence=["OBS-H8-007"],
        output_semantics="MECHANICAL_ARTIFACT標記（排除）vs GENUINE_MOVE（保留）",
        false_positive_conditions=["公司行動與真實派貨恰好同期"],
        false_negative_conditions=["非典型公司行動造成的突變未被日曆涵蓋"],
        falsification_conditions=["被排除的假異動中人工複核證實含真實派發的比例偏高"],
        origin_case_ids=[],
        origin_source_ids=[S_H8.source_id], origin_observation_ids=["OBS-H8-007"],
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
        dedup_classification=DedupClassification.NEW_RULE,
    ),
    RuleCandidate(
        rule_candidate_id="CAND-HILTON-CEILING-GUARD-001", rule_family=RuleFamily.RISK_WINDOW,
        methodology_id="HILTON", rule_name="天花板與推高保護位：市值100億/20億、升幅3-4倍警戒",
        description="風險天花板：主板市值≈100億、創業板≈20億；升幅3-4倍=莊家近零成本警戒區（即使無出貨信號亦加強風管）。持倉管理：升一倍收回本金、三倍必零成本；天花板區每日保護位=當日最低，跌穿前一日低位即離場。",
        preconditions=["已持倉財技股"],
        required_inputs=["當前市值", "入場後升幅倍數", "每日最低價序列"],
        optional_inputs=["出貨信號掃描結果"],
        trigger_conditions=["市值/升幅觸及天花板 或 每日滾動保護位被跌穿"],
        supporting_evidence=["OBS-H8-006", "OBS-H8-008"],
        output_semantics="天花板警告 + 動態保護位（trailing stop）值",
        false_positive_conditions=["大市整體升幅推動的市值膨脹（如指數牛市）"],
        false_negative_conditions=["突破天花板的超級項目（0530型3000億——罕見）"],
        falsification_conditions=["3-4倍警戒離場策略的事後總回報顯著劣於持有至出貨信號"],
        origin_case_ids=["CASE-HILTON-0530（反例）"],
        origin_source_ids=[S_H8.source_id], origin_observation_ids=["OBS-H8-006", "OBS-H8-008"],
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
        dedup_classification=DedupClassification.NEW_RULE,
    ),
]


def _register_h8(store):
    store.register_source(S_H8)
    for o in OBS_H8:
        store.add_observation(o)
    store.add_observation(OBS_H8[3], CHAIN_H8_004)
    for c in CAND_H8:
        store.add_candidate(c)
    store.mark_source_status(S_H8.source_id, "INGESTED")
    store.save_checkpoint(IngestionCheckpoint(
        source_id=S_H8.source_id,
        processed_sections=["核心觀念", "老師重點", "操作流程", "重要案例", "注意事項", "本課總結"],
        observation_ids=[o.observation_id for o in OBS_H8],
        candidate_rule_ids=[c.rule_candidate_id for c in CAND_H8],
        open_questions=["『直觀出貨格約只在少部分個案出現』的比例未量化",
                        "309案例3.3%射倉的日期未在摘要中記錄，需回源文件補"],
        last_position="EOF",
    ))


# ============================================================ HILTON 2668 case
S_H9 = source(
    "HILTON-CAIJI-2668CASE", "莊家佈局2668_課程摘要", "2668百德國際2011-2014完整莊家佈局案例：鬥長命股→25.56%避GO入主→低位配股→九成歸邊→ED入局→出售受阻→兩路皆需炒高→一拆五出貨→DI清倉",
    mtype="case_study",
)

OBS_H9 = [
    Observation(
        observation_id="OBS-H9-001", methodology_id="HILTON", source_id=S_H9.source_id,
        source_section="六條股權界線", source_quote_or_paraphrase_reference="5%須SDI申報；10%主要股東可申請清盤；20%超一般授權具莊家意味；30%觸發GO——20-30%常表示有入主意圖但避開GO；50%絕對控股；75%大股東上限",
        observation_statement="六條股權界線判讀：5%（SDI申報線）/10%（主要股東，可申請清盤，舊主防範線）/20%（超一般授權=自行入局或特別安排，莊家意味）/30%（強制GO線；20-30%停駐=有入主意圖避GO成本）/50%（絕對控股）/75%（對應25%最低公眾持股）。百分比意義來自法規界線+前後文，不可機械下結論。",
        observation_type=ObservationType.METHOD_PRINCIPLE,
        supporting_evidence="2668案例25.56%轉讓=入主但避GO的實際運用",
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
    ),
    Observation(
        observation_id="OBS-H9-002", methodology_id="HILTON", source_id=S_H9.source_id,
        source_section="入主與配股信號", source_quote_or_paraphrase_reference="2013-05-31異動通告：25.56%由鄭季春家族轉售詹培忠…2013-06-04配售20%新股：低位、比例大、折讓大=漂亮買入信號；6-07配股終止——無法確知終止原因也毋須猜測，決策看原配股條件",
        observation_statement="2668入主序列：2013-05-31異動通告25.56%股權轉讓（詹培忠入主避GO線）；轉手當日非買點（價已升、未有財技確認）；06-04低位20%大折讓配股=正面部署（散戶誤把配股一概視壞）；06-07終止——不猜測原因，繼續跟蹤實際通告。",
        observation_type=ObservationType.FACT_FROM_CASE,
        supporting_evidence="SDI異動通告及配股公告日期與百分比",
        generalization_class=GeneralizationClass.POTENTIALLY_GENERALIZABLE,
    ),
    Observation(
        observation_id="OBS-H9-003", methodology_id="HILTON", source_id=S_H9.source_id,
        source_section="貨源歸邊與人物關係", source_quote_or_paraphrase_reference="2013-06-25股權集中報告：九成以上歸邊、16名人士因不尋常射倉被識別為同一組別；08-06羅輝成任執行董事=入局者派自己人查帳，典型賣殼/入主動作；08-08再配20%=完美配股、第二次買入機會",
        observation_statement="部署確認序列：股權集中報告（聯交所散戶警告）對財技派=莊家控制確認；報告內16人射倉組別名單可作陣營線索（羅輝成與詹培忠公開同行記錄）；ED任命=派自己人查帳的入主動作；其後完美配股（08-08）=部署確認+第二次買入機會；公眾持股不足報告揭示吳良好14.13%=共同佈局成員。",
        observation_type=ObservationType.FACT_FROM_CASE,
        supporting_evidence="股權集中報告/董事任命/配股公告的日期序列",
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
    ),
    Observation(
        observation_id="OBS-H9-004", methodology_id="HILTON", source_id=S_H9.source_id,
        source_section="受阻後的必然選擇", source_quote_or_paraphrase_reference="出售業務終止後，無論繼續或離場，鄭詹羅吳合計持貨50-60%同樣需要炒高才能散給市場——財技派在『終止出售』後仍能保持判斷的底氣",
        observation_statement="受阻推演法：主要交易被監管否決（2668出售37.53%業務被現金公司條例阻止）後，計算莊家合計持貨，推演『繼續』與『離場』兩路——續玩需炒高注資、離場需炒高散貨；兩路皆需推高=持有邏輯不變的底氣。散戶只見終止即恐慌。",
        observation_type=ObservationType.AUTHOR_INTERPRETATION,
        supporting_evidence="合計持貨50-60%的股權數字+兩條路的退出需求推演",
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
    ),
    Observation(
        observation_id="OBS-H9-005", methodology_id="HILTON", source_id=S_H9.source_id,
        source_section="出貨完成", source_quote_or_paraphrase_reference="2014-03-14一拆五=出貨財技；07-03詹培忠21.35%→7.22%；07-29再降至0.15%跌穿5%毋須申報=大致清倉；09月更換主席=項目完成",
        observation_statement="2668出貨序列：2014-03-14一拆五（吸引散戶）→07-03詹培忠DI 21.35%→7.22%（出貨開始）→07-29降至0.15%（跌穿5%申報線=清倉）→09月換主席=項目終結。約十倍升幅全程由公開資料（SDI/通告/集中報告/公眾持股報告）逐步驗證。",
        observation_type=ObservationType.FACT_FROM_CASE,
        supporting_evidence="DI百分比序列與日期",
        generalization_class=GeneralizationClass.POTENTIALLY_GENERALIZABLE,
    ),
    Observation(
        observation_id="OBS-H9-006", methodology_id="HILTON", source_id=S_H9.source_id,
        source_section="財技與技術分析的次序", source_quote_or_paraphrase_reference="先用財技確認個案、建立買入基礎，再以TA判斷圖形、最低位止蝕及加分條件；當財技已觸發離場，即使不理會價格位置也應處理",
        observation_statement="方法次序：財技分析先行（確認個案+買入基礎），TA僅作輔助（止蝕位/加分）；財技觸發離場時凌駕圖形。以操盤成本推算最低升幅只提供安全邊際，後續倍數應參考同類項目中位數。",
        observation_type=ObservationType.METHOD_PRINCIPLE,
        supporting_evidence="2668全程以財技信號為主線",
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
    ),
    Observation(
        observation_id="OBS-H9-007", methodology_id="HILTON", source_id=S_H9.source_id,
        source_section="殼股與傳承背景", source_quote_or_paraphrase_reference="實業創辦人離世後，若接班人缺乏能力和意欲，公司數年後逐步停滯最終變成死殼…傳承失效後容易引出賣殼、白武士或重組機會；2668約到第十年才進入可觀察階段",
        observation_statement="鬥長命股模式：傳承失效（接班人無能力無意欲）→長期停滯→死殼候選；判讀=兩次盈警+市值1-2億 vs 殼價比較；此類股可能長期無人問津，必須等待真正股權/財技異動（2668等約十年）。",
        observation_type=ObservationType.CONDITION,
        supporting_evidence="2668背景（鄭季春42.6%+Best Ahead 17%父傳子）",
        generalization_class=GeneralizationClass.POTENTIALLY_GENERALIZABLE,
    ),
]

CHAIN_H9_005 = EvidenceChain(
    chain_id="CHAIN-H9-005", observation_id="OBS-H9-005",
    input_facts=["2013-05-31: 25.56%鄭→詹轉讓", "2013-08-08: 20%配股；08-28吳良好14.13%",
                 "2014-03-14: 一拆五", "2014-07-03: 詹21.35%→7.22%；07-29→0.15%"],
    temporal_order="入主(避GO)→配股部署→歸邊→ED入局→出售受阻(兩路皆需炒高)→拆股出貨→DI清倉→換主席",
    calculation_or_comparison="持貨50-60%合計；詹持股21.35%→7.22%→0.15%（跌穿5%申報線）",
    author_reasoning="每一步以SDI/通告/集中報告/公眾持股報告等公開資料獨立可驗證",
    author_conclusion="完整莊家週期（等待→入主→部署→受阻推演→散貨）可用公開數據重組；前期貨源集中是部署訊號、後期拆股+DI減持是出貨訊號——同一事實的意義隨週期位置反轉",
)

CAND_H9 = [
    RuleCandidate(
        rule_candidate_id="CAND-HILTON-2668-SEQUENCE-001", rule_family=RuleFamily.EVENT_SEQUENCE,
        methodology_id="HILTON", rule_name="莊家完整週期序列模板（2668型）",
        description="鬥長命股等待→大手股權轉讓避GO（20-30%停駐）→低位大比例折讓配股（可終止後重推）→股權集中報告+射倉組別=歸邊確認→ED入局→（受阻則兩路推演）→高位拆股/散貨財技→DI大幅減持→跌穿5%申報線=清倉→換主席=項目終結。前期部署訊號與後期出貨訊號可為同一類事實，意義隨週期位置反轉。",
        preconditions=["有完整通告+SDI+CCASS歷史"],
        required_inputs=["股權轉讓序列", "配股公告（比例/折讓/位置/終止）", "董事任命", "DI百分比序列", "拆股/送股公告", "公眾持股/集中報告"],
        optional_inputs=["射倉組別名單", "人物公開關係"],
        trigger_conditions=["大手股權轉讓停駐20-30%區間（入主避GO線索）"],
        supporting_evidence=["OBS-H9-002", "OBS-H9-003", "OBS-H9-004", "OBS-H9-005"],
        output_semantics="週期階段標籤（WAITING/TAKEOVER/DEPLOYMENT/BLOCKED/BREAKUP/EXITED）+ 各階段可用訊號集",
        false_positive_conditions=["轉讓20-30%實為財務投資無後續部署"],
        false_negative_conditions=["週期跳步（無配股直接注資）或雙莊結構"],
        falsification_conditions=["以序列模板回測歷史十倍股：階段命中率不顯著高於隨機對齊"],
        origin_case_ids=["CASE-HILTON-2668"],
        origin_source_ids=[S_H9.source_id], origin_observation_ids=["OBS-H9-002", "OBS-H9-003", "OBS-H9-004", "OBS-H9-005"],
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
        dedup_classification=DedupClassification.NEW_RULE,
    ),
    RuleCandidate(
        rule_candidate_id="CAND-HILTON-BLOCKED-BOTHWAYS-001", rule_family=RuleFamily.SCENARIO,
        methodology_id="HILTON", rule_name="受阻兩路推演：續玩與離場皆需炒高=持有邏輯不變",
        description="主要交易被監管否決後，計算莊家合計持貨：續玩（注資推進）需炒高、離場（散50-60%貨）亦需炒高→兩路皆需推高時，終止本身不構成離場理由。僅當持貨結構支持兩路皆需炒高時成立；不可脫離持股/監管/承接力套用。",
        preconditions=["重大交易/出售被終止或否決", "可計算莊家陣營合計持貨"],
        required_inputs=["終止公告", "陣營合計持股%"],
        optional_inputs=["後續資產行動通告"],
        trigger_conditions=["交易終止公告發布"],
        supporting_evidence=["OBS-H9-004"],
        output_semantics="推演結論：BOTH_ROADS_REQUIRE_MARKUP / EXIT_RISK（持貨不足時）",
        false_positive_conditions=["莊家已場外找數離場（持貨數字滯後）"],
        false_negative_conditions=["股災令兩路皆不可行（等待亦無意義）"],
        falsification_conditions=["交易終止後60日回報：被標記股票與一般終止公告股無差異"],
        origin_case_ids=["CASE-HILTON-2668"],
        origin_source_ids=[S_H9.source_id], origin_observation_ids=["OBS-H9-004"],
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
        dedup_classification=DedupClassification.NEW_RULE,
    ),
]


def _register_h9(store):
    store.register_source(S_H9)
    for o in OBS_H9:
        store.add_observation(o)
    store.add_observation(OBS_H9[4], CHAIN_H9_005)
    for c in CAND_H9:
        store.add_candidate(c)
    store.mark_source_status(S_H9.source_id, "INGESTED")
    store.save_checkpoint(IngestionCheckpoint(
        source_id=S_H9.source_id,
        processed_sections=["核心觀念", "老師重點", "操作流程", "重要案例", "注意事項", "本課總結"],
        observation_ids=[o.observation_id for o in OBS_H9],
        candidate_rule_ids=[c.rule_candidate_id for c in CAND_H9],
        open_questions=["2668各日期為課堂敘述，平台可用DI/Turso數據獨立覆核（02318 DION管線同源）"],
        last_position="EOF",
    ))


# ============================================================ HILTON 急跌博反彈
S_H10 = source(
    "HILTON-CAIJI-DIPBOUNCE", "急跌博反彈_課程摘要", "急跌博反彈三必要條件(非莊家安排斬倉/跌幅70-90%+/極低市值)+一分鐘圖買盤回流；分拆上市沽壓補充(指數被動基金強制沽壓/2121案例)",
    mtype="course_summary",
)

OBS_H10 = [
    Observation(
        observation_id="OBS-H10-001", methodology_id="HILTON", source_id=S_H10.source_id,
        source_section="急跌的兩大來源", source_quote_or_paraphrase_reference="莊家散貨：利用昨日十元今日一元的錨定效應吸引散戶撈底，屬向下炒散貨方式，低位市值仍可能貼近合理殼價——莊家不因跌幅大而痛苦；被迫斬倉：大股東因孖展壓力被證券行不計價格強制沽貨，非莊家原先安排",
        observation_statement="急跌兩大來源判別：(1)莊家主動散貨——錨定撈底陷阱，跌八九成但低位市值貼合理殼價正是其派貨區，不應撈 (2)被迫斬倉——非自願，目標尋找此類；大股東被斬令同系股票同日急跌、大戶被斬連累其戶口多股。停牌非必然全損：非莊家安排的急跌後停牌可為釐清事件，復牌可能反彈（非保證）。",
        observation_type=ObservationType.METHOD_PRINCIPLE,
        supporting_evidence="謎網2017-06-27同系十多隻單日跌50-90%的系統斬倉案例",
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
    ),
    Observation(
        observation_id="OBS-H10-002", methodology_id="HILTON", source_id=S_H10.source_id,
        source_section="三項必要條件+買入判斷", source_quote_or_paraphrase_reference="細價股最少跌約70%才開始計算，希望85%最好超過90%；主板市值約兩億以下理想一億以下、創板八千萬以下；所有急跌判斷要看一分鐘圖…待跌勢停住、成交由細轉大才代表新買盤進場；大多數個案不會完全還原，反彈至跌幅約一半位置通常已遇第一阻力",
        observation_statement="急跌博反彈三必要條件+操作：(1)非莊家安排（目標=被迫斬倉）(2)跌幅：細價股≥70%起步、85%希望、>90%最好（85與90%的剩餘市值是倍數差）；大價股單日跌3-5成已極端 (3)市值極低（當時參考：主板≤1-2億/創板≤6-8千萬）。買入=一分鐘圖觀察成交縮細→停住→由細轉大（新買盤）；不追最低；離場=1-2倍即夠/跌幅一半阻力區/盤路信號，不等還原。理想個案一年僅三四次，細注參與。",
        observation_type=ObservationType.TIMING_RULE,
        supporting_evidence="1428耀才2014-12-18（確認大股東未沽→他人被斬→2.2買入兩日+50%）；1529/6111兩至四倍個案",
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
    ),
    Observation(
        observation_id="OBS-H10-003", methodology_id="HILTON", source_id=S_H10.source_id,
        source_section="分拆上市補充", source_quote_or_paraphrase_reference="指數成分股分拆出的子公司不會自動成為同一指數成分股，被動基金因此可能必須出售，令第一輪沽壓更明顯；2121以介紹上市分拆，沽壓後約一年三個月升約四倍",
        observation_statement="分拆沽壓補充證據：被動基金強制沽壓——指數成分股分拆的子公司不自動入指數，被動基金必沽（中信電子案例：沽壓後估值一度僅5-6倍PE）。2121介紹上市沽壓後約15個月升約四倍。靚號碼（1469齊牌1/4/6/9）為加分非買入理由；同一系連續分拆均十倍（0015分拆1372）=有往績操盤者重點留意。",
        observation_type=ObservationType.FACT_FROM_CASE,
        supporting_evidence="被動資金機制+2121/中信電子/0015-1372案例",
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
    ),
]

CHAIN_H10_001 = EvidenceChain(
    chain_id="CHAIN-H10-001", observation_id="OBS-H10-001",
    input_facts=["急跌股需判別來源：莊家主動散貨 vs 被迫斬倉", "謎網2017-06-27：同系十多隻單日跌50-90%"],
    temporal_order="系統斬倉在單日內完成；同系多股同日急跌=大股東系統被斬的指紋",
    calculation_or_comparison="多股同日同步急跌的相關性↑=系統性斬倉；單股獨跌=需查莊家是否主動",
    author_reasoning="莊家主動散貨的下跌其派貨區貼合理殼價，撈底者=派貨對象；被迫斬倉者莊家亦痛苦，復原動機真實",
    author_conclusion="急跌博反彈只做被迫斬倉型；判別線索=同系多股同日急跌+大股東持股未減（1428確認法）",
)

CAND_H10 = [
    RuleCandidate(
        rule_candidate_id="CAND-HILTON-DIPBOUNCE-001", rule_family=RuleFamily.RISK_WINDOW,
        methodology_id="HILTON", rule_name="急跌博反彈：被迫斬倉三條件+買盤回流確認",
        description="僅針對非自願急跌（被迫斬倉）的短線反彈策略。三必要條件：(1)非莊家安排——判別線索：同系多股同日急跌/大股東持股未減 (2)跌幅：細價股≥70%（85-90%+理想）(3)市值極低（隨殼價環境更新）。進場=一分鐘圖成交縮→停→由細轉大；離場=1-2倍/跌幅一半阻力/盤路信號。理想個案一年約三四次，細注。",
        preconditions=["標的出現急跌"],
        required_inputs=["跌幅%（高點至現價）", "急跌後市值", "同系/同戶口股票同日表現", "分鐘級成交量序列"],
        optional_inputs=["大股東DI（確認未沽）", "停牌/復牌狀態"],
        trigger_conditions=["三條件同時成立+買盤回流形態"],
        supporting_evidence=["OBS-H10-001", "OBS-H10-002"],
        output_semantics="急跌分類：FORCED_LIQUIDATION_CANDIDATE / DELIBERATE_DISTRIBUTION(禁撈) + 進離場框架",
        false_positive_conditions=["莊家主動散貨被誤判為斬倉（低位貼殼價恰是其派貨區）"],
        false_negative_conditions=["分批斬倉無同日多股指紋"],
        falsification_conditions=["符合三條件的樣本群其後反彈率/幅度不顯著高於隨機急跌股"],
        origin_case_ids=["CASE-HILTON-1428", "CASE-HILTON-謎網2017", "CASE-HILTON-大發地產"],
        origin_source_ids=[S_H10.source_id], origin_observation_ids=["OBS-H10-001", "OBS-H10-002"],
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
        dedup_classification=DedupClassification.NEW_RULE,
    ),
    RuleCandidate(
        rule_candidate_id="CAND-HILTON-SPINOFF-PRESSURE-001", rule_family=RuleFamily.EVENT_SEQUENCE,
        methodology_id="HILTON", rule_name="分拆沽壓：被動基金強制沽售為主要沽壓源（證據增補）",
        description="【SAME_RULE_NEW_EVIDENCE】補強 CAND-HILTON-SPINOFF-PRESSURE-001：第一輪沽壓的最大來源除散戶無償沽售與基金主題不合外，明確加入被動基金強制沽售——指數成分股分拆的子公司不自動入指數（中信電子案例沽壓後估值一度5-6倍PE）。同一操盤者連續分拆均十倍（0015→1372）為重點留意線索。",
        preconditions=["分拆上市完成"],
        required_inputs=["母公司是否指數成分股", "分拆形式", "上市日期"],
        optional_inputs=["操盤者分拆往績"],
        trigger_conditions=["母公司屬指數成分股的分拆（被動沽壓加權）"],
        supporting_evidence=["OBS-H10-003"],
        output_semantics="沽壓強度分級（被動基金加權）+ 等待期",
        false_positive_conditions=["子公司極快獲納入其他指數"],
        false_negative_conditions=["沽壓被造市者提前承接"],
        falsification_conditions=["指數成分股分拆與非成分股分拆的首輪沽壓深度無統計差異"],
        origin_case_ids=["CASE-HILTON-2121", "CASE-HILTON-中信電子", "CASE-HILTON-0015-1372"],
        origin_source_ids=[S_H10.source_id], origin_observation_ids=["OBS-H10-003"],
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
        dedup_classification=DedupClassification.SAME_RULE_NEW_EVIDENCE,
    ),
]


def _register_h10(store):
    store.register_source(S_H10)
    for o in OBS_H10:
        store.add_observation(o)
    store.add_observation(OBS_H10[0], CHAIN_H10_001)
    for c in CAND_H10:
        store.add_candidate(c)
    store.mark_source_status(S_H10.source_id, "INGESTED")
    store.save_checkpoint(IngestionCheckpoint(
        source_id=S_H10.source_id,
        processed_sections=["核心觀念", "老師重點", "操作流程", "重要案例", "注意事項", "本課總結"],
        observation_ids=[o.observation_id for o in OBS_H10],
        candidate_rule_ids=[c.rule_candidate_id for c in CAND_H10],
        open_questions=["本檔與L5/L6重疊（同課程另一次記錄）——已按SAME_RULE_NEW_EVIDENCE處理，未重複建規則",
                        "市值門檻（1-2億/6-8千萬）為課堂時點殼價參考"],
        last_position="EOF",
    ))


# ============================================================ CHAU_HIN lesson 1
Z_DIR = "細價股-財技軍火庫/大師股票投資課程-周顯/知識提煉-周顯大師股票投資課程"
S_Z1 = source(
    "CHAUHIN-COURSE-L1", "周顯大師股票投資課程-第1堂_課程知識摘要", "市場歷史/貨幣與資產價格背離/壞消息失效訊號/方法普及化衰減/槓桿前置條件",
    mid="CHAU_HIN", loc=Z_DIR,
)

OBS_Z1 = [
    Observation(
        observation_id="OBS-Z1-001", methodology_id="CHAU_HIN", source_id=S_Z1.source_id,
        source_section="判斷條件1/案例一", source_quote_or_paraphrase_reference="壞消息很多但市場跌不下去；一旦出現少量好消息反而快速上升——觀察市場對消息的反應，比消息標題本身更重要",
        observation_statement="壞消息失效訊號：連續壞消息殺傷力遞減+好消息反應放大=流動性支撐的線索；分析單位是『消息+價格反應+資金環境』三合一，非消息本身。",
        observation_type=ObservationType.METHOD_PRINCIPLE,
        supporting_evidence="疫情/政治/貿易衝突期美QE下的市場承接案例",
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
    ),
    Observation(
        observation_id="OBS-Z1-002", methodology_id="CHAU_HIN", source_id=S_Z1.source_id,
        source_section="核心觀念3-4", source_quote_or_paraphrase_reference="生意環境差+資金成本低+市場大量資金→資金流向股票樓宇→實體經濟差但資產價格可升；經濟差≠股市必跌",
        observation_statement="實體經濟與資產市場可長期背離：低息大量資金無實體出口→流入資產；分析次序=大勢→資金因素（貨幣供應/利率/流向）→港股外部關係（美元聯匯/美股+人民幣/中國貿易）→個股。",
        observation_type=ObservationType.METHOD_PRINCIPLE,
        supporting_evidence="救市後資產先行案例；低成本資金炒作資產的因果鏈",
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
    ),
    Observation(
        observation_id="OBS-Z1-003", methodology_id="CHAU_HIN", source_id=S_Z1.source_id,
        source_section="核心觀念1/例外6", source_quote_or_paraphrase_reference="財技炒股法普及後資訊優勢下降…不能假設過去的優勢永久存在",
        observation_statement="方法衰減律：任何炒股方法隨參與者學習而優勢遞減；規則有效性須按當前市場環境重估，不可假設永久。（對本平台：Hilton規則亦是環境依賴，須持續驗證。）",
        observation_type=ObservationType.RISK_WARNING,
        supporting_evidence="老師自述財技法普及化過程",
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
    ),
    Observation(
        observation_id="OBS-Z1-004", methodology_id="CHAU_HIN", source_id=S_Z1.source_id,
        source_section="案例六", source_quote_or_paraphrase_reference="技術未到不應借孖展炒股；槓桿把原本判斷與風險控制同步放大",
        observation_statement="槓桿前置條件：技術未成熟（基本交易+風險控制能力）不應使用孖展；槓桿不是獨立技巧，放大判斷也放大錯誤。",
        observation_type=ObservationType.RISK_WARNING,
        supporting_evidence="課堂對孖展提問的回應",
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
    ),
]

CAND_Z1 = [
    RuleCandidate(
        rule_candidate_id="CAND-CHAUHIN-BADNEWS-DECAY-001", rule_family=RuleFamily.EVENT_SEQUENCE,
        methodology_id="CHAU_HIN", rule_name="壞消息失效=流動性支撐線索",
        description="連續壞消息的價格殺傷力遞減、好消息反應放大→推斷流動性/貨幣支撐；大勢判斷以價格反應為準而非消息數量。此為大市層訊號，不直接適用個股。",
        preconditions=["有消息流與價格序列"],
        required_inputs=["壞消息序列及其後價格反應", "好消息反應幅度"],
        optional_inputs=["貨幣供應/利率環境"],
        trigger_conditions=["連續壞消息而市場不再新低"],
        supporting_evidence=["OBS-Z1-001", "OBS-Z1-002"],
        output_semantics="流動性支撐嫌疑標記（大市層）",
        false_positive_conditions=["壞消息已被價格充分計價後的自然企穩"],
        false_negative_conditions=["資金退潮初期消息反應仍鈍"],
        falsification_conditions=["壞消息失效期後的市場表現與流動性指標無關"],
        origin_case_ids=[],
        origin_source_ids=[S_Z1.source_id], origin_observation_ids=["OBS-Z1-001"],
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
        dedup_classification=DedupClassification.NEW_RULE,
    ),
]


def _register_z1(store):
    store.register_source(S_Z1)
    for o in OBS_Z1:
        store.add_observation(o)
    for c in CAND_Z1:
        store.add_candidate(c)
    store.mark_source_status(S_Z1.source_id, "INGESTED")
    store.save_checkpoint(IngestionCheckpoint(
        source_id=S_Z1.source_id,
        processed_sections=["核心觀念", "判斷條件與邏輯", "老師重點", "操作流程", "重要案例", "例外與容易誤判情況", "注意事項", "本課總結"],
        observation_ids=[o.observation_id for o in OBS_Z1],
        candidate_rule_ids=[c.rule_candidate_id for c in CAND_Z1],
        open_questions=["本課屬大勢框架課，CCASS/財技具體規則密度低——僅抽取方法級規則"],
        last_position="EOF",
    ))


# ============================================================ CHAU_HIN lesson 2A
S_Z2 = source(
    "CHAUHIN-COURSE-L2A", "周顯大師股票投資課程-第2A堂_課程知識摘要", "供股結構分析九步；雙質數供股法(碎股減流通)；29.99%門檻追問；理論除權價僅參考；短期風險與中長期財技分開判斷；玩法生命周期",
    mid="CHAU_HIN", loc=Z_DIR,
)

OBS_Z2 = [
    Observation(
        observation_id="OBS-Z2-001", methodology_id="CHAU_HIN", source_id=S_Z2.source_id,
        source_section="核心觀念5", source_quote_or_paraphrase_reference="雙質數供股法：利用特定比例令部分持股者產生碎股…碎股較不方便直接沽出，可能減少部分貨源即時流出…只可以是其中一個動機，交易可同時存在多個平行目的",
        observation_statement="雙質數供股法：質數比例供股令散戶產生碎股→碎股不便即時沽出→減少即時沽壓/貨源流出，屬中長期偏多財技因素。但一宗交易可有多個平行動機（集資/股權安排/碎股），不可單一解釋。",
        observation_type=ObservationType.METHOD_PRINCIPLE,
        supporting_evidence="課堂雙質數比例案例",
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
    ),
    Observation(
        observation_id="OBS-Z2-002", methodology_id="CHAU_HIN", source_id=S_Z2.source_id,
        source_section="核心觀念3/案例三", source_quote_or_paraphrase_reference="某主要股東持股29.99%——為甚麼不是30%？與GO/全面收購責任連結…看到接近重要門檻的精確數字→主動追問交易設計原因",
        observation_statement="門檻精確數字追問法：股權停在29.99%（而非30%）=交易設計線索，聯結GO責任；習慣是見貼門檻精確數字即主動追問「為甚麼停在這裡」，從公告與交易結構找原因。（與Hilton 29.97%線索同構，跨方法論各自獨立記錄。）",
        observation_type=ObservationType.METHOD_PRINCIPLE,
        supporting_evidence="29.99%案例（大型公司資本重組390億案例內）",
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
    ),
    Observation(
        observation_id="OBS-Z2-003", methodology_id="CHAU_HIN", source_id=S_Z2.source_id,
        source_section="判斷條件2,6/案例四", source_quote_or_paraphrase_reference="理論價只是參考，第二天實際開市價可以完全不同；供股公布後原持有人第一個策略是先處理持倉，不論高開低開平開…短期交易處理≠中長期財技結構判斷",
        observation_statement="供股時間尺度分離：短期——供股公布後先處理持倉（不賭高開低開，高開不改寫風險規則）；中長期——碎股減流通等財技效果另行研究。理論除權價（舊股總值+新股按供股價÷總股數）僅參考，可與實際價格脫鈎。",
        observation_type=ObservationType.TIMING_RULE,
        supporting_evidence="復牌高開案例中老師仍先處理持倉",
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
    ),
    Observation(
        observation_id="OBS-Z2-004", methodology_id="CHAU_HIN", source_id=S_Z2.source_id,
        source_section="判斷條件4,7", source_quote_or_paraphrase_reference="股權重組要比較『前』與『後』：交易前主要股東→誰參與/沒參與→誰被攤薄→誰新增→最終百分比→是否靠近重要門檻",
        observation_statement="股權前後對照法：股權重組分析必須比較交易前後的主要股東/參與者/被攤薄者/新增者/最終百分比/門檻接近度；再把人物角色放回事件脈絡。全部用公開資料（公告/招股書/公開股權）。",
        observation_type=ObservationType.METHOD_PRINCIPLE,
        supporting_evidence="九步供股分析流程",
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
    ),
]

CAND_Z2 = [
    RuleCandidate(
        rule_candidate_id="CAND-CHAUHIN-PRIME-RATIO-001", rule_family=RuleFamily.RIGHTS_ISSUE,
        methodology_id="CHAU_HIN", rule_name="雙質數供股比例=碎股減流通的中長期偏多因素",
        description="質數類供股比例製造碎股→碎股難即時沽出→減少即時沽壓與貨源流出；屬中長期財技偏好因素，須與短期供股風險（公布後先處理持倉）分開判斷；一宗交易多動機並存，碎股只是其中一個可能動機。",
        preconditions=["供股公告已發布"],
        required_inputs=["供股比例（是否質數/非整除）", "每手股數"],
        optional_inputs=["集資用途", "股權安排"],
        trigger_conditions=["供股比例與常見持股量非整除"],
        supporting_evidence=["OBS-Z2-001", "OBS-Z2-003"],
        output_semantics="碎股效應標記（中長期流通收縮線索）——不抵消短期風險處理",
        false_positive_conditions=["比例非刻意（湊巧質數）"],
        false_negative_conditions=["碎股經碎股交易市場流通"],
        falsification_conditions=["質數比例與整除比例供股的其後沽壓/回報無統計差異"],
        origin_case_ids=[],
        origin_source_ids=[S_Z2.source_id], origin_observation_ids=["OBS-Z2-001"],
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
        dedup_classification=DedupClassification.RULE_VARIANT,
    ),
    RuleCandidate(
        rule_candidate_id="CAND-CHAUHIN-THRESHOLD-ASK-001", rule_family=RuleFamily.CONTROL_CHANGE,
        methodology_id="CHAU_HIN", rule_name="門檻精確數字追問法（29.99%型）",
        description="主要股東持股停在重要門檻的精確微下方（29.99% vs 30% GO線）→主動追問交易設計原因，從公告與結構找動機（避GO/避主要股東地位/避申報）。股權百分比是設計線索不是資料抄寫。",
        preconditions=["有持股披露"],
        required_inputs=["持股%精確值", "門檻列表（5/10/30/50/75）"],
        trigger_conditions=["持股停駐門檻−ε精確值"],
        supporting_evidence=["OBS-Z2-002"],
        output_semantics="門檻追問標記 + 設計原因候選列表",
        false_positive_conditions=["湊巧數字"],
        false_negative_conditions=["多帳戶隱藏真實位置"],
        falsification_conditions=["門檻停駐樣本的後續交易設計解釋率不顯著高於對照"],
        origin_case_ids=["CASE-CHAUHIN-29.99"],
        origin_source_ids=[S_Z2.source_id], origin_observation_ids=["OBS-Z2-002"],
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
        dedup_classification=DedupClassification.RULE_VARIANT,
    ),
]


def _register_z2(store):
    store.register_source(S_Z2)
    for o in OBS_Z2:
        store.add_observation(o)
    for c in CAND_Z2:
        store.add_candidate(c)
    store.mark_source_status(S_Z2.source_id, "INGESTED")
    store.save_checkpoint(IngestionCheckpoint(
        source_id=S_Z2.source_id,
        processed_sections=["核心觀念", "判斷條件與邏輯", "老師重點", "操作流程", "重要案例", "例外與容易誤判情況", "注意事項", "本課總結"],
        observation_ids=[o.observation_id for o in OBS_Z2],
        candidate_rule_ids=[c.rule_candidate_id for c in CAND_Z2],
        open_questions=["29.99%案例的具體公司名在逐字稿中辨識失真，僅存百分比事實",
                        "CAND-CHAUHIN-THRESHOLD-ASK-001與Hilton CAND-HILTON-THRESHOLD-HUG-001同構——按方法論隔離各自記錄，未合併"],
        last_position="EOF",
    ))


# ============================================================ IVAN_L 型絕地
I_DIR = "細價股-財技軍火庫/L型絕地-Ivan/知識提煉-L型絕地"
S_I1 = source(
    "IVANL-LXING-COURSE", "L型絕地_課程知識摘要", "L型絕地選股條件(半新股/集資低/天生乾身/低市值)；絕地=時間磨走散戶(跌穿招股價+沉底半年至一年)；市值分段注碼(3/2/1億)；向下炒風險排除；炒高後階段性提高警覺(3/5-6/7-8億)",
    mid="IVAN_L", loc=I_DIR, mtype="course_summary",
)

OBS_I1 = [
    Observation(
        observation_id="OBS-I1-001", methodology_id="IVAN_L", source_id=S_I1.source_id,
        source_section="核心觀念2-3/判斷條件1-3", source_quote_or_paraphrase_reference="近期上市股票歷史較短、貨源結構易理解、可由招股文件及招股結果開始追溯；天生乾身：公開發售部分相對有限、大部分股份已集中於特定持有人；集資主板約1億以下較值得留意、約3,600萬屬很理想",
        observation_statement="L型絕地選股前置：半新股優先（歷史短/貨源可追溯，只需招股文件+招股結果兩份文件起步）；『天生乾身』=IPO公開發售有限+大部分貨在相關人手上→免長時間收貨；集資額越低越符合（主板≈1億以下留意、3,600萬級理想）；主動少集資（可多集而少集）=不想街外貨過多的跡象。",
        observation_type=ObservationType.CONDITION,
        supporting_evidence="課堂篩選框架經驗值",
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
    ),
    Observation(
        observation_id="OBS-I1-002", methodology_id="IVAN_L", source_id=S_I1.source_id,
        source_section="核心觀念5/操作流程Step4", source_quote_or_paraphrase_reference="絕地的本質是長時間把散戶磨走…上市後很快跌破招股價、長期未能重返、低位沉底約半年至一年…時間是莊家的重要武器",
        observation_statement="絕地定義：非跌得多=絕地，而是上市後快速跌穿招股價→長期沉底半年至一年→散戶在無希望中逐步離場；L型只是外觀，必須有內在條件（背景/市值/貨源/時間），存在變種形態，不可純圖形機械判斷。",
        observation_type=ObservationType.METHOD_PRINCIPLE,
        supporting_evidence="典型形態五步描述",
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
    ),
    Observation(
        observation_id="OBS-I1-003", methodology_id="IVAN_L", source_id=S_I1.source_id,
        source_section="判斷條件5/案例二四", source_quote_or_paraphrase_reference="3億以下開始留意；2-3億細注；1-2億視位置中注；1億以下視位置大注…市值越低若原條件仍成立注碼可相應提高；不是跌到某市值就必須買",
        observation_statement="市值分段注碼（主板經驗區間）：>3億觀望；3億以下開始留意；2-3億細注；1-2億中注；1億以下大注。注碼按個人本金設計分級；前提=原篩選條件未破壞——條件改變時不可因『更便宜』機械加注。",
        observation_type=ObservationType.CONDITION,
        supporting_evidence="一萬元本金分段示範；2.5-2.8億低位→4.4億才炒起的案例（最低位不即時啟動）",
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
    ),
    Observation(
        observation_id="OBS-I1-004", methodology_id="IVAN_L", source_id=S_I1.source_id,
        source_section="判斷條件7", source_quote_or_paraphrase_reference="本策略最怕的是標的仍有向下炒或進一步破壞股本價格結構的空間…剛上市已完成集資、短時間再向下財技的合理性相對較低；貨源高度集中時向下大量出貨亦需人承接",
        observation_statement="向下炒風險排除邏輯：剛上市已完成集資→短期再向下財技合理性低；貨源高度集中→向下出貨需承接；極低市值→向下空間受限。風險非零——須主動檢查『向下條件』是否存在（印股空間/CB/供股歷史）。",
        observation_type=ObservationType.RISK_WARNING,
        supporting_evidence="排除條件的結構推理",
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
    ),
    Observation(
        observation_id="OBS-I1-005", methodology_id="IVAN_L", source_id=S_I1.source_id,
        source_section="老師重點5", source_quote_or_paraphrase_reference="炒上去後逐級看待：約3億第一個重要區域；5-6億看莊家是否具備繼續推動能力；7-8億開始更重視街貨及是否散貨；約20億屬非常高炒作區需天時地利人和",
        observation_statement="炒高後分級警覺（主板）：≈3億=第一重要區域；5-6億=驗證推動力；7-8億=重點轉向街貨/散貨監察；≈20億=超高區需多條件齊備。市值階段不同，風險假設不同——低位邏輯不可套用到高位。",
        observation_type=ObservationType.TIMING_RULE,
        supporting_evidence="市值階梯觀察重點",
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
    ),
    Observation(
        observation_id="OBS-I1-006", methodology_id="IVAN_L", source_id=S_I1.source_id,
        source_section="判斷條件4", source_quote_or_paraphrase_reference="超額認購不是愈高愈好…幾百倍超額認購可能代表大量散戶參與，要留意背後究竟是甚麼人認購",
        observation_statement="超額認購非單一判準：無超購可以、幾百倍超購=大量散戶參與嫌疑（街外貨結構複雜化）；須看認購者結構而非表面倍數。",
        observation_type=ObservationType.CONDITION,
        supporting_evidence="課堂對超購倍數的討論",
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
    ),
]

CHAIN_I1_003 = EvidenceChain(
    chain_id="CHAIN-I1-003", observation_id="OBS-I1-003",
    input_facts=["L型候選：半新股+天生乾身+集資低", "歷史案例低位≈2.5-2.8億、約4.4億才開始炒上"],
    temporal_order="上市→跌穿招股價→沉底6-12月→市值分區逐步部署→其後於4.4億區啟動",
    calculation_or_comparison="市值越低推動所需資金越少；分段注碼令大注集中在低市值區改善風險回報",
    author_reasoning="不猜最低點；以市值為部署尺度、條件不變為加注前提",
    author_conclusion="分段市值注碼法：3億留意→2-3億細注→1-2億中注→1億以下大注（條件未破壞時）",
)

CAND_I1 = [
    RuleCandidate(
        rule_candidate_id="CAND-IVANL-LXING-SCREEN-001", rule_family=RuleFamily.SHELL_VALUE,
        methodology_id="IVAN_L", rule_name="L型絕地篩選器：半新股+天生乾身+集資低+絕地形態",
        description="候選篩選四支柱：(1)半新股（1-3年內，貨源/人物可由招股文件+招股結果追溯）(2)天生乾身（公開發售有限、街貨低）(3)集資額低（主板≈1億以下；主動少集=保貨源集中）(4)絕地形態（快速跌穿招股價+沉底6-12月）。條件不足即不買；形態變種存在，不機械套圖。",
        preconditions=["標的為近期上市股票"],
        required_inputs=["上市日期", "集資額", "公開發售/配售結構", "招股結果認購結構", "上市後價格歷史（vs 招股價）"],
        optional_inputs=["保薦人/人物往績", "超額認購倍數及結構"],
        trigger_conditions=["四支柱初篩通過"],
        supporting_evidence=["OBS-I1-001", "OBS-I1-002", "OBS-I1-006"],
        output_semantics="L型絕地候選池標記 + 條件完成度評分",
        false_positive_conditions=["純圖形L型無內在條件", "向下炒潛質未排除"],
        false_negative_conditions=["變種形態（沉底期更短/無完全跌穿招股價）"],
        falsification_conditions=["通過篩選的候選池與隨機半新股的後續回報無統計差異"],
        origin_case_ids=["CASE-IVANL-2.8億-4.4億案例"],
        origin_source_ids=[S_I1.source_id], origin_observation_ids=["OBS-I1-001", "OBS-I1-002"],
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
        dedup_classification=DedupClassification.NEW_RULE,
    ),
    RuleCandidate(
        rule_candidate_id="CAND-IVANL-LADDER-STAKE-001", rule_family=RuleFamily.RISK_WINDOW,
        methodology_id="IVAN_L", rule_name="市值階梯注碼與炒高後分級警覺",
        description="部署階梯（主板）：3億留意→2-3億細注→1-2億中注→1億以下大注（條件不變前提）。持有階梯：≈3億第一重要區→5-6億驗證推動力→7-8億轉散貨/街貨監察→≈20億超高區。兩方向都以市值為尺度、非價格；條件破壞即停加注。",
        preconditions=["已入L型絕地候選池"],
        required_inputs=["即時市值", "市值區間邊界", "篩選條件狀態"],
        optional_inputs=["CCASS街貨變化（高位階段）"],
        trigger_conditions=["市值跨越階梯邊界"],
        supporting_evidence=["OBS-I1-003", "OBS-I1-005"],
        output_semantics="當前階段標籤 + 建議注碼級別/警覺級別",
        false_positive_conditions=["條件已破壞（向下財技出現）仍按階梯加注"],
        false_negative_conditions=["極速跨越多級（跳空炒作）"],
        falsification_conditions=["階梯注碼法的事後資金加權回報不優於一次性等額"],
        origin_case_ids=["CASE-IVANL-2.8億-4.4億案例"],
        origin_source_ids=[S_I1.source_id], origin_observation_ids=["OBS-I1-003", "OBS-I1-005"],
        generalization_class=GeneralizationClass.REPEATABLE_METHOD,
        dedup_classification=DedupClassification.NEW_RULE,
    ),
]


def _register_i1(store):
    store.register_source(S_I1)
    for o in OBS_I1:
        store.add_observation(o)
    store.add_observation(OBS_I1[2], CHAIN_I1_003)
    for c in CAND_I1:
        store.add_candidate(c)
    store.mark_source_status(S_I1.source_id, "INGESTED")
    store.save_checkpoint(IngestionCheckpoint(
        source_id=S_I1.source_id,
        processed_sections=["核心觀念", "判斷條件與邏輯", "老師重點", "操作流程", "重要案例", "例外與容易誤判情況", "注意事項", "本課總結"],
        observation_ids=[o.observation_id for o in OBS_I1],
        candidate_rule_ids=[c.rule_candidate_id for c in CAND_I1],
        open_questions=["『MIMA』等術語辨識失真未採用", "股票案例/人物名稱多處失真，不建人物名單",
                        "另有股票案例/L型研究I版_最終版_GO兌現機制_20260731.md等待批次3處理"],
        last_position="EOF",
    ))


if __name__ == "__main__":
    store = IngestionStore()
    ingest(store)
    for fn in (_register_h2, _register_h3, _register_h4, _register_h5, _register_h6, _register_h7, _register_h8, _register_h9, _register_h10, _register_z1, _register_z2, _register_i1):
        fn(store)
    print(store.batch_stats())
