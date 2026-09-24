from datetime import date
from types import SimpleNamespace

from app.services.current_holdings_readback import read_current_participant_holdings


def test_readback_preserves_production_source_identity_and_lineage():
    snapshot = SimpleNamespace(
        stock=SimpleNamespace(code="00005"),
        snapshot_date=date(2026, 9, 17),
        source=SimpleNamespace(source_id="longbridge"),
        provenance=SimpleNamespace(safe_reference="longbridge://broker_holding_detail/00005", checksum_sha256="a" * 64),
        holdings=(SimpleNamespace(participant_id="C00019", participant_name="HSBC", shares=1642265160),),
    )

    class Repository:
        def snapshot_on(self, code, snapshot_date, *, source_id):
            assert (code, snapshot_date, source_id) == ("00005", date(2026, 9, 17), "longbridge")
            return snapshot

    rows = read_current_participant_holdings(Repository(), "00005", date(2026, 9, 17))
    assert rows == [{
        "canonical_security_id": "security:00005",
        "hk_stock_code": "00005",
        "holdings_date": "2026-09-17",
        "source_participant_id": "C00019",
        "canonical_participant_id": None,
        "participant_name": "HSBC",
        "share_quantity": 1642265160,
        "source_reference": "longbridge://broker_holding_detail/00005",
        "source_id": "longbridge",
        "provenance_sha256": "a" * 64,
    }]
