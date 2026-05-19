from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.worker_execution import probe_worker_tools, worker_execution_plan, worker_execution_status

router = APIRouter(prefix="/worker-execution", tags=["worker-execution"])


class WorkerPlanRequest(BaseModel):
    project_type: str | None = Field(default=None, max_length=160)
    tools: list[str] = Field(default_factory=list)
    real_only_acknowledged: bool = True


class WorkerProbeRequest(BaseModel):
    tools: list[str] = Field(default_factory=list)
    real_only_acknowledged: bool = True


@router.get("/status")
def get_worker_execution_status():
    return worker_execution_status()


@router.post("/plan")
def create_worker_execution_plan(payload: WorkerPlanRequest):
    if not payload.real_only_acknowledged:
        raise HTTPException(status_code=400, detail="Real-only acknowledgement is required")
    return worker_execution_plan(project_type=payload.project_type, requested_tools=payload.tools)


@router.post("/probe")
def probe_worker_execution_tools(payload: WorkerProbeRequest):
    if not payload.real_only_acknowledged:
        raise HTTPException(status_code=400, detail="Real-only acknowledgement is required")
    return probe_worker_tools(requested_tools=payload.tools)
