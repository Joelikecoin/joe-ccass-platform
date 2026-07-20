from datetime import date, datetime

from pydantic import BaseModel, Field


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
    cumulative_pct_of_issued: float | None = None
    participant_category: str | None = None


class HoldingsSummary(BaseModel):
    total_in_ccass_shares: int | None = None
    total_in_ccass_pct_of_issued: float | None = None
    issued_shares: int | None = None
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
