from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

from app.services.database_store import (
    PHASE7_REAL_ONLY_NOTE,
    get_project,
    list_projects,
    list_reports,
    list_scans,
    project_detail,
)

WORKFLOW_NOTE = (
    "Dashboard workflow is generated only from real saved projects, scans, and reports owned by the resolved user. "
    "Empty arrays mean no stored records yet; no fake timeline, trend, finding task, or report status is generated."
)


def _dt(value: Any) -> str:
    try:
        return value.isoformat() if hasattr(value, "isoformat") else str(value)
    except Exception:
        return ""


def _score_bucket(score: int | None) -> str:
    if score is None:
        return "not_assessed"
    if score < 40:
        return "critical"
    if score < 60:
        return "high_attention"
    if score < 80:
        return "evidence_needed"
    return "stronger"


def _safe_payload(scan: Any) -> dict[str, Any]:
    payload = getattr(scan, "payload", None)
    return payload if isinstance(payload, dict) else {}


def _collect_findings_from_value(value: Any) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    if isinstance(value, dict):
        for key, nested in value.items():
            if key in {"findings", "issues", "risks"} and isinstance(nested, list):
                for item in nested:
                    if isinstance(item, dict):
                        title = item.get("title") or item.get("name") or item.get("rule") or item.get("id")
                        if title:
                            findings.append(item)
            else:
                findings.extend(_collect_findings_from_value(nested))
    elif isinstance(value, list):
        for item in value:
            findings.extend(_collect_findings_from_value(item))
    return findings


def _finding_title(finding: dict[str, Any], index: int) -> str:
    for key in ("title", "name", "rule", "id", "check"):
        raw = finding.get(key)
        if isinstance(raw, str) and raw.strip():
            return raw.strip()[:180]
    return f"Finding {index + 1}"


def _finding_severity(finding: dict[str, Any]) -> str:
    raw = finding.get("severity") or finding.get("risk") or finding.get("level") or "info"
    if not isinstance(raw, str):
        return "info"
    clean = raw.lower().replace(" ", "_")
    if clean in {"critical", "high", "medium", "low", "info", "informational"}:
        return "info" if clean == "informational" else clean
    return "info"


def _finding_recommendation(finding: dict[str, Any]) -> str | None:
    for key in ("recommendation", "fix", "fix_hint", "safe_fix_direction", "how_to_fix"):
        raw = finding.get(key)
        if isinstance(raw, str) and raw.strip():
            return raw.strip()[:260]
    return None


def _timeline(projects: list[Any], scans: list[Any], reports: list[Any]) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for project in projects:
        events.append({
            "id": getattr(project, "id", ""),
            "type": "project",
            "title": f"Project saved: {getattr(project, 'name', 'Unnamed project')}",
            "subtitle": getattr(project, "website_url", None) or getattr(project, "chain", None) or "Project record created",
            "created_at": _dt(getattr(project, "created_at", "")),
            "project_id": getattr(project, "id", None),
            "href": f"/dashboard/projects/{getattr(project, 'id', '')}",
        })
    for scan in scans:
        events.append({
            "id": getattr(scan, "id", ""),
            "type": "scan",
            "title": f"{getattr(scan, 'module', 'scan')} scan saved",
            "subtitle": f"{getattr(scan, 'risk_label', None) or 'No risk label'} · {getattr(scan, 'findings_count', 0)} finding(s)",
            "created_at": _dt(getattr(scan, "created_at", "")),
            "project_id": getattr(scan, "project_id", None),
            "href": f"/dashboard/scans/{getattr(scan, 'id', '')}",
        })
    for report in reports:
        events.append({
            "id": getattr(report, "id", ""),
            "type": "report",
            "title": f"Report saved: {getattr(report, 'title', 'Untitled report')}",
            "subtitle": f"{getattr(report, 'risk_label', None) or 'No risk label'} · {getattr(report, 'visibility', 'private')}",
            "created_at": _dt(getattr(report, "created_at", "")),
            "project_id": getattr(report, "project_id", None),
            "href": f"/dashboard/reports/{getattr(report, 'id', '')}",
        })
    events.sort(key=lambda item: item.get("created_at") or "", reverse=True)
    return events[:50]


def _trend(scans: list[Any]) -> list[dict[str, Any]]:
    scored = [scan for scan in scans if isinstance(getattr(scan, "score", None), int)]
    scored.sort(key=lambda scan: _dt(getattr(scan, "created_at", "")))
    return [
        {
            "scan_id": getattr(scan, "id", ""),
            "created_at": _dt(getattr(scan, "created_at", "")),
            "module": getattr(scan, "module", "scan"),
            "score": getattr(scan, "score", None),
            "bucket": _score_bucket(getattr(scan, "score", None)),
            "risk_label": getattr(scan, "risk_label", None) or "No risk label",
            "findings_count": getattr(scan, "findings_count", 0),
            "critical_high_count": getattr(scan, "critical_high_count", 0),
            "href": f"/dashboard/scans/{getattr(scan, 'id', '')}",
        }
        for scan in scored[-20:]
    ]


def _module_comparison(scans: list[Any]) -> list[dict[str, Any]]:
    grouped: dict[str, list[Any]] = defaultdict(list)
    for scan in scans:
        grouped[getattr(scan, "module", "scan")].append(scan)

    rows: list[dict[str, Any]] = []
    for module, items in grouped.items():
        items.sort(key=lambda scan: _dt(getattr(scan, "created_at", "")), reverse=True)
        latest = items[0]
        scores = [getattr(scan, "score", None) for scan in items if isinstance(getattr(scan, "score", None), int)]
        rows.append({
            "module": module,
            "scans_count": len(items),
            "latest_scan_id": getattr(latest, "id", ""),
            "latest_score": getattr(latest, "score", None),
            "average_score": round(sum(scores) / len(scores)) if scores else None,
            "latest_risk_label": getattr(latest, "risk_label", None) or "No risk label",
            "findings_count": sum(getattr(scan, "findings_count", 0) for scan in items),
            "critical_high_count": sum(getattr(scan, "critical_high_count", 0) for scan in items),
            "last_seen_at": _dt(getattr(latest, "created_at", "")),
            "href": f"/dashboard/scans/{getattr(latest, 'id', '')}",
        })
    rows.sort(key=lambda item: (item["critical_high_count"], item["findings_count"], item["last_seen_at"]), reverse=True)
    return rows


def _finding_workflow(scans: list[Any], reports: list[Any]) -> dict[str, Any]:
    tasks: list[dict[str, Any]] = []
    status_counter = Counter()
    severity_counter = Counter()

    for scan in scans:
        payload = _safe_payload(scan)
        findings = _collect_findings_from_value(payload)
        for index, finding in enumerate(findings[:10]):
            severity = _finding_severity(finding)
            status = getattr(scan, "status", None) or "open"
            status_counter[status] += 1
            severity_counter[severity] += 1
            tasks.append({
                "id": f"{getattr(scan, 'id', 'scan')}-{index}",
                "scan_id": getattr(scan, "id", None),
                "project_id": getattr(scan, "project_id", None),
                "module": getattr(scan, "module", "scan"),
                "title": _finding_title(finding, index),
                "severity": severity,
                "status": status,
                "recommendation": _finding_recommendation(finding),
                "created_at": _dt(getattr(scan, "created_at", "")),
                "href": f"/dashboard/scans/{getattr(scan, 'id', '')}",
            })

    for report in reports:
        payload = getattr(report, "payload", None) if isinstance(getattr(report, "payload", None), dict) else {}
        findings = _collect_findings_from_value(payload)
        for index, finding in enumerate(findings[:6]):
            severity = _finding_severity(finding)
            status = getattr(report, "status", None) or "saved"
            status_counter[status] += 1
            severity_counter[severity] += 1
            tasks.append({
                "id": f"{getattr(report, 'id', 'report')}-{index}",
                "report_id": getattr(report, "id", None),
                "project_id": getattr(report, "project_id", None),
                "module": "report",
                "title": _finding_title(finding, index),
                "severity": severity,
                "status": status,
                "recommendation": _finding_recommendation(finding),
                "created_at": _dt(getattr(report, "created_at", "")),
                "href": f"/dashboard/reports/{getattr(report, 'id', '')}",
            })

    tasks.sort(key=lambda item: (item.get("severity") in {"critical", "high"}, item.get("created_at") or ""), reverse=True)
    return {
        "tasks": tasks[:25],
        "status_breakdown": dict(status_counter),
        "severity_breakdown": dict(severity_counter),
        "note": "Finding workflow is derived only from actual saved scan/report payload findings. If no payload findings are present, task list remains empty.",
    }


def _project_health(projects: list[Any], scans: list[Any], reports: list[Any]) -> list[dict[str, Any]]:
    scans_by_project: dict[str | None, list[Any]] = defaultdict(list)
    reports_by_project: dict[str | None, list[Any]] = defaultdict(list)
    for scan in scans:
        scans_by_project[getattr(scan, "project_id", None)].append(scan)
    for report in reports:
        reports_by_project[getattr(report, "project_id", None)].append(report)

    rows: list[dict[str, Any]] = []
    for project in projects:
        project_id = getattr(project, "id", None)
        p_scans = scans_by_project.get(project_id, [])
        p_reports = reports_by_project.get(project_id, [])
        scored = [getattr(scan, "score", None) for scan in p_scans if isinstance(getattr(scan, "score", None), int)]
        latest_scan = sorted(p_scans, key=lambda scan: _dt(getattr(scan, "created_at", "")), reverse=True)[0] if p_scans else None
        rows.append({
            "project_id": project_id,
            "name": getattr(project, "name", "Unnamed project"),
            "website_url": getattr(project, "website_url", None),
            "chain": getattr(project, "chain", None),
            "scans_count": len(p_scans),
            "reports_count": len(p_reports),
            "average_score": round(sum(scored) / len(scored)) if scored else None,
            "critical_high_count": sum(getattr(scan, "critical_high_count", 0) for scan in p_scans),
            "latest_scan_at": _dt(getattr(latest_scan, "created_at", "")) if latest_scan else None,
            "latest_risk_label": getattr(latest_scan, "risk_label", None) if latest_scan else "No scan yet",
            "href": f"/dashboard/projects/{project_id}",
        })
    rows.sort(key=lambda item: (item["critical_high_count"], item["scans_count"], item.get("latest_scan_at") or ""), reverse=True)
    return rows


def build_dashboard_workflow(user_id: str, project_id: str | None = None) -> dict[str, Any] | None:
    if project_id:
        detail = project_detail(user_id, project_id)
        if detail is None:
            return None
        projects = [detail.project]
        scans = detail.scans
        reports = detail.reports
        scope = {"mode": "project", "project_id": project_id, "project_name": detail.project.name}
    else:
        projects = list_projects(user_id, limit=100)
        scans = list_scans(user_id, limit=200)
        reports = list_reports(user_id, limit=200)
        scope = {"mode": "workspace", "project_id": None, "project_name": None}

    scored = [getattr(scan, "score", None) for scan in scans if isinstance(getattr(scan, "score", None), int)]
    critical_high = sum(getattr(scan, "critical_high_count", 0) for scan in scans)
    findings_count = sum(getattr(scan, "findings_count", 0) for scan in scans)
    open_records = sum(1 for scan in scans if (getattr(scan, "status", "saved") or "saved") not in {"fixed", "closed", "accepted_risk"})

    return {
        "ok": True,
        "scope": scope,
        "summary": {
            "projects": len(projects),
            "scans": len(scans),
            "reports": len(reports),
            "findings_count": findings_count,
            "critical_high_count": critical_high,
            "average_score": round(sum(scored) / len(scored)) if scored else None,
            "open_scan_records": open_records,
            "score_bucket": _score_bucket(round(sum(scored) / len(scored)) if scored else None),
        },
        "timeline": _timeline(projects, scans, reports),
        "risk_trend": _trend(scans),
        "module_comparison": _module_comparison(scans),
        "project_health": _project_health(projects, scans, reports),
        "finding_workflow": _finding_workflow(scans, reports),
        "real_only_note": WORKFLOW_NOTE,
        "storage_note": PHASE7_REAL_ONLY_NOTE,
    }
