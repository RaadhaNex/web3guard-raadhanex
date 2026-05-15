from fastapi import APIRouter, HTTPException
from app.models.schemas import LeadCreate
from app.services.lead_store import create_lead

router = APIRouter(tags=["leads"])


@router.post("/lead")
def submit_lead(payload: LeadCreate):
    try:
        lead = create_lead(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "ok": True,
        "lead": lead,
        "next_steps": [
            "If paid package was selected, complete UPI payment and save the transaction/reference ID.",
            "RAADHANEX admin verifies payment manually in Phase 4.",
            "After verification, lead can move from Paid to In Review to Delivered.",
        ],
        "message": "Lead submitted. RAADHANEX team can follow up after payment/reference confirmation.",
    }
