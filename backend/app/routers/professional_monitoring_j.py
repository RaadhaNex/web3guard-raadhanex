from __future__ import annotations

from typing import Any, Literal

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.services import professional_monitoring_j as monitoring

router = APIRouter(prefix="/professional-monitoring", tags=["professional-monitoring"])


class BaselineCreateRequest(BaseModel):
    user_id: str = Field(default="local-demo-user", max_length=120)
    project_id: str | None = Field(default=None, max_length=120)
    project_name: str = Field(default="Monitored project", max_length=180)
    baseline_type: Literal["post_review", "public_proof", "launch_baseline", "manual"] = "post_review"
    cadence: Literal["manual", "daily", "weekly", "monthly"] = "manual"
    approved_report_id: str | None = Field(default=None, max_length=160)
    proof_id: str | None = Field(default=None, max_length=160)
    scope: dict[str, Any] = Field(default_factory=dict)
    baseline_evidence: dict[str, Any] = Field(default_factory=dict)
    authorization_confirmed: bool = False
    real_only_acknowledged: bool = True


class CompareRequest(BaseModel):
    baseline_id: str = Field(min_length=4, max_length=160)
    user_id: str | None = Field(default=None, max_length=120)
    current_evidence: dict[str, Any] = Field(default_factory=dict)
    real_only_acknowledged: bool = True


class AcknowledgeEventRequest(BaseModel):
    status: Literal["acknowledged", "resolved", "accepted_risk", "false_positive", "open"] = "acknowledged"
    reviewer: str | None = Field(default=None, max_length=160)
    note: str | None = Field(default=None, max_length=2000)


@router.get("/status")
def status():
    return monitoring.status()


@router.post("/baselines")
def create_baseline(payload: BaselineCreateRequest):
    try:
        return {"ok": True, "baseline": monitoring.create_baseline(payload)}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/baselines")
def list_baselines(user_id: str | None = None, status: str | None = None):
    return {"ok": True, "baselines": monitoring.list_baselines(user_id=user_id, status=status)}


@router.get("/baselines/{baseline_id}")
def get_baseline(baseline_id: str, user_id: str | None = None):
    baseline = monitoring.get_baseline(baseline_id, user_id=user_id)
    if not baseline:
        raise HTTPException(status_code=404, detail="Professional monitoring baseline not found")
    return {"ok": True, "baseline": baseline}


@router.post("/compare")
def compare(payload: CompareRequest):
    try:
        return monitoring.compare_to_baseline(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/events")
def events(
    user_id: str | None = None,
    baseline_id: str | None = None,
    status: str | None = None,
    limit: int = Query(default=100, ge=1, le=250),
):
    return {"ok": True, "events": monitoring.list_events(user_id=user_id, baseline_id=baseline_id, status=status, limit=limit)}


@router.post("/events/{event_id}/acknowledge")
def acknowledge(event_id: str, payload: AcknowledgeEventRequest):
    try:
        return {"ok": True, "event": monitoring.acknowledge_event(event_id, status=payload.status, reviewer=payload.reviewer, note=payload.note)}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/readiness")
def readiness():
    return monitoring.readiness()
