from __future__ import annotations

import io
import re
from datetime import UTC, date, datetime

import httpx
from pypdf import PdfReader

from app.models import FundamentalRow, FundamentalsMetadata, FundamentalsResponse


HKEX_FUNDAMENTAL_DOCUMENTS = {
    "00388": (
        ("2025-H1", "2025-09-01", "Interim Report", "https://www1.hkexnews.hk/listedco/listconews/sehk/2025/0901/2025090100701.pdf"),
        ("2024-FY", "2025-02-27", "Final Results", "https://www1.hkexnews.hk/listedco/listconews/sehk/2025/0227/2025022700759.pdf"),
        ("2025-FY", "2026-02-26", "Final Results", "https://www1.hkexnews.hk/listedco/listconews/sehk/2026/0226/2026022600690.pdf"),
    ),
    "00006": (("2025-H1", "2025-09-01", "Interim Report", "https://www1.hkexnews.hk/listedco/listconews/sehk/2025/0901/2025090101139.pdf"),),
}


def _first_number(text: str, labels: tuple[str, ...]) -> float | None:
    candidates: list[float] = []
    for label in labels:
        matches = re.finditer(rf"{re.escape(label)}(?:(?:\s|\n|\u00a0|:)+|\([^)]*\))*([\(\-]?\d[\d,]*(?:\.\d+)?\)?)", text, re.I)
        for match in matches:
            token = match.group(1).replace(",", "").replace("(", "-").replace(")", "")
            try:
                value = float(token)
                if abs(value) >= 10:
                    candidates.append(value)
            except ValueError:
                continue
    return max(candidates, key=abs) if candidates else None


def parse_fundamental_pdf(*, stock_code: str, reporting_period: str, announcement_date: date, report_type: str, source_url: str, document: str, payload: bytes, retrieved_at: datetime | None = None) -> FundamentalRow:
    text = "\n".join(page.extract_text() or "" for page in PdfReader(io.BytesIO(payload)).pages)
    currency = "HKD" if re.search(r"expressed in HKD|\$m", text, re.I) else None
    unit = "million" if re.search(r"\$m|HKD million|in millions", text, re.I) else None
    values = {
        "revenue": _first_number(text, ("Revenue and other income", "Total revenue and other income", "Revenue")),
        "net_profit_loss": _first_number(text, ("Profit attributable to shareholders", "Profit/(loss) for the period", "Profit for the year")),
        "cash": _first_number(text, ("Cash and cash equivalents",)),
        "debt": _first_number(text, ("Borrowings", "Total borrowings")),
        "net_assets": _first_number(text, ("Net assets",)),
        "equity": _first_number(text, ("Total equity", "Equity attributable to shareholders")),
        "operating_cash_flow": _first_number(text, ("Net cash inflow from operating activities", "Net cash generated from operating activities")),
        "shares_outstanding": _first_number(text, ("Number of shares in issue", "Shares in issue", "issued shares")),
    }
    present = sum(value is not None for value in values.values())
    return FundamentalRow(
        stock_code=stock_code,
        reporting_period=reporting_period,
        announcement_date=announcement_date,
        report_type=report_type,
        source_document=document,
        source_url=source_url,
        retrieval_timestamp=retrieved_at or datetime.now(UTC),
        parser_method="pypdf-labelled-financial-statement-v1",
        completeness_status="complete" if present >= 4 else "partial",
        currency=currency,
        unit=unit,
        **values,
    )


class HKEXFundamentalsSource:
    source_name = "HKEXnews Listed Company Information"

    def __init__(self, timeout: float = 45.0, client: httpx.AsyncClient | None = None):
        self.timeout = timeout
        self.client = client

    async def get_fundamentals(self, code: str | int) -> FundamentalsResponse:
        normalized = str(code).zfill(5)
        docs = HKEX_FUNDAMENTAL_DOCUMENTS.get(normalized, ())
        now = datetime.now(UTC)
        rows: list[FundamentalRow] = []
        warnings: list[str] = []
        async with (self.client or httpx.AsyncClient(timeout=self.timeout, follow_redirects=True)) as client:
            for period, ann, report_type, url in docs:
                try:
                    response = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
                    response.raise_for_status()
                    rows.append(parse_fundamental_pdf(stock_code=normalized, reporting_period=period, announcement_date=date.fromisoformat(ann), report_type=report_type, source_url=url, document=url.rsplit("/", 1)[-1], payload=response.content, retrieved_at=now))
                except Exception as exc:
                    warnings.append(f"DOCUMENT_FAILED:{url.rsplit('/', 1)[-1]}:{type(exc).__name__}")
        status = "ready" if rows and not warnings else ("partial" if rows else "unavailable")
        return FundamentalsResponse(metadata=FundamentalsMetadata(code=normalized, fetched_at=now, source_status=status, documents_attempted=len(docs), documents_fetched=len(rows), documents_parsed=len(rows), documents_failed=len(warnings)), rows=rows, data_quality_warnings=warnings)
