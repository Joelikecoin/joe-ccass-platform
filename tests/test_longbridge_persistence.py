from datetime import UTC, datetime

from app.longbridge_persistence import build_response


def test_longbridge_summary_preserves_issued_and_ccass_denominators():
    response = build_response(
        {
            "updated_at": "2026-09-11",
            "list": [
                {"parti_number": "P1", "name": "One", "shares": 600, "ratio": 0.06},
                {"parti_number": "P2", "name": "Two", "shares": 300, "ratio": 0.03},
                {"parti_number": "P3", "name": "Three", "shares": 100, "ratio": 0.01},
            ],
        },
        stock_code="00005",
        issue_id=5,
        issued_shares=10_000,
        fetched_at=datetime(2026, 9, 11, tzinfo=UTC),
    )

    summary = response.holdings_summary
    assert summary.total_in_ccass_shares == 1_000
    assert summary.top5_pct_of_issued == 10.0
    assert summary.top10_pct_of_issued == 10.0
    assert summary.top5_pct_of_ccass == 100.0
    assert summary.top10_pct_of_ccass == 100.0


def test_longbridge_summary_keeps_issued_metrics_unknown_without_denominator():
    response = build_response(
        {
            "updated_at": "2026-09-11",
            "list": [{"parti_number": "P1", "name": "One", "shares": 100, "ratio": 0}],
        },
        stock_code="00005",
        issue_id=5,
    )

    assert response.holdings_summary.top5_pct_of_issued is None
    assert response.holdings_summary.top10_pct_of_issued is None
    assert response.holdings_summary.top5_pct_of_ccass == 100.0
    assert response.holdings_summary.top10_pct_of_ccass == 100.0
