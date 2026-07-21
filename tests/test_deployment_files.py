from pathlib import Path


def test_streamlit_cloud_files_and_hkex_compliance_notice_exist():
    requirements = Path("requirements.txt").read_text(encoding="utf-8")
    config = Path(".streamlit/config.toml").read_text(encoding="utf-8")
    readme = Path("README.md").read_text(encoding="utf-8")
    schedule_script = Path("scripts/install_collector_task.ps1").read_text(encoding="utf-8")

    assert "streamlit>=1.40,<2" in requirements
    assert "headless = true" in config
    assert "enableXsrfProtection = true" in config
    assert "programmatic、scripted" in readme
    assert "不存取 HKEX SDW" in readme
    assert "SupportsShouldProcess = $true" in schedule_script
    assert "ConfirmImpact = 'High'" in schedule_script
