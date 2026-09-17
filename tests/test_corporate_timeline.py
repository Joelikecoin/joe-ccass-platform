from datetime import UTC, date, datetime

from app.models import AnnouncementRow, AnnouncementsMetadata, AnnouncementsResponse
from app.services.corporate_timeline import build_corporate_timeline


def test_hkex_title_categories_are_conservative_and_source_backed():
    response = AnnouncementsResponse(
        metadata=AnnouncementsMetadata(
            code="00388",
            source_name="HKEXnews",
            source_url="https://www1.hkexnews.hk/search/titlesearch.xhtml",
            fetched_at=datetime(2026, 9, 17, tzinfo=UTC),
        ),
        announcements=[
            AnnouncementRow(
                announcement_date=date(2026, 9, 1),
                title="Disclosure of Interests by Substantial Shareholder",
                source="HKEXnews",
                link="https://www1.hkexnews.hk/event/di.pdf",
            ),
            AnnouncementRow(
                announcement_date=date(2026, 9, 2),
                title="Appointment of Independent Financial Adviser",
                source="HKEXnews",
                link="https://www1.hkexnews.hk/event/adviser.pdf",
            ),
            AnnouncementRow(
                announcement_date=date(2026, 9, 3),
                title="Placing of New Shares",
                source="HKEXnews",
                link="https://www1.hkexnews.hk/event/placing.pdf",
            ),
            AnnouncementRow(
                announcement_date=date(2026, 9, 4),
                title="Whitewash Waiver",
                source="HKEXnews",
                link="https://www1.hkexnews.hk/event/whitewash.pdf",
            ),
        ],
    )

    timeline = build_corporate_timeline(response, start_date=date(2026, 9, 1), end_date=date(2026, 9, 4))

    assert [event.event_type for event in timeline.events] == [
        "DI_DISCLOSURE", "ADVISER_EVENT", "PLACING", "WHITEWASH"
    ]
    assert all(event.source == "HKEXnews" and event.source_url for event in timeline.events)
