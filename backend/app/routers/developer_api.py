from fastapi import APIRouter, Header, HTTPException, Query, Request

from app.core.config import settings
from app.models.schemas import ApiKeyCreate, ApiKeyUpdate, DeveloperAuditRequest
from app.services.auth_guard import resolve_user_id
from app.services.developer_api import create_api_key, developer_api_status, list_api_keys, run_developer_audit, update_api_key, verify_api_key
from app.services.rate_limit import enforce_hourly_limit
from app.services.public_registry import verify_report
from app.services.threat_intel import list_threat_intel

router = APIRouter(tags=["Developer API"])


@router.get("/developer-api/status")
def status():
    return developer_api_status()


@router.post("/developer-api/keys")
def create_key(payload: ApiKeyCreate, request: Request):
    user_id, auth_context = resolve_user_id(request, payload.user_id)
    client_host = request.client.host if request.client else "unknown"
    enforce_hourly_limit(f"api-key-create:{client_host}", limit=settings.max_developer_api_key_write_per_hour)
    try:
        key = create_api_key(payload, user_id=user_id)
        return {"ok": True, "auth_context": auth_context, **key}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/developer-api/keys")
def list_keys(request: Request, user_id: str | None = Query(default=None, max_length=120)):
    resolved_user_id, auth_context = resolve_user_id(request, user_id)
    return {"ok": True, "auth_context": auth_context, "keys": list_api_keys(user_id=resolved_user_id)}


@router.patch("/developer-api/keys/{key_id}")
def patch_key(key_id: str, payload: ApiKeyUpdate):
    key = update_api_key(key_id, payload)
    if not key:
        raise HTTPException(status_code=404, detail="API key not found")
    return {"ok": True, "key": key}


def _require_api_key(header_value: str | None, permission: str):
    if not header_value:
        raise HTTPException(status_code=401, detail="X-Web3Guard-API-Key header is required")
    record = verify_api_key(header_value, permission)
    if not record:
        raise HTTPException(status_code=403, detail="Invalid, disabled, or insufficient API key")
    return record


@router.post("/api/v1/audit")
def api_v1_audit(payload: DeveloperAuditRequest, x_web3guard_api_key: str | None = Header(default=None)):
    record = _require_api_key(x_web3guard_api_key, "audit:start")
    try:
        return run_developer_audit(payload, record)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/api/v1/certificate/{public_id}")
def api_v1_certificate(public_id: str, report_hash: str | None = Query(default=None), x_web3guard_api_key: str | None = Header(default=None)):
    _require_api_key(x_web3guard_api_key, "registry:verify")
    return verify_report(public_id, report_hash)


@router.get("/api/v1/threat-feed")
def api_v1_threat_feed(project_type: str | None = Query(default=None), x_web3guard_api_key: str | None = Header(default=None)):
    _require_api_key(x_web3guard_api_key, "threat:read")
    return list_threat_intel(project_type=project_type, limit=20)
