from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.services.security_passport import (
    add_external_link,
    build_security_passport,
    list_passport_projects,
    security_passport_admin_overview,
    security_passport_status,
)

router = APIRouter(prefix="/security-passport", tags=["security-passport"])


class ExternalLinkPayload(BaseModel):
    user_id: str
    project_id: str
    title: str
    url: str
    link_type: str = "other"
    notes: str | None = None


@router.get("/status")
def status():
    return security_passport_status()


@router.get("/projects")
def projects(user_id: str = Query(..., min_length=1), limit: int = Query(50, ge=1, le=100)):
    return list_passport_projects(user_id=user_id, limit=limit)


@router.get("/project/{project_id}")
def project_passport(project_id: str, user_id: str = Query(..., min_length=1)):
    data = build_security_passport(user_id=user_id, project_id=project_id)
    if not data.get("ok"):
        raise HTTPException(status_code=404, detail=data.get("error") or "Project not found")
    return data


@router.get("/admin/overview")
def admin_overview():
    return security_passport_admin_overview()


@router.post("/external-links")
def external_links(payload: ExternalLinkPayload):
    try:
        return add_external_link(payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
