from __future__ import annotations

import hashlib
import json
import secrets
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import httpx

from app.core.config import settings
from app.services.database_store import list_projects, list_reports, list_scans
from app.services.monitoring_lite import list_monitoring_alerts

CONTINUOUS_MONITORING_NOTE = (
    "Continuous Monitoring Lite is an opt-in, owner-authorized monitoring layer. "
    "It can create monitoring configs, derive stale-report/project-health alerts from stored records, "
    "and optionally run read-only passive checks only when network/RPC/provider settings are enabled. "
    "It does not perform unauthorized active scanning, exploit testing, wallet signing, or fake alert generation."
)

SCHEDULE_NOTE = (
    "The backend stores schedule intent and due status only. A real cron/worker must call the recheck endpoint. "
    "If no scheduler is configured, the UI must show Manual / Not Scheduled rather than fake live monitoring."
)

DEFAULT_CHECKS = [
    "stale_report",
    "scan_age",
    "website_passive",
    "github_repo_change",
    "sentinel_alert_queue",
    "rpc_event_monitoring",
]

SEVERITY_ORDER = {"critical": 5, "high": 4, "medium": 3, "low": 2, "info": 1}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _id(prefix: str) -> str:
    return f"{prefix}_{secrets.token_hex(10)}"


def _path(raw: str) -> Path:
    path = Path(raw)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text("", encoding="utf-8")
    return path


def _read(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            item = json.loads(line)
            if isinstance(item, dict):
                rows.append(item)
        except json.JSONDecodeError:
            continue
    return rows


def _append(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")


def _rewrite(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")


def _configs_file() -> Path:
    return _path(getattr(settings, "continuous_monitoring_configs_file", "app/data/db/continuous_monitoring_configs.jsonl"))


def _alerts_file() -> Path:
    return _path(getattr(settings, "continuous_monitoring_alerts_file", "app/data/db/continuous_monitoring_alerts.jsonl"))


def _events_file() -> Path:
    return _path(getattr(settings, "continuous_monitoring_events_file", "app/data/db/continuous_monitoring_events.jsonl"))


def _snapshots_file() -> Path:
    return _path(getattr(settings, "continuous_monitoring_snapshots_file", "app/data/db/continuous_monitoring_snapshots.jsonl"))


def _hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def _parse_dt(value: Any) -> datetime | None:
    if not value:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    try:
        text = str(value).replace("Z", "+00:00")
        parsed = datetime.fromisoformat(text)
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except Exception:
        return None


def _age_days(value: Any) -> int | None:
    parsed = _parse_dt(value)
    if not parsed:
        return None
    return max(0, (_now() - parsed).days)


def _next_due(last_checked_at: Any, cadence: str) -> str | None:
    base = _parse_dt(last_checked_at) or _now()
    clean = (cadence or "manual").lower()
    if clean == "daily":
        return (base + timedelta(days=1)).isoformat()
    if clean == "weekly":
        return (base + timedelta(days=7)).isoformat()
    if clean == "monthly":
        return (base + timedelta(days=30)).isoformat()
    return None


def _is_due(config: dict[str, Any]) -> bool:
    due = _parse_dt(config.get("next_due_at"))
    return bool(due and due <= _now() and config.get("status") == "active")


def _clean_checks(raw: Any) -> list[str]:
    if isinstance(raw, list):
        checks = [str(item).strip().lower() for item in raw if str(item).strip()]
    elif isinstance(raw, str):
        checks = [item.strip().lower() for item in raw.split(",") if item.strip()]
    else:
        checks = DEFAULT_CHECKS[:]
    allowed = set(DEFAULT_CHECKS)
    return [item for item in checks if item in allowed] or DEFAULT_CHECKS[:]


def _clean_cadence(value: str | None) -> str:
    clean = str(value or "manual").lower().strip()
    if clean in {"manual", "daily", "weekly", "monthly"}:
        return clean
    return "manual"


def _severity(value: str | None) -> str:
    clean = str(value or "info").lower().strip()
    if clean in SEVERITY_ORDER:
        return clean
    return "info"


def _project_to_config_defaults(project: Any) -> dict[str, Any]:
    return {
        "project_id": getattr(project, "id", None),
        "project_name": getattr(project, "name", None),
        "website_url": getattr(project, "website_url", None),
        "github_repo_url": getattr(project, "github_repo_url", None),
        "contract_address": getattr(project, "contract_address", None),
        "chain": getattr(project, "chain", None) or "ethereum",
    }


def _normalise_url(value: str | None) -> str | None:
    if not value:
        return None
    clean = value.strip()
    if not clean:
        return None
    if clean.startswith("http://") or clean.startswith("https://"):
        return clean
    return f"https://{clean}"


def _passive_website_snapshot(url: str) -> dict[str, Any]:
    if not getattr(settings, "continuous_monitoring_network_enabled", False):
        return {
            "status": "Not Assessed",
            "reason": "continuous monitoring network checks are disabled; no fake website drift check was performed",
            "url": url,
        }
    with httpx.Client(timeout=getattr(settings, "continuous_monitoring_http_timeout_seconds", 8), follow_redirects=True) as client:
        response = client.get(url, headers={"User-Agent": settings.website_scanner_user_agent})
    headers = {k.lower(): v for k, v in response.headers.items()}
    parsed = urlparse(str(response.url))
    return {
        "status": "Assessed",
        "url": str(response.url),
        "host": parsed.netloc,
        "status_code": response.status_code,
        "https": parsed.scheme == "https",
        "security_headers": {
            "content-security-policy": bool(headers.get("content-security-policy")),
            "strict-transport-security": bool(headers.get("strict-transport-security")),
            "x-frame-options": bool(headers.get("x-frame-options")),
            "referrer-policy": bool(headers.get("referrer-policy")),
        },
        "server_header_present": bool(headers.get("server")),
        "content_length": len(response.content or b""),
        "snapshot_hash": _hash({"status": response.status_code, "headers": headers, "url": str(response.url)})[:24],
    }


def _github_repo_snapshot(repo_url: str | None) -> dict[str, Any]:
    if not repo_url:
        return {"status": "Not Assessed", "reason": "No GitHub repository URL on monitoring config"}
    if not getattr(settings, "continuous_monitoring_github_enabled", False):
        return {
            "status": "Not Assessed",
            "reason": "GitHub continuous checks disabled; use manual scan or enable provider settings",
            "repo_url": repo_url,
        }
    return {
        "status": "Manual / Provider Ready",
        "repo_url": repo_url,
        "reason": "Provider-ready placeholder only. Deep GitHub drift should use the existing GitHub scanner or GitHub webhooks.",
    }


def _sentinel_alert_summary() -> dict[str, Any]:
    path = _path(settings.sentinel_alerts_file)
    rows = _read(path)
    counts = Counter(_severity(str(item.get("severity"))) for item in rows)
    return {
        "status": "Assessed" if rows else "No stored Sentinel alerts",
        "total": len(rows),
        "by_severity": dict(counts),
        "recent": sorted(rows, key=lambda item: item.get("created_at", ""), reverse=True)[:10],
    }


def _monitoring_status() -> dict[str, Any]:
    configs = _read(_configs_file())
    alerts = _read(_alerts_file())
    events = _read(_events_file())
    due = [item for item in configs if _is_due(item)]
    return {
        "ok": True,
        "phase": "Phase 19 - Continuous Monitoring Lite",
        "enabled": getattr(settings, "continuous_monitoring_enabled", True),
        "network_checks_enabled": getattr(settings, "continuous_monitoring_network_enabled", False),
        "github_checks_enabled": getattr(settings, "continuous_monitoring_github_enabled", False),
        "scheduler_configured": getattr(settings, "continuous_monitoring_scheduler_configured", False),
        "config_count": len(configs),
        "alert_count": len(alerts),
        "event_count": len(events),
        "due_config_count": len(due),
        "supported_checks": DEFAULT_CHECKS,
        "cadences": ["manual", "daily", "weekly", "monthly"],
        "modes": ["manual_recheck", "external_scheduler_calls_endpoint", "optional_passive_network_checks"],
        "real_only_note": CONTINUOUS_MONITORING_NOTE,
        "schedule_note": SCHEDULE_NOTE,
    }


def continuous_status() -> dict[str, Any]:
    return _monitoring_status()


def create_monitoring_config(payload: Any) -> dict[str, Any]:
    cadence = _clean_cadence(getattr(payload, "cadence", "manual"))
    checks = _clean_checks(getattr(payload, "checks", None))
    now = _now().isoformat()
    project_id = getattr(payload, "project_id", None)
    user_id = getattr(payload, "user_id", None) or settings.local_demo_user_id
    row = {
        "id": _id("cmcfg"),
        "created_at": now,
        "updated_at": now,
        "user_id": user_id,
        "project_id": project_id,
        "project_name": getattr(payload, "project_name", None) or "Monitored project",
        "website_url": _normalise_url(getattr(payload, "website_url", None)),
        "github_repo_url": getattr(payload, "github_repo_url", None),
        "contract_address": getattr(payload, "contract_address", None),
        "chain": (getattr(payload, "chain", None) or "ethereum").lower(),
        "cadence": cadence,
        "checks": checks,
        "alert_channels": getattr(payload, "alert_channels", None) or ["dashboard"],
        "status": "active",
        "last_checked_at": None,
        "next_due_at": _next_due(None, cadence),
        "authorization_confirmed": bool(getattr(payload, "authorization_confirmed", False)),
        "real_only_acknowledged": bool(getattr(payload, "real_only_acknowledged", False)),
        "notes": getattr(payload, "notes", None),
        "real_only_note": CONTINUOUS_MONITORING_NOTE,
    }
    _append(_configs_file(), row)
    return row


def list_configs(user_id: str | None = None) -> list[dict[str, Any]]:
    rows = _read(_configs_file())
    if user_id:
        rows = [item for item in rows if item.get("user_id") == user_id]
    rows.sort(key=lambda item: item.get("created_at", ""), reverse=True)
    return rows


def get_config(config_id: str, user_id: str | None = None) -> dict[str, Any] | None:
    for item in list_configs(user_id=user_id):
        if item.get("id") == config_id:
            return item
    return None


def list_alerts(user_id: str | None = None, config_id: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
    rows = _read(_alerts_file())
    if user_id:
        rows = [item for item in rows if item.get("user_id") == user_id]
    if config_id:
        rows = [item for item in rows if item.get("config_id") == config_id]
    rows.sort(key=lambda item: item.get("created_at", ""), reverse=True)
    return rows[:limit]


def _alert(config: dict[str, Any], severity: str, title: str, description: str, check_type: str, evidence: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": _id("cmalert"),
        "created_at": _now().isoformat(),
        "user_id": config.get("user_id"),
        "project_id": config.get("project_id"),
        "config_id": config.get("id"),
        "project_name": config.get("project_name"),
        "severity": _severity(severity),
        "title": title,
        "description": description,
        "check_type": check_type,
        "evidence": evidence,
        "status": "open",
        "notification_status": "dashboard_recorded_only",
        "real_only_note": "This alert is derived from a stored config, stored project/scan/report record, or an enabled read-only check. It is not a fake live alert.",
    }


def _dedupe_alerts(new_alerts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    existing = _read(_alerts_file())
    existing_keys = {
        f"{item.get('config_id')}:{item.get('check_type')}:{item.get('title')}:{item.get('status')}"
        for item in existing
        if item.get("status") == "open"
    }
    stored: list[dict[str, Any]] = []
    for alert in new_alerts:
        key = f"{alert.get('config_id')}:{alert.get('check_type')}:{alert.get('title')}:{alert.get('status')}"
        if key in existing_keys:
            continue
        _append(_alerts_file(), alert)
        stored.append(alert)
        existing_keys.add(key)
    return stored


def _latest_report_and_scan(config: dict[str, Any]) -> tuple[Any | None, Any | None]:
    user_id = config.get("user_id") or settings.local_demo_user_id
    project_id = config.get("project_id")
    reports = list_reports(user_id, limit=50, project_id=project_id) if project_id else list_reports(user_id, limit=50)
    scans = list_scans(user_id, limit=50, project_id=project_id) if project_id else list_scans(user_id, limit=50)
    return (reports[0] if reports else None, scans[0] if scans else None)


def _derive_stale_alerts(config: dict[str, Any]) -> list[dict[str, Any]]:
    alerts: list[dict[str, Any]] = []
    report, scan = _latest_report_and_scan(config)
    report_age = _age_days(getattr(report, "created_at", None)) if report else None
    scan_age = _age_days(getattr(scan, "created_at", None)) if scan else None
    max_report_age = getattr(settings, "continuous_monitoring_stale_report_days", 30)
    max_scan_age = getattr(settings, "continuous_monitoring_stale_scan_days", 14)
    if "stale_report" in config.get("checks", []) and (not report or (report_age is not None and report_age > max_report_age)):
        alerts.append(_alert(
            config,
            "medium",
            "Report freshness review needed",
            "No recent saved report was found for this project, or the latest report is older than the configured freshness window.",
            "stale_report",
            {"latest_report_id": getattr(report, "report_id", None) if report else None, "age_days": report_age, "threshold_days": max_report_age},
        ))
    if "scan_age" in config.get("checks", []) and (not scan or (scan_age is not None and scan_age > max_scan_age)):
        alerts.append(_alert(
            config,
            "low",
            "Scan freshness review needed",
            "No recent saved scan was found for this project, or the latest scan is older than the configured freshness window.",
            "scan_age",
            {"latest_scan_id": getattr(scan, "id", None) if scan else None, "age_days": scan_age, "threshold_days": max_scan_age},
        ))
    return alerts


def _snapshot_record(config: dict[str, Any], snapshot: dict[str, Any], snapshot_type: str) -> dict[str, Any]:
    row = {
        "id": _id("cmsnap"),
        "created_at": _now().isoformat(),
        "user_id": config.get("user_id"),
        "project_id": config.get("project_id"),
        "config_id": config.get("id"),
        "snapshot_type": snapshot_type,
        "snapshot_hash": _hash(snapshot),
        "snapshot": snapshot,
    }
    _append(_snapshots_file(), row)
    return row


def _previous_snapshot(config_id: str, snapshot_type: str) -> dict[str, Any] | None:
    rows = [item for item in _read(_snapshots_file()) if item.get("config_id") == config_id and item.get("snapshot_type") == snapshot_type]
    rows.sort(key=lambda item: item.get("created_at", ""), reverse=True)
    return rows[0] if rows else None


def run_recheck(config_id: str, user_id: str | None = None, force: bool = False) -> dict[str, Any]:
    config = get_config(config_id, user_id=user_id)
    if not config:
        raise ValueError("Continuous monitoring config not found")
    if config.get("status") != "active":
        raise ValueError("Continuous monitoring config is not active")
    if not force and config.get("cadence") != "manual" and not _is_due(config):
        return {
            "ok": True,
            "ran": False,
            "reason": "Config is not due yet. Use force=true for an authorized manual recheck.",
            "config": config,
            "new_alerts": [],
            "real_only_note": CONTINUOUS_MONITORING_NOTE,
        }

    new_alerts = _derive_stale_alerts(config)
    snapshots: list[dict[str, Any]] = []

    if "website_passive" in config.get("checks", []) and config.get("website_url"):
        snapshot = _passive_website_snapshot(config["website_url"])
        prev = _previous_snapshot(config["id"], "website_passive")
        snapshots.append(_snapshot_record(config, snapshot, "website_passive"))
        if prev and snapshot.get("status") == "Assessed" and prev.get("snapshot_hash") != _hash(snapshot):
            new_alerts.append(_alert(
                config,
                "medium",
                "Website surface drift detected",
                "The passive website snapshot changed since the last stored check. Review headers/status before treating it as an incident.",
                "website_passive",
                {"previous_hash": prev.get("snapshot_hash"), "current_hash": _hash(snapshot), "snapshot_status": snapshot.get("status")},
            ))

    if "github_repo_change" in config.get("checks", []):
        snapshot = _github_repo_snapshot(config.get("github_repo_url"))
        snapshots.append(_snapshot_record(config, snapshot, "github_repo_change"))

    if "sentinel_alert_queue" in config.get("checks", []):
        sentinel = _sentinel_alert_summary()
        snapshots.append(_snapshot_record(config, sentinel, "sentinel_alert_queue"))
        critical_or_high = (sentinel.get("by_severity") or {}).get("critical", 0) + (sentinel.get("by_severity") or {}).get("high", 0)
        if critical_or_high:
            new_alerts.append(_alert(
                config,
                "high",
                "Sentinel high-priority alert queue has items",
                "Sentinel has stored high/critical alerts that should be reviewed in the admin intelligence workflow.",
                "sentinel_alert_queue",
                {"high_or_critical_count": critical_or_high, "sentinel_total": sentinel.get("total", 0)},
            ))

    if "rpc_event_monitoring" in config.get("checks", []):
        rpc_alerts = list_monitoring_alerts(limit=50)
        matching = [item for item in rpc_alerts if (config.get("contract_address") and str(item.get("contract_address", "")).lower() == str(config.get("contract_address", "")).lower())]
        if matching:
            new_alerts.append(_alert(
                config,
                "medium",
                "RPC monitoring alerts exist for this contract",
                "Existing Monitoring Lite records contain alerts for this contract. Review them before marking launch status as clean.",
                "rpc_event_monitoring",
                {"matching_alerts": len(matching), "latest_alert": matching[0]},
            ))

    stored_alerts = _dedupe_alerts(new_alerts)
    now = _now().isoformat()
    configs = _read(_configs_file())
    for row in configs:
        if row.get("id") == config["id"]:
            row["last_checked_at"] = now
            row["updated_at"] = now
            row["next_due_at"] = _next_due(now, row.get("cadence", "manual"))
            break
    _rewrite(_configs_file(), configs)

    event = {
        "id": _id("cmrun"),
        "created_at": now,
        "user_id": config.get("user_id"),
        "project_id": config.get("project_id"),
        "config_id": config.get("id"),
        "force": force,
        "checks": config.get("checks", []),
        "snapshots_saved": len(snapshots),
        "alerts_generated": len(new_alerts),
        "alerts_stored": len(stored_alerts),
        "network_checks_enabled": getattr(settings, "continuous_monitoring_network_enabled", False),
        "real_only_note": CONTINUOUS_MONITORING_NOTE,
    }
    _append(_events_file(), event)
    return {
        "ok": True,
        "ran": True,
        "event": event,
        "config": get_config(config["id"], user_id=user_id),
        "snapshots": snapshots,
        "new_alerts": stored_alerts,
        "real_only_note": CONTINUOUS_MONITORING_NOTE,
    }


def run_due_rechecks(limit: int = 10) -> dict[str, Any]:
    due = [item for item in list_configs() if _is_due(item)][: max(1, min(limit, 25))]
    results = []
    for config in due:
        try:
            results.append(run_recheck(config["id"], user_id=config.get("user_id"), force=True))
        except Exception as exc:
            results.append({"ok": False, "config_id": config.get("id"), "error": str(exc)})
    return {
        "ok": True,
        "due_count": len(due),
        "results": results,
        "schedule_note": SCHEDULE_NOTE,
        "real_only_note": CONTINUOUS_MONITORING_NOTE,
    }


def user_dashboard(user_id: str) -> dict[str, Any]:
    projects = list_projects(user_id, limit=100)
    configs = list_configs(user_id=user_id)
    alerts = list_alerts(user_id=user_id, limit=100)
    project_ids_with_config = {item.get("project_id") for item in configs if item.get("project_id")}
    suggested = []
    for project in projects:
        if project.id not in project_ids_with_config:
            suggested.append({
                "project_id": project.id,
                "project_name": project.name,
                "suggested_config": _project_to_config_defaults(project),
                "reason": "No continuous monitoring config exists for this stored project.",
            })
    counts = Counter(_severity(str(item.get("severity"))) for item in alerts)
    return {
        "ok": True,
        "user_id": user_id,
        "project_count": len(projects),
        "config_count": len(configs),
        "alert_count": len(alerts),
        "alerts_by_severity": dict(counts),
        "due_configs": [item for item in configs if _is_due(item)],
        "configs": configs,
        "alerts": alerts[:25],
        "suggested_configs": suggested[:20],
        "status": _monitoring_status(),
        "real_only_note": CONTINUOUS_MONITORING_NOTE,
    }


def admin_overview() -> dict[str, Any]:
    configs = list_configs()
    alerts = list_alerts(limit=500)
    events = _read(_events_file())
    snapshots = _read(_snapshots_file())
    by_user: dict[str, int] = defaultdict(int)
    for config in configs:
        by_user[str(config.get("user_id") or "unknown")] += 1
    severity_counts = Counter(_severity(str(item.get("severity"))) for item in alerts)
    check_counts = Counter(item.get("check_type") or "unknown" for item in alerts)
    return {
        "ok": True,
        "status": _monitoring_status(),
        "config_count": len(configs),
        "alert_count": len(alerts),
        "event_count": len(events),
        "snapshot_count": len(snapshots),
        "due_configs": [item for item in configs if _is_due(item)][:50],
        "alerts_by_severity": dict(severity_counts),
        "alerts_by_check_type": dict(check_counts),
        "configs_by_user": dict(sorted(by_user.items(), key=lambda item: item[1], reverse=True)[:25]),
        "recent_alerts": alerts[:30],
        "recent_events": sorted(events, key=lambda item: item.get("created_at", ""), reverse=True)[:30],
        "real_only_note": CONTINUOUS_MONITORING_NOTE,
    }
