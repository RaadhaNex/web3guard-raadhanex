from fastapi import APIRouter, HTTPException, Request

from app.core.config import settings
from app.models.schemas import ThreatIntelCreate, ThreatIntelQuery
from app.services.rate_limit import enforce_hourly_limit
from app.services.threat_intel import create_threat_intel_entry, list_threat_intel, threat_intel_status, threat_relevance_for_report

router = APIRouter(prefix="/threat-intel", tags=["threat-intel"])


@router.get("/status")
def status():
    return threat_intel_status()


@router.get("/feed")
def feed(project_type: str | None = None, chain: str | None = None, tags: str | None = None, limit: int = 20):
    tag_list = [item.strip() for item in (tags or "").split(",") if item.strip()]
    return list_threat_intel(project_type=project_type, chain=chain, tags=tag_list, limit=limit)


@router.post("/query")
def query(payload: ThreatIntelQuery):
    return list_threat_intel(project_type=payload.project_type, chain=payload.chain, tags=payload.tags, limit=payload.limit)


@router.post("/admin/entries")
def create_entry(payload: ThreatIntelCreate, request: Request):
    if not payload.real_only_acknowledged:
        raise HTTPException(status_code=400, detail="Real-only acknowledgement is required")
    client_host = request.client.host if request.client else "unknown"
    enforce_hourly_limit(f"threat-intel-admin:{client_host}", limit=settings.max_threat_intel_admin_writes_per_hour)
    try:
        return create_threat_intel_entry(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/relevance")
def relevance(payload: dict):
    findings = payload.get("findings") if isinstance(payload.get("findings"), list) else []
    project_type = payload.get("project_type") if isinstance(payload.get("project_type"), str) else None
    return threat_relevance_for_report(findings=findings, project_type=project_type)
