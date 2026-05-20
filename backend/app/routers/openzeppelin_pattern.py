from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.openzeppelin_pattern import (
    analyze_openzeppelin_patterns,
    openzeppelin_claim_check,
    openzeppelin_pattern_status,
    openzeppelin_rule_catalog,
)

router = APIRouter(prefix="/openzeppelin-pattern", tags=["openzeppelin-pattern"])


class SourceFile(BaseModel):
    path: str = Field(default="contracts/Contract.sol", max_length=260)
    content: str = Field(default="", max_length=120_000)


class OpenZeppelinPatternRequest(BaseModel):
    project_name: str | None = Field(default=None, max_length=180)
    contract_source: str | None = Field(default=None, max_length=250_000)
    imports: list[str] = Field(default_factory=list, max_length=120)
    file_names: list[str] = Field(default_factory=list, max_length=120)
    files: list[SourceFile] = Field(default_factory=list, max_length=30)
    readme: str | None = Field(default=None, max_length=20_000)
    notes: str | None = Field(default=None, max_length=10_000)
    real_only_acknowledged: bool = True


class ClaimCheckRequest(BaseModel):
    text: str = Field(min_length=1, max_length=2000)
    real_only_acknowledged: bool = True


@router.get("/status")
def get_openzeppelin_pattern_status():
    return openzeppelin_pattern_status()


@router.get("/rules")
def get_openzeppelin_pattern_rules():
    return openzeppelin_rule_catalog()


@router.post("/analyze")
def post_openzeppelin_pattern_analysis(payload: OpenZeppelinPatternRequest):
    if not payload.real_only_acknowledged:
        raise HTTPException(status_code=400, detail="Real-only acknowledgement is required")
    return analyze_openzeppelin_patterns(payload.model_dump())


@router.post("/claim-check")
def post_openzeppelin_pattern_claim_check(payload: ClaimCheckRequest):
    if not payload.real_only_acknowledged:
        raise HTTPException(status_code=400, detail="Real-only acknowledgement is required")
    return openzeppelin_claim_check(payload.text)
