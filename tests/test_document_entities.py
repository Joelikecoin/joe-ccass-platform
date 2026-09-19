from datetime import date, datetime, UTC

import pytest

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


def test_entity_document_title_classification():
    from app.sources.document_entities import _classify_entity_document

    assert _classify_entity_document("Completion of Placing of Shares under General Mandate") == "placing"
    assert _classify_entity_document("Voluntary General Offer - Response Document") == "general offer"
    assert _classify_entity_document("Circular relating to Whitewash Waiver") == "whitewash"
    assert _classify_entity_document("Rights Issue Circular") == "rights issue"
    assert _classify_entity_document("2025 Interim Results") is None
    assert _classify_entity_document("Monthly Return") is None
    assert _classify_entity_document("ESG Report") is None


@pytest.mark.asyncio
async def test_document_entities_source_discovers_and_extracts(monkeypatch):
    from types import SimpleNamespace
    from app.sources.document_entities import HKEXDocumentEntitiesSource
    from app.sources.announcements import HKEXNewsAnnouncementsSource

    rows = [
        SimpleNamespace(title="Completion of Placing of Shares", link="https://www1.hkexnews.hk/listedco/listconews/sehk/2026/0801/2026080100042.pdf", announcement_date=date(2026, 8, 1)),
        SimpleNamespace(title="2025 Interim Results", link="https://www1.hkexnews.hk/listedco/listconews/sehk/2026/0819/2026081900099.pdf", announcement_date=date(2026, 8, 19)),
    ]

    class _FakeAnnouncements(HKEXNewsAnnouncementsSource):
        async def get_announcements(self, code, *, start_date, end_date, row_range):
            return SimpleNamespace(announcements=rows)

    class _Page:
        def extract_text(self):
            return "entered into the placing agreement with Leeds Securities Investment Limited (the Placing Agent)."

    class _Reader:
        def __init__(self, _):
            self.pages = [_Page()]

    import app.sources.document_entities as source
    monkeypatch.setattr(source, "PdfReader", _Reader)

    class _Response:
        content = b"pdf"

        def raise_for_status(self):
            pass

    class _Client:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

        async def get(self, url, **kwargs):
            return _Response()

    src = HKEXDocumentEntitiesSource(client=_Client(), announcements=_FakeAnnouncements())
    response = await src.get_entities("02318")

    assert response.metadata.source_status == "ready"
    assert response.metadata.documents_attempted == 1
    assert response.metadata.rows_extracted >= 1
    assert any(row.entity_type == "placing_agent" for row in response.rows)
    assert all(row.document_type == "placing document" for row in response.rows)


@pytest.mark.asyncio
async def test_document_entities_source_reports_missing_discovery_fail_loud():
    from types import SimpleNamespace
    from app.sources.document_entities import HKEXDocumentEntitiesSource
    from app.sources.announcements import HKEXNewsAnnouncementsSource

    class _FakeAnnouncements(HKEXNewsAnnouncementsSource):
        async def get_announcements(self, code, *, start_date, end_date, row_range):
            return SimpleNamespace(announcements=[SimpleNamespace(title="Monthly Return", link="https://x.test/a.pdf", announcement_date=date(2026, 1, 5))])

    src = HKEXDocumentEntitiesSource(announcements=_FakeAnnouncements())
    response = await src.get_entities("00941")

    assert response.metadata.source_status == "unavailable"
    assert any(w.startswith("NO_ENTITY_DOCUMENTS_DISCOVERED") for w in response.data_quality_warnings)
