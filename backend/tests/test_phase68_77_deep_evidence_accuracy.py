from app.models.schemas import UnifiedUrlScanRequest
from app.services.deep_evidence_accuracy import build_deep_evidence_accuracy_package, phase68_77_status


def _payload(**kwargs):
    base = {
        "website_url": "https://example.com",
        "project_name": "Example",
        "project_type": "Full Web3 Startup",
        "chain": "Web only",
        "authorization_confirmed": True,
        "real_only_acknowledged": True,
    }
    base.update(kwargs)
    return UnifiedUrlScanRequest(**base)


async def _run(**kwargs):
    return await build_deep_evidence_accuracy_package({}, _payload(**kwargs))


import pytest


@pytest.mark.asyncio
async def test_har_artifact_creates_reachable_admin_finding():
    result = await _run(har_json='{"log":{"entries":[{"request":{"url":"https://example.com/admin","method":"GET"},"response":{"status":200}}]}}')
    assert result["summary"]["total_findings"] >= 1
    assert any(item["phase"] == "69" for item in result["normalized_findings"])


@pytest.mark.asyncio
async def test_authorized_api_bola_observation_is_critical():
    result = await _run(auth_test_context_json='[{"endpoint":"/api/orders/123","cross_account_access_proved":true,"status_code":200,"response_hash":"sha256-demo"}]')
    assert any(item["phase"] == "70" and item["severity"] == "critical" for item in result["normalized_findings"])


@pytest.mark.asyncio
async def test_secret_scanner_artifact_is_real_tool_finding():
    result = await _run(security_tool_artifacts_json='{"gitleaks":[{"RuleID":"generic-api-key","File":"src/config.ts"}]}')
    assert any(item["phase"] == "72" and item["category"] == "secret_scanning_artifact" for item in result["normalized_findings"])


@pytest.mark.asyncio
async def test_foundry_failure_artifact_creates_high_finding():
    result = await _run(foundry_test_output="[FAIL. Reason: invariant broken] test_invariant_assets_conserved()")
    assert any(item["phase"] == "74" and item["severity"] == "high" for item in result["normalized_findings"])


@pytest.mark.asyncio
async def test_wallet_unlimited_approval_is_detected():
    result = await _run(transaction_samples_json='[{"method":"approve","approval":"unlimited","spender":"0xabc"}]')
    assert any(item["phase"] == "75" and item["category"] == "unlimited_approval" for item in result["normalized_findings"])


def test_deep_evidence_router_status_available():
    from fastapi.testclient import TestClient
    from main import app

    client = TestClient(app)
    response = client.get("/deep-evidence/status")
    assert response.status_code == 200
    body = response.json()
    assert body["phase_range"] == "68-77"
    assert "77" in body["phases"]
