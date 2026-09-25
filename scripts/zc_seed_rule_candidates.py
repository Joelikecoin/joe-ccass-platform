"""Seed CASE_DERIVED rule candidates into the development rule registry.

Every seed carries source-of-thought lineage (methodology -> source document
-> case -> evidence) and falsification conditions. None is auto-promoted to
VALIDATED. Idempotent (INSERT OR REPLACE on same id@version).
Run: python -m scripts.zc_seed_rule_candidates   (dev registry only —
NEVER the production Research Store.)
"""
from __future__ import annotations

from pathlib import Path

from app.doctor.models import MethodNamespace, MethodRule, MethodStatus, RuleFamily
from app.doctor.registry import MethodRuleRegistry

SEEDS = [
    MethodRule(
        rule_id="R-JAMES-RTSS-BURST-TIMING-001",
        rule_version=1,
        rule_name="爆量訊號=報時+累積，非買入訊號",
        rule_family=RuleFamily.EVENT_SEQUENCE,
        methodology=MethodNamespace.JAMES_RTSS,
        method_status=MethodStatus.CASE_DERIVED,
        origin_case_ids=["CASE-RTSS-616"],
        origin_source_ids=[
            "latest_reference_updates/13092026 自建 RTSS 式即市異動監察｜開工前準備.md",
            "latest_reference_updates/13092026 自建 RTSS 式即市異動監察｜可行性與架構.md",
            "latest_reference_updates/20260912 技術規格書 自建RTSS掃描器 由零開始.md",
        ],
        origin_methodology_ids=["JAMES_RTSS"],
        description="616 訊號股 / 3,548 配對樣本：控制同日同升幅後超額報酬≈0（平均+0.7pt p=0.382；中位+0.4pt p=0.600）。訊號價值=報時（邊隻有人郁→人手查財技）+累積（歷史庫），回報靠極少數尾部。",
        required_inputs=["爆量事件", "同日升幅", "配對基準"],
        output_type="classification",
        output_semantics="訊號分類為報時事件，不是入場訊號",
        false_positive_conditions=["把報時當買入訊號使用"],
        falsification_conditions=["未來樣本控制同日升幅後仍顯著超額報酬（p<0.05）則推翻"],
    ),
    MethodRule(
        rule_id="R-PLATFORM-5PCT-LINE-001",
        rule_version=1,
        rule_name="5% 申報線雙向穿越=法定申報事件",
        rule_family=RuleFamily.CONTROL_CHANGE,
        methodology=MethodNamespace.PLATFORM,
        method_status=MethodStatus.CASE_DERIVED,
        origin_case_ids=["CASE-02318-DION-2024-2026"],
        origin_source_ids=["HKEX DION 官方申報表（di.hkex.com.hk，02318 1,307 行生產數據）"],
        origin_methodology_ids=["PLATFORM_SFO_DIO"],
        description="SFO Part XV：≥5% 持股其後每次跨越整個百分率級距須3個交易日內申報。升至/跌穿5%線=控制權關注事件（notable）。",
        required_inputs=["filer 申報序列", "申報百分比"],
        calculation_logic="逐 filer 鏈式前值；prev<5<=now 或 prev>=5>now",
        output_type="event",
        output_semantics="申報線穿越事件（雙向）",
        false_positive_conditions=["首次申報無前值時誤判穿越（應標 unknown）"],
        falsification_conditions=["DION 官方定義變更"],
    ),
    MethodRule(
        rule_id="R-HILTON-STAGE-GATE-001",
        rule_version=1,
        rule_name="階段判斷必須帶證據與推翻條件",
        rule_family=RuleFamily.STAGE_CLASSIFICATION,
        methodology=MethodNamespace.HILTON,
        method_status=MethodStatus.OBSERVATION,
        origin_case_ids=["CASE-HILTON-TEACHING-GENERAL"],
        origin_source_ids=["Hilton 教材方法論（教材消化待入庫——本候選為框架規則，非案例結論）"],
        origin_methodology_ids=["HILTON"],
        description="任何階段分類（DOCTOR_STAGES 19 階白名單）必須引用 supporting_evidence + method_rules_used + falsification_conditions；無證據不出階段。",
        preconditions=["DoctorContext 已組裝"],
        output_type="constraint",
        output_semantics="階段輸出的結構性約束",
        falsification_conditions=["若教材顯示存在無證據階段判斷的合法場景，則放寬"],
    ),
]


def seed(registry: MethodRuleRegistry | None = None) -> list[str]:
    reg = registry or MethodRuleRegistry()
    seeded = []
    for rule in SEEDS:
        reg.save_rule(rule)
        seeded.append(f"{rule.rule_id}@{rule.rule_version}")
    return seeded


if __name__ == "__main__":
    for entry in seed():
        print("seeded", entry)
