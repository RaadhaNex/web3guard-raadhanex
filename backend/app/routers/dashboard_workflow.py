from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, Request

from app.services.auth_guard import resolve_user_id
from app.services.dashboard_workflow import build_dashboard_workflow

router = APIRouter(tags=["Web3Guard Dashboard Workflow"])


@router.get("/dashboard-workflow")
def get_dashboard_workflow(
    request: Request,
    user_id: str | None = Query(default=None, max_length=120),
    project_id: str | None = Query(default=None, max_length=120),
):
    """Build real dashboard workflow data from saved records only.

    This endpoint never creates demo timeline events, fake findings, fake trend
    points, or fake report states. Empty arrays mean there is no stored evidence
    yet for the resolved user/project.
    """

    resolved_user_id, auth_context = resolve_user_id(request, user_id)
    workflow = build_dashboard_workflow(resolved_user_id, project_id=project_id)
    if workflow is None:
        raise HTTPException(status_code=404, detail="Project not found for this user")
    return {"auth_context": auth_context, "workflow": workflow}
