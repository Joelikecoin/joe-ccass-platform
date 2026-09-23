from datetime import date

from app.services.cross_source_intelligence import Confidence, EvidenceState
from app.storage.cross_source import CrossSourceRepository
from app.storage.history import NormalizedSnapshotRepository


def test_cross_source_records_are_idempotent_and_append_only(tmp_path):
    repo = CrossSourceRepository(NormalizedSnapshotRepository(tmp_path / "cross.sqlite"))
    payload = {
        "entity_id": "p-1", "entity_type": "PERSON", "canonical_name": "A",
        "source_id": "hkex", "source_native_id": "P-1", "valid_from": None,
        "valid_to": None, "observed_at": date(2025, 1, 1), "confidence": Confidence.EXACT.value,
        "status": "ACTIVE", "lineage": [],
    }
    repo.put(record_id="p-1", record_kind="entity", source_id="hkex", payload=payload, source_date=date(2025, 1, 1), evidence_state=EvidenceState.SUPPORTED.value)
    repo.put(record_id="p-1", record_kind="entity", source_id="hkex", payload={**payload, "canonical_name": "SHOULD_NOT_REPLACE"}, source_date=date(2025, 1, 2), evidence_state=EvidenceState.SUPPORTED.value)
    assert len(repo.records("entity")) == 1
    assert repo.records("entity")[0]["payload_json"].find("SHOULD_NOT_REPLACE") < 0
    assert repo.load_engine().entities[0].canonical_name == "A"
