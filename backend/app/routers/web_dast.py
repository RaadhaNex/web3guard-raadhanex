from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, HttpUrl

from app.services.web_dast import (
    check_ownership_verification,
    light_authorized_scan,
    passive_baseline_scan,
    safe_url_check,
    start_ownership_verification,
    web_dast_claim_check,
    web_dast_status,
)

router = APIRouter(prefix="/web-dast", tags=["web-dast"])


class UrlScopeRequest(BaseModel):
    target_url: str = Field(min_length=4, max_length=500)
    allowed_domains: list[str] = Field(default_factory=list, max_length=25)


class VerificationStartRequest(UrlScopeRequest):
    contact_email: str | None = Field(default=None, max_length=240)
    permission_type: str = Field(default="owner", max_length=80)


class VerificationCheckRequest(VerificationStartRequest):
    method: str = Field(default="manual_proof", max_length=80)
    supplied_token: str | None = Field(default=None, max_length=500)
    proof_text: str | None = Field(default=None, max_length=1000)


class PassiveBaselineRequest(UrlScopeRequest):
    permission_type: str = Field(default="owner", max_length=80)
    authorized_acknowledged: bool = False
    run_live: bool = False


class LightActiveRequest(UrlScopeRequest):
    verification_passed: bool = False
    request_destructive_tests: bool = False


class ClaimCheckRequest(BaseModel):
    text: str = Field(min_length=1, max_length=2000)
    real_only_acknowledged: bool = True


@router.get("/status")
def get_web_dast_status():
    return web_dast_status()


@router.post("/safe-url-check")
def post_safe_url_check(payload: UrlScopeRequest):
    return safe_url_check(payload.model_dump())


@router.post("/verify/start")
def post_verify_start(payload: VerificationStartRequest):
    return start_ownership_verification(payload.model_dump())


@router.post("/verify/check")
def post_verify_check(payload: VerificationCheckRequest):
    return check_ownership_verification(payload.model_dump())


@router.post("/passive-baseline")
def post_passive_baseline(payload: PassiveBaselineRequest):
    return passive_baseline_scan(payload.model_dump())


@router.post("/light-active")
def post_light_active(payload: LightActiveRequest):
    return light_authorized_scan(payload.model_dump())


@router.post("/claim-check")
def post_web_dast_claim_check(payload: ClaimCheckRequest):
    if not payload.real_only_acknowledged:
        raise HTTPException(status_code=400, detail="Real-only acknowledgement is required")
    return web_dast_claim_check(payload.text)
