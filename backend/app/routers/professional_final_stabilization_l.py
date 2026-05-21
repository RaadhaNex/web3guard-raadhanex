from __future__ import annotations

from fastapi import APIRouter, Query

from app.services import professional_final_stabilization_l as phase_l

router = APIRouter(prefix="/professional-final-stabilization", tags=["professional-final-stabilization"])


@router.get("/status")
def status():
    return phase_l.smoke_check()


@router.get("/modules")
def modules():
    return phase_l.phase_module_matrix()


@router.get("/config")
def config():
    return phase_l.production_config_checks()


@router.get("/claim-gate")
def claim_gate(candidate_claim: str | None = Query(default=None, max_length=500)):
    return phase_l.claim_safety_gate(candidate_claim)


@router.get("/production-gate")
def production_gate(candidate_claim: str | None = Query(default=None, max_length=500)):
    return phase_l.production_gate(candidate_claim)


@router.get("/remaining")
def remaining():
    return phase_l.remaining_after_phase_l()
