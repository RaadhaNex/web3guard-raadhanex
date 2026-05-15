from fastapi import APIRouter, Header, HTTPException, Request

from app.models.schemas import PaymentIntentCreate, RazorpayVerifyRequest
from app.services.payment_store import (
    create_payment_intent,
    get_payment_intent,
    handle_razorpay_webhook,
    list_payment_events,
    list_payment_intents,
    list_subscriptions,
    payment_status,
    verify_checkout_signature,
)

router = APIRouter(tags=["payments"])


@router.get("/payments/status")
def get_payment_status():
    return payment_status()


@router.post("/payment-intent")
def payment_intent(payload: PaymentIntentCreate):
    try:
        intent = create_payment_intent(payload)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Package not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    razorpay_steps = [
        "Backend creates a real Razorpay order only if RAZORPAY_ENABLED=true and keys are configured.",
        "Frontend opens Razorpay Checkout with the returned order_id.",
        "After payment, frontend sends order_id, payment_id and signature to backend.",
        "Backend verifies signature before marking payment verified.",
    ]
    manual_steps = [
        "Open the UPI payment link and complete payment.",
        "Copy the UPI transaction/reference ID from your payment app.",
        "Submit the review request form with the same reference ID.",
        "RAADHANEX verifies payment manually before starting paid review or activating subscription.",
    ]
    return {
        "ok": True,
        "intent": intent,
        "payment_status": payment_status(),
        "razorpay_steps": razorpay_steps if intent.provider == "razorpay" else [],
        "manual_steps": manual_steps,
        "disclaimer": "Payment is marked verified only after Razorpay signature/webhook verification or manual admin approval. No fake payment success state is used.",
    }


@router.post("/payments/razorpay/order")
def create_razorpay_order(payload: PaymentIntentCreate):
    """Create a real Razorpay order through the existing PaymentIntent flow.

    This endpoint is an explicit Patch H alias for checkout integrations. It
    never marks success on order creation; success requires checkout signature
    verification and/or a verified raw-body webhook.
    """
    try:
        forced_payload = payload.model_copy(update={"provider_preference": "razorpay"})
        intent = create_payment_intent(forced_payload)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Package not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "ok": True,
        "intent": intent,
        "order_id": intent.razorpay_order_id,
        "key_id": intent.razorpay_key_id,
        "checkout_options": intent.razorpay_checkout_options,
        "real_only_note": "Razorpay order created from the real Razorpay API. Payment is not successful until signature/webhook verification passes.",
    }


@router.get("/payments/{payment_intent_id}")
def get_payment(payment_intent_id: str):
    try:
        return {"payment_intent": get_payment_intent(payment_intent_id)}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Payment intent not found") from exc


@router.get("/payments")
def list_payments():
    return {"payment_intents": list_payment_intents()}


@router.post("/payments/razorpay/verify")
def verify_razorpay_payment(payload: RazorpayVerifyRequest):
    try:
        intent = verify_checkout_signature(payload)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Payment intent not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "ok": True,
        "payment_intent": intent,
        "message": "Razorpay checkout signature verified against backend secret. Payment is marked verified only for this matching payment intent; webhook verification remains supported for asynchronous confirmation.",
    }


@router.post("/payments/webhook/razorpay")
async def razorpay_webhook(request: Request, x_razorpay_signature: str | None = Header(default=None)):
    raw_body = await request.body()
    try:
        result = handle_razorpay_webhook(raw_body, x_razorpay_signature)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return result


@router.get("/payments/events")
def payment_events(limit: int = 100):
    return {"events": list_payment_events(limit=limit)}


@router.get("/subscriptions")
def subscriptions():
    return {"subscriptions": list_subscriptions()}
