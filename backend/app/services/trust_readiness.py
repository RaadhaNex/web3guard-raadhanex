from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from typing import Any

from app.services.continuous_monitoring import user_dashboard
from app.services.database_store import list_projects, list_reports, list_scans
from app.services.eon import build_fix_plan, build_risk_graph, evidence_ledger
from app.services.public_trust_page import MODULE_CATALOG, build_public_trust_page
from app.services.sentinel import build_project_alerts

TRUST_READINESS_NOTE = (
    "Launch Trust Readiness is a pre-audit readiness score generated from stored Web3Guard records, evidence, reports, "
    "monitoring state, Sentinel alerts, and workflow tasks. It is not a certified audit score, not a guarantee of safety, "
    "and must not be described as proof that a project is secure. Not Assessed modules reduce readiness instead of being hidden."
)

TRUST_READINESS_BLOCKED_WORDING = [
    "audited by Web3Guard",
    "certified secure",
    "100% secure",
    "guaranteed safe",
    "exploit-free",
    "fully verified unless a real external audit exists",
]

COMPONENTS = [
    {
        "id": "evidence_completeness",
        "label": "Evidence completeness",
        "weight": 18,
        "description": "How much required launch evidence exists across website, contract, admin, reports, and related modules.",
    },
    {
        "id": "fix_completion",
        "label": "Fix completion",
        "weight": 16,
        "description": "How many EON launch blockers and fix-plan tasks remain open or require evidence.",
    },
    {
        "id": "public_transparency",
        "label": "Public transparency",
        "weight": 12,
        "description": "Whether a project has a public trust-page style summary, report hash, limitations, and responsible disclosure path.",
    },
    {
        "id": "wallet_safety",
        "label": "Wallet / token safety",
        "weight": 10,
        "description": "Wallet, token, approvals, GoPlus/provider readiness, and user-risk explanation coverage.",
    },
    {
        "id": "github_hygiene",
        "label": "GitHub hygiene",
        "weight": 10,
        "description": "Repository hygiene evidence including security policy, CI/tests, lockfiles, and dependency posture.",
    },
    {
        "id": "admin_opsec",
        "label": "Admin OpSec",
        "weight": 12,
        "description": "MFA, multisig/timelock, role separation, signer/treasury evidence, and incident response readiness.",
    },
    {
        "id": "report_verification",
        "label": "Report verification",
        "weight": 8,
        "description": "Saved report presence, report hash, verification workflow, and evidence ledger integrity references.",
    },
    {
        "id": "monitoring_setup",
        "label": "Monitoring setup",
        "weight": 8,
        "description": "Continuous Monitoring Lite configuration, stale report/scan state, and Sentinel alert visibility.",
    },
    {
        "id": "bounty_readiness",
        "label": "Bug bounty readiness",
        "weight": 6,
        "description": "Responsible disclosure, bug bounty scope, triage readiness, and public contact flow.",
    },
]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _contains(value: Any, *needles: str) -> bool:
    text = str(value).lower()
    return any(needle.lower() in text for needle in needles)


def _clamp(value: int | float) -> int:
    return max(0, min(100, int(round(value))))


def _count_status(rows: list[dict[str, Any]], *statuses: str) -> int:
    wanted = {status.lower() for status in statuses}
    return sum(1 for row in rows if str(row.get("status", "")).lower() in wanted or str(row.get("public_label", "")).lower() in wanted)


def _safe_public_trust(user_id: str, project_id: str) -> dict[str, Any] | None:
    try:
        return build_public_trust_page(user_id=user_id, project_id=project_id)
    except Exception:
        return None


def _safe_monitoring(user_id: str) -> dict[str, Any]:
    try:
        return user_dashboard(user_id=user_id)
    except Exception as exc:
        return {"ok": False, "configs": [], "alerts": [], "error": str(exc)}


def _safe_alerts(user_id: str, project_id: str | None) -> dict[str, Any]:
    try:
        return build_project_alerts(user_id=user_id, project_id=project_id)
    except Exception as exc:
        return {"ok": False, "alerts": [], "error": str(exc)}


def _safe_graph(user_id: str, project_id: str | None) -> dict[str, Any]:
    try:
        return build_risk_graph(user_id=user_id, project_id=project_id)
    except Exception as exc:
        return {"ok": False, "summary": {}, "nodes": [], "launch_blockers": [], "error": str(exc)}


def _safe_fix_plan(user_id: str, project_id: str | None) -> dict[str, Any]:
    try:
        return build_fix_plan(user_id=user_id, project_id=project_id)
    except Exception as exc:
        return {"ok": False, "tasks": [], "counts": {}, "error": str(exc)}


def _safe_ledger(user_id: str, project_id: str | None) -> dict[str, Any]:
    try:
        return evidence_ledger(user_id=user_id, project_id=project_id)
    except Exception as exc:
        return {"ok": False, "entries": [], "error": str(exc)}


def _component_score(component_id: str, context: dict[str, Any]) -> dict[str, Any]:
    scans = context["scans"]
    reports = context["reports"]
    trust_page = context.get("trust_page") or {}
    graph = context["graph"]
    fix_plan = context["fix_plan"]
    ledger = context["ledger"]
    monitoring = context["monitoring"]
    alerts = context["alerts"].get("alerts", []) if isinstance(context.get("alerts"), dict) else []

    module_rows = trust_page.get("module_statuses") or trust_page.get("modules") or []
    if not isinstance(module_rows, list):
        module_rows = []

    tasks = fix_plan.get("tasks", []) if isinstance(fix_plan, dict) else []
    nodes = graph.get("nodes", []) if isinstance(graph, dict) else []
    blockers = graph.get("launch_blockers", []) if isinstance(graph, dict) else []
    ledger_entries = ledger.get("entries", []) if isinstance(ledger, dict) else []
    configs = monitoring.get("configs", []) if isinstance(monitoring, dict) else []
    monitoring_alerts = monitoring.get("alerts", []) if isinstance(monitoring, dict) else []

    evidence = 0
    maximum = 1
    status = "not_assessed"
    reasons: list[str] = []
    actions: list[str] = []

    if component_id == "evidence_completeness":
        required_rows = [row for row in module_rows if row.get("required_for_public_launch") or row.get("required")]
        assessed = [row for row in required_rows if str(row.get("status", "")).lower() not in {"not_assessed", "optional / not assessed", ""}]
        maximum = max(1, len(required_rows) or len(MODULE_CATALOG))
        evidence = len(assessed)
        score = (evidence / maximum) * 100
        reasons.append(f"{evidence}/{maximum} required evidence module(s) have stored assessment evidence.")
        if score < 100:
            actions.append("Add evidence for required Not Assessed modules before using public trust wording.")
    elif component_id == "fix_completion":
        open_tasks = [task for task in tasks if str(task.get("status", "open")).lower() in {"open", "in_progress", "manual_review_required"}]
        critical_blockers = [item for item in blockers if str(item.get("severity", "")).lower() in {"critical", "high"}]
        maximum = max(1, len(tasks) + len(critical_blockers))
        evidence = max(0, maximum - len(open_tasks) - len(critical_blockers))
        score = (evidence / maximum) * 100 if tasks or blockers else 65
        reasons.append(f"{len(open_tasks)} open fix task(s) and {len(critical_blockers)} critical/high blocker(s) are visible.")
        actions.append("Close fix tasks only with new scan/report/evidence; never mark fixed by optimism.")
    elif component_id == "public_transparency":
        has_report = bool(reports)
        has_hash = any(bool(getattr(report, "report_hash", None)) for report in reports)
        has_public = bool(trust_page and trust_page.get("ok"))
        has_disclosure = any(_contains(entry, "disclosure", "security.txt", "responsible") for entry in ledger_entries) or any(_contains(scan, "security.txt") for scan in scans)
        checks = [has_report, has_hash, has_public, has_disclosure]
        evidence = sum(1 for item in checks if item)
        maximum = len(checks)
        score = (evidence / maximum) * 100
        reasons.append(f"{evidence}/{maximum} transparency signal(s) are present: report, hash, trust page, disclosure path.")
        if not has_disclosure:
            actions.append("Add responsible disclosure/security.txt evidence before public launch.")
    elif component_id == "wallet_safety":
        relevant = [node for node in nodes if _contains(node.get("id"), "wallet", "token") or _contains(node.get("label"), "wallet", "token")]
        relevant_scans = [scan for scan in scans if _contains(getattr(scan, "module", ""), "wallet", "token", "goplus", "approval")]
        evidence = len(relevant_scans) + sum(int(node.get("evidence_count") or 0) for node in relevant)
        maximum = max(1, 2)
        score = min(100, evidence * 45)
        reasons.append(f"{evidence} wallet/token evidence signal(s) were found.")
        if evidence == 0:
            actions.append("Run wallet/token/provider readiness checks or add manual wallet UX evidence.")
    elif component_id == "github_hygiene":
        relevant_scans = [scan for scan in scans if _contains(getattr(scan, "module", ""), "github", "repo", "dependency") or _contains(getattr(scan, "payload", {}), "github", "repository", "lockfile", "security.md")]
        evidence = len(relevant_scans)
        maximum = 2
        score = min(100, evidence * 50)
        reasons.append(f"{evidence} GitHub/repository hygiene scan(s) are stored.")
        if evidence == 0:
            actions.append("Run the GitHub scanner and verify SECURITY.md, CI/tests, lockfile, and dependency evidence.")
    elif component_id == "admin_opsec":
        relevant_scans = [scan for scan in scans if _contains(getattr(scan, "module", ""), "admin", "opsec", "permission") or _contains(getattr(scan, "payload", {}), "multisig", "timelock", "owner", "admin")]
        relevant_nodes = [node for node in nodes if _contains(node.get("id"), "admin") or _contains(node.get("label"), "admin", "opsec")]
        evidence = len(relevant_scans) + sum(int(node.get("evidence_count") or 0) for node in relevant_nodes)
        maximum = 2
        score = min(100, evidence * 45)
        reasons.append(f"{evidence} admin/OpSec evidence signal(s) are stored.")
        if evidence == 0:
            actions.append("Add multisig/timelock/MFA/role-separation evidence or run Admin OpSec scanner.")
    elif component_id == "report_verification":
        has_report = bool(reports)
        has_hash = any(bool(getattr(report, "report_hash", None)) for report in reports)
        report_entries = [entry for entry in ledger_entries if str(entry.get("kind", "")).lower() == "report"]
        checks = [has_report, has_hash, bool(report_entries)]
        evidence = sum(1 for item in checks if item)
        maximum = len(checks)
        score = (evidence / maximum) * 100
        reasons.append(f"{evidence}/{maximum} report verification signal(s) are available.")
        if not has_hash:
            actions.append("Generate or save a report with report_id and report_hash before sharing public trust status.")
    elif component_id == "monitoring_setup":
        has_config = bool(configs)
        active_alerts = [alert for alert in [*alerts, *monitoring_alerts] if str(alert.get("severity", "")).lower() in {"critical", "high", "medium"}]
        stale = [alert for alert in [*alerts, *monitoring_alerts] if _contains(alert, "stale", "expired")]
        checks = [has_config, not bool(active_alerts), not bool(stale)]
        evidence = sum(1 for item in checks if item)
        maximum = len(checks)
        score = (evidence / maximum) * 100 if has_config else 20 if reports or scans else 0
        reasons.append(f"Monitoring config present: {has_config}. Active medium+ alert(s): {len(active_alerts)}. Stale alert(s): {len(stale)}.")
        if not has_config:
            actions.append("Create a Continuous Monitoring Lite config for this project.")
    elif component_id == "bounty_readiness":
        relevant = [entry for entry in ledger_entries if _contains(entry, "bounty", "disclosure", "security.txt", "responsible")]
        scan_hits = [scan for scan in scans if _contains(getattr(scan, "payload", {}), "bounty", "disclosure", "security.txt", "security policy")]
        evidence = len(relevant) + len(scan_hits)
        maximum = 2
        score = min(100, evidence * 50)
        reasons.append(f"{evidence} bug-bounty/responsible-disclosure signal(s) are stored.")
        if evidence == 0:
            actions.append("Publish a responsible disclosure path and prepare bounty scope/triage rules before public programs.")
    else:
        score = 0

    score = _clamp(score)
    if score >= 80:
        status = "strong"
    elif score >= 60:
        status = "improving"
    elif score >= 35:
        status = "needs_evidence"
    else:
        status = "not_ready"

    return {
        "id": component_id,
        "score": score,
        "status": status,
        "evidence_count": evidence,
        "max_evidence": maximum,
        "reasons": reasons,
        "next_actions": actions[:3],
    }


def _weighted_score(components: list[dict[str, Any]]) -> int:
    by_id = {item["id"]: item for item in components}
    total_weight = sum(component["weight"] for component in COMPONENTS)
    total = 0
    for component in COMPONENTS:
        total += int(by_id.get(component["id"], {}).get("score", 0)) * component["weight"]
    return _clamp(total / max(1, total_weight))


def _label(score: int, critical_blockers: int, not_ready_count: int) -> str:
    if critical_blockers > 0:
        return "Blocked: fix critical launch risks"
    if score >= 85 and not_ready_count == 0:
        return "Strong pre-audit readiness"
    if score >= 70:
        return "Launch-ready with evidence review"
    if score >= 50:
        return "Evidence needed before launch"
    if score >= 30:
        return "Early readiness: major gaps remain"
    return "Not ready for public trust claims"


def build_trust_readiness(user_id: str, project_id: str | None = None) -> dict[str, Any]:
    projects = [project for project in list_projects(user_id, limit=100) if not project_id or project.id == project_id]
    selected_project_id = project_id or (projects[0].id if len(projects) == 1 else None)
    scans = list_scans(user_id, limit=250, project_id=selected_project_id)
    reports = list_reports(user_id, limit=250, project_id=selected_project_id)
    trust_page = _safe_public_trust(user_id, selected_project_id) if selected_project_id else None
    graph = _safe_graph(user_id, selected_project_id)
    fix_plan = _safe_fix_plan(user_id, selected_project_id)
    ledger = _safe_ledger(user_id, selected_project_id)
    monitoring = _safe_monitoring(user_id)
    alerts = _safe_alerts(user_id, selected_project_id)

    context = {
        "projects": projects,
        "scans": scans,
        "reports": reports,
        "trust_page": trust_page,
        "graph": graph,
        "fix_plan": fix_plan,
        "ledger": ledger,
        "monitoring": monitoring,
        "alerts": alerts,
    }

    component_scores = []
    for component in COMPONENTS:
        score = _component_score(component["id"], context)
        component_scores.append({**component, **score})

    score = _weighted_score(component_scores)
    critical_blockers = len([item for item in graph.get("launch_blockers", []) if str(item.get("severity", "")).lower() in {"critical", "high"}]) if isinstance(graph, dict) else 0
    not_ready_count = len([item for item in component_scores if item["status"] in {"not_ready", "not_assessed"}])
    label = _label(score, critical_blockers, not_ready_count)

    priority_actions = []
    for item in sorted(component_scores, key=lambda row: row["score"]):
        for action in item.get("next_actions", []):
            priority_actions.append({"component": item["label"], "action": action, "score": item["score"], "status": item["status"]})
    if graph.get("next_best_action"):
        nba = graph["next_best_action"]
        priority_actions.insert(0, {"component": "EON next best action", "action": nba.get("reason") or nba.get("title"), "score": score, "status": nba.get("severity", "info")})

    return {
        "ok": True,
        "phase": "Phase 20 — Founder Trust Score + Launch Trust Readiness",
        "generated_at": _now(),
        "user_id": user_id,
        "project_id": selected_project_id,
        "requested_project_id": project_id,
        "score": score,
        "label": label,
        "score_type": "Launch Trust Readiness — not an audit score",
        "component_scores": component_scores,
        "summary": {
            "project_count": len(projects),
            "scan_count": len(scans),
            "report_count": len(reports),
            "evidence_entries": len(ledger.get("entries", [])) if isinstance(ledger, dict) else 0,
            "sentinel_alerts": len(alerts.get("alerts", [])) if isinstance(alerts, dict) else 0,
            "monitoring_configs": len(monitoring.get("configs", [])) if isinstance(monitoring, dict) else 0,
            "critical_or_high_blockers": critical_blockers,
        },
        "priority_actions": priority_actions[:12],
        "project_options": [
            {"id": project.id, "name": project.name, "website_url": project.website_url, "chain": project.chain, "project_type": project.project_type}
            for project in projects
        ],
        "safe_public_wording": "Launch Trust Readiness reviewed",
        "blocked_wording": TRUST_READINESS_BLOCKED_WORDING,
        "real_only_note": TRUST_READINESS_NOTE,
        "boundaries": [
            "This is a pre-audit readiness score, not a certified audit or security guarantee.",
            "Report hashes prove payload integrity only, not project safety.",
            "Not Assessed modules lower readiness and must remain visible.",
            "No wallet signing, private keys, seed phrases, or exploit automation are part of this feature.",
        ],
    }


def trust_readiness_status() -> dict[str, Any]:
    return {
        "ok": True,
        "phase": "Phase 20 — Founder Trust Score + Launch Trust Readiness",
        "score_type": "readiness_only_not_audit_score",
        "components": COMPONENTS,
        "safe_public_wording": "Launch Trust Readiness reviewed",
        "blocked_wording": TRUST_READINESS_BLOCKED_WORDING,
        "real_only_note": TRUST_READINESS_NOTE,
        "capabilities": [
            "weighted readiness score from stored evidence",
            "component score breakdown",
            "priority action plan",
            "Not Assessed visibility",
            "EON/Sentinel/Monitoring/Public Trust inputs",
        ],
    }
