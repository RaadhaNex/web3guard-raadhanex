from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.scanner_depth import (
    evaluate_scanner_depth,
    scanner_depth_claim_check,
    scanner_depth_roadmap,
    scanner_depth_status,
)

router = APIRouter(prefix="/scanner-depth", tags=["scanner-depth"])


class ScannerDepthCoverageRequest(BaseModel):
    project_name: str | None = Field(default=None, max_length=180)
    slither_assessed: bool = False
    aderyn_assessed: bool = False
    semgrep_assessed: bool = False
    osv_checked: bool = False
    cisa_checked: bool = False
    github_checked: bool = False
    website_checked: bool = False
    api_checked: bool = False
    wallet_ux_checked: bool = False
    admin_opsec_checked: bool = False
    foundry_tests_run: bool = False
    echidna_run: bool = False
    mythril_run: bool = False
    evidence_items_count: int = Field(default=0, ge=0, le=500)
    report_hash: str | None = Field(default=None, max_length=128)
    critical_findings: int = Field(default=0, ge=0, le=200)
    high_findings: int = Field(default=0, ge=0, le=500)
    real_only_acknowledged: bool = True


class ClaimCheckRequest(BaseModel):
    text: str = Field(min_length=1, max_length=2000)
    real_only_acknowledged: bool = True


@router.get("/status")
def get_scanner_depth_status():
    return scanner_depth_status()


@router.get("/roadmap")
def get_scanner_depth_roadmap():
    return scanner_depth_roadmap()


@router.post("/coverage")
def post_scanner_depth_coverage(payload: ScannerDepthCoverageRequest):
    if not payload.real_only_acknowledged:
        raise HTTPException(status_code=400, detail="Real-only acknowledgement is required")
    return evaluate_scanner_depth(payload.model_dump())


@router.post("/claim-check")
def post_scanner_depth_claim_check(payload: ClaimCheckRequest):
    if not payload.real_only_acknowledged:
        raise HTTPException(status_code=400, detail="Real-only acknowledgement is required")
    return scanner_depth_claim_check(payload.text)
