from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Header, HTTPException, Query, Request
from pydantic import BaseModel, Field

from app.services import professional_direct_level_k as direct

router = APIRouter(prefix="/professional-direct-level", tags=["professional-direct-level"])


class LiveSnapshotRequest(BaseModel):
    user_id: str = Field(default="local-demo-user", max_length=120)
    project_id: str | None = Field(default=None, max_length=120)
    project_name: str | None = Field(default=None, max_length=180)
    website_url: str | None = Field(default=None, max_length=2048)
    chain: str | None = Field(default="ethereum", max_length=80)
    contract_address: str | None = Field(default=None, max_length=120)
    github_repo_url: str | None = Field(default=None, max_length=2048)
    authorization_confirmed: bool = False
    real_only_acknowledged: bool = True


class SnapshotCompareRequest(BaseModel):
    baseline_snapshot: dict[str, Any] = Field(default_factory=dict)
    current_snapshot: dict[str, Any] = Field(default_factory=dict)
    real_only_acknowledged: bool = True


@router.get("/status")
def status():
    return direct.status()


@router.get("/readiness-gate")
def readiness_gate():
    return direct.direct_competition_readiness_gate()


@router.get("/remaining-roadmap")
def remaining_roadmap():
    return direct.remaining_roadmap()


@router.post("/live-snapshot")
async def live_snapshot(payload: LiveSnapshotRequest):
    if not payload.real_only_acknowledged:
        raise HTTPException(status_code=400, detail="Real-only acknowledgement is required.")
    if not payload.authorization_confirmed:
        raise HTTPException(status_code=400, detail="Authorization confirmation is required before live snapshot checks.")
    try:
        return await direct.build_live_snapshot(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/compare-snapshots")
def compare_snapshots(payload: SnapshotCompareRequest):
    if not payload.real_only_acknowledged:
        raise HTTPException(status_code=400, detail="Real-only acknowledgement is required.")
    try:
        return direct.compare_snapshots(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/webhooks/github")
async def github_webhook(request: Request, x_hub_signature_256: str | None = Header(default=None)):
    raw = (await request.body()).decode("utf-8", errors="ignore")
    try:
        payload = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="Invalid GitHub webhook JSON") from exc
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="GitHub webhook payload must be an object")
    return direct.ingest_github_webhook(payload, signature=x_hub_signature_256, raw_body=raw)


@router.post("/webhooks/onchain")
async def onchain_webhook(request: Request, x_web3guard_signature: str | None = Header(default=None)):
    raw = (await request.body()).decode("utf-8", errors="ignore")
    try:
        payload = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="Invalid on-chain webhook JSON") from exc
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="On-chain webhook payload must be an object")
    return direct.ingest_onchain_webhook(payload, signature=x_web3guard_signature, raw_body=raw)


@router.get("/webhook-events")
def webhook_events(source: str | None = None, limit: int = Query(default=100, ge=1, le=250)):
    return direct.list_webhook_events(source=source, limit=limit)

