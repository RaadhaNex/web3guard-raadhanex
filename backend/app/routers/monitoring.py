from fastapi import APIRouter, HTTPException, Request

from app.core.config import settings
from app.models.schemas import MonitoringAlertIngest, MonitoringCheckRequest, MonitoringConfigCreate
from app.services.monitoring_lite import (
    create_monitoring_config,
    ingest_monitoring_alert,
    list_monitoring_alerts,
    list_monitoring_configs,
    monitoring_dashboard_summary,
    monitoring_status,
    run_rpc_monitoring_check,
)
from app.services.rate_limit import enforce_hourly_limit

router = APIRouter(prefix="/monitoring", tags=["monitoring"])


@router.get("/status")
def status():
    return monitoring_status()


@router.get("/dashboard")
def dashboard():
    return monitoring_dashboard_summary()


@router.post("/configs")
def create_config(payload: MonitoringConfigCreate, request: Request):
    if not payload.authorization_confirmed:
        raise HTTPException(status_code=400, detail="Authorization confirmation is required")
    if not payload.real_only_acknowledged:
        raise HTTPException(status_code=400, detail="Real-only acknowledgement is required")
    client_host = request.client.host if request.client else "unknown"
    enforce_hourly_limit(f"monitoring-config:{client_host}", limit=settings.max_monitoring_config_per_hour)
    try:
        return create_monitoring_config(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/configs")
def list_configs():
    return {"ok": True, "configs": list_monitoring_configs()}


@router.get("/alerts")
def list_alerts(config_id: str | None = None, limit: int = 100):
    return {"ok": True, "alerts": list_monitoring_alerts(config_id=config_id, limit=limit)}


@router.post("/alerts/ingest")
def ingest_alert(payload: MonitoringAlertIngest):
    if not payload.real_only_acknowledged:
        raise HTTPException(status_code=400, detail="Real-only acknowledgement is required")
    try:
        return ingest_monitoring_alert(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/check")
def check_monitoring(payload: MonitoringCheckRequest, request: Request):
    if not payload.real_only_acknowledged:
        raise HTTPException(status_code=400, detail="Real-only acknowledgement is required")
    client_host = request.client.host if request.client else "unknown"
    enforce_hourly_limit(f"monitoring-check:{client_host}", limit=settings.max_monitoring_check_per_hour)
    try:
        return run_rpc_monitoring_check(payload.config_id, payload.from_block, payload.to_block)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
