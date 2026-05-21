from fastapi.testclient import TestClient

from app.core.config import settings
from app.services.public_proof_report import (
    approve_public_proof,
    build_public_proof_draft,
    publish_public_proof,
    verify_public_proof,
)
from main import app

client = TestClient(app)


def sample_report():
    return {
        "report_id": "W3G-TEST-D-001",
        "report_hash": "a" * 64,
        "project_name": "Phase D Protocol",
        "coverage": {"assessed_count": 4, "total_modules": 10, "coverage_percent": 40, "confidence": "medium"},
        "professional_scanner_summary": {
            "source_tool_counts": {"slither": 1, "aderyn": 1, "web3guard_local_rules": 1},
            "tool_status": {
                "slither": {"state": "ran", "findings_count": 1},
                "semgrep": {"state": "ran", "findings_count": 0},
                "aderyn": {"state": "ran", "findings_count": 1},
            },
        },
        "top_findings": [
            {
                "id": "f-1",
                "title": "Reentrancy risk",
                "severity": "critical",
                "category": "reentrancy",
                "source_tools": ["web3guard_local_rules", "slither", "aderyn"],
                "affected_file": "contracts/Vault.sol",
                "affected_line": 42,
                "evidence": "External call before state update.",
                "impact": "Funds may be drained.",
                "fix": "Use CEI and ReentrancyGuard.",
                "confidence": "high",
            }
        ],
    }


def test_phase_d_draft_blocks_until_terms_and_scope():
    draft = build_public_proof_draft({"report": sample_report(), "project_name": "Phase D Protocol"})["draft"]
    assert draft["status"] == "draft"
    assert draft["report_hash"] == "a" * 64
    assert draft["findings_count"] == 1
    assert draft["top_findings"][0]["affected_file"] == "contracts/Vault.sol"
    assert draft["approval_gate"]["eligible"] is False
    assert "Authorized scope" in " ".join(draft["approval_gate"]["reasons"])


def test_phase_d_approval_and_public_verification(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "public_proof_reports_file", str(tmp_path / "proof_reports.jsonl"))
    draft = build_public_proof_draft({
        "report": sample_report(),
        "authorized_scope_confirmed": True,
        "real_only_acknowledged": True,
    })["draft"]
    approved = approve_public_proof({
        "draft": draft,
        "decision": "approved_public_pre_audit",
        "reviewer": "RAADHANEX reviewer",
        "reviewer_reason": "Evidence reviewed for pre-audit public proof only.",
        "authorized_scope_confirmed": True,
        "real_only_acknowledged": True,
        "manual_review_completed": True,
    })
    assert approved["approved"] is True
    packet = approved["packet"]
    assert packet["approval"]["manual_review_claim_allowed"] is True
    published = publish_public_proof({"packet": packet, "visibility": "public"})["record"]
    assert published["status"] == "published"
    assert published["manual_review_claim_allowed"] is True
    verify = verify_public_proof(published["id"], integrity_hash=published["integrity_hash"], report_hash="a" * 64)
    assert verify["verified"] is True
    wrong = verify_public_proof(published["id"], integrity_hash="0" * 64)
    assert wrong["verified"] is False


def test_phase_d_router_publish_flow(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "public_proof_reports_file", str(tmp_path / "router_proof_reports.jsonl"))
    payload = {
        "report": sample_report(),
        "authorized_scope_confirmed": True,
        "real_only_acknowledged": True,
    }
    draft_res = client.post("/proof-reports/draft", json=payload)
    assert draft_res.status_code == 200, draft_res.text
    draft = draft_res.json()["draft"]
    approve_res = client.post("/proof-reports/approve", json={
        "draft": draft,
        "decision": "approved_public_pre_audit",
        "reviewer": "Reviewer",
        "reviewer_reason": "Approved for public pre-audit proof with limitations.",
        "authorized_scope_confirmed": True,
        "real_only_acknowledged": True,
        "manual_review_completed": False,
    })
    assert approve_res.status_code == 200, approve_res.text
    packet = approve_res.json()["packet"]
    publish_res = client.post("/proof-reports/publish", json={
        "packet": packet,
        "visibility": "public",
        "reviewer_reason": "Approved for public pre-audit proof with limitations.",
    })
    assert publish_res.status_code == 200, publish_res.text
    record = publish_res.json()["record"]
    get_res = client.get(f"/proof-reports/{record['id']}")
    assert get_res.status_code == 200, get_res.text
    verify_res = client.get(f"/proof-reports/{record['id']}/verify", params={"integrity_hash": record["integrity_hash"]})
    assert verify_res.status_code == 200
    assert verify_res.json()["verified"] is True


def test_phase_d_blocked_claims_prevent_approval():
    draft = build_public_proof_draft({
        "report": sample_report(),
        "authorized_scope_confirmed": True,
        "real_only_acknowledged": True,
        "requested_public_claim": "Certified audit and 100% secure",
    })["draft"]
    assert draft["approval_gate"]["eligible"] is False
    assert "certified audit" in [c.lower() for c in draft["approval_gate"]["blocked_claims_detected"]]
    approved = approve_public_proof({
        "draft": draft,
        "decision": "approved_public_pre_audit",
        "reviewer_reason": "Trying to approve blocked wording should fail gate.",
        "authorized_scope_confirmed": True,
        "real_only_acknowledged": True,
        "requested_public_claim": "Certified audit and 100% secure",
    })
    assert approved["approved"] is False
    assert approved["packet"]["status"] == "not_ready"
