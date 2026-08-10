from pathlib import Path

from ccass_core.ai_research_context_entry import build_ai_research_context_consumer_entry
from ccass_core.ai_research_context_consumer_capability_validation import (
    build_ai_research_context_consumer_capability_validation,
)
from ccass_core.ai_research_context_consumer_governance_validation import (
    build_ai_research_context_consumer_governance_validation,
)
from ccass_core.ai_research_context_consumer_readiness import (
    build_ai_research_context_consumer_readiness_status,
)

from tests.test_ai_research_context_entry import _assembly


def test_ai_research_context_consumer_usage_contract_requires_approved_boundary():
    contract = (
        Path(__file__).resolve().parents[1]
        / "docs_reference_evidence/04_Evidence_Index/M027_AI_RESEARCH_CONTEXT_CONSUMER_USAGE_CONTRACT.md"
    ).read_text(encoding="utf-8")

    assert "Approved Consumer Entry Point" in contract
    assert "AIResearchContextConsumerEntry" in contract
    assert "AIResearchContextConsumerBoundary" in contract
    assert "AIResearchContextDelivery" in contract
    assert "AIResearchContextHistoricalDelivery" in contract
    assert "AIResearchContextQualitySummary" in contract
    assert "Prohibited Direct Domain Access" in contract
    assert "comparison" in contract
    assert "change_summary" in contract
    assert "timeline" in contract
    assert "historical_query" in contract
    assert "historical_comparison_query" in contract
    assert "historical_summary" in contract
    assert "no analysis logic" in contract.lower()


def test_ai_research_context_consumer_boundary_only_exposes_approved_consumer_surface(
    current_response, previous_response
):
    entry = build_ai_research_context_consumer_entry(_assembly(current_response, previous_response))
    boundary = entry.consumer_boundary

    assert boundary is not None
    assert boundary.approved_surface == (
        "current_context",
        "historical_context",
        "consumer_context",
        "quality_summary",
    )
    assert boundary.current_context is entry.delivery
    assert boundary.historical_context is entry.historical_delivery
    assert boundary.consumer_context is entry.consumer_context
    assert boundary.quality_summary is entry.quality_summary
    assert boundary.surface_version_reference == boundary.contract_meta.version
    assert boundary.compatibility_metadata is not None
    assert boundary.compatibility_metadata.supported_surface == boundary.approved_surface
    assert boundary.compatibility_metadata.compatibility_reference
    assert boundary.capability_metadata is not None
    assert boundary.capability_metadata.supported_surface == boundary.approved_surface
    assert boundary.capability_metadata.capability_reference
    assert boundary.capability_validation is not None
    assert boundary.capability_validation.capability_consistent is True
    assert boundary.capability_validation.validation_state == "consistent"
    assert boundary.capability_validation.missing_capability_references == []
    assert boundary.readiness_status is not None
    assert boundary.readiness_status.readiness_status == "ready"
    assert boundary.readiness_status.readiness_visible is True
    assert boundary.readiness_status.readiness_reference
    assert boundary.health_indicator is not None
    assert boundary.health_indicator.health_status == "healthy"
    assert boundary.health_indicator.health_visible is True
    assert boundary.health_indicator.health_reference
    assert boundary.governance_summary is not None
    assert boundary.governance_summary.governance_status == "complete"
    assert boundary.governance_summary.governance_visible is True
    assert boundary.governance_summary.governance_reference
    assert boundary.governance_status is not None
    assert boundary.governance_status.governance_status == "complete"
    assert boundary.governance_status.governance_visible is True
    assert boundary.governance_status.governance_reference
    assert boundary.governance_validation is not None
    assert boundary.governance_validation.governance_consistent is True
    assert boundary.governance_validation.validation_state == "consistent"
    assert boundary.governance_validation.governance_visible is True
    assert boundary.governance_validation.validation_reference
    assert set(type(boundary).model_fields).issuperset(
        {
            "approved_surface",
            "current_context",
            "historical_context",
            "consumer_context",
            "quality_summary",
            "surface_version_reference",
            "compatibility_metadata",
            "capability_metadata",
            "capability_validation",
            "readiness_status",
            "health_indicator",
            "governance_summary",
            "governance_status",
            "governance_validation",
        }
    )
    assert "comparison" not in type(boundary).model_fields
    assert "change_summary" not in type(boundary).model_fields
    assert "timeline" not in type(boundary).model_fields
    assert "timeline_summary" not in type(boundary).model_fields
    assert "historical_query" not in type(boundary).model_fields
    assert "historical_comparison_query" not in type(boundary).model_fields
    assert "historical_summary" not in type(boundary).model_fields


def test_ai_research_context_consumer_entry_preserves_composition_rule(
    current_response, previous_response
):
    entry = build_ai_research_context_consumer_entry(_assembly(current_response, previous_response))

    assert entry.available is True
    assert entry.consumer_boundary is not None
    assert entry.consumer_boundary.available is True
    assert entry.consumer_boundary.consumer_context is entry.consumer_context
    assert entry.consumer_boundary.current_context is entry.delivery
    assert entry.consumer_boundary.historical_context is entry.historical_delivery
    assert "AI research context consumer boundary:" in entry.summary
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
    assert "approved_surface=current_context | historical_context | consumer_context | quality_summary" in entry.summary
    assert "AI Research Context Comparison" not in entry.consumer_boundary.summary
    assert "AI Research Context Timeline" not in entry.consumer_boundary.summary


def test_ai_research_context_consumer_capability_validation_detects_missing_references():
    validation = build_ai_research_context_consumer_capability_validation(
        surface_version_reference="v0.1",
        approved_surface=(
            "current_context",
            "historical_context",
            "consumer_context",
            "quality_summary",
        ),
        capability_supported_surface=("current_context",),
        compatibility_supported_surface=("current_context", "historical_context"),
        capability_reference="",
        compatibility_reference="",
        consumer_surface_declaration="",
    )

    assert validation.available is True
    assert validation.capability_consistent is False
    assert validation.validation_state == "inconsistent"
    assert "capability_reference" in validation.missing_capability_references
    assert "compatibility_reference" in validation.missing_capability_references
    assert "consumer_surface_declaration" in validation.missing_capability_references
    assert validation.consistency_warnings


def test_ai_research_context_consumer_readiness_status_marks_unavailable_when_boundary_is_unavailable():
    readiness = build_ai_research_context_consumer_readiness_status(
        available=False,
        consumer_ready=False,
        capability_validation=None,
        capability_reference="not available",
        compatibility_reference="not available",
        consumer_surface_declaration="not available",
        surface_version_reference="v0.1",
    )

    assert readiness.available is False
    assert readiness.readiness_status == "unavailable"
    assert readiness.readiness_visible is False
    assert readiness.readiness_reference == "not available"


def test_ai_research_context_consumer_health_indicator_marks_unavailable_when_boundary_is_unavailable():
    entry = build_ai_research_context_consumer_entry(None)
    health = entry.consumer_boundary.health_indicator

    assert health is not None
    assert health.available is False
    assert health.health_status == "unavailable"
    assert health.health_visible is False
    assert health.health_reference == "not available"


def test_ai_research_context_consumer_governance_summary_marks_unavailable_when_boundary_is_unavailable():
    entry = build_ai_research_context_consumer_entry(None)
    governance = entry.consumer_boundary.governance_summary

    assert governance is not None
    assert governance.available is False
    assert governance.governance_status == "unavailable"
    assert governance.governance_visible is False
    assert governance.governance_reference == "not available"


def test_ai_research_context_consumer_governance_status_marks_unavailable_when_boundary_is_unavailable():
    entry = build_ai_research_context_consumer_entry(None)
    governance_status = entry.consumer_boundary.governance_status

    assert governance_status is not None
    assert governance_status.available is False
    assert governance_status.governance_status == "unavailable"
    assert governance_status.governance_visible is False
    assert governance_status.governance_reference == "not available"


def test_ai_research_context_consumer_governance_validation_marks_unavailable_when_boundary_is_unavailable():
    entry = build_ai_research_context_consumer_entry(None)
    governance_validation = entry.consumer_boundary.governance_validation

    assert governance_validation is not None
    assert governance_validation.available is False
    assert governance_validation.validation_state == "unknown"
    assert governance_validation.governance_visible is False
    assert governance_validation.validation_reference == "not available"


def test_ai_research_context_consumer_governance_validation_detects_inconsistent_summary_references(
    current_response, previous_response
):
    entry = build_ai_research_context_consumer_entry(_assembly(current_response, previous_response))
    boundary = entry.consumer_boundary
    governance_summary = boundary.governance_summary.model_copy(
        update={
            "version_reference": "wrong-version",
            "compatibility_reference": "wrong-compatibility",
            "capability_reference": "wrong-capability",
            "validation_reference": "wrong-validation",
            "readiness_reference": "wrong-readiness",
            "health_reference": "wrong-health",
        }
    )

    validation = build_ai_research_context_consumer_governance_validation(
        available=True,
        governance_summary=governance_summary,
        version_reference=boundary.surface_version_reference,
        compatibility_reference=boundary.compatibility_metadata.compatibility_reference,
        capability_reference=boundary.capability_metadata.capability_reference,
        capability_validation=boundary.capability_validation,
        readiness_status=boundary.readiness_status,
        health_indicator=boundary.health_indicator,
    )

    assert validation.available is True
    assert validation.governance_consistent is False
    assert validation.validation_state == "inconsistent"
    assert validation.consistency_warnings
