from datetime import date

from fastapi.testclient import TestClient

from app.api import app, get_snapshot_repository
from app.config import Settings
from app.storage.history import NormalizedSnapshotRepository


def test_concentration_evidence_returns_full_exact_persisted_snapshot(
    tmp_path, current_response, monkeypatch
):
    holdings = [
        current_response.holdings[0].model_copy(
            update={
                "rank": rank,
                "participant_id": f"P{rank:04d}",
                "participant": f"Participant {rank}",
                "shares": 500 - (rank % 7),
            }
        )
        for rank in range(1, 445)
    ]
    response = current_response.model_copy(
        update={
            "metadata": current_response.metadata.model_copy(
                update={"code": "00005", "holdings_date": date(2026, 9, 11), "source_name": "Longbridge"}
            ),
            "holdings": holdings,
            "holdings_summary": current_response.holdings_summary.model_copy(
                update={"issued_shares": 250_000, "participant_count": 444}
            ),
        }
    )
    repository = NormalizedSnapshotRepository(tmp_path / "evidence.db")
    repository.save_response(response, source_id="longbridge", parser_version="test")
    monkeypatch.setattr("app.api.get_settings", lambda: Settings(api_key="test"))
    app.dependency_overrides[get_snapshot_repository] = lambda: repository
    client = TestClient(app)
    try:
        result = client.get(
            "/api/v1/stocks/00005/concentration/evidence",
            params={"snapshot_date": "2026-09-11"},
            headers={"X-API-Key": "test"},
        )
    finally:
        app.dependency_overrides.pop(get_snapshot_repository, None)

    assert result.status_code == 200
    payload = result.json()
    participants = payload["participants"]
    summary = payload["summary"]
    top5 = sum(row["shares"] for row in participants[:5])
    top10 = sum(row["shares"] for row in participants[:10])
    total = sum(row["shares"] for row in participants)
    assert payload["stock_code"] == "00005"
    assert payload["snapshot_date"] == "2026-09-11"
    assert payload["source_id"] == "longbridge"
    assert payload["participant_count"] == len(participants) == 444
    assert [row["rank"] for row in participants] == list(range(1, 445))
    assert summary["top5_shares"] == top5
    assert summary["top10_shares"] == top10
    assert summary["total_ccass_shares"] == total
    assert summary["issued_shares"] == 250_000
    assert summary["top5_pct_of_issued"] == round(top5 / 250_000 * 100, 6)
    assert summary["top10_pct_of_issued"] == round(top10 / 250_000 * 100, 6)
    assert summary["top5_pct_of_ccass"] == round(top5 / total * 100, 6)
    assert summary["top10_pct_of_ccass"] == round(top10 / total * 100, 6)


def test_concentration_evidence_fails_loudly_when_exact_snapshot_is_missing(monkeypatch, tmp_path):
    repository = NormalizedSnapshotRepository(tmp_path / "empty.db")
    app.dependency_overrides[get_snapshot_repository] = lambda: repository
    client = TestClient(app)
    try:
        result = client.get(
            "/api/v1/stocks/00005/concentration/evidence",
            params={"snapshot_date": "2026-09-11"},
        )
    finally:
        app.dependency_overrides.pop(get_snapshot_repository, None)

    assert result.status_code == 404
    assert "exact persisted Longbridge snapshot" in result.json()["message"]
