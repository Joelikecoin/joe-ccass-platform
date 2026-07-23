import hashlib
import json
import re
from datetime import UTC, date, datetime
from typing import Literal
from urllib.parse import urlsplit, urlunsplit

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models import CcassResponse, HoldingRow, HoldingsSummary, SourceMetadata

SOURCE_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")


class StockIdentity(BaseModel):
    model_config = ConfigDict(frozen=True)

    code: str = Field(pattern=r"^\d{5}$")
    name: str | None = None
    market: str = "HK"


class SourceIdentity(BaseModel):
    model_config = ConfigDict(frozen=True)

    source_id: str
    safe_identifier: str
    issue_id: int
    display_name: str

    @model_validator(mode="after")
    def validate_source_id(self) -> "SourceIdentity":
        if not SOURCE_ID_PATTERN.fullmatch(self.source_id):
            raise ValueError("source_id must be a stable lowercase identifier")
        return self


class RawProvenance(BaseModel):
    model_config = ConfigDict(frozen=True)

    source_id: str
    safe_reference: str
    checksum_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    fetched_at: datetime
    content_type: str = "application/vnd.joe-ccass.normalized+json"
    byte_size: int = Field(ge=0)


class NormalizedHolding(BaseModel):
    model_config = ConfigDict(frozen=True)

    participant_id: str = Field(min_length=1)
    participant_name: str = Field(min_length=1)
    rank: int = Field(gt=0)
    shares: int = Field(ge=0)
    last_change: date | None = None
    pct_of_issued: float = Field(ge=0)
    pct_of_ccass: float | None = Field(default=None, ge=0)
    cumulative_pct_of_issued: float | None = Field(default=None, ge=0)
    participant_category: str | None = None

    @classmethod
    def from_response_row(
        cls, row: HoldingRow, *, total_in_ccass_shares: int | None
    ) -> "NormalizedHolding":
        pct_of_ccass = (
            round(row.shares / total_in_ccass_shares * 100, 6) if total_in_ccass_shares else None
        )
        return cls(
            participant_id=row.participant_id,
            participant_name=row.participant,
            rank=row.rank,
            shares=row.shares,
            last_change=row.last_change,
            pct_of_issued=row.pct_of_issued,
            pct_of_ccass=pct_of_ccass,
            cumulative_pct_of_issued=row.cumulative_pct_of_issued,
            participant_category=row.participant_category,
        )

    def to_response_row(self) -> HoldingRow:
        return HoldingRow(
            rank=self.rank,
            participant_id=self.participant_id,
            participant=self.participant_name,
            shares=self.shares,
            last_change=self.last_change,
            pct_of_issued=self.pct_of_issued,
            cumulative_pct_of_issued=self.cumulative_pct_of_issued,
            participant_category=self.participant_category,
        )


class HistoricalSnapshot(BaseModel):
    model_config = ConfigDict(frozen=True)

    stock: StockIdentity
    source: SourceIdentity
    snapshot_date: date
    fetched_at: datetime
    cached: bool = False
    stale: bool = False
    partial: bool = False
    warnings: tuple[str, ...] = ()
    parser_version: str = "ccass-response-v1"
    schema_version: int = Field(default=1, ge=1)
    issued_shares: int | None = Field(default=None, ge=0)
    issued_shares_as_of: date | None = None
    denominator: str = "issued_shares"
    total_in_ccass_shares: int | None = Field(default=None, ge=0)
    total_in_ccass_pct_of_issued: float | None = Field(default=None, ge=0)
    non_ccass_shares: int | None = Field(default=None, ge=0)
    non_ccass_pct_of_issued: float | None = Field(default=None, ge=0)
    participant_count: int = Field(ge=0)
    top5_pct_of_issued: float | None = Field(default=None, ge=0)
    top10_pct_of_issued: float | None = Field(default=None, ge=0)
    top5_pct_of_ccass: float | None = Field(default=None, ge=0)
    top10_pct_of_ccass: float | None = Field(default=None, ge=0)
    settlement_note: str
    attribution: str
    holdings: tuple[NormalizedHolding, ...]
    provenance: RawProvenance

    @model_validator(mode="after")
    def validate_snapshot(self) -> "HistoricalSnapshot":
        participant_ids = [row.participant_id for row in self.holdings]
        if len(participant_ids) != len(set(participant_ids)):
            raise ValueError("snapshot contains duplicate participant IDs")
        ranks = [row.rank for row in self.holdings]
        if len(ranks) != len(set(ranks)):
            raise ValueError("snapshot contains duplicate ranks")
        if not self.partial and len(self.holdings) != self.participant_count:
            raise ValueError("complete snapshot must contain every participant row")
        if self.partial and len(self.holdings) > self.participant_count:
            raise ValueError("partial snapshot cannot exceed participant_count")
        if self.issued_shares_as_of and self.issued_shares is None:
            raise ValueError("issued_shares_as_of requires issued_shares")
        return self

    @classmethod
    def from_response(
        cls,
        response: CcassResponse,
        *,
        source_id: str | None = None,
        stale: bool = False,
        partial: bool | None = None,
        parser_version: str = "ccass-response-v1",
        schema_version: int = 1,
        issued_shares_as_of: date | None = None,
        provenance_bytes: bytes | None = None,
        provenance_reference: str | None = None,
    ) -> "HistoricalSnapshot":
        metadata = response.metadata
        if metadata.holdings_date is None:
            raise ValueError("historical snapshot requires a holdings_date")
        normalized_source_id = source_id or _source_id(metadata.source_name)
        safe_identifier = _safe_identifier(metadata.source_url)
        payload = provenance_bytes or _canonical_response_bytes(response)
        holdings = tuple(
            NormalizedHolding.from_response_row(
                row,
                total_in_ccass_shares=response.holdings_summary.total_in_ccass_shares,
            )
            for row in response.holdings
        )
        inferred_partial = len(holdings) != response.holdings_summary.participant_count
        return cls(
            stock=StockIdentity(code=metadata.code, name=metadata.name),
            source=SourceIdentity(
                source_id=normalized_source_id,
                safe_identifier=safe_identifier,
                issue_id=metadata.issue_id,
                display_name=metadata.source_name,
            ),
            snapshot_date=metadata.holdings_date,
            fetched_at=metadata.fetched_at,
            cached=metadata.cached,
            stale=stale,
            partial=inferred_partial if partial is None else partial,
            warnings=tuple(response.data_quality_warnings),
            parser_version=parser_version,
            schema_version=schema_version,
            issued_shares=response.holdings_summary.issued_shares,
            issued_shares_as_of=issued_shares_as_of,
            total_in_ccass_shares=response.holdings_summary.total_in_ccass_shares,
            total_in_ccass_pct_of_issued=(response.holdings_summary.total_in_ccass_pct_of_issued),
            non_ccass_shares=response.holdings_summary.non_ccass_shares,
            non_ccass_pct_of_issued=response.holdings_summary.non_ccass_pct_of_issued,
            participant_count=response.holdings_summary.participant_count,
            top5_pct_of_issued=response.holdings_summary.top5_pct_of_issued,
            top10_pct_of_issued=response.holdings_summary.top10_pct_of_issued,
            top5_pct_of_ccass=response.holdings_summary.top5_pct_of_ccass,
            top10_pct_of_ccass=response.holdings_summary.top10_pct_of_ccass,
            settlement_note=metadata.settlement_note,
            attribution=metadata.attribution,
            holdings=holdings,
            provenance=RawProvenance(
                source_id=normalized_source_id,
                safe_reference=_safe_identifier(provenance_reference or safe_identifier),
                checksum_sha256=hashlib.sha256(payload).hexdigest(),
                fetched_at=metadata.fetched_at,
                byte_size=len(payload),
            ),
        )

    def to_response(self) -> CcassResponse:
        warnings = list(self.warnings)
        if self.stale and not any("stale" in warning.lower() for warning in warnings):
            warnings.append("Stored snapshot is marked stale.")
        if self.partial and not any("partial" in warning.lower() for warning in warnings):
            warnings.append("Stored snapshot is partial; missing participant rows remain absent.")
        return CcassResponse(
            metadata=SourceMetadata(
                code=self.stock.code,
                name=self.stock.name,
                issue_id=self.source.issue_id,
                holdings_date=self.snapshot_date,
                fetched_at=self.fetched_at,
                source_url=self.source.safe_identifier,
                source_name=self.source.display_name,
                cached=self.cached,
                settlement_note=self.settlement_note,
                attribution=self.attribution,
            ),
            holdings_summary=HoldingsSummary(
                total_in_ccass_shares=self.total_in_ccass_shares,
                total_in_ccass_pct_of_issued=self.total_in_ccass_pct_of_issued,
                issued_shares=self.issued_shares,
                non_ccass_shares=self.non_ccass_shares,
                non_ccass_pct_of_issued=self.non_ccass_pct_of_issued,
                participant_count=self.participant_count,
                top5_pct_of_issued=self.top5_pct_of_issued,
                top10_pct_of_issued=self.top10_pct_of_issued,
                top5_pct_of_ccass=self.top5_pct_of_ccass,
                top10_pct_of_ccass=self.top10_pct_of_ccass,
            ),
            holdings=[row.to_response_row() for row in self.holdings],
            data_quality_warnings=warnings,
        )


class CollectorRunRecord(BaseModel):
    run_id: int | None = None
    started_at: datetime
    completed_at: datetime | None = None
    status: str
    source_id: str
    requested_codes: tuple[str, ...] = ()
    success_count: int = Field(default=0, ge=0)
    partial_count: int = Field(default=0, ge=0)
    error_count: int = Field(default=0, ge=0)
    safe_details: dict[str, str | int | bool | None] = Field(default_factory=dict)


class CollectorRunItemRecord(BaseModel):
    run_id: int = Field(gt=0)
    stock_code: str = Field(pattern=r"^\d{5}$")
    status: Literal["SUCCESS", "PARTIAL", "ERROR"]
    source_id: str
    snapshot_id: int | None = Field(default=None, gt=0)
    snapshot_date: date | None = None
    partial: bool = False
    safe_details: dict[str, str | int | bool | None] = Field(default_factory=dict)


class BackfillRunRecord(BaseModel):
    run_id: int | None = None
    stock_code: str = Field(pattern=r"^\d{5}$")
    source_id: str
    requested_dates: tuple[date, ...]
    started_at: datetime
    requested_from: date | None = None
    requested_to: date | None = None
    latest_count: int | None = Field(default=None, gt=0)
    cursor_date: date | None = None
    completed_at: datetime | None = None
    status: Literal["RUNNING", "SUCCESS", "PARTIAL", "ERROR"] = "RUNNING"
    success_count: int = Field(default=0, ge=0)
    partial_count: int = Field(default=0, ge=0)
    error_count: int = Field(default=0, ge=0)
    skipped_count: int = Field(default=0, ge=0)
    safe_details: dict[str, str | int | bool | None] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_requested_dates(self) -> "BackfillRunRecord":
        if not self.requested_dates:
            raise ValueError("backfill run requires at least one requested date")
        if tuple(sorted(set(self.requested_dates))) != self.requested_dates:
            raise ValueError("backfill requested dates must be unique and sorted")
        return self


class BackfillRunItemRecord(BaseModel):
    run_id: int = Field(gt=0)
    requested_date: date
    status: Literal["SUCCESS", "PARTIAL", "ERROR", "SKIPPED"]
    source_id: str
    snapshot_id: int | None = Field(default=None, gt=0)
    partial: bool = False
    error_code: str | None = None
    safe_message: str | None = None
    retry_recommended: bool = False
    safe_details: dict[str, str | int | bool | None] = Field(default_factory=dict)


class SourceErrorRecord(BaseModel):
    error_id: int | None = None

    run_id: int | None = None
    source_id: str
    stock_code: str | None = Field(default=None, pattern=r"^\d{5}$")
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    error_code: str
    safe_message: str
    retry_recommended: bool = False
    retry_after_seconds: int | None = Field(default=None, ge=0)
    safe_details: dict[str, str | int | bool | None] = Field(default_factory=dict)


def _source_id(source_name: str) -> str:
    lowered = source_name.strip().lower()
    if lowered == "google drive csv":
        return "google_drive_csv"
    if "webb-site" in lowered or "webbsite" in lowered:
        return "webbsite_mirror"
    normalized = re.sub(r"[^a-z0-9_-]+", "_", lowered).strip("_")
    return normalized[:64] or "unknown_source"


def _safe_identifier(value: str) -> str:
    parsed = urlsplit(value)
    if parsed.scheme in {"http", "https"} and parsed.hostname:
        return urlunsplit((parsed.scheme, parsed.netloc, parsed.path or "/", "", ""))
    return value.split("?", 1)[0][:512]


def _canonical_response_bytes(response: CcassResponse) -> bytes:
    payload = response.model_dump(mode="json")
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
