from __future__ import annotations

from datetime import date, datetime

from ccass_core.research_workflow import ResearchWorkflowSession
from ccass_core.research_workflow_consumer import build_research_workflow_consumer_view
from ccass_core.source_trace import SourceTraceView
from ccass_core.report import DEFAULT_LOCALE, translate_text


def build_research_workflow_summary_markdown(
    workflow: ResearchWorkflowSession | None,
    *,
    source_trace: SourceTraceView | None = None,
    locale: str = DEFAULT_LOCALE,
) -> str:
    heading = translate_text(locale, "ui.research_workflow_heading")
    caption = translate_text(locale, "ui.research_workflow_caption")
    if workflow is None:
        return "\n".join(
            [
                f"### {heading}",
                caption,
                "",
                translate_text(locale, "ui.research_workflow_unavailable"),
            ]
        )

    consumer_view = build_research_workflow_consumer_view(workflow, source_trace=source_trace)
    quality_context = consumer_view.quality_context
    provenance = quality_context.provenance if quality_context else None
    state_label = _workflow_state_label(workflow.state.value, locale)
    context_label = (
        translate_text(locale, "ui.research_workflow_context_available")
        if consumer_view.context_available
        else translate_text(locale, "ui.research_workflow_context_unavailable")
    )
    quality_label = quality_context.freshness_status if quality_context else translate_text(locale, "report.data_not_available")
    freshness_label = quality_label
    provenance_label = _provenance_label(provenance, locale)
    warnings_label = (
        translate_text(locale, "ui.research_workflow_warnings_none")
        if not consumer_view.warnings
        else f"{len(consumer_view.warnings)} warning(s)"
    )
    package_label = _package_reference_label(workflow, locale)
    governance_context = consumer_view.governance_context
    rows = [
        (translate_text(locale, "ui.research_workflow_state"), state_label),
        (translate_text(locale, "ui.research_workflow_session_id"), workflow.metadata.session_id),
        (translate_text(locale, "ui.research_workflow_stock_code"), workflow.metadata.stock_code),
        (translate_text(locale, "ui.research_workflow_created_at"), _format_value(workflow.metadata.created_at)),
        (translate_text(locale, "ui.research_workflow_loaded_at"), _format_value(workflow.metadata.loaded_at)),
        (translate_text(locale, "ui.research_workflow_ready_at"), _format_value(workflow.metadata.ready_at)),
        (translate_text(locale, "ui.research_workflow_context_availability"), context_label),
        (translate_text(locale, "ui.research_workflow_package_reference"), package_label),
        (translate_text(locale, "ui.research_workflow_quality_reference"), quality_label),
        (translate_text(locale, "ui.research_workflow_freshness_reference"), freshness_label),
        (translate_text(locale, "ui.research_workflow_provenance_reference"), provenance_label),
        (translate_text(locale, "ui.research_workflow_warnings_summary"), warnings_label),
    ]
    if governance_context is not None:
        rows.extend(
            [
                ("Governance summary", governance_context.summary),
                ("Source trace reference", governance_context.source_trace_reference),
                ("Date convention status", governance_context.date_convention_status),
            ]
        )
    lines = [
        f"### {heading}",
        caption,
        "",
        f"*{consumer_view.summary}*",
        "",
        f"| {translate_text(locale, 'report.table.metric')} | {translate_text(locale, 'report.table.value')} |",
        "|---|---|",
    ]
    lines.extend(f"| {label} | {value} |" for label, value in rows)
    if consumer_view.warnings:
        lines.append("")
        lines.extend(f"- {warning}" for warning in consumer_view.warnings)
    return "\n".join(lines)


def _workflow_state_label(state: str, locale: str) -> str:
    return translate_text(locale, f"ui.research_workflow_state_{state}")


def _package_reference_label(workflow: ResearchWorkflowSession, locale: str) -> str:
    package = workflow.research_context_package
    if package is None:
        return translate_text(locale, "report.data_not_available")
    return f"{package.contract_meta.version} / {package.contract_meta.surface}"


def _provenance_label(provenance, locale: str) -> str:
    if provenance is None:
        return translate_text(locale, "report.data_not_available")
    return f"{provenance.source} / {provenance.source_type} / {provenance.primary_or_fallback}"


def _format_value(value: date | datetime | str | None) -> str:
    if value is None:
        return "—"
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return str(value)
