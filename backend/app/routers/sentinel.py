from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Header, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.config import settings
from app.services.sentinel import (
    admin_overview,
    build_project_alerts,
    disclosure_draft,
    ingest_intelligence,
    list_intelligence,
    sentinel_sources,
    sentinel_status,
)

router = APIRouter(prefix="/sentinel", tags=["sentinel"])


class SentinelIngestRequest(BaseModel):
    source: str = Field(..., min_length=2, max_length=80)
    records: list[dict[str, Any]] = Field(default_factory=list)
    imported_by: str | None = Field(default=None, max_length=120)
    real_only_acknowledged: bool = False


class SentinelDisclosureDraftRequest(BaseModel):
    target: str | None = Field(default=None, max_length=160)
    contact: str | None = Field(default=None, max_length=180)
    finding_summary: str = Field(..., min_length=8, max_length=700)
    evidence_summary: str = Field(..., min_length=8, max_length=700)
    confidence: str = Field(default="needs_manual_validation", max_length=80)
    real_only_acknowledged: bool = False


@router.get("/status")
def status():
    return sentinel_status()


@router.get("/sources")
def sources():
    return sentinel_sources()


@router.get("/intelligence")
def intelligence(
    source: str | None = None,
    severity: str | None = None,
    query: str | None = None,
    limit: int = Query(default=50, ge=1, le=100),
):
    return list_intelligence(source=source, severity=severity, query=query, limit=limit)


@router.post("/intelligence/ingest")
def ingest(payload: SentinelIngestRequest, x_admin_token: str | None = Header(default=None)):
    if x_admin_token != settings.admin_token:
        raise HTTPException(status_code=403, detail="Admin token is required for Sentinel intelligence ingestion")
    try:
        return ingest_intelligence(
            source=payload.source,
            records=payload.records,
            real_only_acknowledged=payload.real_only_acknowledged,
            imported_by=payload.imported_by,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/project-alerts")
def project_alerts(user_id: str, project_id: str | None = None):
    return build_project_alerts(user_id=user_id, project_id=project_id)


@router.get("/admin/overview")
def admin(user_id: str | None = None):
    return admin_overview(user_id=user_id)


@router.post("/disclosure/draft")
def disclosure(payload: SentinelDisclosureDraftRequest):
    try:
        return disclosure_draft(payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
