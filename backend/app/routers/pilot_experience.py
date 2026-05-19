from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services import pilot_experience

router = APIRouter(prefix="/pilot-experience", tags=["Phase 35 - Pilot Experience"])


class FeedbackPayload(BaseModel):
    page_path: str = Field(default="/unknown", max_length=180)
    role: str = Field(default="founder", max_length=80)
    friction_area: str = Field(default="general", max_length=120)
    message: str = Field(..., min_length=1, max_length=1500)
    contact_email: str | None = Field(default=None, max_length=180)
    can_contact: bool = False


class ClaimCheckPayload(BaseModel):
    text: str = Field(..., min_length=1, max_length=2000)


@router.get("/status")
def status() -> dict[str, Any]:
    return pilot_experience.get_status()


@router.get("/journey")
def journey() -> dict[str, Any]:
    return pilot_experience.get_journey()


@router.get("/state-copy")
def state_copy() -> dict[str, Any]:
    return pilot_experience.get_state_copy()


@router.get("/conversion-checklist")
def conversion_checklist() -> dict[str, Any]:
    return pilot_experience.get_conversion_checklist()


@router.post("/feedback")
def feedback(payload: FeedbackPayload) -> dict[str, Any]:
    return pilot_experience.submit_feedback(payload.model_dump())


@router.post("/claim-check")
def claim_check(payload: ClaimCheckPayload) -> dict[str, Any]:
    return pilot_experience.check_claim_text(payload.text)
