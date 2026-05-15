from __future__ import annotations

import hashlib
import json
import secrets
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.core.config import settings
from app.models.schemas import ScanHistoryItem
from app.services.database_store import get_project, get_scan, list_projects, list_scans

PHASE10_REAL_ONLY_NOTE = (
    "SecureScore Pro uses only scans/reports explicitly saved by the user. It does not invent fake findings, fake fixes, fake score history, or fake remediation status."
)
FINAL_STATUSES = {"fixed", "false_positive", "accepted_risk"}
SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
MODULE_LABELS = {
    "contract": "Smart Contract",
    "website": "Website Surface",
    "dapp": "dApp Frontend",
    "api": "API Backend",
    "wallet": "Wallet Flow",
    "admin_opsec": "Admin OpSec",
    "unified_url": "Unified URL",
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _path() -> Path:
    path = Path(settings.db_finding_workflow_file)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text("", encoding="utf-8")
    return path


def _read_jsonl(path: Path | None = None) -> list[dict[str, Any]]:
    target = path or _path()
    rows: list[dict[str, Any]] = []
    if not target.exists():
        return rows
    for line in target.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows


def _rewrite_jsonl(rows: list[dict[str, Any]]) -> None:
    path = _path()
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, default=str, ensure_ascii=False) + "\n")


def _new_id(prefix: str) -> str:
    return f"{prefix}_{secrets.token_hex(10)}"


def _hash(value: str, size: int = 16) -> str:
    return hashlib.sha256(value.encode("utf-8", errors="ignore")).hexdigest()[:size]


def _workflow_key(scan_id: str, finding_id: str) -> str:
    return f"{scan_id}:{finding_id}"


def _workflow_rows_for_user(user_id: str) -> dict[str, dict[str, Any]]:
    rows = [row for row in _read_jsonl() if row.get("user_id") == user_id]
    return {row.get("workflow_key", ""): row for row in rows if row.get("workflow_key")}


def _safe_severity(raw: Any) -> str:
    value = str(raw or "info").lower().strip()
    return value if value in SEVERITY_ORDER else "info"


def _extract_payload_findings(scan: ScanHistoryItem) -> list[dict[str, Any]]:
    payload = scan.payload or {}
    candidates: list[Any] = []
    if isinstance(payload.get("findings"), list):
        candidates.extend(payload["findings"])
    combined = payload.get("combined_report") if isinstance(payload.get("combined_report"), dict) else None
    if combined and isinstance(combined.get("top_findings"), list):
        candidates.extend(combined["top_findings"])
    if isinstance(payload.get("top_findings"), list):
        candidates.extend(payload["top_findings"])

    normalized: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, raw in enumerate(candidates):
        if not isinstance(raw, dict):
            continue
        raw_module = raw.get("module") or scan.module or "unknown"
        severity = _safe_severity(raw.get("severity"))
        title = str(raw.get("title") or raw.get("description") or f"Finding {index + 1}").strip()[:240]
        raw_id = raw.get("fingerprint") or raw.get("id") or raw.get("rule_id") or f"{raw_module}:{severity}:{title}:{index}"
        finding_id = str(raw_id)[:160]
        dedupe_key = f"{scan.id}:{finding_id}"
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        normalized.append({
            "id": finding_id,
            "scan_id": scan.id,
            "project_id": scan.project_id,
            "report_id": scan.report_id,
            "module": str(raw_module),
            "module_label": MODULE_LABELS.get(str(raw_module), str(raw_module).replace("_", " ").title()),
            "severity": severity,
            "title": title,
            "description": str(raw.get("description") or "No description saved for this finding.")[:2000],
            "affected_line": raw.get("affected_line"),
            "affected_function": raw.get("affected_function"),
            "confidence": str(raw.get("confidence") or "medium"),
            "source": str(raw.get("source") or "Saved scan payload"),
            "category": str(raw.get("category") or "general"),
            "business_impact": str(raw.get("business_impact") or "Review before launch.")[:2000],
            "recommendation": str(raw.get("recommendation") or raw.get("developer_explanation") or "Review and fix before production launch.")[:2000],
            "paid_review_recommended": bool(raw.get("paid_review_recommended") or severity in {"critical", "high"}),
            "created_at": scan.created_at.isoformat() if hasattr(scan.created_at, "isoformat") else str(scan.created_at),
            "project_name": scan.project_name,
            "risk_label": scan.risk_label,
        })
    return normalized


def _all_findings_for_user(user_id: str, project_id: str | None = None) -> list[dict[str, Any]]:
    scans = list_scans(user_id, limit=500, project_id=project_id)
    workflows = _workflow_rows_for_user(user_id)
    findings: list[dict[str, Any]] = []
    for scan in scans:
        for finding in _extract_payload_findings(scan):
            key = _workflow_key(scan.id, finding["id"])
            workflow = workflows.get(key, {})
            status = workflow.get("status") or "open"
            finding.update({
                "workflow_key": key,
                "workflow_status": status,
                "workflow_notes": workflow.get("notes"),
                "assigned_to": workflow.get("assigned_to"),
                "updated_at": workflow.get("updated_at"),
                "is_open": status not in FINAL_STATUSES,
            })
            findings.append(finding)
    findings.sort(key=lambda item: (SEVERITY_ORDER.get(item["severity"], 9), item.get("created_at", "")))
    return findings


def _risk_bucket(score: int | None) -> str:
    if score is None:
        return "not_scored"
    if score >= 90:
        return "launch_ready"
    if score >= 75:
        return "low_risk"
    if score >= 60:
        return "medium_risk"
    if score >= 40:
        return "high_risk"
    return "critical_risk"


def _score_label(score: int | None) -> str:
    return {
        "launch_ready": "Launch Ready with Minor Notes",
        "low_risk": "Low Risk, Fix Recommended",
        "medium_risk": "Medium Risk, Fix Before Launch",
        "high_risk": "High Risk, Manual Review Recommended",
        "critical_risk": "Critical Launch Risk",
        "not_scored": "Not scored",
    }[_risk_bucket(score)]


def _module_scorecards(scans: list[ScanHistoryItem]) -> list[dict[str, Any]]:
    grouped: dict[str, list[ScanHistoryItem]] = defaultdict(list)
    for scan in scans:
        grouped[scan.module].append(scan)
    cards: list[dict[str, Any]] = []
    for module, rows in sorted(grouped.items()):
        scored = [row.score for row in rows if row.score is not None]
        latest = sorted(rows, key=lambda row: row.created_at, reverse=True)[0]
        avg_score = round(sum(scored) / len(scored)) if scored else None
        cards.append({
            "module": module,
            "label": MODULE_LABELS.get(module, module.replace("_", " ").title()),
            "average_score": avg_score,
            "latest_score": latest.score,
            "risk_label": latest.risk_label or _score_label(latest.score),
            "scans_count": len(rows),
            "findings_count": sum(row.findings_count for row in rows),
            "critical_high_count": sum(row.critical_high_count for row in rows),
            "latest_scan_id": latest.id,
        })
    return cards


def securescore_status() -> dict[str, Any]:
    path = _path()
    return {
        "ok": True,
        "phase": "Phase 10 - SecureScore Pro Dashboard + Findings Workflow",
        "workflow_storage_file": str(path),
        "workflow_records": len(_read_jsonl(path)),
        "live_features": [
            "Saved-scan SecureScore overview",
            "Severity breakdown from real saved findings",
            "Module scorecards from real scan history",
            "Finding workflow status updates",
            "Score trend from saved scans",
        ],
        "manual_or_not_enabled": [
            "Automatic code patching is not enabled",
            "Finding status is changed by user/reviewer action",
            "AI fixes require Phase 15 AI Fix Assistant and user approval",
        ],
        "real_only_note": PHASE10_REAL_ONLY_NOTE,
    }


def securescore_overview(user_id: str) -> dict[str, Any]:
    projects = list_projects(user_id, limit=500)
    scans = list_scans(user_id, limit=500)
    findings = _all_findings_for_user(user_id)
    scored = [scan.score for scan in scans if scan.score is not None]
    average_score = round(sum(scored) / len(scored)) if scored else None
    severity_counts = Counter(f["severity"] for f in findings)
    status_counts = Counter(f["workflow_status"] for f in findings)
    module_counts = Counter(f["module"] for f in findings)
    open_critical_high = [f for f in findings if f["severity"] in {"critical", "high"} and f["workflow_status"] not in FINAL_STATUSES]
    risk_buckets = Counter(_risk_bucket(scan.score) for scan in scans)
    sorted_scans = sorted(scans, key=lambda row: row.created_at)[-20:]
    return {
        "user_id": user_id,
        "summary": {
            "projects": len(projects),
            "saved_scans": len(scans),
            "findings": len(findings),
            "open_findings": sum(1 for f in findings if f["workflow_status"] not in FINAL_STATUSES),
            "open_critical_high": len(open_critical_high),
            "average_score": average_score,
            "risk_label": _score_label(average_score),
        },
        "severity_breakdown": {key: severity_counts.get(key, 0) for key in ["critical", "high", "medium", "low", "info"]},
        "workflow_breakdown": {key: status_counts.get(key, 0) for key in ["open", "in_progress", "fixed", "false_positive", "accepted_risk", "needs_manual_review"]},
        "module_findings": dict(module_counts),
        "risk_buckets": dict(risk_buckets),
        "module_scorecards": _module_scorecards(scans),
        "score_trend": [
            {
                "scan_id": scan.id,
                "created_at": scan.created_at.isoformat() if hasattr(scan.created_at, "isoformat") else str(scan.created_at),
                "module": scan.module,
                "score": scan.score,
                "risk_label": scan.risk_label or _score_label(scan.score),
            }
            for scan in sorted_scans
        ],
        "top_open_findings": open_critical_high[:10] or [f for f in findings if f["workflow_status"] not in FINAL_STATUSES][:10],
        "real_only_note": PHASE10_REAL_ONLY_NOTE,
        "auto_fix_status": "disabled_until_phase15_user_approved_ai_fix_assistant",
    }


def project_scorecard(user_id: str, project_id: str) -> dict[str, Any] | None:
    project = get_project(user_id, project_id)
    if project is None:
        return None
    scans = list_scans(user_id, limit=500, project_id=project_id)
    findings = _all_findings_for_user(user_id, project_id=project_id)
    scored = [scan.score for scan in scans if scan.score is not None]
    average_score = round(sum(scored) / len(scored)) if scored else None
    return {
        "project": project.model_dump(mode="json"),
        "summary": {
            "saved_scans": len(scans),
            "findings": len(findings),
            "open_findings": sum(1 for item in findings if item["workflow_status"] not in FINAL_STATUSES),
            "average_score": average_score,
            "risk_label": _score_label(average_score),
        },
        "module_scorecards": _module_scorecards(scans),
        "findings": findings,
        "real_only_note": PHASE10_REAL_ONLY_NOTE,
    }


def scan_scorecard(user_id: str, scan_id: str) -> dict[str, Any] | None:
    scan = get_scan(user_id, scan_id)
    if scan is None:
        return None
    workflows = _workflow_rows_for_user(user_id)
    findings = []
    for finding in _extract_payload_findings(scan):
        key = _workflow_key(scan.id, finding["id"])
        workflow = workflows.get(key, {})
        finding.update({
            "workflow_key": key,
            "workflow_status": workflow.get("status") or "open",
            "workflow_notes": workflow.get("notes"),
            "assigned_to": workflow.get("assigned_to"),
            "updated_at": workflow.get("updated_at"),
        })
        findings.append(finding)
    return {
        "scan": scan.model_dump(mode="json"),
        "scorecard": {
            "score": scan.score,
            "risk_label": scan.risk_label or _score_label(scan.score),
            "module": scan.module,
            "findings_count": len(findings),
            "critical_high_count": sum(1 for item in findings if item["severity"] in {"critical", "high"}),
        },
        "findings": findings,
        "real_only_note": PHASE10_REAL_ONLY_NOTE,
    }


def list_findings(
    user_id: str,
    *,
    project_id: str | None = None,
    module: str | None = None,
    severity: str | None = None,
    status: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    findings = _all_findings_for_user(user_id, project_id=project_id)
    if module:
        findings = [f for f in findings if f["module"] == module]
    if severity:
        findings = [f for f in findings if f["severity"] == severity]
    if status:
        findings = [f for f in findings if f["workflow_status"] == status]
    return findings[:limit]


def update_finding_workflow(
    user_id: str,
    *,
    scan_id: str,
    finding_id: str,
    status: str,
    notes: str | None = None,
    assigned_to: str | None = None,
) -> dict[str, Any]:
    scan = get_scan(user_id, scan_id)
    if scan is None:
        raise ValueError("Scan not found for this user")
    finding_ids = {item["id"] for item in _extract_payload_findings(scan)}
    if finding_id not in finding_ids:
        raise ValueError("Finding not found inside the saved scan payload")

    if status not in {"open", "in_progress", "fixed", "false_positive", "accepted_risk", "needs_manual_review"}:
        raise ValueError("Unsupported finding workflow status")

    key = _workflow_key(scan_id, finding_id)
    rows = _read_jsonl()
    existing = None
    for row in rows:
        if row.get("user_id") == user_id and row.get("workflow_key") == key:
            existing = row
            break
    now = _now()
    if existing:
        existing.update({
            "status": status,
            "notes": notes,
            "assigned_to": assigned_to,
            "updated_at": now,
            "fixed_at": now if status == "fixed" else existing.get("fixed_at"),
        })
        record = existing
    else:
        record = {
            "id": _new_id("fw"),
            "user_id": user_id,
            "scan_id": scan_id,
            "finding_id": finding_id,
            "workflow_key": key,
            "status": status,
            "notes": notes,
            "assigned_to": assigned_to,
            "created_at": now,
            "updated_at": now,
            "fixed_at": now if status == "fixed" else None,
            "source": "Phase 10 SecureScore workflow",
        }
        rows.append(record)
    _rewrite_jsonl(rows)
    return {**record, "real_only_note": PHASE10_REAL_ONLY_NOTE}
