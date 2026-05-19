from __future__ import annotations

from fastapi.testclient import TestClient

from main import app
from app.core import config

client = TestClient(app)


def test_phase12_dashboard_workflow_uses_saved_records_only(tmp_path, monkeypatch):
    monkeypatch.setattr(config.settings, "db_profiles_file", str(tmp_path / "profiles.jsonl"))
    monkeypatch.setattr(config.settings, "db_projects_file", str(tmp_path / "projects.jsonl"))
    monkeypatch.setattr(config.settings, "db_scan_history_file", str(tmp_path / "scans.jsonl"))
    monkeypatch.setattr(config.settings, "db_saved_reports_file", str(tmp_path / "reports.jsonl"))

    project_response = client.post(
        "/projects",
        json={"user_id": "phase12-user", "name": "Workflow Project", "website_url": "https://example.com", "chain": "Base"},
    )
    assert project_response.status_code == 200
    project_id = project_response.json()["project"]["id"]

    scan_response = client.post(
        "/scan-history",
        json={
            "user_id": "phase12-user",
            "project_id": project_id,
            "module": "contract",
            "project_name": "Workflow Project",
            "score": 52,
            "risk_label": "Evidence Needed",
            "findings_count": 1,
            "critical_high_count": 1,
            "payload": {
                "findings": [
                    {
                        "id": "WG-001",
                        "title": "Owner power review needed",
                        "severity": "high",
                        "recommendation": "Document multisig, timelock, and admin handoff evidence before launch.",
                    }
                ]
            },
        },
    )
    assert scan_response.status_code == 200

    workflow_response = client.get(f"/dashboard-workflow?user_id=phase12-user&project_id={project_id}")
    assert workflow_response.status_code == 200
    workflow = workflow_response.json()["workflow"]
    assert workflow["scope"]["mode"] == "project"
    assert workflow["summary"]["scans"] == 1
    assert workflow["risk_trend"][0]["score"] == 52
    assert workflow["module_comparison"][0]["module"] == "contract"
    assert workflow["finding_workflow"]["tasks"][0]["title"] == "Owner power review needed"
    assert "no fake" in workflow["real_only_note"].lower()


def test_phase12_dashboard_workflow_empty_state_is_empty_not_fake(tmp_path, monkeypatch):
    monkeypatch.setattr(config.settings, "db_profiles_file", str(tmp_path / "profiles.jsonl"))
    monkeypatch.setattr(config.settings, "db_projects_file", str(tmp_path / "projects.jsonl"))
    monkeypatch.setattr(config.settings, "db_scan_history_file", str(tmp_path / "scans.jsonl"))
    monkeypatch.setattr(config.settings, "db_saved_reports_file", str(tmp_path / "reports.jsonl"))

    response = client.get("/dashboard-workflow?user_id=empty-phase12-user")
    assert response.status_code == 200
    workflow = response.json()["workflow"]
    assert workflow["summary"]["projects"] == 0
    assert workflow["timeline"] == []
    assert workflow["risk_trend"] == []
    assert workflow["finding_workflow"]["tasks"] == []
