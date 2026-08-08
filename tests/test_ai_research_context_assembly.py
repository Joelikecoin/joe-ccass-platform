from __future__ import annotations

from app.data_quality import structured_warning
from ccass_core.ai_read_model import build_ai_read_model_v0_1
from ccass_core.ai_read_model_governance import build_ai_read_model_consumer_view
from ccass_core.ai_research_context_assembly import build_ai_research_context_assembly
from ccass_core.compute import compute_analysis
from ccass_core.research_context import build_research_context_package
from ccass_core.research_context_consumer import build_research_context_consumer_view
from ccass_core.source_trace import (
    SourceDateGovernanceReference,
    SourceTraceIdentity,
    SourceTraceSelection,
    SourceTraceView,
)


def _source_trace(response) -> SourceTraceView:
    return SourceTraceView(
        request_id="trace-assembly-001",
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


def test_ai_research_context_assembly_handles_normal_context(current_response, previous_response):
    current_response = current_response.model_copy(
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
    previous_response = previous_response.model_copy(deep=True)
    ai_read_model = _build_read_model(current_response, previous_response)
    research_package = build_research_context_package(ai_read_model=ai_read_model)
    research_view = build_research_context_consumer_view(research_package)
    ai_view = build_ai_read_model_consumer_view(ai_read_model, source_trace=_source_trace(current_response))

    assembly = build_ai_research_context_assembly(
        research_context_package=research_package,
        research_context_consumer_view=research_view,
        ai_read_model_consumer_view=ai_view,
        source_trace=_source_trace(current_response),
    )

    assert assembly.available is True
    assert assembly.identity.stock_code == "01592"
    assert assembly.research_context_available is True
    assert assembly.ai_read_model_available is True
    assert assembly.governance_available is True
    assert assembly.research_context_consumer_view is not None
    assert assembly.ai_read_model_consumer_view is not None
    assert assembly.research_governance_context is not None
    assert assembly.ai_read_model_governance_context is not None
    assert assembly.ai_read_model_consumer_guidance is not None
    assert assembly.input_blocks[0].name == "research_context"
    assert assembly.input_blocks[1].name == "research_governance"
    assert assembly.input_blocks[2].name == "ai_read_model"
    assert assembly.input_blocks[3].name == "ai_read_model_governance"
    assert assembly.input_blocks[4].name == "ai_read_model_guidance"
    assert "AI research context assembly:" in assembly.summary
    assert "research_context=available" in assembly.summary
    assert "ai_read_model=available" in assembly.summary
    assert any("CSV_FALLBACK_USED" in warning for warning in assembly.warnings)


def test_ai_research_context_assembly_handles_missing_context():
    assembly = build_ai_research_context_assembly()

    assert assembly.available is False
    assert assembly.identity is None
    assert assembly.research_context_available is False
    assert assembly.ai_read_model_available is False
    assert assembly.governance_available is False
    assert assembly.input_blocks == []
    assert assembly.warnings == []
    assert "unavailable" in assembly.summary.lower()


def test_ai_research_context_assembly_handles_empty_data():
    ai_read_model = build_ai_read_model_v0_1(
        code="01592",
        response=None,
        surface="ccass_ai_read_model",
    )
    research_package = build_research_context_package(ai_read_model=ai_read_model)
    research_view = build_research_context_consumer_view(research_package)
    ai_view = build_ai_read_model_consumer_view(None)

    assembly = build_ai_research_context_assembly(
        research_context_package=research_package,
        research_context_consumer_view=research_view,
        ai_read_model_consumer_view=ai_view,
    )

    assert assembly.available is True
    assert assembly.research_context_available is True
    assert assembly.ai_read_model_available is False
    assert assembly.identity.stock_code == "01592"
    assert assembly.research_context_consumer_view.quality_context.freshness_status == "unavailable"
    assert assembly.ai_read_model_consumer_view is not None
    assert assembly.ai_read_model_consumer_view.available is False


def test_ai_research_context_assembly_preserves_governance_metadata(current_response, previous_response):
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

    assert assembly.research_governance_context is not None
    assert assembly.research_governance_context.source_trace_reference == source_trace.request_id + " / " + source_trace.route + " / existing_service"
    assert assembly.research_governance_interpretation is not None
    assert assembly.research_governance_interpretation.freshness_state == research_package.quality_context.freshness_status
    assert assembly.ai_read_model_governance_context is not None
    assert assembly.ai_read_model_governance_context.source_trace_reference == source_trace.request_id + " / " + source_trace.route + " / existing_service"
    assert assembly.ai_read_model_governance_interpretation is not None
    assert assembly.ai_read_model_governance_interpretation.provenance_summary == f"{current_response.metadata.source_name} / ccass_holdings / primary"
    assert assembly.ai_read_model_consumer_guidance is not None
    assert assembly.ai_read_model_consumer_guidance.warnings == assembly.ai_read_model_governance_context.warnings
