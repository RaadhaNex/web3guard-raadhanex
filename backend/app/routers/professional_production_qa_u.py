from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services import professional_production_qa_u as qa

router = APIRouter(prefix="/professional-production-qa", tags=["professional-production-qa-u"])


class QaRunRequest(BaseModel):
    project_name: str = "Web3Guard AI"
    environment: str = "production"
    overall_status: str | None = None
    checked_by: str = "manual"
    summary: str = ""
    checks: list[dict[str, Any]] = Field(default_factory=list)


@router.get("/status")
def status():
    return qa.phase_status()


@router.get("/local-test-plan")
def local_test_plan():
    return qa.local_test_plan()


@router.get("/live-smoke-checklist")
def live_smoke_checklist():
    return qa.live_smoke_checklist()


@router.get("/release-checklist")
def release_checklist():
    return qa.release_checklist()


@router.get("/competitor-position")
def competitor_position():
    return qa.competitor_position()


@router.get("/launch-decision")
def launch_decision():
    return qa.launch_decision()


@router.post("/runs")
def create_run(payload: QaRunRequest):
    return qa.record_qa_run(payload.model_dump())


@router.get("/runs")
def runs(limit: int = 50):
    return qa.list_qa_runs(limit=limit)
