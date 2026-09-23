import json
import sys
from types import SimpleNamespace

from scripts import production_acceptance as audit


def test_database_failure_does_not_stop_api_checks_or_leak_secrets(monkeypatch, capsys):
    sentinel = "private-test-value-must-never-appear"
    for key in ("API_KEY", "TURSO_DATABASE_URL", "TURSO_AUTH_TOKEN"):
        monkeypatch.setenv(key, sentinel)
    def denied(**kwargs):
        raise RuntimeError(sentinel)
    monkeypatch.setitem(sys.modules, "libsql", SimpleNamespace(connect=denied))
    calls = []
    def request(path, **kwargs):
        calls.append(path)
        if path == "/health":
            return 200, {}
        return 401, {"secret": sentinel}
    monkeypatch.setattr(audit, "request", request)
    monkeypatch.setattr(audit, "RESULTS", {})
    audit.run()
    output = capsys.readouterr().out
    assert sentinel not in output
    assert audit.RESULTS["audit_finished"]
    assert not audit.RESULTS["database_audit_completed"]
    assert any("/timeline?" in path for path in calls)
    assert any("/sequence?" in path for path in calls)
    assert any("/concentration/evidence?" in path for path in calls)
    assert not audit.RESULTS["evidence_db_readback_consistency"]


def test_log_allowlist_and_no_redirects(capsys):
    audit.emit("redaction", True, count=3, value="private-value", payload={"key": "private-value"})
    output = capsys.readouterr().out
    assert "private-value" not in output
    assert json.loads(output.removeprefix(audit.PREFIX)) == {"check": "redaction", "pass": True, "count": 3}
    assert audit.NoRedirect().redirect_request(None, None, None, None, None, None) is None
