from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.services.trust_metrics import (
    check_public_wording,
    create_advisory_mapping,
    create_disclosure_record,
    create_metric_snapshot,
    list_advisory_mappings,
    list_disclosures,
    list_metric_snapshots,
    public_summary,
    trust_metrics_status,
)

router = APIRouter(prefix="/trust-metrics", tags=["trust-metrics"])


class WordingCheckPayload(BaseModel):
    text: str = Field(..., min_length=1, max_length=4000)


class MetricSnapshotPayload(BaseModel):
    owner_user_id: str = Field(default="local-demo-user", min_length=1, max_length=160)
    organization_id: str | None = Field(default=None, max_length=160)
    project_id: str | None = Field(default=None, max_length=160)
    project_name: str | None = Field(default=None, max_length=180)
    report_hash: str | None = Field(default=None, max_length=160)
    external_advisory_count: int = Field(default=0, ge=0, le=1_000_000)
    web3guard_generated_finding_count: int = Field(default=0, ge=0, le=1_000_000)
    community_review_count: int = Field(default=0, ge=0, le=1_000_000)
    disclosure_count: int = Field(default=0, ge=0, le=1_000_000)
    resolved_disclosure_count: int = Field(default=0, ge=0, le=1_000_000)
    public_metric_note: str = Field(default="", max_length=1000)
    metric_sources: list[str] = Field(default_factory=list)
    safe_public_metrics_acknowledged: bool = False


class AdvisoryMappingPayload(BaseModel):
    owner_user_id: str = Field(default="local-demo-user", min_length=1, max_length=160)
    organization_id: str | None = Field(default=None, max_length=160)
    project_id: str = Field(..., min_length=2, max_length=160)
    project_name: str | None = Field(default=None, max_length=180)
    advisory_source: str = Field(default="manual", max_length=40)
    advisory_id: str = Field(..., min_length=2, max_length=180)
    advisory_title: str | None = Field(default=None, max_length=240)
    severity: str = Field(default="unknown", max_length=40)
    affected_component: str | None = Field(default=None, max_length=240)
    mapping_status: str = Field(default="needs_review", max_length=40)
    evidence_links: list[str] = Field(default_factory=list)
    notes: str = Field(default="", max_length=1400)
    authorization_confirmed: bool = False


class DisclosurePayload(BaseModel):
    owner_user_id: str = Field(default="local-demo-user", min_length=1, max_length=160)
    organization_id: str | None = Field(default=None, max_length=160)
    project_id: str = Field(..., min_length=2, max_length=160)
    project_name: str | None = Field(default=None, max_length=180)
    origin: str = Field(default="manual", max_length=60)
    related_mapping_id: str | None = Field(default=None, max_length=160)
    title: str = Field(..., min_length=3, max_length=240)
    severity: str = Field(default="unknown", max_length=40)
    status: str = Field(default="draft", max_length=40)
    recipient: str | None = Field(default=None, max_length=240)
    public_reference: str | None = Field(default=None, max_length=500)
    summary: str = Field(default="", max_length=2500)
    timeline_notes: str = Field(default="", max_length=2000)
    evidence_links: list[str] = Field(default_factory=list)
    authorization_confirmed: bool = False
    manual_send_acknowledged: bool = False


@router.get("/status")
def status() -> dict[str, Any]:
    return trust_metrics_status()


@router.post("/wording-check")
def wording_check(payload: WordingCheckPayload) -> dict[str, Any]:
    return check_public_wording(payload.text)


@router.post("/snapshots")
def create_snapshot(payload: MetricSnapshotPayload) -> dict[str, Any]:
    try:
        return create_metric_snapshot(payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/snapshots")
def snapshots(
    owner_user_id: str = Query(default="local-demo-user", min_length=1, max_length=160),
    organization_id: str | None = Query(default=None, max_length=160),
    project_id: str | None = Query(default=None, max_length=160),
    limit: int = Query(default=100, ge=1, le=200),
) -> dict[str, Any]:
    return list_metric_snapshots(owner_user_id=owner_user_id, organization_id=organization_id, project_id=project_id, limit=limit)


@router.post("/advisory-mappings")
def create_mapping(payload: AdvisoryMappingPayload) -> dict[str, Any]:
    try:
        return create_advisory_mapping(payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/advisory-mappings")
def advisory_mappings(
    owner_user_id: str = Query(default="local-demo-user", min_length=1, max_length=160),
    organization_id: str | None = Query(default=None, max_length=160),
    project_id: str | None = Query(default=None, max_length=160),
    limit: int = Query(default=100, ge=1, le=200),
) -> dict[str, Any]:
    return list_advisory_mappings(owner_user_id=owner_user_id, organization_id=organization_id, project_id=project_id, limit=limit)


@router.post("/disclosures")
def create_disclosure(payload: DisclosurePayload) -> dict[str, Any]:
    try:
        return create_disclosure_record(payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/disclosures")
def disclosures(
    owner_user_id: str = Query(default="local-demo-user", min_length=1, max_length=160),
    organization_id: str | None = Query(default=None, max_length=160),
    project_id: str | None = Query(default=None, max_length=160),
    status: str | None = Query(default=None, max_length=40),
    limit: int = Query(default=100, ge=1, le=200),
) -> dict[str, Any]:
    return list_disclosures(owner_user_id=owner_user_id, organization_id=organization_id, project_id=project_id, status=status, limit=limit)


@router.get("/public-summary")
def get_public_summary(
    owner_user_id: str = Query(default="local-demo-user", min_length=1, max_length=160),
    organization_id: str | None = Query(default=None, max_length=160),
    project_id: str | None = Query(default=None, max_length=160),
) -> dict[str, Any]:
    return public_summary(owner_user_id=owner_user_id, organization_id=organization_id, project_id=project_id)
