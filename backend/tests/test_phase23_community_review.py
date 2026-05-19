from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_community_review_status():
    response = client.get("/community-review/status")
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert "verified_auditor_badge" in data["blocked_claims"]
    assert "certified_audit_claim" in data["blocked_claims"]


def test_community_review_request_requires_scope_ack():
    response = client.post(
        "/community-review/requests",
        json={
            "user_id": "phase23-user",
            "title": "Review my launch readiness",
            "scope_summary": "Public website and report evidence only.",
            "authorized_scope_confirmed": False,
        },
    )
    assert response.status_code >= 400


def test_community_review_request_feedback_and_template():
    create = client.post(
        "/community-review/requests",
        json={
            "user_id": "phase23-user",
            "project_id": "phase23-project",
            "title": "Review my launch readiness",
            "project_url": "https://example.com",
            "scope_summary": "Public website and report evidence only. No live exploitation is authorized.",
            "focus_areas": ["website", "github", "admin-opsec"],
            "authorized_scope_confirmed": True,
            "public_feedback_enabled": True,
        },
    )
    assert create.status_code == 200
    created = create.json()
    request_id = created["request"]["id"]
    assert created["request"]["status"] == "submitted"

    board = client.get("/community-review/project-board?user_id=phase23-user&project_id=phase23-project")
    assert board.status_code == 200
    assert board.json()["summary"]["requests"] >= 1

    feedback = client.post(
        "/community-review/feedback",
        json={
            "request_id": request_id,
            "user_id": "phase23-user",
            "project_id": "phase23-project",
            "summary": "Keep missing wallet evidence marked Not Assessed.",
            "evidence_note": "Reviewed public report scope only.",
            "severity": "info",
            "safe_feedback_acknowledged": True,
        },
    )
    assert feedback.status_code == 200
    assert feedback.json()["feedback"]["status"] == "needs_moderation"

    triage = client.post(
        "/community-review/triage",
        json={
            "request_id": request_id,
            "user_id": "phase23-user",
            "project_id": "phase23-project",
            "status": "ready_for_review",
            "summary": "Scope validated for manual review.",
            "next_step": "Assign reviewer.",
        },
    )
    assert triage.status_code == 200
    assert triage.json()["triage_item"]["status"] == "ready_for_review"

    template = client.post(
        "/community-review/templates/responsible-review",
        json={
            "project_name": "Phase 23 Project",
            "scope_summary": "Public evidence only.",
            "contact": "founder",
        },
    )
    assert template.status_code == 200
    message = template.json()["template"]["message"]
    assert "not a certified audit" in message
    assert "No wallet signing" in message


def test_community_review_admin_overview():
    response = client.get("/community-review/admin/overview")
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert "moderation_queue" in data["summary"]
