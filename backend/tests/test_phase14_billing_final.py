from fastapi.testclient import TestClient

from main import app
from app.services.billing_access import plan_limit_matrix

client = TestClient(app)


def test_phase14_billing_status_is_real_only():
    response = client.get('/billing/status')
    assert response.status_code == 200, response.text
    data = response.json()
    assert data['phase'] == 'phase_14_payment_final'
    assert 'frontend-only payment success' in data['blocked_states']
    assert any(item['name'] == 'RAZORPAY_KEY_SECRET' and item['secret'] for item in data['required_env'])
    assert data['webhook_endpoint'] == '/payments/webhook/razorpay'


def test_phase14_plan_limits_include_free_and_paid_activation_rules():
    response = client.get('/billing/plan-limits')
    assert response.status_code == 200, response.text
    plans = response.json()['plans']
    assert any(plan['package_id'] == 'free-scan' and plan['activation_rule'] == 'free_access' for plan in plans)
    assert any(plan['package_id'] == 'builder-monthly' and plan['activation_rule'] == 'verified_payment_or_manual_admin_approval' for plan in plans)
    builder = next(plan for plan in plans if plan['package_id'] == 'builder-monthly')
    assert builder['limits']['scan_runs_per_month'] == 20
    assert builder['limits']['enforcement_status'] == 'visible_entitlement_only_until_usage_counters_are_enabled'


def test_phase14_access_defaults_to_free_when_no_verified_record_requested():
    response = client.get('/billing/access?user_id=phase14_no_records')
    assert response.status_code == 200, response.text
    data = response.json()
    assert data['active_plan']['source'] == 'free_default'
    assert data['active_plan']['package']['id'] == 'free-scan'
    assert data['real_only_note'].lower().startswith('billing access is resolved only')


def test_phase14_service_limit_matrix_is_available_from_service():
    matrix = plan_limit_matrix()
    assert matrix
    assert all('activation_rule' in item for item in matrix)
    assert all('limits' in item for item in matrix)
