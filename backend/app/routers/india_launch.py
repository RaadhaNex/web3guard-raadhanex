from __future__ import annotations

from fastapi import APIRouter, Query

from app.services.india_launch import build_india_launch_pack, india_launch_status

router = APIRouter(prefix="/india-launch", tags=["india-launch"])


@router.get("/status")
def status():
    return india_launch_status()


@router.get("/pack")
def pack(
    user_id: str = Query(..., min_length=1),
    project_id: str | None = None,
    mode: str = Query(default="hinglish", pattern="^(english|hinglish|hindi)$"),
):
    return build_india_launch_pack(user_id=user_id, project_id=project_id, mode=mode)
