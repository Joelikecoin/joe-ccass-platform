from datetime import date
from pathlib import Path

import pytest

from app.errors import ErrorCode, PlatformError
from app.sources.webbsite_parser import parse_webbsite_holdings

FIXTURES = Path(__file__).parent / "fixtures" / "webbsite"


def fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def test_parser_returns_sorted_normalized_holdings_and_snapshot_metadata():
    parsed = parse_webbsite_holdings(
        fixture("holdings_normal.html"),
        requested_code="01592",
    )

    assert parsed.code == "01592"
    assert parsed.issue_id == 15_920
    assert parsed.name == "TEST FIXTURE HOLDINGS LIMITED: O HKD"
    assert parsed.holdings_date == date(2026, 7, 20)
    assert [row.rank for row in parsed.holdings] == [1, 2, 3, 4]
    assert [row.participant_id for row in parsed.holdings] == [
        "B00001",
        "B00002",
        "C00003",
        "B00004",
    ]
    assert parsed.holdings[0].participant == "TEST FIXTURE BROKER ONE"
    assert parsed.holdings[0].shares == 3_000
    assert parsed.holdings[0].pct_of_issued == 30.0
    assert parsed.holdings[0].cumulative_pct_of_issued == 30.0
    assert parsed.holdings_summary.participant_count == 4
    assert parsed.holdings_summary.total_in_ccass_shares == 8_000
    assert parsed.holdings_summary.top5_pct_of_issued == 80.0
    assert parsed.holdings_summary.top5_pct_of_ccass == 100.0


@pytest.mark.parametrize(
    ("filename", "code", "error_code"),
    [
        ("holdings_missing_table.html", "01592", ErrorCode.SOURCE_CHANGED),
        ("holdings_malformed.html", "01592", ErrorCode.PARSE_ERROR),
        ("holdings_identity_mismatch.html", "01592", ErrorCode.NOT_FOUND),
    ],
)
def test_parser_fails_loud_for_missing_changed_malformed_or_wrong_identity(
    filename,
    code,
    error_code,
):
    with pytest.raises(PlatformError) as caught:
        parse_webbsite_holdings(fixture(filename), requested_code=code)

    assert caught.value.code == error_code


def test_parser_rejects_empty_table_and_missing_required_column():
    normal = fixture("holdings_normal.html")
    empty = normal.replace(
        normal[normal.index("  <tr>\n    <td>2</td>") : normal.rindex("</table>")],
        "",
    )
    renamed = normal.replace("<th>CCASS ID</th>", "<th>Participant key</th>")

    with pytest.raises(PlatformError) as empty_error:
        parse_webbsite_holdings(empty, requested_code="01592")
    with pytest.raises(PlatformError) as renamed_error:
        parse_webbsite_holdings(renamed, requested_code="01592")

    assert empty_error.value.code == ErrorCode.PARSE_ERROR
    assert renamed_error.value.code == ErrorCode.SOURCE_CHANGED


@pytest.mark.parametrize(
    "issue_field",
    [
        "",
        '<input type="hidden" name="i" value="0">',
        '<input type="hidden" name="i" value="not-an-id">',
    ],
)
def test_parser_rejects_missing_or_invalid_issue_mapping(issue_field):
    html = fixture("holdings_normal.html")
    html = html.replace(
        '<input type="hidden" name="i" value="15920">',
        issue_field,
    )

    with pytest.raises(PlatformError) as caught:
        parse_webbsite_holdings(html, requested_code="01592")

    assert caught.value.code == ErrorCode.NOT_FOUND


def test_parser_rejects_conflicting_issue_mapping():
    html = fixture("holdings_normal.html").replace(
        '<input type="hidden" name="i" value="15920">',
        (
            '<input type="hidden" name="i" value="15920">'
            '<input type="hidden" name="i" value="15921">'
        ),
    )

    with pytest.raises(PlatformError) as caught:
        parse_webbsite_holdings(html, requested_code="01592")

    assert caught.value.code == ErrorCode.SOURCE_CHANGED


def test_parser_preserves_percentages_over_100_and_adds_limitation():
    html = fixture("holdings_normal.html")
    html = html.replace("<td>30.00%</td><td>30.00%</td>", "<td>130.00%</td><td>130.00%</td>")

    parsed = parse_webbsite_holdings(html, requested_code="01592")

    assert parsed.holdings[0].pct_of_issued == 130.0
    assert parsed.holdings[0].cumulative_pct_of_issued == 130.0
    assert any("exceeds 100%" in warning for warning in parsed.warnings)


def test_parser_marks_missing_snapshot_date_without_using_fetch_date():
    html = fixture("holdings_normal.html").replace(
        "<h3>CCASS holdings on 2026-07-20</h3>",
        "<h3>CCASS latest holdings</h3>",
    )

    parsed = parse_webbsite_holdings(html, requested_code="01592")

    assert parsed.holdings_date is None
    assert any("snapshot date is unverified" in warning for warning in parsed.warnings)
