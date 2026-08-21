from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import Protocol
from urllib.parse import parse_qs, urljoin, urlparse

from bs4 import BeautifulSoup, Tag

from app.config import Settings, get_settings
from app.data_quality import structured_warning
from app.errors import ErrorCode, PlatformError
from app.models import StockEventRow, StockEventsMetadata, StockEventsResponse
from app.sources.webbsite import FetchedPage, WebbsiteClient
from ccass_core.normalize import normalize_stock_code

STOCK_EVENTS_SOURCE_NAME = "Webb-site Events"
STOCK_EVENTS_SOURCE_PENDING_NAME = STOCK_EVENTS_SOURCE_NAME
STOCK_EVENTS_SOURCE_PENDING_URL: str | None = "https://webbsite.0xmd.com/dbpub/events.asp"


class StockEventsSource(Protocol):
    async def get_stock_events(self, code: str | int) -> StockEventsResponse: ...


class PendingStockEventsSource:
    async def get_stock_events(self, code: str | int) -> StockEventsResponse:
        normalized = normalize_stock_code(code)
        return StockEventsResponse(
            metadata=StockEventsMetadata(
                code=normalized,
                source_name=STOCK_EVENTS_SOURCE_PENDING_NAME,
                source_url=STOCK_EVENTS_SOURCE_PENDING_URL,
                fetched_at=datetime.now(UTC),
                data_as_of=None,
                stock_events_count=0,
                source_status="pending",
            ),
            stock_events=[],
            data_quality_warnings=[
                structured_warning(
                    "SOURCE_STATUS",
                    "STOCK_EVENTS_SOURCE_PENDING",
                    "Stock events source is pending approval; placeholder read path only.",
                )
            ],
        )


@dataclass(frozen=True, slots=True)
class ParsedStockEventsPage:
    events: tuple[StockEventRow, ...]
    warnings: tuple[str, ...]


class WebbsiteStockEventsSource:
    def __init__(
        self,
        settings: Settings | None = None,
        *,
        client: WebbsiteClient | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.client = client or WebbsiteClient(self.settings)

    async def get_stock_events(self, code: str | int) -> StockEventsResponse:
        normalized = normalize_stock_code(code)
        issue_id: int | None = None
        company_name: str | None = None
        source_url: str | None = None
        try:
            issue_id, company_name = await self.client.resolve_issue_id(normalized)
            source_url = self._build_source_url(issue_id)
            page = await self.client.get_stock_events_page(issue_id)
            parsed = self._parse_page(page, source_url=page.source_url)
            events = sorted(
                parsed.events,
                key=lambda item: (item.event_date, item.title),
                reverse=True,
            )
            warnings = list(dict.fromkeys(parsed.warnings))
            return StockEventsResponse(
                metadata=StockEventsMetadata(
                    code=normalized,
                    name=company_name,
                    source_name=STOCK_EVENTS_SOURCE_NAME,
                    source_url=page.source_url,
                    fetched_at=datetime.now(UTC),
                    data_as_of=events[0].event_date if events else None,
                    stock_events_count=len(events),
                    source_status="ready",
                ),
                stock_events=events,
                data_quality_warnings=warnings,
            )
        except PlatformError as exc:
            return self._unavailable_response(
                normalized,
                source_url or (self._build_source_url(issue_id) if issue_id is not None else None),
                company_name=company_name,
                message=f"Stock events source unavailable ({exc.code}: {exc.message}).",
            )
        except Exception as exc:
            return self._unavailable_response(
                normalized,
                source_url or (self._build_source_url(issue_id) if issue_id is not None else None),
                company_name=company_name,
                message=f"Stock events source unavailable ({type(exc).__name__}).",
            )

    def _parse_page(self, page: FetchedPage, *, source_url: str) -> ParsedStockEventsPage:
        soup = BeautifulSoup(page.html, "html.parser")
        table = self._find_events_table(soup)
        if table is None:
            raise PlatformError(
                ErrorCode.SOURCE_CHANGED,
                "The Webb-site stock events table or required headers were not found.",
            )

        rows = table.select("tr")
        header_index, header_map = self._find_header_row(rows)
        if header_index is None:
            raise PlatformError(
                ErrorCode.SOURCE_CHANGED,
                "The Webb-site stock events table headers were not found.",
            )

        candidate_rows = [
            row for row in rows[header_index + 1 :] if any(cell.strip() for cell in _cells(row))
        ]
        events: list[StockEventRow] = []
        skipped_rows = 0
        warnings: list[str] = []
        for row_index, row in enumerate(candidate_rows, start=1):
            try:
                parsed = self._parse_event_row(row, header_map, source_url=source_url)
            except Exception as exc:
                skipped_rows += 1
                warnings.append(
                    structured_warning(
                        "SOURCE_STATUS",
                        "STOCK_EVENTS_ROW_PARSE_FAILED",
                        f"A Webb-site stock event row could not be parsed ({type(exc).__name__}).",
                    )
                )
                continue
            if parsed is None:
                skipped_rows += 1
                continue
            events.append(parsed)

        if candidate_rows and not events:
            raise PlatformError(
                ErrorCode.PARSE_ERROR,
                "The Webb-site stock events table did not contain parseable event rows.",
            )

        if skipped_rows:
            warnings.append(
                structured_warning(
                    "SOURCE_STATUS",
                    "STOCK_EVENTS_ROWS_SKIPPED",
                    "Some Webb-site stock event rows were skipped because required fields were missing.",
                )
            )
        return ParsedStockEventsPage(events=tuple(events), warnings=tuple(warnings))

    def _parse_event_row(
        self,
        row: Tag,
        header_map: dict[str, int],
        *,
        source_url: str,
    ) -> StockEventRow | None:
        cells = _cells(row)
        announced = _cell_value(cells, header_map, "announced")
        title = _cell_value(cells, header_map, "type")
        if announced is None or title is None:
            return None
        event_date = _parse_date(announced)
        if event_date is None:
            return None

        year_end = _cell_value(cells, header_map, "yearend")
        amount = _cell_value(cells, header_map, "amount")
        quote_value = _cell_value(cells, header_map, "valueinquotecurr")
        new_old = _cell_value(cells, header_map, "newold")
        ex_date = _cell_value(cells, header_map, "exdate")
        distribution = _cell_value(cells, header_map, "distribution")
        notes = _cell_value(cells, header_map, "notes")
        link = _row_link(row, source_url)
        event_id = _event_id_from_link(link)

        details_parts = [
            part
            for part in (
                f"Year-end {year_end}" if year_end else None,
                f"Amount {amount}" if amount else None,
                f"Value in quote curr. {quote_value}" if quote_value else None,
                f"New/Old {new_old}" if new_old else None,
                f"Ex-date {ex_date}" if ex_date else None,
                f"Distribution {distribution}" if distribution else None,
                f"Notes {notes}" if notes else None,
            )
            if part
        ]
        details = "; ".join(details_parts) or None

        return StockEventRow(
            event_date=event_date,
            title=title,
            event_type=_normalize_event_type(title),
            source=STOCK_EVENTS_SOURCE_NAME,
            link=link,
            details=details,
            event_id=event_id,
            event_details_url=link,
        )

    @staticmethod
    def _find_events_table(soup: BeautifulSoup) -> Tag | None:
        for table in soup.find_all("table"):
            header_row, _ = WebbsiteStockEventsSource._find_header_row(table.select("tr"))
            if header_row is not None:
                return table
        return None

    @staticmethod
    def _find_header_row(rows: list[Tag]) -> tuple[int | None, dict[str, int]]:
        for index, row in enumerate(rows):
            cells = _cells(row)
            normalized = {_normalize_header(cell): cell for cell in cells}
            if {
                "announced",
                "yearend",
                "type",
            }.issubset(normalized):
                return index, {key: idx for idx, key in enumerate(_normalize_header(cell) for cell in cells)}
        return None, {}

    def _unavailable_response(
        self,
        normalized: str,
        source_url: str | None,
        *,
        message: str,
        company_name: str | None = None,
    ) -> StockEventsResponse:
        return StockEventsResponse(
            metadata=StockEventsMetadata(
                code=normalized,
                name=company_name,
                source_name=STOCK_EVENTS_SOURCE_NAME,
                source_url=source_url,
                fetched_at=datetime.now(UTC),
                data_as_of=None,
                stock_events_count=0,
                source_status="unavailable",
            ),
            stock_events=[],
            data_quality_warnings=[
                structured_warning(
                    "SOURCE_STATUS",
                    "STOCK_EVENTS_SOURCE_UNAVAILABLE",
                    message,
                )
            ],
        )

    def _build_source_url(self, issue_id: int | None) -> str | None:
        if issue_id is None:
            return None
        return f"{self.settings.webbsite_base_url.rstrip('/')}/dbpub/events.asp?i={issue_id}"


def _cell_value(cells: list[str], header_map: dict[str, int], key: str) -> str | None:
    index = header_map.get(key)
    if index is None or index >= len(cells):
        return None
    value = cells[index].strip()
    if not value or value in {"-", "--"}:
        return None
    return value


def _cells(row: Tag) -> list[str]:
    return [cell.get_text(" ", strip=True) for cell in row.select("th,td")]


def _normalize_header(value: str) -> str:
    return "".join(ch for ch in value.lower() if ch.isalnum())


def _normalize_event_type(value: str) -> str | None:
    normalized = value.strip()
    if not normalized:
        return None
    lowered = normalized.lower()
    if "dividend" in lowered:
        return "Dividend"
    if "distribution" in lowered:
        return "Distribution"
    if "split" in lowered or "consol" in lowered:
        return "Split/Consolidation"
    if "buyback" in lowered or "repurchase" in lowered:
        return "Buyback"
    if "rights" in lowered:
        return "Rights issue"
    if "bonus" in lowered:
        return "Bonus issue"
    if "share capital" in lowered:
        return "Share capital change"
    return normalized


def _parse_date(value: str) -> date | None:
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _row_link(row: Tag, source_url: str) -> str | None:
    link = row.find("a", href=True)
    if link is None:
        return source_url
    href = str(link.get("href") or "").strip()
    if not href:
        return source_url
    return urljoin(source_url, href)


def _event_id_from_link(link: str | None) -> str | None:
    if not link:
        return None
    parsed = urlparse(link)
    query = parse_qs(parsed.query)
    event_id = query.get("e", [None])[0]
    return event_id.strip() if isinstance(event_id, str) and event_id.strip() else None
