from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.provider_live import (
    advisory_live_search,
    goplus_live_status,
    github_repo_live_check,
    provider_live_status,
    explorer_source_snapshot,
)

router = APIRouter(prefix="/provider-live", tags=["provider-live"])


class ExplorerSourceRequest(BaseModel):
    chain: str = Field(default="ethereum", max_length=80)
    address: str = Field(min_length=42, max_length=42)
    include_abi: bool = False
    real_only_acknowledged: bool = True


class GitHubRepoCheckRequest(BaseModel):
    repo_url: str = Field(min_length=12, max_length=300)
    branch: str | None = Field(default=None, max_length=120)
    authorization_confirmed: bool = True
    real_only_acknowledged: bool = True


class AdvisorySearchRequest(BaseModel):
    source: str = Field(default="osv", max_length=40)
    query: str | None = Field(default=None, max_length=220)
    ecosystem: str | None = Field(default=None, max_length=80)
    package_name: str | None = Field(default=None, max_length=220)
    real_only_acknowledged: bool = True


@router.get("/status")
def get_provider_live_status():
    return provider_live_status()


@router.post("/explorer/source")
async def fetch_explorer_source(payload: ExplorerSourceRequest):
    if not payload.real_only_acknowledged:
        raise HTTPException(status_code=400, detail="Real-only acknowledgement is required")
    try:
        return await explorer_source_snapshot(payload.chain, payload.address, include_abi=payload.include_abi)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/goplus/status")
def get_goplus_live_status():
    return goplus_live_status()


@router.post("/github/repo-check")
async def check_github_repo(payload: GitHubRepoCheckRequest):
    if not payload.real_only_acknowledged:
        raise HTTPException(status_code=400, detail="Real-only acknowledgement is required")
    if not payload.authorization_confirmed:
        raise HTTPException(status_code=400, detail="Repository owner authorization / public-scope acknowledgement is required")
    try:
        return await github_repo_live_check(payload.repo_url, branch=payload.branch)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/advisory/search")
async def search_advisory_source(payload: AdvisorySearchRequest):
    if not payload.real_only_acknowledged:
        raise HTTPException(status_code=400, detail="Real-only acknowledgement is required")
    try:
        return await advisory_live_search(
            payload.source,
            query=payload.query,
            ecosystem=payload.ecosystem,
            package_name=payload.package_name,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
