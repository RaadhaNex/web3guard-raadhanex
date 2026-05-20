from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.services.manual_review import (
    add_review_note,
    board,
    client_summary_template,
    create_request,
    decide_report,
    import_findings,
    list_findings,
    list_notes,
    list_requests,
    methodology,
    status,
    triage_finding,
)

router = APIRouter(prefix="/manual-review", tags=["manual-review"])


class ReviewRequestPayload(BaseModel):
    user_id: str = Field(default="local-demo-user", min_length=1, max_length=160)
    project_id: str | None = Field(default=None, max_length=160)
    scan_id: str | None = Field(default=None, max_length=160)
    report_id: str | None = Field(default=None, max_length=160)
    project_name: str = Field(default="Manual review project", min_length=3, max_length=180)
    project_url: str | None = Field(default=None, max_length=500)
    review_type: str = Field(default="pre_audit_readiness", max_length=80)
    priority: str = Field(default="medium", max_length=40)
    scope_summary: str = Field(default="", max_length=1600)
    evidence_sources: list[str] = Field(default_factory=list)
    authorized_scope_confirmed: bool = False
    payment_status: str = Field(default="not_verified", max_length=80)


class ImportFindingsPayload(BaseModel):
    request_id: str | None = Field(default=None, max_length=180)
    user_id: str = Field(default="local-demo-user", min_length=1, max_length=160)
    project_id: str | None = Field(default=None, max_length=160)
    scan_payload: dict[str, Any] = Field(default_factory=dict)
    manual_findings: list[dict[str, Any]] = Field(default_factory=list)


class TriagePayload(BaseModel):
    finding_id: str = Field(..., min_length=4, max_length=180)
    status: str = Field(default="needs_triage", max_length=80)
    reviewer: str = Field(default="Manual reviewer", max_length=160)
    reviewer_note: str = Field(default="", max_length=2000)
    severity: str | None = Field(default=None, max_length=40)
    severity_override_reason: str = Field(default="", max_length=1000)
    confirmed_evidence_note: str = Field(default="", max_length=2000)


class ReviewNotePayload(BaseModel):
    request_id: str | None = Field(default=None, max_length=180)
    finding_id: str | None = Field(default=None, max_length=180)
    user_id: str = Field(default="local-demo-user", max_length=160)
    reviewer: str = Field(default="Manual reviewer", max_length=160)
    visibility: str = Field(default="internal", max_length=80)
    note: str = Field(..., min_length=8, max_length=3000)


class ReportDecisionPayload(BaseModel):
    request_id: str = Field(..., min_length=4, max_length=180)
    decision: str = Field(default="not_ready", max_length=80)
    reviewer: str = Field(default="Manual reviewer", max_length=160)
    reviewer_reason: str = Field(..., min_length=12, max_length=2000)
    payment_verified: bool = False


class SummaryPayload(BaseModel):
    request_id: str | None = Field(default=None, max_length=180)
    project_name: str = Field(default="your Web3 project", max_length=180)


@router.get("/status")
def get_status() -> dict[str, Any]:
    return status()


@router.get("/methodology")
def get_methodology() -> dict[str, Any]:
    return methodology()


@router.post("/requests")
def post_request(payload: ReviewRequestPayload) -> dict[str, Any]:
    return create_request(payload.model_dump())


@router.get("/requests")
def get_requests(
    user_id: str | None = None,
    project_id: str | None = None,
    status_value: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=100, ge=1, le=200),
) -> dict[str, Any]:
    return list_requests(user_id=user_id, project_id=project_id, status_value=status_value, limit=limit)


@router.post("/findings/import")
def post_import_findings(payload: ImportFindingsPayload) -> dict[str, Any]:
    return import_findings(payload.model_dump())


@router.get("/findings")
def get_findings(
    request_id: str | None = None,
    user_id: str | None = None,
    project_id: str | None = None,
    status_value: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=200, ge=1, le=500),
) -> dict[str, Any]:
    return list_findings(request_id=request_id, user_id=user_id, project_id=project_id, status_value=status_value, limit=limit)


@router.post("/findings/triage")
def post_triage(payload: TriagePayload) -> dict[str, Any]:
    try:
        return triage_finding(payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/notes")
def post_note(payload: ReviewNotePayload) -> dict[str, Any]:
    try:
        return add_review_note(payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/notes")
def get_notes(request_id: str | None = None, finding_id: str | None = None, limit: int = Query(default=200, ge=1, le=500)) -> dict[str, Any]:
    return list_notes(request_id=request_id, finding_id=finding_id, limit=limit)


@router.post("/reports/decision")
def post_report_decision(payload: ReportDecisionPayload) -> dict[str, Any]:
    try:
        return decide_report(payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/board")
def get_board(user_id: str | None = None, project_id: str | None = None) -> dict[str, Any]:
    return board(user_id=user_id, project_id=project_id)


@router.post("/templates/client-summary")
def post_client_summary(payload: SummaryPayload) -> dict[str, Any]:
    return client_summary_template(payload.model_dump())
