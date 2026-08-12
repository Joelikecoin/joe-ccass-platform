from __future__ import annotations

from collections.abc import Sequence
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from ccass_core.ai_read_model import AIReadModelIdentity, AIReadModelSnapshotReference
from ccass_core.compute import AnalysisResult
from ccass_core.research_context import ResearchContextPackage

RESEARCH_CONTEXT_HANDOFF_VERSION = "v0.1"
RESEARCH_CONTEXT_HANDOFF_SURFACE = "research_context_handoff"


class ResearchContextHandoffContractMeta(BaseModel):
    version: str = RESEARCH_CONTEXT_HANDOFF_VERSION
    surface: str = RESEARCH_CONTEXT_HANDOFF_SURFACE


class ResearchContextHandoffBlock(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    available: bool = False
    summary: str = "unavailable"
    reference: str = "not available"
    warnings: list[str] = Field(default_factory=list)


class ResearchContextHandoff(BaseModel):
    model_config = ConfigDict(frozen=True)

    available: bool = False
    identity: AIReadModelIdentity | None = None
    snapshot_reference: AIReadModelSnapshotReference | None = None
    ownership_overview: ResearchContextHandoffBlock | None = None
    holder_change_overview: ResearchContextHandoffBlock | None = None
    concentration_overview: ResearchContextHandoffBlock | None = None
    report_reference: str = "not available"
    quality_reference: str = "not available"
    warnings: list[str] = Field(default_factory=list)
    summary: str = "AI research context handoff is unavailable."
    contract_meta: ResearchContextHandoffContractMeta = Field(
        default_factory=ResearchContextHandoffContractMeta
    )


def build_research_context_handoff(
    research_context_package: ResearchContextPackage | None,
    *,
    analysis: AnalysisResult | None = None,
    report_reference: str | None = None,
    surface: str = RESEARCH_CONTEXT_HANDOFF_SURFACE,
) -> ResearchContextHandoff:
    if research_context_package is None:
        return ResearchContextHandoff(
            summary="AI research context handoff is unavailable.",
            report_reference=report_reference or "not available",
            contract_meta=ResearchContextHandoffContractMeta(surface=surface),
        )

    identity = research_context_package.identity
    snapshot_reference = (
        research_context_package.historical_context.current_snapshot
        or research_context_package.ownership_context.current_snapshot
    )
    warnings = list(research_context_package.quality_context.warnings)
    ownership_overview = _ownership_overview(research_context_package)
    holder_change_overview = _holder_change_overview(
        research_context_package,
        analysis=analysis,
    )
    concentration_overview = _concentration_overview(research_context_package)
    quality_reference = _quality_reference(research_context_package)
    report_reference_value = report_reference or "not available"
    summary = _summary_text(
        identity=identity,
        snapshot_reference=snapshot_reference,
        ownership_overview=ownership_overview,
        holder_change_overview=holder_change_overview,
        concentration_overview=concentration_overview,
        report_reference=report_reference_value,
        quality_reference=quality_reference,
        warnings=warnings,
    )
    return ResearchContextHandoff(
        available=True,
        identity=identity,
        snapshot_reference=snapshot_reference,
        ownership_overview=ownership_overview,
        holder_change_overview=holder_change_overview,
        concentration_overview=concentration_overview,
        report_reference=report_reference_value,
        quality_reference=quality_reference,
        warnings=warnings,
        summary=summary,
        contract_meta=ResearchContextHandoffContractMeta(surface=surface),
    )


def build_research_context_handoff_markdown(
    handoff: ResearchContextHandoff | None,
) -> str:
    if handoff is None or not handoff.available:
        return "\n".join(
            [
                "### AI Research Context Handoff",
                "",
                "AI research context handoff is unavailable.",
            ]
        )

    rows = [
        ("Stock identity", _identity_label(handoff.identity)),
        ("Snapshot reference", _snapshot_label(handoff.snapshot_reference)),
        (
            "Ownership overview",
            handoff.ownership_overview.summary if handoff.ownership_overview else "unavailable",
        ),
        (
            "Holder change overview",
            handoff.holder_change_overview.summary if handoff.holder_change_overview else "unavailable",
        ),
        (
            "Concentration overview",
            handoff.concentration_overview.summary if handoff.concentration_overview else "unavailable",
        ),
        ("Report reference", handoff.report_reference),
        ("Quality reference", handoff.quality_reference),
        ("Warnings", f"{len(handoff.warnings)} warning(s)"),
        (
            "Handoff contract",
            f"{handoff.contract_meta.version} / {handoff.contract_meta.surface}",
        ),
    ]
    lines = [
        "### AI Research Context Handoff",
        "",
        f"*{handoff.summary}*",
        "",
        "| Metric | Value |",
        "|---|---|",
    ]
    lines.extend(f"| {label} | {value} |" for label, value in rows)
    if handoff.warnings:
        lines.extend(["", "#### Warnings"])
        lines.extend(f"- {warning}" for warning in handoff.warnings)
    return "\n".join(lines)


def _ownership_overview(
    research_context_package: ResearchContextPackage,
) -> ResearchContextHandoffBlock:
    summary = research_context_package.ownership_context.holdings_summary
    current_snapshot = research_context_package.ownership_context.current_snapshot
    if summary is None:
        return ResearchContextHandoffBlock(
            name="ownership",
            available=False,
            summary="Ownership overview is unavailable.",
            reference=_surface_reference(research_context_package.ownership_context.surface.surface if research_context_package.ownership_context.surface is not None else "ccass", current_snapshot),
            warnings=[],
        )

    top_holders = research_context_package.ownership_context.holdings[:3]
    holder_names = ", ".join(holder.participant for holder in top_holders) if top_holders else "not available"
    return ResearchContextHandoffBlock(
        name="ownership",
        available=True,
        summary=(
            f"snapshot={_snapshot_date(current_snapshot)}; "
            f"participant_count={summary.participant_count}; "
            f"total_in_ccass_shares={summary.total_in_ccass_shares}; "
            f"top_holders={holder_names}"
        ),
        reference=_surface_reference(
            research_context_package.ownership_context.surface.surface
            if research_context_package.ownership_context.surface is not None
            else "ccass",
            current_snapshot,
        ),
        warnings=[],
    )


def _holder_change_overview(
    research_context_package: ResearchContextPackage,
    *,
    analysis: AnalysisResult | None,
) -> ResearchContextHandoffBlock:
    if analysis is None or not analysis.previous_available:
        return ResearchContextHandoffBlock(
            name="holder_change",
            available=False,
            summary="Holder change overview is unavailable.",
            reference=_snapshot_range_reference(research_context_package),
            warnings=[],
        )

    current_snapshot = research_context_package.historical_context.current_snapshot
    previous_snapshot = research_context_package.historical_context.previous_snapshot
    return ResearchContextHandoffBlock(
        name="holder_change",
        available=True,
        summary=(
            f"current_snapshot={_snapshot_date(current_snapshot)}; "
            f"previous_snapshot={_snapshot_date(previous_snapshot)}; "
            f"change_count={len(analysis.changes)}; "
            f"big_change_count={len(analysis.big_changes)}; "
            f"transfer_pattern_count={len(analysis.transfer_patterns)}"
        ),
        reference=_snapshot_range_reference(research_context_package),
        warnings=list(analysis.warnings),
    )


def _concentration_overview(
    research_context_package: ResearchContextPackage,
) -> ResearchContextHandoffBlock:
    summary = research_context_package.ownership_context.holdings_summary
    if summary is None:
        return ResearchContextHandoffBlock(
            name="concentration",
            available=False,
            summary="Concentration overview is unavailable.",
            reference=_snapshot_range_reference(research_context_package),
            warnings=[],
        )

    return ResearchContextHandoffBlock(
        name="concentration",
        available=True,
        summary=(
            f"participant_count={summary.participant_count}; "
            f"top5_pct_of_issued={summary.top5_pct_of_issued}; "
            f"top10_pct_of_issued={summary.top10_pct_of_issued}; "
            f"top5_pct_of_ccass={summary.top5_pct_of_ccass}; "
            f"top10_pct_of_ccass={summary.top10_pct_of_ccass}"
        ),
        reference=_snapshot_range_reference(research_context_package),
        warnings=[],
    )


def _quality_reference(research_context_package: ResearchContextPackage) -> str:
    quality = research_context_package.quality_context
    provenance = quality.provenance
    return (
        f"source={provenance.source}; "
        f"source_type={provenance.source_type}; "
        f"primary_or_fallback={provenance.primary_or_fallback}; "
        f"freshness={quality.freshness_status}; "
        f"warnings={len(quality.warnings)}"
    )


def _summary_text(
    *,
    identity: AIReadModelIdentity,
    snapshot_reference: AIReadModelSnapshotReference | None,
    ownership_overview: ResearchContextHandoffBlock,
    holder_change_overview: ResearchContextHandoffBlock,
    concentration_overview: ResearchContextHandoffBlock,
    report_reference: str,
    quality_reference: str,
    warnings: Sequence[str],
) -> str:
    return (
        "AI research context handoff: "
        f"stock_code={identity.stock_code}; "
        f"snapshot={_snapshot_label(snapshot_reference)}; "
        f"ownership={ownership_overview.summary}; "
        f"holder_change={holder_change_overview.summary}; "
        f"concentration={concentration_overview.summary}; "
        f"report_reference={report_reference}; "
        f"quality={quality_reference}; "
        f"warnings={len(list(warnings))}"
    )


def _snapshot_range_reference(research_context_package: ResearchContextPackage) -> str:
    current_snapshot = research_context_package.historical_context.current_snapshot
    previous_snapshot = research_context_package.historical_context.previous_snapshot
    return f"{_snapshot_label(previous_snapshot)} -> {_snapshot_label(current_snapshot)}"


def _snapshot_label(snapshot_reference: AIReadModelSnapshotReference | None) -> str:
    if snapshot_reference is None:
        return "not available"
    return _snapshot_date(snapshot_reference)


def _snapshot_date(snapshot_reference: AIReadModelSnapshotReference | None) -> str:
    if snapshot_reference is None:
        return "not available"
    if snapshot_reference.snapshot_date is not None:
        return snapshot_reference.snapshot_date.isoformat()
    if snapshot_reference.data_as_of is not None:
        return snapshot_reference.data_as_of.isoformat()
    return "not available"


def _identity_label(identity: AIReadModelIdentity | None) -> str:
    if identity is None:
        return "not available"
    company = identity.company_name or "not available"
    return f"{identity.stock_code} / {identity.market} / {company}"


def _surface_reference(surface: str, snapshot_reference: AIReadModelSnapshotReference | None) -> str:
    return f"{surface} / {_snapshot_label(snapshot_reference)}"
