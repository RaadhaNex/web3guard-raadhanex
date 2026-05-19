from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_security_passport_status():
    response = client.get("/security-passport/status")
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert "Pre-audit" in data["label"]
    assert "certified secure" in data["blocked_wording"]


def test_security_passport_project_and_external_link():
    user_id = "phase24-user"
    project = client.post(
        "/projects",
        json={
            "user_id": user_id,
            "name": "Phase 24 Passport Project",
            "website_url": "https://example.com",
            "chain": "Base",
            "project_type": "dApp",
        },
    )
    assert project.status_code == 200
    project_id = project.json()["project"]["id"]

    scan = client.post(
        "/scan-history",
        json={
            "user_id": user_id,
            "project_id": project_id,
            "module": "website",
            "project_name": "Phase 24 Passport Project",
            "score": 78,
            "risk_label": "Evidence Needed",
            "findings_count": 2,
            "critical_high_count": 0,
            "payload": {"headers": {"csp": "missing"}},
        },
    )
    assert scan.status_code == 200

    report = client.post(
        "/saved-reports",
        json={
            "user_id": user_id,
            "project_id": project_id,
            "report_id": "W3G-PHASE24-REPORT",
            "title": "Phase 24 readiness report",
            "report_hash": "hash_phase24_report",
            "overall_score": 72,
            "risk_label": "Evidence Needed",
            "visibility": "public",
            "payload": {"summary": "pre-audit readiness only"},
        },
    )
    assert report.status_code == 200

    link = client.post(
        "/security-passport/external-links",
        json={
            "user_id": user_id,
            "project_id": project_id,
            "title": "External audit reference",
            "url": "https://example.com/audit.pdf",
            "link_type": "audit",
        },
    )
    assert link.status_code == 200
    assert "not convert this into a certification" in link.json()["link"]["safe_wording"]

    response = client.get(f"/security-passport/project/{project_id}?user_id={user_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["latest_report"]["report_hash"] == "hash_phase24_report"
    assert data["public_share_card"]["subtitle"] == "Pre-audit readiness passport, not a certified audit."
    assert data["external_links"][0]["title"] == "External audit reference"


def test_security_passport_requires_valid_external_link():
    response = client.post(
        "/security-passport/external-links",
        json={
            "user_id": "phase24-user",
            "project_id": "phase24-project",
            "title": "Bad link",
            "url": "javascript:alert(1)",
            "link_type": "audit",
        },
    )
    assert response.status_code == 400


def test_security_passport_admin_overview():
    response = client.get("/security-passport/admin/overview")
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["passport_label"] == "Pre-audit readiness passport"
