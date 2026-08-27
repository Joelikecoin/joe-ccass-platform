from __future__ import annotations

import asyncio
import json
from dataclasses import asdict, dataclass
from datetime import UTC, date, datetime
from typing import Any

from app.data_quality import structured_warning
from app.models import CcassResponse
from app.services.ccass import get_ccass_service
from app.services.announcements import get_announcements_service
from app.services.capital_information import get_capital_information_service
from app.services.officers import get_officers_service
from app.services.price_history import get_price_history_service
from app.services.stock_events import get_stock_events_service
from app.sources.price_history import YAHOO_CHART_BASE_URL
from app.sources.webbsite import WebbsiteClient
from app.streamlit_ui import (
    DEFAULT_LOCALE,
    DownloadArtifacts,
    RawPreviewTable,
    build_download_artifacts,
    build_raw_preview_tables,
)
from ccass_core.normalize import normalize_stock_code
from ccass_core.report import build_markdown_report, build_chatgpt_copy_payload
from ccass_core.source_trace import SourceTraceView, build_source_trace_markdown, build_source_trace_view
from app.models import HoldingsSummary, SourceMetadata

YAHOO_CHART_API_URL = f"{YAHOO_CHART_BASE_URL}{{symbol}}"


@dataclass(slots=True)
class LiveDiagnostic:
    status: str
    message: str | None = None


@dataclass(slots=True)
class LiveDownloadArtifacts:
    combined_csv_bytes: bytes
    combined_csv_filename: str
    workbook_bytes: bytes
    workbook_filename: str
    json_bytes: bytes
    json_filename: str


@dataclass(slots=True)
class LiveProduct:
    code: str
    symbol: str
    company: dict[str, Any]
    latest_price: dict[str, Any]
    price_history: list[dict[str, Any]]
    announcements: list[dict[str, Any]]
    corporate_events: list[dict[str, Any]]
    share_capital_changes: list[dict[str, Any]]
    officers: list[dict[str, Any]]
    source_notes: list[str]
    diagnostics: list[LiveDiagnostic]
    fetched_at: datetime | None
    response: CcassResponse
    source_trace: SourceTraceView | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "symbol": self.symbol,
            "company": self.company,
            "latest_price": self.latest_price,
            "price_history": self.price_history,
            "announcements": self.announcements,
            "corporate_events": self.corporate_events,
            "share_capital_changes": self.share_capital_changes,
            "officers": self.officers,
            "source_notes": self.source_notes,
            "diagnostics": [asdict(item) for item in self.diagnostics],
            "fetched_at": self.fetched_at.isoformat(sep=" ", timespec="seconds")
            if self.fetched_at is not None
            else None,
            "response": self.response.model_dump(mode="json"),
            "source_trace": _dump_pydantic(self.source_trace) if self.source_trace is not None else None,
        }


def build_live_product_from_response(
    response: CcassResponse,
    *,
    source_trace: SourceTraceView | None = None,
) -> LiveProduct:
    announcements, events, capital_information, officers = _build_response_tables(response)
    normalized_code = response.metadata.code
    return LiveProduct(
        code=response.metadata.code,
        symbol=(response.price_history.metadata.ticker if response.price_history is not None else f"{normalized_code}.HK"),
        company=_build_company_dict(response),
        latest_price=_build_latest_price(response),
        price_history=_build_price_history_rows(response),
        announcements=announcements,
        corporate_events=events,
        share_capital_changes=capital_information,
        officers=officers,
        source_notes=_build_source_notes(response, source_trace),
        diagnostics=_build_diagnostics(response, source_trace),
        fetched_at=response.metadata.fetched_at,
        response=response,
        source_trace=source_trace,
    )


async def build_live_product_from_response_with_surfaces(
    response: CcassResponse | None,
    *,
    code: str | int,
    source_trace: SourceTraceView | None = None,
) -> LiveProduct | None:
    normalized_code = normalize_stock_code(code)
    working_response = response.model_copy(deep=True) if response is not None else None

    issue_id = 0
    company_name: str | None = None
    source_url = ""
    if working_response is None:
        try:
            issue_id, company_name = await WebbsiteClient().resolve_issue_id(normalized_code)
            source_url = f"https://www3.hkexnews.hk/sdw/search/searchsdw_c.aspx?i={issue_id}"
        except Exception:
            issue_id = 0
            company_name = None
        working_response = CcassResponse(
            metadata=SourceMetadata(
                code=normalized_code,
                name=company_name,
                issue_id=issue_id,
                holdings_date=None,
                fetched_at=datetime.now(UTC),
                source_url=source_url,
                source_name="Joe auxiliary runtime surfaces",
                cached=False,
            ),
            holdings_summary=HoldingsSummary(),
            holdings=[],
            data_quality_warnings=[],
        )

    need_price_history = working_response.price_history is None or not getattr(working_response.price_history, "prices", ())
    need_announcements = working_response.announcements is None or not getattr(
        working_response.announcements,
        "announcements",
        (),
    )
    need_stock_events = working_response.stock_events is None or not getattr(
        working_response.stock_events,
        "stock_events",
        (),
    )
    need_capital_information = working_response.capital_information is None or not getattr(
        working_response.capital_information,
        "capital_information",
        (),
    )
    need_officers = working_response.officers is None or not getattr(working_response.officers, "officers", ())

    async def _load_auxiliary() -> tuple[Any, Any, Any, Any, Any]:
        tasks: list[Any] = []
        if need_price_history:
            tasks.append(get_price_history_service().get_price_history(normalized_code))
        if need_announcements:
            tasks.append(get_announcements_service().get_announcements(normalized_code))
        if need_stock_events:
            tasks.append(get_stock_events_service().get_stock_events(normalized_code))
        if need_capital_information:
            tasks.append(get_capital_information_service().get_capital_information(normalized_code))
        if need_officers:
            tasks.append(get_officers_service().get_officers(normalized_code))
        results = await asyncio.gather(*tasks, return_exceptions=True) if tasks else []
        iterator = iter(results)
        return (
            next(iterator) if need_price_history else working_response.price_history,
            next(iterator) if need_announcements else working_response.announcements,
            next(iterator) if need_stock_events else working_response.stock_events,
            next(iterator) if need_capital_information else working_response.capital_information,
            next(iterator) if need_officers else working_response.officers,
        )

    price_history, announcements, stock_events, capital_information, officers = await _load_auxiliary()
    warnings = list(working_response.data_quality_warnings)
    has_auxiliary_data = False

    def _merge_if_empty(current: Any | None, incoming: Any, *, label: str) -> Any | None:
        nonlocal has_auxiliary_data
        if isinstance(incoming, Exception):
            warnings.append(
                structured_warning(
                    "DATA_LIMITATION",
                    f"{label.upper()}_UNAVAILABLE",
                    f"{label.replace('_', ' ').title()} are unavailable ({type(incoming).__name__}).",
                )
            )
            return current
        if current is not None:
            if label == "price_history":
                existing_prices = getattr(current, "prices", ())
                if existing_prices:
                    return current
            else:
                existing_rows = getattr(current, label, ())
                if existing_rows:
                    return current
        candidate_rows = getattr(incoming, "prices", None)
        if candidate_rows is None:
            candidate_rows = getattr(incoming, label, ())
        if candidate_rows:
            has_auxiliary_data = True
            warnings.extend(getattr(incoming, "data_quality_warnings", ()))
            return incoming
        warnings.extend(getattr(incoming, "data_quality_warnings", ()))
        return current

    working_response = working_response.model_copy(
        update={
            "price_history": _merge_if_empty(working_response.price_history, price_history, label="price_history"),
            "announcements": _merge_if_empty(working_response.announcements, announcements, label="announcements"),
            "stock_events": _merge_if_empty(working_response.stock_events, stock_events, label="stock_events"),
            "capital_information": _merge_if_empty(
                working_response.capital_information,
                capital_information,
                label="capital_information",
            ),
            "officers": _merge_if_empty(working_response.officers, officers, label="officers"),
            "data_quality_warnings": list(dict.fromkeys(warnings)),
        }
    )

    if response is None and not has_auxiliary_data:
        return None

    return build_live_product_from_response(working_response, source_trace=source_trace)


def _dump_pydantic(value: Any) -> Any:
    if value is None:
        return None
    model_dump = getattr(value, "model_dump", None)
    if callable(model_dump):
        return model_dump(mode="json")
    if isinstance(value, dict):
        return {key: _dump_pydantic(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_dump_pydantic(item) for item in value]
    if isinstance(value, (date, datetime)):
        return value.isoformat(sep=" ", timespec="seconds") if isinstance(value, datetime) else value.isoformat()
    return value


def _format_decimal(value: float | None, digits: int = 2) -> str:
    if value is None:
        return "—"
    return f"{value:,.{digits}f}"


def _format_datetime(value: datetime | None) -> str:
    return "—" if value is None else value.isoformat(sep=" ", timespec="seconds")


def _format_date(value: date | None) -> str:
    return "—" if value is None else value.isoformat()


def _announcement_dict(row: Any) -> dict[str, Any]:
    published = getattr(row, "announcement_date", None)
    title = getattr(row, "title", None)
    source = getattr(row, "source", None)
    link = getattr(row, "link", None)
    return {
        "publish_time": _format_date(published) if isinstance(published, date) else (published or "—"),
        "category": source or "HKEX Announcement",
        "title": title or "—",
        "file_info": source or "—",
        "official_url": link or "",
        "event_tags": source or "—",
    }


def _stock_event_dict(row: Any) -> dict[str, Any]:
    event_date = getattr(row, "event_date", None)
    event_type = getattr(row, "event_type", None)
    source = getattr(row, "source", None)
    link = getattr(row, "link", None)
    details = getattr(row, "details", None)
    title = getattr(row, "title", None)
    return {
        "publish_time": _format_date(event_date) if isinstance(event_date, date) else (event_date or "—"),
        "category": event_type or source or "Corporate Event",
        "title": title or "—",
        "file_info": details or source or "—",
        "official_url": link or "",
        "event_tags": event_type or source or "—",
    }


def _capital_change_dict(row: Any) -> dict[str, Any]:
    as_of = getattr(row, "as_of", None)
    source = getattr(row, "source", None)
    link = getattr(row, "link", None)
    label = getattr(row, "label", None)
    value = getattr(row, "value", None)
    unit = getattr(row, "unit", None)
    note = getattr(row, "note", None)
    return {
        "publish_time": _format_date(as_of) if isinstance(as_of, date) else (as_of or "—"),
        "category": label or "Capital",
        "title": value or "—",
        "file_info": " ".join(part for part in (unit, note, source) if part) or "—",
        "official_url": link or "",
        "event_tags": source or "—",
    }


def _officer_dict(row: Any) -> dict[str, Any]:
    positions = getattr(row, "positions", None) or []
    tenure_from = getattr(row, "tenure_from", None)
    tenure_to = getattr(row, "tenure_to", None)
    salary = getattr(row, "salary", None)
    return {
        "name": getattr(row, "name", None) or "—",
        "title": ", ".join(str(item) for item in positions if item) or "—",
        "age": getattr(row, "age", None),
        "fiscal_year": _format_date(tenure_to) if isinstance(tenure_to, date) else (
            _format_date(tenure_from) if isinstance(tenure_from, date) else "—"
        ),
        "total_pay": salary or "—",
        "exercised_value": "—",
        "unexercised_value": "—",
        "source": "HKEX / Local backend",
    }


def _build_company_dict(response: CcassResponse) -> dict[str, Any]:
    price_history = response.price_history
    currency = None
    if price_history is not None and price_history.metadata.currency:
        currency = price_history.metadata.currency
    return {
        "company_name": response.metadata.name or response.metadata.code,
        "short_name": response.metadata.name or response.metadata.code,
        "exchange": "HKEX",
        "sector": None,
        "industry": None,
        "currency": currency,
        "fetched_at": _format_datetime(response.metadata.fetched_at),
        "data_as_of": _format_date(response.metadata.data_as_of),
        "source_name": response.metadata.source_name,
        "source_url": response.metadata.source_url,
        "issue_id": response.metadata.issue_id,
    }


def _build_price_history_rows(response: CcassResponse) -> list[dict[str, Any]]:
    history = response.price_history
    if history is None:
        return []
    rows: list[dict[str, Any]] = []
    for row in history.prices:
        rows.append(
            {
                "date": _format_date(row.price_date),
                "open": row.open,
                "high": row.high,
                "low": row.low,
                "close": row.close,
                "vwap": row.vwap,
                "adjusted_close": row.adjusted_close,
                "volume": row.volume,
                "turnover": row.turnover,
                "price_source": row.price_source,
                "turnover_est": row.turnover_est,
                "vwap_est": row.vwap_est,
                "source": history.metadata.source_name,
                "source_url": history.metadata.source_url,
            }
        )
    return rows


def _build_latest_price(response: CcassResponse) -> dict[str, Any]:
    history = response.price_history
    if history is None or not history.prices:
        return {
            "price_display": "—",
            "change_display": "—",
            "market_state": "Unavailable",
            "market_time": "—",
            "fallback_used": response.metadata.cached,
            "source_name": response.metadata.source_name,
            "source_url": response.metadata.source_url,
        }
    latest = history.prices[-1]
    previous = history.prices[-2] if len(history.prices) > 1 else None
    latest_close = latest.close
    previous_close = previous.close if previous is not None else None
    change = None
    change_pct = None
    if latest_close is not None and previous_close is not None:
        change = latest_close - previous_close
        if previous_close != 0:
            change_pct = change / previous_close * 100
    price_display = _format_decimal(latest_close, 2)
    if change is not None:
        change_display = f"{change:+,.2f}"
        if change_pct is not None:
            change_display = f"{change_display} ({change_pct:+.2f}%)"
    else:
        change_display = "—"
    return {
        "price_display": price_display,
        "change_display": change_display,
        "market_state": history.metadata.source_name,
        "market_time": _format_date(latest.price_date),
        "fallback_used": response.metadata.cached,
        "source_name": history.metadata.source_name,
        "source_url": history.metadata.source_url,
        "close": latest_close,
        "vwap": latest.vwap,
        "open": latest.open,
        "high": latest.high,
        "low": latest.low,
        "volume": latest.volume,
        "turnover": latest.turnover,
        "price_source": latest.price_source,
        "turnover_est": latest.turnover_est,
        "vwap_est": latest.vwap_est,
        "data_as_of": _format_date(history.metadata.data_as_of),
    }


def _build_source_notes(response: CcassResponse, source_trace: SourceTraceView | None) -> list[str]:
    notes: list[str] = []
    if response.fetch_summary:
        notes.append(response.fetch_summary)
    if source_trace is not None:
        notes.extend(str(note) for note in getattr(source_trace, "notes", ()) if note)
    if response.data_quality_warnings:
        notes.extend(response.data_quality_warnings)
    notes.append(f"Source: {response.metadata.source_name}")
    notes.append(f"Data as of: {_format_date(response.metadata.data_as_of)}")
    if response.metadata.cached:
        notes.append("Cached result: Yes")
    return list(dict.fromkeys(notes))


def _build_diagnostics(response: CcassResponse, source_trace: SourceTraceView | None) -> list[LiveDiagnostic]:
    status = "READY"
    if response.data_quality_warnings:
        status = "PARTIAL"
    if response.metadata.cached:
        status = "CACHED"
    message_parts = [
        response.metadata.source_name,
        f"data_as_of={_format_date(response.metadata.data_as_of)}",
        f"fetched_at={_format_datetime(response.metadata.fetched_at)}",
    ]
    if source_trace is not None and getattr(source_trace, "route", None):
        message_parts.append(f"route={getattr(source_trace, 'route')}")
    return [LiveDiagnostic(status=status, message=" | ".join(message_parts))]


def _build_response_tables(response: CcassResponse) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    announcements = [_announcement_dict(row) for row in response.announcements.announcements] if response.announcements is not None else []
    events = [_stock_event_dict(row) for row in response.stock_events.stock_events] if response.stock_events is not None else []
    capital_information = [
        _capital_change_dict(row) for row in response.capital_information.capital_information
    ] if response.capital_information is not None else []
    officers = [_officer_dict(row) for row in response.officers.officers] if response.officers is not None else []
    return announcements, events, capital_information, officers


async def prepare_live_product(code: str | int) -> LiveProduct | None:
    normalized = normalize_stock_code(code)
    try:
        gateway_response = await get_ccass_service().get_stock_gateway_response(normalized)
    except Exception:
        return None

    return build_live_product_from_response(
        gateway_response.normalized_response,
        source_trace=build_source_trace_view(gateway_response),
    )


def build_live_preview_tables(
    live_product: LiveProduct | None,
    *,
    sample_size: int = 5,
    locale: str = DEFAULT_LOCALE,
) -> tuple[RawPreviewTable, ...]:
    if live_product is None:
        return ()
    return build_raw_preview_tables(live_product.response, sample_size=sample_size, locale=locale)


def build_live_download_artifacts(live_product: LiveProduct | None, *, locale: str = DEFAULT_LOCALE) -> LiveDownloadArtifacts | None:
    if live_product is None:
        return None
    artifacts: DownloadArtifacts = build_download_artifacts(live_product.response, locale=locale)
    json_bytes = json.dumps(live_product.to_dict(), ensure_ascii=False, indent=2).encode("utf-8")
    return LiveDownloadArtifacts(
        combined_csv_bytes=artifacts.combined_csv_bytes,
        combined_csv_filename=artifacts.combined_csv_filename,
        workbook_bytes=artifacts.workbook_bytes,
        workbook_filename=artifacts.workbook_filename,
        json_bytes=json_bytes,
        json_filename=f"{live_product.code}_live_product.json",
    )


def render_live_markdown(live_product: LiveProduct | None, *, locale: str = DEFAULT_LOCALE) -> str:
    if live_product is None:
        return ""
    response = live_product.response
    markdown = build_markdown_report(
        response,
        code=live_product.code,
        announcements=response.announcements,
        stock_events=response.stock_events,
        capital_information=response.capital_information,
        officers=response.officers,
        price_history=response.price_history,
        locale=locale,
    )
    live_summary = [
        "## Live Product",
        "",
        f"- Code: {live_product.code}",
        f"- Symbol: {live_product.symbol}",
        f"- Company: {live_product.company.get('company_name') or '—'}",
        f"- Fetched at: {_format_datetime(live_product.fetched_at)}",
        f"- Data as of: {live_product.company.get('data_as_of') or '—'}",
    ]
    markdown = "\n".join(live_summary) + "\n\n" + markdown
    return markdown.rstrip() + "\n"


def build_live_chatgpt_payload(live_product: LiveProduct | None, *, locale: str = DEFAULT_LOCALE) -> str:
    return build_chatgpt_copy_payload(render_live_markdown(live_product, locale=locale))
