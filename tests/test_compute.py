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
        "B00003",
    }
    assert analysis.transfer_patterns[0].from_participant == "TEST FIXTURE BROKER TWO"
    assert analysis.transfer_patterns[0].to_participant == "TEST FIXTURE BROKER ONE"
    assert analysis.transfer_patterns[0].approximate_shares == 500


def test_compute_concentration_and_warnings(current_response):
    current_response.metadata.cached = True
    analysis = compute_analysis(current_response, big_change_threshold=100)

    assert analysis.concentration["top5_pct_of_issued"] == 33.0
    assert analysis.concentration["top10_pct_of_ccass"] == 100.0
    assert any("cached or snapshot" in warning for warning in analysis.warnings)
    assert any("no previous snapshot" in warning.lower() for warning in analysis.warnings)
