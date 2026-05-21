from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from app.core.config import settings
from app.services.mega_phase_e_store import append_jsonl, new_id, now_iso, read_jsonl, rewrite_jsonl, sort_created, storage_path
from app.services.public_proof_report import (
    ALLOWED_PUBLIC_WORDING,
    BLOCKED_CLAIMS,
    REAL_ONLY_NOTE,
    approve_public_proof,
    build_public_proof_draft,
    publish_public_proof,
)

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "db"
REQUESTS_FILE = DATA_DIR / "manual_review_requests.jsonl"
FINDINGS_FILE = DATA_DIR / "manual_review_findings.jsonl"
NOTES_FILE = DATA_DIR / "manual_review_notes.jsonl"
DECISIONS_FILE = DATA_DIR / "manual_review_report_decisions.jsonl"

ASSIGNMENTS_FILE = Path(getattr(settings, "manual_review_assignments_file", "app/data/db/manual_review_assignments.jsonl"))
FIX_VERIFICATIONS_FILE = Path(getattr(settings, "manual_review_fix_verifications_file", "app/data/db/manual_review_fix_verifications.jsonl"))
APPROVAL_EVENTS_FILE = Path(getattr(settings, "manual_review_approval_events_file", "app/data/db/manual_review_approval_events.jsonl"))

SAFE_REVIEW_WORDING = (
    "Human-reviewed Web3Guard AI pre-audit readiness report. This is not a certified audit, "
    "does not guarantee safety, and only covers the evidence and scope explicitly reviewed."
)

ALLOWED_ASSIGNMENT_ROLES = {"lead_reviewer", "contract_reviewer", "web_api_reviewer", "wallet_reviewer", "qa_reviewer", "report_reviewer"}
ALLOWED_FIX_STATUSES = {"fix_submitted", "verified", "rejected", "regression_needed", "accepted_risk_reviewed"}
ALLOWED_REVIEW_DECISIONS = {"approved_reviewed_pre_audit", "needs_fixes", "needs_more_evidence", "rejected"}
SEVERITY_RANK = {"critical": 5, "high": 4, "medium": 3, "low": 2, "info": 1}
BLOCKED_REVIEW_CLAIMS = [re.compile(re.escape(claim), re.I) for claim in BLOCKED_CLAIMS]


def _read(path: Path) -> list[dict[str, Any]]:
    return read_jsonl(storage_path(str(path)))


def _write(path: Path, rows: list[dict[str, Any]]) -> None:
    rewrite_jsonl(storage_path(str(path)), rows)


def _append(path: Path, row: dict[str, Any]) -> None:
    append_jsonl(storage_path(str(path)), row)


def _safe_text(value: Any, limit: int = 1600) -> str:
    text = "" if value is None else str(value)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:limit]


def _stable_hash(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def _find_by_id(rows: list[dict[str, Any]], item_id: str) -> dict[str, Any] | None:
    return next((row for row in rows if row.get("id") == item_id), None)


def _payment_verified(request: dict[str, Any] | None) -> bool:
    if not request:
        return False
    return str(request.get("payment_status") or "").lower() in {"verified", "paid_verified", "manual_verified"}


def _status_bucket(rows: list[dict[str, Any]]) -> dict[str, int]:
    return dict(Counter(str(row.get("status") or "unknown") for row in rows))


def _severity_bucket(rows: list[dict[str, Any]]) -> dict[str, int]:
    return dict(Counter(str(row.get("severity") or "info") for row in rows))


def _blocked_claims(payload: Any) -> list[str]:
    text = json.dumps(payload, ensure_ascii=False, default=str).lower()
    return sorted({claim for claim in BLOCKED_CLAIMS if claim.lower() in text})


def _request_findings(request_id: str) -> list[dict[str, Any]]:
    return [row for row in _read(FINDINGS_FILE) if row.get("request_id") == request_id]


def _request_fix_records(request_id: str | None = None, finding_id: str | None = None) -> list[dict[str, Any]]:
    rows = _read(FIX_VERIFICATIONS_FILE)
    if request_id:
        rows = [row for row in rows if row.get("request_id") == request_id]
    if finding_id:
        rows = [row for row in rows if row.get("finding_id") == finding_id]
    return rows


def status() -> dict[str, Any]:
    requests = _read(REQUESTS_FILE)
    findings = _read(FINDINGS_FILE)
    assignments = _read(ASSIGNMENTS_FILE)
    fixes = _read(FIX_VERIFICATIONS_FILE)
    approvals = _read(APPROVAL_EVENTS_FILE)
    return {
        "ok": True,
        "version": "phase-e-human-review-fix-verification-v1",
        "admin_only": True,
        "certified_audit": False,
        "allowed_public_wording": ALLOWED_PUBLIC_WORDING,
        "safe_review_wording": SAFE_REVIEW_WORDING,
        "counts": {
            "requests": len(requests),
            "findings": len(findings),
            "assignments": len(assignments),
            "fix_verifications": len(fixes),
            "approval_events": len(approvals),
        },
        "finding_status": _status_bucket(findings),
        "fix_status": _status_bucket(fixes),
        "endpoints": [
            "POST /review-ops/assignments",
            "GET /review-ops/assignments",
            "POST /review-ops/fix-verifications",
            "GET /review-ops/fix-verifications",
            "GET /review-ops/report-readiness",
            "POST /review-ops/reports/approve-reviewed",
            "POST /review-ops/public-proof/from-reviewed",
            "GET /review-ops/admin-board",
        ],
        "real_only_note": REAL_ONLY_NOTE,
    }


def create_assignment(payload: dict[str, Any]) -> dict[str, Any]:
    request_id = _safe_text(payload.get("request_id"), 180)
    reviewer = _safe_text(payload.get("reviewer"), 160)
    role = _safe_text(payload.get("role") or "lead_reviewer", 80)
    if not request_id:
        raise ValueError("request_id is required")
    if not reviewer:
        raise ValueError("reviewer is required")
    if role not in ALLOWED_ASSIGNMENT_ROLES:
        raise ValueError(f"Unsupported reviewer role: {role}")
    requests = _read(REQUESTS_FILE)
    request = _find_by_id(requests, request_id)
    if not request:
        raise ValueError("Manual review request not found")
    row = {
        "id": new_id("assign"),
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "request_id": request_id,
        "reviewer": reviewer,
        "role": role,
        "assigned_by": _safe_text(payload.get("assigned_by") or "RAADHANEX admin", 160),
        "scope_summary": _safe_text(payload.get("scope_summary") or request.get("scope_summary") or "", 1200),
        "due_date": _safe_text(payload.get("due_date") or "", 80) or None,
        "status": "assigned",
        "admin_only": True,
    }
    _append(ASSIGNMENTS_FILE, row)
    return {"ok": True, "assignment": row, "next_steps": ["Import or review findings.", "Verify fixes before report approval."]}


def list_assignments(request_id: str | None = None, reviewer: str | None = None, status_value: str | None = None, limit: int = 100) -> dict[str, Any]:
    rows = _read(ASSIGNMENTS_FILE)
    if request_id:
        rows = [row for row in rows if row.get("request_id") == request_id]
    if reviewer:
        rows = [row for row in rows if row.get("reviewer") == reviewer]
    if status_value:
        rows = [row for row in rows if row.get("status") == status_value]
    rows = sort_created(rows)[:limit]
    return {"ok": True, "items": rows, "count": len(rows)}


def record_fix_verification(payload: dict[str, Any]) -> dict[str, Any]:
    finding_id = _safe_text(payload.get("finding_id"), 180)
    status_value = _safe_text(payload.get("status") or "fix_submitted", 80)
    if not finding_id:
        raise ValueError("finding_id is required")
    if status_value not in ALLOWED_FIX_STATUSES:
        raise ValueError(f"Unsupported fix verification status: {status_value}")
    reviewer_note = _safe_text(payload.get("reviewer_note") or payload.get("verification_note") or "", 2200)
    if status_value in {"verified", "rejected", "regression_needed", "accepted_risk_reviewed"} and len(reviewer_note) < 12:
        raise ValueError("reviewer_note must explain the fix verification decision")

    findings = _read(FINDINGS_FILE)
    finding = _find_by_id(findings, finding_id)
    if not finding:
        raise ValueError("Finding not found")
    request_id = _safe_text(payload.get("request_id") or finding.get("request_id") or "", 180) or None
    evidence = payload.get("evidence") if isinstance(payload.get("evidence"), dict) else {}
    row = {
        "id": new_id("fixv"),
        "created_at": now_iso(),
        "request_id": request_id,
        "finding_id": finding_id,
        "reviewer": _safe_text(payload.get("reviewer") or "Manual reviewer", 160),
        "status": status_value,
        "fix_summary": _safe_text(payload.get("fix_summary") or "", 1600),
        "evidence": evidence,
        "evidence_hash": _stable_hash(evidence or payload.get("fix_summary") or reviewer_note),
        "test_commands": payload.get("test_commands") if isinstance(payload.get("test_commands"), list) else [],
        "reviewer_note": reviewer_note,
        "safe_review_wording": SAFE_REVIEW_WORDING,
    }
    _append(FIX_VERIFICATIONS_FILE, row)

    # Keep the manual finding board in sync without inventing security outcomes.
    for item in findings:
        if item.get("id") != finding_id:
            continue
        item["fix_verification_id"] = row["id"]
        item["fix_verification_status"] = status_value
        item["fix_verification_note"] = reviewer_note
        item["updated_at"] = now_iso()
        if status_value == "verified":
            item["status"] = "fixed"
            item["verification_status"] = "human_verified_fixed"
        elif status_value == "rejected":
            item["status"] = "confirmed"
            item["verification_status"] = "fix_rejected"
        elif status_value == "regression_needed":
            item["status"] = "needs_evidence"
            item["verification_status"] = "regression_test_needed"
        elif status_value == "accepted_risk_reviewed":
            item["status"] = "accepted_risk"
            item["verification_status"] = "human_reviewed_accepted_risk"
        break
    _write(FINDINGS_FILE, findings)
    return {"ok": True, "fix_verification": row, "updated_finding": _find_by_id(findings, finding_id)}


def list_fix_verifications(request_id: str | None = None, finding_id: str | None = None, status_value: str | None = None, limit: int = 200) -> dict[str, Any]:
    rows = _read(FIX_VERIFICATIONS_FILE)
    if request_id:
        rows = [row for row in rows if row.get("request_id") == request_id]
    if finding_id:
        rows = [row for row in rows if row.get("finding_id") == finding_id]
    if status_value:
        rows = [row for row in rows if row.get("status") == status_value]
    rows = sort_created(rows)[:limit]
    return {"ok": True, "items": rows, "count": len(rows), "summary": _status_bucket(rows)}


def report_readiness(request_id: str, report_payload: dict[str, Any] | None = None) -> dict[str, Any]:
    request_id = _safe_text(request_id, 180)
    requests = _read(REQUESTS_FILE)
    request = _find_by_id(requests, request_id)
    findings = _request_findings(request_id)
    fixes = _request_fix_records(request_id=request_id)
    reasons: list[str] = []
    warnings: list[str] = []
    if not request:
        reasons.append("Manual review request not found.")
    else:
        if not request.get("authorized_scope_confirmed"):
            reasons.append("Authorized scope confirmation is required.")
        if not _payment_verified(request):
            warnings.append("Payment/manual validation is not verified; keep report private or pending.")
    if not findings:
        reasons.append("No findings imported or reviewed for this request.")
    status_counts = _status_bucket(findings)
    if status_counts.get("needs_triage", 0):
        reasons.append("All findings must be triaged before reviewed report approval.")
    if status_counts.get("needs_evidence", 0):
        reasons.append("Findings marked needs_evidence require additional proof or out-of-scope decision.")

    unresolved_high = []
    for finding in findings:
        sev = str(finding.get("severity") or "info").lower()
        if SEVERITY_RANK.get(sev, 0) >= SEVERITY_RANK["high"] and finding.get("status") == "confirmed":
            unresolved_high.append(finding.get("id"))
    if unresolved_high:
        reasons.append("Critical/high confirmed findings must be fixed, accepted-risk-reviewed, or explicitly rejected for launch.")

    unsafe_claims = _blocked_claims(report_payload or {})
    if unsafe_claims:
        reasons.append("Blocked certified-audit/security guarantee wording detected.")
    if not any(row.get("status") == "verified" for row in fixes) and status_counts.get("fixed", 0):
        warnings.append("Fixed findings exist but no fix verification records were found.")

    eligible = not reasons
    return {
        "ok": True,
        "request_id": request_id,
        "eligible_for_reviewed_pre_audit_report": eligible,
        "reasons": reasons,
        "warnings": warnings,
        "request_status": request.get("status") if request else None,
        "payment_verified": _payment_verified(request),
        "finding_summary": {"by_status": status_counts, "by_severity": _severity_bucket(findings), "total": len(findings)},
        "fix_summary": {"by_status": _status_bucket(fixes), "total": len(fixes)},
        "required_before_approval": [
            "Authorized scope confirmed",
            "Findings imported from real evidence or manual review",
            "Every finding triaged",
            "Critical/high confirmed findings fixed or accepted-risk-reviewed",
            "No blocked certified-audit/guarantee wording",
        ],
        "safe_review_wording": SAFE_REVIEW_WORDING,
    }


def _reviewed_packet(request: dict[str, Any], findings: list[dict[str, Any]], readiness: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    public_findings = []
    for finding in findings:
        public_findings.append(
            {
                "id": finding.get("id"),
                "title": finding.get("title"),
                "severity": finding.get("severity"),
                "status": finding.get("status"),
                "affected_file": finding.get("affected_file"),
                "affected_line": finding.get("affected_line"),
                "source": finding.get("source"),
                "source_tools": finding.get("source_tools") or ([finding.get("source")] if finding.get("source") else []),
                "verification_status": finding.get("verification_status") or finding.get("fix_verification_status") or "human_triaged",
                "reviewer_note_public": _safe_text(finding.get("confirmed_evidence_note") or finding.get("reviewer_note") or "", 700),
            }
        )
    core = {
        "version": "phase-e-reviewed-pre-audit-v1",
        "request_id": request.get("id"),
        "project_name": request.get("project_name"),
        "project_url": request.get("project_url"),
        "review_type": request.get("review_type"),
        "decision": payload.get("decision"),
        "reviewer": _safe_text(payload.get("reviewer") or "Manual reviewer", 160),
        "reviewer_reason": _safe_text(payload.get("reviewer_reason") or "", 2400),
        "reviewed_at": now_iso(),
        "report_hash": _safe_text(payload.get("report_hash") or "", 160) or None,
        "scan_id": payload.get("scan_id") or request.get("scan_id"),
        "report_id": payload.get("report_id") or request.get("report_id"),
        "safe_review_wording": SAFE_REVIEW_WORDING,
        "certified_audit": False,
        "coverage_boundary": "Only submitted evidence, imported findings, tool outputs, and manual notes are covered.",
        "readiness": readiness,
        "findings": public_findings,
    }
    core["integrity_hash"] = hashlib.sha256(json.dumps(core, sort_keys=True, default=str).encode("utf-8")).hexdigest()
    return core


def approve_reviewed_report(payload: dict[str, Any]) -> dict[str, Any]:
    request_id = _safe_text(payload.get("request_id"), 180)
    decision = _safe_text(payload.get("decision") or "needs_more_evidence", 80)
    reason = _safe_text(payload.get("reviewer_reason") or "", 2400)
    if not request_id:
        raise ValueError("request_id is required")
    if decision not in ALLOWED_REVIEW_DECISIONS:
        raise ValueError(f"Unsupported review decision: {decision}")
    if len(reason) < 12:
        raise ValueError("reviewer_reason must explain the decision in at least 12 characters")

    requests = _read(REQUESTS_FILE)
    request = _find_by_id(requests, request_id)
    if not request:
        raise ValueError("Manual review request not found")
    readiness = report_readiness(request_id, payload.get("report_payload") if isinstance(payload.get("report_payload"), dict) else payload)
    approved = decision == "approved_reviewed_pre_audit" and readiness["eligible_for_reviewed_pre_audit_report"]
    packet = _reviewed_packet(request, _request_findings(request_id), readiness, payload)
    packet["approved"] = approved
    packet["decision"] = decision

    for row in requests:
        if row.get("id") == request_id:
            row["updated_at"] = now_iso()
            row["status"] = "reviewed_report_ready" if approved else "changes_requested"
            row["reviewed_report_integrity_hash"] = packet["integrity_hash"]
            row["review_decision"] = decision
            break
    _write(REQUESTS_FILE, requests)

    event = {
        "id": new_id("approve"),
        "created_at": now_iso(),
        "request_id": request_id,
        "decision": decision,
        "approved": approved,
        "reviewer": packet["reviewer"],
        "reviewer_reason": reason,
        "integrity_hash": packet["integrity_hash"],
        "blocked_public_claims": _blocked_claims(payload),
        "safe_review_wording": SAFE_REVIEW_WORDING,
    }
    _append(APPROVAL_EVENTS_FILE, event)
    return {
        "ok": True,
        "approved": approved,
        "packet": packet,
        "event": event,
        "next_steps": [
            "Publish proof only if public proof gate also passes.",
            "Do not call this a certified audit.",
        ],
    }


def public_proof_from_reviewed(payload: dict[str, Any]) -> dict[str, Any]:
    reviewed = approve_reviewed_report(payload)
    if not reviewed.get("approved"):
        return {"ok": True, "published": False, "reviewed": reviewed, "reason": "Reviewed report approval gate did not pass."}
    packet = reviewed["packet"]
    proof_payload = {
        "project_name": packet.get("project_name"),
        "report_id": packet.get("report_id"),
        "scan_id": packet.get("scan_id"),
        "report_hash": packet.get("report_hash") or packet.get("integrity_hash"),
        "authorized_scope_confirmed": True,
        "real_only_acknowledged": True,
        "manual_review_completed": True,
        "payment_verified": True,
        "custom_summary": SAFE_REVIEW_WORDING,
        "scan_payload": {
            "project_name": packet.get("project_name"),
            "report_hash": packet.get("report_hash") or packet.get("integrity_hash"),
            "coverage": {"assessed_count": 1, "total_modules": 1, "coverage_percent": 100, "confidence": "manual_reviewed_scope"},
            "report_ready_findings": packet.get("findings", []),
        },
    }
    draft = build_public_proof_draft(proof_payload)["draft"]
    approved = approve_public_proof({**proof_payload, "draft": draft, "decision": "approved_public_pre_audit", "reviewer_reason": packet.get("reviewer_reason")})
    if not approved.get("approved"):
        return {"ok": True, "published": False, "reviewed": reviewed, "proof_approval": approved}
    if bool(payload.get("publish", False)):
        published = publish_public_proof({"packet": approved["packet"], "visibility": payload.get("visibility") or "public"})
        return {"ok": True, "published": True, "reviewed": reviewed, "proof_approval": approved, "public_proof": published}
    return {"ok": True, "published": False, "reviewed": reviewed, "proof_approval": approved, "note": "Proof packet approved but not published because publish=false."}


def admin_board(user_id: str | None = None, project_id: str | None = None) -> dict[str, Any]:
    requests = _read(REQUESTS_FILE)
    findings = _read(FINDINGS_FILE)
    assignments = _read(ASSIGNMENTS_FILE)
    fixes = _read(FIX_VERIFICATIONS_FILE)
    approvals = _read(APPROVAL_EVENTS_FILE)
    if user_id:
        requests = [row for row in requests if row.get("user_id") == user_id]
        findings = [row for row in findings if row.get("user_id") == user_id]
    if project_id:
        requests = [row for row in requests if row.get("project_id") == project_id]
        findings = [row for row in findings if row.get("project_id") == project_id]
    request_ids = {row.get("id") for row in requests}
    assignments = [row for row in assignments if row.get("request_id") in request_ids]
    fixes = [row for row in fixes if row.get("request_id") in request_ids]
    approvals = [row for row in approvals if row.get("request_id") in request_ids]
    ready = []
    blocked = []
    for request in requests:
        r = report_readiness(str(request.get("id")))
        item = {"request_id": request.get("id"), "project_name": request.get("project_name"), "readiness": r}
        if r.get("eligible_for_reviewed_pre_audit_report"):
            ready.append(item)
        else:
            blocked.append(item)
    return {
        "ok": True,
        "admin_only": True,
        "safe_review_wording": SAFE_REVIEW_WORDING,
        "summary": {
            "requests": _status_bucket(requests),
            "findings": _status_bucket(findings),
            "fixes": _status_bucket(fixes),
            "assignments": _status_bucket(assignments),
            "approvals": {"approved": sum(1 for row in approvals if row.get("approved")), "total": len(approvals)},
        },
        "ready_for_approval": ready[:30],
        "blocked_or_in_progress": blocked[:30],
        "recent_assignments": sort_created(assignments)[:20],
        "recent_fix_verifications": sort_created(fixes)[:20],
        "recent_approval_events": sort_created(approvals)[:20],
    }
