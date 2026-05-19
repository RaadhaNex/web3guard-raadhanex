from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_phase30_launch_final_status_and_gates_are_truthful():
    response = client.get("/launch-final/status")
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["version"] == "web3guard-launch-final-v30.0"
    assert data["total_gates"] >= 6
    assert data["passed_gates"] <= data["total_gates"]
    assert data["manual_approval_required"] is True
    assert "Not a certified audit company claim." in data["not_claimed"]
    assert "private key" in data["never_collect"]
    assert "Provider Not Configured" in data["safe_missing_labels"]
    assert any(gate["key"] == "safe_public_claims" and gate["passed"] for gate in data["gates"])


def test_phase30_claim_checker_blocks_unsafe_public_copy():
    safe = client.post(
        "/launch-final/claim-check",
        json={"text": "Pre-audit launch readiness evidence with Not Assessed labels for missing providers."},
    )
    assert safe.status_code == 200
    assert safe.json()["safe"] is True

    unsafe = client.post(
        "/launch-final/claim-check",
        json={"text": "Web3Guard audited this project and it is 100% secure."},
    )
    assert unsafe.status_code == 200
    body = unsafe.json()
    assert body["safe"] is False
    assert body["blocked_claim"] in {"100% secure", "web3guard audited"}
    assert "pre-audit" in body["rewrite_hint"].lower()


def test_phase30_public_release_checklist_deploy_plan_and_notes():
    checklist = client.get("/launch-final/public-release-checklist")
    assert checklist.status_code == 200
    sections = checklist.json()["sections"]
    assert any(section["area"] == "Local build verification" for section in sections)
    assert any("npm run build" in item for section in sections for item in section["items"])

    deploy = client.get("/launch-final/deploy-verification")
    assert deploy.status_code == 200
    commands = deploy.json()["commands"]
    assert "python -m pytest -q" in commands["backend"]
    assert "npm run typecheck" in commands["frontend"]
    assert any("git push origin main" == command for command in commands["git"])

    notes = client.get("/launch-final/release-notes")
    assert notes.status_code == 200
    payload = notes.json()
    assert "Not a certified audit." in payload["not_claimed"]
    assert any("Trust Metrics Engine" in layer for layer in payload["included_layers"])
    assert "Publish only after" in payload["release_gate"]


def test_phase30_remaining_work_has_real_next_steps():
    response = client.get("/launch-final/remaining-work")
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    areas = {item["area"] for item in data["next_deep_workstreams"]}
    assert "Live deploy verification" in areas
    assert "Real worker execution hosting" in areas
    assert "Legal + trust operations" in areas
