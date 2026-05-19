from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.risk_intelligence import (
    analyze_risk_intelligence,
    explain_single_finding,
    risk_claim_check,
    risk_intelligence_status,
    risk_taxonomy_map,
)

router = APIRouter(prefix="/risk-intelligence", tags=["risk-intelligence"])


class FindingInput(BaseModel):
    id: str | None = None
    title: str = Field(min_length=1, max_length=240)
    description: str | None = Field(default=None, max_length=3000)
    severity: str | None = Field(default="info", max_length=40)
    status: str | None = Field(default="Assessed", max_length=80)
    module: str | None = Field(default=None, max_length=120)
    source: str | None = Field(default=None, max_length=160)
    rule_id: str | None = Field(default=None, max_length=160)
    confidence: str | None = Field(default=None, max_length=40)
    cwe_ids: list[str] = Field(default_factory=list, max_length=20)
    cve_ids: list[str] = Field(default_factory=list, max_length=20)
    aliases: list[str] = Field(default_factory=list, max_length=30)
    package: str | None = Field(default=None, max_length=160)
    file: str | None = Field(default=None, max_length=260)
    line: int | None = Field(default=None, ge=0, le=5_000_000)
    recommendation: str | None = Field(default=None, max_length=3000)
    impact: str | None = Field(default=None, max_length=3000)
    future_risk: str | None = Field(default=None, max_length=3000)
    exploit_scenario: str | None = Field(default=None, max_length=3000)
    verify_steps: list[str] = Field(default_factory=list, max_length=20)


class RiskAnalysisRequest(BaseModel):
    project_name: str | None = Field(default=None, max_length=180)
    findings: list[FindingInput] = Field(default_factory=list, max_length=250)
    assessed_modules: dict[str, Any] = Field(default_factory=dict)
    real_only_acknowledged: bool = True


class ClaimCheckRequest(BaseModel):
    text: str = Field(min_length=1, max_length=2000)
    real_only_acknowledged: bool = True


@router.get("/status")
def get_risk_intelligence_status():
    return risk_intelligence_status()


@router.get("/taxonomy")
def get_risk_taxonomy_map():
    return risk_taxonomy_map()


@router.post("/analyze")
def post_risk_intelligence_analysis(payload: RiskAnalysisRequest):
    if not payload.real_only_acknowledged:
        raise HTTPException(status_code=400, detail="Real-only acknowledgement is required")
    return analyze_risk_intelligence(payload.model_dump())


@router.post("/finding-impact")
def post_finding_impact(payload: FindingInput):
    return explain_single_finding(payload.model_dump())


@router.post("/claim-check")
def post_risk_claim_check(payload: ClaimCheckRequest):
    if not payload.real_only_acknowledged:
        raise HTTPException(status_code=400, detail="Real-only acknowledgement is required")
    return risk_claim_check(payload.text)
