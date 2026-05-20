from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
import hashlib

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.models.schemas import UnifiedUrlScanRequest
from app.services.deep_evidence_accuracy import build_deep_evidence_accuracy_package, phase68_77_status

router = APIRouter(prefix="/deep-evidence", tags=["Phase 68-77 Deep Evidence Accuracy"])

_JOBS: dict[str, dict[str, Any]] = {}


class DeepEvidencePreviewRequest(UnifiedUrlScanRequest):
    pass


class DeepEvidenceJobCreate(BaseModel):
    website_url: str = Field(min_length=8, max_length=2048)
    project_name: str | None = Field(default=None, max_length=160)
    requested_depth: str = Field(default="standard", max_length=40)
    authorization_confirmed: bool = True
    real_only_acknowledged: bool = True


def _job_id(value: str) -> str:
    return "W3G-DEEP-JOB-" + hashlib.sha256(value.encode()).hexdigest()[:14]


@router.get("/status")
def status() -> dict[str, Any]:
    return phase68_77_status()


@router.post("/preview")
async def preview(payload: DeepEvidencePreviewRequest) -> dict[str, Any]:
    # Preview is evidence/artifact based and uses the same package attached to unified scans.
    package = await build_deep_evidence_accuracy_package({}, payload)
    return {"ok": True, "preview": package}


@router.post("/jobs")
def create_job(payload: DeepEvidenceJobCreate) -> dict[str, Any]:
    jid = _job_id(f"{payload.website_url}:{datetime.now(timezone.utc).isoformat()}")
    _JOBS[jid] = {
        "id": jid,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "website_url": payload.website_url,
        "project_name": payload.project_name,
        "requested_depth": payload.requested_depth,
        "status": "queued",
        "real_only_note": "Phase 68 creates a safe job record. Actual long-running isolated workers must be deployed separately before background tool execution is claimed.",
        "authorization_confirmed": payload.authorization_confirmed,
    }
    return _JOBS[jid]


@router.get("/jobs")
def list_jobs() -> dict[str, Any]:
    return {"count": len(_JOBS), "jobs": list(_JOBS.values())[-25:]}


@router.get("/jobs/{job_id}")
def read_job(job_id: str) -> dict[str, Any]:
    return _JOBS.get(job_id, {"id": job_id, "status": "not_found", "real_only_note": "No job record exists for this ID."})
