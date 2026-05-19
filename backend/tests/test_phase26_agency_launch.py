from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_phase26_agency_status_is_real_only():
    response = client.get("/agency-launch/status")
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert "Phase 26" in data["phase"]
    assert "fake enterprise customers" in data["real_only_note"]
    assert "certified audit" in data["blocked_claims"]


def test_phase26_client_intake_white_label_and_handoff_flow():
    owner_user_id = "phase26-owner"
    client_payload = {
        "owner_user_id": owner_user_id,
        "client_name": "Nimbus DAO",
        "project_name": "Nimbus Launch",
        "website_url": "https://example.com",
        "project_summary": "Authorized pre-audit readiness support for the launch workspace.",
        "tags": ["dao", "launch"],
        "authorization_confirmed": True,
    }
    client_response = client.post("/agency-launch/clients", json=client_payload)
    assert client_response.status_code == 200
    saved_client = client_response.json()["client"]
    assert saved_client["client_name"] == "Nimbus DAO"

    intake_response = client.post(
        "/agency-launch/intake",
        json={
            "owner_user_id": owner_user_id,
            "client_name": "Nimbus DAO",
            "scope_summary": "Review owner-authorized launch evidence, report hash, and open readiness actions.",
            "requested_services": ["security_passport_setup"],
            "authorization_confirmed": True,
            "safe_use_acknowledged": True,
        },
    )
    assert intake_response.status_code == 200
    assert intake_response.json()["intake"]["status"] == "new"

    label_response = client.post(
        "/agency-launch/white-label",
        json={
            "owner_user_id": owner_user_id,
            "brand_name": "Nimbus Security Desk",
            "report_footer": "Pre-audit readiness handoff only.",
            "show_powered_by_raadhanex": True,
        },
    )
    assert label_response.status_code == 200

    handoff_response = client.post(
        "/agency-launch/handoff-packs",
        json={
            "owner_user_id": owner_user_id,
            "client_id": saved_client["id"],
            "executive_summary": "Readiness handoff prepared from available evidence.",
            "open_items": ["Schedule external certified audit before production launch."],
            "evidence_links": ["/security-passport"],
            "authorization_confirmed": True,
        },
    )
    assert handoff_response.status_code == 200
    handoff = handoff_response.json()["handoff_pack"]
    assert handoff["client_name"] == "Nimbus DAO"
    assert "not a certified audit" in handoff["client_email_template"]["body"].lower()

    portfolio_response = client.get(f"/agency-launch/portfolio?owner_user_id={owner_user_id}")
    assert portfolio_response.status_code == 200
    portfolio = portfolio_response.json()
    assert portfolio["totals"]["clients"] >= 1
    assert portfolio["totals"]["handoff_packs"] >= 1
    assert portfolio["latest_white_label_settings"]["brand_name"] == "Nimbus Security Desk"


def test_phase26_blocks_unsafe_claims():
    response = client.post(
        "/agency-launch/white-label",
        json={
            "owner_user_id": "phase26-owner",
            "brand_name": "Unsafe Agency",
            "report_footer": "Audited by Web3Guard and 100% secure.",
        },
    )
    assert response.status_code == 400
    assert "Blocked unsafe claim" in response.json()["detail"]


def test_phase26_requires_authorized_scope_for_client_and_intake():
    client_response = client.post(
        "/agency-launch/clients",
        json={"owner_user_id": "phase26-owner", "client_name": "No Scope"},
    )
    assert client_response.status_code == 400

    intake_response = client.post(
        "/agency-launch/intake",
        json={
            "owner_user_id": "phase26-owner",
            "client_name": "No Safe Ack",
            "scope_summary": "Authorized project scope is missing safe acknowledgement.",
            "authorization_confirmed": True,
            "safe_use_acknowledged": False,
        },
    )
    assert intake_response.status_code == 400
