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


def _gate51_holdings(count):
    return tuple(
        types.SimpleNamespace(
            participant_id=f"B{i:05d}", participant_name=f"Broker '{i}",
            rank=i + 1, shares=1000 + i, last_change=None,
            pct_of_issued=0.1, pct_of_ccass=0.2,
            cumulative_pct_of_issued=0.3, participant_category="broker",
        )
        for i in range(count)
    )


def _gate51_connection():
    connection = sqlite3.connect(":memory:", isolation_level=None)
    connection.execute("""CREATE TABLE ccass_holdings (
        snapshot_id INTEGER, participant_id TEXT UNIQUE, participant_name TEXT,
        rank INTEGER, shares INTEGER, last_change TEXT, pct_of_issued REAL,
        pct_of_ccass REAL, cumulative_pct_of_issued REAL, participant_category TEXT
    )""")
    return connection


def test_remote_holdings_batches_preserve_every_value_and_bound_parameters():
    class Remote:
        def __init__(self):
            self.connection = _gate51_connection()
            self.batch_sizes = []

        def execute(self, statement, parameters):
            self.batch_sizes.append(len(parameters))
            return self.connection.execute(statement, parameters)

        def executemany(self, *args):
            raise AssertionError("remote per-row executemany must not be used")

    repository = object.__new__(NormalizedSnapshotRepository)
    holdings = _gate51_holdings(235)
    remote = Remote()
    local = _gate51_connection()
    repository._insert_holdings(_LibsqlConnection(remote), 7, holdings)
    repository._insert_holdings(local, 7, holdings)
    query = "SELECT * FROM ccass_holdings ORDER BY rank"
    assert remote.connection.execute(query).fetchall() == local.execute(query).fetchall()
    assert remote.batch_sizes == [900, 900, 550]
    repository._insert_holdings(_LibsqlConnection(remote), 7, ())
    assert remote.batch_sizes == [900, 900, 550]


def test_remote_holdings_later_batch_failure_rolls_back_entire_transaction():
    repository = object.__new__(NormalizedSnapshotRepository)
    connection = _gate51_connection()
    holdings = _gate51_holdings(100)
    holdings = holdings[:99] + (holdings[0],)
    connection.execute("BEGIN IMMEDIATE")
    try:
        repository._insert_holdings(_LibsqlConnection(connection), 7, holdings)
    except sqlite3.IntegrityError:
        connection.rollback()
    else:
        raise AssertionError("duplicate participant must reject the batch")
    assert connection.execute("SELECT COUNT(*) FROM ccass_holdings").fetchone()[0] == 0
