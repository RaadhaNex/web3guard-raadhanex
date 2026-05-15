from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_security_hardening_status_real_only():
    response = client.get("/security-hardening/status")
    assert response.status_code == 200
    data = response.json()
    assert data["phase"].startswith("Mega Phase G")
    assert "checks" in data
    assert data["real_only_note"]


def test_security_headers_are_attached():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert response.headers.get("X-Web3Guard-Disclaimer") == "pre-audit-readiness-not-certified-audit"
    assert response.headers.get("X-Request-ID")


def test_production_qa_account_setup_matrix():
    response = client.get("/production-qa/account-setup")
    assert response.status_code == 200
    data = response.json()
    services = {item["service"] for item in data["accounts"]}
    assert "Supabase" in services
    assert "Razorpay" in services
    assert "Legal/CA review" in services


def test_request_body_limit_blocks_large_payload():
    response = client.post("/scan/contract", data="x" * 5_100_000, headers={"content-type": "application/json"})
    assert response.status_code == 413
    assert "max_request_body_bytes" in response.json()
