from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.payment_validation import (
    access_preview,
    checkout_dry_run,
    claim_check,
    first_paid_flow,
    payment_validation_status,
    revenue_readiness,
)

router = APIRouter(prefix="/payment-validation", tags=["payment-validation"])


class CheckoutDryRunRequest(BaseModel):
    package_id: str = Field(default="quick-risk-report", min_length=1, max_length=120)
    billing_cycle: str = Field(default="one_time", max_length=40)
    provider_preference: str = Field(default="auto", max_length=40)


class AccessPreviewRequest(BaseModel):
    package_id: str = Field(default="quick-risk-report", min_length=1, max_length=120)
    verified: bool = False
    manual_admin_approved: bool = False


class ClaimCheckRequest(BaseModel):
    text: str = Field(min_length=1, max_length=4000)


@router.get("/status")
def get_payment_validation_status():
    return payment_validation_status()


@router.get("/first-paid-flow")
def get_first_paid_flow():
    return first_paid_flow()


@router.get("/revenue-readiness")
def get_revenue_readiness():
    return revenue_readiness()


@router.post("/checkout-dry-run")
def post_checkout_dry_run(payload: CheckoutDryRunRequest):
    try:
        return checkout_dry_run(
            package_id=payload.package_id,
            billing_cycle=payload.billing_cycle,
            provider_preference=payload.provider_preference,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Package not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/access-preview")
def post_access_preview(payload: AccessPreviewRequest):
    try:
        return access_preview(
            package_id=payload.package_id,
            verified=payload.verified,
            manual_admin_approved=payload.manual_admin_approved,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Package not found") from exc


@router.post("/claim-check")
def post_claim_check(payload: ClaimCheckRequest):
    return claim_check(payload.text)
