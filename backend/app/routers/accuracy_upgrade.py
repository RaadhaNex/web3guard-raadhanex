from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services.accuracy_upgrade import (
    accuracy_stack_status,
    build_business_logic_review,
    build_reviewed_report_confirmation,
    run_authorized_api_evidence_runner,
    run_defi_simulation_framework,
    run_dependency_osv_engine,
    run_static_worker_bridge,
    run_wallet_ux_evidence_engine,
)

router = APIRouter(prefix="/accuracy-upgrade", tags=["accuracy-upgrade"])


class DependencyEvidenceRequest(BaseModel):
    package_json: str | None = Field(default=None, max_length=800000)
    requirements_txt: str | None = Field(default=None, max_length=500000)
    manifests: list[dict[str, Any]] = Field(default_factory=list)


class StaticWorkerRequest(BaseModel):
    solidity_code: str | None = Field(default=None, max_length=220000)
    project_name: str | None = Field(default=None, max_length=160)


class ApiEvidenceRequest(BaseModel):
    api_base_url: str | None = Field(default=None, max_length=2048)
    observations: list[dict[str, Any]] = Field(default_factory=list)
    openapi_json: str | None = Field(default=None, max_length=500000)
    authorization_confirmed: bool = True
    real_only_acknowledged: bool = True


class WalletEvidenceRequest(BaseModel):
    wallet_evidence: dict[str, Any] = Field(default_factory=dict)
    signature_samples: list[dict[str, Any]] = Field(default_factory=list)
    transaction_samples: list[dict[str, Any]] = Field(default_factory=list)
    authorization_confirmed: bool = True
    real_only_acknowledged: bool = True


class BusinessLogicRequest(BaseModel):
    business_context: dict[str, Any] = Field(default_factory=dict)
    authorization_confirmed: bool = True
    real_only_acknowledged: bool = True


class DefiSimulationRequest(BaseModel):
    simulation_result: dict[str, Any] = Field(default_factory=dict)
    protocol_context: dict[str, Any] = Field(default_factory=dict)
    authorization_confirmed: bool = True
    real_only_acknowledged: bool = True


class ReviewedConfirmationRequest(BaseModel):
    review_context: dict[str, Any] = Field(default_factory=dict)
    real_only_acknowledged: bool = True


@router.get("/status")
def status() -> dict[str, Any]:
    return accuracy_stack_status()


@router.post("/dependency-osv")
async def dependency_osv(payload: DependencyEvidenceRequest) -> dict[str, Any]:
    return await run_dependency_osv_engine(
        package_json=payload.package_json,
        requirements_txt=payload.requirements_txt,
        manifests=payload.manifests,
    )


@router.post("/static-worker")
def static_worker(payload: StaticWorkerRequest) -> dict[str, Any]:
    return run_static_worker_bridge(payload.solidity_code, payload.project_name)


@router.post("/api-evidence")
def api_evidence(payload: ApiEvidenceRequest) -> dict[str, Any]:
    if not payload.authorization_confirmed:
        return {"state": "Blocked", "reason": "Authorization must be confirmed before API evidence can be evaluated."}
    return run_authorized_api_evidence_runner(payload.api_base_url, payload.observations, payload.openapi_json)


@router.post("/wallet-evidence")
def wallet_evidence(payload: WalletEvidenceRequest) -> dict[str, Any]:
    if not payload.authorization_confirmed:
        return {"state": "Blocked", "reason": "Authorization must be confirmed before wallet-flow evidence can be evaluated."}
    return run_wallet_ux_evidence_engine(payload.wallet_evidence, payload.signature_samples, payload.transaction_samples)


@router.post("/business-logic")
def business_logic(payload: BusinessLogicRequest) -> dict[str, Any]:
    if not payload.authorization_confirmed:
        return {"state": "Blocked", "reason": "Authorization must be confirmed before business-logic evidence can be evaluated."}
    return build_business_logic_review(payload.business_context)


@router.post("/defi-simulation")
def defi_simulation(payload: DefiSimulationRequest) -> dict[str, Any]:
    if not payload.authorization_confirmed:
        return {"state": "Blocked", "reason": "Authorization must be confirmed before DeFi simulation evidence can be evaluated."}
    return run_defi_simulation_framework(payload.simulation_result, payload.protocol_context)


@router.post("/reviewed-confirmation")
def reviewed_confirmation(payload: ReviewedConfirmationRequest) -> dict[str, Any]:
    return build_reviewed_report_confirmation(payload.review_context)
