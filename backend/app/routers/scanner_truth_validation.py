from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.scanner_truth_validation import (
    scanner_truth_sample_plan,
    scanner_truth_validation_status,
    validate_scanner_truth,
)

router = APIRouter(prefix="/scanner-truth", tags=["scanner-truth-validation"])


class ScannerTruthValidationRequest(BaseModel):
    project_name: str | None = Field(default=None, max_length=180)
    unified_scan_result: dict[str, Any] = Field(default_factory=dict)
    real_only_acknowledged: bool = True


@router.get("/status")
def get_scanner_truth_status():
    return scanner_truth_validation_status()


@router.get("/sample-plan")
def get_scanner_truth_sample_plan():
    return scanner_truth_sample_plan()


@router.post("/validate")
def post_validate_scanner_truth(payload: ScannerTruthValidationRequest):
    if not payload.real_only_acknowledged:
        raise HTTPException(status_code=400, detail="Real-only acknowledgement is required")
    try:
        return validate_scanner_truth(payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
