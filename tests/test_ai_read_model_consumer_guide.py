from pathlib import Path


def test_ai_read_model_consumer_guide_covers_usage_and_semantics():
    guide = Path("docs_reference_evidence/04_Evidence_Index/M012_AI_READ_MODEL_CONSUMER_GUIDE.md").read_text(
        encoding="utf-8"
    )

    assert "# M012-02 AI Read Model Consumer Guide" in guide
    assert "identity" in guide
    assert "timing" in guide
    assert "provenance" in guide
    assert "quality" in guide
    assert "history" in guide
    assert "context" in guide
    assert "payload" in guide
    assert "contract_meta" in guide
    assert "`payload` is the data consumer plane." in guide
    assert "`context` is supporting information that points to related surfaces." in guide
    assert "`quality` is trust / freshness / availability information." in guide
    assert "freshness" in guide
    assert "fallback" in guide
    assert "unavailable" in guide
