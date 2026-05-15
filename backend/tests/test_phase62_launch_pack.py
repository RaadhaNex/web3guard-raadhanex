from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_launch_pack_endpoint_exposes_real_only_status():
    response = client.get('/launch/pack')
    assert response.status_code == 200
    data = response.json()
    assert data['ok'] is True
    assert 'Phase 6.2' in data['phase']
    statuses = {item['area']: item['status'] for item in data['real_only_status']}
    assert statuses['Unified URL Scanner'] == 'live'
    assert statuses['UPI Payment'] == 'manual'
    assert statuses['Certified Audit'] == 'not-offered'
    assert any('Certified audit' in item for item in data['forbidden_public_wording'])


def test_local_qa_includes_launch_pack_route_and_endpoint():
    routes = client.get('/qa/frontend-routes').json()['routes']
    assert '/launch-pack' in routes
    endpoints = client.get('/qa/backend-endpoints').json()['endpoints']
    assert any(endpoint['path'] == '/launch/pack' for endpoint in endpoints)
