
from __future__ import annotations

import json
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from app.core.config import settings
from app.models.schemas import (
    FindingTask,
    FindingTaskCreate,
    FindingTaskUpdate,
    Organization,
    OrganizationCreate,
    OrganizationMember,
    OrganizationMemberInvite,
    OrganizationMemberUpdate,
    OrganizationUpdate,
    Project,
    SavedReport,
    ScanHistoryItem,
    WorkspaceActivityItem,
    WorkspaceComment,
    WorkspaceCommentCreate,
    WorkspaceOverview,
)
from app.services.database_store import list_projects, list_reports, list_scans

PHASE72_REAL_ONLY_NOTE = (
    "Web3Guard stores real organization/team workspace records only. "
    "Member invites are manual invite records until email delivery is connected; no fake email invite, fake member activity, or fake collaboration data is generated."
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _new_id(prefix: str) -> str:
    return f"{prefix}_{secrets.token_hex(10)}"


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


def _activity(org_id: str, type_: str, title: str, subtitle: str | None = None, user_id: str | None = None, target_id: str | None = None) -> WorkspaceActivityItem:
    row = {
        "id": _new_id("act"),
        "organization_id": org_id,
        "type": type_,
        "title": title,
        "subtitle": subtitle,
        "created_by_user_id": user_id,
        "created_at": _now().isoformat(),
        "target_id": target_id,
    }
    _append_jsonl(_path(settings.db_workspace_activity_file), row)
    return WorkspaceActivityItem.model_validate(row)


def list_organizations(user_id: str, limit: int = 25) -> list[Organization]:
    org_rows = _read_jsonl(_path(settings.db_organizations_file))
    member_rows = _read_jsonl(_path(settings.db_org_members_file))
    allowed_ids = {
        row.get("organization_id") for row in member_rows
        if row.get("user_id") == user_id and row.get("status") == "active"
    }
    rows = [row for row in org_rows if row.get("owner_user_id") == user_id or row.get("id") in allowed_ids]
    return [Organization.model_validate(row) for row in _sort_created(rows)[:limit]]


def create_organization(user_id: str, payload: OrganizationCreate) -> Organization:
    now = _now()
    row = {
        "id": _new_id("org"),
        "owner_user_id": user_id,
        "name": payload.name,
        "website_url": payload.website_url,
        "billing_email": str(payload.billing_email) if payload.billing_email else None,
        "gst_number": payload.gst_number,
        "notes": payload.notes,
        "plan": "free",
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
    }
    _append_jsonl(_path(settings.db_organizations_file), row)
    member = {
        "id": _new_id("mem"),
        "organization_id": row["id"],
        "user_id": user_id,
        "email": str(payload.billing_email) if payload.billing_email else None,
        "full_name": "Workspace owner",
        "role": "owner",
        "status": "active",
        "invited_by_user_id": user_id,
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
        "note": "Auto-created owner membership for the real organization record.",
    }
    _append_jsonl(_path(settings.db_org_members_file), member)
    _activity(row["id"], "organization", "Organization created", payload.name, user_id, row["id"])
    return Organization.model_validate(row)


def get_organization(user_id: str, org_id: str) -> Organization | None:
    for org in list_organizations(user_id, limit=1000):
        if org.id == org_id:
            return org
    return None


def user_role(user_id: str, org_id: str) -> str | None:
    org = next((row for row in _read_jsonl(_path(settings.db_organizations_file)) if row.get("id") == org_id), None)
    if org and org.get("owner_user_id") == user_id:
        return "owner"
    for row in _read_jsonl(_path(settings.db_org_members_file)):
        if row.get("organization_id") == org_id and row.get("user_id") == user_id and row.get("status") == "active":
            return row.get("role")
    return None


def update_organization(user_id: str, org_id: str, payload: OrganizationUpdate) -> Organization | None:
    if user_role(user_id, org_id) not in {"owner", "admin"}:
        return None
    patch = {k: (str(v) if k == "billing_email" and v is not None else v) for k, v in payload.model_dump().items() if v is not None}
    patch["updated_at"] = _now().isoformat()
    path = _path(settings.db_organizations_file)
    rows = _read_jsonl(path)
    updated = None
    for row in rows:
        if row.get("id") == org_id:
            row.update(patch)
            updated = row
            break
    _rewrite_jsonl(path, rows)
    if updated:
        _activity(org_id, "organization", "Organization updated", updated.get("name"), user_id, org_id)
    return Organization.model_validate(updated) if updated else None


def list_members(user_id: str, org_id: str) -> list[OrganizationMember] | None:
    if user_role(user_id, org_id) is None:
        return None
    rows = [row for row in _read_jsonl(_path(settings.db_org_members_file)) if row.get("organization_id") == org_id and row.get("status") != "removed"]
    return [OrganizationMember.model_validate(row) for row in _sort_created(rows)]


def invite_member(user_id: str, org_id: str, payload: OrganizationMemberInvite) -> OrganizationMember | None:
    if user_role(user_id, org_id) not in {"owner", "admin"}:
        return None
    now = _now()
    row = {
        "id": _new_id("mem"),
        "organization_id": org_id,
        "user_id": payload.user_id,
        "email": str(payload.email) if payload.email else None,
        "full_name": payload.full_name,
        "role": payload.role,
        "status": payload.status,
        "invited_by_user_id": user_id,
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
        "note": payload.note,
    }
    _append_jsonl(_path(settings.db_org_members_file), row)
    _activity(org_id, "member", "Member invite saved", f"{payload.email or payload.user_id or payload.full_name} • {payload.role}", user_id, row["id"])
    return OrganizationMember.model_validate(row)


def update_member(user_id: str, org_id: str, member_id: str, payload: OrganizationMemberUpdate) -> OrganizationMember | None:
    if user_role(user_id, org_id) not in {"owner", "admin"}:
        return None
    patch = {k: v for k, v in payload.model_dump().items() if v is not None}
    patch["updated_at"] = _now().isoformat()
    path = _path(settings.db_org_members_file)
    rows = _read_jsonl(path)
    updated = None
    for row in rows:
        if row.get("id") == member_id and row.get("organization_id") == org_id:
            row.update(patch)
            updated = row
            break
    _rewrite_jsonl(path, rows)
    if updated:
        _activity(org_id, "member", "Member updated", updated.get("email") or updated.get("user_id"), user_id, member_id)
    return OrganizationMember.model_validate(updated) if updated else None


def create_task(user_id: str, payload: FindingTaskCreate) -> FindingTask | None:
    if user_role(user_id, payload.organization_id) not in {"owner", "admin", "reviewer", "member"}:
        return None
    now = _now()
    row = payload.model_dump(exclude={"user_id"})
    row.update({"id": _new_id("task"), "created_by_user_id": user_id, "created_at": now.isoformat(), "updated_at": now.isoformat()})
    _append_jsonl(_path(settings.db_finding_tasks_file), row)
    _activity(payload.organization_id, "task", "Finding task created", payload.title, user_id, row["id"])
    return FindingTask.model_validate(row)


def list_tasks(user_id: str, org_id: str, project_id: str | None = None) -> list[FindingTask] | None:
    if user_role(user_id, org_id) is None:
        return None
    rows = [row for row in _read_jsonl(_path(settings.db_finding_tasks_file)) if row.get("organization_id") == org_id]
    if project_id:
        rows = [row for row in rows if row.get("project_id") == project_id]
    return [FindingTask.model_validate(row) for row in _sort_created(rows)]


def update_task(user_id: str, org_id: str, task_id: str, payload: FindingTaskUpdate) -> FindingTask | None:
    if user_role(user_id, org_id) not in {"owner", "admin", "reviewer", "member"}:
        return None
    patch = {k: v for k, v in payload.model_dump().items() if v is not None}
    patch["updated_at"] = _now().isoformat()
    path = _path(settings.db_finding_tasks_file)
    rows = _read_jsonl(path)
    updated = None
    for row in rows:
        if row.get("id") == task_id and row.get("organization_id") == org_id:
            row.update(patch)
            updated = row
            break
    _rewrite_jsonl(path, rows)
    if updated:
        _activity(org_id, "task", "Finding task updated", updated.get("title"), user_id, task_id)
    return FindingTask.model_validate(updated) if updated else None


def add_comment(user_id: str, payload: WorkspaceCommentCreate) -> WorkspaceComment | None:
    if user_role(user_id, payload.organization_id) is None:
        return None
    row = payload.model_dump(exclude={"user_id"})
    row.update({"id": _new_id("com"), "created_by_user_id": user_id, "created_at": _now().isoformat()})
    _append_jsonl(_path(settings.db_workspace_comments_file), row)
    _activity(payload.organization_id, "comment", "Comment added", payload.body[:120], user_id, row["id"])
    return WorkspaceComment.model_validate(row)


def list_comments(user_id: str, org_id: str, project_id: str | None = None) -> list[WorkspaceComment] | None:
    if user_role(user_id, org_id) is None:
        return None
    rows = [row for row in _read_jsonl(_path(settings.db_workspace_comments_file)) if row.get("organization_id") == org_id]
    if project_id:
        rows = [row for row in rows if row.get("project_id") == project_id]
    return [WorkspaceComment.model_validate(row) for row in _sort_created(rows)]


def workspace_overview(user_id: str, org_id: str) -> WorkspaceOverview | None:
    org = get_organization(user_id, org_id)
    if not org:
        return None
    role = user_role(user_id, org_id)
    members = list_members(user_id, org_id) or []
    # Web3Guard keeps ownership simple: projects/scans/reports are filtered by current user, not copied/faked into orgs.
    projects = list_projects(user_id, limit=100)
    scans = list_scans(user_id, limit=100)
    reports = list_reports(user_id, limit=100)
    tasks = list_tasks(user_id, org_id) or []
    comments = list_comments(user_id, org_id) or []
    activities = [WorkspaceActivityItem.model_validate(row) for row in _sort_created([row for row in _read_jsonl(_path(settings.db_workspace_activity_file)) if row.get("organization_id") == org_id])[:80]]
    totals = {
        "members": len(members),
        "active_members": len([m for m in members if m.status == "active"]),
        "invited_members": len([m for m in members if m.status == "invited"]),
        "projects_visible_to_user": len(projects),
        "saved_scans_visible_to_user": len(scans),
        "saved_reports_visible_to_user": len(reports),
        "finding_tasks": len(tasks),
        "open_tasks": len([t for t in tasks if t.status in {"open", "in_progress", "needs_manual_review"}]),
        "comments": len(comments),
    }
    return WorkspaceOverview(
        organization=org,
        current_user_role=role,
        members=members,
        projects=projects,
        scans=scans,
        reports=reports,
        finding_tasks=tasks,
        comments=comments,
        activity=activities,
        totals=totals,
    )


def workspace_status() -> dict[str, Any]:
    return {
        "version": "1.0",
        "storage_mode": "local_first_supabase_ready",
        "tables_ready": ["organizations", "organization_members", "finding_tasks", "workspace_comments", "workspace_activity"],
        "real_only_note": PHASE72_REAL_ONLY_NOTE,
        "local_counts": {
            "organizations": len(_read_jsonl(_path(settings.db_organizations_file))),
            "members": len(_read_jsonl(_path(settings.db_org_members_file))),
            "finding_tasks": len(_read_jsonl(_path(settings.db_finding_tasks_file))),
            "comments": len(_read_jsonl(_path(settings.db_workspace_comments_file))),
            "activity": len(_read_jsonl(_path(settings.db_workspace_activity_file))),
        },
        "not_connected_yet": ["email invite sending", "real-time collaboration", "paid seat billing", "public registry badge"],
    }
