from __future__ import annotations

import io

import pytest

from app.canonical_historical_import import CanonicalImportError, import_canonical_csv


COLUMNS = [
    "stock_code", "stock_name", "snapshot_date", "source_id", "source_url",
    "source_fetched_at", "source_data_as_of", "participant_id", "participant_name",
    "participant_category", "holding_shares", "issued_shares", "ccass_total_shares",
    "stake_pct_of_issued", "stake_pct_of_ccass", "rank", "is_partial",
    "data_quality_status", "warning", "provenance_note", "issue_id",
    "last_change_date", "raw_participant_name", "raw_holding_value",
    "raw_source_payload_ref", "import_batch_id",
]


def csv_text(*rows: dict[str, str]) -> str:
    lines = [",".join(COLUMNS)]
    for row in rows:
        lines.append(",".join(row.get(column, "") for column in COLUMNS))
    return "\n".join(lines) + "\n"


def complete_row(**overrides: str) -> dict[str, str]:
    row = {
        "stock_code": "00005",
        "stock_name": "HSBC",
        "snapshot_date": "2026-08-29",
        "source_id": "approved_source",
        "source_url": "https://example.invalid/holdings.csv",
        "source_fetched_at": "2026-09-01T01:02:03+00:00",
        "source_data_as_of": "2026-08-29",
        "participant_id": "B01438",
        "participant_name": "Example Participant",
        "participant_category": "broker",
        "holding_shares": "100000",
        "issued_shares": "1000000",
        "ccass_total_shares": "500000",
        "stake_pct_of_issued": "10.0",
        "stake_pct_of_ccass": "20.0",
        "rank": "1",
        "is_partial": "false",
        "data_quality_status": "complete",
        "warning": "",
        "provenance_note": "Imported from approved source export.",
        "issue_id": "12345",
    }
    row.update(overrides)
    return row


def test_complete_snapshot_normalizes_and_reports_scope():
    result = import_canonical_csv(io.StringIO(csv_text(complete_row())))

    assert result.usable
    assert len(result.accepted_rows) == 1
    row = result.accepted_rows[0]
    assert row.import_key == ("00005", row.snapshot_date, "B01438")
    assert row.holding_shares == 100000
    assert row.stake_pct_of_issued == 10
    assert result.snapshot_dates[0].isoformat() == "2026-08-29"
    assert result.stocks == ("00005",)
    assert result.sources == ("approved_source",)
    assert result.dry_run is True


def test_partial_snapshot_preserves_missing_denominators_without_fabrication():
    row = complete_row(
        issued_shares="",
        ccass_total_shares="",
        stake_pct_of_issued="",
        stake_pct_of_ccass="",
        is_partial="true",
        data_quality_status="partial",
        warning="Denominators unavailable.",
    )

    result = import_canonical_csv(io.StringIO(csv_text(row)))

    assert result.accepted_rows[0].issued_shares is None
    assert result.accepted_rows[0].ccass_total_shares is None
    assert result.accepted_rows[0].stake_pct_of_issued is None
    assert result.accepted_rows[0].stake_pct_of_ccass is None
    assert result.accepted_rows[0].warning == "Denominators unavailable."


def test_malformed_rows_are_rejected_while_valid_rows_remain_usable():
    valid = complete_row()
    invalid = complete_row(participant_id="bad", holding_shares="-1")

    result = import_canonical_csv(io.StringIO(csv_text(valid, invalid)))

    assert len(result.accepted_rows) == 1
    assert len(result.rejected_rows) == 1
    assert "participant_id" in result.rejected_rows[0]["error"]


def test_conflicting_duplicate_key_fails_loud():
    first = complete_row()
    second = complete_row(participant_name="Different Participant")

    with pytest.raises(CanonicalImportError, match="conflicting duplicate"):
        import_canonical_csv(io.StringIO(csv_text(first, second)))


def test_dry_run_never_calls_writer():
    class FailingWriter:
        def save(self, _row):
            raise AssertionError("dry-run attempted a database write")

    result = import_canonical_csv(
        io.StringIO(csv_text(complete_row())),
        dry_run=True,
        writer=FailingWriter(),
    )

    assert result.accepted_rows
