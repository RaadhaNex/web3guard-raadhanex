from fastapi import APIRouter

from app.services.provider_readiness import provider_readiness_status

router = APIRouter(prefix="/provider-readiness", tags=["provider-readiness"])


@router.get("/status")
def get_provider_readiness_status():
    return provider_readiness_status()
