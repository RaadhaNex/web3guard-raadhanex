from __future__ import annotations

from fastapi import APIRouter

from app.services.production_deployment_qa import (
    deployment_command_checklist,
    manual_live_qa_routes,
    production_deployment_qa_status,
)

router = APIRouter(prefix="/production-deployment-qa", tags=["Production Deployment QA"])


@router.get("/status")
def status():
    return production_deployment_qa_status()


@router.get("/routes")
def routes():
    return {"ok": True, "routes": manual_live_qa_routes()}


@router.get("/commands")
def commands():
    return {"ok": True, "commands": deployment_command_checklist()}
