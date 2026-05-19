from __future__ import annotations

from fastapi import APIRouter, Query

from app.services.trust_readiness import build_trust_readiness, trust_readiness_status

router = APIRouter(prefix="/trust-readiness", tags=["trust-readiness"])


@router.get("/status")
def status():
    return trust_readiness_status()


@router.get("/score")
def score(user_id: str = Query(..., min_length=1), project_id: str | None = None):
    return build_trust_readiness(user_id=user_id, project_id=project_id)
