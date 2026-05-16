from __future__ import annotations

import hashlib
import hmac
import json
from datetime import datetime, timezone

import pytest

from app.core.config import settings
from app.models.schemas import PaymentIntent
from app.services.payment_store import handle_razorpay_webhook, verify_checkout_signature, get_payment_intent


def _write_intent(path, *, amount_paise: int = 99900, status: str = "razorpay_order_created") -> PaymentIntent:
    intent = PaymentIntent(
        id="pay_final_external",
        created_at=datetime(2026, 5, 16, tzinfo=timezone.utc),
        package_id="quick-risk-report",
        package_name="Quick Risk Scan Report",
        amount_inr=amount_paise // 100,
        amount_paise=amount_paise,
        billing_cycle="one_time",
        provider="razorpay",
        provider_preference="razorpay",
        upi_id="raadhanex@upi",
        upi_name="RAADHANEX",
        manual_verification_required=False,
        razorpay_enabled=True,
        razorpay_key_id="rzp_test_key",
        razorpay_order_id="order_final_external",
        status=status,
        note="Order only; not paid yet.",
    )
    path.write_text(json.dumps(intent.model_dump(mode="json")) + "\n", encoding="utf-8")
    return intent


def _signed_webhook(payload: dict, secret: str) -> tuple[bytes, str]:
    raw = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    sig = hmac.new(secret.encode("utf-8"), raw, hashlib.sha256).hexdigest()
    return raw, sig


def test_bad_checkout_signature_does_not_downgrade_existing_verified_payment(tmp_path, monkeypatch):
    payments_file = tmp_path / "payments.jsonl"
    events_file = tmp_path / "events.jsonl"
    subs_file = tmp_path / "subs.jsonl"
    monkeypatch.setattr(settings, "payment_intents_file", str(payments_file))
    monkeypatch.setattr(settings, "payment_events_file", str(events_file))
    monkeypatch.setattr(settings, "subscriptions_file", str(subs_file))
    monkeypatch.setattr(settings, "razorpay_key_secret", "test_secret")

    _write_intent(payments_file, status="verified")
    bad = type("Payload", (), {
        "payment_intent_id": "pay_final_external",
        "razorpay_order_id": "order_final_external",
        "razorpay_payment_id": "pay_bad_callback",
        "razorpay_signature": "bad-signature",
    })()

    with pytest.raises(ValueError, match="Invalid Razorpay payment signature"):
        verify_checkout_signature(bad)

    assert get_payment_intent("pay_final_external").status == "verified"
    assert "mutation\": \"none" in events_file.read_text(encoding="utf-8")


def test_razorpay_webhook_blocks_amount_mismatch_and_keeps_intent_unverified(tmp_path, monkeypatch):
    payments_file = tmp_path / "payments.jsonl"
    events_file = tmp_path / "events.jsonl"
    subs_file = tmp_path / "subs.jsonl"
    monkeypatch.setattr(settings, "payment_intents_file", str(payments_file))
    monkeypatch.setattr(settings, "payment_events_file", str(events_file))
    monkeypatch.setattr(settings, "subscriptions_file", str(subs_file))
    monkeypatch.setattr(settings, "razorpay_webhook_secret", "webhook_secret")

    _write_intent(payments_file, amount_paise=99900)
    payload = {
        "id": "evt_amount_mismatch",
        "event": "payment.captured",
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_real",
                    "entity": "payment",
                    "order_id": "order_final_external",
                    "amount": 100,
                    "currency": "INR",
                    "status": "captured",
                    "captured": True,
                }
            }
        },
    }
    raw, sig = _signed_webhook(payload, "webhook_secret")

    result = handle_razorpay_webhook(raw, sig)

    assert result["mutation"] == "blocked_validation_mismatch"
    assert result["payment_intent"] is None
    assert get_payment_intent("pay_final_external").status == "razorpay_order_created"
    assert "amount_mismatch" in events_file.read_text(encoding="utf-8")


def test_razorpay_webhook_verifies_matching_payment_and_is_idempotent(tmp_path, monkeypatch):
    payments_file = tmp_path / "payments.jsonl"
    events_file = tmp_path / "events.jsonl"
    subs_file = tmp_path / "subs.jsonl"
    monkeypatch.setattr(settings, "payment_intents_file", str(payments_file))
    monkeypatch.setattr(settings, "payment_events_file", str(events_file))
    monkeypatch.setattr(settings, "subscriptions_file", str(subs_file))
    monkeypatch.setattr(settings, "razorpay_webhook_secret", "webhook_secret")

    _write_intent(payments_file, amount_paise=99900)
    payload = {
        "id": "evt_valid_payment",
        "event": "payment.captured",
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_real",
                    "entity": "payment",
                    "order_id": "order_final_external",
                    "amount": 99900,
                    "currency": "INR",
                    "status": "captured",
                    "captured": True,
                }
            }
        },
    }
    raw, sig = _signed_webhook(payload, "webhook_secret")

    result = handle_razorpay_webhook(raw, sig)
    duplicate = handle_razorpay_webhook(raw, sig)

    assert result["mutation"] == "payment_verified"
    assert result["payment_intent"].status == "webhook_verified"
    assert duplicate["duplicate"] is True
    assert get_payment_intent("pay_final_external").status == "webhook_verified"
