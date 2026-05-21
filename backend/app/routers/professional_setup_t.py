from __future__ import annotations

from fastapi import APIRouter

from app.services import professional_setup_t as setup

router = APIRouter(prefix="/professional-setup", tags=["professional-setup-t"])


@router.get("/status")
def status():
    return setup.phase_status()


@router.get("/env-checklist")
def env_checklist():
    return setup.env_checklist()


@router.get("/webhooks")
def webhooks():
    return setup.webhook_readiness()


@router.get("/worker-gate")
def worker_gate():
    return setup.worker_enablement_gate()


@router.get("/production-readiness")
def production_readiness():
    return setup.production_readiness()


@router.get("/manual-actions")
def manual_actions():
    return setup.manual_actions()
