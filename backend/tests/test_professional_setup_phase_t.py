from app.core.config import settings
from app.services import professional_setup_t as setup
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_phase_t_status_and_env_checklist(monkeypatch):
    monkeypatch.setattr(settings, "backend_url", "https://backend.example")
    monkeypatch.setattr(settings, "frontend_origin", "https://frontend.example")
    monkeypatch.setattr(settings, "admin_token", "secret-admin-token-value")
    monkeypatch.setattr(settings, "public_proof_signing_secret", "secret-proof-value")
    monkeypatch.setattr(settings, "github_webhook_secret", "secret-github-value")
    monkeypatch.setattr(settings, "onchain_webhook_secret", "secret-onchain-value")
    result = setup.env_checklist()
    assert result["required_ready"] is True
    assert result["missing_required_count"] == 0
    assert "safe_worker_on_after_isolated_runtime" in result["snippets"]
    response = client.get("/professional-setup/status")
    assert response.status_code == 200
    assert response.json()["phase"] == "T"


def test_worker_gate_blocks_main_api_enablement(monkeypatch):
    monkeypatch.setattr(settings, "professional_worker_enabled", True)
    monkeypatch.setattr(settings, "professional_worker_runner_enabled", False)
    monkeypatch.setattr(settings, "worker_execution_enabled", True)
    monkeypatch.setattr(settings, "professional_worker_service_role", "api")
    monkeypatch.setattr(settings, "professional_worker_isolated_runtime_confirmed", False)
    monkeypatch.setattr(settings, "professional_worker_allow_local_execution", False)
    result = setup.worker_enablement_gate()
    assert result["currently_enabled"]["effective_professional_runner_enabled"] is True
    assert result["safe_to_turn_true"] is False
    assert result["blockers"]
    assert "PROFESSIONAL_WORKER_ENABLED" in result["answer_to_user_env_question"]


def test_worker_gate_can_be_green_when_isolated_and_tools_ready(monkeypatch, tmp_path):
    forge = tmp_path / "forge"
    echidna = tmp_path / "echidna"
    forge.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    echidna.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    monkeypatch.setattr(settings, "professional_worker_enabled", True)
    monkeypatch.setattr(settings, "professional_worker_runner_enabled", True)
    monkeypatch.setattr(settings, "worker_execution_enabled", True)
    monkeypatch.setattr(settings, "professional_worker_service_role", "isolated_worker")
    monkeypatch.setattr(settings, "professional_worker_isolated_runtime_confirmed", True)
    monkeypatch.setattr(settings, "professional_worker_allow_local_execution", True)
    monkeypatch.setattr(settings, "professional_worker_cleanup_workspace", True)
    monkeypatch.setattr(settings, "professional_worker_network_enabled", False)
    monkeypatch.setattr(settings, "foundry_enabled", True)
    monkeypatch.setattr(settings, "foundry_binary", str(forge))
    monkeypatch.setattr(settings, "echidna_enabled", True)
    monkeypatch.setattr(settings, "echidna_binary", str(echidna))
    result = setup.worker_enablement_gate()
    assert result["safe_to_turn_true"] is True
    assert result["tool_status"]["foundry"]["state"] == "Ready"
    assert result["tool_status"]["echidna"]["state"] == "Ready"


def test_phase_t_api_routes():
    for path in [
        "/professional-setup/env-checklist",
        "/professional-setup/webhooks",
        "/professional-setup/worker-gate",
        "/professional-setup/production-readiness",
        "/professional-setup/manual-actions",
    ]:
        response = client.get(path)
        assert response.status_code == 200
        assert response.json()["ok"] is True
