# Phase 8 — Razorpay + UPI Subscription System

Web3Guard AI by RAADHANEX now has a real payment foundation. It does **not** fake payment success.

## What is live

- Payment gateway status endpoint: `GET /payments/status`
- Payment intent endpoint: `POST /payment-intent`
- Razorpay order creation when backend keys are configured
- Razorpay Checkout frontend integration
- Razorpay Checkout signature verification: `POST /payments/razorpay/verify`
- Razorpay webhook verification: `POST /payments/webhook/razorpay`
- UPI manual fallback deep link
- Admin payments dashboard: `/admin/payments`
- Billing status page: `/billing`
- Subscription records created only after verified/admin-approved payments
- Supabase migration for payments/subscriptions

## Real-only payment rule

A payment can become verified only through one of these paths:

1. Razorpay Checkout returns `razorpay_order_id`, `razorpay_payment_id`, and `razorpay_signature`; backend verifies the HMAC signature.
2. Razorpay webhook is received and backend verifies `X-Razorpay-Signature` using `RAZORPAY_WEBHOOK_SECRET`.
3. Admin manually verifies an offline/UPI payment and updates status from `/admin/payments`.

Frontend state alone never activates a subscription.

## Backend env

```env
PAYMENT_MODE=razorpay_or_upi_manual
RAZORPAY_ENABLED=true
RAZORPAY_KEY_ID=rzp_test_xxxxx
RAZORPAY_KEY_SECRET=your_secret_backend_only
RAZORPAY_WEBHOOK_SECRET=your_webhook_secret_backend_only
RAZORPAY_API_BASE=https://api.razorpay.com/v1
PAYMENT_INTENTS_FILE=app/data/payment_intents.jsonl
PAYMENT_EVENTS_FILE=app/data/payment_events.jsonl
SUBSCRIPTIONS_FILE=app/data/subscriptions.jsonl
```

## Frontend env

```env
NEXT_PUBLIC_RAZORPAY_KEY_ID=rzp_test_xxxxx
```

Never add `RAZORPAY_KEY_SECRET` or `RAZORPAY_WEBHOOK_SECRET` to frontend.

## Manual UPI fallback

Manual UPI remains useful for users who want to pay from any UPI app. It creates a payment intent and UPI deep link, but access/review starts only after admin verification.

## What is not yet live

- Razorpay recurring subscription API is not used yet.
- GST invoice PDF generation is not added yet.
- Refund automation is not added yet.
- Plan gating/usage credits are not enforced yet.

These are next payment hardening phases.
