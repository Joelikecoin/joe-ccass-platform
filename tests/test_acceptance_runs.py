from pathlib import Path

from app.services.job_runner import JobStore


def test_acceptance_stage_is_durable_and_recoverable(tmp_path: Path):
    store = JobStore(tmp_path / "ccass.sqlite")
    job_id = store.create("CROSS_SOURCE_PRODUCTION_ACCEPTANCE")
    store.record_stage(job_id, "source_read", "PASS", rows_seen=15)
    recovered = JobStore(tmp_path / "ccass.sqlite")
    stages = recovered.acceptance_stages(job_id)
    assert stages[0]["stage_name"] == "source_read"
    assert recovered.stage_passed(job_id, "source_read")
    assert not recovered.stage_passed(job_id, "canonical_build")


def test_data_not_available_is_not_failure(tmp_path: Path):
    store = JobStore(tmp_path / "ccass.sqlite")
    job_id = store.create("CROSS_SOURCE_PRODUCTION_ACCEPTANCE")
    store.record_stage(job_id, "event_acceptance", "DATA_NOT_AVAILABLE")
    assert store.stage_passed(job_id, "event_acceptance")
    assert store.acceptance_stages(job_id)[0]["stage_status"] == "DATA_NOT_AVAILABLE"


def test_event_field_match_evidence_is_durable(tmp_path: Path):
    store = JobStore(tmp_path / "ccass.sqlite")
    job_id = store.create("EVENT_PRODUCTION_ACCEPTANCE")
    store.record_field_match(job_id, {
        "field_match_id": "event:e-1",
        "record_kind": "event",
        "source_record_id": "e-1",
        "canonical_record_id": "e-1",
        "fields_compared": ["stock_code", "event_type", "event_date"],
        "fields_matched": ["stock_code", "event_type", "event_date"],
        "fields_mismatched": [],
        "mismatch_details": {},
        "source_refs": ["https://source/e-1"],
        "canonical_refs": ["https://source/e-1"],
        "match_pass": True,
    })
    recovered = JobStore(tmp_path / "ccass.sqlite")
    evidence = recovered.field_match_evidence(job_id)
    assert len(evidence) == 1
    assert evidence[0]["match_pass"] == 1
    assert '"event_date"' in evidence[0]["fields_compared"]
