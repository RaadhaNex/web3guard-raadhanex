from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.services.manual_review import (
    add_review_note,
    create_request,
    decide_report,
    import_findings,
    methodology,
    status,
    triage_finding,
)
from main import app


def test_manual_review_status_is_foundation_not_certified_audit():
    data = status()
    assert data["ok"] is True
    assert "Audit-company style workflow" in data["workflow_level"]
    assert data["certified_audit"] is False
    assert data["security_guarantee"] is False
    method = methodology()
    assert "Certified audit" in method["what_it_does_not_claim"]


def test_create_request_gates_scope_and_payment():
    scope_pending = create_request({"project_name": "Scope Pending Demo", "authorized_scope_confirmed": False})
    assert scope_pending["request"]["status"] == "scope_pending"

    payment_pending = create_request({
        "project_name": "Payment Pending Demo",
        "authorized_scope_confirmed": True,
        "payment_status": "not_verified",
    })
    assert payment_pending["request"]["status"] == "payment_pending"

    ready = create_request({
        "project_name": "Ready Demo",
        "authorized_scope_confirmed": True,
        "payment_status": "verified",
    })
    assert ready["request"]["status"] == "ready_for_triage"


def test_import_and_triage_real_scan_finding():
    request = create_request({
        "project_name": "Finding Demo",
        "authorized_scope_confirmed": True,
        "payment_status": "verified",
    })["request"]
    imported = import_findings({
        "request_id": request["id"],
        "scan_payload": {
            "bug_detection_coverage": {
                "confirmed_exposures": [
                    {
                        "title": "Public .env exposure",
                        "severity": "critical",
                        "confidence": "high",
                        "category": "public_secret_exposure",
                        "summary": "A public .env endpoint was reachable.",
                        "fix_hint": "Remove the file and rotate any exposed secrets.",
                        "evidence": {"checked_path": "/.env", "status": 200},
                    }
                ]
            }
        },
    })
    assert imported["imported"] == 1
    finding = imported["items"][0]
    assert finding["status"] == "needs_triage"
    assert finding["severity"] == "critical"
    assert finding["evidence_hash"]

    triaged = triage_finding({
        "finding_id": finding["id"],
        "status": "confirmed",
        "reviewer_note": "Evidence reviewed and confirmed under the authorized readiness scope.",
        "confirmed_evidence_note": "Confirmed via public safe path only.",
    })
    assert triaged["finding"]["status"] == "confirmed"


def test_report_ready_requires_payment_and_completed_triage():
    request = create_request({
        "project_name": "Decision Demo",
        "authorized_scope_confirmed": True,
        "payment_status": "verified",
    })["request"]
    imported = import_findings({
        "request_id": request["id"],
        "manual_findings": [{"title": "Needs triage", "severity": "medium", "evidence": {"source": "manual"}}],
    })
    finding_id = imported["items"][0]["id"]

    blocked = decide_report({
        "request_id": request["id"],
        "decision": "reviewed_report_ready",
        "reviewer_reason": "Trying to unlock before triage should be blocked.",
        "payment_verified": True,
    })
    assert blocked["decision"]["ready_for_reviewed_export"] is False
    assert blocked["decision"]["decision"] == "triage_in_progress"

    triage_finding({
        "finding_id": finding_id,
        "status": "false_positive",
        "reviewer_note": "Reviewer checked the supplied evidence and this item is a false positive.",
    })
    ready = decide_report({
        "request_id": request["id"],
        "decision": "reviewed_report_ready",
        "reviewer_reason": "All attached findings are triaged and payment/manual validation is verified.",
        "payment_verified": True,
    })
    assert ready["decision"]["ready_for_reviewed_export"] is True
    assert ready["decision"]["decision"] == "reviewed_report_ready"


def test_review_notes_block_fake_audit_claims():
    with pytest.raises(ValueError):
        add_review_note({"note": "This is a certified audit and the project is 100% secure."})


def test_manual_review_endpoints():
    client = TestClient(app)
    status_response = client.get("/manual-review/status")
    assert status_response.status_code == 200
    assert status_response.json()["certified_audit"] is False

    create_response = client.post("/manual-review/requests", json={
        "project_name": "Endpoint Review Demo",
        "authorized_scope_confirmed": True,
        "payment_status": "verified",
    })
    assert create_response.status_code == 200
    request_id = create_response.json()["request"]["id"]

    import_response = client.post("/manual-review/findings/import", json={
        "request_id": request_id,
        "scan_payload": {"findings_pipeline": {"real_findings": [{"title": "Semgrep finding", "severity": "high", "evidence": {"rule": "x"}}]}},
    })
    assert import_response.status_code == 200
    assert import_response.json()["imported"] == 1

    board_response = client.get("/manual-review/board")
    assert board_response.status_code == 200
    assert board_response.json()["quality_gates"]["certified_audit_claim"] is False
