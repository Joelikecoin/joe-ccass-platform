"""DOCTOR_INTELLIGENCE V4 — capability consolidation layer.

Converts the 48 raw CASE_DERIVED candidates into:
  RULE_FAMILIES  (semantic groups; methodology variants stay distinct)
  CAPABILITIES   (what Doctor can actually DO in an analysis)
  VALIDATION GAPS
  LUNA VALIDATION TARGETS (consumed by Luna historical-case testing)

Rules of the layer:
- consolidation never deletes lineage: every family/capability references
  rule_candidate_ids, which still resolve to sources/observations
- methodology variants are recorded, never silently merged
- confidence_level never exceeds PARTIALLY_CASE_SUPPORTED here — promotion
  requires Luna (or human) case evidence; teacher repetition != validation
"""
from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, model_validator


class OutputType(str, Enum):
    FACT = "FACT"
    DERIVED_MEASURE = "DERIVED_MEASURE"
    RULE_OUTPUT = "RULE_OUTPUT"
    INFERENCE = "INFERENCE"


class ConfidenceLevel(str, Enum):
    UNVALIDATED_CASE_DERIVED = "UNVALIDATED_CASE_DERIVED"
    PARTIALLY_CASE_SUPPORTED = "PARTIALLY_CASE_SUPPORTED"
    EMPIRICALLY_TESTED = "EMPIRICALLY_TESTED"


class RuleFamilyRecord(BaseModel):
    rule_family_id: str
    rule_family_name: str
    member_rule_ids: List[str]
    shared_analytical_purpose: str
    distinct_conditions: List[str] = Field(default_factory=list)
    distinct_methodology_variants: List[str] = Field(default_factory=list)
    true_duplicates: List[str] = Field(default_factory=list)
    same_rule_new_evidence: List[str] = Field(default_factory=list)
    context_variants: List[str] = Field(default_factory=list)
    keep_separate_reason: str

    @model_validator(mode="after")
    def _no_orphan(self):
        if not self.member_rule_ids:
            raise ValueError(f"orphan rule family {self.rule_family_id}")
        return self


class Capability(BaseModel):
    capability_id: str
    capability_name: str
    what_doctor_can_now_do: str
    supporting_rule_families: List[str]
    supporting_rule_ids: List[str]
    supporting_methodologies: List[str]
    source_ids: List[str]
    required_input_data: List[str]
    output_type: OutputType
    confidence_level: ConfidenceLevel = ConfidenceLevel.UNVALIDATED_CASE_DERIVED
    known_limitations: List[str] = Field(default_factory=list)
    falsification_conditions: List[str] = Field(default_factory=list)
    real_case_validation_status: str = "PENDING_LUNA"

    @model_validator(mode="after")
    def _gates(self):
        if not self.supporting_rule_ids:
            raise ValueError(f"capability {self.capability_id} has no supporting rules")
        if not self.falsification_conditions:
            raise ValueError(f"capability {self.capability_id} lacks falsification")
        if self.confidence_level == ConfidenceLevel.EMPIRICALLY_TESTED:
            raise ValueError("consolidation must not auto-promote to EMPIRICALLY_TESTED")
        return self


class ValidationGap(BaseModel):
    capability_id: str
    source_method_support: bool
    case_support: bool
    contradictory_case: bool
    quantitative_support: bool
    point_in_time_support: bool
    falsification_defined: bool
    real_case_validation_required: bool
    gap_priority: str = "MEDIUM"  # HIGH when method strong + case validation missing


class LunaTarget(BaseModel):
    target_id: str
    capability_id: str
    rule_family_id: str
    claim_to_test: str
    required_case_characteristics: List[str]
    required_evidence: List[str]
    t0_fields_required: List[str]
    t1_outcome_fields_required: List[str]
    support_condition: str
    contradiction_condition: str
    context_dependent_condition: str
    falsification_trigger: str
    minimum_case_count: Optional[int] = None  # None = method specifies none; do not invent
    priority: str = "MEDIUM"

    @model_validator(mode="after")
    def _refs_valid(self):
        if not self.claim_to_test or not self.support_condition or not self.falsification_trigger:
            raise ValueError(f"Luna target {self.target_id} incomplete")
        if self.priority not in ("HIGH", "MEDIUM", "LOW"):
            raise ValueError("priority must be HIGH/MEDIUM/LOW")
        return self


# ============================================================ RULE FAMILIES
RULE_FAMILIES: List[RuleFamilyRecord] = [
    RuleFamilyRecord(
        rule_family_id="RF-01", rule_family_name="供股意圖與R報告解讀",
        member_rule_ids=["CAND-HILTON-SUPPLY-INTENT-001", "CAND-HILTON-REVENGE-TIMING-001",
                         "CAND-HILTON-RREPORT-COUNT-001", "CAND-HILTON-RREPORT-DARK-001",
                         "CAND-CHAUHIN-PRIME-RATIO-001"],
        shared_analytical_purpose="從供股結構與結果推斷大股東要貨還是要錢，並評估散戶參與度與暗倉線索",
        distinct_conditions=["除權後市價 vs 供股價走向", "Last Pay Day 時間窗", "申請份數≤30",
                             "市價>GO價時的異常接受比例", "質數比例→碎股"],
        distinct_methodology_variants=["HILTON: 供乾/供錢分辨器+復仇記", "CHAU_HIN: 碎股減流通（中長期尺度）"],
        true_duplicates=[], same_rule_new_evidence=[],
        context_variants=["CAND-CHAUHIN-PRIME-RATIO-001 與 Hilton 碎股論述同構但機制不同（流通收縮 vs 被迫留存）"],
        keep_separate_reason="周顯碎股規則屬另一方法論且時間尺度不同；Hilton 內部各規則條件互斥（除權後/結果後/比例設計）",
    ),
    RuleFamilyRecord(
        rule_family_id="RF-02", rule_family_name="配股Signal與組合評分",
        member_rule_ids=["CAND-HILTON-PLACEMENT-CHECKLIST-001", "CAND-HILTON-PLACEMENT-TSTOP-001",
                         "CAND-HILTON-GO-2020-001"],
        shared_analytical_purpose="判定配股是收貨還是派貨，以及成立後的持有/退出時間規則",
        distinct_conditions=["七利好六利淡清單", "半個月至一個月時間止蝕", "GO+20/20 組合觸發"],
        distinct_methodology_variants=[],
        true_duplicates=[], same_rule_new_evidence=[], context_variants=[],
        keep_separate_reason="清單/時間止蝕/組合評分是同一能力的三個正交判準，合併會丟失各自的 falsification",
    ),
    RuleFamilyRecord(
        rule_family_id="RF-03", rule_family_name="資本重組意圖（合股/削股/向下炒）",
        member_rule_ids=["CAND-HILTON-CONSOL-INTENT-001", "CAND-HILTON-CAPREORG-MAGNITUDE-001",
                         "CAND-HILTON-CUTPAR-POSITIVE-001", "CAND-HILTON-DOWNWARD-PLAY-001",
                         "CAND-HILTON-REPEAT-DILUTE-001"],
        shared_analytical_purpose="從股本行動序列判讀向下炒/慣犯/轉盈訊號，並計算重組威力倍數",
        distinct_conditions=["貼一仙合股", "ABC混合威力≥100倍", "獨立削股≈累虧", "長期陰跌+反覆印股兩必要條件", "供股間隔≤3年"],
        distinct_methodology_variants=[],
        true_duplicates=[], same_rule_new_evidence=[], context_variants=[],
        keep_separate_reason="五條規則對應五種互斥的股本行動形態；DOWNWARD-PLAY 與 REPEAT-DILUTE 的觸發序列不同（配股供股 vs 供股週期）",
    ),
    RuleFamilyRecord(
        rule_family_id="RF-04", rule_family_name="殼價估值與啤殼篩選",
        member_rule_ids=["CAND-HILTON-SHELL-PRICE-001", "CAND-HILTON-SHELLFARM-IPO-001",
                         "CAND-HILTON-SHELLFARM-TIMING-001", "CAND-HILTON-NONGO-FLOOR-001"],
        shared_analytical_purpose="估合理賣殼價/最低市值下限，並從IPO特徵篩出啤殼及其啟動窗",
        distinct_conditions=["殼價+扣水NAV", "舊主應得÷餘下比例", "集資額雙比較", "1.5-2年啟動窗"],
        distinct_methodology_variants=[],
        true_duplicates=[], same_rule_new_evidence=[], context_variants=[],
        keep_separate_reason="估值公式（靜態）與篩選/時窗（動態）輸入輸出不同",
    ),
    RuleFamilyRecord(
        rule_family_id="RF-05", rule_family_name="GO全購生命週期",
        member_rule_ids=["CAND-HILTON-GO-STAGE-MATRIX-001", "CAND-HILTON-2668-SEQUENCE-001",
                         "CAND-HILTON-BLOCKED-BOTHWAYS-001", "CAND-HILTON-WHITEKNIGHT-CB-001",
                         "CAND-HILTON-OLD-OWNER-STAKE-001"],
        shared_analytical_purpose="定位 GO/白武士/Non-GO 週期階段並套用分階段退出與推演規則",
        distinct_conditions=["A-E 五階段", "GO後一個月守GO價", "受阻兩路推演", "CB兌換後≥90%歸邊", "舊主9.x%保留"],
        distinct_methodology_variants=[],
        true_duplicates=[], same_rule_new_evidence=[], context_variants=[],
        keep_separate_reason="同屬一條生命週期主線的階段級規則；2668 模板是序列級整合，非重複",
    ),
    RuleFamilyRecord(
        rule_family_id="RF-06", rule_family_name="CCASS集中度估算與假象防護",
        member_rule_ids=["CAND-HILTON-CCASS-DRYNESS-CALC-001", "CAND-HILTON-DRYNESS-90-001",
                         "CAND-HILTON-CCASS-PARTCOUNT-001", "CAND-HILTON-FAKE-MOVE-EXCLUDE-001"],
        shared_analytical_purpose="主動估算貨源歸邊度並排除機制性假象；『乾』與『貨源集中』概念分離",
        distinct_conditions=["非CCASS全記M+鴻溝斷層", "90%門檻+M質素補足", "參與者數目下降", "公司行動日曆核對"],
        distinct_methodology_variants=[],
        true_duplicates=[], same_rule_new_evidence=[],
        context_variants=["DRYNESS-90 是決策門檻層；DRYNESS-CALC 是估算方法層——互補不重複"],
        keep_separate_reason="估算/門檻/趨勢/排除四層各自可獨立被 Luna 證偽",
    ),
    RuleFamilyRecord(
        rule_family_id="RF-07", rule_family_name="CCASS轉倉與存入意圖",
        member_rule_ids=["CAND-HILTON-CCASSIN-POSITION-001", "CAND-HILTON-RREPORT-DARK-001",
                         "CAND-HILTON-FAKE-MOVE-EXCLUDE-001"],
        shared_analytical_purpose="從跨行轉移/實物存入/異常接受推斷非散戶意圖（交貨/過倉/派貨前置）",
        distinct_conditions=["存入時的價格位置", "5%/10%比例門檻", "T+3 可見性"],
        distinct_methodology_variants=[],
        true_duplicates=[], same_rule_new_evidence=[], context_variants=[],
        keep_separate_reason="RREPORT-DARK 同時服務 RF-01（供股解讀）與本族（暗倉偵測）——跨族成員按 lineage 保留",
    ),
    RuleFamilyRecord(
        rule_family_id="RF-08", rule_family_name="派發/散貨偵測",
        member_rule_ids=["CAND-HILTON-7SIGNALS-EXIT-001", "CAND-HILTON-ANCHOR-DUMP-001",
                         "CAND-HILTON-BONUS-SHARE-29XX-001", "CAND-HILTON-CHIP-BREAKOUT-001"],
        shared_analytical_purpose="以財技/DI/CCASS/成交/媒體組合偵測莊家派發階段",
        distinct_conditions=["七信號程度×次數", "錨定壓回途中散貨", "29XX窗口掩藏", "蟹貨區返家鄉"],
        distinct_methodology_variants=[],
        true_duplicates=[], same_rule_new_evidence=[],
        context_variants=["ANCHOR-DUMP/CHIP-BREAKOUT 為 AUTHOR_INTERPRETATION 級——單獨標籤不與信號掃描器合併"],
        keep_separate_reason="掃描器是組合計分；心理機制類規則是解釋層，證偽途徑不同",
    ),
    RuleFamilyRecord(
        rule_family_id="RF-09", rule_family_name="收貨/入場時機",
        member_rule_ids=["CAND-HILTON-SPRING-DUCK-001", "CAND-HILTON-LIQUIDITY-PHASE-001"],
        shared_analytical_purpose="從量價異動與流動性形態辨認莊家收集/啟動前狀態",
        distinct_conditions=["低位連升+量爆第二日收市前", "低位難買=收貨中"],
        distinct_methodology_variants=[],
        true_duplicates=[], same_rule_new_evidence=[], context_variants=[],
        keep_separate_reason="公告前異動 vs 持續流動性形態，時間尺度與數據不同",
    ),
    RuleFamilyRecord(
        rule_family_id="RF-10", rule_family_name="控制權人物網絡與門檻意圖",
        member_rule_ids=["CAND-HILTON-THRESHOLD-HUG-001", "CAND-CHAUHIN-THRESHOLD-ASK-001",
                         "CAND-HILTON-FACTION-NETWORK-001", "CAND-HILTON-DI-ARTIFACT-001"],
        shared_analytical_purpose="從貼門檻持股/跨公司重複人物/申報假象推斷控制權意圖",
        distinct_conditions=["門檻−ε停駐", "29.97% vs 29.99% 兩例", "派系累積法", "DI三大盲點"],
        distinct_methodology_variants=["HILTON: 29.97%避GO案例", "CHAU_HIN: 29.99%門檻追問法"],
        true_duplicates=[],
        same_rule_new_evidence=[],
        context_variants=["THRESHOLD-HUG 與 THRESHOLD-ASK 為跨方法論變體——按 §11 不合併，僅記錄 meta 關係"],
        keep_separate_reason="方法論隔離；DI-ARTIFACT 是防護層非意圖推斷層",
    ),
    RuleFamilyRecord(
        rule_family_id="RF-11", rule_family_name="事件序列與量價判讀（大市層）",
        member_rule_ids=["CAND-HILTON-SPINOFF-PRESSURE-001", "CAND-HILTON-VOLUME-DIVERGENCE-001",
                         "CAND-CHAUHIN-BADNEWS-DECAY-001"],
        shared_analytical_purpose="分拆沽壓、成交分歧、消息反應鈍化的事件級判讀",
        distinct_conditions=["沽壓≤2-3月", "極端位置爆量", "壞消息殺傷力遞減"],
        distinct_methodology_variants=["HILTON: 分拆/成交量", "CHAU_HIN: 消息-價格反應"],
        true_duplicates=[], same_rule_new_evidence=["CAND-HILTON-SPINOFF-PRESSURE-001"],
        context_variants=[],
        keep_separate_reason="大市層訊號不直接適用個股，與個股能力分開",
    ),
    RuleFamilyRecord(
        rule_family_id="RF-12", rule_family_name="風險窗與倉位紀律",
        member_rule_ids=["CAND-HILTON-CEILING-GUARD-001", "CAND-HILTON-DIPBOUNCE-001",
                         "CAND-IVANL-LADDER-STAKE-001"],
        shared_analytical_purpose="以市值/升幅/時間窗定義風險邊界與注碼紀律",
        distinct_conditions=["市值天花板100億/20億", "急跌三條件", "市值階梯注碼"],
        distinct_methodology_variants=["HILTON: 天花板/斬倉反彈", "IVAN_L: 階梯注碼"],
        true_duplicates=[], same_rule_new_evidence=[], context_variants=[],
        keep_separate_reason="風險管理規則與訊號規則證偽途徑不同（組合層 vs 個股層）",
    ),
    RuleFamilyRecord(
        rule_family_id="RF-13", rule_family_name="L型絕地低市值模式（IVAN_L專屬）",
        member_rule_ids=["CAND-IVANL-LXING-SCREEN-001", "CAND-IVANL-GO-MEDIATOR-001"],
        shared_analytical_purpose="半新股低市值沉底模式的篩選與 GO 兌現機制",
        distinct_conditions=["四支柱篩選", "階梯=GO機率篩 p≈0.0325", "≥2-3年窗"],
        distinct_methodology_variants=[],
        true_duplicates=[], same_rule_new_evidence=[], context_variants=[],
        keep_separate_reason="IVAN_L 專屬方法論；與 Hilton 啤殼篩選相似但觸發條件與量化基礎不同",
    ),
    RuleFamilyRecord(
        rule_family_id="RF-14", rule_family_name="方法論自我防護與數據品質",
        member_rule_ids=["CAND-HILTON-ADJECTIVE-DECOMPOSE-001", "CAND-IVANL-MCAP-DATA-RISK-001",
                         "CAND-IVANL-SCREENING-NOT-DISCRIMINATOR-001"],
        shared_analytical_purpose="防止形容詞替代數字、防回測數據偏差、防篩選條件被當成判別器",
        distinct_conditions=["形容詞→量化映射", "mcap重建旗標", "top-k貢獻報告"],
        distinct_methodology_variants=[],
        true_duplicates=[], same_rule_new_evidence=[], context_variants=[],
        keep_separate_reason="防護規則適用於所有能力，不屬於任何單一分析對象",
    ),
]

# ============================================================ CAPABILITIES
CAPABILITIES: List[Capability] = [
    Capability(
        capability_id="CAP-01", capability_name="重建操作者成本與合理殼價",
        what_doctor_can_now_do="以殼價+扣水NAV估合理賣殼價；以舊主應得殼價÷餘下比例估 Non-GO 最低市值；以白武士削傷/專業費/營運成本估表面成本與 CB 攤薄後平均成本",
        supporting_rule_families=["RF-04", "RF-05"], supporting_rule_ids=["CAND-HILTON-SHELL-PRICE-001", "CAND-HILTON-NONGO-FLOOR-001", "CAND-HILTON-WHITEKNIGHT-CB-001"],
        supporting_methodologies=["HILTON"],
        source_ids=["HILTON-CAIJI-L2", "HILTON-CAIJI-L3", "HILTON-CAIJI-L4"],
        required_input_data=["當期殼價行情", "NAV明細（商譽/物業所在地/現金）", "已發行股數", "交易後股權結構", "CB條款"],
        output_type=OutputType.DERIVED_MEASURE,
        confidence_level=ConfidenceLevel.PARTIALLY_CASE_SUPPORTED,
        known_limitations=["殼價行情隨時間變動須外部更新", "NAV扣水為經驗規則非會計準則", "場外找數可令公式前提失效"],
        falsification_conditions=["實際GO成交價系統性偏離(殼價+扣水NAV)公式", "Non-GO案例實際市值路徑低於公式下限"],
        real_case_validation_status="部分案例支持（1143/01250 課堂數字；未以本站數據獨立重算）",
    ),
    Capability(
        capability_id="CAP-02", capability_name="判定供股意圖（供乾vs供錢）與R報告解讀",
        what_doctor_can_now_do="除權後市價 vs 供股價分類供乾/供錢；以R報告申請份數/異常接受比例讀散戶冷清與暗倉過倉；質數比例碎股效應標記；供股復仇記三條件+時間窗",
        supporting_rule_families=["RF-01"], supporting_rule_ids=["CAND-HILTON-SUPPLY-INTENT-001", "CAND-HILTON-RREPORT-COUNT-001", "CAND-HILTON-RREPORT-DARK-001", "CAND-HILTON-REVENGE-TIMING-001", "CAND-CHAUHIN-PRIME-RATIO-001"],
        supporting_methodologies=["HILTON", "CHAU_HIN"],
        source_ids=["HILTON-CAIJI-L1", "CHAUHIN-COURSE-L2A"],
        required_input_data=["除權日後價格序列", "供股價/比例/折讓", "R報告（申請份數、接受比例、促使人士）", "Last Pay Day", "要約期市價vs供股價"],
        output_type=OutputType.RULE_OUTPUT,
        confidence_level=ConfidenceLevel.UNVALIDATED_CASE_DERIVED,
        known_limitations=["01236暗倉判讀為作者解讀需CCASS佐證", "R報告份數受集資規模影響"],
        falsification_conditions=["除權後走勢與目的分類系統性不符", "份數≤30與>30的後續表現無差異"],
        real_case_validation_status="PENDING_LUNA",
    ),
    Capability(
        capability_id="CAP-03", capability_name="配股Signal分類與成立後時間管理",
        what_doctor_can_now_do="以七利好六利淡清單分類配股為ACCUMULATION/DISTRIBUTION/UNCLASSIFIED；成立後套用半個月至一個月時間止蝕；辨認GO+20/20高分組合",
        supporting_rule_families=["RF-02"], supporting_rule_ids=["CAND-HILTON-PLACEMENT-CHECKLIST-001", "CAND-HILTON-PLACEMENT-TSTOP-001", "CAND-HILTON-GO-2020-001"],
        supporting_methodologies=["HILTON"],
        source_ids=["HILTON-CAIJI-L3", "HILTON-CAIJI-L2"],
        required_input_data=["配股公告（形式/比例/折讓/承配人人數與披露）", "價格位置", "GO完成狀態", "入場日與隨後日曆"],
        output_type=OutputType.RULE_OUTPUT,
        confidence_level=ConfidenceLevel.UNVALIDATED_CASE_DERIVED,
        known_limitations=["GO+20/20『八至九成勝率』為課堂口述統計無樣本清單"],
        falsification_conditions=["清單分類與事後價格路徑無統計相關", "時間止蝕劣於持有", "20/20勝率回測顯著偏低"],
        real_case_validation_status="PENDING_LUNA",
    ),
    Capability(
        capability_id="CAP-04", capability_name="資本重組意圖判讀與向下炒識別",
        what_doctor_can_now_do="合股意圖四分類（貼仙/印平股前奏/吸基金/負面預設）；混合重組威力倍數計算（≥100倍警告、~2,000倍離場）；獨立削股轉盈訊號；向下炒兩必要條件識別與永久避開；反覆供股慣犯標記",
        supporting_rule_families=["RF-03"], supporting_rule_ids=["CAND-HILTON-CONSOL-INTENT-001", "CAND-HILTON-CAPREORG-MAGNITUDE-001", "CAND-HILTON-CUTPAR-POSITIVE-001", "CAND-HILTON-DOWNWARD-PLAY-001", "CAND-HILTON-REPEAT-DILUTE-001"],
        supporting_methodologies=["HILTON"],
        source_ids=["HILTON-CAIJI-L7", "HILTON-CAIJI-L5", "HILTON-CAIJI-L1"],
        required_input_data=["股本行動序列（合股/削股/拆細/供股/配股/CB）", "面值與法定/已發行/未發行股數（月報表）", "長期價格序列", "關連收購記錄"],
        output_type=OutputType.RULE_OUTPUT,
        confidence_level=ConfidenceLevel.PARTIALLY_CASE_SUPPORTED,
        known_limitations=["488轉盈案例屬大價股外推到細價股未驗證", "威力倍數為乘積近似"],
        falsification_conditions=["貼仙合股樣本後續不差於一般仙股", "高威力重組標記樣本回升率不低於對照"],
        real_case_validation_status="部分案例支持（8071/941/616/1492 課堂數字）",
    ),
    Capability(
        capability_id="CAP-05", capability_name="GO全購生命週期階段定位",
        what_doctor_can_now_do="A-E五階段定位+分階段退出規則；GO後一個月守GO價分界；受阻兩路推演；莊家完整週期序列模板（2668型）；白武士CB路徑動機判準；舊主留一手強度分級",
        supporting_rule_families=["RF-05"], supporting_rule_ids=["CAND-HILTON-GO-STAGE-MATRIX-001", "CAND-HILTON-2668-SEQUENCE-001", "CAND-HILTON-BLOCKED-BOTHWAYS-001", "CAND-HILTON-WHITEKNIGHT-CB-001", "CAND-HILTON-OLD-OWNER-STAKE-001"],
        supporting_methodologies=["HILTON"],
        source_ids=["HILTON-CAIJI-L2", "HILTON-CAIJI-L4", "HILTON-CAIJI-2668CASE"],
        required_input_data=["3.7/3.8通告日", "易手日/GO起止日/GO價", "新主身份與往績", "DI序列", "R報告"],
        output_type=OutputType.RULE_OUTPUT,
        confidence_level=ConfidenceLevel.PARTIALLY_CASE_SUPPORTED,
        known_limitations=["2668日期為課堂敘述，可用本站DI/Turso獨立覆核", "有條件GO失敗風險須另計"],
        falsification_conditions=["C階段GO結束前兩日離場劣於持有", "D階段守GO價與後續回報無相關", "序列模板回測命中率不高於隨機對齊"],
        real_case_validation_status="部分案例支持（2668/1143/0607；未獨立重算）",
    ),
    Capability(
        capability_id="CAP-06", capability_name="CCASS歸邊估算與假象防護",
        what_doctor_can_now_do="非CCASS+券商鴻溝法主動估算歸邊%；90%門檻+M質素分層；參與者數目下降趨勢；公司行動假異動排除",
        supporting_rule_families=["RF-06"], supporting_rule_ids=["CAND-HILTON-CCASS-DRYNESS-CALC-001", "CAND-HILTON-DRYNESS-90-001", "CAND-HILTON-CCASS-PARTCOUNT-001", "CAND-HILTON-FAKE-MOVE-EXCLUDE-001"],
        supporting_methodologies=["HILTON"],
        source_ids=["HILTON-CAIJI-L7", "HILTON-CAIJI-L8", "HILTON-CAIJI-L4", "HILTON-CAIJI-L1"],
        required_input_data=["CCASS participant持股快照序列", "總已發行股數", "公司行動日曆", "M身份/往績"],
        output_type=OutputType.DERIVED_MEASURE,
        confidence_level=ConfidenceLevel.UNVALIDATED_CASE_DERIVED,
        known_limitations=["鴻溝界線為經驗值須自適應", "券商類型標籤（外資=M偏）須以本站134k行獨立驗證", "實體股/OTC在CCASS外"],
        falsification_conditions=["鴻溝法估算與官方『股權高度集中』通告披露值系統性背離"],
        real_case_validation_status="PENDING_LUNA（本站有134k行持倉可即時驗證——高優先）",
    ),
    Capability(
        capability_id="CAP-07", capability_name="CCASS轉倉/存入意圖判讀",
        what_doctor_can_now_do="CCASS In位置判讀（高位偏派貨/低位先炒後派，5%/10%門檻）；射倉序列頻密化=部署接近；R報告暗倉過倉線索；T+3可見性處理",
        supporting_rule_families=["RF-07"], supporting_rule_ids=["CAND-HILTON-CCASSIN-POSITION-001", "CAND-HILTON-RREPORT-DARK-001", "CAND-HILTON-FAKE-MOVE-EXCLUDE-001"],
        supporting_methodologies=["HILTON"],
        source_ids=["HILTON-CAIJI-L8", "HILTON-CAIJI-L1"],
        required_input_data=["CCASS實物存入記錄", "跨行轉移序列", "存入者身份", "價格位置", "T+3窗口"],
        output_type=OutputType.INFERENCE,
        confidence_level=ConfidenceLevel.UNVALIDATED_CASE_DERIVED,
        known_limitations=["人頭戶不可辨認", "射倉方向不可由單次判斷"],
        falsification_conditions=["高位存入樣本其後派發率不顯著高於對照"],
        real_case_validation_status="PENDING_LUNA",
    ),
    Capability(
        capability_id="CAP-08", capability_name="派發/散貨階段偵測",
        what_doctor_can_now_do="七信號掃描（散貨財技/DI減持/CCASS出貨以升幅校準/震倉界線/發水資產/媒體曝光/大成交金額+分鐘圖）；錨定散貨與蟹貨區返家鄉解釋層；29XX窗口標記",
        supporting_rule_families=["RF-08"], supporting_rule_ids=["CAND-HILTON-7SIGNALS-EXIT-001", "CAND-HILTON-ANCHOR-DUMP-001", "CAND-HILTON-BONUS-SHARE-29XX-001", "CAND-HILTON-CHIP-BREAKOUT-001"],
        supporting_methodologies=["HILTON"],
        source_ids=["HILTON-CAIJI-L8", "HILTON-CAIJI-L1", "HILTON-CAIJI-L3", "HILTON-CAIJI-L4"],
        required_input_data=["財技通告序列", "DI序列", "CCASS持倉序列", "日+分鐘成交量", "市值", "媒體曝光（人工）"],
        output_type=OutputType.RULE_OUTPUT,
        confidence_level=ConfidenceLevel.UNVALIDATED_CASE_DERIVED,
        known_limitations=["直觀出貨格只在少部分個案出現", "心理機制類規則（錨定/蟹貨）屬作者解讀"],
        falsification_conditions=["七信號計分與事後30日回撤無統計相關"],
        real_case_validation_status="PENDING_LUNA",
    ),
    Capability(
        capability_id="CAP-09", capability_name="收貨/入場時機辨認",
        what_doctor_can_now_do="公告前量價異動（春江鴨）第二日收市前追入法；流動性反訊號（低位難買=收貨中/高位易沽=散貨期）；蟹貨區突破確認買點",
        supporting_rule_families=["RF-09", "RF-08"], supporting_rule_ids=["CAND-HILTON-SPRING-DUCK-001", "CAND-HILTON-LIQUIDITY-PHASE-001", "CAND-HILTON-CHIP-BREAKOUT-001"],
        supporting_methodologies=["HILTON"],
        source_ids=["HILTON-CAIJI-L2", "HILTON-CAIJI-L3", "HILTON-CAIJI-L4"],
        required_input_data=["日成交量/收盤序列", "買賣盤深度", "歷史成交量分佈"],
        output_type=OutputType.INFERENCE,
        confidence_level=ConfidenceLevel.UNVALIDATED_CASE_DERIVED,
        known_limitations=["拆倉2-3%門檻為實務經驗值", "僵屍殼與收貨形態難區分"],
        falsification_conditions=["第二日收市前追入統計不優於隨機低位買入"],
        real_case_validation_status="PENDING_LUNA",
    ),
    Capability(
        capability_id="CAP-10", capability_name="控制權人物網絡與門檻意圖",
        what_doctor_can_now_do="貼門檻持股停駐偵測（避GO/保地位/避申報）；跨公司重複人物派系累積；舊主留貨強度；DI申報假象排除",
        supporting_rule_families=["RF-10"], supporting_rule_ids=["CAND-HILTON-THRESHOLD-HUG-001", "CAND-CHAUHIN-THRESHOLD-ASK-001", "CAND-HILTON-FACTION-NETWORK-001", "CAND-HILTON-DI-ARTIFACT-001"],
        supporting_methodologies=["HILTON", "CHAU_HIN"],
        source_ids=["HILTON-CAIJI-L3", "HILTON-CAIJI-L6", "HILTON-CAIJI-L2", "CHAUHIN-COURSE-L2A"],
        required_input_data=["filer持股披露序列", "董事/高管名單", "改名/重組歷史", "門檻列表"],
        output_type=OutputType.INFERENCE,
        confidence_level=ConfidenceLevel.UNVALIDATED_CASE_DERIVED,
        known_limitations=["同名≠同人（IDENTITY_AMBIGUOUS合約）", "派系名單本體待累積"],
        falsification_conditions=["貼門檻停駐樣本後續路徑與隨機持股群無差異"],
        real_case_validation_status="PENDING_LUNA（02318 DION 1,780行可先驗 THRESHOLD-HUG）",
    ),
    Capability(
        capability_id="CAP-11", capability_name="L型絕地低市值模式評估",
        what_doctor_can_now_do="四支柱篩選半新股候選；市值階梯作GO機率篩（state→event→payoff）；≥2-3年窗效能評估；階梯注碼與炒高後分級警覺",
        supporting_rule_families=["RF-13", "RF-12"], supporting_rule_ids=["CAND-IVANL-LXING-SCREEN-001", "CAND-IVANL-GO-MEDIATOR-001", "CAND-IVANL-LADDER-STAKE-001"],
        supporting_methodologies=["IVAN_L"],
        source_ids=["IVANL-LXING-COURSE", "IVANL-LXING-GO-MECH"],
        required_input_data=["上市日期/集資額/招股結果", "歷史市值（含股本品質旗標）", "GO事件記錄", "hit_rate_12m/24m/36m/60m"],
        output_type=OutputType.RULE_OUTPUT,
        confidence_level=ConfidenceLevel.PARTIALLY_CASE_SUPPORTED,
        known_limitations=["原研究有生存偏差+市值重建誤差（已列一級風險）", "禁止倒推『入階梯必GO』"],
        falsification_conditions=["獨立樣本（含除牌股）階梯組GO率優勢消失"],
        real_case_validation_status="唯一有量化支持的capability（原研究統計），仍需含除牌股的獨立樣本",
    ),
    Capability(
        capability_id="CAP-12", capability_name="風險窗界定與倉位紀律",
        what_doctor_can_now_do="市值/升幅天花板警戒+推高保護位；急跌博反彈被迫斬倉三條件；時間止蝕框架（配股一個月/供股半年/啤殼1.5-2年/L型24-36月）",
        supporting_rule_families=["RF-12"], supporting_rule_ids=["CAND-HILTON-CEILING-GUARD-001", "CAND-HILTON-DIPBOUNCE-001", "CAND-HILTON-SHELLFARM-TIMING-001", "CAND-IVANL-LADDER-STAKE-001"],
        supporting_methodologies=["HILTON", "IVAN_L"],
        source_ids=["HILTON-CAIJI-L8", "HILTON-CAIJI-急跌", "HILTON-CAIJI-L4", "IVANL-LXING-GO-MECH"],
        required_input_data=["市值", "升幅倍數", "每日最低價", "同系股票同日表現", "分鐘級成交量"],
        output_type=OutputType.RULE_OUTPUT,
        confidence_level=ConfidenceLevel.UNVALIDATED_CASE_DERIVED,
        known_limitations=["天花板數字為課堂時點市場環境值", "超級項目可破天花板（0530反例已記錄）"],
        falsification_conditions=["3-4倍警戒離場事後總回報顯著劣於持有至出貨信號"],
        real_case_validation_status="PENDING_LUNA",
    ),
    Capability(
        capability_id="CAP-13", capability_name="大市層事件判讀（分拆/成交量/消息反應）",
        what_doctor_can_now_do="分拆首輪沽壓（含被動基金強制沽售加權）；大成交分歧度量與極端位置解讀；壞消息失效=流動性支撐線索",
        supporting_rule_families=["RF-11"], supporting_rule_ids=["CAND-HILTON-SPINOFF-PRESSURE-001", "CAND-HILTON-VOLUME-DIVERGENCE-001", "CAND-CHAUHIN-BADNEWS-DECAY-001"],
        supporting_methodologies=["HILTON", "CHAU_HIN"],
        source_ids=["HILTON-CAIJI-L5", "HILTON-CAIJI-急跌", "HILTON-CAIJI-L5", "CHAUHIN-COURSE-L1"],
        required_input_data=["分拆公告與母公司指數成分", "成交量異常偵測", "消息-價格反應序列"],
        output_type=OutputType.INFERENCE,
        confidence_level=ConfidenceLevel.UNVALIDATED_CASE_DERIVED,
        known_limitations=["大市層訊號不直接適用個股"],
        falsification_conditions=["極端位置爆量後反彈率不顯著高於基準"],
        real_case_validation_status="PENDING_LUNA",
    ),
    Capability(
        capability_id="CAP-14", capability_name="分析方法自我防護與數據品質把關",
        what_doctor_can_now_do="形容詞→量化判準映射（乾=90%歸邊等）；歷史市值重建與生存偏差旗標；篩選條件≠贏家判別器聲明+top-k貢獻報告",
        supporting_rule_families=["RF-14"], supporting_rule_ids=["CAND-HILTON-ADJECTIVE-DECOMPOSE-001", "CAND-IVANL-MCAP-DATA-RISK-001", "CAND-IVANL-SCREENING-NOT-DISCRIMINATOR-001"],
        supporting_methodologies=["HILTON", "IVAN_L"],
        source_ids=["HILTON-CAIJI-L6", "IVANL-LXING-GO-MECH"],
        required_input_data=["歸邊%數字", "股本數據來源品質", "樣本構成"],
        output_type=OutputType.RULE_OUTPUT,
        confidence_level=ConfidenceLevel.PARTIALLY_CASE_SUPPORTED,
        known_limitations=["部分規則為內部紀律，以矛盾率監察而非傳統證偽"],
        falsification_conditions=["被標記artifact的申報事後證實為真實持股的比例偏高"],
        real_case_validation_status="部分支持（IVAN研究自身限制聲明）",
    ),
]

# ============================================================ VALIDATION GAPS
VALIDATION_GAPS: List[ValidationGap] = [
    ValidationGap(capability_id="CAP-02", source_method_support=True, case_support=False, contradictory_case=False, quantitative_support=True, point_in_time_support=True, falsification_defined=True, real_case_validation_required=True, gap_priority="HIGH"),
    ValidationGap(capability_id="CAP-03", source_method_support=True, case_support=False, contradictory_case=False, quantitative_support=True, point_in_time_support=True, falsification_defined=True, real_case_validation_required=True, gap_priority="HIGH"),
    ValidationGap(capability_id="CAP-04", source_method_support=True, case_support=True, contradictory_case=False, quantitative_support=True, point_in_time_support=True, falsification_defined=True, real_case_validation_required=True, gap_priority="MEDIUM"),
    ValidationGap(capability_id="CAP-05", source_method_support=True, case_support=True, contradictory_case=False, quantitative_support=True, point_in_time_support=True, falsification_defined=True, real_case_validation_required=True, gap_priority="HIGH"),
    ValidationGap(capability_id="CAP-06", source_method_support=True, case_support=False, contradictory_case=False, quantitative_support=True, point_in_time_support=True, falsification_defined=True, real_case_validation_required=True, gap_priority="HIGH"),
    ValidationGap(capability_id="CAP-07", source_method_support=True, case_support=False, contradictory_case=False, quantitative_support=False, point_in_time_support=True, falsification_defined=True, real_case_validation_required=True, gap_priority="HIGH"),
    ValidationGap(capability_id="CAP-08", source_method_support=True, case_support=False, contradictory_case=False, quantitative_support=True, point_in_time_support=True, falsification_defined=True, real_case_validation_required=True, gap_priority="HIGH"),
    ValidationGap(capability_id="CAP-09", source_method_support=True, case_support=False, contradictory_case=False, quantitative_support=False, point_in_time_support=True, falsification_defined=True, real_case_validation_required=True, gap_priority="MEDIUM"),
    ValidationGap(capability_id="CAP-10", source_method_support=True, case_support=False, contradictory_case=False, quantitative_support=False, point_in_time_support=True, falsification_defined=True, real_case_validation_required=True, gap_priority="HIGH"),
    ValidationGap(capability_id="CAP-11", source_method_support=True, case_support=True, contradictory_case=False, quantitative_support=True, point_in_time_support=False, falsification_defined=True, real_case_validation_required=True, gap_priority="MEDIUM"),
    ValidationGap(capability_id="CAP-12", source_method_support=True, case_support=False, contradictory_case=False, quantitative_support=True, point_in_time_support=True, falsification_defined=True, real_case_validation_required=True, gap_priority="MEDIUM"),
    ValidationGap(capability_id="CAP-13", source_method_support=True, case_support=False, contradictory_case=False, quantitative_support=False, point_in_time_support=True, falsification_defined=True, real_case_validation_required=True, gap_priority="LOW"),
    ValidationGap(capability_id="CAP-01", source_method_support=True, case_support=True, contradictory_case=False, quantitative_support=True, point_in_time_support=True, falsification_defined=True, real_case_validation_required=True, gap_priority="MEDIUM"),
    ValidationGap(capability_id="CAP-14", source_method_support=True, case_support=True, contradictory_case=False, quantitative_support=True, point_in_time_support=False, falsification_defined=True, real_case_validation_required=False, gap_priority="LOW"),
]

# ============================================================ LUNA TARGETS
LUNA_TARGETS: List[LunaTarget] = [
    LunaTarget(
        target_id="LT-01", capability_id="CAP-02", rule_family_id="RF-01",
        claim_to_test="除權後大股東推高市價=供錢、壓住貼供股價橫行=供乾；供乾/供錢分類可由除權後價格路徑事前判定",
        required_case_characteristics=["已完成供股除權", "有包銷安排", "除權後至少90個交易日價格"],
        required_evidence=["除權後日收盤序列", "供股價", "R報告（大股東最終認購/包銷承接量）", "包銷商身份"],
        t0_fields_required=["rights_issue_record(ex_ratio, offer_price, ratio, underwriter_id)", "daily_close(ex_date, ex_date+90d)", "mkt_cap"],
        t1_outcome_fields_required=["final_subscription_result(underwriter_takeup_share, application_count)", "price_path_90d", "markup_vs_range"],
        support_condition="事前分類為供乾的案例，包銷商/大股東最終承接顯著高於供錢分類案例",
        contradiction_condition="分類為供乾但包銷商最終棄認（承接低於上限）比例偏高",
        context_dependent_condition="大市系統性下跌期的橫行應剔除或另計",
        falsification_trigger="分類與包銷承接結果的關聯在≥可得的完整供股案例集中不成立",
        minimum_case_count=None, priority="HIGH",
    ),
    LunaTarget(
        target_id="LT-02", capability_id="CAP-03", rule_family_id="RF-02",
        claim_to_test="低位+大比例大折讓+配新股+≥6名匿名承配的配股，半個月至一個月內啟動的比例顯著高於高位/小比例/配舊股組",
        required_case_characteristics=["配股公告（一般授權或特別授權）", "可判定公告時價格位置"],
        required_evidence=["公告條款", "公告前60日價格", "承配人人數與披露狀態", "其後60交易日價格"],
        t0_fields_required=["placement_record(form, ratio, discount, placee_count, disclosed)", "price_position_t0"],
        t1_outcome_fields_required=["launch_within_30d", "return_1m/3m", "timestop_mwould_triggered"],
        support_condition="清單ACCUMULATION組的30日啟動率顯著高於DISTRIBUTION組",
        contradiction_condition="ACCUMULATION組其後表現與DISTRIBUTION組無差異",
        context_dependent_condition="市況急跌期啟動延遲應另計（時間止蝕失效屬環境非規則）",
        falsification_trigger="兩組30日啟動率差異不顯著",
        minimum_case_count=None, priority="HIGH",
    ),
    LunaTarget(
        target_id="LT-03", capability_id="CAP-03", rule_family_id="RF-02",
        claim_to_test="GO結束後20/20配股組合的三至四個月回報分佈（課堂聲稱勝率八至九成、常見3-4倍）",
        required_case_characteristics=["GO已完成", "其後12個月內有配股公告", "配股比例≈20%且折讓≈20%"],
        required_evidence=["GO完成日", "配股條款", "其後120交易日價格"],
        t0_fields_required=["go_completion_date", "placement_record(ratio≈20%, discount≈20%)"],
        t1_outcome_fields_required=["return_3m/4m", "win_rate", "max_drawdown"],
        support_condition="實際勝率與倍數與課堂聲稱同量級（八至九成/3-4倍）",
        contradiction_condition="勝率顯著低於八成或倍數中位顯著低於3倍",
        context_dependent_condition="僅GO後配股；非GO後的20/20不屬本組合",
        falsification_trigger="可得的GO+20/20案例集統計與聲稱量級明顯背離",
        minimum_case_count=None, priority="HIGH",
    ),
    LunaTarget(
        target_id="LT-04", capability_id="CAP-05", rule_family_id="RF-05",
        claim_to_test="GO結束後一個月守住GO價+成交配合的案例，其後回報顯著優於跌穿GO價未收復組（D階段分界）",
        required_case_characteristics=["已完成GO", "GO結束後至少一年價格"],
        required_evidence=["GO價", "GO結束日", "其後30日價格vs GO價", "其後一年價格"],
        t0_fields_required=["go_record(gO_price, go_end_date)"],
        t1_outcome_fields_required=["hold_above_go_30d", "return_1y", "max_drawdown_1y"],
        support_condition="守GO價組1年回報分佈顯著優於跌穿組",
        contradiction_condition="兩組回報無差異或跌穿組更佳",
        context_dependent_condition="股災期跌穿不算規則失敗（環境項）",
        falsification_trigger="分界與1年回報無統計相關",
        minimum_case_count=None, priority="HIGH",
    ),
    LunaTarget(
        target_id="LT-05", capability_id="CAP-07", rule_family_id="RF-07",
        claim_to_test="市價高於GO價的要約期內，異常高的接受比例與其後CCASS貨源流向新主關聯券商一致（暗倉過倉假設，01236型）",
        required_case_characteristics=["GO要約期內市價>GO價", "R報告接受比例異常", "要約期後90日CCASS快照"],
        required_evidence=["R報告接受比例", "市價/GO價對照", "CCASS participant變化"],
        t0_fields_required=["go_offer(acceptance_ratio, mkt_vs_go)"],
        t1_outcome_fields_required=["ccass_transfer_destination(90d)", "controller_stake_change"],
        support_condition="異常接受部份與新主關聯券商持倉增加方向一致",
        contradiction_condition="接受部份流向無關聯散戶行或場外消失",
        context_dependent_condition="指數剔除等機械沽壓期另計",
        falsification_trigger="CCASS流向與關聯券商假設不一致的案例佔多數",
        minimum_case_count=None, priority="HIGH",
    ),
    LunaTarget(
        target_id="LT-06", capability_id="CAP-07", rule_family_id="RF-07",
        claim_to_test="實物存入CCASS的位置判讀：高位存入（≥5%）其後派發/回撤風險高於低位存入組",
        required_case_characteristics=["有實物存入事件", "可判定存入時價格位置", "排除公司行動假異動"],
        required_evidence=["存入比例與日期", "存入者身份", "其後180日價格與CCASS分佈"],
        t0_fields_required=["ccass_in_event(ratio, date, position_class)"],
        t1_outcome_fields_required=["return_180d", "max_drawdown_180d", "ccass_dispersion_change"],
        support_condition="HIGH組回撤顯著大於LOW組",
        contradiction_condition="兩組風險無差異",
        context_dependent_condition="LOW存入後遇市況急跌的下行使另計",
        falsification_trigger="位置分級與其後回撤無關",
        minimum_case_count=None, priority="HIGH",
    ),
    LunaTarget(
        target_id="LT-07", capability_id="CAP-04", rule_family_id="RF-03",
        claim_to_test="股價接近一仙宣布合股的案例，其後派發向下路徑（再合股/供股/續跌）比例顯著高於對照仙股",
        required_case_characteristics=["合股公告時股價≤0.05", "有其後24個月資本行動與價格"],
        required_evidence=["合股公告", "公告時股價", "其後資本行動序列", "價格路徑"],
        t0_fields_required=["consolidation_record(ratio, price_at_announcement)"],
        t1_outcome_fields_required=["subsequent_capital_actions_24m", "return_24m"],
        support_condition="貼仙合股組的向下續作率顯著高於對照",
        contradiction_condition="貼仙合股組回升/向上的比例不低於對照",
        context_dependent_condition="白武士重組配套的合股另計",
        falsification_trigger="兩組向下續作率無差異",
        minimum_case_count=None, priority="HIGH",
    ),
    LunaTarget(
        target_id="LT-08", capability_id="CAP-06", rule_family_id="RF-06",
        claim_to_test="券商鴻溝法估算歸邊與官方『股權高度集中』通告披露值的吻合度（平台已有134k行持倉可測）",
        required_case_characteristics=["曾發股權高度集中通告的股票", "通告前後CCASS快照"],
        required_evidence=["通告披露的持股集中數字", "同期CCASS participant分佈", "總已發行股數"],
        t0_fields_required=["concentration_alert(disclosed_top_holders, date)"],
        t1_outcome_fields_required=["gap_method_estimate(same_date)", "estimate_error"],
        support_condition="鴻溝法估算與披露值誤差在規則聲明的精度內（>90%即可用級）",
        contradiction_condition="系統性背離且方向一致（高估或低估）",
        context_dependent_condition="非CCASS實體股比例大的股票誤差上限放寬",
        falsification_trigger="估算與披露值背離無法由實體股解釋",
        minimum_case_count=None, priority="HIGH",
    ),
    LunaTarget(
        target_id="LT-09", capability_id="CAP-10", rule_family_id="RF-10",
        claim_to_test="持股停駐法定門檻微下方（29-30%區）後續出現 Non-GO 路徑（配股/CB/供股包銷入主）的比例顯著高於隨機持股群",
        required_case_characteristics=["filer持股序列顯示貼門檻停駐≥60日", "其後24個月資本行動"],
        required_evidence=["DI持股序列", "其後配股/供股/CB公告", "控制權變動記錄"],
        t0_fields_required=["di_series(filer_id, pct, date)", "threshold_hug_flag"],
        t1_outcome_fields_required=["subsequent_control_path_24m(nongo/go/none)"],
        support_condition="停駐組Non-GO路徑比例顯著高於對照",
        contradiction_condition="停駐組與隨機組後續路徑無差異",
        context_dependent_condition="財務投資者長期持股停駐另計",
        falsification_trigger="兩組路徑分佈無統計差異",
        minimum_case_count=None, priority="HIGH",
    ),
    LunaTarget(
        target_id="LT-10", capability_id="CAP-08", rule_family_id="RF-08",
        claim_to_test="七大出貨信號計分（尤其升幅校準後的CCASS減持+大成交金額）與其後30/60日回撤正相關",
        required_case_characteristics=["升幅≥3倍的財技股", "有CCASS+DI+成交序列"],
        required_evidence=["信號觸發記錄", "其後30/60日價格"],
        t0_fields_required=["signal_score(date, components)"],
        t1_outcome_fields_required=["return_30d/60d", "max_drawdown_30d/60d"],
        support_condition="計分與回撤的等級相關顯著",
        contradiction_condition="計分與回撤無關",
        context_dependent_condition="大市系統性回撤期個股信號貢獻需分離",
        falsification_trigger="相關係數不顯著",
        minimum_case_count=None, priority="HIGH",
    ),
    LunaTarget(
        target_id="LT-11", capability_id="CAP-11", rule_family_id="RF-13",
        claim_to_test="市值階梯狀態的GO機率優勢在含除牌股的獨立樣本中重現（原研究：11.2% vs 3.6%，p≈0.0325）",
        required_case_characteristics=["含已除牌/清盤股票的樣本", "可重建歷史市值（須帶股本品質旗標）"],
        required_evidence=["歷史市值序列", "GO公告記錄", "除牌/清盤結果"],
        t0_fields_required=["ladder_state(date)", "mcap_reconstruction_flag"],
        t1_outcome_fields_required=["go_within_36m", "delisting_outcome"],
        support_condition="含除牌樣本中階梯組GO率仍顯著高於從未入階梯組",
        contradiction_condition="加入除牌股後優勢消失",
        context_dependent_condition="2018年前老股與新上市股票分層",
        falsification_trigger="生存偏差修正後優勢不復存在",
        minimum_case_count=None, priority="HIGH",
    ),
    LunaTarget(
        target_id="LT-12", capability_id="CAP-12", rule_family_id="RF-12",
        claim_to_test="急跌股中被迫斬倉型（同系多股同日急跌/大股東未減持）其後20日反彈率顯著高於莊家主動散貨型",
        required_case_characteristics=["單日跌幅≥50%的細價股", "可取得同系/同戶口股票當日表現"],
        required_evidence=["急跌日全板塊表現", "大股東DI", "其後20日價格", "分鐘級成交量（可得時）"],
        t0_fields_required=["crash_record(date, pct_drop, same_group_drop_count, controller_di_change)"],
        t1_outcome_fields_required=["bounce_20d", "return_20d"],
        support_condition="FORCED組反彈率/幅度顯著高於DELIBERATE組",
        contradiction_condition="兩組反彈無差異",
        context_dependent_condition="停牌復牌個案的價格跳空另計",
        falsification_trigger="分類與反彈無關",
        minimum_case_count=None, priority="MEDIUM",
    ),
    LunaTarget(
        target_id="LT-13", capability_id="CAP-05", rule_family_id="RF-05",
        claim_to_test="GO後舊主保留9.x%（貼10%下）的案例，其後12個月回報分佈優於全清倉案例（舊主留一手訊號）",
        required_case_characteristics=["控制權轉移完成", "舊主轉移後持股披露清晰"],
        required_evidence=["舊主保留比例", "其後12個月價格"],
        t0_fields_required=["old_owner_stake(pct_band: 9.x/4.x/0)"],
        t1_outcome_fields_required=["return_12m"],
        support_condition="9.x%組回報分佈優於0%組（4.x%居中或與0%無差異）",
        contradiction_condition="保留組與清倉組無差異",
        context_dependent_condition="禁售期內被迫保留不算訊號",
        falsification_trigger="分組回報無統計差異",
        minimum_case_count=None, priority="MEDIUM",
    ),
    LunaTarget(
        target_id="LT-14", capability_id="CAP-12", rule_family_id="RF-12",
        claim_to_test="啤殼特徵（集資額不合理+七條件）篩出的半新股，上市後1.5-2.5年窗口的啟動/上升比例顯著高於對照半新股",
        required_case_characteristics=["2020年後上市主板/創業板股票", "有集資額與CCASS初篩數據"],
        required_evidence=["集資額/上市費用/盈利", "上市後36個月價格", "CCASS集中度序列"],
        t0_fields_required=["ipo_record(proceeds, listing_cost, prior_profit, mcap)"],
        t1_outcome_fields_required=["launch_in_window(18-30m)", "return_36m"],
        support_condition="篩選組窗口內啟動率顯著高於對照",
        contradiction_condition="兩組無差異",
        context_dependent_condition="股災期可把異常時間加回（規則自帶）",
        falsification_trigger="篩選與啟動無關",
        minimum_case_count=None, priority="MEDIUM",
    ),
]

# ============================================================ INFLATION CONTROL
def inflation_stats() -> dict:
    return {
        "RAW_RULE_COUNT": 48,
        "RULE_FAMILY_COUNT": len(RULE_FAMILIES),
        "DISTINCT_CAPABILITY_COUNT": len(CAPABILITIES),
        "LUNA_TARGET_COUNT": len(LUNA_TARGETS),
        "LUNA_TARGETS_HIGH": sum(1 for t in LUNA_TARGETS if t.priority == "HIGH"),
        "rules_referenced_by_at_least_one_family": sorted(
            {rid for f in RULE_FAMILIES for rid in f.member_rule_ids}),
    }


def validate_consolidation(all_rule_ids: List[str]) -> List[str]:
    """Cross-check families/capabilities/targets against the raw rule inventory."""
    problems = []
    fam_ids = {f.rule_family_id for f in RULE_FAMILIES}
    cap_ids = {c.capability_id for c in CAPABILITIES}
    referenced = set(inflation_stats()["rules_referenced_by_at_least_one_family"])
    for rid in all_rule_ids:
        if rid not in referenced:
            problems.append(f"orphan rule {rid}: not in any family")
    for c in CAPABILITIES:
        if c.supporting_rule_families and not set(c.supporting_rule_families) <= fam_ids:
            problems.append(f"{c.capability_id}: unknown family ref")
        if not set(c.supporting_rule_ids) <= set(all_rule_ids):
            problems.append(f"{c.capability_id}: unknown rule ref")
    for g in VALIDATION_GAPS:
        if g.capability_id not in cap_ids:
            problems.append(f"gap for unknown capability {g.capability_id}")
    for t in LUNA_TARGETS:
        if t.capability_id not in cap_ids:
            problems.append(f"{t.target_id}: unknown capability ref")
        if t.rule_family_id not in fam_ids:
            problems.append(f"{t.target_id}: unknown family ref")
    return problems
