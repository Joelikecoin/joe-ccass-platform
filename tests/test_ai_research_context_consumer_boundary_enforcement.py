from pathlib import Path

from ccass_core.ai_research_context_entry import build_ai_research_context_consumer_entry

from tests.test_ai_research_context_entry import _assembly


def test_ai_research_context_consumer_usage_contract_requires_approved_boundary():
    contract = Path(
        "codecopy/docs_reference_evidence/04_Evidence_Index/M027_AI_RESEARCH_CONTEXT_CONSUMER_USAGE_CONTRACT.md"
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
    assert set(type(boundary).model_fields).issuperset(
        {
            "approved_surface",
            "current_context",
            "historical_context",
            "consumer_context",
            "quality_summary",
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
    assert "approved_surface=current_context | historical_context | consumer_context | quality_summary" in entry.summary
    assert "AI Research Context Comparison" not in entry.consumer_boundary.summary
    assert "AI Research Context Timeline" not in entry.consumer_boundary.summary
