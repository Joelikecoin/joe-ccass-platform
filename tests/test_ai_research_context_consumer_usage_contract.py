from pathlib import Path


def test_ai_research_context_consumer_usage_contract_defines_approved_entry_point():
    contract = Path(
        "docs_reference_evidence/04_Evidence_Index/M027_AI_RESEARCH_CONTEXT_CONSUMER_USAGE_CONTRACT.md"
    ).read_text(encoding="utf-8")

    assert "# M027-01 AI Research Context Consumer Usage Contract" in contract
    assert "Approved Consumer Entry Point" in contract
    assert "AIResearchContextConsumerEntry" in contract
    assert "AIResearchContextConsumerBoundary" in contract
    assert "AIResearchContextDelivery" in contract
    assert "AIResearchContextHistoricalDelivery" in contract
    assert "AIResearchContextQualitySummary" in contract


def test_ai_research_context_consumer_usage_contract_defines_allowed_and_prohibited_dependencies():
    contract = Path(
        "docs_reference_evidence/04_Evidence_Index/M027_AI_RESEARCH_CONTEXT_CONSUMER_USAGE_CONTRACT.md"
    ).read_text(encoding="utf-8")

    assert "Allowed Consumer Dependencies" in contract
    assert "Prohibited Direct Domain Access" in contract
    assert "comparison" in contract
    assert "change_summary" in contract
    assert "timeline" in contract
    assert "historical_query" in contract
    assert "historical_comparison_query" in contract
    assert "historical_summary" in contract
    assert "recreate the domain layers" not in contract.lower()
    assert "analysis logic" in contract.lower()
    assert "no new source" in contract.lower()
