from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.services.public_trust_page import build_public_trust_page, list_public_trust_projects, public_trust_status

router = APIRouter(prefix="/public-trust", tags=["public-trust"])


@router.get("/status")
def status():
    return public_trust_status()


@router.get("/projects")
def projects(user_id: str = Query(..., min_length=1), limit: int = Query(default=50, ge=1, le=100)):
    return list_public_trust_projects(user_id=user_id, limit=limit)


@router.get("/project/{project_id}")
def project_trust_page(project_id: str, user_id: str = Query(..., min_length=1)):
    try:
        return build_public_trust_page(user_id=user_id, project_id=project_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
