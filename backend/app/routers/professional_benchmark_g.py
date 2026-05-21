from __future__ import annotations

from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services.professional_benchmark_g import (
    append_regression_case,
    dataset_catalog,
    list_regression_cases,
    phase_g_readiness_summary,
    run_custom_real_world_case,
    run_real_world_benchmark,
)

router = APIRouter(prefix="/professional-benchmark", tags=["professional-benchmark"])


class CustomPhaseGBenchmarkRequest(BaseModel):
    solidity_code: str = Field(min_length=20, max_length=220000)
    expected_rule_ids: list[str] = Field(default_factory=list, max_length=100)
    forbidden_rule_ids: list[str] = Field(default_factory=list, max_length=100)
    family: str = Field(default="custom", max_length=80)
    authorization_confirmed: bool = True
    real_only_acknowledged: bool = True


class RegressionCaseRequest(BaseModel):
    title: str = Field(default="Custom regression case", max_length=180)
    case_class: Literal["vulnerable", "clean", "regression"] = "regression"
    family: str = Field(default="custom", max_length=80)
    solidity_code: str = Field(default="", max_length=220000)
    expected_rule_ids: list[str] = Field(default_factory=list, max_length=100)
    forbidden_rule_ids: list[str] = Field(default_factory=list, max_length=100)
    notes: str | None = Field(default=None, max_length=3000)
    store_code: bool = False
    sanitized_code_confirmed: bool = False
    real_only_acknowledged: bool = True


@router.get("/status")
def status():
    return {
        "ok": True,
        "phase": "Professional Scanner Phase G",
        "engine": "real_world_style_benchmark_and_rule_tuning_pack",
        "summary": phase_g_readiness_summary(),
        "claim_policy": "Internal scanner calibration only. Not a certified audit or public parity claim.",
    }


@router.get("/dataset")
def dataset():
    return dataset_catalog()


@router.get("/run")
def run():
    return run_real_world_benchmark()


@router.get("/tuning-pack")
def tuning_pack():
    result = run_real_world_benchmark()
    return {
        "ok": True,
        "phase": result.get("phase"),
        "benchmark_id": result.get("benchmark_id"),
        "quality_gate": result.get("quality_gate"),
        "family_metrics": result.get("family_metrics"),
        "tuning_pack": result.get("tuning_pack"),
        "blocked_claim": result.get("blocked_claim"),
    }


@router.post("/custom-case")
def custom_case(payload: CustomPhaseGBenchmarkRequest):
    if not payload.authorization_confirmed or not payload.real_only_acknowledged:
        return {"ok": False, "status": "blocked", "reason": "Authorization and real-only acknowledgement are required."}
    return run_custom_real_world_case(
        payload.solidity_code,
        expected_rule_ids=payload.expected_rule_ids,
        forbidden_rule_ids=payload.forbidden_rule_ids,
        family=payload.family,
    )


@router.post("/regression-cases")
def create_regression_case(payload: RegressionCaseRequest):
    if not payload.real_only_acknowledged:
        return {"ok": False, "status": "blocked", "reason": "real_only_acknowledged is required."}
    if payload.store_code and not payload.sanitized_code_confirmed:
        return {"ok": False, "status": "blocked", "reason": "sanitized_code_confirmed is required before storing code."}
    record = append_regression_case(payload.model_dump())
    return {"ok": True, "record": record}


@router.get("/regression-cases")
def regression_cases(limit: int = 100):
    return {"ok": True, "items": list_regression_cases(limit=limit)}
