from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, EmailStr, Field

from app.services.agency_launch import (
    agency_launch_status,
    build_agency_portfolio,
    build_handoff_pack,
    create_client_profile,
    create_intake_request,
    list_client_profiles,
    list_handoff_packs,
    list_intake_requests,
    list_white_label_settings,
    save_white_label_settings,
)

router = APIRouter(prefix="/agency-launch", tags=["agency-launch"])


class ClientProfilePayload(BaseModel):
    owner_user_id: str = Field(default="local-demo-user", min_length=1, max_length=160)
    organization_id: str | None = Field(default=None, max_length=160)
    client_name: str = Field(..., min_length=2, max_length=180)
    contact_email: EmailStr | None = None
    website_url: str | None = Field(default=None, max_length=2048)
    project_id: str | None = Field(default=None, max_length=160)
    project_name: str | None = Field(default=None, max_length=180)
    project_summary: str = Field(default="", max_length=2500)
    chain: str | None = Field(default=None, max_length=80)
    status: str = Field(default="active", max_length=40)
    tags: list[str] = Field(default_factory=list)
    notes: str = Field(default="", max_length=2000)
    authorization_confirmed: bool = False


class IntakePayload(BaseModel):
    owner_user_id: str = Field(default="local-demo-user", min_length=1, max_length=160)
    organization_id: str | None = Field(default=None, max_length=160)
    client_name: str = Field(..., min_length=2, max_length=180)
    contact_email: EmailStr | None = None
    contact_handle: str | None = Field(default=None, max_length=160)
    website_url: str | None = Field(default=None, max_length=2048)
    repo_url: str | None = Field(default=None, max_length=2048)
    scope_summary: str = Field(..., min_length=10, max_length=3000)
    requested_services: list[str] = Field(default_factory=list)
    status: str = Field(default="new", max_length=40)
    priority: str = Field(default="medium", max_length=40)
    notes: str = Field(default="", max_length=2000)
    authorization_confirmed: bool = False
    safe_use_acknowledged: bool = False


class WhiteLabelPayload(BaseModel):
    owner_user_id: str = Field(default="local-demo-user", min_length=1, max_length=160)
    organization_id: str | None = Field(default=None, max_length=160)
    brand_name: str = Field(..., min_length=2, max_length=180)
    logo_url: str | None = Field(default=None, max_length=2048)
    accent_label: str | None = Field(default=None, max_length=80)
    report_footer: str = Field(default="", max_length=600)
    custom_disclaimer: str = Field(default="", max_length=800)
    show_powered_by_raadhanex: bool = True
    client_safe_wording: str = Field(default="", max_length=600)


class HandoffPackPayload(BaseModel):
    owner_user_id: str = Field(default="local-demo-user", min_length=1, max_length=160)
    organization_id: str | None = Field(default=None, max_length=160)
    client_id: str | None = Field(default=None, max_length=160)
    client_name: str | None = Field(default=None, max_length=180)
    project_id: str | None = Field(default=None, max_length=160)
    project_name: str | None = Field(default=None, max_length=180)
    status: str = Field(default="ready", max_length=40)
    executive_summary: str = Field(default="", max_length=2500)
    services_included: list[str] = Field(default_factory=list)
    open_items: list[str] = Field(default_factory=list)
    evidence_links: list[str] = Field(default_factory=list)
    handoff_notes: str = Field(default="", max_length=2000)
    authorization_confirmed: bool = False


@router.get("/status")
def status() -> dict[str, Any]:
    return agency_launch_status()


@router.get("/portfolio")
def portfolio(
    owner_user_id: str = Query(default="local-demo-user", min_length=1, max_length=160),
    organization_id: str | None = Query(default=None, max_length=160),
    limit: int = Query(default=100, ge=1, le=200),
) -> dict[str, Any]:
    return build_agency_portfolio(owner_user_id=owner_user_id, organization_id=organization_id, limit=limit)


@router.post("/clients")
def create_client(payload: ClientProfilePayload) -> dict[str, Any]:
    try:
        return create_client_profile(payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/clients")
def clients(
    owner_user_id: str = Query(default="local-demo-user", min_length=1, max_length=160),
    organization_id: str | None = Query(default=None, max_length=160),
    limit: int = Query(default=100, ge=1, le=200),
) -> dict[str, Any]:
    return list_client_profiles(owner_user_id=owner_user_id, organization_id=organization_id, limit=limit)


@router.post("/intake")
def create_intake(payload: IntakePayload) -> dict[str, Any]:
    try:
        return create_intake_request(payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/intake")
def intake(
    owner_user_id: str = Query(default="local-demo-user", min_length=1, max_length=160),
    organization_id: str | None = Query(default=None, max_length=160),
    status: str | None = Query(default=None, max_length=40),
    limit: int = Query(default=100, ge=1, le=200),
) -> dict[str, Any]:
    return list_intake_requests(owner_user_id=owner_user_id, organization_id=organization_id, status=status, limit=limit)


@router.post("/white-label")
def save_white_label(payload: WhiteLabelPayload) -> dict[str, Any]:
    try:
        return save_white_label_settings(payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/white-label")
def white_label(
    owner_user_id: str = Query(default="local-demo-user", min_length=1, max_length=160),
    organization_id: str | None = Query(default=None, max_length=160),
    limit: int = Query(default=50, ge=1, le=100),
) -> dict[str, Any]:
    return list_white_label_settings(owner_user_id=owner_user_id, organization_id=organization_id, limit=limit)


@router.post("/handoff-packs")
def create_handoff(payload: HandoffPackPayload) -> dict[str, Any]:
    try:
        return build_handoff_pack(payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/handoff-packs")
def handoff_packs(
    owner_user_id: str = Query(default="local-demo-user", min_length=1, max_length=160),
    organization_id: str | None = Query(default=None, max_length=160),
    client_id: str | None = Query(default=None, max_length=160),
    limit: int = Query(default=100, ge=1, le=200),
) -> dict[str, Any]:
    return list_handoff_packs(owner_user_id=owner_user_id, organization_id=organization_id, client_id=client_id, limit=limit)
