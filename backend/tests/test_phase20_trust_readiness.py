from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_trust_readiness_status_is_safe():
    response = client.get("/trust-readiness/status")
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["score_type"] == "readiness_only_not_audit_score"
    assert "certified secure" in data["blocked_wording"]
    assert any(item["id"] == "evidence_completeness" for item in data["components"])


def test_trust_readiness_empty_user_has_no_fake_pass():
    response = client.get("/trust-readiness/score", params={"user_id": "phase20-empty-user"})
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["score_type"] == "Launch Trust Readiness — not an audit score"
    assert data["score"] <= 50
    assert data["summary"]["project_count"] == 0
    assert data["safe_public_wording"] == "Launch Trust Readiness reviewed"
    assert "100% secure" in data["blocked_wording"]


def test_trust_readiness_requires_user_id():
    response = client.get("/trust-readiness/score")
    assert response.status_code == 422
