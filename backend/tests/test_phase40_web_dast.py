from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_web_dast_status_blocks_dangerous_tests():
    res = client.get('/web-dast/status')
    assert res.status_code == 200
    data = res.json()
    assert data['ok'] is True
    assert data['full_active'] == 'disabled_by_default_admin_manual_only'
    assert 'brute force' in data['blocked_dangerous_tests']
    assert 'private key/seed/mnemonic collection' in data['blocked_dangerous_tests']


def test_safe_url_rejects_localhost_and_private_scope():
    res = client.post('/web-dast/safe-url-check', json={'target_url': 'http://localhost:8000', 'allowed_domains': ['localhost']})
    assert res.status_code == 200
    data = res.json()
    assert data['ok'] is False
    assert data['status'] == 'Scope Rejected'
    assert any('private' in reason.lower() or 'local' in reason.lower() for reason in data['reasons'])


def test_verification_token_flow_locks_scope_without_live_attack():
    start = client.post('/web-dast/verify/start', json={'target_url': 'https://example.com', 'allowed_domains': ['example.com'], 'contact_email': 'security@example.com', 'permission_type': 'owner'})
    assert start.status_code == 200
    start_data = start.json()
    assert start_data['ok'] is True
    token = start_data['token']

    check = client.post('/web-dast/verify/check', json={'target_url': 'https://example.com', 'allowed_domains': ['example.com'], 'contact_email': 'security@example.com', 'method': 'dns_txt', 'supplied_token': token})
    assert check.status_code == 200
    data = check.json()
    assert data['verified'] is True
    assert data['scope_locked'] is True


def test_passive_baseline_requires_permission_and_does_not_fake_live_scan():
    denied = client.post('/web-dast/passive-baseline', json={'target_url': 'https://example.com', 'allowed_domains': ['example.com']})
    assert denied.status_code == 200
    assert denied.json()['status'] == 'Permission Required'

    safe = client.post('/web-dast/passive-baseline', json={'target_url': 'https://example.com', 'allowed_domains': ['example.com'], 'permission_type': 'owner', 'authorized_acknowledged': True, 'run_live': False})
    assert safe.status_code == 200
    data = safe.json()
    assert data['ok'] is True
    assert data['status'] == 'Not assessed yet'
    assert data['findings'][0]['status'] == 'Not assessed yet'
    assert 'brute force' in data['blocked_tests']


def test_light_active_blocks_destructive_requests_even_when_verified():
    res = client.post('/web-dast/light-active', json={'target_url': 'https://example.com', 'allowed_domains': ['example.com'], 'verification_passed': True, 'request_destructive_tests': True})
    assert res.status_code == 200
    data = res.json()
    assert data['ok'] is False
    assert data['status'] == 'Full Active Disabled'
    assert 'RCE exploitation' in data['blocked_tests']


def test_claim_checker_blocks_hacking_wording():
    res = client.post('/web-dast/claim-check', json={'text': 'Active hacking scan can brute force and hack any website', 'real_only_acknowledged': True})
    assert res.status_code == 200
    data = res.json()
    assert data['ok'] is False
    assert 'hack any website' in data['violations']
