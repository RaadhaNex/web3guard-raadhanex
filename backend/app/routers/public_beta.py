from fastapi import APIRouter

from app.services.public_beta_readiness import public_beta_readiness_status

router = APIRouter(prefix="/public-beta", tags=["public-beta"])


@router.get("/readiness")
def public_beta_readiness():
    return public_beta_readiness_status()
