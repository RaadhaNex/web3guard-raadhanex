from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field

from app.core.config import settings
from app.services.continuous_monitoring import (
    admin_overview,
    continuous_status,
    create_monitoring_config,
    list_alerts,
    list_configs,
    run_due_rechecks,
    run_recheck,
    user_dashboard,
)
from app.services.rate_limit import enforce_hourly_limit

router = APIRouter(prefix="/continuous-monitoring", tags=["continuous-monitoring"])


class ContinuousMonitoringConfigCreate(BaseModel):
    user_id: str = Field(default="local-demo-user", max_length=120)
    project_id: str | None = Field(default=None, max_length=120)
    project_name: str = Field(min_length=2, max_length=160)
    website_url: str | None = Field(default=None, max_length=2048)
    github_repo_url: str | None = Field(default=None, max_length=2048)
    contract_address: str | None = Field(default=None, max_length=120)
    chain: str | None = Field(default="ethereum", max_length=80)
    cadence: Literal["manual", "daily", "weekly", "monthly"] = "manual"
    checks: list[Literal["stale_report", "scan_age", "website_passive", "github_repo_change", "sentinel_alert_queue", "rpc_event_monitoring"]] = [
        "stale_report",
        "scan_age",
        "website_passive",
        "github_repo_change",
        "sentinel_alert_queue",
        "rpc_event_monitoring",
    ]
    alert_channels: list[str] = ["dashboard"]
    authorization_confirmed: bool = False
    real_only_acknowledged: bool = True
    notes: str | None = Field(default=None, max_length=2000)


class ContinuousRecheckRequest(BaseModel):
    config_id: str = Field(min_length=4, max_length=120)
    user_id: str | None = Field(default=None, max_length=120)
    force: bool = True
    real_only_acknowledged: bool = True


class DueRecheckRequest(BaseModel):
    limit: int = Field(default=10, ge=1, le=25)
    real_only_acknowledged: bool = True


@router.get("/status")
def status():
    return continuous_status()


@router.get("/configs")
def configs(user_id: str | None = None):
    return {"ok": True, "configs": list_configs(user_id=user_id)}


@router.post("/configs")
def create_config(payload: ContinuousMonitoringConfigCreate, request: Request):
    if not payload.authorization_confirmed:
        raise HTTPException(status_code=400, detail="Authorization confirmation is required before continuous monitoring config creation")
    if not payload.real_only_acknowledged:
        raise HTTPException(status_code=400, detail="Real-only acknowledgement is required")
    client_host = request.client.host if request.client else "unknown"
    enforce_hourly_limit(f"continuous-monitoring-config:{client_host}", limit=getattr(settings, "max_continuous_monitoring_config_per_hour", 20))
    return create_monitoring_config(payload)


@router.get("/alerts")
def alerts(user_id: str | None = None, config_id: str | None = None, limit: int = Query(default=100, ge=1, le=250)):
    return {"ok": True, "alerts": list_alerts(user_id=user_id, config_id=config_id, limit=limit)}


@router.get("/user")
def user(user_id: str = "local-demo-user"):
    return user_dashboard(user_id)


@router.get("/admin")
def admin():
    return admin_overview()


@router.post("/recheck")
def recheck(payload: ContinuousRecheckRequest, request: Request):
    if not payload.real_only_acknowledged:
        raise HTTPException(status_code=400, detail="Real-only acknowledgement is required")
    client_host = request.client.host if request.client else "unknown"
    enforce_hourly_limit(f"continuous-monitoring-recheck:{client_host}", limit=getattr(settings, "max_continuous_monitoring_recheck_per_hour", 20))
    try:
        return run_recheck(payload.config_id, user_id=payload.user_id, force=payload.force)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/recheck-due")
def recheck_due(payload: DueRecheckRequest):
    if not payload.real_only_acknowledged:
        raise HTTPException(status_code=400, detail="Real-only acknowledgement is required")
    return run_due_rechecks(limit=payload.limit)
