from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field

from app.services.auth_guard import resolve_user_id
from app.services.securescore import (
    list_findings,
    project_scorecard,
    scan_scorecard,
    securescore_overview,
    securescore_status,
    update_finding_workflow,
)

router = APIRouter(tags=["Web3Guard SecureScore Pro"])


class FindingWorkflowUpdate(BaseModel):
    scan_id: str = Field(min_length=2, max_length=160)
    status: str = Field(min_length=2, max_length=40)
    notes: str | None = Field(default=None, max_length=2000)
    assigned_to: str | None = Field(default=None, max_length=160)


@router.get("/securescore/status")
def get_securescore_status():
    return securescore_status()


@router.get("/securescore/overview")
def get_securescore_overview(request: Request, user_id: str | None = Query(default=None, max_length=120)):
    resolved_user_id, auth_context = resolve_user_id(request, user_id)
    return {"ok": True, "auth_context": auth_context, "overview": securescore_overview(resolved_user_id)}


@router.get("/securescore/project/{project_id}")
def get_project_securescore(request: Request, project_id: str, user_id: str | None = Query(default=None, max_length=120)):
    resolved_user_id, auth_context = resolve_user_id(request, user_id)
    scorecard = project_scorecard(resolved_user_id, project_id)
    if scorecard is None:
        raise HTTPException(status_code=404, detail="Project not found for this user")
    return {"ok": True, "auth_context": auth_context, "scorecard": scorecard}


@router.get("/securescore/scan/{scan_id}")
def get_scan_securescore(request: Request, scan_id: str, user_id: str | None = Query(default=None, max_length=120)):
    resolved_user_id, auth_context = resolve_user_id(request, user_id)
    scorecard = scan_scorecard(resolved_user_id, scan_id)
    if scorecard is None:
        raise HTTPException(status_code=404, detail="Scan not found for this user")
    return {"ok": True, "auth_context": auth_context, "scorecard": scorecard}


@router.get("/findings")
def get_findings(
    request: Request,
    user_id: str | None = Query(default=None, max_length=120),
    project_id: str | None = Query(default=None, max_length=120),
    module: str | None = Query(default=None, max_length=80),
    severity: str | None = Query(default=None, max_length=20),
    status: str | None = Query(default=None, max_length=40),
    limit: int = Query(default=100, ge=1, le=500),
):
    resolved_user_id, auth_context = resolve_user_id(request, user_id)
    findings = list_findings(resolved_user_id, project_id=project_id, module=module, severity=severity, status=status, limit=limit)
    return {"ok": True, "auth_context": auth_context, "findings": findings}


@router.patch("/findings/{finding_id}/workflow")
def patch_finding_workflow(
    request: Request,
    finding_id: str,
    payload: FindingWorkflowUpdate,
    user_id: str | None = Query(default=None, max_length=120),
):
    resolved_user_id, auth_context = resolve_user_id(request, user_id)
    try:
        record = update_finding_workflow(
            resolved_user_id,
            scan_id=payload.scan_id,
            finding_id=finding_id,
            status=payload.status,
            notes=payload.notes,
            assigned_to=payload.assigned_to,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404 if "not found" in str(exc).lower() else 400, detail=str(exc)) from exc
    return {"ok": True, "auth_context": auth_context, "workflow": record}
