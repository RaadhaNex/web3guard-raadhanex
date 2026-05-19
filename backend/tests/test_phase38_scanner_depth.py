from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_phase38_status_is_honest_about_90_not_99():
    response = client.get("/scanner-depth/status")
    assert response.status_code == 200
    data = response.json()
    assert data["version"] == "web3guard-scanner-depth-hardening-v38.0"
    assert data["max_automated_pre_audit_coverage"] == 90
    assert data["security_guarantee_percent"] == 0
    assert any("No 99%" in item for item in data["not_claimed"])
    assert "100% secure" in data["blocked_claims"]


def test_phase38_empty_coverage_does_not_fake_depth():
    response = client.post("/scanner-depth/coverage", json={"project_name": "Empty", "real_only_acknowledged": True})
    assert response.status_code == 200
    data = response.json()
    assert data["coverage_depth_percent"] == 0
    assert data["target_gap_to_90"] == 90
    assert data["missing_modules"]
    assert all(item["status"] != "Assessed" for item in data["items"])


def test_phase38_strong_scope_can_reach_90_but_not_exceed_cap():
    payload = {
        "project_name": "Strong Scope",
        "slither_assessed": True,
        "aderyn_assessed": True,
        "semgrep_assessed": True,
        "osv_checked": True,
        "cisa_checked": True,
        "github_checked": True,
        "website_checked": True,
        "api_checked": True,
        "wallet_ux_checked": True,
        "admin_opsec_checked": True,
        "foundry_tests_run": True,
        "echidna_run": True,
        "mythril_run": True,
        "evidence_items_count": 10,
        "critical_findings": 0,
        "high_findings": 0,
        "real_only_acknowledged": True,
    }
    response = client.post("/scanner-depth/coverage", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["raw_module_points"] == 100
    assert data["coverage_depth_percent"] == 90
    assert data["target_gap_to_90"] == 0
    assert "not a certified audit" in data["safe_wording"]["required_disclaimer"].lower()


def test_phase38_critical_findings_cap_depth_below_90():
    payload = {
        "project_name": "Critical Blocker",
        "slither_assessed": True,
        "aderyn_assessed": True,
        "semgrep_assessed": True,
        "osv_checked": True,
        "cisa_checked": True,
        "github_checked": True,
        "website_checked": True,
        "api_checked": True,
        "wallet_ux_checked": True,
        "admin_opsec_checked": True,
        "foundry_tests_run": True,
        "echidna_run": True,
        "mythril_run": True,
        "evidence_items_count": 10,
        "critical_findings": 1,
        "real_only_acknowledged": True,
    }
    response = client.post("/scanner-depth/coverage", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["coverage_depth_percent"] == 72
    assert any("Critical unresolved" in item for item in data["blockers"])


def test_phase38_claim_check_blocks_fake_99_percent_security():
    response = client.post(
        "/scanner-depth/claim-check",
        json={"text": "Web3Guard makes projects 99% secure and 100% secure", "real_only_acknowledged": True},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is False
    assert data["blocked_matches"]
    assert "not a certified audit" in data["safe_rewrite"].lower()


def test_phase38_requires_real_only_acknowledgement():
    response = client.post("/scanner-depth/coverage", json={"real_only_acknowledged": False})
    assert response.status_code == 400
