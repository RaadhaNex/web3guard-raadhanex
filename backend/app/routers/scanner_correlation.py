from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.scanner_correlation import (
    build_attack_path,
    prioritize_findings,
    scanner_correlation_claim_check,
    scanner_correlation_playbook,
    scanner_correlation_status,
)

router = APIRouter(prefix="/scanner-correlation", tags=["scanner-correlation"])


class FindingPayload(BaseModel):
    id: str | None = Field(default=None, max_length=120)
    title: str = Field(default="Untitled finding", max_length=260)
    description: str | None = Field(default=None, max_length=6000)
    severity: str | None = Field(default="info", max_length=40)
    confidence: str | None = Field(default="medium", max_length=40)
    source: str | None = Field(default=None, max_length=120)
    module: str | None = Field(default=None, max_length=120)
    rule_id: str | None = Field(default=None, max_length=160)
    file: str | None = Field(default=None, max_length=260)
    line: int | None = None
    cwe_ids: list[str] = Field(default_factory=list, max_length=30)
    cve_ids: list[str] = Field(default_factory=list, max_length=30)
    tags: list[str] = Field(default_factory=list, max_length=40)
    evidence: str | None = Field(default=None, max_length=8000)
    status: str | None = Field(default=None, max_length=80)
    known_exploited: bool = False
    public_poc: bool = False
    requires_auth: bool = False
    human_review_required: bool = False
    fix_plan: dict[str, Any] | None = None
    impact: str | None = Field(default=None, max_length=4000)
    future_risk: str | None = Field(default=None, max_length=4000)
    verification_steps: list[str] | None = Field(default=None, max_length=20)


class CorrelationRequest(BaseModel):
    project_name: str | None = Field(default=None, max_length=180)
    findings: list[FindingPayload] = Field(default_factory=list, max_length=200)
    assessed_modules: dict[str, bool] = Field(default_factory=dict)
    asset_context: dict[str, Any] = Field(default_factory=dict)
    real_only_acknowledged: bool = True


class ClaimCheckRequest(BaseModel):
    text: str = Field(min_length=1, max_length=2000)
    real_only_acknowledged: bool = True


@router.get("/status")
def get_scanner_correlation_status():
    return scanner_correlation_status()


@router.get("/playbook")
def get_scanner_correlation_playbook():
    return scanner_correlation_playbook()


@router.post("/prioritize")
def post_prioritize_findings(payload: CorrelationRequest):
    if not payload.real_only_acknowledged:
        raise HTTPException(status_code=400, detail="Real-only acknowledgement is required")
    return prioritize_findings(payload.model_dump())


@router.post("/attack-path")
def post_attack_path(payload: CorrelationRequest):
    if not payload.real_only_acknowledged:
        raise HTTPException(status_code=400, detail="Real-only acknowledgement is required")
    return build_attack_path(payload.model_dump())


@router.post("/claim-check")
def post_scanner_correlation_claim_check(payload: ClaimCheckRequest):
    if not payload.real_only_acknowledged:
        raise HTTPException(status_code=400, detail="Real-only acknowledgement is required")
    return scanner_correlation_claim_check(payload.text)
