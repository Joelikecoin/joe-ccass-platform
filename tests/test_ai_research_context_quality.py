from __future__ import annotations

from app.data_quality import structured_warning
from ccass_core.ai_read_model import build_ai_read_model_v0_1
from ccass_core.ai_read_model_governance import build_ai_read_model_consumer_view
from ccass_core.ai_research_context_assembly import build_ai_research_context_assembly
from ccass_core.ai_research_context_consumer import (
    build_ai_research_context_consumer_view,
    build_ai_research_context_usage_markdown,
)
from ccass_core.ai_research_context_quality import build_ai_research_context_quality_summary
from ccass_core.compute import compute_analysis
from ccass_core.research_context import build_research_context_package
from ccass_core.research_context_consumer import build_research_context_consumer_view
from ccass_core.source_trace import (
    SourceDateGovernanceReference,
    SourceTraceIdentity,
    SourceTraceSelection,
    SourceTraceView,
)


def _source_trace(response):
    return SourceTraceView(
        request_id="trace-quality-001",
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


def test_ai_research_context_quality_summary_reflects_validation_and_governance(current_response, previous_response):
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
    ai_read_model = _build_read_model(current_response, previous_response)
    source_trace = _source_trace(current_response)
    research_package = build_research_context_package(ai_read_model=ai_read_model)
    assembly = build_ai_research_context_assembly(
        research_context_package=research_package,
        research_context_consumer_view=build_research_context_consumer_view(research_package),
        ai_read_model_consumer_view=build_ai_read_model_consumer_view(ai_read_model, source_trace=source_trace),
        source_trace=source_trace,
    )
    consumer_view = build_ai_research_context_consumer_view(assembly)

    quality_summary = build_ai_research_context_quality_summary(
        validation_status=consumer_view.validation.status,
        consumer_ready=consumer_view.validation.consumer_ready,
        context_available=consumer_view.context_available,
        provenance_reference=consumer_view.provenance_reference,
        freshness_reference=consumer_view.freshness_reference,
        validation_summary=consumer_view.validation.summary,
        warning_summary=consumer_view.warning_summary,
        limitation_summary=consumer_view.limitation_summary,
        warnings=consumer_view.validation.warnings,
    )

    assert quality_summary.overall_context_status == "partial"
    assert quality_summary.consumer_ready is True
    assert quality_summary.availability_summary == "Consumer context is available."
    assert quality_summary.provenance_summary == consumer_view.provenance_reference
    assert quality_summary.freshness_summary == consumer_view.freshness_reference
    assert quality_summary.validation_summary == consumer_view.validation.summary
    assert quality_summary.warning_summary == consumer_view.warning_summary
    assert quality_summary.limitation_summary == consumer_view.limitation_summary
    assert quality_summary.warnings
    assert "AI research context quality:" in quality_summary.summary


def test_ai_research_context_quality_summary_handles_missing_context():
    quality_summary = build_ai_research_context_quality_summary()

    assert quality_summary.overall_context_status == "unknown"
    assert quality_summary.consumer_ready is False
    assert quality_summary.availability_summary == "Consumer context is unavailable."
    assert quality_summary.provenance_summary == "not available"
    assert quality_summary.freshness_summary == "unavailable"
    assert quality_summary.warning_summary == "0 warning(s)"
    assert quality_summary.warnings == []


def test_ai_research_context_quality_summary_is_visible_in_consumer_markdown(current_response, previous_response):
    ai_read_model = _build_read_model(current_response, previous_response)
    source_trace = _source_trace(current_response)
    research_package = build_research_context_package(ai_read_model=ai_read_model)
    assembly = build_ai_research_context_assembly(
        research_context_package=research_package,
        research_context_consumer_view=build_research_context_consumer_view(research_package),
        ai_read_model_consumer_view=build_ai_read_model_consumer_view(ai_read_model, source_trace=source_trace),
        source_trace=source_trace,
    )
    consumer_view = build_ai_research_context_consumer_view(assembly)

    markdown = build_ai_research_context_usage_markdown(consumer_view)

    assert "Quality overall status" in markdown
    assert "Quality availability summary" in markdown
    assert "Quality summary" in markdown
    assert "Freshness" in markdown
    assert "Provenance" in markdown
    assert "Validation" in markdown
