from __future__ import annotations

from datetime import date
from functools import lru_cache
import json
import time

from app.config import Settings, get_settings
from app.errors import PlatformError
from app.models import AnnouncementsResponse
from app.storage.announcements import AnnouncementRepository
from app.storage.history import NormalizedSnapshotRepository
from app.sources.announcements import HKEXNewsAnnouncementsSource
from ccass_core.normalize import normalize_stock_code


def _dependency_trace(stage: str, started: float) -> None:
    payload = {"stage": stage, "elapsed_ms": round((time.perf_counter() - started) * 1000, 1)}
    print("ANN_DEP_TRACE " + json.dumps(payload, separators=(",", ":")), flush=True)


class AnnouncementsService:
    def __init__(
        self,
        source: HKEXNewsAnnouncementsSource | None = None,
        repository: AnnouncementRepository | None = None,
    ) -> None:
        self.source = source or HKEXNewsAnnouncementsSource()
        self.repository = repository

    async def get_announcements(
        self,
        code: str | int,
        *,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> AnnouncementsResponse:
        try:
            response = await self.source.get_announcements(
                code,
                start_date=start_date,
                end_date=end_date,
            )
            if self.repository is not None:
                self.repository.save(response)
            return response
        except PlatformError:
            if self.repository is not None:
                cached = self.repository.load(
                    normalize_stock_code(code),
                    start_date=start_date or date(1999, 4, 1),
                    end_date=end_date or date.today(),
                )
                if cached is not None:
                    return cached
            raise


@lru_cache
def get_announcements_service() -> AnnouncementsService:
    started = time.perf_counter()
    _dependency_trace("GET_ANN_SERVICE_START", started)
    settings: Settings = get_settings()
    _dependency_trace("GET_ANN_SETTINGS_DONE", started)
    _dependency_trace("GET_ANN_REPOSITORY_START", started)
    repository = AnnouncementRepository(NormalizedSnapshotRepository(settings.ccass_sqlite_path))
    _dependency_trace("GET_ANN_REPOSITORY_DONE", started)
    source = HKEXNewsAnnouncementsSource(settings)
    _dependency_trace("GET_ANN_SOURCE_DONE", started)
    service = AnnouncementsService(source, repository)
    _dependency_trace("GET_ANN_SERVICE_DONE", started)
    return service

