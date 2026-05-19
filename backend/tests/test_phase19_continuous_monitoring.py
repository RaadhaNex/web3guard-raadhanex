from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_continuous_monitoring_status():
    response = client.get("/continuous-monitoring/status")
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert "stale_report" in data["supported_checks"]
    assert "real_only_note" in data


def test_create_config_requires_authorization():
    response = client.post("/continuous-monitoring/configs", json={
        "user_id": "phase19-user",
        "project_name": "Phase19 Project",
        "authorization_confirmed": False,
        "real_only_acknowledged": True,
    })
    assert response.status_code == 400


def test_create_config_and_manual_recheck_no_fake_network():
    payload = {
        "user_id": "phase19-user",
        "project_name": "Phase19 Project",
        "website_url": "https://example.com",
        "github_repo_url": "https://github.com/example/repo",
        "chain": "ethereum",
        "cadence": "manual",
        "checks": ["stale_report", "scan_age", "website_passive", "github_repo_change", "sentinel_alert_queue"],
        "authorization_confirmed": True,
        "real_only_acknowledged": True,
    }
    created = client.post("/continuous-monitoring/configs", json=payload)
    assert created.status_code == 200
    config = created.json()
    assert config["id"].startswith("cmcfg_")
    assert config["website_url"] == "https://example.com"

    recheck = client.post("/continuous-monitoring/recheck", json={
        "config_id": config["id"],
        "user_id": "phase19-user",
        "force": True,
        "real_only_acknowledged": True,
    })
    assert recheck.status_code == 200
    result = recheck.json()
    assert result["ok"] is True
    assert result["ran"] is True
    assert "new_alerts" in result
    assert any(snapshot["snapshot_type"] == "website_passive" for snapshot in result["snapshots"])


def test_user_and_admin_dashboards():
    user_response = client.get("/continuous-monitoring/user?user_id=phase19-user")
    assert user_response.status_code == 200
    assert user_response.json()["ok"] is True

    admin_response = client.get("/continuous-monitoring/admin")
    assert admin_response.status_code == 200
    data = admin_response.json()
    assert data["ok"] is True
    assert "alerts_by_severity" in data


def test_due_recheck_endpoint_real_only():
    response = client.post("/continuous-monitoring/recheck-due", json={"limit": 5, "real_only_acknowledged": True})
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert "schedule_note" in data
