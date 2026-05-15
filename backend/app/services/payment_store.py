from __future__ import annotations

import hashlib
import hmac
import json
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus

import httpx

from app.core.config import settings
from app.models.schemas import (
    AdminPaymentUpdate,
    BillingCycle,
    PaymentIntent,
    PaymentIntentCreate,
    RazorpayVerifyRequest,
    SubscriptionRecord,
    SubscriptionUpdate,
)

PACKAGES_PATH = Path("app/data/packages.json")


def _jsonl_path(path_value: str) -> Path:
    path = Path(path_value)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.touch(exist_ok=True)
    return path


def _payment_path() -> Path:
    return _jsonl_path(settings.payment_intents_file)


def _events_path() -> Path:
    return _jsonl_path(settings.payment_events_file)


def _subscriptions_path() -> Path:
    return _jsonl_path(settings.subscriptions_file)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def load_packages() -> list[dict]:
    return json.loads(PACKAGES_PATH.read_text(encoding="utf-8"))


def find_package(package_id: str) -> dict:
    for package in load_packages():
        if package["id"] == package_id:
            return package
    raise KeyError("Package not found")


def is_razorpay_configured() -> bool:
    return bool(settings.razorpay_enabled and settings.razorpay_key_id and settings.razorpay_key_secret)


def payment_status() -> dict[str, Any]:
    configured = is_razorpay_configured()
    webhook_configured = bool(settings.razorpay_webhook_secret)
    return {
        "ok": True,
        "phase": "Phase 8 - Razorpay + UPI subscription system",
        "payment_mode": settings.payment_mode,
        "upi_manual_enabled": True,
        "upi_id_configured": settings.raadhanex_upi_id not in {"", "yourupi@bank", "raadhanex@upi"},
        "razorpay_enabled": settings.razorpay_enabled,
        "razorpay_configured": configured,
        "razorpay_key_id_public": settings.razorpay_key_id if configured else None,
        "razorpay_webhook_configured": webhook_configured,
        "auto_payment_verification": configured,
        "manual_verification_fallback": True,
        "real_only_note": "Razorpay payments are marked verified only after signature/webhook verification. Manual UPI payments require admin verification.",
        "blocked_claims": [
            "Do not show payment successful before Razorpay signature/webhook verification.",
            "Do not activate subscription before verified payment or manual admin approval.",
            "Do not expose RAZORPAY_KEY_SECRET or webhook secret in frontend.",
        ],
    }


def build_upi_deep_link(amount: int, package_name: str, intent_id: str) -> str | None:
    if amount <= 0:
        return None
    note = quote_plus(f"Web3Guard AI {package_name} {intent_id}")
    return (
        f"upi://pay?pa={quote_plus(settings.raadhanex_upi_id)}"
        f"&pn={quote_plus(settings.raadhanex_upi_name)}"
        f"&am={amount}&cu=INR&tn={note}"
    )


def package_with_payment(package: dict) -> dict:
    package = dict(package)
    amount = int(package.get("price_inr", 0))
    preview_id = f"preview_{package['id']}"
    package["upi_payment"] = {
        "enabled": amount > 0,
        "upi_id": settings.raadhanex_upi_id,
        "upi_name": settings.raadhanex_upi_name,
        "deep_link": build_upi_deep_link(amount, package["name"], preview_id),
        "manual_verification_required": True,
        "note": "UPI deep link opens a payment app. User must submit reference unless Razorpay checkout is used and verified.",
    }
    package["razorpay_payment"] = {
        "enabled": amount > 0 and is_razorpay_configured(),
        "key_id_public": settings.razorpay_key_id if is_razorpay_configured() else None,
        "auto_verification": is_razorpay_configured(),
        "note": "Razorpay Checkout creates a real order only when backend Razorpay keys are configured.",
    }
    return package


def _read_payments() -> list[PaymentIntent]:
    rows: list[PaymentIntent] = []
    for line in _payment_path().read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(PaymentIntent.model_validate(json.loads(line)))
    return rows


def _write_payments(rows: list[PaymentIntent]) -> None:
    with _payment_path().open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row.model_dump(mode="json"), ensure_ascii=False) + "\n")


def _append_event(event: dict[str, Any]) -> None:
    event.setdefault("created_at", _now().isoformat())
    with _events_path().open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False, default=str) + "\n")


def _save_intent(intent: PaymentIntent) -> PaymentIntent:
    with _payment_path().open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(intent.model_dump(mode="json"), ensure_ascii=False) + "\n")
    return intent


def list_payment_intents() -> list[PaymentIntent]:
    return sorted(_read_payments(), key=lambda item: item.created_at, reverse=True)


def get_payment_intent(intent_id: str) -> PaymentIntent:
    for intent in _read_payments():
        if intent.id == intent_id:
            return intent
    raise KeyError("Payment intent not found")


def get_payment_by_razorpay_order(order_id: str) -> PaymentIntent:
    for intent in _read_payments():
        if intent.razorpay_order_id == order_id:
            return intent
    raise KeyError("Razorpay order not found")


def _replace_intent(updated: PaymentIntent) -> PaymentIntent:
    rows = _read_payments()
    found = False
    for index, row in enumerate(rows):
        if row.id == updated.id:
            rows[index] = updated
            found = True
            break
    if not found:
        raise KeyError("Payment intent not found")
    _write_payments(rows)
    return updated


def _should_use_razorpay(preference: str) -> bool:
    if preference == "upi_manual":
        return False
    if preference == "razorpay":
        if not is_razorpay_configured():
            raise ValueError("Razorpay is requested but backend Razorpay keys are not configured")
        return True
    return is_razorpay_configured() and settings.payment_mode in {"razorpay", "razorpay_or_upi_manual"}


def _create_razorpay_order(*, amount_inr: int, receipt: str, notes: dict[str, str]) -> dict[str, Any]:
    if not is_razorpay_configured():
        raise ValueError("Razorpay is not configured")
    payload = {
        "amount": amount_inr * 100,
        "currency": "INR",
        "receipt": receipt,
        "notes": notes,
    }
    with httpx.Client(timeout=20.0) as client:
        response = client.post(
            f"{settings.razorpay_api_base.rstrip('/')}/orders",
            json=payload,
            auth=(settings.razorpay_key_id or "", settings.razorpay_key_secret or ""),
        )
    if response.status_code >= 400:
        raise ValueError(f"Razorpay order create failed: {response.text[:500]}")
    return response.json()


def create_payment_intent(payload: PaymentIntentCreate) -> PaymentIntent:
    package = find_package(payload.package_id)
    allowed_cycles = package.get("billing_cycles", ["one_time"])
    if payload.billing_cycle not in allowed_cycles:
        raise ValueError(f"Billing cycle {payload.billing_cycle} is not available for this package")

    intent_id = f"pay_{uuid.uuid4().hex[:12]}"
    amount = int(package["price_inr"])
    amount_paise = amount * 100
    provider = "upi_manual"
    status = "created"
    receipt = f"rcpt_{intent_id}"
    razorpay_order: dict[str, Any] | None = None

    if amount > 0 and _should_use_razorpay(payload.provider_preference):
        razorpay_order = _create_razorpay_order(
            amount_inr=amount,
            receipt=receipt,
            notes={
                "payment_intent_id": intent_id,
                "package_id": package["id"],
                "project_name": payload.project_name or "",
                "billing_cycle": payload.billing_cycle,
            },
        )
        provider = "razorpay"
        status = "razorpay_order_created"

    intent = PaymentIntent(
        id=intent_id,
        created_at=_now(),
        package_id=package["id"],
        package_name=package["name"],
        amount_inr=amount,
        amount_paise=amount_paise,
        billing_cycle=payload.billing_cycle,
        customer_name=payload.customer_name,
        customer_email=str(payload.customer_email) if payload.customer_email else None,
        project_name=payload.project_name,
        user_id=payload.user_id,
        organization_id=payload.organization_id,
        provider=provider,  # type: ignore[arg-type]
        provider_preference=payload.provider_preference,
        upi_id=settings.raadhanex_upi_id,
        upi_name=settings.raadhanex_upi_name,
        upi_deep_link=build_upi_deep_link(amount, package["name"], intent_id),
        manual_verification_required=provider != "razorpay",
        razorpay_enabled=provider == "razorpay",
        razorpay_key_id=settings.razorpay_key_id if provider == "razorpay" else None,
        razorpay_order_id=razorpay_order.get("id") if razorpay_order else None,
        razorpay_receipt=receipt,
        razorpay_order_status=razorpay_order.get("status") if razorpay_order else None,
        razorpay_checkout_options={
            "key": settings.razorpay_key_id,
            "amount": amount_paise,
            "currency": "INR",
            "name": "Web3Guard AI by RAADHANEX",
            "description": package["name"],
            "order_id": razorpay_order.get("id") if razorpay_order else None,
            "prefill": {
                "name": payload.customer_name or "",
                "email": str(payload.customer_email) if payload.customer_email else "",
            },
            "notes": {"payment_intent_id": intent_id, "package_id": package["id"]},
        } if provider == "razorpay" else {},
        status=status,  # type: ignore[arg-type]
        metadata={"package_category": package.get("category", "service")},
        note=(
            "Razorpay order created. Mark paid only after Checkout signature or webhook verification."
            if provider == "razorpay"
            else "Pay with UPI, then submit the UPI reference in the review request. Manual admin verification is required."
        ),
    )
    _save_intent(intent)
    _append_event({"type": "payment_intent_created", "payment_intent_id": intent.id, "provider": provider, "status": status})
    return intent


def _signature_digest(message: str, secret: str) -> str:
    return hmac.new(secret.encode("utf-8"), message.encode("utf-8"), hashlib.sha256).hexdigest()


def verify_checkout_signature(payload: RazorpayVerifyRequest) -> PaymentIntent:
    if not settings.razorpay_key_secret:
        raise ValueError("Razorpay key secret is not configured")
    intent = get_payment_intent(payload.payment_intent_id)
    if intent.razorpay_order_id != payload.razorpay_order_id:
        raise ValueError("Razorpay order does not match this payment intent")
    message = f"{payload.razorpay_order_id}|{payload.razorpay_payment_id}"
    expected = _signature_digest(message, settings.razorpay_key_secret)
    if not hmac.compare_digest(expected, payload.razorpay_signature):
        intent.status = "failed"
        _replace_intent(intent)
        _append_event({"type": "razorpay_signature_failed", "payment_intent_id": intent.id, "order_id": payload.razorpay_order_id})
        raise ValueError("Invalid Razorpay payment signature")
    intent.razorpay_payment_id = payload.razorpay_payment_id
    intent.razorpay_signature = payload.razorpay_signature
    intent.status = "verified"
    intent.verified_at = _now()
    intent.manual_verification_required = False
    updated = _replace_intent(intent)
    subscription = maybe_create_or_activate_subscription(updated, source="checkout_signature")
    if subscription:
        updated.subscription_id = subscription.id
        updated = _replace_intent(updated)
    _append_event({"type": "razorpay_checkout_verified", "payment_intent_id": updated.id, "order_id": payload.razorpay_order_id, "payment_id": payload.razorpay_payment_id})
    return updated


def verify_webhook_signature(raw_body: bytes, signature: str | None) -> bool:
    if not settings.razorpay_webhook_secret:
        raise ValueError("Razorpay webhook secret is not configured")
    if not signature:
        return False
    expected = hmac.new(settings.razorpay_webhook_secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


def handle_razorpay_webhook(raw_body: bytes, signature: str | None) -> dict[str, Any]:
    if not verify_webhook_signature(raw_body, signature):
        raise ValueError("Invalid Razorpay webhook signature")
    event = json.loads(raw_body.decode("utf-8"))
    event_name = event.get("event", "unknown")
    entity = (event.get("payload") or {}).get("payment", {}).get("entity") or (event.get("payload") or {}).get("order", {}).get("entity") or {}
    order_id = entity.get("order_id") or entity.get("id")
    payment_id = entity.get("id") if entity.get("entity") == "payment" or event_name.startswith("payment.") else entity.get("payment_id")
    updated_intent: PaymentIntent | None = None
    if order_id:
        try:
            intent = get_payment_by_razorpay_order(order_id)
            if event_name in {"payment.captured", "order.paid"}:
                intent.status = "webhook_verified"
                intent.webhook_verified_at = _now()
                intent.manual_verification_required = False
                if payment_id:
                    intent.razorpay_payment_id = payment_id
                updated_intent = _replace_intent(intent)
                subscription = maybe_create_or_activate_subscription(updated_intent, source=f"webhook:{event_name}")
                if subscription:
                    updated_intent.subscription_id = subscription.id
                    updated_intent = _replace_intent(updated_intent)
            elif event_name in {"payment.failed"}:
                intent.status = "failed"
                updated_intent = _replace_intent(intent)
        except KeyError:
            pass
    _append_event({"type": "razorpay_webhook", "event": event_name, "order_id": order_id, "payment_id": payment_id, "intent_updated": updated_intent.id if updated_intent else None})
    return {"ok": True, "event": event_name, "order_id": order_id, "payment_intent": updated_intent}


def list_payment_events(limit: int = 100) -> list[dict[str, Any]]:
    rows = []
    for line in _events_path().read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return list(reversed(rows[-limit:]))


def _period_end(start: datetime, cycle: BillingCycle) -> datetime | None:
    if cycle == "monthly":
        return start + timedelta(days=30)
    if cycle == "annual":
        return start + timedelta(days=365)
    return None


def list_subscriptions() -> list[SubscriptionRecord]:
    rows: list[SubscriptionRecord] = []
    for line in _subscriptions_path().read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(SubscriptionRecord.model_validate(json.loads(line)))
    return sorted(rows, key=lambda item: item.created_at, reverse=True)


def _write_subscriptions(rows: list[SubscriptionRecord]) -> None:
    with _subscriptions_path().open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row.model_dump(mode="json"), ensure_ascii=False) + "\n")


def maybe_create_or_activate_subscription(intent: PaymentIntent, *, source: str) -> SubscriptionRecord | None:
    package = find_package(intent.package_id)
    if package.get("category") != "subscription" and intent.billing_cycle == "one_time":
        return None
    existing_rows = list_subscriptions()
    for row in existing_rows:
        if row.payment_intent_id == intent.id:
            if row.status != "active":
                row.status = "active"
                row.activated_at = _now()
                row.current_period_start = row.activated_at
                row.current_period_end = _period_end(row.activated_at, row.billing_cycle)
                row.notes.append(f"Activated by {source}")
                _write_subscriptions(existing_rows)
            return row
    start = _now()
    record = SubscriptionRecord(
        id=f"sub_{uuid.uuid4().hex[:12]}",
        created_at=start,
        package_id=intent.package_id,
        plan_name=intent.package_name,
        billing_cycle=intent.billing_cycle,
        amount_inr=intent.amount_inr,
        status="active",
        customer_name=intent.customer_name,
        customer_email=intent.customer_email,
        user_id=intent.user_id,
        organization_id=intent.organization_id,
        payment_intent_id=intent.id,
        provider=intent.provider,
        current_period_start=start,
        current_period_end=_period_end(start, intent.billing_cycle),
        activated_at=start,
        manual_verification_required=intent.provider == "upi_manual",
        notes=[f"Activated by {source}"],
    )
    with _subscriptions_path().open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record.model_dump(mode="json"), ensure_ascii=False) + "\n")
    _append_event({"type": "subscription_activated", "subscription_id": record.id, "payment_intent_id": intent.id, "source": source})
    return record


def admin_update_payment(intent_id: str, payload: AdminPaymentUpdate) -> PaymentIntent:
    intent = get_payment_intent(intent_id)
    intent.status = payload.status
    if payload.payment_reference:
        intent.razorpay_payment_id = payload.payment_reference if intent.provider == "razorpay" else intent.razorpay_payment_id
        intent.metadata["manual_payment_reference"] = payload.payment_reference
    if payload.status == "verified":
        intent.verified_at = _now()
        intent.manual_verification_required = False
        subscription = maybe_create_or_activate_subscription(intent, source="admin_manual_verification")
        if subscription:
            intent.subscription_id = subscription.id
    updated = _replace_intent(intent)
    _append_event({"type": "admin_payment_update", "payment_intent_id": intent_id, "status": payload.status, "note": payload.note})
    return updated


def admin_update_subscription(subscription_id: str, payload: SubscriptionUpdate) -> SubscriptionRecord:
    rows = list_subscriptions()
    for index, row in enumerate(rows):
        if row.id == subscription_id:
            row.status = payload.status
            if payload.status == "cancelled":
                row.cancelled_at = _now()
            if payload.note:
                row.notes.append(payload.note)
            rows[index] = row
            _write_subscriptions(rows)
            _append_event({"type": "admin_subscription_update", "subscription_id": subscription_id, "status": payload.status})
            return row
    raise KeyError("Subscription not found")
