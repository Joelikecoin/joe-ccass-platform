from datetime import date

from fastapi.testclient import TestClient

from app.api import get_snapshot_repository, verify_api_key
from app.config import Settings
from app.portal_8504 import app as portal_app
from app.storage.history import NormalizedSnapshotRepository


def test_portal_runtime_registers_concentration_evidence_route(tmp_path, current_response, monkeypatch):
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
    repository = NormalizedSnapshotRepository(tmp_path / "portal-evidence.db")
    repository.save_response(response, source_id="longbridge", parser_version="test")
    monkeypatch.setattr("app.api.get_settings", lambda: Settings(api_key="test"))
    original_snapshot_on = repository.snapshot_on
    reads = []

    def snapshot_on(*args, **kwargs):
        reads.append((args, kwargs))
        return original_snapshot_on(*args, **kwargs)

    def fail_write(*args, **kwargs):
        raise AssertionError("acceptance route must not write")

    repository.snapshot_on = snapshot_on
    repository.save_response = fail_write
    portal_app.dependency_overrides[get_snapshot_repository] = lambda: repository
    client = TestClient(portal_app)
    try:
        result = client.get("/internal/acceptance/concentration-evidence")
        attempted_override = client.get(
            "/internal/acceptance/concentration-evidence",
            params={"stock_code": "99999", "snapshot_date": "2020-01-01"},
        )
        authenticated = client.get(
            "/api/v1/stocks/00005/concentration/evidence",
            params={"snapshot_date": "2026-09-11"},
            headers={"X-API-Key": "test"},
        )
        unauthenticated = client.get(
            "/api/v1/stocks/00005/concentration/evidence",
            params={"snapshot_date": "2026-09-11"},
        )
        acceptance_route = next(
            item for item in portal_app.routes if item.path == "/internal/acceptance/concentration-evidence"
        )
        production_route = next(
            item for item in portal_app.routes if item.path.endswith("/concentration/evidence")
        )
    finally:
        portal_app.dependency_overrides.pop(get_snapshot_repository, None)

    assert result.status_code == 200
    assert attempted_override.status_code == 200
    payload = result.json()
    assert payload == attempted_override.json()
    assert payload["stock_code"] == "00005"
    assert payload["snapshot_date"] == "2026-09-11"
    assert payload["source_id"] == "longbridge"
    assert payload["participant_count"] == 444
    assert len(payload["participants"]) == 444
    assert len(reads) == 4
    assert all(call[0][:2] == ("00005", date(2026, 9, 11)) for call in reads)
    assert all(call[1] == {"source_id": "longbridge"} for call in reads)
    acceptance_dependency_callables = {
        dependency.call
        for dependency in acceptance_route.dependant.dependencies
    }
    assert verify_api_key not in acceptance_dependency_callables
    dependency_callables = {
        dependency.call
        for dependency in production_route.dependant.dependencies
    }
    assert verify_api_key in dependency_callables
    assert authenticated.status_code == 200


def test_temporary_acceptance_route_fails_loudly_without_exact_snapshot(tmp_path):
    repository = NormalizedSnapshotRepository(tmp_path / "empty-portal-evidence.db")
    portal_app.dependency_overrides[get_snapshot_repository] = lambda: repository
    client = TestClient(portal_app)
    try:
        result = client.get("/internal/acceptance/concentration-evidence")
    finally:
        portal_app.dependency_overrides.pop(get_snapshot_repository, None)

    assert result.status_code == 404
    assert "exact persisted Longbridge snapshot" in result.json()["message"]
