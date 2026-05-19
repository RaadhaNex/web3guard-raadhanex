from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

AGENCY_LAUNCH_NOTE = (
    "Web3Guard Agency Launch Layer stores real owner-created client, intake, white-label, and handoff records only. "
    "It does not create fake enterprise customers, fake audit claims, fake verified reviewers, or certified-audit wording."
)

SAFE_AGENCY_BOUNDARY = (
    "Use this workspace only for clients/projects you own or are explicitly authorized to support. "
    "Do not request private keys, seed phrases, mnemonics, production credentials, wallet signatures, or exploit live systems. "
    "Client handoff packs are pre-audit readiness handoffs, not certified audits."
)

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data" / "db"
CLIENTS_FILE = DATA_DIR / "agency_clients.jsonl"
INTAKE_FILE = DATA_DIR / "agency_intake_requests.jsonl"
WHITE_LABEL_FILE = DATA_DIR / "agency_white_label_settings.jsonl"
HANDOFF_FILE = DATA_DIR / "agency_handoff_packs.jsonl"

CLIENT_STATUSES = {"prospect", "active", "paused", "handoff_ready", "completed", "archived"}
INTAKE_STATUSES = {"new", "qualified", "needs_scope", "proposal_ready", "accepted", "rejected", "closed"}
HANDOFF_STATUSES = {"draft", "ready", "sent_manually", "accepted", "closed"}

BLOCKED_CLAIMS = [
    "certified audit",
    "certified auditor",
    "100% secure",
    "100 percent secure",
    "audited by web3guard",
    "web3guard audited",
    "verified auditor",
    "guaranteed secure",
    "exploit proof",
]

DEFAULT_SERVICES = [
    "pre_audit_readiness_review",
    "launch_trust_readiness",
    "public_trust_page_setup",
    "security_passport_setup",
    "community_review_coordination",
    "monitoring_lite_setup",
    "founder_opsec_checklist",
]


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


def _latest_by_owner(path: Path, owner_user_id: str, organization_id: str | None = None) -> list[dict[str, Any]]:
    rows = [row for row in _read_jsonl(path) if str(row.get("owner_user_id") or "") == owner_user_id]
    if organization_id:
        rows = [row for row in rows if str(row.get("organization_id") or "") == organization_id]
    return sorted(rows, key=lambda row: str(row.get("created_at") or ""), reverse=True)


def _normalize_status(value: str | None, allowed: set[str], default: str) -> str:
    clean = (value or default).strip().lower().replace(" ", "_")
    return clean if clean in allowed else default


def _compact_list(value: Any, limit: int = 12) -> list[str]:
    if not isinstance(value, list):
        return []
    result: list[str] = []
    for item in value:
        clean = str(item).strip()
        if clean:
            result.append(clean[:160])
        if len(result) >= limit:
            break
    return result


def _contains_blocked_claim(*values: str | None) -> str | None:
    text = " ".join(value or "" for value in values).lower()
    safe_certification_negations = (
        "not a certified audit",
        "not certified audit",
        "not a certified auditor",
        "not certified auditor",
        "does not replace a certified audit",
        "does not replace an external audit",
    )
    for claim in BLOCKED_CLAIMS:
        if claim not in text:
            continue
        if claim in {"certified audit", "certified auditor"} and any(phrase in text for phrase in safe_certification_negations):
            continue
        return claim
    return None


def agency_launch_status() -> dict[str, Any]:
    clients = _read_jsonl(CLIENTS_FILE)
    intake = _read_jsonl(INTAKE_FILE)
    labels = _read_jsonl(WHITE_LABEL_FILE)
    handoffs = _read_jsonl(HANDOFF_FILE)
    return {
        "ok": True,
        "phase": "Phase 26 — Enterprise / Agency Launch Layer",
        "mode": "local_first_real_records",
        "counts": {
            "client_profiles": len(clients),
            "intake_requests": len(intake),
            "white_label_settings": len(labels),
            "handoff_packs": len(handoffs),
            "active_clients": len([row for row in clients if row.get("status") == "active"]),
            "ready_handoffs": len([row for row in handoffs if row.get("status") == "ready"]),
        },
        "capabilities": [
            "client_project_portfolio",
            "agency_intake_queue",
            "team_role_playbook",
            "white_label_report_settings",
            "client_handoff_pack_builder",
            "safe_scope_and_disclaimer_guardrails",
        ],
        "blocked_claims": BLOCKED_CLAIMS,
        "real_only_note": AGENCY_LAUNCH_NOTE,
        "safe_boundary": SAFE_AGENCY_BOUNDARY,
    }


def create_client_profile(payload: dict[str, Any]) -> dict[str, Any]:
    if not payload.get("authorization_confirmed"):
        raise ValueError("authorization_confirmed must be true before saving a client profile")
    owner_user_id = str(payload.get("owner_user_id") or "local-demo-user").strip()
    client_name = str(payload.get("client_name") or "").strip()
    if len(client_name) < 2:
        raise ValueError("client_name is required")
    blocked = _contains_blocked_claim(client_name, payload.get("project_summary"), payload.get("notes"))
    if blocked:
        raise ValueError(f"Blocked unsafe claim detected: {blocked}")
    record = {
        "id": _id("agc", payload),
        "owner_user_id": owner_user_id,
        "organization_id": payload.get("organization_id") or None,
        "client_name": client_name[:180],
        "contact_email": payload.get("contact_email") or None,
        "website_url": payload.get("website_url") or None,
        "project_id": payload.get("project_id") or None,
        "project_name": str(payload.get("project_name") or "").strip()[:180] or None,
        "project_summary": str(payload.get("project_summary") or "").strip()[:2500],
        "chain": str(payload.get("chain") or "").strip()[:80] or None,
        "status": _normalize_status(str(payload.get("status") or "active"), CLIENT_STATUSES, "active"),
        "tags": _compact_list(payload.get("tags"), limit=10),
        "notes": str(payload.get("notes") or "").strip()[:2000],
        "created_at": _now(),
        "updated_at": _now(),
        "authorization_confirmed": True,
        "safe_wording": "Client profile saved as owner-provided agency/workspace data. This is not a public customer claim unless separately authorized.",
    }
    _append_jsonl(CLIENTS_FILE, record)
    return {"ok": True, "client": record, "real_only_note": AGENCY_LAUNCH_NOTE}


def list_client_profiles(owner_user_id: str, organization_id: str | None = None, limit: int = 100) -> dict[str, Any]:
    rows = _latest_by_owner(CLIENTS_FILE, owner_user_id=owner_user_id, organization_id=organization_id)[:limit]
    return {"ok": True, "clients": rows, "count": len(rows), "real_only_note": AGENCY_LAUNCH_NOTE}


def create_intake_request(payload: dict[str, Any]) -> dict[str, Any]:
    if not payload.get("safe_use_acknowledged"):
        raise ValueError("safe_use_acknowledged must be true before saving intake")
    if not payload.get("authorization_confirmed"):
        raise ValueError("authorization_confirmed must be true before saving intake")
    owner_user_id = str(payload.get("owner_user_id") or "local-demo-user").strip()
    client_name = str(payload.get("client_name") or "").strip()
    if len(client_name) < 2:
        raise ValueError("client_name is required")
    scope_summary = str(payload.get("scope_summary") or "").strip()
    if len(scope_summary) < 10:
        raise ValueError("scope_summary must explain the client request")
    blocked = _contains_blocked_claim(client_name, scope_summary, payload.get("notes"))
    if blocked:
        raise ValueError(f"Blocked unsafe claim detected: {blocked}")
    record = {
        "id": _id("agi", payload),
        "owner_user_id": owner_user_id,
        "organization_id": payload.get("organization_id") or None,
        "client_name": client_name[:180],
        "contact_email": payload.get("contact_email") or None,
        "contact_handle": str(payload.get("contact_handle") or "").strip()[:160] or None,
        "website_url": payload.get("website_url") or None,
        "repo_url": payload.get("repo_url") or None,
        "scope_summary": scope_summary[:3000],
        "requested_services": _compact_list(payload.get("requested_services"), limit=12) or DEFAULT_SERVICES[:4],
        "status": _normalize_status(str(payload.get("status") or "new"), INTAKE_STATUSES, "new"),
        "priority": str(payload.get("priority") or "medium").strip().lower()[:40],
        "notes": str(payload.get("notes") or "").strip()[:2000],
        "authorization_confirmed": True,
        "safe_use_acknowledged": True,
        "created_at": _now(),
        "updated_at": _now(),
        "safe_boundary": SAFE_AGENCY_BOUNDARY,
    }
    _append_jsonl(INTAKE_FILE, record)
    return {"ok": True, "intake": record, "real_only_note": AGENCY_LAUNCH_NOTE}


def list_intake_requests(owner_user_id: str, organization_id: str | None = None, status: str | None = None, limit: int = 100) -> dict[str, Any]:
    rows = _latest_by_owner(INTAKE_FILE, owner_user_id=owner_user_id, organization_id=organization_id)
    if status:
        wanted = _normalize_status(status, INTAKE_STATUSES, status)
        rows = [row for row in rows if row.get("status") == wanted]
    rows = rows[:limit]
    return {"ok": True, "intake_requests": rows, "count": len(rows), "real_only_note": AGENCY_LAUNCH_NOTE}


def save_white_label_settings(payload: dict[str, Any]) -> dict[str, Any]:
    owner_user_id = str(payload.get("owner_user_id") or "local-demo-user").strip()
    brand_name = str(payload.get("brand_name") or "").strip()
    if len(brand_name) < 2:
        raise ValueError("brand_name is required")
    blocked = _contains_blocked_claim(
        brand_name,
        payload.get("report_footer"),
        payload.get("custom_disclaimer"),
        payload.get("client_safe_wording"),
    )
    if blocked:
        raise ValueError(f"Blocked unsafe claim detected: {blocked}")
    custom_disclaimer = str(payload.get("custom_disclaimer") or "").strip()
    if not custom_disclaimer:
        custom_disclaimer = "Prepared as a pre-audit readiness handoff. Not a certified audit or guarantee of security."
    record = {
        "id": _id("agw", payload),
        "owner_user_id": owner_user_id,
        "organization_id": payload.get("organization_id") or None,
        "brand_name": brand_name[:180],
        "logo_url": payload.get("logo_url") or None,
        "accent_label": str(payload.get("accent_label") or "").strip()[:80] or None,
        "report_footer": str(payload.get("report_footer") or "").strip()[:600],
        "custom_disclaimer": custom_disclaimer[:800],
        "show_powered_by_raadhanex": bool(payload.get("show_powered_by_raadhanex", True)),
        "client_safe_wording": str(payload.get("client_safe_wording") or "Owner-provided white-label presentation settings only.").strip()[:600],
        "created_at": _now(),
        "updated_at": _now(),
        "safe_wording": "White-label settings change presentation only. They do not create certification, audit, or customer-proof claims.",
    }
    _append_jsonl(WHITE_LABEL_FILE, record)
    return {"ok": True, "white_label_settings": record, "real_only_note": AGENCY_LAUNCH_NOTE}


def list_white_label_settings(owner_user_id: str, organization_id: str | None = None, limit: int = 50) -> dict[str, Any]:
    rows = _latest_by_owner(WHITE_LABEL_FILE, owner_user_id=owner_user_id, organization_id=organization_id)[:limit]
    return {"ok": True, "white_label_settings": rows, "count": len(rows), "real_only_note": AGENCY_LAUNCH_NOTE}


def _find_client(owner_user_id: str, client_id: str) -> dict[str, Any] | None:
    return next(
        (
            row
            for row in _read_jsonl(CLIENTS_FILE)
            if row.get("id") == client_id and str(row.get("owner_user_id") or "") == owner_user_id
        ),
        None,
    )


def build_handoff_pack(payload: dict[str, Any]) -> dict[str, Any]:
    if not payload.get("authorization_confirmed"):
        raise ValueError("authorization_confirmed must be true before building a handoff pack")
    owner_user_id = str(payload.get("owner_user_id") or "local-demo-user").strip()
    client_id = str(payload.get("client_id") or "").strip()
    client = _find_client(owner_user_id, client_id) if client_id else None
    client_name = str(payload.get("client_name") or (client or {}).get("client_name") or "").strip()
    if len(client_name) < 2:
        raise ValueError("client_name or a valid client_id is required")
    blocked = _contains_blocked_claim(client_name, payload.get("handoff_notes"), payload.get("executive_summary"))
    if blocked:
        raise ValueError(f"Blocked unsafe claim detected: {blocked}")
    services = _compact_list(payload.get("services_included"), limit=12) or DEFAULT_SERVICES
    open_items = _compact_list(payload.get("open_items"), limit=20)
    evidence_links = _compact_list(payload.get("evidence_links"), limit=20)
    handoff_checklist = [
        "Confirm client owns or is authorized to test every listed asset.",
        "Attach latest Web3Guard report hash or Security Passport link when available.",
        "Keep Not Assessed modules visible instead of hiding missing evidence.",
        "Separate readiness notes from certified-audit language.",
        "Share remaining open actions, owner dependencies, and recommended external audit/bounty steps.",
        "Do not request private keys, seed phrases, mnemonics, wallet signing, or production credentials.",
    ]
    record = {
        "id": _id("agh", payload),
        "owner_user_id": owner_user_id,
        "organization_id": payload.get("organization_id") or (client or {}).get("organization_id"),
        "client_id": client_id or None,
        "client_name": client_name[:180],
        "project_id": payload.get("project_id") or (client or {}).get("project_id"),
        "project_name": str(payload.get("project_name") or (client or {}).get("project_name") or "").strip()[:180] or None,
        "status": _normalize_status(str(payload.get("status") or "ready"), HANDOFF_STATUSES, "ready"),
        "executive_summary": str(payload.get("executive_summary") or "Pre-audit readiness handoff prepared from available project evidence.").strip()[:2500],
        "services_included": services,
        "open_items": open_items,
        "evidence_links": evidence_links,
        "handoff_checklist": handoff_checklist,
        "client_email_template": {
            "subject": f"{client_name} — Web3Guard readiness handoff pack",
            "body": (
                f"Hi {client_name},\n\n"
                "Sharing the Web3Guard readiness handoff pack for your review. "
                "This is a pre-audit readiness handoff, not a certified audit or guarantee of security.\n\n"
                "Please review the open actions, Not Assessed modules, and evidence links before launch. "
                "For production-critical contracts, schedule a certified external audit and maintain responsible disclosure channels.\n\n"
                "Regards,\nYour security readiness team"
            ),
        },
        "safe_wording": "Client handoff pack is a readiness handoff only. It must not be marketed as a Web3Guard-certified audit.",
        "safe_boundary": SAFE_AGENCY_BOUNDARY,
        "created_at": _now(),
        "updated_at": _now(),
        "authorization_confirmed": True,
    }
    _append_jsonl(HANDOFF_FILE, record)
    return {"ok": True, "handoff_pack": record, "real_only_note": AGENCY_LAUNCH_NOTE}


def list_handoff_packs(owner_user_id: str, organization_id: str | None = None, client_id: str | None = None, limit: int = 100) -> dict[str, Any]:
    rows = _latest_by_owner(HANDOFF_FILE, owner_user_id=owner_user_id, organization_id=organization_id)
    if client_id:
        rows = [row for row in rows if row.get("client_id") == client_id]
    rows = rows[:limit]
    return {"ok": True, "handoff_packs": rows, "count": len(rows), "real_only_note": AGENCY_LAUNCH_NOTE}


def build_agency_portfolio(owner_user_id: str, organization_id: str | None = None, limit: int = 100) -> dict[str, Any]:
    clients = list_client_profiles(owner_user_id=owner_user_id, organization_id=organization_id, limit=limit)["clients"]
    handoffs = list_handoff_packs(owner_user_id=owner_user_id, organization_id=organization_id, limit=limit)["handoff_packs"]
    intake = list_intake_requests(owner_user_id=owner_user_id, organization_id=organization_id, limit=limit)["intake_requests"]
    labels = list_white_label_settings(owner_user_id=owner_user_id, organization_id=organization_id, limit=10)["white_label_settings"]
    client_cards = []
    for client in clients:
        client_handoffs = [row for row in handoffs if row.get("client_id") == client.get("id")]
        client_cards.append(
            {
                "client_id": client.get("id"),
                "client_name": client.get("client_name"),
                "project_name": client.get("project_name"),
                "website_url": client.get("website_url"),
                "status": client.get("status"),
                "tags": client.get("tags", []),
                "handoff_count": len(client_handoffs),
                "latest_handoff_status": client_handoffs[0].get("status") if client_handoffs else "not_started",
                "safe_wording": "Owner-created client record. Do not use as a public customer proof unless the client has separately approved it.",
            }
        )
    return {
        "ok": True,
        "owner_user_id": owner_user_id,
        "organization_id": organization_id,
        "portfolio": client_cards,
        "intake_queue": intake,
        "latest_white_label_settings": labels[0] if labels else None,
        "totals": {
            "clients": len(clients),
            "intake_requests": len(intake),
            "handoff_packs": len(handoffs),
            "white_label_profiles": len(labels),
        },
        "team_role_playbook": [
            {"role": "owner", "scope": "Client relationship, pricing, legal approval, final handoff."},
            {"role": "admin", "scope": "Workspace setup, intake qualification, report packaging."},
            {"role": "reviewer", "scope": "Manual evidence review and finding triage; no certification wording."},
            {"role": "viewer", "scope": "Client-safe read-only progress review."},
        ],
        "blocked_claims": BLOCKED_CLAIMS,
        "real_only_note": AGENCY_LAUNCH_NOTE,
        "safe_boundary": SAFE_AGENCY_BOUNDARY,
    }
