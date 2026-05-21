from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.services.public_proof_report import (
    approve_public_proof,
    build_public_proof_draft,
    get_public_proof,
    list_public_proofs,
    publish_public_proof,
    revoke_public_proof,
    status,
    verify_public_proof,
)

router = APIRouter(prefix="/proof-reports", tags=["proof-reports"])


class ProofDraftPayload(BaseModel):
    project_name: str | None = Field(default=None, max_length=180)
    source: str = Field(default="scanner_report_payload", max_length=120)
    scan_id: str | None = Field(default=None, max_length=180)
    report_id: str | None = Field(default=None, max_length=180)
    report_hash: str | None = Field(default=None, max_length=180)
    report: dict[str, Any] = Field(default_factory=dict)
    scan_payload: dict[str, Any] = Field(default_factory=dict)
    requested_public_claim: str | None = Field(default=None, max_length=500)
    custom_summary: str | None = Field(default=None, max_length=2000)
    public_notes: str | None = Field(default=None, max_length=2000)
    authorized_scope_confirmed: bool = False
    real_only_acknowledged: bool = False


class ProofApprovalPayload(ProofDraftPayload):
    draft: dict[str, Any] | None = None
    decision: str = Field(default="needs_more_evidence", max_length=80)
    reviewer: str = Field(default="Manual reviewer", max_length=160)
    reviewer_reason: str = Field(..., min_length=12, max_length=2400)
    payment_verified: bool = False
    manual_review_completed: bool = False


class ProofPublishPayload(ProofApprovalPayload):
    packet: dict[str, Any] | None = None
    visibility: str = Field(default="public", max_length=40)


class ProofRevokePayload(BaseModel):
    reviewer: str = Field(default="Admin reviewer", max_length=160)
    reason: str = Field(..., min_length=8, max_length=1200)


@router.get("/status")
def get_status() -> dict[str, Any]:
    return status()


@router.post("/draft")
def draft_public_proof(payload: ProofDraftPayload) -> dict[str, Any]:
    return build_public_proof_draft(payload.model_dump())


@router.post("/approve")
def approve_proof(payload: ProofApprovalPayload) -> dict[str, Any]:
    try:
        return approve_public_proof(payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/publish")
def publish_proof(payload: ProofPublishPayload) -> dict[str, Any]:
    try:
        return publish_public_proof(payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("")
def list_proofs(include_private: bool = Query(default=False), limit: int = Query(default=100, ge=1, le=200)) -> dict[str, Any]:
    return list_public_proofs(include_private=include_private, limit=limit)


@router.get("/{proof_id}")
def get_proof(proof_id: str, allow_private: bool = Query(default=False)) -> dict[str, Any]:
    record = get_public_proof(proof_id, allow_private=allow_private)
    if not record:
        raise HTTPException(status_code=404, detail="Proof report not found, private, or revoked")
    return {"ok": True, "record": record}


@router.get("/{proof_id}/verify")
def verify_proof(
    proof_id: str,
    integrity_hash: str | None = Query(default=None),
    report_hash: str | None = Query(default=None),
) -> dict[str, Any]:
    return verify_public_proof(proof_id, integrity_hash=integrity_hash, report_hash=report_hash)


@router.post("/{proof_id}/revoke")
def revoke_proof(proof_id: str, payload: ProofRevokePayload) -> dict[str, Any]:
    return revoke_public_proof(proof_id, reason=payload.reason, reviewer=payload.reviewer)
