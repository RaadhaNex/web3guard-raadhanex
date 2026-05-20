from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services.accuracy_hardening import (
    accuracy_hardening_status,
    benchmark_scanner_accuracy,
    build_accuracy_hardening_package,
    build_trust_proof_pack,
    parse_formal_fuzz_artifacts,
    tune_false_positive_policy,
    validate_authenticated_api_test_plan,
    validate_defi_invariant_plan,
)

router = APIRouter(prefix="/accuracy-hardening", tags=["accuracy-hardening"])


class BenchmarkRequest(BaseModel):
    samples: list[dict[str, Any]] = Field(default_factory=list)


class FalsePositiveRequest(BaseModel):
    triaged_findings: list[dict[str, Any]] = Field(default_factory=list)


class FormalFuzzArtifactRequest(BaseModel):
    foundry_json: str | None = Field(default=None, max_length=900000)
    echidna_json: str | None = Field(default=None, max_length=900000)
    invariant_results: list[dict[str, Any]] = Field(default_factory=list)


class ApiHarnessRequest(BaseModel):
    plan: dict[str, Any] = Field(default_factory=dict)
    observations: list[dict[str, Any]] = Field(default_factory=list)
    authorization_confirmed: bool = True


class DefiInvariantRequest(BaseModel):
    protocol_context: dict[str, Any] = Field(default_factory=dict)
    invariant_catalog: list[dict[str, Any]] = Field(default_factory=list)


class TrustProofRequest(BaseModel):
    case_studies: list[dict[str, Any]] = Field(default_factory=list)
    sample_reports: list[dict[str, Any]] = Field(default_factory=list)
    claims: list[str] = Field(default_factory=list)


class AccuracyHardeningPackageRequest(BaseModel):
    payload: dict[str, Any] = Field(default_factory=dict)


@router.get("/status")
def status() -> dict[str, Any]:
    return accuracy_hardening_status()


@router.post("/benchmark")
def benchmark(payload: BenchmarkRequest) -> dict[str, Any]:
    return benchmark_scanner_accuracy(payload.samples)


@router.post("/false-positive-tuning")
def false_positive_tuning(payload: FalsePositiveRequest) -> dict[str, Any]:
    return tune_false_positive_policy(payload.triaged_findings)


@router.post("/formal-fuzz-artifact")
def formal_fuzz_artifact(payload: FormalFuzzArtifactRequest) -> dict[str, Any]:
    return parse_formal_fuzz_artifacts(
        foundry_json=payload.foundry_json,
        echidna_json=payload.echidna_json,
        invariant_results=payload.invariant_results,
    )


@router.post("/api-harness")
def api_harness(payload: ApiHarnessRequest) -> dict[str, Any]:
    if not payload.authorization_confirmed:
        return {"state": "Blocked", "reason": "Authorization must be confirmed before API evidence is evaluated."}
    return validate_authenticated_api_test_plan(payload.plan, payload.observations)


@router.post("/defi-invariants")
def defi_invariants(payload: DefiInvariantRequest) -> dict[str, Any]:
    return validate_defi_invariant_plan(payload.protocol_context, payload.invariant_catalog)


@router.post("/trust-proof-pack")
def trust_proof_pack(payload: TrustProofRequest) -> dict[str, Any]:
    return build_trust_proof_pack(payload.case_studies, payload.sample_reports, payload.claims)


@router.post("/package")
def package(payload: AccuracyHardeningPackageRequest) -> dict[str, Any]:
    return build_accuracy_hardening_package(payload.payload)
