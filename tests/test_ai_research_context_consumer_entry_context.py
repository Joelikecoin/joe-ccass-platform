from __future__ import annotations

from datetime import timedelta

from ccass_core.ai_read_model import AIReadModelSnapshotReference, build_ai_read_model_v0_1
from ccass_core.ai_read_model_governance import build_ai_read_model_consumer_view
from ccass_core.ai_research_context_assembly import build_ai_research_context_assembly
from ccass_core.ai_research_context_consumer import build_ai_research_context_consumer_view
from ccass_core.ai_research_context_consumer_entry_context import (
    build_ai_research_context_consumer_entry_context,
    build_ai_research_context_consumer_entry_context_markdown,
)
from ccass_core.ai_research_context_entry import build_ai_research_context_consumer_entry
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
        request_id="trace-consumer-entry-context-001",
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


def _entry(current_response, previous_response):
    ai_read_model = _build_read_model(current_response, previous_response)
    source_trace = _source_trace(current_response)
    historical_one = AIReadModelSnapshotReference(
        snapshot_id=98,
        snapshot_date=current_response.metadata.data_as_of - timedelta(days=2),
        data_as_of=current_response.metadata.data_as_of - timedelta(days=2),
        fetched_at=current_response.metadata.fetched_at,
        source=current_response.metadata.source_name,
    )
    historical_two = AIReadModelSnapshotReference(
        snapshot_id=99,
        snapshot_date=current_response.metadata.data_as_of - timedelta(days=1),
        data_as_of=current_response.metadata.data_as_of - timedelta(days=1),
        fetched_at=current_response.metadata.fetched_at,
        source=current_response.metadata.source_name,
    )
    research_package = build_research_context_package(
        ai_read_model=ai_read_model,
        history_snapshots=(historical_one, historical_two),
    )
    assembly = build_ai_research_context_assembly(
        research_context_package=research_package,
        research_context_consumer_view=build_research_context_consumer_view(research_package),
        ai_read_model_consumer_view=build_ai_read_model_consumer_view(
            ai_read_model,
            source_trace=source_trace,
        ),
        source_trace=source_trace,
    )
    return build_ai_research_context_consumer_entry(assembly)


def test_ai_research_context_consumer_entry_context_unifies_current_and_historical_access(
    current_response, previous_response
):
    entry = _entry(current_response, previous_response)
    consumer_entry_context = build_ai_research_context_consumer_entry_context(
        entry.delivery,
        entry.historical_delivery,
    )

    assert consumer_entry_context.available is True
    assert consumer_entry_context.current_context is not None
    assert consumer_entry_context.historical_context is not None
    assert consumer_entry_context.current_context_visible is True
    assert consumer_entry_context.historical_context_visible is True
    assert consumer_entry_context.comparison_visible is True
    assert consumer_entry_context.timeline_visible is True
    assert consumer_entry_context.quality_visible is True
    assert consumer_entry_context.summary_visible is True
    assert consumer_entry_context.context_state == "available"
    assert "current_context_visible=" in consumer_entry_context.summary
    assert "historical_context_visible=" in consumer_entry_context.summary
    assert consumer_entry_context.current_context_reference
    assert consumer_entry_context.historical_context_reference


def test_ai_research_context_consumer_entry_context_markdown_handles_unavailable_state():
    markdown = build_ai_research_context_consumer_entry_context_markdown(None)

    assert "AI Research Context Consumer Entry Context" in markdown
    assert "unavailable" in markdown.lower()
