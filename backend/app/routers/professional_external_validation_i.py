from __future__ import annotations

from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services.professional_external_validation_i import (
    append_reviewer_confirmation,
    direct_competition_readiness_gate,
    external_validation_status,
    ingest_external_case,
    list_external_cases,
    reviewer_consensus,
    run_sanitized_external_suite,
    validate_external_case,
    validate_stored_case,
)

router = APIRouter(prefix="/professional-external-validation", tags=["professional-external-validation"])


class ExternalValidationCaseRequest(BaseModel):
    case_id: str | None = Field(default=None, max_length=120)
    title: str | None = Field(default=None, max_length=220)
    case_type: Literal["vulnerable", "clean", "regression", "external_reference"] = "external_reference"
    family: str = Field(default="custom", max_length=80)
    project_name: str | None = Field(default=None, max_length=160)
    source_label: str | None = Field(default=None, max_length=180)
    source_url: str | None = Field(default=None, max_length=2048)
    solidity_code: str = Field(min_length=20, max_length=260000)
    expected_rule_ids: list[str] = Field(default_factory=list, max_length=120)
    forbidden_rule_ids: list[str] = Field(default_factory=list, max_length=120)
    expected_min_severity: str | None = Field(default=None, max_length=20)
    notes: str | None = Field(default=None, max_length=4000)
    authorization_confirmed: bool = True
    real_only_acknowledged: bool = True


class ExternalCaseIngestRequest(BaseModel):
    case_id: str | None = Field(default=None, max_length=120)
    title: str = Field(default="External validation case", max_length=220)
    case_type: Literal["vulnerable", "clean", "regression", "external_reference"] = "external_reference"
    family: str = Field(default="custom", max_length=80)
    source_label: str | None = Field(default=None, max_length=180)
    source_url: str | None = Field(default=None, max_length=2048)
    solidity_code: str | None = Field(default=None, max_length=260000)
    case_hash: str | None = Field(default=None, max_length=120)
    expected_rule_ids: list[str] = Field(default_factory=list, max_length=120)
    forbidden_rule_ids: list[str] = Field(default_factory=list, max_length=120)
    expected_min_severity: str | None = Field(default=None, max_length=20)
    notes: str | None = Field(default=None, max_length=4000)
    store_code: bool = False
    sanitized_code_confirmed: bool = False
    real_only_acknowledged: bool = True


class ReviewerConfirmationRequest(BaseModel):
    case_id: str | None = Field(default=None, max_length=120)
    finding_id: str | None = Field(default=None, max_length=160)
    rule_id: str | None = Field(default=None, max_length=120)
    title: str | None = Field(default=None, max_length=220)
    category: str | None = Field(default=None, max_length=80)
    family: str | None = Field(default=None, max_length=80)
    reviewer_id: str = Field(default="anonymous_reviewer", max_length=120)
    reviewer_role: str = Field(default="security_reviewer", max_length=120)
    decision: Literal["confirmed", "false_positive", "missed", "fixed", "accepted_risk", "needs_evidence"] = "needs_evidence"
    severity_override: str | None = Field(default=None, max_length=20)
    confidence: Literal["high", "medium", "low"] = "medium"
    review_note: str | None = Field(default=None, max_length=4000)
    evidence_hash: str | None = Field(default=None, max_length=120)
    real_only_acknowledged: bool = True


@router.get("/status")
def status():
    return external_validation_status()


@router.get("/run-sanitized-suite")
def run_sanitized_suite():
    return run_sanitized_external_suite()


@router.post("/validate-case")
def validate_case(payload: ExternalValidationCaseRequest):
    return validate_external_case(payload.model_dump())


@router.post("/cases")
def create_case(payload: ExternalCaseIngestRequest):
    return {"ok": True, "record": ingest_external_case(payload.model_dump())}


@router.get("/cases")
def cases(limit: int = 100):
    return {"ok": True, "items": list_external_cases(limit=limit)}


@router.get("/cases/{case_id}/validate")
def validate_case_by_id(case_id: str):
    return validate_stored_case(case_id)


@router.post("/reviewer-confirmations")
def reviewer_confirmation(payload: ReviewerConfirmationRequest):
    result = append_reviewer_confirmation(payload.model_dump())
    if result.get("ok") is False:
        return result
    return {"ok": True, "record": result}


@router.get("/reviewer-consensus")
def consensus(case_id: str | None = None, limit: int = 1000):
    return reviewer_consensus(case_id=case_id, limit=limit)


@router.get("/direct-competition-gate")
def direct_competition_gate():
    return direct_competition_readiness_gate()
