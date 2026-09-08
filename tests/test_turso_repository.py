import sqlite3
import sys
import types

from app.storage.history import NormalizedSnapshotRepository, _LibsqlConnection


def test_repository_uses_local_sqlite_without_turso_env(monkeypatch, tmp_path):
    monkeypatch.delenv("TURSO_DATABASE_URL", raising=False)
    monkeypatch.delenv("TURSO_AUTH_TOKEN", raising=False)
    repository = NormalizedSnapshotRepository(tmp_path / "history.db")
    assert repository.path == tmp_path / "history.db"


def test_repository_selects_libsql_when_turso_is_configured(monkeypatch, tmp_path):
    calls = []

    def connect(*, database, auth_token):
        calls.append((database, auth_token))
        return sqlite3.connect(":memory:", isolation_level=None)

    monkeypatch.setenv("TURSO_DATABASE_URL", "libsql://joe-ccass-prod.turso.io")
    monkeypatch.setenv("TURSO_AUTH_TOKEN", "test-token")
    monkeypatch.setitem(sys.modules, "libsql", types.SimpleNamespace(connect=connect))

    repository = NormalizedSnapshotRepository(tmp_path / "history.db")
    with repository._connect() as connection:
        connection.execute("SELECT 1")

    assert len(calls) >= 2
    assert set(calls) == {("libsql://joe-ccass-prod.turso.io", "test-token")}


def test_libsql_adapter_translates_named_parameter_mapping():
    class TupleOnlyConnection:
        def __init__(self):
            self.connection = sqlite3.connect(":memory:")

        def execute(self, statement, parameters=None):
            if isinstance(parameters, dict):
                raise ValueError("Expected a list or tuple for parameters")
            return self.connection.execute(statement, parameters or ())

    connection = _LibsqlConnection(TupleOnlyConnection())
    connection.execute("CREATE TABLE snapshots (code TEXT, snapshot_date TEXT)")
    connection.execute(
        "INSERT INTO snapshots(code, snapshot_date) VALUES (:code, :snapshot_date)",
        {"code": "06182", "snapshot_date": "2026-09-07"},
    )
    row = connection.execute("SELECT code, snapshot_date FROM snapshots").fetchone()
    assert tuple(row) == ("06182", "2026-09-07")
