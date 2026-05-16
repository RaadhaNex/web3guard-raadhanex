import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from app.core.config import settings
from app.models.schemas import Lead, LeadCreate
from app.services.payment_store import find_package


def _path() -> Path:
    path = Path(settings.leads_file)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.touch(exist_ok=True)
    return path


def create_lead(payload: LeadCreate) -> Lead:
    if not payload.authorization_confirmed or not payload.consent_confirmed:
        raise ValueError("Authorization and consent are required")

    package_amount = payload.package_amount_inr
    package_id = payload.package_id
    try:
        package = find_package(package_id or payload.selected_package)
        package_id = package["id"]
        package_amount = int(package["price_inr"])
        selected_package = package["name"]
    except KeyError:
        selected_package = payload.selected_package

    payment_status = "reference_submitted" if payload.payment_reference else "created"
    status = "Payment Pending" if package_amount and package_amount > 0 else "New"

    lead = Lead(
        **payload.model_dump(exclude={"selected_package", "package_id", "package_amount_inr"}),
        selected_package=selected_package,
        package_id=package_id,
        package_amount_inr=package_amount,
        id=f"lead_{uuid.uuid4().hex[:12]}",
        created_at=datetime.now(timezone.utc),
        status=status,
        payment_status=payment_status,
        payment_amount_inr=package_amount,
        payment_upi_id=settings.raadhanex_upi_id,
        last_updated_at=datetime.now(timezone.utc),
    )
    with _path().open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(lead.model_dump(mode="json"), ensure_ascii=False) + "\n")
    return lead


def list_leads() -> list[Lead]:
    leads: list[Lead] = []
    for line in _path().read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        raw = json.loads(line)
        # Backward compatibility for old current-3 leads.
        raw.setdefault("payment_status", "created")
        raw.setdefault("payment_intent_id", None)
        raw.setdefault("payment_amount_inr", raw.get("package_amount_inr"))
        raw.setdefault("payment_upi_id", settings.raadhanex_upi_id)
        raw.setdefault("last_updated_at", raw.get("created_at"))
        raw.setdefault("package_id", None)
        raw.setdefault("package_amount_inr", raw.get("payment_amount_inr"))
        raw.setdefault("billing_cycle", "one_time")
        leads.append(Lead.model_validate(raw))
    return leads


def replace_leads(leads: list[Lead]) -> None:
    with _path().open("w", encoding="utf-8") as handle:
        for lead in leads:
            handle.write(json.dumps(lead.model_dump(mode="json"), ensure_ascii=False) + "\n")


def update_status(lead_id: str, status: str) -> Lead:
    leads = list_leads()
    for index, lead in enumerate(leads):
        if lead.id == lead_id:
            lead.status = status
            lead.last_updated_at = datetime.now(timezone.utc)
            leads[index] = lead
            replace_leads(leads)
            return lead
    raise KeyError("Lead not found")


def update_payment(lead_id: str, payment_status: str, payment_reference: str | None = None, payment_intent_id: str | None = None) -> Lead:
    leads = list_leads()
    for index, lead in enumerate(leads):
        if lead.id == lead_id:
            lead.payment_status = payment_status
            if payment_reference:
                lead.payment_reference = payment_reference
            if payment_intent_id:
                lead.payment_intent_id = payment_intent_id
            if payment_status == "verified":
                lead.status = "Paid"
            elif payment_status in {"reference_submitted", "manual_verification_pending"}:
                lead.status = "Payment Pending"
            lead.last_updated_at = datetime.now(timezone.utc)
            leads[index] = lead
            replace_leads(leads)
            return lead
    raise KeyError("Lead not found")


def assign_reviewer(lead_id: str, reviewer: str | None) -> Lead:
    leads = list_leads()
    for index, lead in enumerate(leads):
        if lead.id == lead_id:
            lead.assigned_reviewer = reviewer
            lead.last_updated_at = datetime.now(timezone.utc)
            leads[index] = lead
            replace_leads(leads)
            return lead
    raise KeyError("Lead not found")


def add_note(lead_id: str, note: str, reviewer: str | None = None) -> Lead:
    leads = list_leads()
    for index, lead in enumerate(leads):
        if lead.id == lead_id:
            author = reviewer or "admin"
            lead.internal_notes.append(f"{datetime.now(timezone.utc).isoformat()} — {author}: {note}")
            lead.last_updated_at = datetime.now(timezone.utc)
            leads[index] = lead
            replace_leads(leads)
            return lead
    raise KeyError("Lead not found")
