from __future__ import annotations

import json
import secrets
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import httpx

from app.core.config import settings
from app.models.schemas import (
    DashboardActivityItem,
    DashboardOverview,
    Project,
    ProjectCreate,
    ProjectDetail,
    ProjectUpdate,
    SavedReport,
    SavedReportCreate,
    SavedReportUpdate,
    ScanHistoryCreate,
    ScanHistoryItem,
    ScanHistoryUpdate,
    UserProfile,
    UserProfileUpsert,
)

PHASE7_REAL_ONLY_NOTE = (
    "current/7.1 uses local JSONL persistence by default and switches to Supabase only when real Supabase env keys are configured. "
    "No fake users, fake scans, fake reports, fake subscriptions, or fake audit statuses are generated. "
    "When SUPABASE_AUTH_REQUIRED=true, dashboard APIs require a real Supabase session token."
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _new_id(prefix: str) -> str:
    return f"{prefix}_{secrets.token_hex(10)}"


def _storage_id(prefix: str) -> str:
    """Use UUIDs for Supabase tables and readable prefixed ids for local JSONL."""
    return str(uuid.uuid4()) if active_storage_mode() == "supabase" else _new_id(prefix)


def _path(raw: str) -> Path:
    path = Path(raw)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text("", encoding="utf-8")
    return path


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows


def _append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, default=str, ensure_ascii=False) + "\n")


def _rewrite_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, default=str, ensure_ascii=False) + "\n")


def _sort_created(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows.sort(key=lambda item: item.get("created_at", ""), reverse=True)
    return rows


def supabase_configured(require_service_role: bool = False) -> bool:
    if not settings.supabase_url or not settings.supabase_anon_key:
        return False
    if require_service_role and not settings.supabase_service_role_key:
        return False
    return True


def active_storage_mode() -> str:
    if settings.storage_mode == "supabase" and supabase_configured(require_service_role=True):
        return "supabase"
    if settings.storage_mode == "auto" and supabase_configured(require_service_role=True):
        return "supabase"
    return "local"


def db_status() -> dict[str, Any]:
    profiles_path = _path(settings.db_profiles_file)
    projects_path = _path(settings.db_projects_file)
    scans_path = _path(settings.db_scan_history_file)
    reports_path = _path(settings.db_saved_reports_file)
    return {
        "ok": True,
        "version": "1.0",
        "storage_mode_requested": settings.storage_mode,
        "storage_mode_active": active_storage_mode(),
        "supabase_configured": active_storage_mode() == "supabase",
        "supabase_env_configured": supabase_configured(),
        "supabase_service_role_configured": supabase_configured(require_service_role=True),
        "supabase_jwt_verify_enabled": settings.supabase_jwt_verify_enabled,
        "local_files": {
            "profiles": str(profiles_path),
            "projects": str(projects_path),
            "scan_history": str(scans_path),
            "saved_reports": str(reports_path),
        },
        "counts": {
            "profiles": len(_read_jsonl(profiles_path)),
            "projects": len(_read_jsonl(projects_path)),
            "scan_history": len(_read_jsonl(scans_path)),
            "saved_reports": len(_read_jsonl(reports_path)),
        },
        "real_only_note": PHASE7_REAL_ONLY_NOTE,
        "production_note": "Use Supabase migrations and set SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_ROLE_KEY, STORAGE_MODE=supabase, SUPABASE_JWT_VERIFY_ENABLED=true, and SUPABASE_AUTH_REQUIRED=true for production.",
    }


def _supabase_headers(use_service_role: bool = True) -> dict[str, str]:
    key = settings.supabase_service_role_key if use_service_role and settings.supabase_service_role_key else settings.supabase_anon_key
    if not key:
        raise RuntimeError("Supabase key is not configured")
    return {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }


def _sb_url(table: str, query: str = "") -> str:
    if not settings.supabase_url:
        raise RuntimeError("SUPABASE_URL is not configured")
    return f"{settings.supabase_url.rstrip('/')}/rest/v1/{table}{query}"


def _supabase_insert(table: str, row: dict[str, Any]) -> dict[str, Any]:
    with httpx.Client(timeout=12) as client:
        response = client.post(_sb_url(table), headers=_supabase_headers(), json=row)
        response.raise_for_status()
        data = response.json()
        return data[0] if isinstance(data, list) and data else row


def _supabase_select(table: str, query: str) -> list[dict[str, Any]]:
    with httpx.Client(timeout=12) as client:
        response = client.get(_sb_url(table, query), headers=_supabase_headers())
        response.raise_for_status()
        data = response.json()
        return data if isinstance(data, list) else []


def _supabase_patch(table: str, row_id: str, user_id: str, patch: dict[str, Any]) -> dict[str, Any] | None:
    with httpx.Client(timeout=12) as client:
        response = client.patch(
            _sb_url(table, f"?id=eq.{row_id}&user_id=eq.{user_id}"),
            headers=_supabase_headers(),
            json=patch,
        )
        response.raise_for_status()
        data = response.json()
        return data[0] if isinstance(data, list) and data else None


def upsert_profile(payload: UserProfileUpsert) -> UserProfile:
    now = _now()
    row = payload.model_dump()
    row["updated_at"] = now.isoformat()
    if active_storage_mode() == "supabase":
        with httpx.Client(timeout=12) as client:
            response = client.post(
                _sb_url("profiles", "?on_conflict=id"),
                headers={**_supabase_headers(), "Prefer": "resolution=merge-duplicates,return=representation"},
                json={**row, "created_at": now.isoformat()},
            )
            response.raise_for_status()
            data = response.json()
            return UserProfile.model_validate(data[0] if isinstance(data, list) and data else row)

    path = _path(settings.db_profiles_file)
    rows = _read_jsonl(path)
    existing = next((item for item in rows if item.get("id") == payload.id), None)
    if existing:
        existing.update(row)
    else:
        rows.append({**row, "created_at": now.isoformat(), "role": "user"})
    _rewrite_jsonl(path, rows)
    return UserProfile.model_validate(next(item for item in rows if item.get("id") == payload.id))


def get_profile(user_id: str) -> UserProfile | None:
    if active_storage_mode() == "supabase":
        rows = _supabase_select("profiles", f"?id=eq.{user_id}&limit=1")
        return UserProfile.model_validate(rows[0]) if rows else None
    for item in _read_jsonl(_path(settings.db_profiles_file)):
        if item.get("id") == user_id:
            return UserProfile.model_validate(item)
    return None


def create_project(user_id: str, payload: ProjectCreate) -> Project:
    now = _now()
    row = payload.model_dump()
    row.update({"id": _storage_id("project"), "user_id": user_id, "created_at": now.isoformat(), "updated_at": now.isoformat()})
    if active_storage_mode() == "supabase":
        return Project.model_validate(_supabase_insert("projects", row))
    _append_jsonl(_path(settings.db_projects_file), row)
    return Project.model_validate(row)


def list_projects(user_id: str, limit: int = 25) -> list[Project]:
    if active_storage_mode() == "supabase":
        rows = _supabase_select("projects", f"?user_id=eq.{user_id}&order=created_at.desc&limit={limit}")
        return [Project.model_validate(row) for row in rows]
    rows = [row for row in _read_jsonl(_path(settings.db_projects_file)) if row.get("user_id") == user_id]
    return [Project.model_validate(row) for row in _sort_created(rows)[:limit]]


def get_project(user_id: str, project_id: str) -> Project | None:
    if active_storage_mode() == "supabase":
        rows = _supabase_select("projects", f"?id=eq.{project_id}&user_id=eq.{user_id}&limit=1")
        return Project.model_validate(rows[0]) if rows else None
    for row in _read_jsonl(_path(settings.db_projects_file)):
        if row.get("id") == project_id and row.get("user_id") == user_id:
            return Project.model_validate(row)
    return None


def update_project(user_id: str, project_id: str, payload: ProjectUpdate) -> Project | None:
    patch = {k: v for k, v in payload.model_dump().items() if v is not None}
    patch["updated_at"] = _now().isoformat()
    if active_storage_mode() == "supabase":
        row = _supabase_patch("projects", project_id, user_id, patch)
        return Project.model_validate(row) if row else None
    path = _path(settings.db_projects_file)
    rows = _read_jsonl(path)
    updated = None
    for row in rows:
        if row.get("id") == project_id and row.get("user_id") == user_id:
            row.update(patch)
            updated = row
            break
    _rewrite_jsonl(path, rows)
    return Project.model_validate(updated) if updated else None


def save_scan(user_id: str, payload: ScanHistoryCreate) -> ScanHistoryItem:
    now = _now()
    row = payload.model_dump()
    row.update({"id": _storage_id("scan"), "user_id": user_id, "created_at": now.isoformat()})
    if active_storage_mode() == "supabase":
        return ScanHistoryItem.model_validate(_supabase_insert("scan_history", row))
    _append_jsonl(_path(settings.db_scan_history_file), row)
    return ScanHistoryItem.model_validate(row)


def list_scans(user_id: str, limit: int = 25, project_id: str | None = None) -> list[ScanHistoryItem]:
    if active_storage_mode() == "supabase":
        project_filter = f"&project_id=eq.{project_id}" if project_id else ""
        rows = _supabase_select("scan_history", f"?user_id=eq.{user_id}{project_filter}&order=created_at.desc&limit={limit}")
        return [ScanHistoryItem.model_validate(row) for row in rows]
    rows = [row for row in _read_jsonl(_path(settings.db_scan_history_file)) if row.get("user_id") == user_id]
    if project_id:
        rows = [row for row in rows if row.get("project_id") == project_id]
    return [ScanHistoryItem.model_validate(row) for row in _sort_created(rows)[:limit]]


def get_scan(user_id: str, scan_id: str) -> ScanHistoryItem | None:
    if active_storage_mode() == "supabase":
        rows = _supabase_select("scan_history", f"?id=eq.{scan_id}&user_id=eq.{user_id}&limit=1")
        return ScanHistoryItem.model_validate(rows[0]) if rows else None
    for row in _read_jsonl(_path(settings.db_scan_history_file)):
        if row.get("id") == scan_id and row.get("user_id") == user_id:
            return ScanHistoryItem.model_validate(row)
    return None


def update_scan(user_id: str, scan_id: str, payload: ScanHistoryUpdate) -> ScanHistoryItem | None:
    patch = {k: v for k, v in payload.model_dump().items() if v is not None}
    if active_storage_mode() == "supabase":
        row = _supabase_patch("scan_history", scan_id, user_id, patch)
        return ScanHistoryItem.model_validate(row) if row else None
    path = _path(settings.db_scan_history_file)
    rows = _read_jsonl(path)
    updated = None
    for row in rows:
        if row.get("id") == scan_id and row.get("user_id") == user_id:
            row.update(patch)
            updated = row
            break
    _rewrite_jsonl(path, rows)
    return ScanHistoryItem.model_validate(updated) if updated else None


def save_report(user_id: str, payload: SavedReportCreate) -> SavedReport:
    now = _now()
    row = payload.model_dump()
    row.update({"id": _storage_id("report"), "user_id": user_id, "created_at": now.isoformat()})
    if active_storage_mode() == "supabase":
        return SavedReport.model_validate(_supabase_insert("saved_reports", row))
    _append_jsonl(_path(settings.db_saved_reports_file), row)
    return SavedReport.model_validate(row)


def list_reports(user_id: str, limit: int = 25, project_id: str | None = None) -> list[SavedReport]:
    if active_storage_mode() == "supabase":
        project_filter = f"&project_id=eq.{project_id}" if project_id else ""
        rows = _supabase_select("saved_reports", f"?user_id=eq.{user_id}{project_filter}&order=created_at.desc&limit={limit}")
        return [SavedReport.model_validate(row) for row in rows]
    rows = [row for row in _read_jsonl(_path(settings.db_saved_reports_file)) if row.get("user_id") == user_id]
    if project_id:
        rows = [row for row in rows if row.get("project_id") == project_id]
    return [SavedReport.model_validate(row) for row in _sort_created(rows)[:limit]]


def get_report(user_id: str, saved_report_id: str) -> SavedReport | None:
    if active_storage_mode() == "supabase":
        rows = _supabase_select("saved_reports", f"?id=eq.{saved_report_id}&user_id=eq.{user_id}&limit=1")
        return SavedReport.model_validate(rows[0]) if rows else None
    for row in _read_jsonl(_path(settings.db_saved_reports_file)):
        if row.get("id") == saved_report_id and row.get("user_id") == user_id:
            return SavedReport.model_validate(row)
    return None


def update_report(user_id: str, saved_report_id: str, payload: SavedReportUpdate) -> SavedReport | None:
    patch = {k: v for k, v in payload.model_dump().items() if v is not None}
    if active_storage_mode() == "supabase":
        row = _supabase_patch("saved_reports", saved_report_id, user_id, patch)
        return SavedReport.model_validate(row) if row else None
    path = _path(settings.db_saved_reports_file)
    rows = _read_jsonl(path)
    updated = None
    for row in rows:
        if row.get("id") == saved_report_id and row.get("user_id") == user_id:
            row.update(patch)
            updated = row
            break
    _rewrite_jsonl(path, rows)
    return SavedReport.model_validate(updated) if updated else None


def _activity_from(projects: list[Project], scans: list[ScanHistoryItem], reports: list[SavedReport]) -> list[DashboardActivityItem]:
    activity: list[DashboardActivityItem] = []
    for project in projects:
        activity.append(DashboardActivityItem(
            id=project.id,
            type="project",
            title=f"Project saved: {project.name}",
            subtitle=project.website_url or project.chain or "No project URL yet",
            created_at=project.created_at,
            project_id=project.id,
            href=f"/dashboard/projects/{project.id}",
        ))
    for scan in scans:
        activity.append(DashboardActivityItem(
            id=scan.id,
            type="scan",
            title=f"{scan.module.title()} scan saved",
            subtitle=f"{scan.risk_label or 'No risk label'} • {scan.findings_count} finding(s)",
            created_at=scan.created_at,
            project_id=scan.project_id,
            href=f"/dashboard/scans/{scan.id}",
        ))
    for report in reports:
        activity.append(DashboardActivityItem(
            id=report.id,
            type="report",
            title=f"Report saved: {report.title}",
            subtitle=f"{report.risk_label or 'No risk label'} • {report.visibility}",
            created_at=report.created_at,
            project_id=report.project_id,
            href=f"/dashboard/reports/{report.id}",
        ))
    activity.sort(key=lambda item: item.created_at, reverse=True)
    return activity[:25]


def project_detail(user_id: str, project_id: str) -> ProjectDetail | None:
    project = get_project(user_id, project_id)
    if not project:
        return None
    scans = list_scans(user_id, limit=50, project_id=project_id)
    reports = list_reports(user_id, limit=50, project_id=project_id)
    activity = _activity_from([project], scans, reports)
    scored = [scan.score for scan in scans if scan.score is not None]
    totals = {
        "scans": len(scans),
        "reports": len(reports),
        "critical_high_findings": sum(scan.critical_high_count for scan in scans),
        "findings": sum(scan.findings_count for scan in scans),
        "average_score": round(sum(scored) / len(scored)) if scored else None,
    }
    return ProjectDetail(project=project, scans=scans, reports=reports, activity=activity, totals=totals)


def dashboard_overview(user_id: str) -> DashboardOverview:
    profile = get_profile(user_id)
    projects = list_projects(user_id, limit=100)
    scans = list_scans(user_id, limit=100)
    reports = list_reports(user_id, limit=100)
    critical_high = sum(item.critical_high_count for item in scans)
    scored = [item.score for item in scans if item.score is not None]
    average_score = round(sum(scored) / len(scored)) if scored else None
    recent_projects = projects[:10]
    recent_scans = scans[:10]
    recent_reports = reports[:10]
    return DashboardOverview(
        user_id=user_id,
        storage_mode=active_storage_mode(),
        auth_mode="supabase-jwt" if settings.supabase_jwt_verify_enabled and supabase_configured() else "local-or-client-session",
        profile=profile,
        totals={
            "projects": len(projects),
            "saved_scans": len(scans),
            "saved_reports": len(reports),
            "critical_high_findings": critical_high,
            "average_score": average_score,
            "subscription_status": "not_connected_until_phase8_razorpay",
        },
        projects=recent_projects,
        recent_scans=recent_scans,
        recent_reports=recent_reports,
        activity=_activity_from(recent_projects, recent_scans, recent_reports),
    )
