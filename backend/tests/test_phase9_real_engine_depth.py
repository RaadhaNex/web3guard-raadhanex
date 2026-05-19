from fastapi.testclient import TestClient

from app.services.engine_depth import engine_depth_status
from app.services.scan_github_repo import _repo_readiness_findings, _repo_structure_summary
from main import app


def test_engine_depth_status_is_real_only_and_has_safety_boundaries():
    data = engine_depth_status()
    assert data["ok"] is True
    assert data["version"] == "web3guard-real-engine-depth-v9.0"
    assert data["safety_boundaries"]["no_fake_tool_output"] is True
    assert data["safety_boundaries"]["no_wallet_signing"] is True
    assert data["total_count"] >= 9


def test_engine_depth_endpoint_available():
    client = TestClient(app)
    response = client.get("/engine-depth/status")
    assert response.status_code == 200
    body = response.json()
    assert body["ready_count"] <= body["total_count"]
    assert "static_tools" in body
    assert "provider_integrations" in body


def test_github_repo_readiness_detects_missing_controls():
    summary = _repo_structure_summary([
        "package.json",
        "src/App.tsx",
        "contracts/Token.sol",
        "hardhat.config.ts",
    ])
    findings = _repo_readiness_findings(summary, 1)
    titles = {finding.title for finding in findings}
    assert "CI Security Workflow Missing" in titles
    assert "Dependency Lockfile Missing" in titles
    assert "Security Policy Missing" in titles
    assert "Test Evidence Missing" in titles
