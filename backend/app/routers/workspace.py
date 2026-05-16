
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, Request

from app.models.schemas import (
    FindingTaskCreate,
    FindingTaskUpdate,
    OrganizationCreate,
    OrganizationMemberInvite,
    OrganizationMemberUpdate,
    OrganizationUpdate,
    WorkspaceCommentCreate,
)
from app.services.auth_guard import resolve_user_id
from app.services.workspace_store import (
    PHASE72_REAL_ONLY_NOTE,
    add_comment,
    create_organization,
    create_task,
    invite_member,
    list_comments,
    list_members,
    list_organizations,
    list_tasks,
    update_member,
    update_organization,
    update_task,
    workspace_overview,
    workspace_status,
)

router = APIRouter(tags=["Web3Guard Organization + Team Workspace"])


@router.get("/workspace/status")
def get_workspace_status():
    return workspace_status()


@router.post("/organizations")
def create_organization_record(request: Request, payload: OrganizationCreate):
    resolved_user_id, auth_context = resolve_user_id(request, payload.user_id)
    organization = create_organization(resolved_user_id, payload)
    return {"ok": True, "auth_context": auth_context, "organization": organization, "real_only_note": PHASE72_REAL_ONLY_NOTE}


@router.get("/organizations")
def list_organization_records(request: Request, user_id: str | None = Query(default=None, max_length=120), limit: int = Query(default=25, ge=1, le=100)):
    resolved_user_id, auth_context = resolve_user_id(request, user_id)
    organizations = list_organizations(resolved_user_id, limit=limit)
    return {"ok": True, "auth_context": auth_context, "organizations": organizations}


@router.get("/organizations/{organization_id}")
def get_workspace_record(request: Request, organization_id: str, user_id: str | None = Query(default=None, max_length=120)):
    resolved_user_id, auth_context = resolve_user_id(request, user_id)
    overview = workspace_overview(resolved_user_id, organization_id)
    if overview is None:
        raise HTTPException(status_code=404, detail="Organization workspace not found for this user")
    return {"ok": True, "auth_context": auth_context, "workspace": overview}


@router.patch("/organizations/{organization_id}")
def update_organization_record(request: Request, organization_id: str, payload: OrganizationUpdate, user_id: str | None = Query(default=None, max_length=120)):
    resolved_user_id, auth_context = resolve_user_id(request, user_id)
    organization = update_organization(resolved_user_id, organization_id, payload)
    if organization is None:
        raise HTTPException(status_code=403, detail="Only workspace owner/admin can update this organization")
    return {"ok": True, "auth_context": auth_context, "organization": organization}


@router.post("/organizations/{organization_id}/members")
def invite_member_record(request: Request, organization_id: str, payload: OrganizationMemberInvite, user_id: str | None = Query(default=None, max_length=120)):
    resolved_user_id, auth_context = resolve_user_id(request, user_id)
    member = invite_member(resolved_user_id, organization_id, payload)
    if member is None:
        raise HTTPException(status_code=403, detail="Only workspace owner/admin can save member invite records")
    return {"ok": True, "auth_context": auth_context, "member": member, "real_only_note": PHASE72_REAL_ONLY_NOTE}


@router.get("/organizations/{organization_id}/members")
def list_member_records(request: Request, organization_id: str, user_id: str | None = Query(default=None, max_length=120)):
    resolved_user_id, auth_context = resolve_user_id(request, user_id)
    members = list_members(resolved_user_id, organization_id)
    if members is None:
        raise HTTPException(status_code=404, detail="Organization workspace not found for this user")
    return {"ok": True, "auth_context": auth_context, "members": members}


@router.patch("/organizations/{organization_id}/members/{member_id}")
def update_member_record(request: Request, organization_id: str, member_id: str, payload: OrganizationMemberUpdate, user_id: str | None = Query(default=None, max_length=120)):
    resolved_user_id, auth_context = resolve_user_id(request, user_id)
    member = update_member(resolved_user_id, organization_id, member_id, payload)
    if member is None:
        raise HTTPException(status_code=403, detail="Only workspace owner/admin can update member records")
    return {"ok": True, "auth_context": auth_context, "member": member}


@router.post("/workspace/finding-tasks")
def create_finding_task_record(request: Request, payload: FindingTaskCreate):
    resolved_user_id, auth_context = resolve_user_id(request, payload.user_id)
    task = create_task(resolved_user_id, payload)
    if task is None:
        raise HTTPException(status_code=403, detail="You must be a workspace member to create finding tasks")
    return {"ok": True, "auth_context": auth_context, "task": task}


@router.get("/workspace/finding-tasks")
def list_finding_task_records(request: Request, organization_id: str = Query(min_length=2, max_length=120), project_id: str | None = Query(default=None, max_length=120), user_id: str | None = Query(default=None, max_length=120)):
    resolved_user_id, auth_context = resolve_user_id(request, user_id)
    tasks = list_tasks(resolved_user_id, organization_id, project_id=project_id)
    if tasks is None:
        raise HTTPException(status_code=404, detail="Organization workspace not found for this user")
    return {"ok": True, "auth_context": auth_context, "tasks": tasks}


@router.patch("/workspace/finding-tasks/{task_id}")
def update_finding_task_record(request: Request, task_id: str, payload: FindingTaskUpdate, organization_id: str = Query(min_length=2, max_length=120), user_id: str | None = Query(default=None, max_length=120)):
    resolved_user_id, auth_context = resolve_user_id(request, user_id)
    task = update_task(resolved_user_id, organization_id, task_id, payload)
    if task is None:
        raise HTTPException(status_code=403, detail="You must be a workspace member to update finding tasks")
    return {"ok": True, "auth_context": auth_context, "task": task}


@router.post("/workspace/comments")
def create_workspace_comment_record(request: Request, payload: WorkspaceCommentCreate):
    resolved_user_id, auth_context = resolve_user_id(request, payload.user_id)
    comment = add_comment(resolved_user_id, payload)
    if comment is None:
        raise HTTPException(status_code=403, detail="You must be a workspace member to comment")
    return {"ok": True, "auth_context": auth_context, "comment": comment}


@router.get("/workspace/comments")
def list_workspace_comment_records(request: Request, organization_id: str = Query(min_length=2, max_length=120), project_id: str | None = Query(default=None, max_length=120), user_id: str | None = Query(default=None, max_length=120)):
    resolved_user_id, auth_context = resolve_user_id(request, user_id)
    comments = list_comments(resolved_user_id, organization_id, project_id=project_id)
    if comments is None:
        raise HTTPException(status_code=404, detail="Organization workspace not found for this user")
    return {"ok": True, "auth_context": auth_context, "comments": comments}
