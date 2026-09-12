from datetime import UTC, date, datetime

import pytest

from app.models import (
    AnnouncementRow,
    AnnouncementsMetadata,
    AnnouncementsResponse,
    OfficerRow,
    OfficersMetadata,
    OfficersResponse,
    ShareCapitalHistoryMetadata,
    ShareCapitalHistoryResponse,
    ShareCapitalHistoryRow,
    StockEventsMetadata,
    StockEventsResponse,
    StockEventRow,
)
from app.services.historical_intelligence import get_historical_intelligence


class Announcements:
    async def get_announcements(self, code, *, start_date, end_date):
        return AnnouncementsResponse(
            metadata=AnnouncementsMetadata(
                code=code, source_name="HKEX", source_url="https://hkex.invalid",
                fetched_at=datetime(2026, 9, 1, tzinfo=UTC),
                earliest_announcement_date=start_date, latest_announcement_date=end_date,
                announcement_count=1,
            ),
            announcements=[AnnouncementRow(
                announcement_date=date(2026, 8, 1), title="Capital change",
                source="HKEX", link="https://hkex.invalid/event",
            )],
        )


class ShareCapital:
    async def get_share_capital_history(self, code, *, start_date, end_date):
        return ShareCapitalHistoryResponse(
            metadata=ShareCapitalHistoryMetadata(
                code=code, source_name="HKEX monthly returns",
                fetched_at=datetime(2026, 9, 1, tzinfo=UTC), source_status="ready",
                documents_attempted=1, documents_fetched=1, documents_parsed=1,
            ),
            rows=[ShareCapitalHistoryRow(
                announce_date=date(2026, 8, 2), reason="Rights issue",
                source="HKEX", source_url="https://hkex.invalid/capital",
            )],
        )


class Officers:
    async def get_officers(self, code):
        return OfficersResponse(
            metadata=OfficersMetadata(
                code=code, source_name="Officers", source_url="https://officers.invalid",
                fetched_at=datetime(2026, 9, 1, tzinfo=UTC), source_status="ready",
                data_as_of=date(2026, 8, 1), officers_count=1,
            ),
            officers=[OfficerRow(name="Example Director", positions=["Director"], tenure_from=date(2020, 1, 1))],
        )


class StockEvents:
    async def get_stock_events(self, code):
        return StockEventsResponse(
            metadata=StockEventsMetadata(
                code=code, source_name="Stock events", source_url="https://events.invalid",
                fetched_at=datetime(2026, 9, 1, tzinfo=UTC), data_as_of=date(2026, 8, 3),
                stock_events_count=1, source_status="pending",
            ),
            stock_events=[StockEventRow(
                event_date=date(2026, 8, 3), title="Suspension", source="Stock events",
            )],
            data_quality_warnings=["source pending"],
        )


@pytest.mark.asyncio
async def test_historical_intelligence_builds_timeline_and_explicit_gaps():
    result = await get_historical_intelligence(
        "00005", start_date=date(2021, 9, 1), end_date=date(2026, 9, 1),
        announcements_service=Announcements(), capital_service=object(),
        share_capital_service=ShareCapital(), officers_service=Officers(),
        stock_events_service=StockEvents(),
    )

    assert result.domains["announcements"].status == "COMPLETE"
    assert result.domains["share_capital"].status == "COMPLETE"
    assert result.domains["stock_events"].status == "PARTIAL"
    assert result.domains["di_ownership"].status == "UNAVAILABLE"
    assert [item.event_date for item in result.timeline] == [date(2026, 8, 1), date(2026, 8, 2)]
    assert result.timeline[0].source_url
    assert result.timeline[0].raw_label == "Capital change"


@pytest.mark.asyncio
async def test_historical_intelligence_rejects_more_than_five_years():
    with pytest.raises(ValueError, match="five years"):
        await get_historical_intelligence(
            "00005", start_date=date(2020, 1, 1), end_date=date(2026, 9, 1),
            announcements_service=Announcements(), capital_service=object(),
            share_capital_service=ShareCapital(), officers_service=Officers(),
            stock_events_service=StockEvents(),
        )
