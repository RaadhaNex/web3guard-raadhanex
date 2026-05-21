from __future__ import annotations

from pydantic import BaseModel, Field
from fastapi import APIRouter

from app.services.formal_fuzz_artifacts import (
    analyze_formal_fuzz_artifacts,
    formal_fuzz_not_assessed_summary,
    formal_fuzz_summary_from_report,
    parse_echidna_output,
    parse_foundry_output,
    parse_invariant_artifact,
)

router = APIRouter(prefix="/formal-fuzz-artifacts", tags=["formal-fuzz-artifacts"])


class FormalFuzzArtifactRequest(BaseModel):
    project_name: str | None = Field(default=None, max_length=160)
    foundry_test_output: str | None = Field(default=None, max_length=900000)
    echidna_output_json: str | None = Field(default=None, max_length=1000000)
    invariant_artifact_json: str | None = Field(default=None, max_length=1000000)
    defi_simulation_json: str | None = Field(default=None, max_length=1000000)
    real_only_acknowledged: bool = True


@router.get("/status")
def status() -> dict:
    return {
        "ok": True,
        "engine": "web3guard-formal-fuzz-artifact-engine-v1",
        "execution_mode": "artifact_parser_only",
        "accepted_inputs": ["foundry_test_output", "echidna_output_json", "invariant_artifact_json", "defi_simulation_json"],
        "not_claimed": [
            "No server-side forge test execution in this endpoint.",
            "No server-side Echidna execution in this endpoint.",
            "No exploit automation, wallet signing, or private key collection.",
            "Not a certified audit or complete formal verification proof.",
        ],
        "missing_evidence_state": formal_fuzz_not_assessed_summary(),
    }


@router.post("/parse")
def parse(payload: FormalFuzzArtifactRequest) -> dict:
    report = analyze_formal_fuzz_artifacts(
        foundry_test_output=payload.foundry_test_output,
        echidna_output_json=payload.echidna_output_json,
        invariant_artifact_json=payload.invariant_artifact_json,
        defi_simulation_json=payload.defi_simulation_json,
        project_name=payload.project_name,
    )
    return formal_fuzz_summary_from_report(report)


@router.post("/preview")
def preview(payload: FormalFuzzArtifactRequest) -> dict:
    foundry_findings, foundry_status = parse_foundry_output(payload.foundry_test_output)
    echidna_findings, echidna_status = parse_echidna_output(payload.echidna_output_json)
    invariant_findings, invariant_status = parse_invariant_artifact(payload.invariant_artifact_json or payload.defi_simulation_json)
    return {
        "foundry": {"status": foundry_status, "finding_count": len(foundry_findings)},
        "echidna": {"status": echidna_status, "finding_count": len(echidna_findings)},
        "invariant_artifact": {"status": invariant_status, "finding_count": len(invariant_findings)},
        "real_only_note": "Preview counts are derived only from supplied artifacts. Missing inputs stay Not Assessed.",
    }
