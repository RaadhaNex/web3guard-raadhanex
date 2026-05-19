from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.launch_validation import (
    dependency_intelligence,
    launch_validation_status,
    razorpay_readiness,
    slither_render_readiness,
    visible_journey,
)

router = APIRouter(prefix="/launch-validation", tags=["launch-validation"])


class DependencyPackage(BaseModel):
    name: str = Field(min_length=1, max_length=220)
    version: str | None = Field(default=None, max_length=120)
    ecosystem: str = Field(default="npm", max_length=60)


class DependencyIntelRequest(BaseModel):
    package_json: str | None = Field(default=None, max_length=260000)
    packages: list[DependencyPackage] = []
    live_lookup: bool = False
    real_only_acknowledged: bool = True
    limit: int = Field(default=40, ge=1, le=100)


@router.get("/status")
def phase31_status():
    return launch_validation_status()


@router.get("/visible-journey")
def phase31_visible_journey():
    return visible_journey()


@router.get("/slither-readiness")
def phase31_slither_readiness():
    return slither_render_readiness()


@router.get("/razorpay-readiness")
def phase31_razorpay_readiness():
    return razorpay_readiness()


@router.post("/dependency-intel")
async def phase31_dependency_intel(payload: DependencyIntelRequest):
    try:
        return await dependency_intelligence(
            package_json_text=payload.package_json,
            packages=[item.model_dump() for item in payload.packages],
            live_lookup=payload.live_lookup,
            real_only_acknowledged=payload.real_only_acknowledged,
            limit=payload.limit,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
