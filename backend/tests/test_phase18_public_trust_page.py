from fastapi.testclient import TestClient

from app.models.schemas import ProjectCreate
from app.services.database_store import create_project
from main import app

client = TestClient(app)


def test_public_trust_status_blocks_audit_claims():
    response = client.get("/public-trust/status")
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert "Phase 18" in body["phase"]
    assert "Pre-audit launch-readiness reviewed" in body["public_wording"]
    assert any("Certified" in claim or "100%" in claim for claim in body["blocked_wording"])
    assert "does not certify" in body["real_only_note"].lower()


def test_public_trust_projects_empty_state_does_not_fake_data():
    response = client.get("/public-trust/projects?user_id=phase18-empty-user")
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["items"] == []
    assert "No stored projects" in body["empty_state"]
    assert "fake trust badges" in body["real_only_note"].lower()


def test_public_trust_project_page_marks_missing_modules_not_assessed():
    user_id = "phase18-trust-user"
    project = create_project(
        user_id,
        ProjectCreate(
            name="Phase18 Trust Project",
            website_url="https://example.org",
            chain="Polygon",
            project_type="Token launch",
        ),
    )
    response = client.get(f"/public-trust/project/{project.id}?user_id={user_id}")
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["project"]["name"] == "Phase18 Trust Project"
    assert body["public_wording"] == "Pre-audit launch-readiness reviewed"
    assert body["summary"]["not_assessed_modules"] >= 1
    assert any(module["status"] == "not_assessed" for module in body["modules"])
    assert "audited" in " ".join(body["blocked_claims"]).lower()
    assert "not a certified audit" in body["share_card"]["subtitle"].lower()


def test_public_trust_missing_project_404():
    response = client.get("/public-trust/project/missing-project?user_id=phase18-empty-user")
    assert response.status_code == 404
    assert "Project not found" in response.text
