"""Safe Razorpay webhook signature smoke test for Web3Guard.

This script does not mark a real payment successful unless you pass a real
Razorpay order id that already exists in Web3Guard and the amount/currency/status
match the stored payment intent. By default it sends a signed event for a fake
order id, so the expected mutation is `no_matching_payment_intent`.

PowerShell example:
  $env:BACKEND_URL="https://your-render-backend.onrender.com"
  $env:RAZORPAY_WEBHOOK_SECRET="your_test_webhook_secret"
  python scripts/razorpay_webhook_signature_test.py

Optional real test order:
  $env:RAZORPAY_TEST_ORDER_ID="order_xxx"
  $env:RAZORPAY_TEST_AMOUNT_PAISE="99900"
  python scripts/razorpay_webhook_signature_test.py
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import sys
import time
import urllib.error
import urllib.request

backend_url = os.getenv("BACKEND_URL", "http://localhost:8000").rstrip("/")
secret = os.getenv("RAZORPAY_WEBHOOK_SECRET", "")
order_id = os.getenv("RAZORPAY_TEST_ORDER_ID", "order_web3guard_signature_smoke_only")
payment_id = os.getenv("RAZORPAY_TEST_PAYMENT_ID", "pay_web3guard_signature_smoke_only")
amount_paise = int(os.getenv("RAZORPAY_TEST_AMOUNT_PAISE", "100"))
event_id = os.getenv("RAZORPAY_TEST_EVENT_ID", f"evt_web3guard_smoke_{int(time.time())}")

if not secret:
    print("RAZORPAY_WEBHOOK_SECRET env is required. Do not paste it into frontend code.", file=sys.stderr)
    sys.exit(2)

payload = {
    "id": event_id,
    "event": "payment.captured",
    "payload": {
        "payment": {
            "entity": {
                "id": payment_id,
                "entity": "payment",
                "order_id": order_id,
                "amount": amount_paise,
                "currency": "INR",
                "status": "captured",
                "captured": True,
            }
        }
    },
}
raw = json.dumps(payload, separators=(",", ":")).encode("utf-8")
signature = hmac.new(secret.encode("utf-8"), raw, hashlib.sha256).hexdigest()
request = urllib.request.Request(
    f"{backend_url}/payments/webhook/razorpay",
    data=raw,
    method="POST",
    headers={"content-type": "application/json", "x-razorpay-signature": signature},
)

try:
    with urllib.request.urlopen(request, timeout=30) as response:
        body = response.read().decode("utf-8")
        print(f"HTTP {response.status}")
        print(body)
except urllib.error.HTTPError as exc:
    print(f"HTTP {exc.code}", file=sys.stderr)
    print(exc.read().decode("utf-8", errors="replace"), file=sys.stderr)
    sys.exit(1)
except Exception as exc:
    print(str(exc), file=sys.stderr)
    sys.exit(1)
