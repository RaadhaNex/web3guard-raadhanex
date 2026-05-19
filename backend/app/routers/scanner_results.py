from __future__ import annotations

from typing import Any, Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.scanner_results import build_pilot_report, evaluate_scanner_results, scanner_results_status

router = APIRouter(prefix="/scanner-results", tags=["scanner-results"])


class ScannerResultsPackage(BaseModel):
    name: str = Field(min_length=1, max_length=220)
    version: str | None = Field(default=None, max_length=120)
    ecosystem: str = Field(default="npm", max_length=60)


class ScannerResultsEvaluateRequest(BaseModel):
    project_name: str | None = Field(default=None, max_length=160)
    solidity_code: str | None = Field(default=None, max_length=180000)
    file_name: str = Field(default="Contract.sol", max_length=160)
    tools: list[Literal["slither", "aderyn", "semgrep"]] = ["slither", "semgrep"]
    run_static_tools: bool = False
    slither_json: str | None = Field(default=None, max_length=350000)
    package_json: str | None = Field(default=None, max_length=260000)
    packages: list[ScannerResultsPackage] = []
    live_dependency_lookup: bool = False
    authorization_confirmed: bool = True
    real_only_acknowledged: bool = True


class PilotReportRequest(BaseModel):
    result: dict[str, Any] = Field(default_factory=dict)
    real_only_acknowledged: bool = True


@router.get("/status")
def phase32_status():
    return scanner_results_status()


@router.post("/evaluate")
async def phase32_evaluate(payload: ScannerResultsEvaluateRequest):
    if not payload.authorization_confirmed:
        raise HTTPException(status_code=400, detail="Authorization confirmation is required")
    if not payload.real_only_acknowledged:
        raise HTTPException(status_code=400, detail="Real-only acknowledgement is required")
    try:
        return await evaluate_scanner_results(
            project_name=payload.project_name,
            solidity_code=payload.solidity_code,
            file_name=payload.file_name,
            tools=list(payload.tools),
            run_static_tools=payload.run_static_tools,
            slither_json=payload.slither_json,
            package_json_text=payload.package_json,
            packages=[item.model_dump() for item in payload.packages],
            live_dependency_lookup=payload.live_dependency_lookup,
            real_only_acknowledged=payload.real_only_acknowledged,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/pilot-report")
def phase32_pilot_report(payload: PilotReportRequest):
    if not payload.real_only_acknowledged:
        raise HTTPException(status_code=400, detail="Real-only acknowledgement is required")
    try:
        return build_pilot_report(payload.result)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
