from __future__ import annotations

import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from typing import Any

from app.services.database_store import get_project, list_projects, list_reports, list_scans
from app.services.eon import build_fix_plan, build_risk_graph, evidence_ledger
from app.services.sentinel import build_project_alerts

PUBLIC_TRUST_REAL_ONLY_NOTE = (
    "Web3Guard public trust pages summarize stored project records, scan history, saved reports, EON evidence ledger entries, "
    "and Sentinel-derived alerts only. They do not certify, audit, guarantee security, or create fake trust badges; Web3Guard does not certify project safety from this page. "
    "Not Assessed modules are shown clearly instead of being hidden or fake-scored."
)

PUBLIC_TRUST_SAFE_WORDING = "Pre-audit launch-readiness reviewed"
PUBLIC_TRUST_UNSAFE_WORDING = [
    "Audited by Web3Guard",
    "Certified secure",
    "100% secure",
    "Exploit-free",
    "Guaranteed safe",
    "KYC/audit completed unless separately verified",
]

MODULE_CATALOG = [
    {
        "id": "website",
        "label": "Website surface",
        "description": "HTTPS, security headers, security.txt, robots/sitemap, policy and launch-page visibility.",
        "required_for_public_launch": True,
    },
    {
        "id": "contract",
        "label": "Smart contract rules",
        "description": "Pasted or verified Solidity rule-engine findings and contract-source evidence.",
        "required_for_public_launch": True,
    },
    {
        "id": "github",
        "label": "GitHub hygiene",
        "description": "SECURITY.md, CI, tests, lockfiles, dependency posture, and repo hygiene signals.",
        "required_for_public_launch": False,
    },
    {
        "id": "wallet",
        "label": "Wallet/token UX",
        "description": "Approval clarity, chain mismatch, token risk, spender visibility, and wallet flow safety evidence.",
        "required_for_public_launch": False,
    },
    {
        "id": "api",
        "label": "API/backend readiness",
        "description": "Auth, CORS, rate limits, webhooks, IDOR/BOLA checklist and backend exposure evidence.",
        "required_for_public_launch": False,
    },
    {
        "id": "admin_opsec",
        "label": "Admin OpSec",
        "description": "Owner roles, multisig/timelock, emergency powers, signer rotation, and incident workflow evidence.",
        "required_for_public_launch": True,
    },
    {
        "id": "provider",
        "label": "Provider readiness",
        "description": "Etherscan-compatible explorer, GoPlus, GitHub token, and real tool/provider status.",
        "required_for_public_launch": False,
    },
    {
        "id": "monitoring",
        "label": "Sentinel monitoring",
        "description": "Public advisory intelligence, project alerts, and responsible disclosure readiness.",
        "required_for_public_launch": False,
    },
    {
        "id": "report",
        "label": "Report verification",
        "description": "Report ID, report hash, public summary, and evidence-ledger integrity references.",
        "required_for_public_launch": True,
    },
]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _dump(value: Any) -> str:
    try:
        return json.dumps(value, ensure_ascii=False, default=str, sort_keys=True)
    except Exception:
        return str(value)


def _sha(value: Any) -> str:
    return hashlib.sha256(_dump(value).encode("utf-8")).hexdigest()


def _obj_dump(obj: Any) -> dict[str, Any]:
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    if isinstance(obj, dict):
        return obj
    return {key: getattr(obj, key) for key in dir(obj) if not key.startswith("_") and not callable(getattr(obj, key, None))}


def _module_from_text(value: str) -> str | None:
    text = value.lower()
    if any(token in text for token in ["website", "header", "security.txt", "url", "launch"]):
        return "website"
    if any(token in text for token in ["contract", "solidity", "static", "address", "permission", "upgrade"]):
        return "contract"
    if any(token in text for token in ["github", "repo", "repository", "dependency", "lockfile"]):
        return "github"
    if any(token in text for token in ["wallet", "token", "approval", "goplus", "spender"]):
        return "wallet"
    if any(token in text for token in ["api", "backend", "cors", "webhook", "idor", "bola"]):
        return "api"
    if any(token in text for token in ["admin", "opsec", "multisig", "timelock", "owner"]):
        return "admin_opsec"
    if any(token in text for token in ["provider", "etherscan", "engine", "slither", "aderyn"]):
        return "provider"
    if any(token in text for token in ["sentinel", "monitoring", "advisory", "intelligence"]):
        return "monitoring"
    if "report" in text or "hash" in text:
        return "report"
    return None


def _status_from_score(score: Any, critical_high_count: int = 0, risk_label: str | None = None) -> str:
    label = (risk_label or "").lower()
    if critical_high_count > 0 or "critical" in label:
        return "needs_fix"
    if "high" in label or "manual" in label or "evidence" in label:
        return "evidence_needed"
    if isinstance(score, (int, float)):
        if score >= 80:
            return "reviewed"
        if score >= 60:
            return "evidence_needed"
        return "needs_fix"
    return "assessed"


def public_trust_status() -> dict[str, Any]:
    return {
        "ok": True,
        "phase": "Phase 18 — Public Trust Page Generator",
        "public_wording": PUBLIC_TRUST_SAFE_WORDING,
        "blocked_wording": PUBLIC_TRUST_UNSAFE_WORDING,
        "modules": MODULE_CATALOG,
        "real_only_note": PUBLIC_TRUST_REAL_ONLY_NOTE,
        "boundaries": [
            "Public trust page is a launch-readiness summary, not a certified audit.",
            "Report hash proves report-payload integrity only, not project safety.",
            "Not Assessed modules must stay visible.",
            "No fake trust badges, no guarantee, no 100% secure claim.",
        ],
    }


def _collect_module_evidence(user_id: str, project_id: str) -> dict[str, list[dict[str, Any]]]:
    module_evidence: dict[str, list[dict[str, Any]]] = {module["id"]: [] for module in MODULE_CATALOG}
    scans = list_scans(user_id, limit=200, project_id=project_id)
    reports = list_reports(user_id, limit=200, project_id=project_id)

    for scan in scans:
        payload = _obj_dump(scan)
        text = f"{getattr(scan, 'module', '')} {getattr(scan, 'risk_label', '')} {_dump(payload.get('payload', {}))}"
        module_id = _module_from_text(text) or "report"
        module_evidence.setdefault(module_id, []).append(
            {
                "kind": "scan",
                "id": getattr(scan, "id", None),
                "title": f"{getattr(scan, 'module', 'scan')} scan",
                "score": getattr(scan, "score", None),
                "risk_label": getattr(scan, "risk_label", None),
                "critical_high_count": getattr(scan, "critical_high_count", 0),
                "findings_count": getattr(scan, "findings_count", 0),
                "created_at": str(getattr(scan, "created_at", "")),
                "evidence_hash": _sha(payload),
            }
        )

    for report in reports:
        payload = _obj_dump(report)
        module_evidence.setdefault("report", []).append(
            {
                "kind": "report",
                "id": getattr(report, "id", None),
                "title": getattr(report, "title", "Saved report"),
                "report_id": getattr(report, "report_id", None),
                "report_hash": getattr(report, "report_hash", None),
                "score": getattr(report, "overall_score", None) or getattr(report, "available_score", None),
                "risk_label": getattr(report, "risk_label", None),
                "visibility": getattr(report, "visibility", None),
                "status": getattr(report, "status", None),
                "created_at": str(getattr(report, "created_at", "")),
                "evidence_hash": _sha(payload),
            }
        )

    return module_evidence


def _module_statuses(user_id: str, project_id: str) -> list[dict[str, Any]]:
    evidence = _collect_module_evidence(user_id, project_id)
    rows: list[dict[str, Any]] = []
    for module in MODULE_CATALOG:
        module_items = evidence.get(module["id"], [])
        if not module_items:
            status = "not_assessed"
            public_label = "Not Assessed"
            evidence_count = 0
            latest = None
        else:
            evidence_count = len(module_items)
            latest = module_items[0]
            statuses = [
                _status_from_score(item.get("score"), int(item.get("critical_high_count") or 0), item.get("risk_label"))
                for item in module_items
            ]
            if "needs_fix" in statuses:
                status = "needs_fix"
                public_label = "Needs Fix"
            elif "evidence_needed" in statuses:
                status = "evidence_needed"
                public_label = "Evidence Needed"
            else:
                status = "reviewed"
                public_label = "Reviewed"
        rows.append(
            {
                **module,
                "status": status,
                "public_label": public_label,
                "evidence_count": evidence_count,
                "latest_evidence": latest,
            }
        )
    return rows


def _latest_report(user_id: str, project_id: str) -> dict[str, Any] | None:
    reports = list_reports(user_id, limit=50, project_id=project_id)
    if not reports:
        return None
    report = reports[0]
    return _obj_dump(report)


def build_public_trust_page(user_id: str, project_id: str) -> dict[str, Any]:
    project = get_project(user_id, project_id)
    if not project:
        raise ValueError("Project not found for this user_id/project_id. Public trust page cannot be generated from missing data.")

    project_payload = _obj_dump(project)
    modules = _module_statuses(user_id, project_id)
    assessed = [item for item in modules if item["status"] != "not_assessed"]
    not_assessed = [item for item in modules if item["status"] == "not_assessed"]
    needs_attention = [item for item in modules if item["status"] in {"needs_fix", "evidence_needed"}]

    report = _latest_report(user_id, project_id)
    graph = build_risk_graph(user_id=user_id, project_id=project_id)
    fix_plan = build_fix_plan(user_id=user_id, project_id=project_id)
    ledger = evidence_ledger(user_id=user_id, project_id=project_id)
    sentinel = build_project_alerts(user_id=user_id, project_id=project_id)

    ledger_entries = ledger.get("entries", []) if isinstance(ledger, dict) else []
    open_tasks = [task for task in fix_plan.get("tasks", []) if isinstance(task, dict) and task.get("status") not in {"fixed"}]
    fixed_tasks = [task for task in fix_plan.get("tasks", []) if isinstance(task, dict) and task.get("status") == "fixed"]
    alerts = sentinel.get("alerts", []) if isinstance(sentinel, dict) else []

    trust_payload_for_hash = {
        "project": project_payload,
        "modules": modules,
        "latest_report_hash": report.get("report_hash") if report else None,
        "ledger_hashes": [entry.get("evidence_hash") for entry in ledger_entries[:25] if isinstance(entry, dict)],
        "generated_at": _now(),
    }
    trust_page_hash = _sha(trust_payload_for_hash)

    return {
        "ok": True,
        "generated_at": _now(),
        "public_wording": PUBLIC_TRUST_SAFE_WORDING,
        "project": {
            "id": project.id,
            "name": project.name,
            "website_url": project.website_url,
            "chain": project.chain,
            "contract_address": project.contract_address,
            "github_repo_url": project.github_repo_url,
            "project_type": project.project_type,
            "description": project.description,
            "created_at": str(project.created_at),
            "updated_at": str(project.updated_at) if project.updated_at else None,
        },
        "summary": {
            "assessed_modules": len(assessed),
            "not_assessed_modules": len(not_assessed),
            "needs_attention_modules": len(needs_attention),
            "evidence_entries": len(ledger_entries),
            "open_fix_tasks": len(open_tasks),
            "fixed_tasks": len(fixed_tasks),
            "sentinel_alerts": len(alerts),
            "launch_blockers": graph.get("summary", {}).get("launch_blockers", 0) if isinstance(graph, dict) else 0,
        },
        "modules": modules,
        "latest_report": {
            "available": bool(report),
            "report_id": report.get("report_id") if report else None,
            "report_hash": report.get("report_hash") if report else None,
            "risk_label": report.get("risk_label") if report else None,
            "visibility": report.get("visibility") if report else None,
            "status": report.get("status") if report else "not_generated",
            "integrity_note": "Report hash verifies report payload integrity only. It does not certify safety.",
        },
        "fix_status": {
            "open_tasks": open_tasks[:12],
            "fixed_tasks": fixed_tasks[:12],
            "workflow_note": "Fix tasks must be updated only after new evidence or re-scan proof exists. Do not mark issues fixed for marketing reasons.",
        },
        "evidence_ledger_summary": {
            "entries": ledger_entries[:20],
            "counts": dict(Counter(entry.get("kind") for entry in ledger_entries if isinstance(entry, dict))),
            "integrity_note": "Evidence hashes prove captured payload integrity, not project security or audit completion.",
        },
        "sentinel_summary": {
            "alerts": alerts[:12],
            "note": "Sentinel alerts are derived from stored project evidence and indexed public advisories. They are not proof of exploitation.",
        },
        "responsible_disclosure": {
            "available": True,
            "recommended_link": f"/sentinel/disclosure?project_id={project.id}",
            "public_note": "Use responsible disclosure for validated, authorized, non-invasive findings. Web3Guard does not send disclosure emails automatically.",
        },
        "share_card": {
            "title": f"{project.name} · {PUBLIC_TRUST_SAFE_WORDING}",
            "subtitle": "Evidence-first public readiness summary. Not a certified audit.",
            "bullets": [
                f"{len(assessed)} modules reviewed from stored evidence",
                f"{len(not_assessed)} modules clearly marked Not Assessed",
                "Report hash and evidence ledger shown when available",
                "No audited / certified / 100% secure claim",
            ],
        },
        "trust_page_hash": trust_page_hash,
        "safe_public_claims": [
            PUBLIC_TRUST_SAFE_WORDING,
            "Evidence-first readiness summary",
            "Not Assessed modules disclosed",
            "Report hash available when generated",
        ],
        "blocked_claims": PUBLIC_TRUST_UNSAFE_WORDING,
        "real_only_note": PUBLIC_TRUST_REAL_ONLY_NOTE,
    }


def list_public_trust_projects(user_id: str, limit: int = 50) -> dict[str, Any]:
    projects = list_projects(user_id, limit=limit)
    items: list[dict[str, Any]] = []
    for project in projects:
        modules = _module_statuses(user_id, project.id)
        assessed = [item for item in modules if item["status"] != "not_assessed"]
        reports = list_reports(user_id, limit=1, project_id=project.id)
        items.append(
            {
                "id": project.id,
                "name": project.name,
                "website_url": project.website_url,
                "project_type": project.project_type,
                "chain": project.chain,
                "assessed_modules": len(assessed),
                "total_modules": len(MODULE_CATALOG),
                "latest_report_hash": getattr(reports[0], "report_hash", None) if reports else None,
                "public_path": f"/trust-pages/project/{project.id}?user_id={user_id}",
                "status": "ready_to_preview" if assessed else "needs_evidence",
            }
        )
    return {
        "ok": True,
        "user_id": user_id,
        "items": items,
        "empty_state": "No stored projects found. Create a project and save real scan/report evidence before generating a public trust page.",
        "real_only_note": PUBLIC_TRUST_REAL_ONLY_NOTE,
    }
