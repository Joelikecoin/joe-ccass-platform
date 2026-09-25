"""ZC_DOCTOR_VALIDATION_TARGET_FEASIBILITY_AUDIT_V1.

Re-ranks the 14 Luna validation targets by empirical executability against the
platform's CURRENT evidence surfaces. No new capabilities; no semantics weakened.

Evidence surface inventory (as of 2026-09-25, baseline f03d93a):
  AVAILABLE : CCASS_DAILY_HOLDINGS(134k rows, ~53-stock watchlist, post-gap window
              2026-07-21→now), CCASS_SNAPSHOTS(1,356), DION_DI(1,780 rows incl
              02318 full multi-year 696-event series), ANNOUNCEMENTS(6,109 HKEXnews,
              watchlist coverage), SHARE_CAPITAL(146), FUNDAMENTALS(72),
              ENTITIES(9), INTEL_EVENT_SNAPSHOTS(28), PRICE_DAILY(Longbridge,
              watchlist, multi-year candles)
  PARTIAL   : UNDERWRITER/R報告 terms (inside announcement text, unstructured),
              PLACEE structure (announcement text), ENTITY/OPERATOR group map (9
              rows only), NON_WATCHLIST_DI (DION jobs run per-stock on demand)
  MISSING   : SFC concentration alerts (official, public, not ingested),
              MEDIA_EXPOSURE, IPO/PROSPECTUS universe, BROAD_HISTORICAL_MCAP,
              DELISTED_UNIVERSE, HISTORICAL_CCASS_19Y (staging exists 87.5M rows
              but GATED at Codex final parent gate — NOT production)
"""
from __future__ import annotations

import json
from typing import List, Optional

from pydantic import BaseModel, model_validator


class FeasibilityRow(BaseModel):
    target_id: str
    capability_id: str
    rule_family_id: str
    required_t0_domains: List[str]
    required_t1_domains: List[str]
    currently_available_domains: List[str]
    partial_domains: List[str]
    missing_domains: List[str]
    requires_official_disclosure: bool
    requires_exact_date_alignment: bool
    requires_price_volume: bool
    requires_ccass: bool
    requires_di: bool
    requires_share_capital: bool
    source_independence_feasible: str  # YES/PARTIAL/NO
    point_in_time_feasible: str
    expected_implementation_cost: str  # LOW/MEDIUM/HIGH
    evidence_availability_risk: str
    likelihood_of_ready_for_case_validation: str
    blocker: str

    @model_validator(mode="after")
    def _gates(self):
        assert self.source_independence_feasible in ("YES", "PARTIAL", "NO")
        assert self.point_in_time_feasible in ("YES", "PARTIAL", "NO")
        for f in ("expected_implementation_cost", "evidence_availability_risk",
                  "likelihood_of_ready_for_case_validation"):
            assert getattr(self, f) in ("LOW", "MEDIUM", "HIGH"), (self.target_id, f)
        return self


ROWS: List[FeasibilityRow] = [
    FeasibilityRow(
        target_id="LT-09", capability_id="CAP-10", rule_family_id="RF-10",
        required_t0_domains=["DION_DI_SERIES", "THRESHOLD_HUG_FLAG"],
        required_t1_domains=["ANNOUNCEMENTS_CAPITAL_ACTIONS_24M", "CONTROL_PATH_OUTCOME", "SHARE_CAPITAL"],
        currently_available_domains=["DION_DI_SERIES(02318 全史 696 events)", "ANNOUNCEMENTS(02318)", "SHARE_CAPITAL", "PRICE_DAILY"],
        partial_domains=[], missing_domains=[],
        requires_official_disclosure=True, requires_exact_date_alignment=False,
        requires_price_volume=False, requires_ccass=False, requires_di=True, requires_share_capital=True,
        source_independence_feasible="YES", point_in_time_feasible="YES",
        expected_implementation_cost="LOW", evidence_availability_risk="LOW",
        likelihood_of_ready_for_case_validation="HIGH",
        blocker="無結構性 blocker；單股樣本（n=1 個案）只支持 case-package 級驗證，非統計級",
    ),
    FeasibilityRow(
        target_id="LT-04", capability_id="CAP-05", rule_family_id="RF-05",
        required_t0_domains=["GO_RECORD(go_price,end_date)", "ANNOUNCEMENTS"],
        required_t1_domains=["PRICE_1Y", "HOLD_ABOVE_GO_30D"],
        currently_available_domains=["ANNOUNCEMENTS(watchlist GO/易手通告)", "PRICE_DAILY"],
        partial_domains=["GO_PRICE/END_DATE 欄位需從通告文本抽取"],
        missing_domains=[],
        requires_official_disclosure=True, requires_exact_date_alignment=True,
        requires_price_volume=True, requires_ccass=False, requires_di=False, requires_share_capital=False,
        source_independence_feasible="PARTIAL", point_in_time_feasible="YES",
        expected_implementation_cost="MEDIUM", evidence_availability_risk="MEDIUM",
        likelihood_of_ready_for_case_validation="HIGH",
        blocker="GO 價/起止日為通告文本抽取（無現成結構欄位）——一次性 parser 工作量",
    ),
    FeasibilityRow(
        target_id="LT-02", capability_id="CAP-03", rule_family_id="RF-02",
        required_t0_domains=["PLACEMENT_RECORD", "PRICE_POSITION_T0"],
        required_t1_domains=["LAUNCH_30D", "RETURN_1M_3M"],
        currently_available_domains=["ANNOUNCEMENTS(配股公告)", "PRICE_DAILY"],
        partial_domains=["承配人人數/披露狀態（通告文本抽取）"],
        missing_domains=[],
        requires_official_disclosure=True, requires_exact_date_alignment=True,
        requires_price_volume=True, requires_ccass=False, requires_di=False, requires_share_capital=False,
        source_independence_feasible="PARTIAL", point_in_time_feasible="YES",
        expected_implementation_cost="MEDIUM", evidence_availability_risk="MEDIUM",
        likelihood_of_ready_for_case_validation="HIGH",
        blocker="placee_count/disclosed 欄位需文本抽取；watchlist 樣本量受 6,109 通告覆蓋限制",
    ),
    FeasibilityRow(
        target_id="LT-01", capability_id="CAP-02", rule_family_id="RF-01",
        required_t0_domains=["RIGHTS_ISSUE_RECORD", "DAILY_CLOSE_90D"],
        required_t1_domains=["R_REPORT_TAKEUP", "UNDERWRITER_ID"],
        currently_available_domains=["ANNOUNCEMENTS(供股+結果通告)", "PRICE_DAILY", "SHARE_CAPITAL"],
        partial_domains=["R報告承給/申請份數（文本抽取）", "包銷商身份（文本抽取）"],
        missing_domains=[],
        requires_official_disclosure=True, requires_exact_date_alignment=True,
        requires_price_volume=True, requires_ccass=False, requires_di=False, requires_share_capital=True,
        source_independence_feasible="PARTIAL", point_in_time_feasible="YES",
        expected_implementation_cost="MEDIUM", evidence_availability_risk="MEDIUM",
        likelihood_of_ready_for_case_validation="MEDIUM",
        blocker="R報告結構化抽取是主要成本；除權日須從通告對齊",
    ),
    FeasibilityRow(
        target_id="LT-03", capability_id="CAP-03", rule_family_id="RF-02",
        required_t0_domains=["GO_COMPLETION", "PLACEMENT_20_20"],
        required_t1_domains=["RETURN_3M_4M", "WIN_RATE"],
        currently_available_domains=["ANNOUNCEMENTS", "PRICE_DAILY"],
        partial_domains=["GO完成狀態", "20/20 條款抽取"],
        missing_domains=[],
        requires_official_disclosure=True, requires_exact_date_alignment=True,
        requires_price_volume=True, requires_ccass=False, requires_di=False, requires_share_capital=False,
        source_independence_feasible="PARTIAL", point_in_time_feasible="YES",
        expected_implementation_cost="MEDIUM", evidence_availability_risk="HIGH",
        likelihood_of_ready_for_case_validation="MEDIUM",
        blocker="GO+20/20 組合本身罕見——watchlist 範圍內案例數可能不足以支持任何結論（方法亦無指定最低 n）",
    ),
    FeasibilityRow(
        target_id="LT-07", capability_id="CAP-04", rule_family_id="RF-03",
        required_t0_domains=["CONSOLIDATION_RECORD(price≤0.05)", "PRICE"],
        required_t1_domains=["CAPITAL_ACTIONS_24M", "RETURN_24M"],
        currently_available_domains=["ANNOUNCEMENTS", "PRICE_DAILY", "SHARE_CAPITAL"],
        partial_domains=[], missing_domains=[],
        requires_official_disclosure=True, requires_exact_date_alignment=False,
        requires_price_volume=True, requires_ccass=False, requires_di=False, requires_share_capital=True,
        source_independence_feasible="YES", point_in_time_feasible="YES",
        expected_implementation_cost="LOW", evidence_availability_risk="MEDIUM",
        likelihood_of_ready_for_case_validation="MEDIUM",
        blocker="貼仙合股在 watchlist 範圍內的事件數未知；通告覆蓋決定樣本",
    ),
    FeasibilityRow(
        target_id="LT-06", capability_id="CAP-07", rule_family_id="RF-07",
        required_t0_domains=["CCASS_IN_EVENT(ratio,position)", "NON_CCASS_TRANSITIONS"],
        required_t1_domains=["RETURN_180D", "CCASS_DISPERSION_180D"],
        currently_available_domains=["CCASS_DAILY_HOLDINGS(watchlist, 2026-07-21→)", "SHARE_CAPITAL", "PRICE_DAILY"],
        partial_domains=["存入者身份（需 DI 交叉）"],
        missing_domains=["更長歷史窗口（實物存入為低頻事件，2 個月窗口事件數不足）"],
        requires_official_disclosure=False, requires_exact_date_alignment=True,
        requires_price_volume=True, requires_ccass=True, requires_di=False, requires_share_capital=True,
        source_independence_feasible="YES", point_in_time_feasible="YES",
        expected_implementation_cost="MEDIUM", evidence_availability_risk="HIGH",
        likelihood_of_ready_for_case_validation="LOW",
        blocker="非CCASS→CCASS 轉換事件在現有 2 個月窗口內太稀疏；需要 19 年歷史庫（Codex gated）或累積 12+ 個月",
    ),
    FeasibilityRow(
        target_id="LT-05", capability_id="CAP-07", rule_family_id="RF-07",
        required_t0_domains=["GO_OFFER(acceptance_ratio,mkt_vs_go)"],
        required_t1_domains=["CCASS_DESTINATION_90D", "CONTROLLER_STAKE_CHANGE"],
        currently_available_domains=["ANNOUNCEMENTS", "PRICE_DAILY"],
        partial_domains=["R報告接受比例（文本抽取）"],
        missing_domains=["要約期後 90 日 CCASS（限 watchlist+窗口）", "新主關聯券商映射（ENTITIES 僅 9 行）"],
        requires_official_disclosure=True, requires_exact_date_alignment=True,
        requires_price_volume=True, requires_ccass=True, requires_di=True, requires_share_capital=False,
        source_independence_feasible="PARTIAL", point_in_time_feasible="YES",
        expected_implementation_cost="HIGH", evidence_availability_risk="HIGH",
        likelihood_of_ready_for_case_validation="LOW",
        blocker="同時需要 R報告抽取+關聯券商映射+CCASS 歷史——三項缺口疊加",
    ),
    FeasibilityRow(
        target_id="LT-10", capability_id="CAP-08", rule_family_id="RF-08",
        required_t0_domains=["SIGNAL_SCORE(7 components)"],
        required_t1_domains=["RETURN_30D_60D", "DRAWDOWN"],
        currently_available_domains=["ANNOUNCEMENTS", "DI(watchlist)", "CCASS(watchlist)", "PRICE_DAILY+分鐘(當日)"],
        partial_domains=["CCASS 出貨程度（窗口短）", "歷史分鐘圖（僅當日）"],
        missing_domains=["MEDIA_EXPOSURE（無來源，需人工）"],
        # media 組件結構性缺席 → 證據可得性風險 HIGH（不弱化七信號語義）
        requires_official_disclosure=False, requires_exact_date_alignment=True,
        requires_price_volume=True, requires_ccass=True, requires_di=True, requires_share_capital=False,
        source_independence_feasible="PARTIAL", point_in_time_feasible="YES",
        expected_implementation_cost="HIGH", evidence_availability_risk="HIGH",
        likelihood_of_ready_for_case_validation="LOW",
        blocker="media exposure 無結構來源；合約要求 7 組件齊備——不弱化語義則須人工輸入通道",
    ),
    FeasibilityRow(
        target_id="LT-12", capability_id="CAP-12", rule_family_id="RF-12",
        required_t0_domains=["CRASH_RECORD", "SAME_GROUP_MAP", "CONTROLLER_DI"],
        required_t1_domains=["BOUNCE_20D"],
        currently_available_domains=["PRICE_DAILY(可掃急跌)", "DION_DI(watchlist)"],
        partial_domains=["同系/同戶口映射（ENTITIES 僅 9 行）", "非 watchlist 大股東 DI"],
        missing_domains=["BROAD_UNIVERSE_GROUP_MAP"],
        requires_official_disclosure=False, requires_exact_date_alignment=True,
        requires_price_volume=True, requires_ccass=False, requires_di=True, requires_share_capital=False,
        source_independence_feasible="PARTIAL", point_in_time_feasible="YES",
        expected_implementation_cost="MEDIUM", evidence_availability_risk="HIGH",
        likelihood_of_ready_for_case_validation="MEDIUM",
        blocker="被迫斬倉 vs 主動散貨的分類依賴同系映射+DI，兩者覆蓋薄；急跌事件本身可全掃",
    ),
    FeasibilityRow(
        target_id="LT-13", capability_id="CAP-05", rule_family_id="RF-05",
        required_t0_domains=["OLD_OWNER_STAKE_BAND"],
        required_t1_domains=["RETURN_12M"],
        currently_available_domains=["ANNOUNCEMENTS(易手)", "PRICE_DAILY"],
        partial_domains=["舊主轉移後持股（DI 僅 watchlist；DION 可按股開 job）"],
        missing_domains=["BROAD_HISTORICAL_DI"],
        requires_official_disclosure=True, requires_exact_date_alignment=False,
        requires_price_volume=True, requires_ccass=False, requires_di=True, requires_share_capital=False,
        source_independence_feasible="PARTIAL", point_in_time_feasible="YES",
        expected_implementation_cost="MEDIUM", evidence_availability_risk="HIGH",
        likelihood_of_ready_for_case_validation="LOW",
        blocker="需要歷史 GO 案例全集的易手+舊主持股——DI 歷史覆蓋是主要缺口",
    ),
    FeasibilityRow(
        target_id="LT-14", capability_id="CAP-12", rule_family_id="RF-12",
        required_t0_domains=["IPO_RECORD(proceeds,cost,profit,mcap)"],
        required_t1_domains=["LAUNCH_18_30M", "RETURN_36M", "CCASS_FROM_LISTING"],
        currently_available_domains=["PRICE_DAILY"],
        partial_domains=["招股結果（公告內文本）"],
        missing_domains=["IPO/PROSPECTUS_UNIVERSE", "CCASS_FROM_LISTING_DATE"],
        requires_official_disclosure=True, requires_exact_date_alignment=True,
        requires_price_volume=True, requires_ccass=True, requires_di=False, requires_share_capital=True,
        source_independence_feasible="PARTIAL", point_in_time_feasible="YES",
        expected_implementation_cost="HIGH", evidence_availability_risk="HIGH",
        likelihood_of_ready_for_case_validation="LOW",
        blocker="無招股書/上市費用結構化來源；CCASS 自上市日起的序列不存在（歷史庫 gated）",
    ),
    FeasibilityRow(
        target_id="LT-11", capability_id="CAP-11", rule_family_id="RF-13",
        required_t0_domains=["LADDER_STATE", "BROAD_HISTORICAL_MCAP", "MCAP_RECONSTRUCTION_FLAG"],
        required_t1_domains=["GO_WITHIN_36M", "DELISTING_OUTCOME"],
        currently_available_domains=["GO 公告（部分）"],
        partial_domains=["SHARE_CAPITAL(watchlist)"],
        missing_domains=["BROAD_HISTORICAL_MCAP", "DELISTED_UNIVERSE", "HISTORICAL_CCASS_19Y(gated)"],
        requires_official_disclosure=True, requires_exact_date_alignment=False,
        requires_price_volume=True, requires_ccass=True, requires_di=False, requires_share_capital=True,
        source_independence_feasible="NO", point_in_time_feasible="PARTIAL",
        expected_implementation_cost="HIGH", evidence_availability_risk="HIGH",
        likelihood_of_ready_for_case_validation="LOW",
        blocker="BLOCKED_BY_CODEX_GATE：重跑需 19 年歷史庫（staging 87.5M 行未過 final parent gate）+ 除牌全集；ZC 不得繞過 gate",
    ),
    FeasibilityRow(
        target_id="LT-08", capability_id="CAP-06", rule_family_id="RF-06",
        required_t0_domains=["SFC_CONCENTRATION_ALERT", "CCASS_SNAPSHOT_SAME_DATE"],
        required_t1_domains=["GAP_METHOD_ESTIMATE", "ESTIMATE_ERROR"],
        currently_available_domains=["CCASS_DAILY_HOLDINGS(watchlist only)"],
        partial_domains=["鴻溝法估算器（可實作）"],
        missing_domains=["SFC_CONCENTRATION_ALERTS（官方公開但未攝取）", "ALERT_DATE_CCASS_HISTORY（alert 股票多在 watchlist 外；歷史快照 gated）"],
        requires_official_disclosure=True, requires_exact_date_alignment=True,
        requires_price_volume=False, requires_ccass=True, requires_di=False, requires_share_capital=True,
        source_independence_feasible="PARTIAL", point_in_time_feasible="PARTIAL",
        expected_implementation_cost="MEDIUM", evidence_availability_risk="HIGH",
        likelihood_of_ready_for_case_validation="LOW",
        blocker="FAILURE_CLASS=A(缺來源攝取：證監會集中通告未入庫) + B(證據本質稀有：alert 事件本身低頻且日期回溯需歷史 CCASS)。非 C(合約過度具體——語義不改) 非 D(非暫時性 data gap——官方通告來源結構性缺席)",
    ),
]

# Ranking: 1 evidence availability 2 PIT feasibility 3 source independence 4 cost 5 value
_RANK_VALUE = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}
_COST = {"LOW": 3, "MEDIUM": 2, "HIGH": 1}
_INDEP = {"YES": 3, "PARTIAL": 2, "NO": 1}
# validation value weight per target (impact on major conclusions / timing / intention rules)
_VALUE = {"LT-09": 5, "LT-04": 5, "LT-02": 4, "LT-01": 4, "LT-08": 5, "LT-10": 4,
          "LT-06": 3, "LT-05": 3, "LT-07": 3, "LT-03": 3, "LT-11": 4, "LT-12": 2,
          "LT-13": 2, "LT-14": 2}


def rank_rows(rows: List[FeasibilityRow]) -> List[FeasibilityRow]:
    def key(r: FeasibilityRow):
        return (-_RANK_VALUE[r.evidence_availability_risk and
                             ("HIGH" if r.evidence_availability_risk == "LOW" else
                              "MEDIUM" if r.evidence_availability_risk == "MEDIUM" else "LOW")],
                -_INDEP[r.point_in_time_feasible],
                -_INDEP[r.source_independence_feasible],
                -_COST[r.expected_implementation_cost],
                -_VALUE[r.target_id])
    return sorted(rows, key=key)


class AuditReport(BaseModel):
    baseline: str = "f03d93a"
    rows: List[FeasibilityRow]
    ranked_ids: List[str]

    @model_validator(mode="after")
    def _complete(self):
        assert len(self.rows) == 14
        assert sorted(self.ranked_ids) == sorted(r.target_id for r in self.rows)
        return self


def build_report() -> AuditReport:
    return AuditReport(rows=ROWS, ranked_ids=[r.target_id for r in rank_rows(ROWS)])


def dump(json_path: str, md_path: str) -> AuditReport:
    rep = build_report()
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(rep.model_dump(), f, ensure_ascii=False, indent=1)
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# DOCTOR_VALIDATION_PRIORITY_V2\n\n")
        f.write("Baseline f03d93a。排序準則：1 證據可得性 2 PIT 可行 3 來源獨立 4 實作成本 5 驗證價值。")
        f.write("不按方法論重要性排序。\n\n## 排名\n\n")
        for i, r in enumerate(rank_rows(ROWS), 1):
            f.write(f"{i}. **{r.target_id}**（{r.capability_id}/{r.rule_family_id}）"
                    f" likelihood={r.likelihood_of_ready_for_case_validation}"
                    f" cost={r.expected_implementation_cost}"
                    f" risk={r.evidence_availability_risk}\n"
                    f"   - blocker: {r.blocker}\n")
        f.write("\n## 明細\n\n")
        for r in ROWS:
            f.write(f"### {r.target_id} → {r.capability_id} / {r.rule_family_id}\n")
            f.write(f"- T0: {'; '.join(r.required_t0_domains)}\n- T1: {'; '.join(r.required_t1_domains)}\n")
            f.write(f"- AVAILABLE: {'; '.join(r.currently_available_domains) or '—'}\n")
            f.write(f"- PARTIAL: {'; '.join(r.partial_domains) or '—'}\n")
            f.write(f"- MISSING: {'; '.join(r.missing_domains) or '—'}\n")
            f.write(f"- official={r.requires_official_disclosure} date_align={r.requires_exact_date_alignment} "
                    f"price={r.requires_price_volume} ccass={r.requires_ccass} di={r.requires_di} "
                    f"share_cap={r.requires_share_capital}\n")
            f.write(f"- source_indep={r.source_independence_feasible} pit={r.point_in_time_feasible} "
                    f"cost={r.expected_implementation_cost} risk={r.evidence_availability_risk} "
                    f"likelihood={r.likelihood_of_ready_for_case_validation}\n")
            f.write(f"- BLOCKER: {r.blocker}\n\n")
    return rep
