from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.services.community_review import (
    admin_overview,
    community_review_status,
    create_review_request,
    list_feedback,
    list_review_requests,
    list_triage,
    project_board,
    responsible_review_template,
    submit_feedback,
    update_triage,
)

router = APIRouter(prefix="/community-review", tags=["community-review"])


class ReviewRequestPayload(BaseModel):
    user_id: str = Field(default="local-demo-user", min_length=1, max_length=160)
    project_id: str | None = Field(default=None, max_length=160)
    title: str = Field(..., min_length=4, max_length=180)
    project_url: str | None = Field(default=None, max_length=500)
    repo_url: str | None = Field(default=None, max_length=500)
    scope_summary: str = Field(default="", max_length=1200)
    focus_areas: list[str] = Field(default_factory=list)
    review_type: str = Field(default="pre_audit_readiness", max_length=80)
    priority: str = Field(default="medium", max_length=40)
    public_feedback_enabled: bool = False
    authorized_scope_confirmed: bool = False


class FeedbackPayload(BaseModel):
    request_id: str | None = Field(default=None, max_length=180)
    user_id: str = Field(default="local-demo-user", min_length=1, max_length=160)
    project_id: str | None = Field(default=None, max_length=160)
    reviewer_display_name: str = Field(default="Community reviewer", max_length=120)
    summary: str = Field(..., min_length=8, max_length=1000)
    evidence_note: str = Field(default="", max_length=1200)
    severity: str = Field(default="info", max_length=40)
    safe_feedback_acknowledged: bool = False


class TriagePayload(BaseModel):
    request_id: str | None = Field(default=None, max_length=180)
    feedback_id: str | None = Field(default=None, max_length=180)
    user_id: str = Field(default="local-demo-user", min_length=1, max_length=160)
    project_id: str | None = Field(default=None, max_length=160)
    status: str = Field(default="validating_scope", max_length=80)
    severity: str = Field(default="info", max_length=40)
    summary: str = Field(default="Triage event", max_length=1000)
    next_step: str = Field(default="Continue manual validation.", max_length=1000)
    assigned_to: str | None = Field(default=None, max_length=120)


class TemplatePayload(BaseModel):
    project_name: str = Field(default="your Web3 project", max_length=160)
    scope_summary: str = Field(default="the supplied launch-readiness scope", max_length=600)
    contact: str = Field(default="project team", max_length=160)


@router.get("/status")
def status() -> dict[str, Any]:
    return community_review_status()


@router.post("/requests")
def create_request(payload: ReviewRequestPayload) -> dict[str, Any]:
    try:
        return create_review_request(payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/requests")
def requests(
    user_id: str | None = None,
    project_id: str | None = None,
    status: str | None = None,
    limit: int = Query(default=100, ge=1, le=200),
) -> dict[str, Any]:
    return list_review_requests(user_id=user_id, project_id=project_id, status=status, limit=limit)


@router.post("/feedback")
def feedback(payload: FeedbackPayload) -> dict[str, Any]:
    try:
        return submit_feedback(payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/feedback")
def feedback_list(
    user_id: str | None = None,
    project_id: str | None = None,
    request_id: str | None = None,
    status: str | None = None,
    limit: int = Query(default=100, ge=1, le=200),
) -> dict[str, Any]:
    return list_feedback(user_id=user_id, project_id=project_id, request_id=request_id, status=status, limit=limit)


@router.post("/triage")
def triage(payload: TriagePayload) -> dict[str, Any]:
    try:
        return update_triage(payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/triage")
def triage_list(
    user_id: str | None = None,
    project_id: str | None = None,
    request_id: str | None = None,
    limit: int = Query(default=100, ge=1, le=200),
) -> dict[str, Any]:
    return list_triage(user_id=user_id, project_id=project_id, request_id=request_id, limit=limit)


@router.get("/project-board")
def board(user_id: str = Query(default="local-demo-user", min_length=1), project_id: str | None = None) -> dict[str, Any]:
    return project_board(user_id=user_id, project_id=project_id)


@router.get("/admin/overview")
def admin() -> dict[str, Any]:
    return admin_overview()


@router.post("/templates/responsible-review")
def template(payload: TemplatePayload) -> dict[str, Any]:
    return responsible_review_template(payload.model_dump())
