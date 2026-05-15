from datetime import datetime, timezone

from fastapi.testclient import TestClient

from main import app
from app.services import ownership
from app.services.rate_limit import reset_rate_limits_for_tests

client = TestClient(app)


def test_scan_policy_lists_blocked_abuse_actions():
    response = client.get("/ownership/policy")
    assert response.status_code == 200
    data = response.json()
    assert data["private_network_blocking"] is True
    assert data["deep_scan_available"] is False
    assert any("Exploit automation" in item for item in data["blocked_actions"])
    assert "consent_text" in data


def test_ownership_challenge_rejects_private_hosts(tmp_path, monkeypatch):
    monkeypatch.setattr(ownership, "_storage_path", lambda: tmp_path / "ownership.jsonl")
    response = client.post(
        "/ownership/challenge",
        json={"website_url": "http://localhost:3000", "project_name": "Unsafe", "method": "well_known"},
    )
    assert response.status_code == 400
    assert "Private" in response.json()["detail"] or "blocked" in response.json()["detail"]


def test_well_known_ownership_verification_success(tmp_path, monkeypatch):
    monkeypatch.setattr(ownership, "_storage_path", lambda: tmp_path / "ownership.jsonl")
    monkeypatch.setattr(ownership, "validate_public_http_url", lambda raw_url: raw_url.strip())

    async def fake_check_well_known(url: str, token: str):
        return True, {"method": "well_known", "url": url, "token_found": True}

    monkeypatch.setattr(ownership, "_check_well_known", fake_check_well_known)
    created = client.post(
        "/ownership/challenge",
        json={"website_url": "https://example.com", "project_name": "Demo", "method": "well_known"},
    )
    assert created.status_code == 200
    challenge = created.json()
    assert challenge["token"].startswith("web3guard-raadhanex-verify-")
    assert challenge["well_known_path"] == "/.well-known/web3guard-verify.txt"

    verified = client.post(
        "/ownership/verify",
        json={
            "challenge_id": challenge["id"],
            "website_url": "https://example.com",
            "method": "well_known",
            "token": challenge["token"],
        },
    )
    assert verified.status_code == 200
    data = verified.json()
    assert data["verified"] is True
    assert data["status"] == "verified"


def test_contract_endpoint_requires_authorization_and_rate_limit_resets():
    reset_rate_limits_for_tests()
    response = client.post(
        "/scan/contract",
        json={"project_name": "No Auth", "solidity_code": "pragma solidity ^0.8.20; contract A { function x() public {} }", "authorization_confirmed": False},
    )
    assert response.status_code == 400
