from __future__ import annotations

import asyncio
import hashlib
from datetime import UTC, date, datetime, timedelta
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from app.models import (
    AnnouncementsResponse,
    CapitalInformationResponse,
    OfficersResponse,
    ShareCapitalHistoryResponse,
    StockEventsResponse,
)
from app.services.announcements import AnnouncementsService
from app.services.capital_information import CapitalInformationService
from app.services.officers import OfficersService
from app.services.share_capital_history import ShareCapitalHistoryService
from app.services.stock_events import StockEventsService


Status = Literal["COMPLETE", "PARTIAL", "UNAVAILABLE", "ERROR"]


class IntelligenceTimelineItem(BaseModel):
    event_id: str
    event_date: date
    event_type: str
    raw_label: str
    source: str
    source_url: str | None = None
    source_date: date | None = None
    provenance: str
    data_quality_status: Status


class IntelligenceDomain(BaseModel):
    status: Status
    source: str | None = None
    source_url: str | None = None
    warnings: list[str] = Field(default_factory=list)
    count: int = 0


class HistoricalIntelligenceResponse(BaseModel):
    stock_code: str
    lookback_start: date
    lookback_end: date
    domains: dict[str, IntelligenceDomain]
    timeline: list[IntelligenceTimelineItem] = Field(default_factory=list)
    officers: OfficersResponse | None = None
    announcements: AnnouncementsResponse | None = None
    share_capital: ShareCapitalHistoryResponse | None = None
    stock_events: StockEventsResponse | None = None

    @model_validator(mode="after")
    def timeline_is_sorted(self) -> "HistoricalIntelligenceResponse":
        if self.timeline != sorted(self.timeline, key=lambda item: (item.event_date, item.event_id)):
            raise ValueError("timeline must be sorted by authoritative event date")
        return self


async def get_historical_intelligence(
    code: str,
    *,
    start_date: date,
    end_date: date,
    announcements_service: AnnouncementsService,
    capital_service: CapitalInformationService,
    share_capital_service: ShareCapitalHistoryService,
    officers_service: OfficersService,
    stock_events_service: StockEventsService,
) -> HistoricalIntelligenceResponse:
    if start_date > end_date:
        raise ValueError("start_date must not be after end_date")
    if end_date - start_date > timedelta(days=366 * 5 + 2):
        raise ValueError("lookback window cannot exceed five years")
    results = await asyncio.gather(
        announcements_service.get_announcements(code, start_date=start_date, end_date=end_date),
        share_capital_service.get_share_capital_history(code, start_date=start_date, end_date=end_date),
        officers_service.get_officers(code),
        stock_events_service.get_stock_events(code),
        return_exceptions=True,
    )
    announcements = results[0] if isinstance(results[0], AnnouncementsResponse) else None
    share_capital = results[1] if isinstance(results[1], ShareCapitalHistoryResponse) else None
    officers = results[2] if isinstance(results[2], OfficersResponse) else None
    stock_events = results[3] if isinstance(results[3], StockEventsResponse) else None
    domains: dict[str, IntelligenceDomain] = {}
    domains["announcements"] = _response_domain(announcements, "announcements", results[0])
    domains["share_capital"] = _response_domain(share_capital, "share_capital", results[1])
    domains["officers"] = _response_domain(officers, "officers", results[2])
    domains["stock_events"] = _response_domain(stock_events, "stock_events", results[3])
    for unavailable in ("di_ownership", "major_shareholders", "advisers_intermediaries"):
        domains[unavailable] = IntelligenceDomain(
            status="UNAVAILABLE",
            warnings=["No approved historical source is implemented for this domain."],
        )
    timeline = _timeline(code, announcements, share_capital, stock_events, start_date, end_date)
    return HistoricalIntelligenceResponse(
        stock_code=code,
        lookback_start=start_date,
        lookback_end=end_date,
        domains=domains,
        timeline=timeline,
        officers=officers,
        announcements=announcements,
        share_capital=share_capital,
        stock_events=stock_events,
    )


def _response_domain(response: BaseModel | None, name: str, result: object) -> IntelligenceDomain:
    if response is None:
        return IntelligenceDomain(status="ERROR", warnings=[f"{name} retrieval failed: {type(result).__name__}"])
    metadata = response.metadata
    status = getattr(metadata, "source_status", None)
    if status == "unavailable":
        quality: Status = "UNAVAILABLE"
    elif status in {"pending", "partial"}:
        quality = "PARTIAL"
    elif getattr(response, "data_quality_warnings", []):
        quality = "PARTIAL"
    else:
        quality = "COMPLETE"
    source = getattr(metadata, "source_name", None)
    source_url = getattr(metadata, "source_url", None)
    rows = getattr(response, "announcements", None) or getattr(response, "rows", None) or getattr(response, "officers", None) or getattr(response, "stock_events", None) or []
    if not rows and quality == "COMPLETE":
        quality = "PARTIAL"
    if name in {"officers", "stock_events"} and quality == "COMPLETE":
        quality = "PARTIAL"
    return IntelligenceDomain(
        status=quality,
        source=source,
        source_url=source_url,
        warnings=list(getattr(response, "data_quality_warnings", [])),
        count=len(rows),
    )


def _timeline(code: str, announcements: AnnouncementsResponse | None, capital: ShareCapitalHistoryResponse | None, stock_events: StockEventsResponse | None, start_date: date, end_date: date) -> list[IntelligenceTimelineItem]:
    items: list[IntelligenceTimelineItem] = []
    if announcements:
        for row in announcements.announcements:
            items.append(_item(code, row.announcement_date, "ANNOUNCEMENT", row.title, row.source, row.link, row.announcement_date, "HKEX announcement row", "COMPLETE"))
    if capital:
        for row in capital.rows:
            items.append(_item(code, row.announce_date, "SHARE_CAPITAL_CHANGE", row.reason or "Share capital history event", row.source, row.source_url, row.announce_date, "HKEX monthly return parsed by Joe source adapter", "COMPLETE" if row.reason else "PARTIAL"))
    if stock_events and stock_events.metadata.source_status == "ready":
        for row in stock_events.stock_events:
            if start_date <= row.event_date <= end_date:
                items.append(_item(code, row.event_date, row.event_type or "STOCK_EVENT", row.title, row.source, row.link or row.event_details_url, row.event_date, "Stock event source row", "COMPLETE"))
    return sorted({item.event_id: item for item in items}.values(), key=lambda item: (item.event_date, item.event_id))


def _item(code: str, event_date: date, event_type: str, raw_label: str, source: str, source_url: str | None, source_date: date, provenance: str, status: Status) -> IntelligenceTimelineItem:
    key = f"{code}|{event_date.isoformat()}|{event_type}|{raw_label}|{source_url or ''}"
    return IntelligenceTimelineItem(
        event_id=hashlib.sha256(key.encode()).hexdigest()[:24],
        event_date=event_date,
        event_type=event_type,
        raw_label=raw_label,
        source=source,
        source_url=source_url,
        source_date=source_date,
        provenance=provenance,
        data_quality_status=status,
    )
