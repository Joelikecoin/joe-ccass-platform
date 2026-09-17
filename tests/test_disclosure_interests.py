from datetime import date

from app.sources.disclosure_interests import HKEXDisclosureInterestsSource


def test_dion_result_parser_normalizes_official_row_shape():
    html = """
    <table><tr><th>Form Serial Number</th><th>Name</th><th>Reason</th><th>Shares</th>
    <th>Average price</th><th>Interested</th><th>%</th><th>Date</th></tr>
    <tr><td><a href="NSForm2.aspx?fn=CS20260824E00178">CS20260824E00178</a></td>
    <td>JPMorgan Chase &amp; Co.</td><td>1104 (L)</td><td>775,802(L)</td>
    <td>HKD 413.2018</td><td>101,583,554(L)</td><td>8.01(L)</td>
    <td><a href="NSForm2.aspx?fn=CS20260824E00178">19/08/2026</a></td></tr></table>
    """
    result = HKEXDisclosureInterestsSource()._parse_result("00388", html, date(2025, 1, 1), date(2026, 12, 31))
    assert len(result.filings) == 1
    row = result.filings[0]
    assert row.filer == "JPMorgan Chase & Co."
    assert row.event_date == date(2026, 8, 19)
    assert row.shares_involved == 775802
    assert row.present_balance == 101583554
    assert row.percentage == 8.01
    assert row.source_url.endswith("CS20260824E00178")
