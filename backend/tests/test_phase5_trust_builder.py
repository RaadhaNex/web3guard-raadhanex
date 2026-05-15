from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_trust_policy_has_no_overclaim_boundaries():
    response = client.get("/trust/policy")
    assert response.status_code == 200
    data = response.json()
    joined = " ".join(data["what_we_do_not_do"])
    assert "100% secure" in joined
    assert "exploit automation" in joined
    assert data["company"] == "RAADHANEX"


def test_methodology_endpoint_exposes_weights_and_penalties():
    response = client.get("/trust/methodology")
    assert response.status_code == 200
    data = response.json()
    assert data["module_weights"]["smart_contract"] == 35
    assert data["penalties"]["critical"] == -25
    assert "preliminary" in data["disclaimer"].lower()


def test_sample_report_detail_returns_priority_actions():
    response = client.get("/sample-reports/staking-sample")
    assert response.status_code == 200
    data = response.json()
    assert data["score"] == 54
    assert data["priority_actions"]
    assert "Manual" in data["package_recommendation"]
