from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from app.services.mega_phase_e_store import append_jsonl, new_id, now_iso, read_jsonl, rewrite_jsonl, sort_created, storage_path

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "db"
REQUESTS_FILE = DATA_DIR / "manual_review_requests.jsonl"
FINDINGS_FILE = DATA_DIR / "manual_review_findings.jsonl"
NOTES_FILE = DATA_DIR / "manual_review_notes.jsonl"
DECISIONS_FILE = DATA_DIR / "manual_review_report_decisions.jsonl"

ALLOWED_FINDING_STATUS = {
    "needs_triage",
    "confirmed",
    "false_positive",
    "needs_evidence",
    "accepted_risk",
    "fixed",
    "duplicate",
    "out_of_scope",
}
ALLOWED_REQUEST_STATUS = {
    "payment_pending",
    "scope_pending",
    "ready_for_triage",
    "in_review",
    "changes_requested",
    "reviewed_report_ready",
    "closed",
}
ALLOWED_DECISIONS = {
    "not_ready",
    "needs_more_evidence",
    "triage_in_progress",
    "reviewed_report_ready",
    "closed_no_export",
}
SEVERITY_ORDER = ["critical", "high", "medium", "low", "info"]
SAFE_REVIEW_NOTE = (
    "Manual Expert Review is a triage and evidence-review workflow. It helps confirm scanner findings, "
    "remove false positives, collect missing evidence, and prepare a reviewed pre-audit readiness report. "
    "It is not a certified audit, does not guarantee all vulnerabilities are found, and does not replace a professional security review."
)
BLOCKED_CLAIM_PATTERNS = [
    re.compile(pattern, re.I)
    for pattern in [
        r"\b100\s*%\s*secure\b",
        r"\bfully\s+secure\b",
        r"\bcertified\s+audit\b",
        r"\baudited\s+by\s+(web3guard|raadhaanex|raadhanex)\b",
        r"\ball\s+vulnerabilities\s+found\b",
        r"\bguaranteed\s+safe\b",
        r"\bopenzeppelin\s+certified\b",
        r"\bcertik\s+level\b",
        r"\bhacken\s+level\b",
    ]
]


def _path(path: Path) -> Path:
    return storage_path(str(path))


def _read(path: Path) -> list[dict[str, Any]]:
    return read_jsonl(_path(path))


def _write(path: Path, rows: list[dict[str, Any]]) -> None:
    rewrite_jsonl(_path(path), rows)


def _append(path: Path, row: dict[str, Any]) -> None:
    append_jsonl(_path(path), row)


def _stable_hash(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def _normalize_severity(value: Any) -> str:
    text = str(value or "info").strip().lower()
    if text in {"critical", "high", "medium", "low", "info"}:
        return text
    if text in {"warning", "warn", "moderate"}:
        return "medium"
    if text in {"error", "danger"}:
        return "high"
    return "info"


def _normalize_confidence(value: Any) -> str:
    text = str(value or "medium").strip().lower()
    if text in {"high", "medium", "low"}:
        return text
    return "medium"


def _safe_text(value: Any, limit: int = 800) -> str:
    text = "" if value is None else str(value)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:limit]


def _looks_like_fake_claim(text: str) -> list[str]:
    return [pattern.pattern for pattern in BLOCKED_CLAIM_PATTERNS if pattern.search(text or "")]


def status() -> dict[str, Any]:
    requests = _read(REQUESTS_FILE)
    findings = _read(FINDINGS_FILE)
    decisions = _read(DECISIONS_FILE)
    return {
        "ok": True,
        "phase": "51",
        "name": "Manual Expert Review + Finding Triage Workflow",
        "workflow_level": "Audit-company style workflow and audit-company level scanner foundation",
        "certified_audit": False,
        "security_guarantee": False,
        "safe_review_note": SAFE_REVIEW_NOTE,
        "states": {
            "finding_statuses": sorted(ALLOWED_FINDING_STATUS),
            "request_statuses": sorted(ALLOWED_REQUEST_STATUS),
            "report_decisions": sorted(ALLOWED_DECISIONS),
        },
        "counts": {
            "requests": len(requests),
            "findings": len(findings),
            "decisions": len(decisions),
            "confirmed_findings": sum(1 for item in findings if item.get("status") == "confirmed"),
            "false_positives": sum(1 for item in findings if item.get("status") == "false_positive"),
            "needs_evidence": sum(1 for item in findings if item.get("status") == "needs_evidence"),
        },
    }


def methodology() -> dict[str, Any]:
    return {
        "ok": True,
        "title": "Manual expert review methodology",
        "safe_review_note": SAFE_REVIEW_NOTE,
        "workflow": [
            "Create authorized manual review request with scope and evidence sources.",
            "Import scanner findings from real scan payload, static artifacts, or manual evidence.",
            "Triage every finding as confirmed, false positive, needs evidence, accepted risk, fixed, duplicate, or out of scope.",
            "Require reviewer reason for severity override and report decision.",
            "Prepare reviewed pre-audit readiness report only after payment/manual validation and triage checks.",
        ],
        "what_this_adds": [
            "Audit-company style workflow",
            "Audit-company level scanner foundation",
            "False-positive control",
            "Human-review notes and report-readiness decision",
            "Clear boundary between confirmed, warning, and not-assessed states",
        ],
        "what_it_does_not_claim": [
            "Certified audit",
            "All vulnerabilities found",
            "100% secure",
            "OpenZeppelin/CertiK/Hacken-level official audit",
            "Exploit automation or unauthorized testing",
        ],
    }


def create_request(payload: dict[str, Any]) -> dict[str, Any]:
    scope_confirmed = bool(payload.get("authorized_scope_confirmed"))
    payment_verified = str(payload.get("payment_status") or "not_verified").lower() in {"verified", "paid_verified", "manual_verified"}
    project_name = _safe_text(payload.get("project_name") or "Manual review project", 180)
    if not scope_confirmed:
        status_value = "scope_pending"
    elif not payment_verified:
        status_value = "payment_pending"
    else:
        status_value = "ready_for_triage"
    row = {
        "id": new_id("mrev"),
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "user_id": _safe_text(payload.get("user_id") or "local-demo-user", 160),
        "project_id": _safe_text(payload.get("project_id") or "", 160) or None,
        "scan_id": _safe_text(payload.get("scan_id") or "", 160) or None,
        "report_id": _safe_text(payload.get("report_id") or "", 160) or None,
        "project_name": project_name,
        "project_url": _safe_text(payload.get("project_url") or "", 500) or None,
        "review_type": _safe_text(payload.get("review_type") or "pre_audit_readiness", 80),
        "priority": _normalize_severity(payload.get("priority") or "medium"),
        "scope_summary": _safe_text(payload.get("scope_summary") or "", 1600),
        "evidence_sources": payload.get("evidence_sources") if isinstance(payload.get("evidence_sources"), list) else [],
        "authorized_scope_confirmed": scope_confirmed,
        "payment_status": "verified" if payment_verified else _safe_text(payload.get("payment_status") or "not_verified", 80),
        "status": status_value,
        "safe_review_note": SAFE_REVIEW_NOTE,
    }
    _append(REQUESTS_FILE, row)
    return {"ok": True, "request": row, "next_steps": _next_steps_for_request(row)}


def list_requests(user_id: str | None = None, project_id: str | None = None, status_value: str | None = None, limit: int = 100) -> dict[str, Any]:
    rows = _read(REQUESTS_FILE)
    if user_id:
        rows = [row for row in rows if row.get("user_id") == user_id]
    if project_id:
        rows = [row for row in rows if row.get("project_id") == project_id]
    if status_value:
        rows = [row for row in rows if row.get("status") == status_value]
    return {"ok": True, "items": sort_created(rows)[:limit], "count": len(rows), "safe_review_note": SAFE_REVIEW_NOTE}


def _next_steps_for_request(row: dict[str, Any]) -> list[str]:
    if row.get("status") == "scope_pending":
        return ["Confirm authorized scope before any review or testing.", "Attach target URLs, repo/contract evidence, and allowed surfaces."]
    if row.get("status") == "payment_pending":
        return ["Verify ₹999 pilot/manual review payment before reviewed export unlock.", "Import scanner findings for triage while payment remains pending."]
    if row.get("status") == "ready_for_triage":
        return ["Import scan findings.", "Assign reviewer and triage every finding."]
    return ["Continue triage and evidence review."]


def _add_finding(candidates: list[dict[str, Any]], source: str, item: dict[str, Any], default_category: str = "scanner") -> None:
    title = _safe_text(item.get("title") or item.get("name") or item.get("check") or item.get("rule_id") or item.get("message") or "Scanner finding", 220)
    evidence = item.get("evidence") or item.get("raw_evidence") or item.get("proof") or item.get("metadata") or item
    candidates.append(
        {
            "title": title,
            "severity": _normalize_severity(item.get("severity") or item.get("impact") or item.get("level")),
            "confidence": _normalize_confidence(item.get("confidence") or item.get("proof_confidence")),
            "category": _safe_text(item.get("category") or item.get("type") or default_category, 120),
            "source": source,
            "status": "needs_triage",
            "summary": _safe_text(item.get("summary") or item.get("description") or item.get("message") or title, 1200),
            "fix_hint": _safe_text(item.get("fix_hint") or item.get("recommendation") or item.get("remediation") or "Reviewer should verify evidence and provide a project-specific fix plan.", 1200),
            "evidence": evidence,
            "evidence_hash": _stable_hash(evidence),
        }
    )


def _collect_from_any(value: Any, candidates: list[dict[str, Any]], source: str) -> None:
    if isinstance(value, list):
        for item in value:
            if isinstance(item, dict):
                _add_finding(candidates, source, item)
        return
    if isinstance(value, dict):
        # Common Phase 45-50 containers.
        for key in [
            "confirmed_exposures",
            "proof_based_exposures",
            "real_findings",
            "visible_findings",
            "findings",
            "detectors",
            "results",
            "issues",
            "vulnerabilities",
        ]:
            child = value.get(key)
            if isinstance(child, list):
                _collect_from_any(child, candidates, f"{source}.{key}")
        # Module cards often store nested actions/findings.
        if value.get("title") or value.get("severity") or value.get("message") or value.get("rule_id"):
            _add_finding(candidates, source, value)


def import_findings(payload: dict[str, Any]) -> dict[str, Any]:
    request_id = _safe_text(payload.get("request_id") or "", 180) or None
    user_id = _safe_text(payload.get("user_id") or "local-demo-user", 160)
    project_id = _safe_text(payload.get("project_id") or "", 160) or None
    scan_payload = payload.get("scan_payload") if isinstance(payload.get("scan_payload"), dict) else {}
    manual_findings = payload.get("manual_findings") if isinstance(payload.get("manual_findings"), list) else []
    candidates: list[dict[str, Any]] = []

    if scan_payload:
        for key in [
            "bug_detection_coverage",
            "proof_based_bug_detection",
            "real_evidence_summary",
            "findings_pipeline",
            "static_artifact_findings",
            "tool_findings",
            "module_cards",
            "combined_report",
            "scanner_correlation",
            "slither",
            "semgrep",
            "aderyn",
        ]:
            if key in scan_payload:
                _collect_from_any(scan_payload.get(key), candidates, key)
    for item in manual_findings:
        if isinstance(item, dict):
            _add_finding(candidates, "manual_evidence", item, default_category="manual")

    if not candidates:
        return {
            "ok": True,
            "imported": 0,
            "items": [],
            "note": "No real findings were imported. Provide scan_payload/manual_findings with evidence; missing modules stay Not Assessed.",
            "safe_review_note": SAFE_REVIEW_NOTE,
        }

    existing = _read(FINDINGS_FILE)
    existing_keys = {row.get("dedupe_key") for row in existing}
    imported: list[dict[str, Any]] = []
    for item in candidates:
        dedupe_key = _stable_hash({"request_id": request_id, "project_id": project_id, "title": item.get("title"), "evidence_hash": item.get("evidence_hash")})
        if dedupe_key in existing_keys:
            continue
        row = {
            "id": new_id("mfind"),
            "dedupe_key": dedupe_key,
            "created_at": now_iso(),
            "updated_at": now_iso(),
            "request_id": request_id,
            "user_id": user_id,
            "project_id": project_id,
            "reviewer": None,
            "reviewer_note": "",
            "severity_override_reason": "",
            "confirmed_evidence_note": "",
            **item,
        }
        imported.append(row)
        existing.append(row)
        existing_keys.add(dedupe_key)
    _write(FINDINGS_FILE, existing)
    return {
        "ok": True,
        "imported": len(imported),
        "items": imported,
        "safe_review_note": SAFE_REVIEW_NOTE,
        "next_steps": ["Triage imported findings.", "Mark false positives and confirmed issues before reviewed report unlock."],
    }


def list_findings(
    request_id: str | None = None,
    user_id: str | None = None,
    project_id: str | None = None,
    status_value: str | None = None,
    limit: int = 200,
) -> dict[str, Any]:
    rows = _read(FINDINGS_FILE)
    if request_id:
        rows = [row for row in rows if row.get("request_id") == request_id]
    if user_id:
        rows = [row for row in rows if row.get("user_id") == user_id]
    if project_id:
        rows = [row for row in rows if row.get("project_id") == project_id]
    if status_value:
        rows = [row for row in rows if row.get("status") == status_value]
    return {"ok": True, "items": sort_created(rows)[:limit], "count": len(rows), "summary": _finding_summary(rows), "safe_review_note": SAFE_REVIEW_NOTE}


def _finding_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "by_status": dict(Counter(str(row.get("status") or "unknown") for row in rows)),
        "by_severity": dict(Counter(str(row.get("severity") or "info") for row in rows)),
        "confirmed": sum(1 for row in rows if row.get("status") == "confirmed"),
        "needs_triage": sum(1 for row in rows if row.get("status") == "needs_triage"),
        "false_positive": sum(1 for row in rows if row.get("status") == "false_positive"),
        "needs_evidence": sum(1 for row in rows if row.get("status") == "needs_evidence"),
    }


def triage_finding(payload: dict[str, Any]) -> dict[str, Any]:
    finding_id = _safe_text(payload.get("finding_id") or "", 180)
    if not finding_id:
        raise ValueError("finding_id is required")
    new_status = _safe_text(payload.get("status") or "needs_triage", 80)
    if new_status not in ALLOWED_FINDING_STATUS:
        raise ValueError(f"Unsupported finding status: {new_status}")
    reviewer_note = _safe_text(payload.get("reviewer_note") or "", 2000)
    if new_status in {"confirmed", "false_positive", "accepted_risk", "out_of_scope"} and len(reviewer_note) < 10:
        raise ValueError("reviewer_note with clear reason is required for this status")
    override_severity = payload.get("severity")
    override_reason = _safe_text(payload.get("severity_override_reason") or "", 1000)
    if override_severity and not override_reason:
        raise ValueError("severity_override_reason is required when changing severity")
    rows = _read(FINDINGS_FILE)
    updated = None
    for row in rows:
        if row.get("id") == finding_id:
            row["status"] = new_status
            if override_severity:
                row["severity"] = _normalize_severity(override_severity)
                row["severity_override_reason"] = override_reason
            row["reviewer"] = _safe_text(payload.get("reviewer") or "Manual reviewer", 160)
            row["reviewer_note"] = reviewer_note
            row["confirmed_evidence_note"] = _safe_text(payload.get("confirmed_evidence_note") or "", 2000)
            row["updated_at"] = now_iso()
            updated = row
            break
    if not updated:
        raise ValueError("Finding not found")
    _write(FINDINGS_FILE, rows)
    return {"ok": True, "finding": updated, "safe_review_note": SAFE_REVIEW_NOTE}


def add_review_note(payload: dict[str, Any]) -> dict[str, Any]:
    note = _safe_text(payload.get("note") or "", 3000)
    if len(note) < 8:
        raise ValueError("note is required")
    blocked = _looks_like_fake_claim(note)
    if blocked:
        raise ValueError("Unsafe audit/security claim detected. Use pre-audit readiness wording only.")
    row = {
        "id": new_id("mnote"),
        "created_at": now_iso(),
        "request_id": _safe_text(payload.get("request_id") or "", 180) or None,
        "finding_id": _safe_text(payload.get("finding_id") or "", 180) or None,
        "user_id": _safe_text(payload.get("user_id") or "local-demo-user", 160),
        "reviewer": _safe_text(payload.get("reviewer") or "Manual reviewer", 160),
        "visibility": _safe_text(payload.get("visibility") or "internal", 80),
        "note": note,
        "safe_review_note": SAFE_REVIEW_NOTE,
    }
    _append(NOTES_FILE, row)
    return {"ok": True, "note": row}


def list_notes(request_id: str | None = None, finding_id: str | None = None, limit: int = 200) -> dict[str, Any]:
    rows = _read(NOTES_FILE)
    if request_id:
        rows = [row for row in rows if row.get("request_id") == request_id]
    if finding_id:
        rows = [row for row in rows if row.get("finding_id") == finding_id]
    return {"ok": True, "items": sort_created(rows)[:limit], "count": len(rows)}


def decide_report(payload: dict[str, Any]) -> dict[str, Any]:
    request_id = _safe_text(payload.get("request_id") or "", 180)
    if not request_id:
        raise ValueError("request_id is required")
    decision = _safe_text(payload.get("decision") or "not_ready", 80)
    if decision not in ALLOWED_DECISIONS:
        raise ValueError(f"Unsupported report decision: {decision}")
    reviewer_reason = _safe_text(payload.get("reviewer_reason") or "", 2000)
    if len(reviewer_reason) < 12:
        raise ValueError("reviewer_reason is required")
    if _looks_like_fake_claim(reviewer_reason):
        raise ValueError("Unsafe audit/security claim detected in reviewer_reason")
    payment_verified = bool(payload.get("payment_verified"))
    findings = [row for row in _read(FINDINGS_FILE) if row.get("request_id") == request_id]
    triaged = [row for row in findings if row.get("status") not in {"needs_triage"}]
    open_needs = [row for row in findings if row.get("status") in {"needs_triage", "needs_evidence"}]
    ready_allowed = decision == "reviewed_report_ready" and payment_verified and findings and len(open_needs) == 0
    final_decision = decision
    blockers: list[str] = []
    if decision == "reviewed_report_ready":
        if not payment_verified:
            blockers.append("Payment/manual validation is not verified.")
        if not findings:
            blockers.append("No findings are attached to this review request.")
        if open_needs:
            blockers.append("Some findings still need triage or evidence.")
        if blockers:
            final_decision = "triage_in_progress"
    row = {
        "id": new_id("mdec"),
        "created_at": now_iso(),
        "request_id": request_id,
        "decision": final_decision,
        "requested_decision": decision,
        "reviewer": _safe_text(payload.get("reviewer") or "Manual reviewer", 160),
        "reviewer_reason": reviewer_reason,
        "payment_verified": payment_verified,
        "ready_for_reviewed_export": ready_allowed,
        "blockers": blockers,
        "finding_summary": _finding_summary(findings),
        "safe_review_note": SAFE_REVIEW_NOTE,
    }
    _append(DECISIONS_FILE, row)
    if final_decision in {"reviewed_report_ready", "triage_in_progress", "needs_more_evidence", "closed_no_export"}:
        _update_request_status(request_id, final_decision)
    return {"ok": True, "decision": row}


def _update_request_status(request_id: str, decision: str) -> None:
    mapping = {
        "reviewed_report_ready": "reviewed_report_ready",
        "triage_in_progress": "in_review",
        "needs_more_evidence": "changes_requested",
        "closed_no_export": "closed",
    }
    rows = _read(REQUESTS_FILE)
    changed = False
    for row in rows:
        if row.get("id") == request_id:
            row["status"] = mapping.get(decision, row.get("status"))
            row["updated_at"] = now_iso()
            changed = True
            break
    if changed:
        _write(REQUESTS_FILE, rows)


def board(user_id: str | None = None, project_id: str | None = None) -> dict[str, Any]:
    requests = _read(REQUESTS_FILE)
    findings = _read(FINDINGS_FILE)
    decisions = _read(DECISIONS_FILE)
    if user_id:
        requests = [row for row in requests if row.get("user_id") == user_id]
        findings = [row for row in findings if row.get("user_id") == user_id]
    if project_id:
        requests = [row for row in requests if row.get("project_id") == project_id]
        findings = [row for row in findings if row.get("project_id") == project_id]
    return {
        "ok": True,
        "safe_review_note": SAFE_REVIEW_NOTE,
        "workflow_level": "Audit-company style workflow and audit-company level scanner foundation",
        "request_summary": dict(Counter(str(row.get("status") or "unknown") for row in requests)),
        "finding_summary": _finding_summary(findings),
        "latest_requests": sort_created(requests)[:10],
        "latest_findings": sort_created(findings)[:20],
        "latest_decisions": sort_created(decisions)[:10],
        "quality_gates": {
            "scope_required": True,
            "payment_verification_required_for_reviewed_export": True,
            "triage_required_before_reviewed_export": True,
            "unsafe_audit_claims_blocked": True,
            "certified_audit_claim": False,
        },
        "next_steps": [
            "Create or select a review request.",
            "Import latest real scan output/findings.",
            "Triage findings with reviewer notes.",
            "Only unlock reviewed report/export after payment/manual validation and no open triage blockers.",
        ],
    }


def client_summary_template(payload: dict[str, Any]) -> dict[str, Any]:
    project_name = _safe_text(payload.get("project_name") or "your Web3 project", 180)
    request_id = _safe_text(payload.get("request_id") or "", 180)
    findings = [row for row in _read(FINDINGS_FILE) if not request_id or row.get("request_id") == request_id]
    summary = _finding_summary(findings)
    return {
        "ok": True,
        "project_name": project_name,
        "safe_title": f"{project_name} — reviewed pre-audit readiness summary",
        "safe_review_note": SAFE_REVIEW_NOTE,
        "client_copy": [
            f"Web3Guard reviewed the supplied scanner evidence for {project_name} under the authorized pre-audit readiness scope.",
            "This is not a certified audit and does not provide a security guarantee.",
            f"Confirmed findings: {summary['confirmed']}. Needs evidence: {summary['needs_evidence']}. False positives removed: {summary['false_positive']}.",
            "Use this report to fix launch blockers before a professional audit or production launch.",
        ],
        "blocked_phrases": ["100% secure", "certified audit", "all vulnerabilities found", "audited by Web3Guard"],
    }
