from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.services.launch_final import (
    deploy_verification_plan,
    public_release_checklist,
    public_release_gates,
    release_claim_check,
    release_status,
    remaining_after_phase30,
    safe_release_notes,
)

router = APIRouter(prefix="/launch-final", tags=["Launch Final QA"])


class ClaimCheckRequest(BaseModel):
    text: str


@router.get("/status")
def status():
    return release_status()


@router.get("/gates")
def gates():
    return {"ok": True, "gates": public_release_gates()}


@router.get("/public-release-checklist")
def checklist():
    return public_release_checklist()


@router.get("/deploy-verification")
def deploy_verification():
    return deploy_verification_plan()


@router.get("/release-notes")
def release_notes():
    return safe_release_notes()


@router.get("/remaining-work")
def remaining_work():
    return remaining_after_phase30()


@router.post("/claim-check")
def claim_check(payload: ClaimCheckRequest):
    return release_claim_check(payload.text)
