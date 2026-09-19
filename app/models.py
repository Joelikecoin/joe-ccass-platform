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

    @computed_field
    @property
    def data_as_of(self) -> date | None:
        return self.holdings_date


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
    # Export contract version.  Keep this literal so incompatible payloads fail
    # validation instead of being silently interpreted as the current schema.
    schema_version: Literal[1] = 1
    metadata: SourceMetadata
    holdings_summary: HoldingsSummary
    holdings: list[HoldingRow] = Field(default_factory=list)
    data_quality_warnings: list[str] = Field(default_factory=list)
    fetch_summary: str | None = None
    errors: list[str] = Field(default_factory=list)
    changes: "ChangesResponse | None" = None
    big_changes: "BigChangesResponse | None" = None
    concentration: "ConcentrationResponse | None" = None
    price_history: "PriceHistoryResponse | None" = None
    announcements: "AnnouncementsResponse | None" = None
    stock_events: "StockEventsResponse | None" = None
    capital_information: "CapitalInformationResponse | None" = None
    officers: "OfficersResponse | None" = None


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

    @computed_field
    @property
    def data_as_of(self) -> date:
        return self.issued_shares_as_of


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
    source_status: Literal["local_derived", "unavailable"] = "unavailable"
    authority_status: Literal["exact_persisted", "local_history_limited", "unavailable"] = "unavailable"
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


class PriceHistoryRow(BaseModel):
    price_date: date
    open: float | None = None
    high: float | None = None
    low: float | None = None
    close: float | None = None
    vwap: float | None = None
    adjusted_close: float | None = None
    volume: int | None = None
    turnover: float | None = None
    price_source: str | None = None
    turnover_est: float | None = None
    vwap_est: float | None = None


class PriceHistoryMetadata(BaseModel):
    code: str
    name: str | None = None
    ticker: str
    price_date_from: date
    price_date_to: date
    source_name: str
    source_url: str
    fetched_at: datetime
    adjustment_state: Literal["adjusted", "unadjusted"] = "adjusted"
    currency: str | None = None
    adjustment_note: str | None = None

    @computed_field
    @property
    def data_as_of(self) -> date:
        return self.price_date_to


class PriceHistoryResponse(BaseModel):
    metadata: PriceHistoryMetadata
    prices: list[PriceHistoryRow] = Field(default_factory=list)
    data_quality_warnings: list[str] = Field(default_factory=list)


class AnnouncementRow(BaseModel):
    announcement_date: date
    title: str
    source: str
    link: str | None = None
    publication_datetime: datetime | None = None
    category: str | None = None
    long_text: str | None = None
    language: str | None = None
    document_id: str | None = None
    file_type: str | None = None
    file_info: str | None = None
    retrieval_status: str = "metadata"


class AnnouncementsMetadata(BaseModel):
    code: str
    name: str | None = None
    source_name: str
    source_url: str
    fetched_at: datetime
    earliest_announcement_date: date | None = None
    latest_announcement_date: date | None = None
    announcement_count: int = 0
    coverage_start: date | None = None
    coverage_end: date | None = None
    source_status: str = "ready"
    document_access_status: str = "links_available"
    cached: bool = False

    @computed_field
    @property
    def data_as_of(self) -> date | None:
        return self.latest_announcement_date


class AnnouncementsResponse(BaseModel):
    metadata: AnnouncementsMetadata
    announcements: list[AnnouncementRow] = Field(default_factory=list)
    data_quality_warnings: list[str] = Field(default_factory=list)


class CorporateEvidence(BaseModel):
    event_id: str
    stock_code: str
    event_date: date
    event_type: str
    title: str
    source: str
    source_url: str | None = None
    evidence_status: str = "verified"
    retrieved_at: datetime


class CorporateTimeline(BaseModel):
    stock_code: str
    start_date: date
    end_date: date
    events: list[CorporateEvidence] = Field(default_factory=list)


class DisclosureInterestRow(BaseModel):
    filing_id: str
    stock_code: str
    event_date: date
    filer: str
    classification: str
    shares_involved: int | None = None
    previous_balance: int | None = None
    present_balance: int | None = None
    percentage: float | None = None
    average_price: float | None = None
    reason: str | None = None
    source_url: str
    retrieved_at: datetime
    provenance: str = "HKEX DION"


class DisclosureInterestsMetadata(BaseModel):
    code: str
    source_name: str = "HKEX DION"
    source_url: str
    fetched_at: datetime
    source_status: Literal["ready", "unavailable"] = "ready"
    filing_count: int = 0


class DisclosureInterestsResponse(BaseModel):
    metadata: DisclosureInterestsMetadata
    filings: list[DisclosureInterestRow] = Field(default_factory=list)
    data_quality_warnings: list[str] = Field(default_factory=list)


class DocumentEntityRow(BaseModel):
    stock_code: str
    document_id: str
    document_type: str
    entity_type: Literal["placing_agent", "financial_adviser", "independent_financial_adviser", "offeror", "underwriter", "whitewash_waiver", "concert_party"]
    entity_name: str | None = None
    direct_source_fact: str
    derived_classification: str | None = None
    source_url: str
    announcement_date: date
    retrieved_at: datetime
    provenance: str = "HKEXnews document text"


class DocumentEntitiesMetadata(BaseModel):
    code: str
    source_name: str = "HKEXnews document text"
    fetched_at: datetime
    source_status: Literal["ready", "partial", "unavailable"]
    documents_attempted: int = 0
    documents_fetched: int = 0
    rows_extracted: int = 0


class DocumentEntitiesResponse(BaseModel):
    metadata: DocumentEntitiesMetadata
    rows: list[DocumentEntityRow] = Field(default_factory=list)
    data_quality_warnings: list[str] = Field(default_factory=list)


class StockEventRow(BaseModel):
    event_date: date
    title: str
    event_type: str | None = None
    source: str
    link: str | None = None
    details: str | None = None
    event_id: str | None = None
    event_details_url: str | None = None


class StockEventsMetadata(BaseModel):
    code: str
    name: str | None = None
    source_name: str
    source_url: str | None = None
    fetched_at: datetime
    data_as_of: date | None = None
    stock_events_count: int = 0
    source_status: Literal["ready", "pending", "unavailable"] = "pending"


class StockEventsResponse(BaseModel):
    metadata: StockEventsMetadata
    stock_events: list[StockEventRow] = Field(default_factory=list)
    data_quality_warnings: list[str] = Field(default_factory=list)


class OfficerRow(BaseModel):
    name: str
    positions: list[str] = Field(default_factory=list)
    tenure_from: date | None = None
    tenure_to: date | None = None
    is_current: bool | None = None
    sex: str | None = None
    age: int | None = None
    education: str | None = None
    salary: str | None = None
    biography: str | None = None


class OfficersMetadata(BaseModel):
    code: str
    name: str | None = None
    source_name: str
    source_url: str | None = None
    fetched_at: datetime
    data_as_of: date | None = None
    officers_count: int = 0
    source_status: Literal["ready", "pending", "unavailable"] = "pending"


class OfficersResponse(BaseModel):
    metadata: OfficersMetadata
    officers: list[OfficerRow] = Field(default_factory=list)
    data_quality_warnings: list[str] = Field(default_factory=list)


class CapitalInformationRow(BaseModel):
    label: str
    value: str | None = None
    unit: str | None = None
    as_of: date | None = None
    source: str | None = None
    note: str | None = None
    link: str | None = None


class CapitalInformationMetadata(BaseModel):
    code: str
    name: str | None = None
    source_name: str
    source_url: str | None = None
    fetched_at: datetime
    data_as_of: date | None = None
    capital_information_count: int = 0
    source_status: Literal["ready", "pending", "unavailable"] = "pending"


class CapitalInformationResponse(BaseModel):
    metadata: CapitalInformationMetadata
    capital_information: list[CapitalInformationRow] = Field(default_factory=list)
    data_quality_warnings: list[str] = Field(default_factory=list)


class ShareCapitalHistoryRow(BaseModel):
    announce_date: date
    shares_million: float | None = None
    shares_approx: str | None = None
    reason: str | None = None
    reason_tags: list[str] = Field(default_factory=list)
    change_date: date | None = None
    source: str
    source_url: str


class ShareCapitalHistoryMetadata(BaseModel):
    code: str
    source_name: str
    fetched_at: datetime
    source_status: Literal["ready", "partial", "unavailable"]
    documents_attempted: int = 0
    documents_fetched: int = 0
    documents_parsed: int = 0
    documents_failed: int = 0


class ShareCapitalHistoryResponse(BaseModel):
    metadata: ShareCapitalHistoryMetadata
    rows: list[ShareCapitalHistoryRow] = Field(default_factory=list)
    data_quality_warnings: list[str] = Field(default_factory=list)


class IntelligenceEventRow(BaseModel):
    stock_code: str
    event_type: str
    announce_date: date
    effective_date: date | None = None
    shares_before: float | None = None
    shares_after: float | None = None
    price: float | None = None
    ratio: str | None = None
    discount: float | None = None
    counterparty: str | None = None
    beneficial_owner: str | None = None
    placing_agent: str | None = None
    adviser: str | None = None
    entity_name: str | None = None
    source_document: str
    source_url: str
    confidence: Literal["official", "extracted", "derived"] = "derived"
    extraction_method: str
    retrieved_at: datetime
    provenance: str = ""


class IntelligenceEventsMetadata(BaseModel):
    code: str
    source_name: str = "Joe Intelligence Event Layer"
    fetched_at: datetime
    source_status: Literal["ready", "partial", "unavailable"] = "ready"
    event_count: int = 0
    coverage_start: date | None = None
    coverage_end: date | None = None


class IntelligenceEventsResponse(BaseModel):
    metadata: IntelligenceEventsMetadata
    events: list[IntelligenceEventRow] = Field(default_factory=list)
    data_quality_warnings: list[str] = Field(default_factory=list)


class FundamentalRow(BaseModel):
    stock_code: str
    reporting_period: str
    announcement_date: date
    report_type: str
    revenue: float | None = None
    net_profit_loss: float | None = None
    cash: float | None = None
    debt: float | None = None
    net_assets: float | None = None
    equity: float | None = None
    operating_cash_flow: float | None = None
    shares_outstanding: float | None = None
    currency: str | None = None
    unit: str | None = None
    source_document: str
    source_url: str
    retrieval_timestamp: datetime
    parser_method: str
    completeness_status: Literal["complete", "partial"] = "partial"


class FundamentalsMetadata(BaseModel):
    code: str
    source_name: str = "HKEXnews"
    fetched_at: datetime
    source_status: Literal["ready", "partial", "unavailable"]
    documents_attempted: int = 0
    documents_fetched: int = 0
    documents_parsed: int = 0
    documents_failed: int = 0


class FundamentalsResponse(BaseModel):
    metadata: FundamentalsMetadata
    rows: list[FundamentalRow] = Field(default_factory=list)
    data_quality_warnings: list[str] = Field(default_factory=list)
