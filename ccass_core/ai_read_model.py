from __future__ import annotations

import re
from datetime import UTC, date, datetime
from typing import Literal, Sequence

from pydantic import BaseModel, Field, computed_field

from app.data_quality import structured_warning, warning_code
from app.errors import PlatformError
from app.models import AnnouncementsResponse, CcassResponse, PriceHistoryResponse
from ccass_core.compute import AnalysisResult

AI_READ_MODEL_VERSION = "v0.1"


class AIReadModelSnapshotReference(BaseModel):
    snapshot_id: int | None = None
    snapshot_date: date | None = None
    data_as_of: date | None = None
    fetched_at: datetime | None = None
    source: str | None = None


class AIReadModelSurfaceReference(BaseModel):
    surface: str
    available: bool = True
    source: str | None = None
    source_type: str | None = None
    data_as_of: date | None = None
    fetched_at: datetime | None = None
    row_count: int | None = None


class AIReadModelIdentity(BaseModel):
    stock_code: str
    market: str = "HK"
    company_name: str | None = None


class AIReadModelTiming(BaseModel):
    data_as_of: date | None = None
    fetched_at: datetime | None = None
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class AIReadModelProvenance(BaseModel):
    source: str
    source_type: str
    primary_or_fallback: Literal["primary", "fallback", "unknown"] = "unknown"


class AIReadModelErrorState(BaseModel):
    code: str
    message: str
    retry_recommended: bool = False
    retry_after_seconds: int | None = None


class AIReadModelQuality(BaseModel):
    freshness_status: Literal["fresh", "cached", "stale", "partial", "unavailable", "unknown"] = (
        "unknown"
    )
    warnings: list[str] = Field(default_factory=list)
    error_state: AIReadModelErrorState | None = None


class AIReadModelComparisonContext(BaseModel):
    previous_available: bool = False
    previous_snapshot_id: int | None = None
    previous_snapshot_date: date | None = None
    change_count: int | None = None
    big_change_count: int | None = None
    note: str | None = None


class AIReadModelHistory(BaseModel):
    snapshot_id: int | None = None
    previous_snapshot: AIReadModelSnapshotReference | None = None
    comparison_context: AIReadModelComparisonContext | None = None


class AIReadModelContext(BaseModel):
    announcements: AIReadModelSurfaceReference | None = None
    price_reference: AIReadModelSurfaceReference | None = None
    company_information_references: list[AIReadModelSurfaceReference] = Field(default_factory=list)


class AIReadModelPayload(BaseModel):
    ccass: CcassResponse | None = None
    announcements: AnnouncementsResponse | None = None
    price_history: PriceHistoryResponse | None = None


class AIReadModelContractMeta(BaseModel):
    version: str = AI_READ_MODEL_VERSION
    surface: str


class AIReadModelV0_1(BaseModel):
    identity: AIReadModelIdentity
    timing: AIReadModelTiming
    provenance: AIReadModelProvenance
    quality: AIReadModelQuality
    history: AIReadModelHistory
    context: AIReadModelContext
    payload: AIReadModelPayload
    contract_meta: AIReadModelContractMeta

    @computed_field
    @property
    def version(self) -> str:
        return self.contract_meta.version


def build_ai_read_model_v0_1(
    *,
    code: str,
    response: CcassResponse | None,
    surface: str,
    analysis: AnalysisResult | None = None,
    previous_response: CcassResponse | None = None,
    snapshot_id: int | None = None,
    previous_snapshot_id: int | None = None,
    announcements: AnnouncementsResponse | None = None,
    price_history: PriceHistoryResponse | None = None,
    error: PlatformError | None = None,
    extra_warnings: Sequence[str] = (),
) -> AIReadModelV0_1:
    identity = AIReadModelIdentity(
        stock_code=code,
        company_name=response.metadata.name if response else None,
    )
    data_as_of = response.metadata.data_as_of if response else None
    fetched_at = response.metadata.fetched_at if response else None
    source_name = response.metadata.source_name if response else "unavailable"
    source_type = "ccass_holdings"
    primary_or_fallback = _primary_or_fallback(response)
    warnings = _collect_warnings(response, announcements, price_history)
    if analysis is not None:
        warnings.extend(analysis.warnings)
    warnings.extend(extra_warnings)
    warnings = list(dict.fromkeys(warnings))
    freshness_status = _freshness_status(
        response,
        announcements,
        price_history,
        error,
        analysis_warnings=analysis.warnings if analysis is not None else (),
        extra_warnings=extra_warnings,
    )
    error_state = (
        AIReadModelErrorState(
            code=str(error.code),
            message=error.message,
            retry_recommended=error.retry_recommended,
            retry_after_seconds=error.retry_after_seconds,
        )
        if error
        else None
    )
    previous_reference = (
        _snapshot_reference(previous_response, previous_snapshot_id)
        if previous_response
        else None
    )
    comparison_context = (
        AIReadModelComparisonContext(
            previous_available=analysis.previous_available,
            previous_snapshot_id=previous_snapshot_id,
            previous_snapshot_date=previous_response.metadata.data_as_of if previous_response else None,
            change_count=len(analysis.changes),
            big_change_count=len(analysis.big_changes),
            note=(
                "Previous snapshot available for comparison."
                if analysis.previous_available
                else "No previous snapshot was supplied for comparison."
            ),
        )
        if analysis
        else None
    )
    context = AIReadModelContext(
        announcements=_surface_reference(
            "announcements",
            announcements,
            source_type="company_announcements",
        ),
        price_reference=_surface_reference(
            "price_history",
            price_history,
            source_type="market_price",
        ),
        company_information_references=[
            AIReadModelSurfaceReference(
                surface="announcements",
                available=announcements is not None,
                source=announcements.metadata.source_name if announcements else None,
                source_type="company_announcements",
                data_as_of=announcements.metadata.data_as_of if announcements else None,
                fetched_at=announcements.metadata.fetched_at if announcements else None,
                row_count=len(announcements.announcements) if announcements else None,
            ),
            AIReadModelSurfaceReference(
                surface="stock_events",
                available=False,
                source=None,
                source_type="company_information",
            ),
            AIReadModelSurfaceReference(
                surface="officers",
                available=False,
                source=None,
                source_type="company_information",
            ),
        ],
    )
    payload = AIReadModelPayload(
        ccass=response,
        announcements=announcements,
        price_history=price_history,
    )
    return AIReadModelV0_1(
        identity=identity,
        timing=AIReadModelTiming(data_as_of=data_as_of, fetched_at=fetched_at),
        provenance=AIReadModelProvenance(
            source=source_name,
            source_type=source_type,
            primary_or_fallback=primary_or_fallback,
        ),
        quality=AIReadModelQuality(
            freshness_status=freshness_status,
            warnings=warnings,
            error_state=error_state,
        ),
        history=AIReadModelHistory(
            snapshot_id=snapshot_id,
            previous_snapshot=previous_reference,
            comparison_context=comparison_context,
        ),
        context=context,
        payload=payload,
        contract_meta=AIReadModelContractMeta(surface=surface),
    )


def _snapshot_reference(
    response: CcassResponse | None,
    snapshot_id: int | None,
) -> AIReadModelSnapshotReference | None:
    if response is None:
        return None
    return AIReadModelSnapshotReference(
        snapshot_id=snapshot_id,
        snapshot_date=response.metadata.data_as_of,
        data_as_of=response.metadata.data_as_of,
        fetched_at=response.metadata.fetched_at,
        source=response.metadata.source_name,
    )


def _surface_reference(
    surface: str,
    response: AnnouncementsResponse | PriceHistoryResponse | None,
    *,
    source_type: str,
) -> AIReadModelSurfaceReference | None:
    if response is None:
        return None
    metadata = response.metadata
    row_count = len(response.announcements) if isinstance(response, AnnouncementsResponse) else len(response.prices)
    return AIReadModelSurfaceReference(
        surface=surface,
        available=True,
        source=metadata.source_name,
        source_type=source_type,
        data_as_of=metadata.data_as_of,
        fetched_at=metadata.fetched_at,
        row_count=row_count,
    )


def _collect_warnings(
    response: CcassResponse | None,
    announcements: AnnouncementsResponse | None,
    price_history: PriceHistoryResponse | None,
) -> list[str]:
    warnings: list[str] = []
    if response is not None:
        warnings.extend(response.data_quality_warnings)
    if announcements is not None:
        warnings.extend(announcements.data_quality_warnings)
    if price_history is not None:
        warnings.extend(price_history.data_quality_warnings)
    return list(dict.fromkeys(warnings))


def context_unavailable_warning(surface: str, message: str) -> str:
    return structured_warning("SOURCE_STATUS", f"{surface.upper()}_UNAVAILABLE", message)


def _freshness_status(
    response: CcassResponse | None,
    announcements: AnnouncementsResponse | None,
    price_history: PriceHistoryResponse | None,
    error: PlatformError | None,
    *,
    analysis_warnings: Sequence[str] = (),
    extra_warnings: Sequence[str] = (),
) -> str:
    if error is not None or response is None:
        return "unavailable"
    warnings = _collect_warnings(response, announcements, price_history)
    warnings.extend(analysis_warnings)
    warnings.extend(extra_warnings)
    warnings = list(dict.fromkeys(warnings))
    warning_codes = {code for code in (warning_code(warning) for warning in warnings) if code}
    if "CSV_FALLBACK_USED" in warning_codes or response.metadata.cached:
        return "cached"
    if any(code in {"STALE_DATA", "CACHED_SNAPSHOT"} for code in warning_codes):
        return "stale"
    if any(code in {"PARTIAL_DATA", "MISSING_ROWS"} or code.endswith("_UNAVAILABLE") for code in warning_codes):
        return "partial"
    return "fresh"


def _primary_or_fallback(response: CcassResponse | None) -> Literal["primary", "fallback", "unknown"]:
    if response is None:
        return "unknown"
    source_name = response.metadata.source_name.casefold()
    if response.metadata.cached:
        return "fallback"
    if "csv_fallback_used" in " ".join(response.data_quality_warnings).casefold():
        return "fallback"
    if "google drive csv" in source_name:
        return "fallback"
    return "primary"


def _source_id(source_name: str) -> str:
    lowered = source_name.strip().lower()
    if lowered == "google drive csv":
        return "google_drive_csv"
    if "webb-site" in lowered or "webbsite" in lowered:
        return "webbsite_mirror"
    normalized = re.sub(r"[^a-z0-9_-]+", "_", lowered).strip("_")
    return normalized[:64] or "unknown_source"
