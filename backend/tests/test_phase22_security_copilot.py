from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_security_copilot_status_real_only():
    response = client.get('/security-copilot/status')
    assert response.status_code == 200
    data = response.json()
    assert data['ok'] is True
    assert data['mode']['mode'] in {'local_fallback', 'provider_ready'}
    assert 'ai_auditor_claim' in data['blocked']
    assert 'certified audit' in data['real_only_note'].lower()


def test_security_copilot_workspace_local_fallback():
    response = client.get('/security-copilot/workspace', params={'user_id': 'local-demo-user'})
    assert response.status_code == 200
    data = response.json()
    assert data['ok'] is True
    assert data['mode']['mode'] in {'local_fallback', 'provider_ready'}
    assert isinstance(data['next_steps'], list)
    assert isinstance(data['safe_commands'], list)
    assert data['safe_commands']
    assert 'not an ai auditor' in data['real_only_note'].lower() or 'not a certified audit' in data['real_only_note'].lower()


def test_security_copilot_ask_returns_safe_guidance():
    response = client.post('/security-copilot/ask', json={'user_id': 'local-demo-user', 'question': 'What should I fix next?', 'include_commands': True})
    assert response.status_code == 200
    data = response.json()
    assert data['ok'] is True
    assert 'Recommended next steps' in data['answer']
    assert 'exploit automation' in data['blocked']
    assert isinstance(data['safe_commands'], list)
