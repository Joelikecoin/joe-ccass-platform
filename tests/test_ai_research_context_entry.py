from __future__ import annotations

from ccass_core.ai_read_model import build_ai_read_model_v0_1
from ccass_core.ai_read_model_governance import build_ai_read_model_consumer_view
from ccass_core.ai_research_context_assembly import build_ai_research_context_assembly
from ccass_core.ai_research_context_consumer import build_ai_research_context_consumer_view
from ccass_core.ai_research_context_delivery import build_ai_research_context_delivery_markdown
from ccass_core.ai_research_context_entry import (
    build_ai_research_context_consumer_entry,
    build_ai_research_context_consumer_entry_markdown,
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
        request_id="trace-entry-001",
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


def _assembly(current_response, previous_response):
    ai_read_model = _build_read_model(current_response, previous_response)
    source_trace = _source_trace(current_response)
    research_package = build_research_context_package(ai_read_model=ai_read_model)
    return build_ai_research_context_assembly(
        research_context_package=research_package,
        research_context_consumer_view=build_research_context_consumer_view(research_package),
        ai_read_model_consumer_view=build_ai_read_model_consumer_view(
            ai_read_model,
            source_trace=source_trace,
        ),
        source_trace=source_trace,
    )


def test_ai_research_context_consumer_entry_unifies_access_delivery_and_quality(current_response, previous_response):
    entry = build_ai_research_context_consumer_entry(_assembly(current_response, previous_response))

    assert entry.available is True
    assert entry.access is not None
    assert entry.delivery is not None
    assert entry.consumer_view is not None
    assert entry.validation is not None
    assert entry.quality_summary is not None
    assert entry.consumer_metadata is not None
    assert entry.audit_trail is not None
    assert entry.audit_trail.available is True
    assert entry.audit_trail.snapshot_id == 101
    assert entry.audit_trail.previous_snapshot_id == 100
    assert entry.audit_trail.context_version_reference
    assert "ai_research_context_delivery" in entry.audit_trail.creation_reference
    assert entry.audit_trail.linked_audit_reference
    assert entry.governance_visible == entry.delivery.governance_visible
    assert entry.quality_visible == entry.delivery.quality_visible
    assert entry.consumer_ready == entry.delivery.consumer_ready
    assert entry.context_available == entry.delivery.context_available
    assert entry.provenance_reference == entry.delivery.provenance_reference
    assert entry.freshness_reference == entry.delivery.freshness_reference
    assert entry.warning_summary == entry.delivery.warning_summary
    assert entry.limitation_summary == entry.delivery.limitation_summary
    assert entry.usage_steps == entry.delivery.usage_steps
    assert entry.warnings == entry.delivery.warnings
    assert entry.delivery_markdown == build_ai_research_context_delivery_markdown(entry.delivery)
    assert "AI research context consumer entry:" in entry.summary
    assert "consumer_ready=" in entry.summary


def test_ai_research_context_consumer_entry_handles_missing_assembly():
    entry = build_ai_research_context_consumer_entry(None)

    assert entry.available is False
    assert entry.access is not None
    assert entry.access.available is False
    assert entry.delivery is not None
    assert entry.delivery.available is False
    assert entry.consumer_view is None
    assert entry.validation is None
    assert entry.quality_summary is None
    assert entry.consumer_metadata is None
    assert entry.consumer_ready is False
    assert entry.context_available is False
    assert entry.availability_state == "unavailable"
    assert entry.freshness_state == "unavailable"
    assert entry.audit_trail is not None
    assert entry.audit_trail.available is False
    assert entry.audit_trail.snapshot_id is None
    assert entry.provenance_reference == "not available"
    assert entry.freshness_reference == "unavailable"
    assert entry.warning_summary == "0 warning(s)"
    assert entry.delivery_markdown.startswith("### AI Research Context Delivery")
    assert "unavailable" in entry.summary.lower()


def test_ai_research_context_consumer_entry_markdown_includes_delivery_output(current_response, previous_response):
    entry = build_ai_research_context_consumer_entry(_assembly(current_response, previous_response))

    markdown = build_ai_research_context_consumer_entry_markdown(entry)

    assert "AI Research Context Consumer Entry" in markdown
    assert "Governance visibility" in markdown
    assert "Quality visibility" in markdown
    assert "Delivery output:" in markdown
    assert "AI Research Context Delivery" in markdown
    assert "AI Research Context Audit Trail" in markdown
    assert "Stock code" in markdown
    assert "Market" in markdown
    assert "Company name" in markdown
    assert "recommendation" not in markdown.lower()
    assert "trading signal" not in markdown.lower()
