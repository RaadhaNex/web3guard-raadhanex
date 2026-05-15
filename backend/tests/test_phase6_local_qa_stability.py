from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_health_readiness_has_realness_flags():
    response = client.get('/health/readiness')
    assert response.status_code == 200
    data = response.json()
    assert data['phase'].startswith(('Phase 8', 'Phase 9', 'Phase 10', 'Phase 11'))
    assert data['certified_audit'] is False
    assert data['manual_upi_verification'] is True
    assert data['summary']['failed'] == 0
    assert any(check['key'] == 'admin_token' for check in data['checks'])
    assert any(check['key'] == 'upi_id' for check in data['checks'])


def test_qa_runbook_lists_frontend_routes_and_backend_endpoints():
    response = client.get('/qa/runbook')
    assert response.status_code == 200
    data = response.json()
    assert '/local-qa' in data['essential_frontend_routes']
    assert any(endpoint['path'] == '/scan/unified-url' for endpoint in data['essential_backend_endpoints'])
    assert 'backend_windows' in data['run_commands']
    assert 'frontend_windows' in data['run_commands']


def test_feature_status_endpoint_still_returns_real_only_matrix():
    response = client.get('/scan/feature-status')
    assert response.status_code == 200
    data = response.json()
    assert 'Real-only' in data['rule']
    statuses = {feature['status'] for feature in data['features']}
    assert 'Live' in statuses
    assert any('Manual' in status for status in statuses) or any('Input' in status for status in statuses)


def test_admin_leads_requires_admin_token():
    response = client.get('/admin/leads')
    assert response.status_code in {401, 403}


def test_payment_intent_keeps_manual_verification_wording():
    response = client.post('/payment-intent', json={
        'package_id': 'quick-risk-report',
        'customer_name': 'QA Tester',
        'customer_email': 'qa@example.com',
        'project_name': 'QA Project',
        'billing_cycle': 'one_time',
    })
    assert response.status_code == 200
    data = response.json()
    assert data['intent']['manual_verification_required'] is True
    assert 'manual' in data['disclaimer'].lower()
