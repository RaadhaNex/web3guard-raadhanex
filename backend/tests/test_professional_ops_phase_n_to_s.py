from fastapi.testclient import TestClient

from app.core.config import settings
from main import app

client = TestClient(app)


def test_phase_n_to_s_status_and_setup_endpoints(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "professional_reviewer_profiles_file", str(tmp_path / "reviewers.jsonl"))
    monkeypatch.setattr(settings, "professional_client_deliveries_file", str(tmp_path / "deliveries.jsonl"))
    monkeypatch.setattr(settings, "professional_worker_runs_file", str(tmp_path / "workers.jsonl"))
    monkeypatch.setattr(settings, "professional_monitoring_baselines_file", str(tmp_path / "baselines.jsonl"))
    monkeypatch.setattr(settings, "professional_monitoring_events_file", str(tmp_path / "events.jsonl"))
    monkeypatch.setattr(settings, "professional_monitoring_runs_file", str(tmp_path / "runs.jsonl"))
    monkeypatch.setattr(settings, "professional_webhook_events_file", str(tmp_path / "webhooks.jsonl"))

    status = client.get("/professional-ops/status")
    assert status.status_code == 200
    assert status.json()["direct_competition_public_claim_allowed"] is False
    assert status.json()["modules"]["phase_n_monitoring_dashboard_ui"] is True

    monitoring = client.get("/professional-ops/monitoring-dashboard")
    assert monitoring.status_code == 200
    assert monitoring.json()["phase"] == "N"

    github = client.get("/professional-ops/github-webhook/setup")
    assert github.status_code == 200
    assert github.json()["phase"] == "O"
    assert "webhook_url" in github.json()

    onchain = client.get("/professional-ops/onchain-webhook/setup")
    assert onchain.status_code == 200
    assert onchain.json()["phase"] == "P"


def test_phase_q_worker_stays_not_assessed_when_disabled(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "professional_worker_runs_file", str(tmp_path / "workers.jsonl"))
    monkeypatch.setattr(settings, "professional_worker_runner_enabled", False)

    response = client.post("/professional-ops/worker/run", json={
        "runner": "foundry",
        "authorization_confirmed": True,
        "real_only_acknowledged": True,
        "files": [{"path": "src/Test.sol", "content": "pragma solidity ^0.8.20; contract Test {}"}],
    })
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "Not Assessed"
    assert data["tool_status"]["enabled"] is False


def test_phase_r_reviewer_onboarding_gate(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "professional_reviewer_profiles_file", str(tmp_path / "reviewers.jsonl"))

    created = client.post("/professional-ops/reviewers", json={
        "name": "Security Reviewer",
        "email": "reviewer@example.com",
        "status": "invited",
        "capabilities": ["solidity", "web_api"],
    })
    assert created.status_code == 200
    reviewer_id = created.json()["reviewer"]["id"]
    assert created.json()["gate"]["approved_for_client_reports"] is False

    approved = client.post(f"/professional-ops/reviewers/{reviewer_id}/status", json={
        "status": "approved",
        "identity_verified": True,
        "nda_signed": True,
        "conflict_check_completed": True,
        "sample_review_completed": True,
        "quality_score": 90,
    })
    assert approved.status_code == 200
    assert approved.json()["gate"]["approved_for_client_reports"] is True


def test_phase_s_client_delivery_blocks_unsafe_claims_and_verifies_hash(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "professional_client_deliveries_file", str(tmp_path / "deliveries.jsonl"))

    blocked = client.post("/professional-ops/deliveries", json={
        "client_name": "Client",
        "project_name": "Project",
        "summary": "This is a certified audit and 100% secure.",
    })
    assert blocked.status_code == 400

    created = client.post("/professional-ops/deliveries", json={
        "client_name": "Client",
        "project_name": "Project",
        "summary": "Pre-audit readiness packet only. Not a certified audit.",
        "report_payload": {"report_id": "W3G-TEST"},
    })
    assert created.status_code == 200
    delivery = created.json()["delivery"]
    assert delivery["certified_audit"] is False

    verified = client.get(f"/professional-ops/deliveries/{delivery['id']}/verify")
    assert verified.status_code == 200
    assert verified.json()["record_valid"] is True
