from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.services.payment_store import (
    find_package,
    is_razorpay_configured,
    list_payment_events,
    list_payment_intents,
    list_subscriptions,
    load_packages,
    payment_status,
)

ACTIVE_SUBSCRIPTION_STATUSES = {"active"}
VERIFIED_PAYMENT_STATUSES = {"verified", "webhook_verified"}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _package_limit_template(package_id: str, category: str, billing_cycle: str) -> dict[str, Any]:
    """Return honest product limits without pretending server-side rate limiting exists.

    These values are product entitlements shown in billing UI. Enforcement should
    be wired later through authenticated usage counters before hard blocking.
    """

    base: dict[str, dict[str, Any]] = {
        "free-scan": {
            "scan_runs_per_month": 5,
            "saved_reports_per_month": 2,
            "manual_review_slots": 0,
            "team_members": 1,
            "priority_support": False,
            "provider_depth": "Free readiness checks only",
        },
        "builder-monthly": {
            "scan_runs_per_month": 20,
            "saved_reports_per_month": 5,
            "manual_review_slots": 1,
            "team_members": 3,
            "priority_support": True,
            "provider_depth": "Builder readiness + limited manual follow-up",
        },
        "shield-monthly": {
            "scan_runs_per_month": "unlimited_preliminary_local_scans",
            "saved_reports_per_month": 10,
            "manual_review_slots": 2,
            "team_members": 8,
            "priority_support": True,
            "provider_depth": "Shield readiness + wallet/admin review support",
        },
        "launch-annual": {
            "scan_runs_per_month": "fair_use_preliminary_scans",
            "saved_reports_per_month": 25,
            "manual_review_slots": 4,
            "team_members": 15,
            "priority_support": True,
            "provider_depth": "Annual launch support + quarterly readiness review",
        },
    }
    if package_id in base:
        limits = dict(base[package_id])
    elif category == "service":
        limits = {
            "scan_runs_per_month": 0,
            "saved_reports_per_month": 1,
            "manual_review_slots": 1,
            "team_members": 1,
            "priority_support": False,
            "provider_depth": "One-time scoped service entitlement after verified payment",
        }
    else:
        limits = dict(base["free-scan"])

    limits["billing_cycle"] = billing_cycle
    limits["enforcement_status"] = "visible_entitlement_only_until_usage_counters_are_enabled"
    limits["real_only_note"] = "Limits are shown from configured package metadata and verified subscription/payment records. No premium access is granted without verification."
    return limits


def plan_limit_matrix() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for package in load_packages():
        package_id = str(package.get("id"))
        category = str(package.get("category", "service"))
        cycles = package.get("billing_cycles") or ["one_time"]
        rows.append({
            "package_id": package_id,
            "name": package.get("name"),
            "category": category,
            "price_inr": package.get("price_inr", 0),
            "billing_cycles": cycles,
            "popular": bool(package.get("popular", False)),
            "limits": _package_limit_template(package_id, category, str(cycles[0])),
            "activation_rule": "verified_payment_or_manual_admin_approval" if int(package.get("price_inr", 0)) > 0 else "free_access",
        })
    return rows


def billing_final_status() -> dict[str, Any]:
    status = payment_status()
    payments = list_payment_intents()
    subscriptions = list_subscriptions()
    events = list_payment_events(limit=20)
    verified_payments = [item for item in payments if item.status in VERIFIED_PAYMENT_STATUSES]
    active_subscriptions = [item for item in subscriptions if item.status in ACTIVE_SUBSCRIPTION_STATUSES]
    pending_manual = [item for item in payments if item.status in {"created", "manual_verification_pending", "reference_submitted"} and item.manual_verification_required]

    return {
        "ok": True,
        "phase": "phase_14_payment_final",
        "checked_at": _now_iso(),
        "provider_status": status,
        "razorpay_live_ready": bool(is_razorpay_configured() and status.get("razorpay_webhook_configured")),
        "checkout_ready": bool(is_razorpay_configured()),
        "webhook_ready": bool(status.get("razorpay_webhook_configured")),
        "upi_manual_ready": bool(status.get("upi_manual_enabled") and status.get("upi_id_configured")),
        "counts": {
            "payment_intents": len(payments),
            "verified_payments": len(verified_payments),
            "manual_pending": len(pending_manual),
            "subscriptions": len(subscriptions),
            "active_subscriptions": len(active_subscriptions),
            "recent_events": len(events),
        },
        "required_env": [
            {"name": "PAYMENT_MODE", "required_for": "provider selection", "secret": False},
            {"name": "RAZORPAY_ENABLED", "required_for": "Razorpay Checkout", "secret": False},
            {"name": "RAZORPAY_KEY_ID", "required_for": "Razorpay Checkout public key", "secret": False},
            {"name": "RAZORPAY_KEY_SECRET", "required_for": "server-side order and checkout signature verification", "secret": True},
            {"name": "RAZORPAY_WEBHOOK_SECRET", "required_for": "server-side webhook verification", "secret": True},
            {"name": "RAADHANEX_UPI_ID", "required_for": "manual UPI fallback", "secret": False},
        ],
        "webhook_endpoint": "/payments/webhook/razorpay",
        "checkout_flow": [
            "Create order on backend with /payments/razorpay/order or /payment-intent.",
            "Open Razorpay Checkout with backend order_id and public key_id only.",
            "Send order_id, payment_id and signature to /payments/razorpay/verify.",
            "Backend verifies HMAC signature and activates subscription only after match.",
            "Webhook /payments/webhook/razorpay verifies raw body signature and idempotently confirms async events.",
        ],
        "blocked_states": [
            "frontend-only payment success",
            "subscription active without verified payment/manual approval",
            "hardcoded Razorpay key secret in frontend",
            "fake paid plan unlock",
        ],
        "recent_payment_events": events[:10],
        "real_only_note": "Phase 14 enables the final real payment workflow, but provider success is shown only when backend signature or webhook verification passes.",
    }


def _matches_identity(record: Any, user_id: str | None, organization_id: str | None, customer_email: str | None) -> bool:
    if user_id and getattr(record, "user_id", None) == user_id:
        return True
    if organization_id and getattr(record, "organization_id", None) == organization_id:
        return True
    if customer_email and (getattr(record, "customer_email", None) or "").lower() == customer_email.lower():
        return True
    return not any([user_id, organization_id, customer_email])


def billing_access_summary(user_id: str | None = None, organization_id: str | None = None, customer_email: str | None = None) -> dict[str, Any]:
    subscriptions = [
        item for item in list_subscriptions()
        if item.status in ACTIVE_SUBSCRIPTION_STATUSES and _matches_identity(item, user_id, organization_id, customer_email)
    ]
    verified_services = [
        item for item in list_payment_intents()
        if item.status in VERIFIED_PAYMENT_STATUSES and _matches_identity(item, user_id, organization_id, customer_email)
    ]

    selected_subscription = sorted(subscriptions, key=lambda item: (item.amount_inr, item.created_at), reverse=True)[0] if subscriptions else None

    if selected_subscription:
        package_id = selected_subscription.package_id
        try:
            package = find_package(package_id)
            category = str(package.get("category", "subscription"))
        except KeyError:
            package = {"id": package_id, "name": selected_subscription.plan_name, "category": "subscription"}
            category = "subscription"
        active_plan = {
            "source": "active_subscription",
            "subscription": selected_subscription.model_dump(mode="json"),
            "package": package,
            "limits": _package_limit_template(package_id, category, selected_subscription.billing_cycle),
        }
    else:
        free_package = find_package("free-scan")
        active_plan = {
            "source": "free_default",
            "subscription": None,
            "package": free_package,
            "limits": _package_limit_template("free-scan", "free", "one_time"),
        }

    return {
        "ok": True,
        "checked_at": _now_iso(),
        "identity": {
            "user_id": user_id,
            "organization_id": organization_id,
            "customer_email": customer_email,
        },
        "active_plan": active_plan,
        "active_subscriptions": [item.model_dump(mode="json") for item in subscriptions],
        "verified_service_payments": [item.model_dump(mode="json") for item in verified_services],
        "real_only_note": "Billing access is resolved only from stored active subscriptions and verified payment records. If no verified record exists, free-default limits are returned.",
    }
