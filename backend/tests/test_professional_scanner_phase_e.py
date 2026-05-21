from __future__ import annotations

import json
from pathlib import Path

from app.services import review_ops


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


def _isolate(monkeypatch, tmp_path: Path) -> dict[str, Path]:
    paths = {
        "requests": tmp_path / "manual_review_requests.jsonl",
        "findings": tmp_path / "manual_review_findings.jsonl",
        "notes": tmp_path / "manual_review_notes.jsonl",
        "decisions": tmp_path / "manual_review_report_decisions.jsonl",
        "assignments": tmp_path / "manual_review_assignments.jsonl",
        "fixes": tmp_path / "manual_review_fix_verifications.jsonl",
        "approvals": tmp_path / "manual_review_approval_events.jsonl",
        "proofs": tmp_path / "public_proof_reports.jsonl",
    }
    monkeypatch.setattr(review_ops, "REQUESTS_FILE", paths["requests"])
    monkeypatch.setattr(review_ops, "FINDINGS_FILE", paths["findings"])
    monkeypatch.setattr(review_ops, "NOTES_FILE", paths["notes"])
    monkeypatch.setattr(review_ops, "DECISIONS_FILE", paths["decisions"])
    monkeypatch.setattr(review_ops, "ASSIGNMENTS_FILE", paths["assignments"])
    monkeypatch.setattr(review_ops, "FIX_VERIFICATIONS_FILE", paths["fixes"])
    monkeypatch.setattr(review_ops, "APPROVAL_EVENTS_FILE", paths["approvals"])

    # Public proof service reads settings.public_proof_reports_file at call time.
    from app.services import public_proof_report

    monkeypatch.setattr(public_proof_report.settings, "public_proof_reports_file", str(paths["proofs"]))
    for path in paths.values():
        _write_jsonl(path, [])
    return paths


def test_phase_e_assignment_fix_verification_and_approval(monkeypatch, tmp_path):
    _isolate(monkeypatch, tmp_path)
    request = {
        "id": "mrev_test",
        "created_at": "2026-01-01T00:00:00Z",
        "updated_at": "2026-01-01T00:00:00Z",
        "user_id": "user_1",
        "project_id": "project_1",
        "project_name": "Vault Project",
        "project_url": "https://example.com",
        "review_type": "pre_audit_readiness",
        "authorized_scope_confirmed": True,
        "payment_status": "verified",
        "scope_summary": "Review submitted Solidity source and scanner findings.",
        "status": "ready_for_triage",
    }
    finding = {
        "id": "mfind_test",
        "created_at": "2026-01-01T00:00:00Z",
        "updated_at": "2026-01-01T00:00:00Z",
        "request_id": "mrev_test",
        "user_id": "user_1",
        "project_id": "project_1",
        "title": "Unchecked external call",
        "severity": "high",
        "status": "confirmed",
        "source": "slither",
        "affected_file": "contracts/Vault.sol",
        "affected_line": 42,
        "reviewer_note": "Confirmed external call before state update.",
    }
    _write_jsonl(review_ops.REQUESTS_FILE, [request])
    _write_jsonl(review_ops.FINDINGS_FILE, [finding])

    assignment = review_ops.create_assignment({"request_id": "mrev_test", "reviewer": "N. Reviewer", "role": "lead_reviewer"})
    assert assignment["ok"] is True
    assert assignment["assignment"]["admin_only"] is True

    fix = review_ops.record_fix_verification(
        {
            "request_id": "mrev_test",
            "finding_id": "mfind_test",
            "reviewer": "N. Reviewer",
            "status": "verified",
            "fix_summary": "Moved state update before external call and added guard.",
            "evidence": {"commit": "abc123", "test": "forge test"},
            "test_commands": ["forge test"],
            "reviewer_note": "Fix verified by code review and regression command output.",
        }
    )
    assert fix["updated_finding"]["status"] == "fixed"
    assert fix["updated_finding"]["verification_status"] == "human_verified_fixed"

    readiness = review_ops.report_readiness("mrev_test")
    assert readiness["eligible_for_reviewed_pre_audit_report"] is True
    assert readiness["finding_summary"]["by_status"]["fixed"] == 1

    approval = review_ops.approve_reviewed_report(
        {
            "request_id": "mrev_test",
            "decision": "approved_reviewed_pre_audit",
            "reviewer": "N. Reviewer",
            "reviewer_reason": "All submitted findings were triaged and verified inside the authorized scope.",
            "report_hash": "report_hash_123",
        }
    )
    assert approval["approved"] is True
    assert approval["packet"]["certified_audit"] is False
    assert approval["packet"]["integrity_hash"]


def test_phase_e_blocks_unsafe_claims(monkeypatch, tmp_path):
    _isolate(monkeypatch, tmp_path)
    _write_jsonl(
        review_ops.REQUESTS_FILE,
        [
            {
                "id": "mrev_claim",
                "project_name": "Claim Project",
                "authorized_scope_confirmed": True,
                "payment_status": "verified",
                "status": "ready_for_triage",
            }
        ],
    )
    _write_jsonl(
        review_ops.FINDINGS_FILE,
        [
            {
                "id": "mfind_claim",
                "request_id": "mrev_claim",
                "title": "Info finding",
                "severity": "info",
                "status": "false_positive",
                "reviewer_note": "Reviewed and rejected as false positive.",
            }
        ],
    )
    readiness = review_ops.report_readiness("mrev_claim", {"public_claim": "Certified audit and 100% secure"})
    assert readiness["eligible_for_reviewed_pre_audit_report"] is False
    assert any("Blocked" in reason for reason in readiness["reasons"])


def test_phase_e_admin_board_groups_ready_and_blocked(monkeypatch, tmp_path):
    _isolate(monkeypatch, tmp_path)
    _write_jsonl(
        review_ops.REQUESTS_FILE,
        [
            {"id": "ready", "project_name": "Ready", "authorized_scope_confirmed": True, "payment_status": "verified", "status": "ready_for_triage"},
            {"id": "blocked", "project_name": "Blocked", "authorized_scope_confirmed": False, "payment_status": "not_verified", "status": "scope_pending"},
        ],
    )
    _write_jsonl(
        review_ops.FINDINGS_FILE,
        [
            {"id": "f1", "request_id": "ready", "title": "Fixed", "severity": "medium", "status": "fixed"},
            {"id": "f2", "request_id": "blocked", "title": "Needs triage", "severity": "high", "status": "needs_triage"},
        ],
    )
    board = review_ops.admin_board()
    assert board["ok"] is True
    assert len(board["ready_for_approval"]) == 1
    assert len(board["blocked_or_in_progress"]) == 1
