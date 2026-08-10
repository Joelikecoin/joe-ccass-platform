from __future__ import annotations

from app.data_quality import structured_warning
from ccass_core.ai_read_model import build_ai_read_model_v0_1
from ccass_core.ai_read_model_governance import build_ai_read_model_consumer_view
from ccass_core.ai_research_context_assembly import build_ai_research_context_assembly
from ccass_core.ai_research_context_validation import build_ai_research_context_validation
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
        request_id="trace-validation-001",
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


def test_ai_research_context_validation_marks_consumer_ready_with_warnings(current_response, previous_response):
    ai_read_model = _build_read_model(current_response, previous_response)
    source_trace = _source_trace(current_response)
    research_package = build_research_context_package(ai_read_model=ai_read_model)
    assembly = build_ai_research_context_assembly(
        research_context_package=research_package,
        research_context_consumer_view=build_research_context_consumer_view(research_package),
        ai_read_model_consumer_view=build_ai_read_model_consumer_view(ai_read_model, source_trace=source_trace),
        source_trace=source_trace,
    )

    validation = build_ai_research_context_validation(assembly)

    assert validation.context_available is True
    assert validation.provenance_present is True
    assert validation.freshness_metadata_present is True
    assert validation.warnings_consistent is True
    assert validation.limitation_visible is True
    assert validation.consumer_ready is True
    assert validation.status == "partial"
    assert any("warning" in warning.lower() for warning in validation.warnings)
    assert "status=partial" in validation.summary


def test_ai_research_context_validation_marks_missing_assembly_unavailable():
    validation = build_ai_research_context_validation(None)

    assert validation.status == "unavailable"
    assert validation.consumer_ready is False
    assert validation.warnings == ["AI research context assembly is unavailable."]
    assert "unavailable" in validation.summary.lower()


def test_ai_research_context_validation_flags_missing_provenance(current_response, previous_response):
    ai_read_model = _build_read_model(current_response, previous_response)
    research_package = build_research_context_package(ai_read_model=ai_read_model)
    assembly = build_ai_research_context_assembly(
        research_context_package=research_package,
        research_context_consumer_view=build_research_context_consumer_view(research_package),
        ai_read_model_consumer_view=build_ai_read_model_consumer_view(ai_read_model),
    )

    validation = build_ai_research_context_validation(assembly)

    assert validation.context_available is True
    assert validation.provenance_present is False
    assert validation.consumer_ready is False
    assert validation.status in {"partial", "unknown"}
    assert any("provenance" in warning.lower() for warning in validation.warnings)


def test_ai_research_context_validation_flags_missing_freshness_metadata():
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

    validation = build_ai_research_context_validation(assembly)

    assert validation.context_available is False
    assert validation.freshness_metadata_present is False
    assert validation.consumer_ready is False
    assert any("freshness metadata" in warning.lower() for warning in validation.warnings)
