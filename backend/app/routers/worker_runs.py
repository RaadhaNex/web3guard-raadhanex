from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.worker_runs import import_worker_json, run_static_worker, worker_manifest, worker_run_status

router = APIRouter(prefix="/worker-runs", tags=["worker-runs"])


class WorkerManifestRequest(BaseModel):
    project_name: str | None = Field(default=None, max_length=160)
    project_type: str | None = Field(default=None, max_length=160)
    tools: list[str] = Field(default_factory=list)
    real_only_acknowledged: bool = True


class StaticWorkerRunRequest(BaseModel):
    project_name: str | None = Field(default=None, max_length=160)
    source_code: str = Field(min_length=1, max_length=220_000)
    file_name: str | None = Field(default="Contract.sol", max_length=120)
    tools: list[str] = Field(default_factory=list)
    execute: bool = False
    real_only_acknowledged: bool = True


class ImportWorkerJsonRequest(BaseModel):
    tool: str = Field(max_length=40)
    tool_json: str = Field(min_length=2, max_length=260_000)
    generated_by_web3guard_worker: bool = False
    real_only_acknowledged: bool = True


@router.get("/status")
def get_worker_run_status():
    return worker_run_status()


@router.post("/manifest")
def create_worker_manifest(payload: WorkerManifestRequest):
    if not payload.real_only_acknowledged:
        raise HTTPException(status_code=400, detail="Real-only acknowledgement is required")
    return worker_manifest(payload.project_name, payload.project_type, payload.tools)


@router.post("/static")
def run_static_worker_endpoint(payload: StaticWorkerRunRequest):
    if not payload.real_only_acknowledged:
        raise HTTPException(status_code=400, detail="Real-only acknowledgement is required")
    try:
        return run_static_worker(
            source_code=payload.source_code,
            project_name=payload.project_name,
            file_name=payload.file_name,
            tools=payload.tools,
            execute=payload.execute,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/import-json")
def import_worker_json_endpoint(payload: ImportWorkerJsonRequest):
    if not payload.real_only_acknowledged:
        raise HTTPException(status_code=400, detail="Real-only acknowledgement is required")
    try:
        return import_worker_json(payload.tool, payload.tool_json, payload.generated_by_web3guard_worker)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
