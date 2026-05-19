from fastapi import APIRouter, Query

from app.services.billing_access import billing_access_summary, billing_final_status, plan_limit_matrix

router = APIRouter(tags=["billing-final"])


@router.get("/billing/status")
def get_billing_status():
    return billing_final_status()


@router.get("/billing/plan-limits")
def get_plan_limits():
    return {"ok": True, "plans": plan_limit_matrix()}


@router.get("/billing/access")
def get_billing_access(
    user_id: str | None = Query(default=None, max_length=120),
    organization_id: str | None = Query(default=None, max_length=120),
    customer_email: str | None = Query(default=None, max_length=160),
):
    return billing_access_summary(user_id=user_id, organization_id=organization_id, customer_email=customer_email)
