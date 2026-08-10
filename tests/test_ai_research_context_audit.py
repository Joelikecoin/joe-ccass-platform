from __future__ import annotations

from ccass_core.ai_read_model import build_ai_read_model_v0_1
from ccass_core.ai_read_model_governance import build_ai_read_model_consumer_view
from ccass_core.ai_research_context_assembly import build_ai_research_context_assembly
from ccass_core.ai_research_context_audit import (
    build_ai_research_context_audit_trail_markdown,
)
from ccass_core.ai_research_context_consumer import build_ai_research_context_consumer_view
from ccass_core.ai_research_context_delivery import build_ai_research_context_delivery
from ccass_core.compute import compute_analysis
from ccass_core.research_context import build_research_context_package
from ccass_core.research_context_consumer import build_research_context_consumer_view
from ccass_core.source_trace import (
    SourceDateGovernanceReference,
    SourceTraceIdentity,
    SourceTraceSelection,
    SourceTraceView,
)


def _build_read_model(current_response, previous_response):
    analysis = compute_analysis(current_response, previous_response)
    return build_ai_read_model_v0_1(
        code=current_response.metadata.code,
        response=current_response,
        surface="ccass_ai_read_model",
        analysis=analysis,
        previous_response=previous_response,
        snapshot_id=101,
        previous_snapshot_id=100,
    )


def _source_trace(response):
    return SourceTraceView(
        request_id="trace-audit-001",
        request_surface="service",
        route="existing_service",
        cache_first=True,
        cache_usage_state="miss",
        source_identity=SourceTraceIdentity(
            source_id="offline_test_fixture",
            source_name=response.metadata.source_name,
            source_url=response.metadata.source_url,
            source_status="active",
        ),
        selection=SourceTraceSelection(
            selected_source_id="existing_service",
            selected_source_name="FixtureCcassService",
            selected_source_status="active",
            attempted_sources=("existing_service",),
            attempted_statuses=("active",),
            source_candidates=("existing_service",),
        ),
        fetched_at=response.metadata.fetched_at,
        data_as_of=response.metadata.data_as_of,
        date_governance=SourceDateGovernanceReference(),
        authoritative=False,
    )


def _delivery(current_response, previous_response):
    ai_read_model = _build_read_model(current_response, previous_response)
    source_trace = _source_trace(current_response)
    research_package = build_research_context_package(ai_read_model=ai_read_model)
    assembly = build_ai_research_context_assembly(
        research_context_package=research_package,
        research_context_consumer_view=build_research_context_consumer_view(research_package),
        ai_read_model_consumer_view=build_ai_read_model_consumer_view(
            ai_read_model,
            source_trace=source_trace,
        ),
        source_trace=source_trace,
    )
    return build_ai_research_context_delivery(assembly)


def test_ai_research_context_audit_trail_captures_context_chain(current_response, previous_response):
    delivery = _delivery(current_response, previous_response)
    audit_trail = delivery.audit_trail

    assert audit_trail is not None
    assert audit_trail.available is True
    assert audit_trail.snapshot_id == 101
    assert audit_trail.previous_snapshot_id == 100
    assert audit_trail.context_version_reference
    assert "ai_research_context_access" in audit_trail.creation_reference
    assert "ai_research_context_delivery" in audit_trail.creation_reference
    assert audit_trail.linked_audit_reference
    assert audit_trail.provenance_reference
    assert audit_trail.governance_reference
    assert audit_trail.validation_reference
    assert audit_trail.quality_summary_reference
    assert audit_trail.warnings_reference == delivery.warning_summary
    assert audit_trail.warnings == delivery.warnings
    assert "AI research context audit trail:" in audit_trail.summary
    assert "snapshot_id=101" in audit_trail.summary


def test_ai_research_context_audit_trail_markdown_handles_unavailable_state():
    markdown = build_ai_research_context_audit_trail_markdown(None)

    assert "AI Research Context Audit Trail" in markdown
    assert "unavailable" in markdown.lower()
