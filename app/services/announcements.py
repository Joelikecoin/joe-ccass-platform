from __future__ import annotations

from functools import lru_cache
from datetime import date

from app.config import Settings, get_settings
from app.models import AnnouncementsResponse
from app.sources.announcements import HKEXNewsAnnouncementsSource


class AnnouncementsService:
    def __init__(self, source: HKEXNewsAnnouncementsSource | None = None) -> None:
        self.source = source or HKEXNewsAnnouncementsSource()

    async def get_announcements(
        self,
        code: str | int,
        *,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> AnnouncementsResponse:
        return await self.source.get_announcements(
            code,
            start_date=start_date,
            end_date=end_date,
        )


@lru_cache
def get_announcements_service() -> AnnouncementsService:
    settings: Settings = get_settings()
    return AnnouncementsService(HKEXNewsAnnouncementsSource(settings))

