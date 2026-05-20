from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services.real_findings_pipeline import ENGINE_VERSION, PHASE, build_real_findings_pipeline

router = APIRouter(prefix="/findings-pipeline", tags=["real-findings-pipeline"])


class FindingsPipelineValidateRequest(BaseModel):
    scan_payload: dict[str, Any] = Field(default_factory=dict)


@router.get("/status")
def findings_pipeline_status() -> dict[str, Any]:
    return {
        "ok": True,
        "phase": PHASE,
        "engine_version": ENGINE_VERSION,
        "purpose": "Validate that real scanner/tool output is normalized, mapped to Results/Report/export, and not replaced by fake scores or fake findings.",
        "checks": [
            "module_cards evidence mapping",
            "Slither/Semgrep tool-state vs real finding count",
            "combined_report/report_hash export gate",
            "blocked audit/security claim wording",
            "tool-status messages separated from vulnerability findings",
        ],
        "not_claimed": [
            "No certified audit",
            "No 100% secure claim",
            "No fake Slither/Semgrep findings",
            "No fake report export unlock",
            "No exploit automation",
        ],
    }


@router.post("/validate")
def validate_findings_pipeline(payload: FindingsPipelineValidateRequest) -> dict[str, Any]:
    return build_real_findings_pipeline(payload.scan_payload)
