from __future__ import annotations

from fastapi.testclient import TestClient

from main import app
from app.core.config import settings
from app.services.professional_report import publish_report_record
from app.services.report_verification import (
    build_finding_status_workflow,
    build_report_verification_packet,
    report_verification_status,
    verify_public_report_record,
)


def sample_report() -> dict:
    return {
        "report_id": "W3G-DEMO-001",
        "report_hash": "a" * 64,
        "project_name": "Demo Protocol",
        "generated_at": "2026-05-19T00:00:00+00:00",
        "combined": {"available_score": 72, "risk_label": "Evidence Needed"},
        "score_split": {
            "website_surface_score": {"score": 80, "status": "assessed"},
            "contract_rule_score": {"score": 64, "status": "assessed"},
        },
        "module_matrix": [
            {"module": "website", "label": "Website", "assessed": True, "score": 80, "status": "assessed"},
            {"module": "wallet", "label": "Wallet UX", "assessed": False, "score": None, "status": "Not Assessed"},
        ],
        "evidence_summary": [
            {"module": "website", "module_label": "Website", "status": "assessed", "evidence": ["HTTPS observed", "CSP present"]},
        ],
        "evidence_required": [
            {"module": "wallet", "module_label": "Wallet UX", "status": "Not Assessed", "required_input": "Wallet UX notes", "next_step": "Submit wallet flow evidence"},
        ],
        "top_findings": [
            {
                "id": "F-1",
                "severity": "high",
                "module": "contract",
                "title": "Owner can pause transfers",
                "fix_guidance": {"verify": "Add timelock evidence and rerun scan."},
            }
        ],
    }


def test_report_verification_status_safe_boundaries():
    status = report_verification_status()
    assert status["ok"] is True
    assert status["version"].startswith("web3guard-report-verification")
    assert status["safety_boundaries"]["not_certified_audit"] is True
    assert "public_report_hash_verification" in status["capabilities"]


def test_report_payload_packet_contains_evidence_and_workflow():
    packet = build_report_verification_packet(sample_report())
    assert packet["ok"] is True
    assert packet["verification"]["metadata_integrity_ready"] is True
    assert packet["evidence_snapshot"]["evidence_items_count"] == 2
    assert packet["evidence_snapshot"]["not_assessed_modules"] == ["Wallet UX"]
    workflow = build_finding_status_workflow(sample_report())
    assert workflow["summary"]["manual_review_required"] == 1
    assert workflow["items"][0]["status"] == "manual_review_required"


def test_report_verification_endpoint_payload():
    client = TestClient(app)
    response = client.post("/report-verification/payload", json={"report": sample_report()})
    assert response.status_code == 200
    data = response.json()
    assert data["report_id"] == "W3G-DEMO-001"
    assert data["real_only_note"]


def test_public_report_verification_endpoint(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "public_reports_file", str(tmp_path / "public_reports.jsonl"))
    record = publish_report_record(sample_report(), visibility="public")
    result = verify_public_report_record(record["id"], "a" * 64)
    assert result["verified"] is True
    assert result["packet"]["report_id"] == "W3G-DEMO-001"

    client = TestClient(app)
    response = client.get(f"/report-verification/public/{record['id']}?report_hash={'a' * 64}")
    assert response.status_code == 200
    assert response.json()["verified"] is True

    mismatch = client.get(f"/report-verification/public/{record['id']}?report_hash={'b' * 64}")
    assert mismatch.status_code == 200
    assert mismatch.json()["verified"] is False
