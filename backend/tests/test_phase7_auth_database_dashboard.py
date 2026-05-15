from fastapi.testclient import TestClient

from main import app
from app.core import config

client = TestClient(app)


def test_phase7_db_status_is_local_first_and_real_only(tmp_path, monkeypatch):
    monkeypatch.setattr(config.settings, "db_profiles_file", str(tmp_path / "profiles.jsonl"))
    monkeypatch.setattr(config.settings, "db_projects_file", str(tmp_path / "projects.jsonl"))
    monkeypatch.setattr(config.settings, "db_scan_history_file", str(tmp_path / "scans.jsonl"))
    monkeypatch.setattr(config.settings, "db_saved_reports_file", str(tmp_path / "reports.jsonl"))
    response = client.get("/db/status")
    assert response.status_code == 200
    data = response.json()
    assert data["storage_mode_active"] == "local"
    assert data["supabase_configured"] is False
    assert "No fake" in data["real_only_note"]


def test_phase7_project_scan_and_dashboard_persist_locally(tmp_path, monkeypatch):
    monkeypatch.setattr(config.settings, "db_profiles_file", str(tmp_path / "profiles.jsonl"))
    monkeypatch.setattr(config.settings, "db_projects_file", str(tmp_path / "projects.jsonl"))
    monkeypatch.setattr(config.settings, "db_scan_history_file", str(tmp_path / "scans.jsonl"))
    monkeypatch.setattr(config.settings, "db_saved_reports_file", str(tmp_path / "reports.jsonl"))

    profile = client.post("/profile", json={"id": "user-1", "email": "u1@example.com", "full_name": "User One"})
    assert profile.status_code == 200
    assert profile.json()["profile"]["id"] == "user-1"

    project = client.post("/projects", json={"user_id": "user-1", "name": "Real MVP Token", "website_url": "https://example.com", "chain": "Polygon"})
    assert project.status_code == 200
    assert project.json()["project"]["name"] == "Real MVP Token"

    scan = client.post("/scan-history", json={"user_id": "user-1", "module": "website", "project_name": "Real MVP Token", "score": 79, "risk_label": "Low Risk", "findings_count": 2, "critical_high_count": 0})
    assert scan.status_code == 200

    report = client.post("/saved-reports", json={"user_id": "user-1", "report_id": "W3G-TEST", "title": "Real MVP Report", "available_score": 79, "risk_label": "Low Risk"})
    assert report.status_code == 200

    overview = client.get("/dashboard/overview?user_id=user-1")
    assert overview.status_code == 200
    data = overview.json()["overview"]
    assert data["totals"]["projects"] == 1
    assert data["totals"]["saved_scans"] == 1
    assert data["totals"]["saved_reports"] == 1
    assert data["totals"]["subscription_status"] == "not_connected_until_phase8_razorpay"


def test_phase7_local_qa_lists_auth_and_dashboard_routes():
    routes = client.get("/qa/frontend-routes").json()["routes"]
    assert "/auth/login" in routes
    assert "/auth/signup" in routes
    assert "/dashboard" in routes
    endpoints = client.get("/qa/backend-endpoints").json()["endpoints"]
    assert any(endpoint["path"] == "/db/status" for endpoint in endpoints)
    assert any(endpoint["path"] == "/dashboard/overview" for endpoint in endpoints)
