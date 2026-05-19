from fastapi.testclient import TestClient

from main import app

client = TestClient(app)
OWNER = "phase29-owner"
PROJECT = "phase29-project"


def test_phase29_status_and_wording_guardrails():
    status = client.get("/trust-metrics/status")
    assert status.status_code == 200
    data = status.json()
    assert data["ok"] is True
    assert data["safety_boundaries"]["no_fake_public_metrics"] is True
    assert data["safety_boundaries"]["not_certified_audit"] is True
    assert any(surface["key"] == "public_safe_summary" for surface in data["surfaces"])

    safe = client.post("/trust-metrics/wording-check", json={"text": "External advisory records are mapped separately from Web3Guard-generated findings."})
    assert safe.status_code == 200
    assert safe.json()["safe"] is True

    unsafe = client.post("/trust-metrics/wording-check", json={"text": "This is a certified audit and 100% secure."})
    assert unsafe.status_code == 200
    assert unsafe.json()["safe"] is False
    assert unsafe.json()["blocked_claim"] in {"certified audit", "100% secure"}


def test_phase29_metric_snapshot_mapping_disclosure_and_public_summary():
    snapshot = client.post(
        "/trust-metrics/snapshots",
        json={
            "owner_user_id": OWNER,
            "project_id": PROJECT,
            "project_name": "Phase 29 Project",
            "external_advisory_count": 2,
            "web3guard_generated_finding_count": 1,
            "community_review_count": 3,
            "disclosure_count": 2,
            "resolved_disclosure_count": 1,
            "metric_sources": ["manual evidence ledger", "security passport"],
            "safe_public_metrics_acknowledged": True,
        },
    )
    assert snapshot.status_code == 200
    assert snapshot.json()["snapshot"]["web3guard_generated_finding_count"] == 1
    assert snapshot.json()["snapshot"]["unresolved_disclosure_count"] == 1

    mapping = client.post(
        "/trust-metrics/advisory-mappings",
        json={
            "owner_user_id": OWNER,
            "project_id": PROJECT,
            "project_name": "Phase 29 Project",
            "advisory_source": "osv",
            "advisory_id": "GHSA-test-1234",
            "advisory_title": "Dependency advisory for launch review",
            "severity": "high",
            "affected_component": "frontend dependency",
            "mapping_status": "affected",
            "authorization_confirmed": True,
        },
    )
    assert mapping.status_code == 200
    mapping_id = mapping.json()["mapping"]["id"]
    assert mapping.json()["mapping"]["not_claimed"][1].startswith("This mapping does not claim")

    disclosure = client.post(
        "/trust-metrics/disclosures",
        json={
            "owner_user_id": OWNER,
            "project_id": PROJECT,
            "project_name": "Phase 29 Project",
            "origin": "external_advisory",
            "related_mapping_id": mapping_id,
            "title": "Manual advisory disclosure tracking",
            "severity": "high",
            "status": "resolved",
            "recipient": "project owner",
            "summary": "Owner manually tracked advisory fix and resolution evidence.",
            "authorization_confirmed": True,
            "manual_send_acknowledged": True,
        },
    )
    assert disclosure.status_code == 200
    assert disclosure.json()["disclosure"]["status"] == "resolved"

    summary = client.get(f"/trust-metrics/public-summary?owner_user_id={OWNER}&project_id={PROJECT}")
    assert summary.status_code == 200
    metrics = summary.json()["metrics"]
    assert metrics["snapshot_count"] >= 1
    assert metrics["advisory_mapping_count"] >= 1
    assert metrics["disclosure_count"] >= 1
    assert metrics["external_advisory_mapping_count"] >= 1
    assert metrics["web3guard_generated_finding_count"] >= 1
    assert "Not a certified audit score." in summary.json()["not_claimed"]


def test_phase29_blocks_unsafe_metric_claims_and_requires_acknowledgement():
    missing_ack = client.post(
        "/trust-metrics/snapshots",
        json={
            "owner_user_id": OWNER,
            "project_id": "unsafe-project",
            "project_name": "Unsafe Project",
            "public_metric_note": "Transparency metric only.",
            "safe_public_metrics_acknowledged": False,
        },
    )
    assert missing_ack.status_code == 400
    assert "safe_public_metrics_acknowledged" in missing_ack.json()["detail"]

    unsafe = client.post(
        "/trust-metrics/snapshots",
        json={
            "owner_user_id": OWNER,
            "project_id": "unsafe-project",
            "project_name": "Unsafe Project",
            "public_metric_note": "Audited by Web3Guard and 100% secure.",
            "safe_public_metrics_acknowledged": True,
        },
    )
    assert unsafe.status_code == 400
    assert "Blocked unsafe public claim" in unsafe.json()["detail"]

    auto_send = client.post(
        "/trust-metrics/disclosures",
        json={
            "owner_user_id": OWNER,
            "project_id": "unsafe-project",
            "title": "Disclosure",
            "authorization_confirmed": True,
            "manual_send_acknowledged": False,
        },
    )
    assert auto_send.status_code == 400
    assert "does not auto-send" in auto_send.json()["detail"]
