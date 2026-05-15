from fastapi import APIRouter, Query, Request

from app.models.schemas import ComplianceScanRequest
from app.services.auth_guard import resolve_user_id
from app.services.compliance_scanner import compliance_status, list_compliance_scans, run_compliance_scan

router = APIRouter(tags=["Mega Phase F - Compliance Scanner"])


@router.get("/compliance/status")
def status():
    return compliance_status()


@router.post("/compliance/scan")
def scan(payload: ComplianceScanRequest, request: Request):
    user_id, auth_context = resolve_user_id(request, payload.user_id)
    return {"ok": True, "auth_context": auth_context, "report": run_compliance_scan(payload, user_id)}


@router.get("/compliance/scans")
def scans(limit: int = Query(default=50, ge=1, le=200)):
    return {"ok": True, "scans": list_compliance_scans(limit=limit)}
