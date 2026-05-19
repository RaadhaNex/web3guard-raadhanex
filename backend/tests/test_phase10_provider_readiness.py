from fastapi.testclient import TestClient

from main import app
from app.services.provider_readiness import provider_readiness_status
from app.services.wallet_risk_integrations import wallet_risk_api_status


def test_provider_readiness_status_safe_defaults():
    status = provider_readiness_status()
    assert status["ok"] is True
    assert status["version"].startswith("web3guard-provider-readiness")
    assert status["total_count"] >= 3
    provider_keys = {item["key"] for item in status["providers"]}
    assert {"etherscan_v2", "goplus", "github_public_repo"}.issubset(provider_keys)
    assert status["safety_boundaries"]["no_wallet_signing"] is True
    assert status["safety_boundaries"]["no_private_key_collection"] is True
    assert status["safety_boundaries"]["not_certified_audit"] is True


def test_provider_readiness_endpoint():
    client = TestClient(app)
    response = client.get("/provider-readiness/status")
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert isinstance(data["providers"], list)
    assert any(item["key"] == "etherscan_v2" for item in data["providers"])


def test_wallet_risk_status_lists_provider_endpoints():
    status = wallet_risk_api_status()
    assert status["no_wallet_connection"] is True
    assert status["no_private_key_collection"] is True
    assert "address_security" in status["provider_endpoints"]
    assert "approval_security" in status["provider_endpoints"]
