from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.security import require_admin
from app.services.security_hardening import data_retention_policy, log_security_event, platform_boundary_matrix, recent_security_events, security_headers_policy, security_status

router = APIRouter(prefix="/security", tags=["Mega Phase G - Security Hardening"])


class SecurityEventCreate(BaseModel):
    event_type: str = "manual_review"
    actor: str = "admin"
    note: str


@router.get("/status")
def status():
    return security_status()


@router.get("/headers-policy")
def headers_policy():
    return security_headers_policy()


@router.get("/data-retention")
def data_retention():
    return data_retention_policy()


@router.get("/boundaries")
def boundaries():
    return platform_boundary_matrix()


@router.post("/events", dependencies=[Depends(require_admin)])
def create_event(payload: SecurityEventCreate):
    return {"ok": True, "event": log_security_event(payload.event_type, payload.actor, payload.note)}


@router.get("/events", dependencies=[Depends(require_admin)])
def events():
    return {"ok": True, "events": recent_security_events()}


alias_router = APIRouter(prefix="/security-hardening", tags=["Mega Phase G - Security Hardening Alias"])

@alias_router.get("/status")
def alias_status():
    return security_status()

@alias_router.get("/headers-policy")
def alias_headers_policy():
    return security_headers_policy()

@alias_router.get("/data-retention")
def alias_data_retention():
    return data_retention_policy()

@alias_router.get("/boundaries")
def alias_boundaries():
    return platform_boundary_matrix()
