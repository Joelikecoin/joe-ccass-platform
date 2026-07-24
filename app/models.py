from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field, computed_field


class SourceMetadata(BaseModel):
    code: str
    name: str | None = None
    issue_id: int
    holdings_date: date | None = None
    fetched_at: datetime
    source_url: str
    source_name: str = "Webb-site mirror"
    cached: bool = False
    settlement_note: str = (
        "CCASS is settlement-layer nominee data and normally reflects T+2; "
        "recent trades may not yet be reflected."
    )
    attribution: str = (
        "Data from Renavon/Webb-site mirror, originally compiled by Webb-site.com | CC-BY 4.0"
    )


class HoldingRow(BaseModel):
    rank: int
    participant_id: str
    participant: str
    shares: int
    last_change: date | None = None
    pct_of_issued: float
    pct_of_ccass: float | None = None
    cumulative_pct_of_issued: float | None = None
    participant_category: str | None = None

    @computed_field
    @property
    def participant_name(self) -> str:
        """Canonical name while preserving the legacy ``participant`` field."""
        return self.participant


class HoldingsSummary(BaseModel):
    total_in_ccass_shares: int | None = None
    total_in_ccass_pct_of_issued: float | None = None
    issued_shares: int | None = None
    issued_shares_as_of: date | None = None
    non_ccass_shares: int | None = None
    non_ccass_pct_of_issued: float | None = None
    participant_count: int = 0
    top5_pct_of_issued: float | None = None
    top10_pct_of_issued: float | None = None
    top5_pct_of_ccass: float | None = None
    top10_pct_of_ccass: float | None = None


class CcassResponse(BaseModel):
    metadata: SourceMetadata
    holdings_summary: HoldingsSummary
    holdings: list[HoldingRow] = Field(default_factory=list)
    data_quality_warnings: list[str] = Field(default_factory=list)


class ChangesSourceMetadata(BaseModel):
    source_id: str
    source_name: str
    safe_identifier: str
    issue_id: int
    fetched_at: datetime
    parser_version: str
    schema_version: int
    checksum_sha256: str
    attribution: str
    issued_shares: int = Field(gt=0)
    issued_shares_as_of: date
    cached: bool
    stale: bool
    partial: bool


class ChangesMetadata(BaseModel):
    code: str
    name: str | None = None
    issue_id: int
    compare_date: date
    snapshot_date: date
    percentage_basis: Literal["issued_shares"] = "issued_shares"
    compare_source: ChangesSourceMetadata
    snapshot_source: ChangesSourceMetadata
    settlement_note: str


class ChangeRow(BaseModel):
    participant_id: str
    participant: str
    shares_before: int = Field(ge=0)
    shares_after: int = Field(ge=0)
    shares_change: int
    percent_before: float = Field(ge=0)
    percent_after: float = Field(ge=0)
    percent_change: float
    relative_change_percent: float | None = None
    new_participant: bool = False
    removed_participant: bool = False
    status: Literal["new", "removed", "increased", "decreased", "unchanged"]


class ChangesSummary(BaseModel):
    participant_count: int = Field(ge=0)
    changed_count: int = Field(ge=0)
    new_count: int = Field(ge=0)
    removed_count: int = Field(ge=0)
    increased_count: int = Field(ge=0)
    decreased_count: int = Field(ge=0)
    unchanged_count: int = Field(ge=0)


class ChangesDiagnostics(BaseModel):
    validation_status: Literal["COMPLETE"] = "COMPLETE"
    compare_snapshot_complete: bool = True
    snapshot_complete: bool = True
    identity_match: bool = True
    exact_dates: bool = True
    stale_data_used: bool = False


class ChangesResponse(BaseModel):
    metadata: ChangesMetadata
    summary: ChangesSummary
    changes: list[ChangeRow] = Field(default_factory=list)
    diagnostics: ChangesDiagnostics
    data_quality_warnings: list[str] = Field(default_factory=list)


class BigChangesSummary(BaseModel):
    threshold_shares: int = Field(gt=0)
    participants_compared: int = Field(ge=0)
    changed_participants_considered: int = Field(ge=0)
    big_changes_count: int = Field(ge=0)
    new_count: int = Field(ge=0)
    removed_count: int = Field(ge=0)
    increased_count: int = Field(ge=0)
    decreased_count: int = Field(ge=0)


class BigChangesResponse(BaseModel):
    metadata: ChangesMetadata
    summary: BigChangesSummary
    big_changes: list[ChangeRow] = Field(default_factory=list)
    diagnostics: ChangesDiagnostics
    data_quality_warnings: list[str] = Field(default_factory=list)


class ConcentrationMetadata(BaseModel):
    code: str
    name: str | None = None
    issue_id: int
    snapshot_date: date
    percentage_basis: Literal["issued_shares"] = "issued_shares"
    snapshot_source: ChangesSourceMetadata
    settlement_note: str


class ConcentrationSummary(BaseModel):
    participant_count: int = Field(ge=0)
    total_tracked_shares: int = Field(ge=0)
    total_tracked_pct_of_issued: float = Field(ge=0)
    total_tracked_pct_of_ccass: float = Field(ge=0)
    top1_pct_of_issued: float = Field(ge=0)
    top1_pct_of_ccass: float = Field(ge=0)
    top5_pct_of_issued: float = Field(ge=0)
    top5_pct_of_ccass: float = Field(ge=0)
    top10_pct_of_issued: float = Field(ge=0)
    top10_pct_of_ccass: float = Field(ge=0)


class ConcentrationDiagnostics(BaseModel):
    validation_status: Literal["COMPLETE"] = "COMPLETE"
    snapshot_complete: bool = True
    identity_match: bool = True
    exact_date: bool = True
    stale_data_used: bool = False


class ConcentrationResponse(BaseModel):
    metadata: ConcentrationMetadata
    summary: ConcentrationSummary
    participant_ranking: list[HoldingRow] = Field(default_factory=list)
    top_holders: list[HoldingRow] = Field(default_factory=list)
    diagnostics: ConcentrationDiagnostics
    data_quality_warnings: list[str] = Field(default_factory=list)
