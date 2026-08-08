from __future__ import annotations

from functools import lru_cache

from app.config import Settings, get_settings
from app.errors import PlatformError
from app.models import AnnouncementsResponse, CcassResponse, PriceHistoryResponse
from app.services.announcements import AnnouncementsService, get_announcements_service
from app.services.ccass import CcassService, get_ccass_service
from app.services.price_history import PriceHistoryService, get_price_history_service
from app.storage.history import NormalizedSnapshotRepository
from ccass_core.ai_read_model import (
    AIReadModelV0_1,
    build_ai_read_model_v0_1,
    context_unavailable_warning,
    _source_id,
)
from ccass_core.ai_read_model_governance import (
    AIReadModelConsumerView,
    AIReadModelConsumerUsageGuidance,
    AIReadModelGovernanceContext,
    build_ai_read_model_consumer_view,
    build_ai_read_model_consumer_guidance,
    build_ai_read_model_governance_context,
    build_ai_read_model_governance_interpretation,
)
from ccass_core.compute import compute_analysis
from ccass_core.normalize import normalize_stock_code
from ccass_core.source_trace import SourceTraceView


class AIReadModelService:
    def __init__(
        self,
        *,
        ccass_service: CcassService | None = None,
        announcements_service: AnnouncementsService | None = None,
        price_history_service: PriceHistoryService | None = None,
        snapshot_repository: NormalizedSnapshotRepository | None = None,
        settings: Settings | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.ccass_service = ccass_service or get_ccass_service()
        self.announcements_service = announcements_service or get_announcements_service()
        self.price_history_service = price_history_service or get_price_history_service()
        self.snapshot_repository = snapshot_repository or NormalizedSnapshotRepository(
            self.settings.ccass_sqlite_path
        )

    async def get_read_model(
        self,
        code: str | int,
        *,
        surface: str = "ccass_ai_read_model",
    ) -> AIReadModelV0_1:
        normalized = normalize_stock_code(code)
        try:
            response = await self.ccass_service.get_stock_data(normalized)
        except PlatformError as exc:
            return build_ai_read_model_v0_1(
                code=normalized,
                response=None,
                surface=surface,
                error=exc,
            )

        source_id = _source_id(response.metadata.source_name)
        snapshot_id = self._snapshot_id(response, source_id=source_id)
        previous_response = self._previous_response(response, source_id=source_id)
        previous_snapshot_id = (
            self._snapshot_id(previous_response, source_id=source_id)
            if previous_response is not None
            else None
        )
        analysis = compute_analysis(response, previous_response)
        extra_warnings: list[str] = []
        announcements = await self._get_announcements(normalized, extra_warnings)
        price_history = await self._get_price_history(normalized, extra_warnings)

        return build_ai_read_model_v0_1(
            code=normalized,
            response=response,
            surface=surface,
            analysis=analysis,
            previous_response=previous_response,
            snapshot_id=snapshot_id,
            previous_snapshot_id=previous_snapshot_id,
            announcements=announcements,
            price_history=price_history,
            extra_warnings=extra_warnings,
        )

    async def get_read_model_governance_context(
        self,
        code: str | int,
        *,
        surface: str = "ccass_ai_read_model",
        source_trace: SourceTraceView | None = None,
    ) -> AIReadModelGovernanceContext:
        read_model = await self.get_read_model(code, surface=surface)
        return build_ai_read_model_governance_context(read_model, source_trace=source_trace)

    async def get_read_model_consumer_view(
        self,
        code: str | int,
        *,
        surface: str = "ccass_ai_read_model",
        source_trace: SourceTraceView | None = None,
    ) -> AIReadModelConsumerView:
        read_model = await self.get_read_model(code, surface=surface)
        return build_ai_read_model_consumer_view(read_model, source_trace=source_trace)

    async def get_read_model_consumer_guidance(
        self,
        code: str | int,
        *,
        surface: str = "ccass_ai_read_model",
        source_trace: SourceTraceView | None = None,
    ) -> AIReadModelConsumerUsageGuidance:
        read_model = await self.get_read_model(code, surface=surface)
        governance_context = build_ai_read_model_governance_context(
            read_model,
            source_trace=source_trace,
        )
        governance_interpretation = build_ai_read_model_governance_interpretation(
            governance_context
        )
        return build_ai_read_model_consumer_guidance(
            governance_context,
            governance_interpretation,
        )

    def _snapshot_id(self, response: CcassResponse | None, *, source_id: str) -> int | None:
        if response is None or response.metadata.data_as_of is None:
            return None
        return self.snapshot_repository.snapshot_id_on(
            response.metadata.code,
            response.metadata.data_as_of,
            source_id=source_id,
        )

    def _previous_response(self, response: CcassResponse, *, source_id: str) -> CcassResponse | None:
        if response.metadata.data_as_of is None:
            return None
        previous = self.snapshot_repository.previous(
            response.metadata.code,
            before_date=response.metadata.data_as_of,
            source_id=source_id,
        )
        return previous.to_response() if previous is not None else None

    async def _get_announcements(
        self,
        code: str,
        extra_warnings: list[str],
    ) -> AnnouncementsResponse | None:
        try:
            return await self.announcements_service.get_announcements(code)
        except PlatformError as exc:
            extra_warnings.append(
                context_unavailable_warning(
                    "announcements",
                    f"Announcements surface unavailable: {exc.code}: {exc.message}",
                )
            )
            return None

    async def _get_price_history(
        self,
        code: str,
        extra_warnings: list[str],
    ) -> PriceHistoryResponse | None:
        try:
            return await self.price_history_service.get_price_history(code)
        except PlatformError as exc:
            extra_warnings.append(
                context_unavailable_warning(
                    "price_history",
                    f"Price history surface unavailable: {exc.code}: {exc.message}",
                )
            )
            return None


@lru_cache
def get_ai_read_model_service() -> AIReadModelService:
    return AIReadModelService(settings=get_settings())
