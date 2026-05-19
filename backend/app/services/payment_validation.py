from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.core.config import settings
from app.services.billing_access import plan_limit_matrix
from app.services.payment_store import (
    find_package,
    is_razorpay_configured,
    list_payment_events,
    list_payment_intents,
    list_subscriptions,
    load_packages,
    payment_status,
)

PHASE34_VERSION = "phase_34_payment_validation_first_paid_flow"
BLOCKED_PAYMENT_CLAIMS = [
    "payment successful without backend signature or webhook verification",
    "subscription active without verified payment or manual admin approval",
    "Razorpay live-ready without live keys and webhook secret",
    "customer paid without a persisted payment intent/event",
    "refund/compliance/GST status without real operational records",
    "certified audit or audited by Web3Guard claim",
    "100% secure claim",
]
SAFE_PAYMENT_STATES = {
    "created": "Payment intent created; not paid.",
    "razorpay_order_created": "Razorpay order created; payment is not successful yet.",
    "manual_verification_pending": "Manual UPI/reference review is pending.",
    "reference_submitted": "User submitted a manual reference; admin must verify.",
    "verified": "Checkout signature verified by backend.",
    "webhook_verified": "Signed Razorpay webhook verified by backend.",
    "failed": "Payment failed or was rejected.",
    "refunded": "Refunded state requires real payment records; no fake refund status.",
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _mask_secret(value: str | None, *, keep: int = 5) -> str | None:
    if not value:
        return None
    clean = value.strip()
    if len(clean) <= keep:
        return "*" * len(clean)
    return f"{clean[:keep]}...{clean[-4:]}"


def _razorpay_mode() -> str:
    key_id = (settings.razorpay_key_id or "").strip()
    if key_id.startswith("rzp_test_"):
        return "test"
    if key_id.startswith("rzp_live_"):
        return "live"
    if key_id:
        return "unknown"
    return "not_configured"


def _env_check(name: str, configured: bool, *, secret: bool, required_for: str, value_preview: str | None = None) -> dict[str, Any]:
    return {
        "name": name,
        "configured": configured,
        "status": "Assessed" if configured else "Needs API Key",
        "secret": secret,
        "required_for": required_for,
        "value_preview": value_preview if not secret else None,
    }


def payment_validation_status() -> dict[str, Any]:
    provider = payment_status()
    mode = _razorpay_mode()
    checkout_ready = bool(is_razorpay_configured())
    webhook_ready = bool(provider.get("razorpay_webhook_configured"))
    test_ready = bool(checkout_ready and webhook_ready and mode == "test")
    live_ready = bool(checkout_ready and webhook_ready and mode == "live")
    payments = list_payment_intents()
    events = list_payment_events(limit=50)
    subscriptions = list_subscriptions()
    verified = [item for item in payments if item.status in {"verified", "webhook_verified"}]
    pending = [item for item in payments if item.status not in {"verified", "webhook_verified", "failed", "refunded"}]

    gates = [
        {
            "key": "razorpay_enabled",
            "label": "Razorpay enabled",
            "passed": bool(settings.razorpay_enabled),
            "status": "Assessed" if settings.razorpay_enabled else "Provider Not Configured",
            "fix": "Set RAZORPAY_ENABLED=true only after adding backend keys.",
        },
        {
            "key": "razorpay_keys",
            "label": "Razorpay key id + secret",
            "passed": checkout_ready,
            "status": "Assessed" if checkout_ready else "Needs API Key",
            "fix": "Set RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET in Render backend env.",
        },
        {
            "key": "razorpay_webhook_secret",
            "label": "Webhook secret",
            "passed": webhook_ready,
            "status": "Assessed" if webhook_ready else "Needs API Key",
            "fix": "Create Razorpay webhook and set RAZORPAY_WEBHOOK_SECRET.",
        },
        {
            "key": "payment_mode",
            "label": "Payment mode allows Razorpay",
            "passed": settings.payment_mode in {"razorpay", "razorpay_or_upi_manual"},
            "status": "Assessed" if settings.payment_mode in {"razorpay", "razorpay_or_upi_manual"} else "Manual review required",
            "fix": "Use PAYMENT_MODE=razorpay_or_upi_manual for first paid validation.",
        },
        {
            "key": "manual_fallback",
            "label": "Manual UPI fallback visible",
            "passed": bool(provider.get("upi_manual_enabled")),
            "status": "Assessed" if provider.get("upi_manual_enabled") else "Manual review required",
            "fix": "Keep manual verification fallback until live Razorpay is proven.",
        },
    ]

    return {
        "ok": True,
        "phase": PHASE34_VERSION,
        "checked_at": _now_iso(),
        "detected_mode": mode,
        "status": "Live Ready" if live_ready else ("Test Ready" if test_ready else "Needs Setup"),
        "test_mode_ready": test_ready,
        "live_mode_ready": live_ready,
        "checkout_ready": checkout_ready,
        "webhook_ready": webhook_ready,
        "provider_status": provider,
        "masked_keys": {
            "razorpay_key_id": _mask_secret(settings.razorpay_key_id, keep=9),
            "razorpay_key_secret": None,
            "razorpay_webhook_secret": None,
        },
        "env_checks": [
            _env_check("RAZORPAY_ENABLED", bool(settings.razorpay_enabled), secret=False, required_for="checkout", value_preview=str(settings.razorpay_enabled).lower()),
            _env_check("RAZORPAY_KEY_ID", bool(settings.razorpay_key_id), secret=False, required_for="checkout", value_preview=_mask_secret(settings.razorpay_key_id, keep=9)),
            _env_check("RAZORPAY_KEY_SECRET", bool(settings.razorpay_key_secret), secret=True, required_for="checkout signature verification"),
            _env_check("RAZORPAY_WEBHOOK_SECRET", bool(settings.razorpay_webhook_secret), secret=True, required_for="signed webhook verification"),
            _env_check("PAYMENT_MODE", settings.payment_mode in {"razorpay", "razorpay_or_upi_manual"}, secret=False, required_for="checkout selection", value_preview=settings.payment_mode),
        ],
        "gates": gates,
        "counts": {
            "payment_intents": len(payments),
            "verified_payments": len(verified),
            "pending_payments": len(pending),
            "subscriptions": len(subscriptions),
            "payment_events": len(events),
        },
        "blocked_claims": BLOCKED_PAYMENT_CLAIMS,
        "real_only_note": "Payment success and paid access are shown only after backend verification or manual admin approval. Order creation alone is never treated as paid.",
    }


def first_paid_flow() -> dict[str, Any]:
    paid_packages = [pkg for pkg in load_packages() if int(pkg.get("price_inr", 0)) > 0]
    starter = next((pkg for pkg in paid_packages if int(pkg.get("price_inr", 0)) <= 999), paid_packages[0] if paid_packages else None)
    return {
        "ok": True,
        "phase": PHASE34_VERSION,
        "recommended_first_offer": starter,
        "flow": [
            {"step": 1, "title": "Run free scan", "status": "Assessed", "note": "User sees real scanner output and Not Assessed modules clearly."},
            {"step": 2, "title": "Show pilot report preview", "status": "Assessed", "note": "Preview must include limitations and no certified-audit claim."},
            {"step": 3, "title": "Create backend payment intent", "status": "Assessed", "note": "Backend creates UPI/manual or real Razorpay order based on configured keys."},
            {"step": 4, "title": "Verify checkout signature/webhook", "status": "Assessed", "note": "Only verified callback/webhook can mark payment verified."},
            {"step": 5, "title": "Unlock paid deliverable", "status": "Manual review required", "note": "First paid deliverable should be manually reviewed until enough payment/support ops are proven."},
        ],
        "first_paid_cta": "Unlock Quick Risk Scan Report — ₹999",
        "blocked_shortcuts": [
            "Do not unlock report on frontend callback alone or without verified signature/webhook.",
            "Do not mark subscription active on order_id creation.",
            "Do not show fake invoice/GST/refund data.",
            "Do not hide Not Assessed modules inside a paid report.",
        ],
    }


def checkout_dry_run(package_id: str, billing_cycle: str = "one_time", provider_preference: str = "auto") -> dict[str, Any]:
    package = find_package(package_id)
    amount = int(package.get("price_inr", 0))
    provider = "free" if amount <= 0 else "upi_manual"
    if amount > 0 and provider_preference == "razorpay":
        provider = "razorpay" if is_razorpay_configured() else "blocked_missing_razorpay_keys"
    elif amount > 0 and provider_preference == "auto":
        provider = "razorpay" if is_razorpay_configured() and settings.payment_mode in {"razorpay", "razorpay_or_upi_manual"} else "upi_manual"

    status = "Ready" if provider in {"free", "razorpay", "upi_manual"} else "Needs API Key"
    next_steps: list[str]
    if provider == "razorpay":
        next_steps = [
            "POST /payment-intent with provider_preference=razorpay to create a real order.",
            "Open Razorpay Checkout with returned checkout options.",
            "POST /payments/razorpay/verify after checkout callback.",
            "Verify signed /payments/webhook/razorpay for asynchronous confirmation.",
        ]
    elif provider == "upi_manual":
        next_steps = [
            "Create a manual UPI payment intent.",
            "User pays using UPI app and submits reference.",
            "Admin verifies payment before paid access or deliverable.",
        ]
    elif provider == "free":
        next_steps = ["Free package requires no payment. Do not create fake payment records for free access."]
    else:
        next_steps = ["Configure Razorpay backend keys or use provider_preference=upi_manual."]

    return {
        "ok": True,
        "phase": PHASE34_VERSION,
        "dry_run": True,
        "package": package,
        "billing_cycle": billing_cycle,
        "provider_preference": provider_preference,
        "selected_provider": provider,
        "status": status,
        "amount_inr": amount,
        "will_create_real_order": False,
        "real_order_endpoint": "/payment-intent",
        "next_steps": next_steps,
        "real_only_note": "This endpoint never creates a payment/order. It explains which real flow will be used before the frontend calls payment-intent.",
    }


def access_preview(package_id: str, verified: bool = False, manual_admin_approved: bool = False) -> dict[str, Any]:
    package = find_package(package_id)
    limits = next((row for row in plan_limit_matrix() if row["package_id"] == package_id), None)
    paid = int(package.get("price_inr", 0)) > 0
    access_granted = (not paid) or bool(verified or manual_admin_approved)
    return {
        "ok": True,
        "package_id": package_id,
        "package_name": package.get("name"),
        "paid_package": paid,
        "access_granted": access_granted,
        "status": "Assessed" if access_granted else "Manual review required",
        "reason": "free_access" if not paid else ("verified_payment_or_manual_approval" if access_granted else "awaiting_verified_payment_or_manual_admin_approval"),
        "limits": limits.get("limits") if limits else {},
        "blocked_states": [
            "frontend_only_payment_success",
            "razorpay_order_created_without_signature",
            "webhook_event_without_valid_signature",
            "manual_reference_without_admin_review",
        ],
    }


def claim_check(text: str) -> dict[str, Any]:
    clean = (text or "").lower()
    blocked_patterns = [
        "100% secure",
        "certified audit",
        "audited by web3guard",
        "payment successful without verification",
        "subscription active without payment",
        "guaranteed secure",
        "risk free",
        "verified customer payment" if "without" in clean else "__never_match__",
    ]
    hits = [pattern for pattern in blocked_patterns if pattern != "__never_match__" and pattern in clean]
    return {
        "ok": True,
        "allowed": len(hits) == 0,
        "blocked_terms": hits,
        "safe_replacement": "Payment and access are confirmed only after backend verification. Web3Guard provides pre-audit readiness guidance, not a certified audit or security guarantee.",
        "blocked_claims": BLOCKED_PAYMENT_CLAIMS,
    }


def revenue_readiness() -> dict[str, Any]:
    status = payment_validation_status()
    plans = plan_limit_matrix()
    paid = [item for item in plans if int(item.get("price_inr", 0)) > 0]
    return {
        "ok": True,
        "phase": PHASE34_VERSION,
        "ready_for_first_paid_user": bool(status["test_mode_ready"] or status["provider_status"].get("upi_id_configured")),
        "recommended_first_plan_id": "quick-risk-report",
        "recommended_first_price_inr": 999,
        "paid_plan_count": len(paid),
        "checklist": [
            {"item": "Razorpay test order", "status": "Ready" if status["test_mode_ready"] else "Needs API Key"},
            {"item": "Signed webhook verification", "status": "Ready" if status["webhook_ready"] else "Needs API Key"},
            {"item": "Manual UPI fallback", "status": "Ready" if status["provider_status"].get("upi_id_configured") else "Manual review required"},
            {"item": "Paid access only after verification", "status": "Assessed"},
            {"item": "First paid offer visible", "status": "Assessed" if any(item["package_id"] == "quick-risk-report" for item in paid) else "Manual review required"},
        ],
        "outreach_offer": "₹999 Quick Risk Scan Report for first 10 Indian Web3 founders. Preliminary readiness only; not a certified audit.",
        "real_only_note": "Revenue readiness means the payment path can be tested or manually verified. It does not mean live payments are active unless Razorpay/live UPI records prove it.",
    }
