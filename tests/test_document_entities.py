from datetime import date, datetime, UTC

from app.sources.document_entities import HKEXDocumentSpec, _extract_rows


def test_document_entity_extraction_keeps_direct_fact_only():
    spec = HKEXDocumentSpec("00006", "x", "major transaction circular", date(2026, 4, 8), "https://example.test/x.pdf")
    rows = _extract_rows(spec, "Platinum Securities Company Limited has been engaged to act as the independent financial adviser to the Independent Board Committee.", datetime.now(UTC))
    assert any(row.entity_type == "independent_financial_adviser" for row in rows)
    assert rows[0].derived_classification is None


def test_document_entity_extraction_qualifies_offer_roles():
    spec = HKEXDocumentSpec("00372", "offer", "offer document", date(2025, 4, 24), "https://example.test/offer.pdf")
    rows = _extract_rows(
        spec,
        '“Offeror” Marching Great Limited. The Offeror and the Offeror’s Concert Parties hold the shares.',
        datetime.now(UTC),
    )
    assert any(row.entity_type == "offeror" and row.entity_name == "Marching Great Limited" for row in rows)
    assert any(row.entity_type == "concert_party" for row in rows)


def test_document_entity_extraction_qualifies_placing_and_underwriter():
    spec = HKEXDocumentSpec("00362", "placing", "placing circular", date(2024, 10, 25), "https://example.test/placing.pdf")
    rows = _extract_rows(
        spec,
        'entered into the placing agreement with Leeds Securities Investment Limited (the “New Placing Agent”). First Underwriter: Koala Securities Limited.',
        datetime.now(UTC),
    )
    assert ("placing_agent", "Leeds Securities Investment Limited") in {(row.entity_type, row.entity_name) for row in rows}
    assert ("underwriter", "Koala Securities Limited") in {(row.entity_type, row.entity_name) for row in rows}
