from datetime import date, datetime, UTC

from app.sources.document_entities import HKEXDocumentSpec, _extract_rows


def test_document_entity_extraction_keeps_direct_fact_only():
    spec = HKEXDocumentSpec("00006", "x", "major transaction circular", date(2026, 4, 8), "https://example.test/x.pdf")
    rows = _extract_rows(spec, "Platinum Securities Company Limited has been engaged to act as the independent financial adviser to the Independent Board Committee.", datetime.now(UTC))
    assert any(row.entity_type == "independent_financial_adviser" for row in rows)
    assert rows[0].derived_classification is None
