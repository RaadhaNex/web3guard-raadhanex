from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_india_launch_status():
    response = client.get('/india-launch/status')
    assert response.status_code == 200
    data = response.json()
    assert data['ok'] is True
    assert data['phase'] == '21'
    assert 'India Launch Pack' in data['name']
    assert any(mode['id'] == 'hinglish' for mode in data['language_modes'])
    assert 'audited by Web3Guard' in data['blocked_wording']


def test_india_launch_pack_empty_user_is_honest():
    response = client.get('/india-launch/pack', params={'user_id': 'phase21-empty-user', 'mode': 'hinglish'})
    assert response.status_code == 200
    data = response.json()
    assert data['ok'] is True
    assert data['mode'] == 'hinglish'
    assert data['project']['name'] == 'Your Web3 project'
    assert data['readiness']['note'].lower().startswith('launch trust readiness')
    assert data['founder_checklist']
    assert data['investor_summary']['safe_disclaimer']
    assert 'certified audit' in data['safe_share_copy']
    assert 'audited by Web3Guard' in data['blocked_wording']


def test_india_launch_hindi_mode():
    response = client.get('/india-launch/pack', params={'user_id': 'phase21-empty-user', 'mode': 'hindi'})
    assert response.status_code == 200
    data = response.json()
    assert data['mode'] == 'hindi'
    assert data['public_trust_summary']['disclaimer']
