from __future__ import annotations

from ccass_core.ai_read_model import build_ai_read_model_v0_1
from ccass_core.ai_read_model_governance import build_ai_read_model_consumer_view
from ccass_core.ai_research_context_assembly import build_ai_research_context_assembly
from ccass_core.ai_research_context_consumer import build_ai_research_context_consumer_view
from ccass_core.ai_research_context_delivery import (
    build_ai_research_context_delivery,
    build_ai_research_context_delivery_markdown,
)
from ccass_core.compute import compute_analysis
from ccass_core.research_context import build_research_context_package
from ccass_core.research_context_consumer import build_research_context_consumer_view
from ccass_core.source_trace import (
    SourceDateGovernanceReference,
    SourceTraceIdentity,
    SourceTraceSelection,
    SourceTraceView,
)


def _build_read_model(current_response: CcassResponse, previous_response: CcassResponse):
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


def _source_trace(response: CcassResponse) -> SourceTraceView:
    return SourceTraceView(
        request_id="trace-delivery-001",
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


def _delivery(current_response: CcassResponse, previous_response: CcassResponse):
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


def test_ai_research_context_delivery_bundle_exposes_unified_context_validation_and_quality(
    current_response, previous_response
):
    delivery = _delivery(current_response, previous_response)

    assert delivery.available is True
    assert delivery.access is not None
    assert delivery.consumer_view is not None
    assert delivery.validation is not None
    assert delivery.quality_summary is not None
    assert delivery.governance_visible is True
    assert delivery.quality_visible is True
    assert delivery.consumer_ready == delivery.validation.consumer_ready
    assert delivery.context_available == delivery.consumer_view.context_available
    assert delivery.audit_trail is not None
    assert delivery.audit_trail.available is True
    assert delivery.audit_trail.snapshot_id == 101
    assert delivery.audit_trail.previous_snapshot_id == 100
    assert delivery.audit_trail.context_version_reference
    assert "ai_research_context_delivery" in delivery.audit_trail.creation_reference
    assert delivery.audit_trail.linked_audit_reference
    assert delivery.provenance_reference == delivery.access.provenance_reference
    assert delivery.freshness_reference == delivery.access.freshness_reference
    assert delivery.warning_summary == delivery.access.warning_summary
    assert delivery.limitation_summary == delivery.access.limitation_summary
    assert delivery.consumer_metadata is not None
    assert delivery.consumer_metadata.identity is not None
    assert delivery.consumer_metadata.identity.stock_code == delivery.consumer_view.assembly.identity.stock_code
    assert delivery.consumer_metadata.assembly_reference.endswith("ai_research_context_assembly")
    assert delivery.consumer_metadata.access_reference.endswith("ai_research_context_access")
    assert "AI research context delivery:" in delivery.summary
    assert "consumer_ready=" in delivery.summary


def test_ai_research_context_delivery_handles_missing_assembly():
    delivery = build_ai_research_context_delivery(None)

    assert delivery.available is False
    assert delivery.access is not None
    assert delivery.access.available is False
    assert delivery.consumer_view is None
    assert delivery.validation is None
    assert delivery.quality_summary is None
    assert delivery.consumer_metadata is None
    assert delivery.governance_visible is False
    assert delivery.quality_visible is False
    assert delivery.consumer_ready is False
    assert delivery.context_available is False
    assert delivery.availability_state == "unavailable"
    assert delivery.freshness_state == "unavailable"
    assert delivery.audit_trail is not None
    assert delivery.audit_trail.available is False
    assert delivery.audit_trail.snapshot_id is None
    assert delivery.provenance_reference == "not available"
    assert delivery.freshness_reference == "unavailable"
    assert delivery.warning_summary == "0 warning(s)"
    assert "unavailable" in delivery.summary.lower()


def test_ai_research_context_delivery_markdown_includes_delivery_fields(
    current_response, previous_response
):
    delivery = _delivery(current_response, previous_response)

    markdown = build_ai_research_context_delivery_markdown(delivery)

    assert "AI Research Context Delivery" in markdown
    assert "Context availability" in markdown
    assert "Governance visibility" in markdown
    assert "Quality visibility" in markdown
    assert "Consumer ready" in markdown
    assert "Provenance reference" in markdown
    assert "Freshness reference" in markdown
    assert "Warning summary" in markdown
    assert "Limitation summary" in markdown
    assert "Assembly contract" in markdown
    assert "Access contract" in markdown
    assert "Delivery contract" in markdown
    assert "AI Research Context Audit Trail" in markdown
    assert "Creation reference" in markdown
    assert "recommendation" not in markdown.lower()
    assert "trading signal" not in markdown.lower()
