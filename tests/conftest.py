from datetime import UTC, date, datetime

import pytest

from app.models import CcassResponse, HoldingRow, HoldingsSummary, SourceMetadata


def _response(*, current: bool, cached: bool = False) -> CcassResponse:
    rows = (
        [
            HoldingRow(
                rank=1,
                participant_id="B00001",
                participant="TEST FIXTURE BROKER ONE",
                shares=1_500,
                last_change=date(2026, 7, 20),
                pct_of_issued=15.0,
                cumulative_pct_of_issued=15.0,
                participant_category="broker",
            ),
            HoldingRow(
                rank=2,
                participant_id="B00002",
                participant="TEST FIXTURE BROKER TWO",
                shares=1_500,
                last_change=date(2026, 7, 20),
                pct_of_issued=15.0,
                cumulative_pct_of_issued=30.0,
                participant_category="broker",
            ),
            HoldingRow(
                rank=3,
                participant_id="B00004",
                participant="TEST FIXTURE BROKER FOUR",
                shares=300,
                last_change=date(2026, 7, 20),
                pct_of_issued=3.0,
                cumulative_pct_of_issued=33.0,
                participant_category="broker",
            ),
        ]
        if current
        else [
            HoldingRow(
                rank=1,
                participant_id="B00002",
                participant="TEST FIXTURE BROKER TWO",
                shares=2_000,
                last_change=date(2026, 7, 19),
                pct_of_issued=20.0,
                cumulative_pct_of_issued=20.0,
                participant_category="broker",
            ),
            HoldingRow(
                rank=2,
                participant_id="B00001",
                participant="TEST FIXTURE BROKER ONE",
                shares=1_000,
                last_change=date(2026, 7, 19),
                pct_of_issued=10.0,
                cumulative_pct_of_issued=30.0,
                participant_category="broker",
            ),
            HoldingRow(
                rank=3,
                participant_id="B00003",
                participant="TEST FIXTURE BROKER THREE",
                shares=500,
                last_change=date(2026, 7, 19),
                pct_of_issued=5.0,
                cumulative_pct_of_issued=35.0,
                participant_category="broker",
            ),
        ]
    )
    return CcassResponse(
        metadata=SourceMetadata(
            code="01592",
            name="TEST FIXTURE — GOLDEN STOCK",
            issue_id=15_920,
            holdings_date=date(2026, 7, 20 if current else 19),
            fetched_at=datetime(2026, 7, 21, 1 if current else 0, tzinfo=UTC),
            source_url="https://fixture.invalid/",
            source_name="Offline test fixture",
            cached=cached,
            attribution="TEST FIXTURE — not production data",
        ),
        holdings_summary=HoldingsSummary(
            total_in_ccass_shares=4_000,
            total_in_ccass_pct_of_issued=40.0,
            issued_shares=10_000,
            non_ccass_shares=6_000,
            non_ccass_pct_of_issued=60.0,
            participant_count=len(rows),
            top5_pct_of_issued=33.0 if current else 35.0,
            top10_pct_of_issued=33.0 if current else 35.0,
            top5_pct_of_ccass=82.5 if current else 87.5,
            top10_pct_of_ccass=82.5 if current else 87.5,
        ),
        holdings=rows,
        data_quality_warnings=["TEST FIXTURE warning"] if current else [],
    )


@pytest.fixture
def current_response() -> CcassResponse:
    return _response(current=True)


@pytest.fixture
def previous_response() -> CcassResponse:
    return _response(current=False)
