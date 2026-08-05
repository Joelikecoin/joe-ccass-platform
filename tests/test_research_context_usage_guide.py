from pathlib import Path


def test_research_context_usage_guide_covers_package_and_boundaries():
    guide = Path("docs_reference_evidence/M013_RESEARCH_CONTEXT_USAGE_GUIDE.md").read_text(encoding="utf-8")

    assert "ResearchContextPackage" in guide
    assert "identity" in guide
    assert "ownership_context" in guide
    assert "market_context" in guide
    assert "company_context" in guide
    assert "historical_context" in guide
    assert "quality_context" in guide
    assert "contract_meta" in guide
    assert "no investment logic" in guide
    assert "no trading signal" in guide
    assert "no recommendation" in guide


def test_research_context_usage_guide_explains_usage_and_limitations():
    guide = Path("docs_reference_evidence/M013_RESEARCH_CONTEXT_USAGE_GUIDE.md").read_text(encoding="utf-8")

    assert "organize existing platform data" in guide
    assert "consumer-friendly context" in guide
    assert "future AI consumption" in guide
    assert "not an investment conclusion" in guide
    assert "not a decision engine" in guide
    assert "not an AI analysis layer" in guide
    assert "does not imply trend prediction" in guide
    assert "does not assign a company quality rating" in guide
    assert "does not re-define M007 historical analysis scope" in guide
