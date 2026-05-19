from __future__ import annotations

from fastapi.testclient import TestClient

from main import app
from app.core import config

client = TestClient(app)


def test_phase13_production_deployment_qa_status_is_real_only(monkeypatch):
    monkeypatch.setattr(config.settings, "frontend_origin", "https://web3guard.example")
    monkeypatch.setattr(config.settings, "backend_url", "https://api.web3guard.example")
    monkeypatch.setattr(config.settings, "app_env", "production")
    monkeypatch.setattr(config.settings, "admin_token", "safe-admin-token-with-32-chars-123")
    monkeypatch.setattr(config.settings, "storage_mode", "local")
    monkeypatch.setattr(config.settings, "razorpay_enabled", False)
    monkeypatch.setattr(config.settings, "ai_send_code", False)
    monkeypatch.setattr(config.settings, "ai_fix_send_code", False)
    monkeypatch.setattr(config.settings, "deep_analysis_network_enabled", False)
    monkeypatch.setattr(config.settings, "deep_analysis_allow_dependency_install", False)

    response = client.get("/production-deployment-qa/status")
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["total"] >= 10
    assert data["score"] <= 100
    assert "does not certify" in data["real_only_note"].lower()
    keys = {item["key"] for item in data["checks"]}
    assert "payment_deferred" in keys
    assert "deep_tools_safe_defaults" in keys
    assert "supabase_service_role_ready" in keys


def test_phase13_production_deployment_qa_routes_and_commands():
    routes_response = client.get("/production-deployment-qa/routes")
    assert routes_response.status_code == 200
    routes = routes_response.json()["routes"]
    assert any(item["path"] == "/scanner/unified-url" for item in routes)
    assert any(item["path"] == "/report/verify" for item in routes)

    commands_response = client.get("/production-deployment-qa/commands")
    assert commands_response.status_code == 200
    commands = commands_response.json()["commands"]
    assert "npm run typecheck" in commands["frontend"]
    assert "npm run build" in commands["frontend"]
    assert "git push origin main" in commands["git"]
