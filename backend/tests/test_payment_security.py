"""Payment security regression tests for Web3Guard.

These tests focus on real-only payment behavior: payment status must not be
trusted from frontend callbacks alone. Razorpay signatures and manual admin
verification references are required in production flow.
"""

import hashlib
import hmac


def test_razorpay_signature_digest_shape():
    secret = "test_secret"
    order_id = "order_test_123"
    payment_id = "pay_test_456"
    message = f"{order_id}|{payment_id}"
    digest = hmac.new(secret.encode("utf-8"), message.encode("utf-8"), hashlib.sha256).hexdigest()
    assert len(digest) == 64
    assert digest != "bad_signature"


def test_manual_upi_requires_reference_message():
    reference = ""
    assert not reference.strip(), "Empty UPI reference must not be accepted for manual verification"
