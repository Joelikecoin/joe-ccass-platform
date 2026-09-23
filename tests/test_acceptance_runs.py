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
