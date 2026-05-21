from __future__ import annotations

from fastapi import APIRouter

from app.services.professional_rule_tuning_h import phase_h_status, run_phase_h_tuning_validation

router = APIRouter(prefix="/professional-rule-tuning", tags=["professional-rule-tuning"])


@router.get("/status")
def status():
    return phase_h_status()


@router.get("/run")
def run():
    return run_phase_h_tuning_validation()
