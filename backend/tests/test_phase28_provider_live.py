from fastapi.testclient import TestClient

from app.core.config import settings
from main import app

client = TestClient(app)


def test_provider_live_status_truthful_defaults():
    response = client.get("/provider-live/status")
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["version"].startswith("web3guard-provider-live-integrations-v28")
    assert data["total_count"] >= 4
    labels = {surface["key"]: surface["status"] for surface in data["surfaces"]}
    assert labels["explorer_verified_source"] in {"Ready", "Needs API Key", "Provider Not Configured"}
    assert labels["advisory_live_sources"] in {"Ready", "Provider Not Configured"}
    assert data["safety_boundaries"]["no_fake_provider_data"] is True
    assert data["safety_boundaries"]["no_wallet_signing"] is True


def test_explorer_source_returns_needs_key_without_fake_data(monkeypatch):
    monkeypatch.setattr(settings, "provider_live_enabled", True)
    monkeypatch.setattr(settings, "provider_live_network_enabled", True)
    monkeypatch.setattr(settings, "etherscan_api_key", None)
    response = client.post(
        "/provider-live/explorer/source",
        json={
            "chain": "ethereum",
            "address": "0x0000000000000000000000000000000000000000",
            "real_only_acknowledged": True,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "Needs API Key"
    assert data["source_available"] is False
    assert "fake" in data["real_only_note"].lower()


def test_provider_live_requires_real_only_acknowledgement():
    response = client.post(
        "/provider-live/explorer/source",
        json={
            "chain": "ethereum",
            "address": "0x0000000000000000000000000000000000000000",
            "real_only_acknowledged": False,
        },
    )
    assert response.status_code == 400


def test_advisory_search_disabled_is_not_assessed_without_fake_records(monkeypatch):
    monkeypatch.setattr(settings, "provider_live_enabled", True)
    monkeypatch.setattr(settings, "provider_live_advisory_sources_enabled", False)
    response = client.post(
        "/provider-live/advisory/search",
        json={"source": "osv", "package_name": "lodash", "ecosystem": "npm", "real_only_acknowledged": True},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "Provider Not Configured"
    assert data["records"] == []
    assert "No fake advisory" in data["real_only_note"]


def test_github_repo_check_validates_scope_acknowledgement():
    response = client.post(
        "/provider-live/github/repo-check",
        json={
            "repo_url": "https://github.com/openzeppelin/openzeppelin-contracts",
            "authorization_confirmed": False,
            "real_only_acknowledged": True,
        },
    )
    assert response.status_code == 400


def test_goplus_status_preserves_no_wallet_signing_boundary():
    response = client.get("/provider-live/goplus/status")
    assert response.status_code == 200
    data = response.json()
    assert data["provider"] == "goplus"
    assert data["safety_boundaries"]["no_wallet_connect"] is True
    assert data["safety_boundaries"]["no_transaction_signing"] is True
