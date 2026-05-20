from app.models.schemas import UnifiedUrlScanRequest
from app.services.detection_expansion import _phase62_api_auth, _phase64_wallet, _phase65_business_logic, _phase66_defi, _phase67_false_positive


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


def test_phase62_openapi_admin_without_security_becomes_real_evidence_finding():
    payload = _payload(openapi_json='{"openapi":"3.0.0","paths":{"/admin/users":{"get":{"responses":{"200":{"description":"ok"}}}}}}')
    result = _phase62_api_auth(payload)
    assert result["state"] == "Assessed"
    assert result["findings"]
    assert result["findings"][0]["rule_id"] == "PH62-OPENAPI-ADMIN-NO-SECURITY"


def test_phase64_wallet_unlimited_approval_sample_is_detected():
    payload = _payload(transaction_samples_json='[{"method":"approve","amount":"115792089237316195423570985008687907853269984665640564039457584007913129639935","spender":"0xabc"}]')
    result = _phase64_wallet(payload)
    assert result["state"] == "Assessed"
    assert any(item["rule_id"] == "PH64-UNLIMITED-APPROVAL" for item in result["findings"])


def test_phase65_business_context_creates_manual_review_items_without_fake_bug():
    payload = _payload(business_context_json='{"roles":["user","admin"],"critical_flows":["payment report unlock", "referral reward"]}')
    result = _phase65_business_logic(payload)
    assert result["state"] == "Assessed"
    assert len(result["review_items"]) >= 2
    assert result["findings"] == []


def test_phase66_failed_defi_invariant_is_high_evidence_finding():
    payload = _payload(defi_simulation_json='{"invariants":[{"name":"solvency","passed":false,"trace":"local fork test"}]}')
    result = _phase66_defi(payload)
    assert result["state"] == "Assessed"
    assert result["findings"][0]["severity"] == "high"
    assert result["findings"][0]["rule_id"] == "PH66-INVARIANT-FAILED"


def test_phase67_precision_requires_triage_context():
    payload = _payload(review_context_json='{"triaged_findings":[{"status":"confirmed"},{"status":"false_positive"},{"status":"fixed"}]}')
    result = _phase67_false_positive(payload, [{"id":"a"}])
    assert result["state"] == "Assessed"
    assert result["estimated_precision_from_triage_percent"] == 66.67


def test_detection_expansion_status_router_available():
    from fastapi.testclient import TestClient
    from main import app

    client = TestClient(app)
    response = client.get("/detection-expansion/status")
    assert response.status_code == 200
    body = response.json()
    assert body["phase_range"] == "60-67"
    assert "60" in body["phases"]
