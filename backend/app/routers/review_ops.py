from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.services.review_ops import (
    admin_board,
    approve_reviewed_report,
    create_assignment,
    list_assignments,
    list_fix_verifications,
    public_proof_from_reviewed,
    record_fix_verification,
    report_readiness,
    status,
)

router = APIRouter(prefix="/review-ops", tags=["review-ops"])


class AssignmentPayload(BaseModel):
    request_id: str = Field(..., min_length=4, max_length=180)
    reviewer: str = Field(..., min_length=2, max_length=160)
    role: str = Field(default="lead_reviewer", max_length=80)
    assigned_by: str = Field(default="RAADHANEX admin", max_length=160)
    scope_summary: str = Field(default="", max_length=1200)
    due_date: str | None = Field(default=None, max_length=80)


class FixVerificationPayload(BaseModel):
    finding_id: str = Field(..., min_length=4, max_length=180)
    request_id: str | None = Field(default=None, max_length=180)
    reviewer: str = Field(default="Manual reviewer", max_length=160)
    status: str = Field(default="fix_submitted", max_length=80)
    fix_summary: str = Field(default="", max_length=1600)
    evidence: dict[str, Any] = Field(default_factory=dict)
    test_commands: list[str] = Field(default_factory=list)
    reviewer_note: str = Field(default="", max_length=2200)


class ReviewedReportPayload(BaseModel):
    request_id: str = Field(..., min_length=4, max_length=180)
    decision: str = Field(default="needs_more_evidence", max_length=80)
    reviewer: str = Field(default="Manual reviewer", max_length=160)
    reviewer_reason: str = Field(..., min_length=12, max_length=2400)
    report_hash: str | None = Field(default=None, max_length=160)
    report_id: str | None = Field(default=None, max_length=180)
    scan_id: str | None = Field(default=None, max_length=180)
    report_payload: dict[str, Any] = Field(default_factory=dict)


class PublishReviewedPayload(ReviewedReportPayload):
    publish: bool = False
    visibility: str = Field(default="public", max_length=40)


@router.get("/status")
def get_status() -> dict[str, Any]:
    return status()


@router.post("/assignments")
def post_assignment(payload: AssignmentPayload) -> dict[str, Any]:
    try:
        return create_assignment(payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/assignments")
def get_assignments(
    request_id: str | None = None,
    reviewer: str | None = None,
    status_value: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=100, ge=1, le=500),
) -> dict[str, Any]:
    return list_assignments(request_id=request_id, reviewer=reviewer, status_value=status_value, limit=limit)


@router.post("/fix-verifications")
def post_fix_verification(payload: FixVerificationPayload) -> dict[str, Any]:
    try:
        return record_fix_verification(payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/fix-verifications")
def get_fix_verifications(
    request_id: str | None = None,
    finding_id: str | None = None,
    status_value: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=200, ge=1, le=500),
) -> dict[str, Any]:
    return list_fix_verifications(request_id=request_id, finding_id=finding_id, status_value=status_value, limit=limit)


@router.get("/report-readiness")
def get_report_readiness(request_id: str = Query(..., min_length=4, max_length=180)) -> dict[str, Any]:
    return report_readiness(request_id)


@router.post("/reports/approve-reviewed")
def post_approve_reviewed(payload: ReviewedReportPayload) -> dict[str, Any]:
    try:
        return approve_reviewed_report(payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/public-proof/from-reviewed")
def post_public_proof_from_reviewed(payload: PublishReviewedPayload) -> dict[str, Any]:
    try:
        return public_proof_from_reviewed(payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/admin-board")
def get_admin_board(user_id: str | None = None, project_id: str | None = None) -> dict[str, Any]:
    return admin_board(user_id=user_id, project_id=project_id)
