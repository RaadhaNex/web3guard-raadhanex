from __future__ import annotations

import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from typing import Any

from app.services.community_review import admin_overview as community_admin_overview
from app.services.community_review import project_board as community_project_board
from app.services.continuous_monitoring import admin_overview as monitoring_admin_dashboard
from app.services.continuous_monitoring import user_dashboard as monitoring_user_dashboard
from app.services.database_store import get_project, list_projects, list_reports, list_scans
from app.services.eon import evidence_ledger
from app.services.public_trust_page import build_public_trust_page
from app.services.sentinel import build_project_alerts
from app.services.trust_readiness import build_trust_readiness

SECURITY_PASSPORT_NOTE = (
    "Security Passport is a pre-audit readiness passport generated from stored Web3Guard records, report hashes, "
    "evidence ledger entries, monitoring state, community review workflow, and explicit external links. It is not a "
    "certified audit, not a security certificate, not a guarantee of safety, and must not be described as audited by Web3Guard."
)

SAFE_PASSPORT_LABEL = "Pre-audit readiness passport"
BLOCKED_PASSPORT_WORDING = [
    "audited by Web3Guard",
    "certified secure",
    "100% secure",
    "security certificate",
    "guaranteed safe",
    "exploit-free",
    "verified auditor badge unless a real external audit link exists",
]

EXTERNAL_LINK_TYPES = {"audit", "bounty", "docs", "monitoring", "disclosure", "other"}
_external_links: list[dict[str, Any]] = []


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _dump(value: Any) -> str:
    try:
        return json.dumps(value, default=str, ensure_ascii=False, sort_keys=True)
    except Exception:
        return str(value)


def _hash(value: Any) -> str:
    return hashlib.sha256(_dump(value).encode("utf-8")).hexdigest()


def _obj(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    if hasattr(value, "model_dump"):
        return value.model_dump()
    return {"value": str(value)}


def _safe_call(default: Any, func, *args, **kwargs) -> Any:
    try:
        return func(*args, **kwargs)
    except Exception as exc:
        if isinstance(default, dict):
            data = dict(default)
            data["error"] = str(exc)
            return data
        return default


def security_passport_status() -> dict[str, Any]:
    return {
        "ok": True,
        "phase": "Phase 24 — Security Passport / Trust Network",
        "label": SAFE_PASSPORT_LABEL,
        "real_only_note": SECURITY_PASSPORT_NOTE,
        "blocked_wording": BLOCKED_PASSPORT_WORDING,
        "boundaries": [
            "Passport summarizes readiness evidence only; it does not certify safety.",
            "Report hash proves report-payload integrity only, not project safety.",
            "External audit/bounty links are shown only when explicitly provided.",
            "Not Assessed modules and unresolved actions must stay visible.",
        ],
    }


def list_passport_projects(user_id: str, limit: int = 50) -> dict[str, Any]:
    projects = list_projects(user_id, limit=limit)
    passports = []
    for project in projects:
        passport = build_security_passport(user_id=user_id, project_id=project.id, compact=True)
        passports.append(
            {
                "project_id": project.id,
                "project_name": project.name,
                "website_url": project.website_url,
                "chain": project.chain,
                "project_type": project.project_type,
                "passport_id": passport["passport_id"],
                "readiness_score": passport["readiness_snapshot"].get("score"),
                "readiness_label": passport["readiness_snapshot"].get("label"),
                "passport_label": passport["public_share_card"].get("label"),
                "open_actions": passport["action_summary"].get("open_actions", 0),
                "not_assessed_modules": passport["action_summary"].get("not_assessed_modules", 0),
            }
        )
    return {
        "ok": True,
        "projects": passports,
        "count": len(passports),
        "real_only_note": SECURITY_PASSPORT_NOTE,
    }


def _external_links_for(user_id: str, project_id: str) -> list[dict[str, Any]]:
    return [
        link
        for link in _external_links
        if link.get("user_id") == user_id and link.get("project_id") == project_id
    ]


def add_external_link(payload: dict[str, Any]) -> dict[str, Any]:
    user_id = str(payload.get("user_id") or "").strip()
    project_id = str(payload.get("project_id") or "").strip()
    url = str(payload.get("url") or "").strip()
    title = str(payload.get("title") or "").strip()
    link_type = str(payload.get("link_type") or "other").strip().lower()

    if not user_id or not project_id or not url or not title:
        raise ValueError("user_id, project_id, title, and url are required.")
    if not (url.startswith("https://") or url.startswith("http://")):
        raise ValueError("External links must start with http:// or https://.")
    if link_type not in EXTERNAL_LINK_TYPES:
        link_type = "other"

    row = {
        "id": f"passport_link_{_hash({'user_id': user_id, 'project_id': project_id, 'url': url})[:16]}",
        "user_id": user_id,
        "project_id": project_id,
        "title": title,
        "url": url,
        "link_type": link_type,
        "notes": str(payload.get("notes") or "").strip(),
        "created_at": _now(),
        "safe_wording": "External link supplied by project owner/admin. Web3Guard does not convert this into a certification claim.",
    }
    _external_links.append(row)
    return {"ok": True, "link": row, "real_only_note": SECURITY_PASSPORT_NOTE}


def _latest_report(reports: list[Any]) -> dict[str, Any] | None:
    if not reports:
        return None
    report = _obj(reports[0])
    return {
        "id": report.get("id"),
        "title": report.get("title"),
        "report_id": report.get("report_id"),
        "report_hash": report.get("report_hash"),
        "risk_label": report.get("risk_label"),
        "overall_score": report.get("overall_score") or report.get("available_score"),
        "created_at": str(report.get("created_at") or ""),
        "visibility": report.get("visibility"),
        "status": report.get("status"),
    }


def _module_summary(trust_page: dict[str, Any]) -> dict[str, Any]:
    modules = trust_page.get("module_statuses") or trust_page.get("modules") or []
    if not isinstance(modules, list):
        modules = []
    statuses = Counter(str(row.get("status") or row.get("public_label") or "unknown") for row in modules)
    not_assessed = [row for row in modules if "not" in str(row.get("status") or row.get("public_label") or "").lower()]
    return {
        "modules": modules,
        "counts": dict(statuses),
        "not_assessed_count": len(not_assessed),
        "assessed_count": max(0, len(modules) - len(not_assessed)),
    }


def build_security_passport(user_id: str, project_id: str, compact: bool = False) -> dict[str, Any]:
    project = get_project(user_id, project_id)
    if not project:
        return {
            "ok": False,
            "error": "Project not found for this user.",
            "project_id": project_id,
            "real_only_note": SECURITY_PASSPORT_NOTE,
        }

    reports = list_reports(user_id, limit=10, project_id=project_id)
    scans = list_scans(user_id, limit=50, project_id=project_id)

    trust_page = _safe_call({"ok": False, "module_statuses": []}, build_public_trust_page, user_id=user_id, project_id=project_id)
    readiness = _safe_call({"ok": False, "score": None, "label": "Not Assessed", "components": []}, build_trust_readiness, user_id=user_id, project_id=project_id)
    ledger = _safe_call({"ok": False, "entries": []}, evidence_ledger, user_id=user_id, project_id=project_id)
    monitoring = _safe_call({"ok": False, "configs": [], "alerts": []}, monitoring_user_dashboard, user_id=user_id)
    alerts = _safe_call({"ok": False, "alerts": []}, build_project_alerts, user_id=user_id, project_id=project_id)
    community = _safe_call({"ok": False, "requests": [], "feedback": [], "triage": []}, community_project_board, user_id=user_id, project_id=project_id)

    project_payload = _obj(project)
    latest_report = _latest_report(reports)
    module_summary = _module_summary(trust_page if isinstance(trust_page, dict) else {})
    ledger_entries = ledger.get("entries", []) if isinstance(ledger, dict) else []
    monitoring_alerts = monitoring.get("alerts", []) if isinstance(monitoring, dict) else []
    sentinel_alerts = alerts.get("alerts", []) if isinstance(alerts, dict) else []
    triage = community.get("triage", []) if isinstance(community, dict) else []
    feedback = community.get("feedback", []) if isinstance(community, dict) else []
    requests = community.get("requests", []) if isinstance(community, dict) else []
    ext_links = _external_links_for(user_id, project_id)

    passport_payload_for_hash = {
        "project": project_payload,
        "latest_report": latest_report,
        "readiness_score": readiness.get("score") if isinstance(readiness, dict) else None,
        "module_counts": module_summary.get("counts"),
        "ledger_count": len(ledger_entries),
        "alerts_count": len(sentinel_alerts) + len(monitoring_alerts),
        "community_triage_count": len(triage),
        "external_links_count": len(ext_links),
    }
    passport_hash = _hash(passport_payload_for_hash)
    passport_id = f"w3g_passport_{passport_hash[:16]}"

    action_summary = {
        "open_actions": sum(1 for row in triage if str(row.get("status", "open")).lower() in {"open", "triaged", "in_progress", "manual_review_required"}),
        "not_assessed_modules": module_summary.get("not_assessed_count", 0),
        "monitoring_alerts": len(monitoring_alerts),
        "sentinel_alerts": len(sentinel_alerts),
        "community_feedback_items": len(feedback),
        "review_requests": len(requests),
    }

    public_share_card = {
        "label": SAFE_PASSPORT_LABEL,
        "title": f"{project.name} — Web3Guard Security Passport",
        "subtitle": "Pre-audit readiness passport, not a certified audit.",
        "score": readiness.get("score") if isinstance(readiness, dict) else None,
        "readiness_label": readiness.get("label") if isinstance(readiness, dict) else "Not Assessed",
        "report_hash": latest_report.get("report_hash") if latest_report else None,
        "passport_hash": passport_hash,
        "safe_wording": "Share as a readiness snapshot only. Do not describe as audited/certified unless a real external audit is linked.",
    }

    result = {
        "ok": True,
        "passport_id": passport_id,
        "passport_hash": passport_hash,
        "generated_at": _now(),
        "project": project_payload,
        "readiness_snapshot": {
            "score": readiness.get("score") if isinstance(readiness, dict) else None,
            "label": readiness.get("label") if isinstance(readiness, dict) else "Not Assessed",
            "components": readiness.get("components", []) if isinstance(readiness, dict) else [],
            "blocked_wording": readiness.get("blocked_wording", BLOCKED_PASSPORT_WORDING) if isinstance(readiness, dict) else BLOCKED_PASSPORT_WORDING,
        },
        "latest_report": latest_report,
        "module_summary": module_summary,
        "evidence_summary": {
            "entries_count": len(ledger_entries),
            "latest_entries": ledger_entries[:8],
            "note": "Evidence hashes prove payload integrity only; they do not prove project safety.",
        },
        "monitoring_status": {
            "configs_count": len(monitoring.get("configs", [])) if isinstance(monitoring, dict) else 0,
            "alerts_count": len(monitoring_alerts),
            "latest_alerts": monitoring_alerts[:5],
        },
        "sentinel_status": {
            "alerts_count": len(sentinel_alerts),
            "latest_alerts": sentinel_alerts[:5],
        },
        "community_review_status": {
            "requests_count": len(requests),
            "feedback_count": len(feedback),
            "triage_count": len(triage),
            "latest_triage": triage[:5],
        },
        "external_links": ext_links,
        "action_summary": action_summary,
        "public_share_card": public_share_card,
        "safe_wording": SAFE_PASSPORT_LABEL,
        "real_only_note": SECURITY_PASSPORT_NOTE,
    }
    if compact:
        return {
            "ok": result["ok"],
            "passport_id": passport_id,
            "passport_hash": passport_hash,
            "project": result["project"],
            "readiness_snapshot": result["readiness_snapshot"],
            "action_summary": action_summary,
            "public_share_card": public_share_card,
            "real_only_note": SECURITY_PASSPORT_NOTE,
        }
    return result


def security_passport_admin_overview() -> dict[str, Any]:
    monitoring = _safe_call({"ok": False}, monitoring_admin_dashboard)
    community = _safe_call({"ok": False}, community_admin_overview)
    return {
        "ok": True,
        "generated_at": _now(),
        "passport_label": SAFE_PASSPORT_LABEL,
        "monitoring_overview": monitoring,
        "community_overview": community,
        "external_links_count": len(_external_links),
        "external_link_types": dict(Counter(link.get("link_type", "other") for link in _external_links)),
        "boundaries": security_passport_status()["boundaries"],
        "real_only_note": SECURITY_PASSPORT_NOTE,
    }
