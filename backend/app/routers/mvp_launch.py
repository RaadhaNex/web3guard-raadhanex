from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from app.services import mvp_launch

router = APIRouter(prefix="/mvp-launch", tags=["Phase 36 - MVP Launch Pack"])


class ClaimCheckPayload(BaseModel):
    text: str = Field(..., min_length=1, max_length=2000)


class PilotUserPayload(BaseModel):
    project_name: str = Field(default="Unnamed pilot project", max_length=120)
    founder_segment: str = Field(default="web3 founder", max_length=100)
    source_channel: str = Field(default="manual outreach", max_length=100)
    stage: str = Field(default="contacted", max_length=80)
    paid_intent: str = Field(default="unknown", max_length=80)
    highest_friction: str = Field(default="not recorded", max_length=240)
    next_action: str = Field(default="book review", max_length=240)
    safe_contact_note: str | None = Field(default=None, max_length=240)


@router.get("/status")
def status() -> dict[str, Any]:
    return mvp_launch.get_status()


@router.get("/launch-checklist")
def launch_checklist() -> dict[str, Any]:
    return mvp_launch.get_launch_checklist()


@router.get("/outreach-kit")
def outreach_kit() -> dict[str, Any]:
    return mvp_launch.get_outreach_kit()


@router.get("/sample-report")
def sample_report() -> dict[str, Any]:
    return mvp_launch.get_sample_report_template()


@router.get("/public-beta-checklist")
def public_beta_checklist() -> dict[str, Any]:
    return mvp_launch.get_public_beta_checklist()


@router.get("/claim-guidance")
def claim_guidance() -> dict[str, Any]:
    return mvp_launch.get_claim_guidance()


@router.post("/claim-check")
def claim_check(payload: ClaimCheckPayload) -> dict[str, Any]:
    return mvp_launch.check_claim_text(payload.text)


@router.get("/first-10")
def first_10(limit: int = Query(default=10, ge=1, le=50)) -> dict[str, Any]:
    return mvp_launch.list_pilot_users(limit=limit)


@router.post("/first-10")
def add_first_10(payload: PilotUserPayload) -> dict[str, Any]:
    return mvp_launch.add_pilot_user(payload.model_dump())
