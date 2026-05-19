from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

COMMUNITY_REVIEW_NOTE = (
    "Web3Guard Community Review is a request, triage, and feedback workflow for defensive manual review. "
    "It is not a bounty marketplace, does not create a verified auditor badge, and does not replace a certified audit."
)

SAFE_BOUNDARY = (
    "Only submit projects you own or are authorized to review. Reviewers must not request private keys, seed phrases, mnemonics, "
    "wallet signatures, production credentials, or exploit live systems. Public feedback is moderation-first."
)

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data" / "db"
REQUESTS_FILE = DATA_DIR / "community_review_requests.jsonl"
FEEDBACK_FILE = DATA_DIR / "community_review_feedback.jsonl"
TRIAGE_FILE = DATA_DIR / "community_review_triage.jsonl"

REQUEST_STATUSES = {"draft", "submitted", "triage", "accepted", "in_review", "needs_information", "completed", "closed"}
FEEDBACK_STATUSES = {"queued", "needs_moderation", "accepted", "rejected", "converted_to_task", "closed"}
TRIAGE_STATUSES = {"new", "validating_scope", "needs_more_evidence", "ready_for_review", "assigned", "closed"}
SEVERITIES = {"critical", "high", "medium", "low", "info"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_json(value: Any) -> str:
    try:
        return json.dumps(value, sort_keys=True, default=str, ensure_ascii=False)
    except Exception:
        return str(value)


def _id(prefix: str, payload: Any) -> str:
    digest = hashlib.sha256(f"{_now()}::{_safe_json(payload)}".encode("utf-8")).hexdigest()[:16]
    return f"{prefix}_{digest}"


def _ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            value = json.loads(line)
            if isinstance(value, dict):
                rows.append(value)
        except json.JSONDecodeError:
            continue
    return rows


def _append_jsonl(path: Path, record: dict[str, Any]) -> None:
    _ensure_parent(path)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True, default=str) + "\n")


def _normalize_status(status: str | None, allowed: set[str], default: str) -> str:
    clean = (status or default).strip().lower().replace(" ", "_")
    return clean if clean in allowed else default


def _normalize_severity(value: str | None) -> str:
    clean = (value or "info").strip().lower()
    return clean if clean in SEVERITIES else "info"


def _for_user(rows: list[dict[str, Any]], user_id: str | None = None, project_id: str | None = None) -> list[dict[str, Any]]:
    result = rows
    if user_id:
        result = [row for row in result if str(row.get("user_id") or "") == user_id]
    if project_id:
        result = [row for row in result if str(row.get("project_id") or "") == project_id]
    return result


def community_review_status() -> dict[str, Any]:
    requests = _read_jsonl(REQUESTS_FILE)
    feedback = _read_jsonl(FEEDBACK_FILE)
    triage = _read_jsonl(TRIAGE_FILE)
    return {
        "ok": True,
        "service": "Community Review Layer",
        "mode": "manual_review_request_workflow",
        "counts": {
            "review_requests": len(requests),
            "feedback_items": len(feedback),
            "triage_items": len(triage),
            "open_review_requests": len([r for r in requests if r.get("status") not in {"completed", "closed"}]),
            "queued_feedback": len([f for f in feedback if f.get("status") in {"queued", "needs_moderation"}]),
        },
        "capabilities": [
            "review_request_board",
            "safe_public_feedback_queue",
            "manual_triage_states",
            "responsible_review_templates",
            "admin_overview",
            "user_project_review_view",
        ],
        "blocked_claims": [
            "verified_auditor_badge",
            "bounty_marketplace_claim",
            "certified_audit_claim",
            "100_percent_secure_claim",
            "exploit_automation",
            "wallet_signing",
            "private_key_or_seed_phrase_collection",
        ],
        "real_only_note": COMMUNITY_REVIEW_NOTE,
        "safe_boundary": SAFE_BOUNDARY,
    }


def create_review_request(payload: dict[str, Any]) -> dict[str, Any]:
    if not payload.get("authorized_scope_confirmed"):
        raise ValueError("authorized_scope_confirmed must be true before submitting a community review request")
    title = str(payload.get("title") or "").strip()
    if len(title) < 4:
        raise ValueError("title is required")
    project_id = payload.get("project_id")
    user_id = str(payload.get("user_id") or "local-demo-user")
    focus_areas = payload.get("focus_areas") if isinstance(payload.get("focus_areas"), list) else []
    safe_focus = [str(item).strip() for item in focus_areas if str(item).strip()][:12]
    record = {
        "id": _id("crr", payload),
        "user_id": user_id,
        "project_id": str(project_id) if project_id else None,
        "title": title,
        "project_url": payload.get("project_url") or None,
        "repo_url": payload.get("repo_url") or None,
        "scope_summary": str(payload.get("scope_summary") or "").strip()[:1200],
        "focus_areas": safe_focus,
        "review_type": str(payload.get("review_type") or "pre_audit_readiness").strip()[:80],
        "status": "submitted",
        "priority": _normalize_severity(str(payload.get("priority") or "medium")),
        "authorized_scope_confirmed": True,
        "public_feedback_enabled": bool(payload.get("public_feedback_enabled", False)),
        "created_at": _now(),
        "updated_at": _now(),
        "safe_boundary": SAFE_BOUNDARY,
        "note": COMMUNITY_REVIEW_NOTE,
    }
    _append_jsonl(REQUESTS_FILE, record)
    triage = {
        "id": _id("crt", record),
        "request_id": record["id"],
        "user_id": user_id,
        "project_id": record["project_id"],
        "status": "new",
        "severity": record["priority"],
        "summary": f"Review request submitted: {title}",
        "next_step": "Validate scope, confirm evidence, and assign manual reviewer if available.",
        "created_at": _now(),
        "updated_at": _now(),
    }
    _append_jsonl(TRIAGE_FILE, triage)
    return {"ok": True, "request": record, "triage_item": triage}


def list_review_requests(user_id: str | None = None, project_id: str | None = None, status: str | None = None, limit: int = 100) -> dict[str, Any]:
    rows = _for_user(_read_jsonl(REQUESTS_FILE), user_id=user_id, project_id=project_id)
    if status:
        wanted = _normalize_status(status, REQUEST_STATUSES, status)
        rows = [row for row in rows if row.get("status") == wanted]
    rows = sorted(rows, key=lambda row: str(row.get("created_at") or ""), reverse=True)[:limit]
    return {"ok": True, "requests": rows, "count": len(rows), "real_only_note": COMMUNITY_REVIEW_NOTE}


def submit_feedback(payload: dict[str, Any]) -> dict[str, Any]:
    if not payload.get("safe_feedback_acknowledged"):
        raise ValueError("safe_feedback_acknowledged must be true before submitting feedback")
    summary = str(payload.get("summary") or "").strip()
    if len(summary) < 8:
        raise ValueError("summary is required")
    record = {
        "id": _id("crf", payload),
        "request_id": payload.get("request_id") or None,
        "user_id": str(payload.get("user_id") or "local-demo-user"),
        "project_id": payload.get("project_id") or None,
        "reviewer_display_name": str(payload.get("reviewer_display_name") or "Community reviewer")[:120],
        "summary": summary[:1000],
        "evidence_note": str(payload.get("evidence_note") or "")[:1200],
        "severity": _normalize_severity(str(payload.get("severity") or "info")),
        "status": "needs_moderation",
        "visibility": "private_until_moderated",
        "created_at": _now(),
        "updated_at": _now(),
        "safe_feedback_acknowledged": True,
        "note": "Feedback is moderation-first and does not represent an audit finding until validated.",
    }
    _append_jsonl(FEEDBACK_FILE, record)
    return {"ok": True, "feedback": record}


def list_feedback(user_id: str | None = None, project_id: str | None = None, request_id: str | None = None, status: str | None = None, limit: int = 100) -> dict[str, Any]:
    rows = _for_user(_read_jsonl(FEEDBACK_FILE), user_id=user_id, project_id=project_id)
    if request_id:
        rows = [row for row in rows if row.get("request_id") == request_id]
    if status:
        wanted = _normalize_status(status, FEEDBACK_STATUSES, status)
        rows = [row for row in rows if row.get("status") == wanted]
    rows = sorted(rows, key=lambda row: str(row.get("created_at") or ""), reverse=True)[:limit]
    return {"ok": True, "feedback": rows, "count": len(rows), "real_only_note": COMMUNITY_REVIEW_NOTE}


def update_triage(payload: dict[str, Any]) -> dict[str, Any]:
    # Append-only triage event to avoid rewriting history in local JSONL mode.
    status = _normalize_status(str(payload.get("status") or "validating_scope"), TRIAGE_STATUSES, "validating_scope")
    record = {
        "id": _id("crt", payload),
        "request_id": payload.get("request_id") or None,
        "feedback_id": payload.get("feedback_id") or None,
        "user_id": str(payload.get("user_id") or "local-demo-user"),
        "project_id": payload.get("project_id") or None,
        "status": status,
        "severity": _normalize_severity(str(payload.get("severity") or "info")),
        "summary": str(payload.get("summary") or "Triage event")[:1000],
        "next_step": str(payload.get("next_step") or "Continue manual validation.")[:1000],
        "assigned_to": payload.get("assigned_to") or None,
        "created_at": _now(),
        "updated_at": _now(),
        "note": "Append-only triage event; not a verified auditor badge or certified audit status.",
    }
    _append_jsonl(TRIAGE_FILE, record)
    return {"ok": True, "triage_item": record}


def list_triage(user_id: str | None = None, project_id: str | None = None, request_id: str | None = None, limit: int = 100) -> dict[str, Any]:
    rows = _for_user(_read_jsonl(TRIAGE_FILE), user_id=user_id, project_id=project_id)
    if request_id:
        rows = [row for row in rows if row.get("request_id") == request_id]
    rows = sorted(rows, key=lambda row: str(row.get("created_at") or ""), reverse=True)[:limit]
    return {"ok": True, "triage": rows, "count": len(rows), "real_only_note": COMMUNITY_REVIEW_NOTE}


def responsible_review_template(payload: dict[str, Any]) -> dict[str, Any]:
    project_name = str(payload.get("project_name") or "your Web3 project").strip()[:160]
    scope = str(payload.get("scope_summary") or "the supplied launch-readiness scope").strip()[:600]
    contact = str(payload.get("contact") or "project team").strip()[:160]
    message = (
        f"Hello {contact},\n\n"
        f"Web3Guard AI received a community review request for {project_name}. This is a defensive pre-audit readiness review workflow, "
        "not a certified audit and not a bounty marketplace.\n\n"
        f"Scope summary:\n{scope}\n\n"
        "Review boundaries:\n"
        "- No wallet signing, private keys, seed phrases, or production secrets should be shared.\n"
        "- No exploitation of live systems is authorized through this workflow.\n"
        "- Any feedback should include evidence, severity, suggested fix, and verification steps.\n"
        "- Public feedback remains moderation-first until validated.\n\n"
        "Recommended next step: confirm scope, provide non-sensitive evidence, and assign a manual reviewer if available.\n\n"
        "Regards,\nWeb3Guard AI by RAADHANEX"
    )
    return {
        "ok": True,
        "template": {
            "subject": f"Community review scope confirmation — {project_name}",
            "message": message,
            "safe_boundary": SAFE_BOUNDARY,
            "blocked_claims": ["audited", "certified secure", "verified auditor badge", "bounty marketplace guarantee"],
        },
    }


def admin_overview() -> dict[str, Any]:
    requests = _read_jsonl(REQUESTS_FILE)
    feedback = _read_jsonl(FEEDBACK_FILE)
    triage = _read_jsonl(TRIAGE_FILE)
    by_status: dict[str, int] = {}
    for row in requests:
        status = str(row.get("status") or "unknown")
        by_status[status] = by_status.get(status, 0) + 1
    feedback_status: dict[str, int] = {}
    for row in feedback:
        status = str(row.get("status") or "unknown")
        feedback_status[status] = feedback_status.get(status, 0) + 1
    return {
        "ok": True,
        "summary": {
            "review_requests": len(requests),
            "feedback_items": len(feedback),
            "triage_events": len(triage),
            "open_requests": len([r for r in requests if r.get("status") not in {"completed", "closed"}]),
            "moderation_queue": len([f for f in feedback if f.get("status") in {"queued", "needs_moderation"}]),
        },
        "requests_by_status": by_status,
        "feedback_by_status": feedback_status,
        "latest_requests": sorted(requests, key=lambda row: str(row.get("created_at") or ""), reverse=True)[:10],
        "latest_feedback": sorted(feedback, key=lambda row: str(row.get("created_at") or ""), reverse=True)[:10],
        "latest_triage": sorted(triage, key=lambda row: str(row.get("created_at") or ""), reverse=True)[:10],
        "real_only_note": COMMUNITY_REVIEW_NOTE,
        "safe_boundary": SAFE_BOUNDARY,
    }


def project_board(user_id: str, project_id: str | None = None) -> dict[str, Any]:
    requests = list_review_requests(user_id=user_id, project_id=project_id).get("requests", [])
    feedback = list_feedback(user_id=user_id, project_id=project_id).get("feedback", [])
    triage = list_triage(user_id=user_id, project_id=project_id).get("triage", [])
    return {
        "ok": True,
        "user_id": user_id,
        "project_id": project_id,
        "requests": requests,
        "feedback": feedback,
        "triage": triage,
        "summary": {
            "requests": len(requests),
            "feedback_items": len(feedback),
            "triage_events": len(triage),
            "open_requests": len([r for r in requests if r.get("status") not in {"completed", "closed"}]),
            "needs_moderation": len([f for f in feedback if f.get("status") in {"queued", "needs_moderation"}]),
        },
        "reviewer_rules": [
            "Use only authorized scope and non-sensitive evidence.",
            "Do not ask for seed phrases, private keys, wallet signatures, or production secrets.",
            "Provide severity, evidence, fix direction, and verification step.",
            "Avoid audit/certification wording unless a real certified audit process exists.",
        ],
        "real_only_note": COMMUNITY_REVIEW_NOTE,
    }
