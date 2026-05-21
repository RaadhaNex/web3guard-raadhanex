from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.services import professional_ops_n_to_s as ops

router = APIRouter(prefix="/professional-ops", tags=["professional-ops-n-to-s"])


class WorkerRunRequest(BaseModel):
    runner: str = Field(default="foundry", max_length=40)
    files: list[dict[str, Any]] = Field(default_factory=list)
    source: str | None = Field(default=None, max_length=240)
    authorization_confirmed: bool = False
    real_only_acknowledged: bool = True


class ReviewerCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    email: str | None = Field(default=None, max_length=240)
    role: str = Field(default="security_reviewer", max_length=80)
    status: str = Field(default="invited", max_length=80)
    capabilities: list[str] = Field(default_factory=list)
    years_experience: int = Field(default=0, ge=0, le=80)
    identity_verified: bool = False
    nda_signed: bool = False
    conflict_check_completed: bool = False
    sample_review_completed: bool = False
    quality_score: int = Field(default=0, ge=0, le=100)
    notes: str | None = Field(default=None, max_length=1200)


class ReviewerUpdateRequest(BaseModel):
    status: str = Field(default="screening", max_length=80)
    identity_verified: bool | None = None
    nda_signed: bool | None = None
    conflict_check_completed: bool | None = None
    sample_review_completed: bool | None = None
    quality_score: int | None = Field(default=None, ge=0, le=100)
    notes: str | None = Field(default=None, max_length=1200)


class DeliveryCreateRequest(BaseModel):
    client_name: str = Field(min_length=2, max_length=180)
    client_email: str | None = Field(default=None, max_length=240)
    project_name: str = Field(min_length=2, max_length=180)
    report_id: str | None = Field(default=None, max_length=180)
    proof_id: str | None = Field(default=None, max_length=160)
    summary: str | None = Field(default=None, max_length=2200)
    included_artifacts: list[Any] = Field(default_factory=list)
    report_payload: dict[str, Any] = Field(default_factory=dict)
    status: str = Field(default="draft", max_length=80)


class DeliveryStatusRequest(BaseModel):
    status: str = Field(default="client_viewed", max_length=80)
    client_note: str | None = Field(default=None, max_length=1800)


@router.get("/status")
def status():
    return ops.phase_status()


@router.get("/monitoring-dashboard")
def monitoring_dashboard():
    return ops.monitoring_dashboard()


@router.get("/github-webhook/setup")
def github_webhook_setup():
    return ops.github_webhook_setup_status()


@router.get("/onchain-webhook/setup")
def onchain_webhook_setup():
    return ops.onchain_webhook_setup_status()


@router.get("/worker/status")
def worker_status():
    return ops.worker_tool_status()


@router.post("/worker/run")
def worker_run(payload: WorkerRunRequest):
    try:
        return ops.run_worker(payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/worker/runs")
def worker_runs(limit: int = Query(default=100, ge=1, le=250)):
    return ops.list_worker_runs(limit=limit)


@router.post("/reviewers")
def create_reviewer(payload: ReviewerCreateRequest):
    try:
        return ops.create_reviewer_profile(payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/reviewers")
def reviewers(status: str | None = None, limit: int = Query(default=100, ge=1, le=250)):
    return ops.list_reviewer_profiles(status=status, limit=limit)


@router.post("/reviewers/{reviewer_id}/status")
def update_reviewer(reviewer_id: str, payload: ReviewerUpdateRequest):
    try:
        return ops.update_reviewer_status(reviewer_id, payload.model_dump(exclude_none=True))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/deliveries")
def create_delivery(payload: DeliveryCreateRequest):
    try:
        return ops.create_delivery(payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/deliveries")
def deliveries(status: str | None = None, limit: int = Query(default=100, ge=1, le=250)):
    return ops.list_deliveries(status=status, limit=limit)


@router.post("/deliveries/{delivery_id}/status")
def update_delivery(delivery_id: str, payload: DeliveryStatusRequest):
    try:
        return ops.update_delivery_status(delivery_id, payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/deliveries/{delivery_id}/verify")
def verify_delivery(delivery_id: str, integrity_hash: str | None = None):
    try:
        return ops.verify_delivery(delivery_id, integrity_hash=integrity_hash)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/deliveries/{delivery_id}/public")
def delivery_public(delivery_id: str):
    try:
        return ops.delivery_public_summary(delivery_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
