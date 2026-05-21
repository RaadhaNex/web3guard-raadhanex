from __future__ import annotations

from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services.professional_accuracy import (
    accuracy_readiness_summary,
    append_accuracy_feedback,
    calibration_report,
    feedback_summary,
    list_accuracy_feedback,
    run_custom_contract_case,
    run_professional_accuracy_benchmark,
)

router = APIRouter(prefix="/professional-accuracy", tags=["professional-accuracy"])


class CustomContractBenchmarkRequest(BaseModel):
    solidity_code: str = Field(min_length=20, max_length=220000)
    project_name: str | None = Field(default=None, max_length=160)
    expected_rule_ids: list[str] = Field(default_factory=list, max_length=80)
    forbidden_rule_ids: list[str] = Field(default_factory=list, max_length=80)
    authorization_confirmed: bool = True
    real_only_acknowledged: bool = True


class AccuracyFeedbackRequest(BaseModel):
    finding_id: str | None = Field(default=None, max_length=160)
    rule_id: str | None = Field(default=None, max_length=160)
    verdict: Literal["confirmed", "false_positive", "accepted_risk", "fixed", "missed", "needs_evidence"] = "needs_evidence"
    severity: str | None = Field(default=None, max_length=40)
    source: str = Field(default="manual_reviewer", max_length=160)
    evidence: str | None = Field(default=None, max_length=3000)
    notes: str | None = Field(default=None, max_length=3000)
    project_id: str | None = Field(default=None, max_length=160)
    reviewer: str | None = Field(default=None, max_length=160)
    safe_for_training: bool = False
    real_only_acknowledged: bool = True


@router.get("/status")
def status():
    return {
        "ok": True,
        "phase": "Professional Scanner Phase F",
        "engine": "benchmark_false_positive_accuracy_engine",
        "summary": accuracy_readiness_summary(),
        "claim_policy": "Use for scanner improvement and internal QA. Do not claim certified audit equivalence.",
    }


@router.get("/benchmark")
def benchmark():
    return run_professional_accuracy_benchmark()


@router.post("/benchmark/custom")
def custom_benchmark(payload: CustomContractBenchmarkRequest):
    if not payload.authorization_confirmed or not payload.real_only_acknowledged:
        return {
            "ok": False,
            "status": "blocked",
            "reason": "Authorization and real-only acknowledgement are required.",
        }
    return run_custom_contract_case(
        payload.solidity_code,
        expected_rule_ids=payload.expected_rule_ids,
        forbidden_rule_ids=payload.forbidden_rule_ids,
        project_name=payload.project_name,
    )


@router.post("/feedback")
def create_feedback(payload: AccuracyFeedbackRequest):
    if not payload.real_only_acknowledged:
        return {"ok": False, "status": "blocked", "reason": "real_only_acknowledged is required."}
    record = append_accuracy_feedback(payload.model_dump())
    return {"ok": True, "record": record}


@router.get("/feedback")
def feedback(limit: int = 100):
    return {"ok": True, "summary": feedback_summary(limit=limit), "items": list_accuracy_feedback(limit=limit)}


@router.get("/calibration")
def calibration():
    return calibration_report()
