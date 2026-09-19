from datetime import date, datetime, UTC
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.models import FundamentalRow, FundamentalsMetadata, FundamentalsResponse
from app.sources.fundamentals import (
    HKEXFundamentalsSource,
    _classify_results_document,
    _reporting_period,
    parse_fundamental_pdf,
)
from app.storage.fundamentals import FundamentalsRepository
from app.storage.history import NormalizedSnapshotRepository


def test_labelled_parser_extracts_supported_fields():
    # Representative text is fed through the same deterministic label parser
    # used for official HKEX PDFs; no accounting value is inferred.
    import app.sources.fundamentals as source
    original = source.PdfReader

    class _Page:
        def extract_text(self):
            return "Financial figures are expressed in HKD millions\nRevenue and other income 14,076\nProfit attributable to shareholders 8,519\nCash and cash equivalents 18,470\nTotal equity 58,729\nNet cash inflow from operating activities 14,399"

    class _Reader:
        def __init__(self, _): self.pages = [_Page()]

    source.PdfReader = _Reader
    try:
        row = parse_fundamental_pdf(stock_code="00388", reporting_period="2025-H1", announcement_date=date(2025, 9, 1), report_type="Interim Report", source_url="https://www1.hkexnews.hk/example.pdf", document="example.pdf", payload=b"pdf")
    finally:
        source.PdfReader = original
    assert row.revenue == 14076
    assert row.net_profit_loss == 8519
    assert row.operating_cash_flow == 14399
    assert row.completeness_status == "complete"


def test_fundamentals_repository_is_idempotent(tmp_path: Path):
    row = FundamentalRow(stock_code="00388", reporting_period="2025-H1", announcement_date=date(2025, 9, 1), report_type="Interim Report", revenue=14076, source_document="example.pdf", source_url="https://example.test/example.pdf", retrieval_timestamp=datetime.now(UTC), parser_method="test")
    response = FundamentalsResponse(metadata=FundamentalsMetadata(code="00388", fetched_at=datetime.now(UTC), source_status="ready"), rows=[row])
    repo = FundamentalsRepository(NormalizedSnapshotRepository(tmp_path / "db.sqlite"))
    repo.save(response)
    repo.save(response)
    loaded = repo.load("00388")
    assert loaded is not None and len(loaded.rows) == 1


def test_results_document_classification_prefers_concise_and_excludes_non_financial():
    assert _classify_results_document("2025 Interim Results") == ("Interim", 0)
    assert _classify_results_document("2024 Final Results") == ("Annual", 0)
    assert _classify_results_document("二○二四年度業績") == ("Annual", 0)
    assert _classify_results_document("Annual Report 2024") == ("Annual", 1)
    assert _classify_results_document("2025 Interim Report") == ("Interim", 1)
    assert _classify_results_document("ESG Report 2024") is None
    assert _classify_results_document("Notice of Annual General Meeting") is None
    assert _classify_results_document("Circular re: Placing of Shares") is None
    assert _classify_results_document("Monthly Return") is None


def test_reporting_period_derivation_rules():
    assert _reporting_period(date(2025, 9, 1), "Interim", "2025 Interim Results") == "2025-H1"
    assert _reporting_period(date(2025, 2, 27), "Annual", "2024 Final Results") == "2024-FY"
    assert _reporting_period(date(2025, 2, 27), "Annual", "Annual Results") == "2024-FY"
    assert _reporting_period(date(2026, 8, 15), "Annual", "Annual Results") == "2026-FY"


class _Announcements:
    def __init__(self, rows):
        self.rows = rows

    async def get_announcements(self, code, *, start_date, end_date, row_range):
        return SimpleNamespace(announcements=self.rows)


def _announcement(title, year, month, day, link="https://www1.hkexnews.hk/x.pdf"):
    return SimpleNamespace(title=title, link=link, announcement_date=date(year, month, day))


class _Response:
    def __init__(self, content):
        self.content = content

    def raise_for_status(self):
        pass


class _Client:
    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    async def get(self, url, **kwargs):
        return _Response(b"pdf")


def _with_stub_pdf_reader(monkeypatch):
    import app.sources.fundamentals as source
    original = source.PdfReader

    class _Page:
        def extract_text(self):
            return "Revenue and other income 14,076\nTotal equity 58,729"

    class _Reader:
        def __init__(self, _):
            self.pages = [_Page()]

    monkeypatch.setattr(source, "PdfReader", _Reader)


@pytest.mark.asyncio
async def test_fundamentals_source_discovers_results_documents_dynamically(monkeypatch):
    _with_stub_pdf_reader(monkeypatch)
    announcements = _Announcements([
        _announcement("2025 Interim Results", 2025, 8, 20),
        _announcement("ESG Report 2025", 2025, 7, 1),
        _announcement("Notice of Annual General Meeting", 2025, 4, 1),
        _announcement("2024 Final Results", 2025, 2, 27),
        _announcement("Monthly Return", 2025, 1, 5),
    ])
    source = HKEXFundamentalsSource(client=_Client(), announcements=announcements)
    response = await source.get_fundamentals("02318")

    assert response.metadata.source_status == "ready"
    assert response.metadata.documents_attempted == 2
    assert response.metadata.documents_parsed == 2
    periods = [row.reporting_period for row in response.rows]
    assert periods == ["2025-H1", "2024-FY"]
    assert response.data_quality_warnings == []


@pytest.mark.asyncio
async def test_fundamentals_source_caps_discovered_periods_and_warns(monkeypatch):
    _with_stub_pdf_reader(monkeypatch)
    rows = [_announcement(f"{2025 - i} Final Results", 2025 - i, 2, 20) for i in range(6)]
    source = HKEXFundamentalsSource(client=_Client(), announcements=_Announcements(rows))
    response = await source.get_fundamentals("02318")

    assert response.metadata.source_status == "ready"
    assert response.metadata.documents_attempted == 4
    assert any(w.startswith("DISCOVERY_CAPPED") for w in response.data_quality_warnings)
    assert response.rows[0].reporting_period == "2025-FY"


@pytest.mark.asyncio
async def test_fundamentals_source_reports_missing_discovery_fail_loud(monkeypatch):
    _with_stub_pdf_reader(monkeypatch)
    source = HKEXFundamentalsSource(client=_Client(), announcements=_Announcements([_announcement("Monthly Return", 2026, 1, 5)]))
    response = await source.get_fundamentals("00941")

    assert response.metadata.source_status == "unavailable"
    assert response.metadata.documents_attempted == 0
    assert any(w.startswith("NO_RESULTS_DOCUMENTS_DISCOVERED") for w in response.data_quality_warnings)
