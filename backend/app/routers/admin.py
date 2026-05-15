import csv
import io
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse

from app.core.security import require_admin
from app.models.schemas import AdminPaymentUpdate, LeadAssignUpdate, LeadNoteCreate, LeadPaymentUpdate, LeadStatusUpdate, SubscriptionUpdate
from app.services.lead_store import add_note, assign_reviewer, list_leads, update_payment, update_status
from app.services.payment_store import admin_update_payment, admin_update_subscription as update_subscription_record, list_payment_events, list_payment_intents, list_subscriptions

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])


@router.get("/leads")
def admin_leads(status: str | None = Query(default=None), package_id: str | None = Query(default=None), q: str | None = Query(default=None)):
    leads = list_leads()
    if status:
        leads = [lead for lead in leads if lead.status == status]
    if package_id:
        leads = [lead for lead in leads if lead.package_id == package_id]
    if q:
        needle = q.lower()
        leads = [lead for lead in leads if needle in " ".join([lead.project_name, lead.name, lead.email, lead.contact, lead.selected_package]).lower()]
    revenue_pending = sum((lead.payment_amount_inr or 0) for lead in leads if lead.status in {"Payment Pending", "Paid", "In Review", "Delivered", "Closed"})
    verified_revenue = sum((lead.payment_amount_inr or 0) for lead in leads if lead.payment_status == "verified")
    return {
        "leads": leads,
        "summary": {
            "total": len(leads),
            "new": sum(1 for lead in leads if lead.status == "New"),
            "payment_pending": sum(1 for lead in leads if lead.status == "Payment Pending"),
            "paid": sum(1 for lead in leads if lead.status == "Paid"),
            "in_review": sum(1 for lead in leads if lead.status == "In Review"),
            "delivered": sum(1 for lead in leads if lead.status == "Delivered"),
            "revenue_pipeline_inr": revenue_pending,
            "verified_revenue_inr": verified_revenue,
        },
    }


@router.get("/leads.csv")
def admin_leads_csv():
    leads = list_leads()
    buffer = io.StringIO()
    fieldnames = [
        "id", "created_at", "name", "email", "contact", "project_name", "website_url",
        "selected_package", "package_id", "package_amount_inr", "billing_cycle", "status",
        "payment_status", "payment_reference", "payment_intent_id", "urgency", "preferred_language",
        "assigned_reviewer", "last_updated_at",
    ]
    writer = csv.DictWriter(buffer, fieldnames=fieldnames)
    writer.writeheader()
    for lead in leads:
        writer.writerow({key: getattr(lead, key) for key in fieldnames})
    buffer.seek(0)
    return StreamingResponse(iter([buffer.getvalue()]), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=raadhanex-web3guard-leads.csv"})


@router.get("/payment-intents")
def admin_payment_intents():
    return {"payment_intents": list_payment_intents()}


@router.get("/payments")
def admin_payments():
    payments = list_payment_intents()
    verified = sum(payment.amount_inr for payment in payments if payment.status in {"verified", "webhook_verified", "razorpay_paid"})
    pending = sum(payment.amount_inr for payment in payments if payment.status not in {"verified", "webhook_verified", "razorpay_paid", "failed", "cancelled"})
    return {"payment_intents": payments, "summary": {"total": len(payments), "verified_revenue_inr": verified, "pending_amount_inr": pending}}


@router.patch("/payments/{payment_intent_id}")
def admin_update_payment_intent(payment_intent_id: str, payload: AdminPaymentUpdate):
    try:
        return {"payment_intent": admin_update_payment(payment_intent_id, payload)}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Payment intent not found") from exc


@router.get("/subscriptions")
def admin_subscriptions():
    return {"subscriptions": list_subscriptions()}


@router.patch("/subscriptions/{subscription_id}")
def admin_update_subscription(subscription_id: str, payload: SubscriptionUpdate):
    try:
        return {"subscription": update_subscription_record(subscription_id, payload)}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Subscription not found") from exc


@router.get("/payment-events")
def admin_payment_events():
    return {"events": list_payment_events(limit=200)}


@router.patch("/leads/{lead_id}/status")
def admin_update_lead_status(lead_id: str, payload: LeadStatusUpdate):
    try:
        return {"lead": update_status(lead_id, payload.status)}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Lead not found") from exc


@router.patch("/leads/{lead_id}/payment")
def admin_update_lead_payment(lead_id: str, payload: LeadPaymentUpdate):
    try:
        return {"lead": update_payment(lead_id, payload.payment_status, payload.payment_reference, payload.payment_intent_id)}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Lead not found") from exc


@router.patch("/leads/{lead_id}/assign")
def admin_assign_lead(lead_id: str, payload: LeadAssignUpdate):
    try:
        return {"lead": assign_reviewer(lead_id, payload.assigned_reviewer)}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Lead not found") from exc


@router.post("/leads/{lead_id}/note")
def admin_add_lead_note(lead_id: str, payload: LeadNoteCreate):
    try:
        return {"lead": add_note(lead_id, payload.note, payload.reviewer)}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Lead not found") from exc
