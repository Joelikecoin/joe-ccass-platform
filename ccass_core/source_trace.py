from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.data_quality import structured_warning


GatewayRoute = Literal["cache", "existing_service"]
GatewaySourceStatus = Literal[
    "active",
    "fallback",
    "disabled",
    "unverified",
    "unavailable",
    "cached",
    "unknown",
]
CCASS_SOURCE_DATE_TYPE = "holdings_date"
CCASS_DATE_CONVENTION_REFERENCE = "ccass_holdings_date_v1"


class SourceTraceIdentity(BaseModel):
    model_config = ConfigDict(frozen=True)

    source_id: str
    source_name: str | None = None
    source_url: str | None = None
    source_status: GatewaySourceStatus = "unknown"


class SourceTraceSelection(BaseModel):
    model_config = ConfigDict(frozen=True)

    selected_source_id: str | None = None
    selected_source_name: str | None = None
    selected_source_status: GatewaySourceStatus = "unknown"
    attempted_sources: tuple[str, ...] = ()
    attempted_statuses: tuple[GatewaySourceStatus, ...] = ()
    fallback_reason: str | None = None
    source_candidates: tuple[str, ...] = ()


class SourceDateGovernanceReference(BaseModel):
    model_config = ConfigDict(frozen=True)

    source_date_type: Literal["holdings_date", "unknown"] = CCASS_SOURCE_DATE_TYPE
    date_convention_reference: str = CCASS_DATE_CONVENTION_REFERENCE


@dataclass(frozen=True, slots=True)
class SourceDateValidationResult:
    source_date_type: Literal["holdings_date", "unknown"]
    date_convention_reference: str
    warnings: tuple[str, ...] = ()
    notes: tuple[str, ...] = ()
    is_consistent: bool = True


class SourceTraceView(BaseModel):
    model_config = ConfigDict(frozen=True)

    request_id: str
    request_surface: str
    route: GatewayRoute
    cache_first: bool
    cache_usage_state: Literal["cached", "miss", "not_used", "unknown"] = "unknown"
    source_identity: SourceTraceIdentity
    selection: SourceTraceSelection = Field(default_factory=SourceTraceSelection)
    fetched_at: datetime | None = None
    data_as_of: date | None = None
    date_governance: SourceDateGovernanceReference = Field(
        default_factory=SourceDateGovernanceReference
    )
    authoritative: bool = False
    notes: tuple[str, ...] = ()


def build_source_trace_view(gateway_response: Any) -> SourceTraceView:
    trace = getattr(gateway_response, "source_trace", None)
    response = getattr(gateway_response, "normalized_response", None)
    if trace is None or response is None:
        raise ValueError("gateway_response must provide source_trace and normalized_response")

    metadata = response.metadata
    selected_source_id = trace.selected_source_id
    cache_usage_state = _cache_usage_state(trace, metadata)
    return SourceTraceView(
        request_id=trace.request_id,
        request_surface=trace.request_surface,
        route=trace.route,
        cache_first=trace.cache_first,
        cache_usage_state=cache_usage_state,
        source_identity=SourceTraceIdentity(
            source_id=_source_identity_id(trace, metadata),
            source_name=trace.source_name or metadata.source_name,
            source_url=trace.source_url or metadata.source_url,
            source_status=trace.selected_source_status,
        ),
        selection=SourceTraceSelection(
            selected_source_id=selected_source_id,
            selected_source_name=trace.selected_source_name,
            selected_source_status=trace.selected_source_status,
            attempted_sources=tuple(trace.attempted_sources),
            attempted_statuses=tuple(trace.attempted_statuses),
            fallback_reason=trace.fallback_reason,
            source_candidates=tuple(trace.source_candidates),
        ),
        fetched_at=metadata.fetched_at,
        data_as_of=metadata.data_as_of,
        date_governance=SourceDateGovernanceReference(
            source_date_type=trace.source_date_type,
            date_convention_reference=trace.date_convention_reference,
        ),
        authoritative=bool(getattr(trace, "authoritative", False)),
        notes=tuple(getattr(trace, "notes", ())),
    )


def validate_ccass_date_convention(
    source_trace: SourceTraceView | None,
    *,
    data_as_of: date | None = None,
) -> SourceDateValidationResult:
    if source_trace is None:
        return SourceDateValidationResult(
            source_date_type="unknown",
            date_convention_reference="",
            warnings=(
                structured_warning(
                    "CCASS_DATE_CONVENTION",
                    "CCASS_DATE_TRACE_MISSING",
                    "CCASS date governance trace is unavailable.",
                ),
            ),
            notes=("date_trace_missing",),
            is_consistent=False,
        )

    warnings: list[str] = []
    notes: list[str] = []
    reference = source_trace.date_governance
    source_date_type = reference.source_date_type
    date_convention_reference = reference.date_convention_reference
    consistent = True

    if source_date_type != CCASS_SOURCE_DATE_TYPE:
        consistent = False
        notes.append("source_date_type_inconsistent")
        warnings.append(
            structured_warning(
                "CCASS_DATE_CONVENTION",
                "CCASS_SOURCE_DATE_TYPE_INCONSISTENT",
                f"Expected {CCASS_SOURCE_DATE_TYPE} but received {source_date_type}.",
            )
        )

    if not date_convention_reference:
        consistent = False
        notes.append("date_convention_reference_missing")
        warnings.append(
            structured_warning(
                "CCASS_DATE_CONVENTION",
                "CCASS_DATE_CONVENTION_REFERENCE_MISSING",
                "CCASS date convention reference is missing.",
            )
        )
    elif date_convention_reference != CCASS_DATE_CONVENTION_REFERENCE:
        consistent = False
        notes.append("date_convention_reference_inconsistent")
        warnings.append(
            structured_warning(
                "CCASS_DATE_CONVENTION",
                "CCASS_DATE_CONVENTION_REFERENCE_INCONSISTENT",
                f"Expected {CCASS_DATE_CONVENTION_REFERENCE} but received {date_convention_reference}.",
            )
        )

    if data_as_of is None:
        consistent = False
        notes.append("data_as_of_missing")
        warnings.append(
            structured_warning(
                "CCASS_DATE_CONVENTION",
                "CCASS_DATA_AS_OF_MISSING",
                "CCASS data_as_of is unavailable.",
            )
        )
    elif source_trace.data_as_of is None:
        consistent = False
        notes.append("source_trace_data_as_of_missing")
        warnings.append(
            structured_warning(
                "CCASS_DATE_CONVENTION",
                "CCASS_SOURCE_TRACE_DATA_AS_OF_MISSING",
                "Source trace data_as_of is unavailable.",
            )
        )
    elif source_trace.data_as_of != data_as_of:
        consistent = False
        notes.append("data_as_of_inconsistent")
        warnings.append(
            structured_warning(
                "CCASS_DATE_CONVENTION",
                "CCASS_DATA_AS_OF_INCONSISTENT",
                f"Expected {data_as_of.isoformat()} but received {source_trace.data_as_of.isoformat()}.",
            )
        )

    return SourceDateValidationResult(
        source_date_type=source_date_type,
        date_convention_reference=date_convention_reference,
        warnings=tuple(warnings),
        notes=tuple(notes),
        is_consistent=consistent,
    )


def build_source_trace_markdown(source_trace: SourceTraceView) -> str:
    selection = source_trace.selection
    attempted = _join_attempts(selection.attempted_sources, selection.attempted_statuses)
    rows: list[tuple[str, str]] = [
        ("Source identity", _source_identity_text(source_trace.source_identity)),
        ("Source status", source_trace.source_identity.source_status),
        ("Selected source", _selected_source_text(selection)),
        ("Attempted sources", attempted),
        ("Fallback reason", selection.fallback_reason or "N/A"),
        ("Cache usage state", source_trace.cache_usage_state),
        ("Fetched at", _format_value(source_trace.fetched_at)),
        ("Data as of", _format_value(source_trace.data_as_of)),
        ("Source date type", source_trace.date_governance.source_date_type),
        ("Date convention reference", _date_governance_text(source_trace.date_governance)),
        ("Authoritative", "Yes" if source_trace.authoritative else "No"),
    ]
    lines = [
        "### Source Trace",
        "",
        "| Metric | Value |",
        "|---|---|",
    ]
    lines.extend(f"| {metric} | {value} |" for metric, value in rows)
    if source_trace.notes:
        lines.extend(["", "Notes:"])
        lines.extend(f"- {note}" for note in source_trace.notes)
    return "\n".join(lines)


def _cache_usage_state(trace: Any, metadata: Any) -> Literal["cached", "miss", "not_used", "unknown"]:
    if getattr(trace, "route", None) == "cache":
        return "cached"
    if getattr(trace, "cache_hit", False) or getattr(metadata, "cached", False):
        return "cached"
    if getattr(trace, "cache_first", False):
        return "miss"
    return "not_used"


def _source_identity_id(trace: Any, metadata: Any) -> str:
    if getattr(metadata, "source_name", None):
        return _slugify(str(metadata.source_name))
    if getattr(trace, "selected_source_id", None):
        return str(trace.selected_source_id)
    return "unknown"


def _join_attempts(
    attempted_sources: tuple[str, ...],
    attempted_statuses: tuple[GatewaySourceStatus, ...],
) -> str:
    if not attempted_sources:
        return "N/A"
    values = []
    for index, source_id in enumerate(attempted_sources):
        status = attempted_statuses[index] if index < len(attempted_statuses) else "unknown"
        values.append(f"{source_id} ({status})")
    return ", ".join(values)


def _source_identity_text(identity: SourceTraceIdentity) -> str:
    parts = [identity.source_id]
    if identity.source_name:
        parts.append(identity.source_name)
    if identity.source_url:
        parts.append(identity.source_url)
    return " / ".join(parts)


def _selected_source_text(selection: SourceTraceSelection) -> str:
    if selection.selected_source_id is None:
        return "N/A"
    parts = [selection.selected_source_id]
    if selection.selected_source_name:
        parts.append(selection.selected_source_name)
    parts.append(selection.selected_source_status)
    return " / ".join(parts)


def _date_governance_text(date_governance: SourceDateGovernanceReference) -> str:
    return f"{date_governance.source_date_type} / {date_governance.date_convention_reference}"


def _format_value(value: date | datetime | None) -> str:
    if value is None:
        return "N/A"
    return value.isoformat()


def _slugify(value: str) -> str:
    cleaned = [
        character.lower() if character.isalnum() else "_"
        for character in value.strip()
    ]
    slug = "".join(cleaned).strip("_")
    while "__" in slug:
        slug = slug.replace("__", "_")
    return slug or "unknown"
