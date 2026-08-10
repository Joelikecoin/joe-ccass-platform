from __future__ import annotations

from datetime import UTC, date, datetime

from app.data_quality import structured_warning
from app.models import CcassResponse, SourceMetadata
from ccass_core.ai_read_model import build_ai_read_model_v0_1
from ccass_core.ai_read_model_governance import build_ai_read_model_consumer_view
from ccass_core.ai_research_context_assembly import build_ai_research_context_assembly
from ccass_core.ai_research_context_consumer import (
    build_ai_research_context_consumer_view,
    build_ai_research_context_usage_markdown,
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


def _source_trace(response: CcassResponse) -> SourceTraceView:
    return SourceTraceView(
        request_id="trace-consumer-001",
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


def test_ai_research_context_consumer_view_handles_normal_assembly(current_response, previous_response):
    ai_read_model = _build_read_model(current_response, previous_response)
    research_package = build_research_context_package(ai_read_model=ai_read_model)
    source_trace = _source_trace(current_response)
    research_view = build_research_context_consumer_view(research_package)
    ai_view = build_ai_read_model_consumer_view(ai_read_model, source_trace=source_trace)
    assembly = build_ai_research_context_assembly(
        research_context_package=research_package,
        research_context_consumer_view=research_view,
        ai_read_model_consumer_view=ai_view,
        source_trace=source_trace,
    )

    consumer_view = build_ai_research_context_consumer_view(assembly)

    assert consumer_view.available is True
    assert consumer_view.context_available is True
    assert consumer_view.governance_summary == assembly.summary
    assert source_trace.request_id in consumer_view.provenance_reference
    assert consumer_view.freshness_reference
    assert consumer_view.warning_summary == f"{len(assembly.warnings)} warning(s)"
    assert consumer_view.limitation_summary == assembly.research_governance_interpretation.limitation_summary
    assert consumer_view.usage_steps
    assert consumer_view.input_blocks == assembly.input_blocks
    assert consumer_view.validation is not None
    assert consumer_view.validation.context_available is True
    assert consumer_view.validation.provenance_present is True
    assert consumer_view.validation.freshness_metadata_present is True
    assert consumer_view.validation.warnings_consistent is True
    assert consumer_view.validation.limitation_visible is True
    assert consumer_view.contract_meta == assembly.contract_meta
    assert "AI research context consumer view:" in consumer_view.summary


def test_ai_research_context_consumer_view_handles_missing_assembly():
    consumer_view = build_ai_research_context_consumer_view(None)

    assert consumer_view.available is False
    assert consumer_view.assembly is None
    assert consumer_view.context_available is False
    assert consumer_view.governance_summary == "AI research context assembly is unavailable."
    assert consumer_view.provenance_reference == "not available"
    assert consumer_view.freshness_reference == "unavailable"
    assert consumer_view.warning_summary == "0 warning(s)"
    assert consumer_view.input_blocks == []
    assert consumer_view.warnings == []
    assert "unavailable" in consumer_view.summary.lower()


def test_ai_research_context_consumer_view_handles_empty_data():
    ai_read_model = build_ai_read_model_v0_1(
        code="01592",
        response=None,
        surface="ccass_ai_read_model",
    )
    research_package = build_research_context_package(ai_read_model=ai_read_model)
    assembly = build_ai_research_context_assembly(
        research_context_package=research_package,
        research_context_consumer_view=build_research_context_consumer_view(research_package),
        ai_read_model_consumer_view=build_ai_read_model_consumer_view(None),
    )

    consumer_view = build_ai_research_context_consumer_view(assembly)

    assert consumer_view.available is True
    assert consumer_view.context_available is True
    assert consumer_view.freshness_reference == "unavailable"
    assert consumer_view.warning_summary == "0 warning(s)"
    assert consumer_view.validation is not None
    assert consumer_view.validation.status == "partial"
    assert consumer_view.validation.consumer_ready is False
    assert consumer_view.governance_summary == assembly.summary


def test_ai_research_context_consumer_view_propagates_warnings(current_response, previous_response):
    current_with_warning = current_response.model_copy(
        deep=True,
        update={
            "data_quality_warnings": [
                structured_warning(
                    "SOURCE_STATUS",
                    "CSV_FALLBACK_USED",
                    "Primary mirror failed; CSV fallback used.",
                )
            ]
        },
    )
    ai_read_model = _build_read_model(current_with_warning, previous_response)
    research_package = build_research_context_package(ai_read_model=ai_read_model)
    source_trace = _source_trace(current_with_warning)
    assembly = build_ai_research_context_assembly(
        research_context_package=research_package,
        research_context_consumer_view=build_research_context_consumer_view(research_package),
        ai_read_model_consumer_view=build_ai_read_model_consumer_view(ai_read_model, source_trace=source_trace),
        source_trace=source_trace,
    )

    consumer_view = build_ai_research_context_consumer_view(assembly)

    assert any("CSV_FALLBACK_USED" in warning for warning in consumer_view.warnings)
    assert "warning(s)" in consumer_view.warning_summary
    assert consumer_view.validation is not None
    assert consumer_view.validation.status == "partial"
    assert consumer_view.validation.consumer_ready is True
    assert "recommendation" not in build_ai_research_context_usage_markdown(consumer_view).lower()
    assert "trading signal" not in build_ai_research_context_usage_markdown(consumer_view).lower()


def test_ai_research_context_usage_markdown_includes_governance_fields(current_response, previous_response):
    ai_read_model = _build_read_model(current_response, previous_response)
    research_package = build_research_context_package(ai_read_model=ai_read_model)
    source_trace = _source_trace(current_response)
    assembly = build_ai_research_context_assembly(
        research_context_package=research_package,
        research_context_consumer_view=build_research_context_consumer_view(research_package),
        ai_read_model_consumer_view=build_ai_read_model_consumer_view(ai_read_model, source_trace=source_trace),
        source_trace=source_trace,
    )
    consumer_view = build_ai_research_context_consumer_view(assembly)

    markdown = build_ai_research_context_usage_markdown(consumer_view)

    assert "AI Research Context Consumer" in markdown
    assert "Context availability" in markdown
    assert "Governance summary" in markdown
    assert "Provenance reference" in markdown
    assert "Freshness reference" in markdown
    assert "Warning summary" in markdown
    assert "Limitation summary" in markdown
    assert "Validation status" in markdown
    assert "Consumer ready" in markdown
    assert "no investment logic" not in markdown.lower()
