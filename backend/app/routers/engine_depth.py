from fastapi import APIRouter

from app.services.engine_depth import engine_depth_status

router = APIRouter(prefix="/engine-depth", tags=["engine-depth"])


@router.get("/status")
def get_engine_depth_status():
    return engine_depth_status()
