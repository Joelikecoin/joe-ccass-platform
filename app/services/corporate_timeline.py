from __future__ import annotations

import hashlib
from datetime import date

from app.models import AnnouncementsResponse, CorporateEvidence, CorporateTimeline


def build_corporate_timeline(
    response: AnnouncementsResponse,
    *,
    start_date: date,
    end_date: date,
) -> CorporateTimeline:
    events: list[CorporateEvidence] = []
    for row in response.announcements:
        key = f"{response.metadata.code}|{row.announcement_date.isoformat()}|{row.title}|{row.link or ''}"
        event_id = hashlib.sha256(key.encode()).hexdigest()[:24]
        events.append(
            CorporateEvidence(
                event_id=event_id,
                stock_code=response.metadata.code,
                event_date=row.announcement_date,
                event_type=_tag(row.title),
                title=row.title,
                source=row.source,
                source_url=row.link,
                evidence_status="verified",
                retrieved_at=response.metadata.fetched_at,
            )
        )
    events.sort(key=lambda e: (e.event_date, e.event_id))
    return CorporateTimeline(stock_code=response.metadata.code, start_date=start_date, end_date=end_date, events=events)


def _tag(title: str) -> str:
    value = title.casefold()
    if "buy-back" in value or "buyback" in value:
        return "BUYBACK"
    if "dividend" in value:
        return "OTHER_MAJOR_CORPORATE_EVENT"
    if "capital" in value or "securities" in value or "share" in value:
        return "SHARE_CAPITAL_CHANGE"
    if "acquisition" in value:
        return "MAJOR_ACQUISITION"
    if "disposal" in value:
        return "MAJOR_DISPOSAL"
    if "auditor" in value:
        return "AUDITOR_CHANGE"
    return "OTHER_MAJOR_CORPORATE_EVENT"
