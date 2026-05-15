from fastapi.testclient import TestClient

from main import app
from app.core import config

client = TestClient(app)


def _local_db(tmp_path, monkeypatch):
    monkeypatch.setattr(config.settings, "db_profiles_file", str(tmp_path / "profiles.jsonl"))
    monkeypatch.setattr(config.settings, "db_projects_file", str(tmp_path / "projects.jsonl"))
    monkeypatch.setattr(config.settings, "db_scan_history_file", str(tmp_path / "scans.jsonl"))
    monkeypatch.setattr(config.settings, "db_saved_reports_file", str(tmp_path / "reports.jsonl"))


def test_phase71_project_detail_scan_report_flow(tmp_path, monkeypatch):
    _local_db(tmp_path, monkeypatch)

    project_response = client.post("/projects", json={
        "user_id": "user-71",
        "name": "RAADHANEX Launch Project",
        "website_url": "https://example.com",
        "chain": "Polygon",
        "project_type": "ERC20",
        "description": "Real MVP project detail test",
    })
    assert project_response.status_code == 200
    project = project_response.json()["project"]

    scan_response = client.post("/scan-history", json={
        "user_id": "user-71",
        "project_id": project["id"],
        "module": "website",
        "project_name": project["name"],
        "score": 82,
        "risk_label": "Low Risk, Fix Recommended",
        "findings_count": 2,
        "critical_high_count": 0,
        "status": "saved_from_scanner",
        "payload": {"real_scan_result": True},
    })
    assert scan_response.status_code == 200
    scan = scan_response.json()["scan"]

    report_response = client.post("/saved-reports", json={
        "user_id": "user-71",
        "project_id": project["id"],
        "scan_id": scan["id"],
        "report_id": "W3G-71",
        "title": "Phase 7.1 Saved Report",
        "available_score": 82,
        "risk_label": "Low Risk, Fix Recommended",
        "visibility": "private",
        "payload": {"real_report": True},
    })
    assert report_response.status_code == 200
    report = report_response.json()["report"]

    detail_response = client.get(f"/projects/{project['id']}?user_id=user-71")
    assert detail_response.status_code == 200
    detail = detail_response.json()["detail"]
    assert detail["project"]["id"] == project["id"]
    assert detail["totals"]["scans"] == 1
    assert detail["totals"]["reports"] == 1
    assert detail["activity"][0]["type"] in {"report", "scan", "project"}

    scan_detail = client.get(f"/scan-history/{scan['id']}?user_id=user-71")
    assert scan_detail.status_code == 200
    assert scan_detail.json()["scan"]["payload"]["real_scan_result"] is True

    report_detail = client.get(f"/saved-reports/{report['id']}?user_id=user-71")
    assert report_detail.status_code == 200
    assert report_detail.json()["report"]["payload"]["real_report"] is True


def test_phase71_update_project_scan_and_report_status(tmp_path, monkeypatch):
    _local_db(tmp_path, monkeypatch)
    project = client.post("/projects", json={"user_id": "user-72", "name": "Before", "chain": "Ethereum"}).json()["project"]
    updated = client.patch(f"/projects/{project['id']}?user_id=user-72", json={"name": "After", "description": "Updated from dashboard"})
    assert updated.status_code == 200
    assert updated.json()["project"]["name"] == "After"

    scan = client.post("/scan-history", json={"user_id": "user-72", "project_id": project["id"], "module": "contract", "status": "open"}).json()["scan"]
    scan_update = client.patch(f"/scan-history/{scan['id']}?user_id=user-72", json={"status": "fixed", "notes": "Issue reviewed"})
    assert scan_update.status_code == 200
    assert scan_update.json()["scan"]["status"] == "fixed"

    report = client.post("/saved-reports", json={"user_id": "user-72", "project_id": project["id"], "report_id": "R-72", "title": "Report 72"}).json()["report"]
    report_update = client.patch(f"/saved-reports/{report['id']}?user_id=user-72", json={"visibility": "private", "status": "delivered"})
    assert report_update.status_code == 200
    assert report_update.json()["report"]["status"] == "delivered"
