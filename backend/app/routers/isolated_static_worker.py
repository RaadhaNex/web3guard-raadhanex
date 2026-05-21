from __future__ import annotations

from fastapi import APIRouter

from app.services.isolated_static_worker import isolated_static_worker_status

router = APIRouter(prefix="/professional/static-worker", tags=["isolated-static-worker"])


@router.get("/status")
def status():
    return isolated_static_worker_status()
