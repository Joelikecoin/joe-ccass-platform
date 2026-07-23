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
                pct_of_ccass=45.454545,
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
                pct_of_ccass=45.454545,
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
                pct_of_ccass=9.090909,
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
                pct_of_ccass=57.142857,
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
                pct_of_ccass=28.571429,
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
                pct_of_ccass=14.285714,
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
            total_in_ccass_shares=3_300 if current else 3_500,
            total_in_ccass_pct_of_issued=33.0 if current else 35.0,
            issued_shares=10_000,
            issued_shares_as_of=date(2026, 7, 20 if current else 19),
            non_ccass_shares=6_700 if current else 6_500,
            non_ccass_pct_of_issued=67.0 if current else 65.0,
            participant_count=len(rows),
            top5_pct_of_issued=33.0 if current else 35.0,
            top10_pct_of_issued=33.0 if current else 35.0,
            top5_pct_of_ccass=100.0,
            top10_pct_of_ccass=100.0,
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
