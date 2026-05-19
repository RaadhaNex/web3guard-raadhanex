from fastapi.testclient import TestClient

from main import app
from app.services import worker_execution as svc

client = TestClient(app)


def test_phase27_worker_status_real_only_matrix():
    response = client.get("/worker-execution/status")
    assert response.status_code == 200
    data = response.json()
    assert data["version"] == "web3guard-real-worker-execution-v27.0"
    assert data["safety_boundaries"]["no_fake_tool_output"] is True
    assert data["safety_boundaries"]["no_private_key_collection"] is True
    assert data["safety_boundaries"]["no_wallet_signing"] is True
    assert {tool["key"] for tool in data["tools"]} >= {"slither", "aderyn", "semgrep", "foundry", "echidna", "mythril"}
    assert all(tool["status"] in {"Ready", "Tool Not Installed", "Provider Not Configured", "Manual"} for tool in data["tools"])


def test_phase27_plan_requires_real_only_acknowledgement():
    response = client.post("/worker-execution/plan", json={"tools": ["slither"], "real_only_acknowledged": False})
    assert response.status_code == 400
    assert "Real-only" in response.json()["detail"]


def test_phase27_plan_returns_no_fake_worker_steps():
    response = client.post("/worker-execution/plan", json={"project_type": "Solidity", "tools": ["slither", "foundry", "mythril"], "real_only_acknowledged": True})
    assert response.status_code == 200
    data = response.json()
    assert data["project_type"] == "Solidity"
    assert [step["tool"] for step in data["steps"]] == ["slither", "foundry", "mythril"]
    assert all("Do not invent findings" in step["evidence_policy"] for step in data["steps"])
    assert "No fake scanner output" in data["blocked_actions"]


def test_phase27_probe_missing_tools_are_status_only(monkeypatch):
    monkeypatch.setattr(svc.settings, "worker_allow_version_probe", True)
    monkeypatch.setattr(svc.settings, "worker_execution_enabled", False)
    data = svc.probe_worker_tools(["foundry"])
    assert data["ok"] is True
    assert data["results"]["foundry"]["status"] in {"Provider Not Configured", "Tool Not Installed", "Manual"}
    assert data["results"]["foundry"]["real_findings"] == 0


def test_phase27_probe_can_be_disabled_without_subprocess(monkeypatch):
    monkeypatch.setattr(svc.settings, "worker_allow_version_probe", False)
    data = svc.probe_worker_tools(["slither"])
    assert data["probe_status"] == "Manual / Not Assessed"
    assert data["results"] == {}
