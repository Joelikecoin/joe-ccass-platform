from __future__ import annotations

import io
import re
from datetime import UTC, date, datetime, timedelta

import httpx
from pypdf import PdfReader

from app.models import FundamentalRow, FundamentalsMetadata, FundamentalsResponse
from app.sources.announcements import HKEXNewsAnnouncementsSource

# Discovery is dynamic: results/annual documents are found per stock from the
# HKEXnews announcement stream at runtime — no per-stock URL whitelist.
MAX_DISCOVERY_WINDOW_DAYS = 2 * 365
MAX_PERIODS_PER_RUN = 4
MAX_DOCUMENT_ATTEMPTS_PER_RUN = 6
MAX_PDF_BYTES = 25 * 1024 * 1024

INTERIM_TITLE_RE = re.compile(r"interim|中期|half[- ]year", re.IGNORECASE)
ANNUAL_TITLE_RE = re.compile(r"annual report|年度報告|年報|final results|全年業績|年度業績|annual results", re.IGNORECASE)
NON_FINANCIAL_TITLE_RE = re.compile(r"esg|sustainab|可持續|governance|circular|通函|AGM|SGM|notice of|proxy", re.IGNORECASE)
OVERSEAS_TITLE_RE = re.compile(r"overseas regulatory", re.IGNORECASE)
YEAR_RE = re.compile(r"20\d{2}")
# Labels may be followed by bound qualifier words ("… shareholders OF THE PARENT COMPANY  43,656")
# before the figure; the qualifier set is closed to keep the jump bounded.
LABEL_QUALIFIER_RE = r"(?:(?:\s|\u00a0)+|\([^)]*\)|\b(?:of|the|to|for|and|in|from|parent|company|owners|group|period|year|issued|activities)\b)*"

VALUE_FIELDS = ("revenue", "net_profit_loss", "cash", "debt", "net_assets", "equity", "operating_cash_flow", "shares_outstanding")


def _classify_results_document(title: str) -> tuple[str, int] | None:
    """Return (kind, rank) for a reporting document title, else None.

    rank 0 = concise results announcement (parses cleanly), rank 1 = full report,
    rank 2 = overseas-regulatory republication (narrative, parsed last).
    """
    if NON_FINANCIAL_TITLE_RE.search(title):
        return None
    lowered = title.lower()
    if OVERSEAS_TITLE_RE.search(lowered):
        concise = 2
    elif "results" in lowered or "業績" in title:
        concise = 0
    else:
        concise = 1
    if ANNUAL_TITLE_RE.search(title):
        return "Annual", concise
    if INTERIM_TITLE_RE.search(title):
        return "Interim", concise
    return None


def _reporting_period(announcement_date: date, kind: str, title: str) -> str:
    # Title years are only trusted when they sit next to the announcement year;
    # otherwise stray references (bond names, restatements) hijack the period.
    years = [int(year) for year in YEAR_RE.findall(title)]
    trusted = [year for year in years if announcement_date.year - 1 <= year <= announcement_date.year]
    if kind == "Interim":
        return f"{trusted[0] if trusted else announcement_date.year}-H1"
    if trusted:
        return f"{trusted[-1]}-FY"
    return f"{announcement_date.year - 1 if announcement_date.month <= 6 else announcement_date.year}-FY"


def _first_number(text: str, labels: tuple[str, ...]) -> float | None:
    candidates: list[float] = []
    for label in labels:
        matches = re.finditer(rf"{re.escape(label)}{LABEL_QUALIFIER_RE}((?:\(|\-)?\d[\d,]*(?:\.\d+)?\)?)", text, re.I)
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
    currency = "HKD" if re.search(r"expressed in HKD|\$m|RMB", text, re.I) else None
    unit = "million" if re.search(r"\$m|HKD million|in millions|RMB million|bn\b", text, re.I) else None
    values = {
        "revenue": _first_number(text, ("Total operating income", "Revenue and other income", "Total revenue and other income", "Total revenue", "Operating income", "Revenue")),
        "net_profit_loss": _first_number(text, ("Profit attributable to shareholders of the parent company", "Profit attributable to owners of the parent", "Net profit attributable to shareholders", "Profit attributable to shareholders", "Profit/(loss) for the period", "Profit for the year", "Profit for the period")),
        "cash": _first_number(text, ("Cash and cash equivalents",)),
        "debt": _first_number(text, ("Total borrowings", "Borrowings", "Total debt")),
        "net_assets": _first_number(text, ("Net assets",)),
        "equity": _first_number(text, ("Total equity attributable to owners of the parent", "Equity attributable to shareholders of the parent company", "Equity attributable to shareholders", "Total equity")),
        "operating_cash_flow": _first_number(text, ("Net cash generated from operating activities", "Net cash inflow from operating activities", "Net cash from operating activities")),
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
        parser_method="pypdf-labelled-financial-statement-v2",
        completeness_status="complete" if present >= 4 else "partial",
        currency=currency,
        unit=unit,
        **values,
    )


class HKEXFundamentalsSource:
    source_name = "HKEXnews Listed Company Information"

    def __init__(self, timeout: float = 45.0, client: httpx.AsyncClient | None = None, announcements: HKEXNewsAnnouncementsSource | None = None):
        self.timeout = timeout
        self.client = client
        self.announcements = announcements or HKEXNewsAnnouncementsSource()

    async def get_fundamentals(self, code: str | int) -> FundamentalsResponse:
        normalized = str(code).zfill(5)
        now = datetime.now(UTC)
        warnings: list[str] = []
        try:
            discovered, discovery_warnings = await self._discover_results_documents(normalized)
        except Exception as exc:
            warnings.append(f"DISCOVERY_FAILED:{type(exc).__name__}")
            return FundamentalsResponse(metadata=FundamentalsMetadata(code=normalized, fetched_at=now, source_status="unavailable", documents_attempted=0, documents_fetched=0, documents_parsed=0, documents_failed=0), rows=[], data_quality_warnings=warnings)
        warnings.extend(discovery_warnings)
        rows: list[FundamentalRow] = []
        failed = 0
        attempts = 0
        async with (self.client or httpx.AsyncClient(timeout=self.timeout, follow_redirects=True)) as client:
            for period, candidates in discovered:
                best_row: FundamentalRow | None = None
                best_fields = 0
                for report_type, announcement_date, url in candidates:
                    if attempts >= MAX_DOCUMENT_ATTEMPTS_PER_RUN and best_row is not None:
                        break
                    if attempts >= MAX_DOCUMENT_ATTEMPTS_PER_RUN:
                        warnings.append("ATTEMPT_BUDGET_REACHED: document attempt budget exhausted before this period")
                        break
                    attempts += 1
                    try:
                        response = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
                        response.raise_for_status()
                        if len(response.content) > MAX_PDF_BYTES:
                            warnings.append(f"DOCUMENT_TOO_LARGE:{url.rsplit('/', 1)[-1]}:{len(response.content)}")
                            failed += 1
                            continue
                        parsed_row = parse_fundamental_pdf(stock_code=normalized, reporting_period=period, announcement_date=announcement_date, report_type=report_type, source_url=url, document=url.rsplit("/", 1)[-1], payload=response.content, retrieved_at=now)
                        present = sum(parsed_row.model_dump().get(field) is not None for field in VALUE_FIELDS)
                        if present < 2:
                            warnings.append(f"LABELS_NOT_MATCHED:{url.rsplit('/', 1)[-1]}:{present}")
                        if present > best_fields or best_row is None:
                            best_row = parsed_row
                            best_fields = present
                        if best_fields >= 2:
                            break
                    except Exception as exc:
                        warnings.append(f"DOCUMENT_FAILED:{url.rsplit('/', 1)[-1]}:{type(exc).__name__}")
                        failed += 1
                if best_row is not None:
                    rows.append(best_row)
        if rows and not failed:
            status = "ready"
        elif rows:
            status = "partial"
        else:
            status = "unavailable"
        return FundamentalsResponse(metadata=FundamentalsMetadata(code=normalized, fetched_at=now, source_status=status, documents_attempted=attempts, documents_fetched=len(rows), documents_parsed=len(rows), documents_failed=failed), rows=rows, data_quality_warnings=warnings)

    async def _discover_results_documents(self, code: str) -> tuple[list[tuple[str, list[tuple[str, date, str]]]], list[str]]:
        """Find reporting-period PDF candidates for any stock from its announcement stream.

        Each period carries ranked backup documents (results announcement first,
        then the full report, then overseas-regulatory republications): some
        issuers publish cover-only PDFs, so the fetch loop walks candidates
        until one yields real figures.
        """
        warnings: list[str] = []
        end = datetime.now(UTC).date()
        start = end - timedelta(days=MAX_DISCOVERY_WINDOW_DAYS)
        announcements = await self.announcements.get_announcements(code, start_date=start, end_date=end, row_range=400)
        per_period: dict[str, list[tuple[int, date, str, str]]] = {}
        for row in announcements.announcements:
            title = (row.title or "").strip()
            if not title or not row.link:
                continue
            classified = _classify_results_document(title)
            if classified is None:
                continue
            kind, rank = classified
            period = _reporting_period(row.announcement_date, kind, title)
            report_type = f"{kind} Results" if rank == 0 else f"{kind} Report"
            per_period.setdefault(period, []).append((rank, row.announcement_date, report_type, row.link))
        if not per_period:
            warnings.append("NO_RESULTS_DOCUMENTS_DISCOVERED: no interim/annual results announcements found in the discovery window")
            return [], warnings
        ordered = sorted(per_period.items(), key=lambda item: (min(c[0] for c in item[1]), max(c[1] for c in item[1])), reverse=True)
        if len(ordered) > MAX_PERIODS_PER_RUN:
            warnings.append(f"DISCOVERY_CAPPED: parsing latest {MAX_PERIODS_PER_RUN} of {len(ordered)} discovered reporting periods (capacity discipline; heavy pulls move to the async pattern)")
            ordered = ordered[:MAX_PERIODS_PER_RUN]
        plan: list[tuple[str, list[tuple[str, date, str]]]] = []
        for period, candidates in ordered:
            ranked = sorted(candidates, key=lambda c: (c[0], c[1]), reverse=True)
            plan.append((period, [(report_type, announcement_date, url) for _rank, announcement_date, report_type, url in ranked]))
        return plan, warnings
