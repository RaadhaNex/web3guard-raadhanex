from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_security_tests_status_is_defensive_only():
    response = client.get("/security-tests/status")
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert "Phase 17" in body["phase"]
    assert "foundry" in body["frameworks"]
    assert "exploit automation" in " ".join(body["blocked_capabilities"]).lower()
    assert "does not execute tools" in body["real_only_note"].lower()


def test_security_tests_generate_default_pack_without_fake_tool_output():
    response = client.post("/security-tests/generate", json={"contract_name": "VaultToken", "project_type": "ERC20 launch"})
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["contract_name"] == "VaultToken"
    frameworks = {template["framework"] for template in body["templates"]}
    assert {"foundry", "echidna", "slither", "aderyn", "semgrep"}.issubset(frameworks)
    assert all("review" in template["review_note"].lower() or "treat" in template["review_note"].lower() for template in body["templates"])
    assert "does not execute tools" in body["real_only_note"].lower()
    assert "attacking live third-party targets" in body["blocked_use_cases"]


def test_security_tests_generate_selected_frameworks_and_safe_identifier():
    response = client.post(
        "/security-tests/generate",
        json={
            "contract_name": "123 Bad-Name!!",
            "frameworks": ["foundry", "semgrep", "unknown"],
            "risk_focus": ["reentrancy", "owner abuse"],
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["contract_name"].startswith("Contract")
    assert body["frameworks"] == ["foundry", "semgrep"]
    assert len(body["templates"]) == 2
    filenames = {template["filename"] for template in body["templates"]}
    assert any(name.endswith(".security.t.sol") for name in filenames)
    assert "security/semgrep-web3guard.yml" in filenames
