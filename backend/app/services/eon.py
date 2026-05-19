from __future__ import annotations

import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from typing import Any

from app.core.config import settings
from app.services.database_store import list_projects, list_reports, list_scans
from app.services.sentinel import build_project_alerts, list_intelligence

EON_REAL_ONLY_NOTE = (
    "Web3Guard EON builds project risk graphs, fix plans, and evidence ledger entries only from stored projects, scans, reports, "
    "Sentinel-derived alerts, and indexed public advisories. It does not invent evidence, does not perform exploit automation, "
    "and does not claim certified audit or 100% security."
)

EON_SAFE_BOUNDARY = (
    "Defensive launch-readiness workflow only. No unauthorized active scanning, no exploit attempts, no wallet signing, "
    "no private key or seed phrase collection."
)

MODULES = [
    {
        "id": "website",
        "label": "Website surface",
        "required": True,
        "scan_keywords": ["website", "unified", "url", "launch"],
        "missing_action": "Add website URL and run website/unified launch scan.",
        "verify": "Run /scanner/unified-url or /scanner/website and confirm headers/security.txt evidence.",
    },
    {
        "id": "contract",
        "label": "Smart contract rules",
        "required": True,
        "scan_keywords": ["contract", "solidity", "static", "address", "permission", "upgrade"],
        "missing_action": "Provide verified source or pasted Solidity and run contract/static checks.",
        "verify": "Run contract scanner and review critical/high findings plus Not Assessed modules.",
    },
    {
        "id": "github",
        "label": "GitHub repository hygiene",
        "required": False,
        "scan_keywords": ["github", "repo", "repository"],
        "missing_action": "Connect or submit a public authorized GitHub repo for read-only hygiene checks.",
        "verify": "Run GitHub scanner and confirm SECURITY.md, tests, lockfile, and CI evidence.",
    },
    {
        "id": "api",
        "label": "API/backend readiness",
        "required": False,
        "scan_keywords": ["api", "backend", "dapp"],
        "missing_action": "Submit authorized API/base URL evidence for CORS/auth/rate-limit checklist review.",
        "verify": "Run API/deep-readiness scanner and confirm missing controls are documented.",
    },
    {
        "id": "wallet",
        "label": "Wallet/token UX safety",
        "required": False,
        "scan_keywords": ["wallet", "goplus", "token", "approval"],
        "missing_action": "Document wallet flow, chain switching, approvals, spender visibility, and token risk provider status.",
        "verify": "Run wallet/token readiness checks and confirm no wallet signing is requested by Web3Guard.",
    },
    {
        "id": "admin_opsec",
        "label": "Admin OpSec",
        "required": True,
        "scan_keywords": ["admin", "opsec", "multisig", "ownership", "permission"],
        "missing_action": "Add admin ownership, multisig/timelock, signer rotation, and emergency procedure evidence.",
        "verify": "Run Admin OpSec/Permission Map review and confirm evidence links are stored.",
    },
    {
        "id": "report",
        "label": "Report verification",
        "required": True,
        "scan_keywords": ["report"],
        "missing_action": "Generate and verify a report hash before sharing launch-readiness results.",
        "verify": "Open /report/verify and confirm report_id/report_hash integrity.",
    },
    {
        "id": "provider",
        "label": "Provider readiness",
        "required": False,
        "scan_keywords": ["provider", "etherscan", "goplus", "engine"],
        "missing_action": "Configure optional providers or keep status as Needs API Key / Provider Not Configured.",
        "verify": "Open /provider-readiness and /engine-depth to confirm honest provider/tool states.",
    },
    {
        "id": "monitoring",
        "label": "Sentinel monitoring",
        "required": False,
        "scan_keywords": ["sentinel", "monitoring", "threat", "intel"],
        "missing_action": "Enable project monitoring by saving project scans/reports and ingesting public advisories where authorized.",
        "verify": "Open /sentinel/project/{id} or /sentinel and confirm alerts are derived from stored records only.",
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


def _score_to_severity(score: Any, critical_high: int = 0, risk_label: str | None = None) -> str:
    label = (risk_label or "").lower()
    if critical_high > 0 or "critical" in label:
        return "critical"
    if "high" in label:
        return "high"
    if isinstance(score, (int, float)):
        if score < 40:
            return "critical"
        if score < 60:
            return "high"
        if score < 75:
            return "medium"
        return "low"
    if "manual" in label or "evidence" in label:
        return "medium"
    return "info"


def _priority_from_severity(severity: str) -> str:
    return {
        "critical": "P0 launch blocker",
        "high": "P1 fix before launch",
        "medium": "P2 evidence needed",
        "low": "P3 hardening",
        "info": "P4 informational",
    }.get(severity, "P4 informational")


def _module_for_scan(module_name: str, payload_text: str) -> str | None:
    haystack = f"{module_name} {payload_text}".lower()
    for module in MODULES:
        if any(keyword in haystack for keyword in module["scan_keywords"]):
            return module["id"]
    return None


def _ledger_entry(kind: str, title: str, source: str, payload: dict[str, Any], project_id: str | None = None, module: str | None = None) -> dict[str, Any]:
    evidence_hash = _sha({"kind": kind, "title": title, "source": source, "payload": payload})
    return {
        "id": f"eon_evd_{evidence_hash[:16]}",
        "kind": kind,
        "title": title,
        "source": source,
        "project_id": project_id,
        "module": module,
        "evidence_hash": evidence_hash,
        "captured_at": payload.get("created_at") or payload.get("updated_at") or _now(),
        "summary": payload,
        "integrity_note": "Hash proves this evidence entry payload was captured by EON; it does not prove the project is secure or audited.",
    }


def _collect(user_id: str, project_id: str | None = None) -> dict[str, Any]:
    projects = [p for p in list_projects(user_id, limit=100) if not project_id or p.id == project_id]
    scans = list_scans(user_id, limit=200, project_id=project_id)
    reports = list_reports(user_id, limit=200, project_id=project_id)
    alerts_payload = build_project_alerts(user_id=user_id, project_id=project_id)
    alerts = alerts_payload.get("alerts", []) if isinstance(alerts_payload, dict) else []
    intel = list_intelligence(limit=25)
    advisories = intel.get("items", []) if isinstance(intel, dict) else []
    patterns = intel.get("patterns", []) if isinstance(intel, dict) else []
    return {
        "projects": projects,
        "scans": scans,
        "reports": reports,
        "alerts": alerts,
        "advisories": advisories,
        "patterns": patterns,
    }


def evidence_ledger(user_id: str, project_id: str | None = None) -> dict[str, Any]:
    data = _collect(user_id, project_id)
    entries: list[dict[str, Any]] = []

    for project in data["projects"]:
        payload = _obj_dump(project)
        entries.append(_ledger_entry("project", f"Project record: {project.name}", "stored_project_record", payload, project.id, "project"))

    for scan in data["scans"]:
        payload = _obj_dump(scan)
        module = _module_for_scan(str(getattr(scan, "module", "scan")), _dump(payload)) or "scan"
        title = f"{getattr(scan, 'module', 'scan')} scan · {getattr(scan, 'score', None) if getattr(scan, 'score', None) is not None else 'Not scored'}"
        entries.append(_ledger_entry("scan", title, "stored_scan_history", payload, getattr(scan, "project_id", None), module))

    for report in data["reports"]:
        payload = _obj_dump(report)
        title = f"Saved report: {getattr(report, 'title', 'Untitled report')}"
        entries.append(_ledger_entry("report", title, "stored_saved_report", payload, getattr(report, "project_id", None), "report"))

    for alert in data["alerts"]:
        if isinstance(alert, dict):
            entries.append(_ledger_entry("sentinel_alert", alert.get("title", "Sentinel alert"), "derived_sentinel_alert", alert, alert.get("project_id"), alert.get("type")))

    for advisory in data["advisories"][:20]:
        if isinstance(advisory, dict):
            entries.append(_ledger_entry("indexed_public_advisory", advisory.get("title", "Indexed advisory"), advisory.get("source", "sentinel_intelligence"), advisory, None, "intelligence"))

    entries.sort(key=lambda item: str(item.get("captured_at", "")), reverse=True)
    return {
        "ok": True,
        "user_id": user_id,
        "project_id": project_id,
        "entries": entries[:150],
        "counts": Counter(entry["kind"] for entry in entries),
        "real_only_note": EON_REAL_ONLY_NOTE,
    }


def build_risk_graph(user_id: str, project_id: str | None = None) -> dict[str, Any]:
    data = _collect(user_id, project_id)
    projects = data["projects"]
    scans = data["scans"]
    reports = data["reports"]
    alerts = data["alerts"]
    ledger = evidence_ledger(user_id, project_id).get("entries", [])

    root_id = project_id or (projects[0].id if len(projects) == 1 else "portfolio")
    root_label = projects[0].name if len(projects) == 1 else "Project portfolio"
    nodes: list[dict[str, Any]] = [
        {
            "id": root_id,
            "label": root_label,
            "type": "root",
            "status": "active" if projects else "no_project_record",
            "severity": "info" if projects else "medium",
            "confidence": 40 if projects else 0,
            "evidence_count": len([entry for entry in ledger if entry.get("kind") == "project"]),
            "last_checked_at": _now(),
            "next_action": "Select a project or save one from the dashboard." if not projects else "Review module nodes and close launch blockers.",
        }
    ]
    edges: list[dict[str, Any]] = []
    blockers: list[dict[str, Any]] = []

    scans_by_module: dict[str, list[Any]] = {module["id"]: [] for module in MODULES}
    for scan in scans:
        payload = _obj_dump(scan)
        module_id = _module_for_scan(str(getattr(scan, "module", "")), _dump(payload))
        if module_id:
            scans_by_module.setdefault(module_id, []).append(scan)

    report_count = len(reports)
    if report_count:
        scans_by_module.setdefault("report", []).extend(reports)

    alert_counter = Counter(str(alert.get("severity") or "info") for alert in alerts if isinstance(alert, dict))

    for module in MODULES:
        module_scans = scans_by_module.get(module["id"], [])
        module_ledger = [entry for entry in ledger if entry.get("module") == module["id"]]
        module_alerts = [alert for alert in alerts if isinstance(alert, dict) and (module["id"] in _dump(alert).lower() or any(keyword in _dump(alert).lower() for keyword in module["scan_keywords"]))]
        assessed = bool(module_scans or module_ledger or module_alerts)
        scores = [getattr(item, "score", None) for item in module_scans if hasattr(item, "score") and getattr(item, "score", None) is not None]
        critical_high = sum(int(getattr(item, "critical_high_count", 0) or 0) for item in module_scans if hasattr(item, "critical_high_count"))
        latest = module_scans[0] if module_scans else None
        severity = "info"
        confidence = 0
        if assessed:
            score = round(sum(scores) / len(scores)) if scores else None
            severity = _score_to_severity(score, critical_high, getattr(latest, "risk_label", None) if latest else None)
            confidence = int(score) if isinstance(score, int) else (65 if module["id"] == "report" and report_count else 50)
        elif module["required"]:
            severity = "high"
            confidence = 0
        else:
            severity = "info"
            confidence = 0

        status = "Assessed" if assessed else ("Not Assessed" if module["required"] else "Optional / Not Assessed")
        last_checked = None
        if latest is not None:
            last_checked = getattr(latest, "created_at", None)
        elif module_ledger:
            last_checked = module_ledger[0].get("captured_at")

        node = {
            "id": module["id"],
            "label": module["label"],
            "type": "module",
            "required": module["required"],
            "status": status,
            "severity": severity,
            "confidence": confidence,
            "evidence_count": len(module_ledger) + len(module_scans),
            "alert_count": len(module_alerts),
            "last_checked_at": last_checked or "Not checked",
            "next_action": module["missing_action"] if not assessed else ("Review critical/high findings." if severity in {"critical", "high"} else "Keep evidence fresh and re-run before launch."),
            "verify": module["verify"],
        }
        nodes.append(node)
        edges.append({"from": root_id, "to": module["id"], "label": "requires evidence" if module["required"] else "optional evidence"})
        if node["severity"] in {"critical", "high"} or (node["required"] and node["status"] == "Not Assessed"):
            blockers.append({
                "module": module["id"],
                "title": node["label"],
                "severity": node["severity"],
                "reason": node["next_action"],
                "verify": node["verify"],
            })

    if alert_counter.get("critical") or alert_counter.get("high"):
        blockers.append({
            "module": "sentinel",
            "title": "Sentinel alert queue has high-priority items",
            "severity": "critical" if alert_counter.get("critical") else "high",
            "reason": "Review project monitoring alerts derived from stored scans/reports and indexed advisories.",
            "verify": "Open /sentinel and close alerts with real evidence only.",
        })

    severity_rank = {"critical": 5, "high": 4, "medium": 3, "low": 2, "info": 1}
    blockers.sort(key=lambda item: severity_rank.get(item["severity"], 0), reverse=True)
    assessed_nodes = [node for node in nodes if node.get("type") == "module" and node.get("status") == "Assessed"]
    required_nodes = [node for node in nodes if node.get("type") == "module" and node.get("required")]
    coverage = round((len([node for node in required_nodes if node.get("status") == "Assessed"]) / len(required_nodes)) * 100) if required_nodes else 0
    confidence_values = [node["confidence"] for node in assessed_nodes if isinstance(node.get("confidence"), int)]
    overall_confidence = round(sum(confidence_values) / len(confidence_values)) if confidence_values else 0
    if blockers:
        overall_confidence = min(overall_confidence, 59 if any(item["severity"] == "critical" for item in blockers) else 74)

    return {
        "ok": True,
        "user_id": user_id,
        "project_id": project_id,
        "generated_at": _now(),
        "summary": {
            "project_count": len(projects),
            "scan_count": len(scans),
            "report_count": len(reports),
            "sentinel_alert_count": len(alerts),
            "required_evidence_coverage": coverage,
            "overall_launch_confidence": overall_confidence,
            "launch_blockers": len(blockers),
        },
        "nodes": nodes,
        "edges": edges,
        "launch_blockers": blockers[:30],
        "next_best_action": blockers[0] if blockers else {
            "module": "monitoring",
            "title": "Keep evidence fresh",
            "severity": "low",
            "reason": "No launch blockers were derived from stored records. Re-run scans before sharing claims.",
            "verify": "Re-run scanner and report verification after any code or website change.",
        },
        "safe_boundary": EON_SAFE_BOUNDARY,
        "real_only_note": EON_REAL_ONLY_NOTE,
    }


def build_fix_plan(user_id: str, project_id: str | None = None) -> dict[str, Any]:
    graph = build_risk_graph(user_id, project_id)
    data = _collect(user_id, project_id)
    tasks: list[dict[str, Any]] = []

    for idx, blocker in enumerate(graph.get("launch_blockers", []), start=1):
        severity = blocker.get("severity", "medium")
        tasks.append({
            "id": f"eon_task_blocker_{idx}",
            "module": blocker.get("module"),
            "title": blocker.get("title"),
            "priority": _priority_from_severity(severity),
            "severity": severity,
            "action": blocker.get("reason"),
            "verify": blocker.get("verify"),
            "status": "open",
            "evidence_required": True,
            "owner_suggestion": "Founder / security lead",
            "safe_boundary": EON_SAFE_BOUNDARY,
        })

    for alert in data["alerts"][:25]:
        if not isinstance(alert, dict):
            continue
        severity = str(alert.get("severity") or "medium")
        tasks.append({
            "id": f"eon_task_alert_{len(tasks)+1}",
            "module": alert.get("type", "sentinel"),
            "title": alert.get("title", "Sentinel alert follow-up"),
            "priority": _priority_from_severity(severity),
            "severity": severity,
            "action": alert.get("detail", "Review Sentinel alert with real evidence."),
            "verify": "Close only after new scan/report/evidence proves the issue is resolved or accepted as risk.",
            "status": alert.get("status", "open"),
            "evidence_required": True,
            "owner_suggestion": "Security reviewer / founder",
            "safe_boundary": EON_SAFE_BOUNDARY,
        })

    seen = set()
    unique: list[dict[str, Any]] = []
    for task in tasks:
        key = (task.get("module"), task.get("title"), task.get("action"))
        if key in seen:
            continue
        seen.add(key)
        unique.append(task)

    unique.sort(key=lambda item: {"P0": 5, "P1": 4, "P2": 3, "P3": 2, "P4": 1}.get(str(item.get("priority", "P4"))[:2], 0), reverse=True)

    return {
        "ok": True,
        "user_id": user_id,
        "project_id": project_id,
        "tasks": unique[:60],
        "counts": Counter(str(task.get("priority", "P4 informational")) for task in unique),
        "next_best_action": graph.get("next_best_action"),
        "workflow_note": "Tasks are generated from existing records and alerts. Marking a task fixed should require new evidence, not manual optimism.",
        "real_only_note": EON_REAL_ONLY_NOTE,
    }


def eon_status() -> dict[str, Any]:
    return {
        "ok": True,
        "phase": "Phase 16 - EON Risk Graph + Autonomous Fix Plan",
        "version": "1.0",
        "modules": [module["id"] for module in MODULES],
        "capabilities": [
            "project risk graph",
            "launch blocker extraction",
            "next-best-action selection",
            "autonomous defensive fix plan",
            "evidence ledger hashing",
            "Sentinel alert integration",
        ],
        "blocked_capabilities": [
            "certified audit claim",
            "100% secure claim",
            "exploit automation",
            "private key or seed phrase collection",
            "wallet signing",
            "fake evidence generation",
        ],
        "real_only_note": EON_REAL_ONLY_NOTE,
        "safe_boundary": EON_SAFE_BOUNDARY,
    }
