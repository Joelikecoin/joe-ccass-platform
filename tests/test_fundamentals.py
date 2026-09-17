from datetime import date, datetime, UTC
from pathlib import Path

from app.models import FundamentalRow, FundamentalsMetadata, FundamentalsResponse
from app.sources.fundamentals import parse_fundamental_pdf
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
