from datetime import date
import sqlite3

import pytest

from app.sources.webbsite_historical import WebbHistoricalSqliteSource


@pytest.mark.asyncio
async def test_webb_historical_source_reads_canonical_snapshot(tmp_path):
    path = tmp_path / "canonical.sqlite"
    connection = sqlite3.connect(path)
    connection.execute(
        "CREATE TABLE historical_snapshot ("
        "stock_code TEXT, issue_id INTEGER, snapshot_date TEXT, participant_id INTEGER, "
        "participant_name TEXT, holding REAL, issued_shares REAL, stake_pct REAL, "
        "source TEXT, source_record_date TEXT, provenance_metadata TEXT)"
    )
    connection.executemany(
        "INSERT INTO historical_snapshot VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        [
            ("00004", 1, "2025-12-23", 460, "BANK A", 100, 1000, 10, "Webb", "2025-11-30", "{}"),
            ("00004", 1, "2025-12-23", 454, "BANK B", 50, 1000, 5, "Webb", "2025-11-30", "{}"),
        ],
    )
    connection.commit()
    connection.close()

    source = WebbHistoricalSqliteSource(path)
    assert await source.available_dates("4") == (date(2025, 12, 23),)
    response = await source.get_holdings_for_date("00004", date(2025, 12, 23))
    assert response.metadata.issue_id == 1
    assert response.metadata.source_name == "Webb-site repository archive"
    assert response.holdings_summary.issued_shares == 1000
    assert response.holdings[0].participant == "BANK A"
    assert response.holdings[0].pct_of_issued == 10


@pytest.mark.asyncio
async def test_webb_historical_source_is_explicit_when_date_is_unavailable(tmp_path):
    path = tmp_path / "canonical.sqlite"
    connection = sqlite3.connect(path)
    connection.execute(
        "CREATE TABLE historical_snapshot (stock_code TEXT, issue_id INTEGER, snapshot_date TEXT, "
        "participant_id INTEGER, participant_name TEXT, holding REAL, issued_shares REAL, "
        "stake_pct REAL, source TEXT, source_record_date TEXT, provenance_metadata TEXT)"
    )
    connection.commit()
    connection.close()
    source = WebbHistoricalSqliteSource(path)
    with pytest.raises(Exception, match="No Webb-site archive snapshot"):
        await source.get_holdings_for_date("00004", date(2025, 12, 24))
