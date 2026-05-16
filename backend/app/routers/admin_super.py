from fastapi import APIRouter, Depends, Query

from app.core.security import require_admin
from app.models.schemas import AdminFeatureFlagUpdate
from app.services.admin_super_panel import admin_super_dashboard, admin_super_status, list_audit_logs, list_feature_flags, system_health_snapshot, upsert_feature_flag

router = APIRouter(prefix="/admin/super", tags=["Admin Super Panel"], dependencies=[Depends(require_admin)])


@router.get("/status")
def status():
    return admin_super_status()


@router.get("/dashboard")
def dashboard():
    return admin_super_dashboard()


@router.get("/feature-flags")
def feature_flags():
    return {"ok": True, "feature_flags": list_feature_flags()}


@router.patch("/feature-flags/{key}")
def patch_feature_flag(key: str, payload: AdminFeatureFlagUpdate):
    return {"ok": True, "feature_flag": upsert_feature_flag(key, payload.enabled, payload.note, actor=payload.actor)}


@router.get("/audit-log")
def audit_log(limit: int = Query(default=100, ge=1, le=500)):
    return {"ok": True, "events": list_audit_logs(limit=limit)}


@router.get("/system-health")
def system_health():
    return system_health_snapshot()
