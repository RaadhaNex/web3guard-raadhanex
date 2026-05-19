from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_phase34_payment_validation_status_is_truthful():
    response = client.get('/payment-validation/status')
    assert response.status_code == 200
    data = response.json()
    assert data['ok'] is True
    assert data['phase'] == 'phase_34_payment_validation_first_paid_flow'
    assert data['status'] in {'Needs Setup', 'Test Ready', 'Live Ready'}
    assert 'payment successful without backend signature or webhook verification' in data['blocked_claims']
    assert any(item['name'] == 'RAZORPAY_KEY_SECRET' and item['secret'] is True for item in data['env_checks'])
    assert data['masked_keys']['razorpay_key_secret'] is None


def test_phase34_first_paid_flow_has_999_offer_and_blocks_fake_success():
    response = client.get('/payment-validation/first-paid-flow')
    assert response.status_code == 200
    data = response.json()
    assert data['ok'] is True
    assert data['recommended_first_offer']['id'] == 'quick-risk-report'
    assert data['recommended_first_offer']['price_inr'] == 999
    assert any('signature' in shortcut.lower() for shortcut in data['blocked_shortcuts'])
    assert len(data['flow']) >= 5


def test_phase34_checkout_dry_run_never_creates_real_order():
    response = client.post('/payment-validation/checkout-dry-run', json={'package_id': 'quick-risk-report', 'provider_preference': 'auto'})
    assert response.status_code == 200
    data = response.json()
    assert data['ok'] is True
    assert data['dry_run'] is True
    assert data['will_create_real_order'] is False
    assert data['amount_inr'] == 999
    assert data['selected_provider'] in {'razorpay', 'upi_manual', 'blocked_missing_razorpay_keys'}


def test_phase34_access_preview_blocks_paid_access_without_verification():
    response = client.post('/payment-validation/access-preview', json={'package_id': 'quick-risk-report'})
    assert response.status_code == 200
    data = response.json()
    assert data['paid_package'] is True
    assert data['access_granted'] is False
    assert data['reason'] == 'awaiting_verified_payment_or_manual_admin_approval'

    approved = client.post('/payment-validation/access-preview', json={'package_id': 'quick-risk-report', 'manual_admin_approved': True}).json()
    assert approved['access_granted'] is True


def test_phase34_claim_check_blocks_dangerous_payment_and_audit_claims():
    response = client.post('/payment-validation/claim-check', json={'text': '100% secure certified audit and payment successful without verification'})
    assert response.status_code == 200
    data = response.json()
    assert data['allowed'] is False
    assert '100% secure' in data['blocked_terms']
    assert 'certified audit' in data['blocked_terms']
    assert 'payment successful without verification' in data['blocked_terms']


def test_phase34_revenue_readiness_keeps_manual_truth():
    response = client.get('/payment-validation/revenue-readiness')
    assert response.status_code == 200
    data = response.json()
    assert data['ok'] is True
    assert data['recommended_first_plan_id'] == 'quick-risk-report'
    assert data['recommended_first_price_inr'] == 999
    assert 'Preliminary readiness only; not a certified audit.' in data['outreach_offer']
