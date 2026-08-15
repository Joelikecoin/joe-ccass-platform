from datetime import date

from app.models import HoldingRow
from ccass_core.compute import compute_analysis


def test_compute_diff_big_changes_and_transfer_pattern(current_response, previous_response):
    analysis = compute_analysis(
        current_response,
        previous_response,
        big_change_threshold=500,
    )

    by_id = {change.participant_id: change for change in analysis.changes}
    assert by_id["B00001"].share_change == 500
    assert by_id["B00001"].status == "increased"
    assert by_id["B00002"].share_change == -500
    assert by_id["B00003"].status == "exited"
    assert by_id["B00004"].status == "new"
    assert {change.participant_id for change in analysis.big_changes} == {
        "B00001",
        "B00002",
    }
    assert analysis.transfer_patterns[0].from_participant == "TEST FIXTURE BROKER TWO"
    assert analysis.transfer_patterns[0].to_participant == "TEST FIXTURE BROKER ONE"
    assert analysis.transfer_patterns[0].approximate_shares == 500


def test_compute_concentration_and_warnings(current_response):
    current_response.metadata.cached = True
    analysis = compute_analysis(current_response, big_change_threshold=100)

    assert analysis.concentration["top5_pct_of_issued"] == 33.0
    assert analysis.concentration["top10_pct_of_ccass"] == 100.0
    assert any(
        warning.startswith("FRESHNESS_STATUS: CACHED_SNAPSHOT")
        for warning in analysis.warnings
    )
    assert any(
        warning.startswith("DATA_LIMITATION: PREVIOUS_SNAPSHOT_UNAVAILABLE")
        for warning in analysis.warnings
    )


def test_compute_big_changes_uses_percentage_point_threshold(current_response, previous_response):
    current = current_response.model_copy(deep=True)
    previous = previous_response.model_copy(deep=True)
    current.holdings = [
        HoldingRow(
            rank=1,
            participant_id="B00001",
            participant="TEST FIXTURE BROKER ONE",
            shares=130,
            last_change=date(2026, 7, 20),
            pct_of_issued=1.3,
            pct_of_ccass=100.0,
            cumulative_pct_of_issued=1.3,
            participant_category="broker",
        )
    ]
    previous.holdings = [
        HoldingRow(
            rank=1,
            participant_id="B00001",
            participant="TEST FIXTURE BROKER ONE",
            shares=100,
            last_change=date(2026, 7, 19),
            pct_of_issued=1.0,
            pct_of_ccass=100.0,
            cumulative_pct_of_issued=1.0,
            participant_category="broker",
        )
    ]
    current.holdings_summary = current.holdings_summary.model_copy(
        update={
            "participant_count": 1,
            "total_in_ccass_shares": 130,
            "total_in_ccass_pct_of_issued": 1.3,
            "non_ccass_shares": 9_870,
            "non_ccass_pct_of_issued": 98.7,
            "top5_pct_of_issued": 1.3,
            "top10_pct_of_issued": 1.3,
            "top5_pct_of_ccass": 100.0,
            "top10_pct_of_ccass": 100.0,
        }
    )
    previous.holdings_summary = previous.holdings_summary.model_copy(
        update={
            "participant_count": 1,
            "total_in_ccass_shares": 100,
            "total_in_ccass_pct_of_issued": 1.0,
            "non_ccass_shares": 9_900,
            "non_ccass_pct_of_issued": 99.0,
            "top5_pct_of_issued": 1.0,
            "top10_pct_of_issued": 1.0,
            "top5_pct_of_ccass": 100.0,
            "top10_pct_of_ccass": 100.0,
        }
    )

    analysis = compute_analysis(current, previous, big_change_threshold=500)

    assert analysis.changes[0].share_change == 30
    assert analysis.changes[0].pct_point_change == 0.3
    assert [row.participant_id for row in analysis.big_changes] == ["B00001"]
