from __future__ import annotations

from ccass_core.ai_read_model import build_ai_read_model_v0_1
from ccass_core.ai_read_model_governance import build_ai_read_model_consumer_view
from ccass_core.ai_research_context_assembly import build_ai_research_context_assembly
from ccass_core.ai_research_context_consumer import build_ai_research_context_consumer_view
from ccass_core.ai_research_context_consumer_boundary import (
    build_ai_research_context_consumer_boundary_markdown,
)
from ccass_core.ai_research_context_consumer_governance_status_validation import (
    build_ai_research_context_consumer_governance_status_validation_markdown,
)
from ccass_core.ai_research_context_consumer_governance_snapshot import (
    build_ai_research_context_consumer_governance_snapshot_markdown,
)
from ccass_core.ai_research_context_consumer_governance_snapshot_validation import (
    build_ai_research_context_consumer_governance_snapshot_validation_markdown,
)
from ccass_core.ai_research_context_consumer_governance_timeline import (
    build_ai_research_context_consumer_governance_timeline_markdown,
)
from ccass_core.ai_research_context_consumer_governance_timeline_validation import (
    build_ai_research_context_consumer_governance_timeline_validation_markdown,
)
from ccass_core.ai_research_context_consumer_governance_timeline_summary import (
    build_ai_research_context_consumer_governance_timeline_summary_markdown,
)
from ccass_core.ai_research_context_consumer_governance_timeline_snapshot import (
    build_ai_research_context_consumer_governance_timeline_snapshot_markdown,
)
from ccass_core.ai_research_context_consumer_governance_timeline_snapshot_validation import (
    build_ai_research_context_consumer_governance_timeline_snapshot_validation_markdown,
)
from ccass_core.ai_research_context_consumer_governance_timeline_snapshot_summary import (
    build_ai_research_context_consumer_governance_timeline_snapshot_summary_markdown,
)
from ccass_core.ai_research_context_consumer_governance_timeline_snapshot_summary_validation import (
    build_ai_research_context_consumer_governance_timeline_snapshot_summary_validation_markdown,
)
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
    assert entry.historical_delivery is not None
    assert entry.historical_delivery.available is True
    assert entry.historical_delivery.timeline_visible is True
    assert entry.historical_delivery.summary_visible is True
    assert entry.consumer_context is not None
    assert entry.consumer_context.available is True
    assert entry.consumer_context.current_context is entry.delivery
    assert entry.consumer_context.historical_context is entry.historical_delivery
    assert entry.consumer_context.context_state == "available"
    assert entry.consumer_boundary is not None
    assert entry.consumer_boundary.available is True
    assert entry.consumer_boundary.approved_surface == (
        "current_context",
        "historical_context",
        "consumer_context",
        "quality_summary",
    )
    assert entry.consumer_boundary.current_context is entry.delivery
    assert entry.consumer_boundary.historical_context is entry.historical_delivery
    assert entry.consumer_boundary.consumer_context is entry.consumer_context
    assert entry.consumer_boundary.quality_summary is entry.quality_summary
    assert entry.consumer_boundary.current_context_visible is True
    assert entry.consumer_boundary.historical_context_visible is True
    assert entry.consumer_boundary.comparison_visible is True
    assert entry.consumer_boundary.timeline_visible is True
    assert entry.consumer_boundary.quality_visible is True
    assert entry.consumer_boundary.summary_visible is True
    assert entry.consumer_boundary.context_state == "available"
    assert entry.consumer_boundary.surface_version_reference == entry.consumer_boundary.contract_meta.version
    assert entry.consumer_boundary.compatibility_metadata is not None
    assert entry.consumer_boundary.compatibility_metadata.supported_surface == entry.consumer_boundary.approved_surface
    assert entry.consumer_boundary.capability_metadata is not None
    assert entry.consumer_boundary.capability_metadata.supported_surface == entry.consumer_boundary.approved_surface
    assert entry.consumer_boundary.capability_validation is not None
    assert entry.consumer_boundary.capability_validation.capability_consistent is True
    assert entry.consumer_boundary_capability_validation is entry.consumer_boundary.capability_validation
    assert entry.consumer_boundary.readiness_status is not None
    assert entry.consumer_boundary.readiness_status.readiness_status == "ready"
    assert entry.consumer_boundary_readiness_status is entry.consumer_boundary.readiness_status
    assert entry.consumer_boundary.health_indicator is not None
    assert entry.consumer_boundary.health_indicator.health_status == "healthy"
    assert entry.consumer_boundary_health_indicator is entry.consumer_boundary.health_indicator
    assert entry.consumer_boundary.governance_summary is not None
    assert entry.consumer_boundary.governance_summary.governance_status == "complete"
    assert entry.consumer_boundary_governance_summary is entry.consumer_boundary.governance_summary
    assert entry.consumer_boundary.governance_status is not None
    assert entry.consumer_boundary.governance_status.governance_status == "complete"
    assert entry.consumer_boundary_governance_status is entry.consumer_boundary.governance_status
    assert entry.consumer_boundary.governance_status_validation is not None
    assert entry.consumer_boundary.governance_status_validation.governance_status_consistent is True
    assert entry.consumer_boundary_governance_status_validation is entry.consumer_boundary.governance_status_validation
    assert entry.consumer_boundary.governance_snapshot_validation is not None
    assert entry.consumer_boundary.governance_snapshot_validation.governance_snapshot_consistent is True
    assert entry.consumer_boundary_governance_snapshot_validation is entry.consumer_boundary.governance_snapshot_validation
    assert entry.consumer_boundary.governance_timeline is not None
    assert entry.consumer_boundary.governance_timeline.governance_timeline_state == "complete"
    assert entry.consumer_boundary.governance_timeline.governance_timeline_visible is True
    assert entry.consumer_boundary.governance_timeline.timeline_continuity_consistent is True
    assert entry.consumer_boundary_governance_timeline is entry.consumer_boundary.governance_timeline
    assert entry.consumer_boundary.governance_timeline_validation is not None
    assert entry.consumer_boundary.governance_timeline_validation.validation_state == "consistent"
    assert entry.consumer_boundary.governance_timeline_validation.governance_timeline_visible is True
    assert (
        entry.consumer_boundary_governance_timeline_validation
        is entry.consumer_boundary.governance_timeline_validation
    )
    assert entry.consumer_boundary.governance_timeline_summary is not None
    assert entry.consumer_boundary.governance_timeline_summary.governance_timeline_summary_state == "complete"
    assert entry.consumer_boundary.governance_timeline_summary.governance_timeline_summary_visible is True
    assert (
        entry.consumer_boundary_governance_timeline_summary
        is entry.consumer_boundary.governance_timeline_summary
    )
    assert entry.consumer_boundary.governance_timeline_snapshot is not None
    assert entry.consumer_boundary.governance_timeline_snapshot.governance_timeline_snapshot_state == "complete"
    assert entry.consumer_boundary.governance_timeline_snapshot.governance_timeline_snapshot_visible is True
    assert (
        entry.consumer_boundary_governance_timeline_snapshot
        is entry.consumer_boundary.governance_timeline_snapshot
    )
    assert entry.consumer_boundary.governance_timeline_snapshot_validation is not None
    assert entry.consumer_boundary.governance_timeline_snapshot_validation.validation_state == "consistent"
    assert entry.consumer_boundary.governance_timeline_snapshot_validation.governance_timeline_snapshot_visible is True
    assert (
        entry.consumer_boundary_governance_timeline_snapshot_validation
        is entry.consumer_boundary.governance_timeline_snapshot_validation
    )
    assert entry.consumer_boundary.governance_timeline_snapshot_summary is not None
    assert entry.consumer_boundary.governance_timeline_snapshot_summary.governance_timeline_snapshot_summary_state == "complete"
    assert entry.consumer_boundary.governance_timeline_snapshot_summary.governance_timeline_snapshot_summary_visible is True
    assert (
        entry.consumer_boundary_governance_timeline_snapshot_summary
        is entry.consumer_boundary.governance_timeline_snapshot_summary
    )
    assert entry.consumer_boundary.governance_timeline_snapshot_summary_validation is not None
    assert entry.consumer_boundary.governance_timeline_snapshot_summary_validation.validation_state == "consistent"
    assert entry.consumer_boundary.governance_timeline_snapshot_summary_validation.governance_timeline_snapshot_summary_visible is True
    assert (
        entry.consumer_boundary_governance_timeline_snapshot_summary_validation
        is entry.consumer_boundary.governance_timeline_snapshot_summary_validation
    )
    assert entry.consumer_boundary.governance_snapshot is not None
    assert entry.consumer_boundary.governance_snapshot.governance_snapshot_state == "complete"
    assert entry.consumer_boundary_governance_snapshot is entry.consumer_boundary.governance_snapshot
    assert entry.consumer_boundary.governance_validation is not None
    assert entry.consumer_boundary.governance_validation.governance_consistent is True
    assert entry.consumer_boundary.governance_validation.validation_state == "consistent"
    assert entry.consumer_boundary_governance_validation is entry.consumer_boundary.governance_validation
    assert entry.consumer_boundary_version_reference == entry.consumer_boundary.contract_meta.version
    assert (
        entry.consumer_boundary_compatibility_reference
        == entry.consumer_boundary.compatibility_metadata.compatibility_reference
    )
    assert (
        entry.consumer_boundary_capability_reference
        == entry.consumer_boundary.capability_metadata.capability_reference
    )
    assert (
        entry.consumer_boundary_readiness_reference
        == entry.consumer_boundary.readiness_status.readiness_reference
    )
    assert (
        entry.consumer_boundary_health_reference
        == entry.consumer_boundary.health_indicator.health_reference
    )
    assert (
        entry.consumer_boundary_governance_reference
        == entry.consumer_boundary.governance_summary.governance_reference
    )
    assert (
        entry.consumer_boundary_governance_status_reference
        == entry.consumer_boundary.governance_status.governance_reference
    )
    assert (
        entry.consumer_boundary_governance_status_validation_reference
        == entry.consumer_boundary.governance_status_validation.validation_reference
    )
    assert (
        entry.consumer_boundary_governance_snapshot_validation_reference
        == entry.consumer_boundary.governance_snapshot_validation.validation_reference
    )
    assert (
        entry.consumer_boundary_governance_timeline_reference
        == entry.consumer_boundary.governance_timeline.governance_timeline_reference
    )
    assert (
        entry.consumer_boundary_governance_timeline_validation_reference
        == entry.consumer_boundary.governance_timeline_validation.validation_reference
    )
    assert (
        entry.consumer_boundary_governance_timeline_summary_reference
        == entry.consumer_boundary.governance_timeline_summary.governance_timeline_summary_reference
    )
    assert (
        entry.consumer_boundary_governance_timeline_snapshot_summary_validation_reference
        == entry.consumer_boundary.governance_timeline_snapshot_summary_validation.validation_reference
    )
    assert (
        entry.consumer_boundary_governance_snapshot_reference
        == entry.consumer_boundary.governance_snapshot.governance_snapshot_reference
    )
    assert (
        entry.consumer_boundary_governance_continuity_reference
        == entry.consumer_boundary.governance_snapshot.governance_continuity_reference
    )
    assert (
        entry.consumer_boundary_governance_validation_reference
        == entry.consumer_boundary.governance_validation.validation_reference
    )
    assert "consumer boundary:" in entry.summary
    assert "current_context_visible=" in entry.summary
    assert "historical_context_visible=" in entry.summary
    assert "surface_version_reference=v0.1" in entry.summary
    assert "compatibility_reference=" in entry.summary
    assert "capability_reference=" in entry.summary
    assert "capability_validation_state=consistent" in entry.summary
    assert "readiness_status=ready" in entry.summary
    assert "health_status=healthy" in entry.summary
    assert "governance_status=complete" in entry.summary
    assert "governance_validation_state=consistent" in entry.summary
    assert "governance_status_value=complete" in entry.summary
    assert "governance_status_visible=yes" in entry.summary
    assert "governance_status_validation_state=consistent" in entry.summary
    assert "governance_status_validation_visible=yes" in entry.summary
    assert "governance_snapshot_validation_state=consistent" in entry.summary
    assert "governance_snapshot_validation_visible=yes" in entry.summary
    assert "governance_timeline_validation_state=consistent" in entry.summary
    assert "governance_timeline_validation_visible=yes" in entry.summary
    assert "governance_timeline_summary_state=complete" in entry.summary
    assert "governance_timeline_summary_visible=yes" in entry.summary
    assert "governance_timeline_snapshot_state=complete" in entry.summary
    assert "governance_timeline_snapshot_visible=yes" in entry.summary
    assert "governance_timeline_snapshot_validation_state=consistent" in entry.summary
    assert "governance_timeline_snapshot_validation_visible=yes" in entry.summary
    assert "governance_timeline_snapshot_summary_state=complete" in entry.summary
    assert "governance_timeline_snapshot_summary_visible=yes" in entry.summary
    assert "governance_timeline_snapshot_summary_validation_state=consistent" in entry.summary
    assert "governance_timeline_snapshot_summary_validation_visible=yes" in entry.summary
    assert "governance_timeline_state=complete" in entry.summary
    assert "governance_timeline_visible=yes" in entry.summary
    assert "approved_surface=current_context | historical_context | consumer_context | quality_summary" in entry.summary
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
    assert "AI research context consumer boundary:" in entry.summary
    assert "consumer_ready=" in entry.summary
    assert "consumer boundary:" in entry.summary


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
    assert entry.comparison is not None
    assert entry.comparison.available is False
    assert entry.comparison.current_snapshot_reference is None
    assert entry.change_summary is not None
    assert entry.change_summary.available is False
    assert entry.change_summary.current_snapshot_summary == "not available"
    assert entry.timeline is not None
    assert entry.timeline.available is False
    assert entry.timeline_summary is not None
    assert entry.timeline_summary.available is False
    assert entry.historical_query is not None
    assert entry.historical_query.available is False
    assert entry.historical_comparison_query is not None
    assert entry.historical_comparison_query.available is False
    assert entry.historical_summary is not None
    assert entry.historical_summary.available is False
    assert entry.historical_delivery is not None
    assert entry.historical_delivery.available is False
    assert entry.consumer_context is not None
    assert entry.consumer_context.available is False
    assert entry.consumer_boundary is not None
    assert entry.consumer_boundary.available is False
    assert entry.consumer_boundary.governance_timeline is not None
    assert entry.consumer_boundary.governance_timeline.available is False
    assert entry.consumer_boundary.governance_timeline.governance_timeline_state == "unavailable"
    assert entry.consumer_boundary.governance_timeline.governance_timeline_visible is False
    assert entry.consumer_boundary.governance_timeline_validation is not None
    assert entry.consumer_boundary.governance_timeline_validation.available is False
    assert entry.consumer_boundary.governance_timeline_validation.validation_state == "unknown"
    assert entry.consumer_boundary.governance_timeline_validation.governance_timeline_visible is False
    assert entry.consumer_boundary.governance_timeline_summary is not None
    assert entry.consumer_boundary.governance_timeline_summary.available is False
    assert entry.consumer_boundary.governance_timeline_summary.governance_timeline_summary_state == "unavailable"
    assert entry.consumer_boundary.governance_timeline_summary.governance_timeline_summary_visible is False
    assert entry.consumer_boundary.governance_timeline_snapshot is not None
    assert entry.consumer_boundary.governance_timeline_snapshot.available is False
    assert entry.consumer_boundary.governance_timeline_snapshot.governance_timeline_snapshot_state == "unavailable"
    assert entry.consumer_boundary.governance_timeline_snapshot.governance_timeline_snapshot_visible is False
    assert entry.consumer_boundary.governance_timeline_snapshot_validation is not None
    assert entry.consumer_boundary.governance_timeline_snapshot_validation.available is False
    assert entry.consumer_boundary.governance_timeline_snapshot_validation.validation_state == "unknown"
    assert entry.consumer_boundary.governance_timeline_snapshot_validation.governance_timeline_snapshot_visible is False
    assert entry.consumer_boundary.governance_timeline_snapshot_validation.validation_reference == "not available"
    assert entry.consumer_boundary.governance_timeline_snapshot_summary is not None
    assert entry.consumer_boundary.governance_timeline_snapshot_summary.available is False
    assert entry.consumer_boundary.governance_timeline_snapshot_summary.governance_timeline_snapshot_summary_state == "unavailable"
    assert entry.consumer_boundary.governance_timeline_snapshot_summary.governance_timeline_snapshot_summary_visible is False
    assert entry.consumer_boundary.governance_timeline_snapshot_summary.governance_timeline_snapshot_summary_reference == "not available"
    assert entry.consumer_boundary.governance_timeline_snapshot_summary_validation is not None
    assert entry.consumer_boundary.governance_timeline_snapshot_summary_validation.available is False
    assert entry.consumer_boundary.governance_timeline_snapshot_summary_validation.validation_state == "unknown"
    assert entry.consumer_boundary.governance_timeline_snapshot_summary_validation.governance_timeline_snapshot_summary_visible is False
    assert entry.consumer_boundary.governance_timeline_snapshot_summary_validation.validation_reference == "not available"
    assert entry.consumer_boundary.governance_summary is not None
    assert entry.consumer_boundary.governance_summary.governance_status == "unavailable"
    assert entry.consumer_boundary.governance_status is not None
    assert entry.consumer_boundary.governance_status.governance_status == "unavailable"
    assert entry.consumer_boundary_governance_status is entry.consumer_boundary.governance_status
    assert entry.consumer_boundary.governance_status_validation is not None
    assert entry.consumer_boundary.governance_status_validation.validation_state == "unknown"
    assert entry.consumer_boundary_governance_status_validation is entry.consumer_boundary.governance_status_validation
    assert entry.consumer_boundary.governance_snapshot_validation is not None
    assert entry.consumer_boundary.governance_snapshot_validation.validation_state == "unknown"
    assert entry.consumer_boundary_governance_snapshot_validation is entry.consumer_boundary.governance_snapshot_validation
    assert entry.consumer_boundary_governance_timeline is entry.consumer_boundary.governance_timeline
    assert entry.consumer_boundary.governance_snapshot is not None
    assert entry.consumer_boundary.governance_snapshot.governance_snapshot_state == "unavailable"
    assert entry.consumer_boundary_governance_snapshot is entry.consumer_boundary.governance_snapshot
    assert entry.consumer_boundary_governance_status_reference == "not available"
    assert entry.consumer_boundary_governance_status_validation_reference == "not available"
    assert entry.consumer_boundary_governance_snapshot_validation_reference == "not available"
    assert entry.consumer_boundary_governance_timeline_reference == "not available"
    assert entry.consumer_boundary_governance_timeline_validation_reference == "not available"
    assert entry.consumer_boundary_governance_timeline_summary_reference == "not available"
    assert entry.consumer_boundary_governance_timeline_snapshot_reference == "not available"
    assert entry.consumer_boundary_governance_timeline_snapshot_validation_reference == "not available"
    assert entry.consumer_boundary_governance_timeline_snapshot_summary_reference == "not available"
    assert entry.consumer_boundary_governance_timeline_snapshot_summary_validation_reference == "not available"
    assert entry.consumer_boundary_governance_snapshot_reference == "not available"
    assert entry.consumer_boundary_governance_continuity_reference == "not available"
    assert entry.consumer_boundary.approved_surface == (
        "current_context",
        "historical_context",
        "consumer_context",
        "quality_summary",
    )
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
    assert "AI Research Context Consumer Boundary" in markdown
    assert "AI Research Context Consumer Capability Validation" in markdown
    assert "AI Research Context Consumer Readiness" in markdown
    assert "AI Research Context Consumer Health" in markdown
    assert "AI Research Context Consumer Governance Summary" in markdown
    assert "AI Research Context Consumer Governance Status" in markdown
    assert "AI Research Context Consumer Governance Status Validation" in markdown
    assert "AI Research Context Consumer Governance Snapshot Validation" in markdown
    assert "AI Research Context Consumer Governance Timeline" in markdown
    assert "AI Research Context Consumer Governance Timeline Validation" in markdown
    assert "AI Research Context Consumer Governance Timeline Summary" in markdown
    assert "AI Research Context Consumer Governance Snapshot" in markdown
    assert "AI Research Context Consumer Governance Timeline Snapshot Validation" in markdown
    assert "AI Research Context Consumer Governance Validation" in markdown
    assert "AI Research Context Consumer Governance Snapshot" in build_ai_research_context_consumer_governance_snapshot_markdown(
        entry.consumer_boundary.governance_snapshot
    )
    assert "AI Research Context Consumer Governance Snapshot Validation" in build_ai_research_context_consumer_governance_snapshot_validation_markdown(
        entry.consumer_boundary.governance_snapshot_validation
    )
    assert (
        "AI Research Context Consumer Governance Timeline Validation"
        in build_ai_research_context_consumer_governance_timeline_validation_markdown(
            entry.consumer_boundary.governance_timeline_validation
        )
    )
    assert (
        "AI Research Context Consumer Governance Timeline Summary"
        in build_ai_research_context_consumer_governance_timeline_summary_markdown(
            entry.consumer_boundary.governance_timeline_summary
        )
    )
    assert (
        "AI Research Context Consumer Governance Timeline Snapshot"
        in build_ai_research_context_consumer_governance_timeline_snapshot_markdown(
            entry.consumer_boundary.governance_timeline_snapshot
        )
    )
    assert (
        "AI Research Context Consumer Governance Timeline Snapshot Validation"
        in build_ai_research_context_consumer_governance_timeline_snapshot_validation_markdown(
            entry.consumer_boundary.governance_timeline_snapshot_validation
        )
    )
    assert (
        "AI Research Context Consumer Governance Timeline Snapshot Summary"
        in build_ai_research_context_consumer_governance_timeline_snapshot_summary_markdown(
            entry.consumer_boundary.governance_timeline_snapshot_summary
        )
    )
    assert (
        "AI Research Context Consumer Governance Timeline Snapshot Summary Validation"
        in build_ai_research_context_consumer_governance_timeline_snapshot_summary_validation_markdown(
            entry.consumer_boundary.governance_timeline_snapshot_summary_validation
        )
    )
    assert "Delivery output:" in markdown
    assert "AI Research Context Delivery" in markdown
    assert "Surface version reference" in markdown
    assert "Compatibility reference" in markdown
    assert "Capability reference" in markdown
    assert "AI Research Context Audit Trail" in markdown
    assert "Stock code" in markdown
    assert "Market" in markdown
    assert "Company name" in markdown
    assert "AI Research Context Comparison" not in markdown
    assert "AI Research Context Change Summary" not in markdown
    assert "AI Research Context Timeline" not in markdown
    assert "AI Research Context Historical Query" not in markdown
    assert "AI Research Context Historical Delivery" not in markdown
    assert "recommendation" not in markdown.lower()
    assert "trading signal" not in markdown.lower()


def test_ai_research_context_consumer_boundary_markdown_uses_approved_consumer_surface(
    current_response, previous_response
):
    entry = build_ai_research_context_consumer_entry(_assembly(current_response, previous_response))

    markdown = build_ai_research_context_consumer_boundary_markdown(entry.consumer_boundary)

    assert "AI Research Context Consumer Boundary" in markdown
    assert "Current context visible" in markdown
    assert "Historical context visible" in markdown
    assert "Quality visible" in markdown
    assert "Health status" in markdown
    assert "Governance status" in markdown
    assert "Governance validation state" in markdown
    assert "Approved surface" in markdown
    assert "Consumer boundary contract" in markdown
    assert set(type(entry.consumer_boundary).model_fields).issuperset(
        {
            "approved_surface",
            "current_context",
            "historical_context",
            "consumer_context",
            "quality_summary",
            "health_indicator",
            "governance_summary",
            "governance_status",
            "governance_status_validation",
            "governance_snapshot_validation",
            "governance_timeline",
            "governance_timeline_validation",
            "governance_timeline_summary",
            "governance_timeline_snapshot",
            "governance_timeline_snapshot_validation",
            "governance_timeline_snapshot_summary",
            "governance_timeline_snapshot_summary_validation",
            "governance_snapshot",
            "governance_validation",
        }
    )
    assert "comparison" not in type(entry.consumer_boundary).model_fields
    assert "timeline" not in type(entry.consumer_boundary).model_fields
    assert "timeline_summary" not in type(entry.consumer_boundary).model_fields
    assert "historical_query" not in type(entry.consumer_boundary).model_fields
