from fastapi import APIRouter, HTTPException, Query, Request

from app.core.config import settings
from app.models.schemas import RegistryPublicationCreate, RegistryStatusUpdate
from app.services.auth_guard import resolve_user_id
from app.services.public_registry import create_publication, get_publication, list_publications, registry_status, update_publication_status, verify_report
from app.services.rate_limit import enforce_hourly_limit

router = APIRouter(prefix="/registry", tags=["Public Registry"])


@router.get("/status")
def status():
    return registry_status()


@router.post("/publications")
def create_registry_publication(payload: RegistryPublicationCreate, request: Request):
    user_id, auth_context = resolve_user_id(request, payload.user_id)
    client_host = request.client.host if request.client else "unknown"
    enforce_hourly_limit(f"registry-write:{client_host}", limit=settings.max_registry_write_per_hour)
    try:
        publication = create_publication(payload, user_id=user_id)
        return {"ok": True, "auth_context": auth_context, "publication": publication}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/publications")
def get_registry_publications(status: str | None = Query(default=None), limit: int = Query(default=100, ge=1, le=200)):
    return {"ok": True, "publications": list_publications(status=status, limit=limit)}


@router.get("/publications/{public_id}")
def get_registry_publication(public_id: str):
    publication = get_publication(public_id)
    if not publication:
        raise HTTPException(status_code=404, detail="Public report record not found")
    return {"ok": True, "publication": publication}


@router.patch("/publications/{public_id}/status")
def patch_registry_status(public_id: str, payload: RegistryStatusUpdate):
    publication = update_publication_status(public_id, payload)
    if not publication:
        raise HTTPException(status_code=404, detail="Public report record not found")
    return {"ok": True, "publication": publication}


@router.get("/verify/{public_id}")
def verify_registry_record(public_id: str, report_hash: str | None = Query(default=None)):
    return verify_report(public_id, report_hash)
