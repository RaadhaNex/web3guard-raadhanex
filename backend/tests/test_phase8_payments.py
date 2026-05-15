import hashlib
import hmac
import json
from pathlib import Path

from fastapi.testclient import TestClient
from main import app
from app.core.config import settings

client = TestClient(app)


def test_payment_status_real_only_flags():
    response = client.get('/payments/status')
    assert response.status_code == 200
    data = response.json()
    assert data['manual_verification_fallback'] is True
    assert 'payment successful before' in ' '.join(data['blocked_claims']).lower()


def test_manual_upi_intent_still_works_without_razorpay_keys():
    response = client.post('/payment-intent', json={
        'package_id': 'quick-risk-report',
        'customer_name': 'Phase 8 Tester',
        'customer_email': 'phase8@example.com',
        'project_name': 'Phase 8 Manual UPI',
        'provider_preference': 'upi_manual',
    })
    assert response.status_code == 200, response.text
    intent = response.json()['intent']
    assert intent['provider'] == 'upi_manual'
    assert intent['upi_deep_link'].startswith('upi://pay')
    assert intent['manual_verification_required'] is True


def test_razorpay_only_fails_honestly_when_not_configured():
    old_enabled = settings.razorpay_enabled
    old_key = settings.razorpay_key_id
    old_secret = settings.razorpay_key_secret
    settings.razorpay_enabled = False
    settings.razorpay_key_id = None
    settings.razorpay_key_secret = None
    try:
        response = client.post('/payment-intent', json={
            'package_id': 'quick-risk-report',
            'customer_email': 'phase8@example.com',
            'provider_preference': 'razorpay',
        })
        assert response.status_code == 400
        assert 'Razorpay is requested' in response.json()['detail']
    finally:
        settings.razorpay_enabled = old_enabled
        settings.razorpay_key_id = old_key
        settings.razorpay_key_secret = old_secret


def test_razorpay_signature_verifier_marks_payment_verified(monkeypatch):
    # Make the verifier deterministic without calling Razorpay order-create API.
    old_secret = settings.razorpay_key_secret
    settings.razorpay_key_secret = 'test_secret'
    try:
        create = client.post('/payment-intent', json={
            'package_id': 'builder-monthly',
            'customer_email': 'sub@example.com',
            'provider_preference': 'upi_manual',
            'billing_cycle': 'monthly',
        })
        assert create.status_code == 200, create.text
        intent = create.json()['intent']
        path = Path(settings.payment_intents_file)
        rows = []
        for line in path.read_text(encoding='utf-8').splitlines():
            row = json.loads(line)
            if row['id'] == intent['id']:
                row['provider'] = 'razorpay'
                row['razorpay_enabled'] = True
                row['razorpay_order_id'] = 'order_phase8test'
                row['razorpay_key_id'] = 'rzp_test_key'
                row['manual_verification_required'] = False
            rows.append(row)
        path.write_text('\n'.join(json.dumps(row) for row in rows) + '\n', encoding='utf-8')
        message = 'order_phase8test|pay_phase8test'
        signature = hmac.new(b'test_secret', message.encode(), hashlib.sha256).hexdigest()
        verify = client.post('/payments/razorpay/verify', json={
            'payment_intent_id': intent['id'],
            'razorpay_order_id': 'order_phase8test',
            'razorpay_payment_id': 'pay_phase8test',
            'razorpay_signature': signature,
        })
        assert verify.status_code == 200, verify.text
        verified = verify.json()['payment_intent']
        assert verified['status'] == 'verified'
        assert verified['subscription_id']
    finally:
        settings.razorpay_key_secret = old_secret
