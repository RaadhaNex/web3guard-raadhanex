from fastapi.testclient import TestClient

from main import app
from app.services import static_analysis_tools as svc

client = TestClient(app)


def test_phase13_static_analysis_status_real_only():
    response = client.get('/scan/static-analysis/status')
    assert response.status_code == 200
    data = response.json()
    assert data['engine_version'] == 'web3guard-static-analysis-engine-v13.0'
    assert data['safety_controls']['collects_private_keys'] is False
    assert 'slither' in data['tools']
    assert 'No fake Slither/Aderyn/Semgrep output' in data['not_claimed']


def test_phase13_endpoint_requires_real_only_acknowledgement():
    response = client.post('/scan/static-analysis', json={
        'solidity_code': 'pragma solidity ^0.8.20; contract A { function x() external {} }',
        'project_name': 'No real only',
        'file_name': 'A.sol',
        'tools': ['slither'],
        'authorization_confirmed': True,
        'real_only_acknowledged': False,
    })
    assert response.status_code == 400
    assert 'Real-only' in response.json()['detail']


def test_phase13_disabled_tools_generate_status_only_no_fake_vulns(monkeypatch):
    monkeypatch.setattr(svc.settings, 'static_analysis_enabled', False)
    result = svc.run_static_analysis(
        'pragma solidity ^0.8.20; contract A { function x() external {} }',
        project_name='Disabled Tool Status',
        file_name='A.sol',
        requested_tools=['slither', 'semgrep'],
    )
    assert result.engine_version == 'web3guard-static-analysis-engine-v13.0'
    assert result.module_score.module == 'static_analysis'
    assert result.module_score.score >= 90
    assert all(f.category == 'tool_status' for f in result.findings)
    assert any('STATIC_ANALYSIS_ENABLED is false' in f.description for f in result.findings)


def test_phase13_semgrep_parser_maps_real_json_output():
    raw = '{"results":[{"check_id":"web3guard-solidity-tx-origin-auth","start":{"line":7},"extra":{"message":"Avoid tx.origin","severity":"ERROR","lines":"tx.origin == owner"}}]}'
    findings = svc._parse_semgrep_json(raw)
    assert len(findings) == 1
    assert findings[0].severity == 'high'
    assert findings[0].affected_line == 7
    assert 'tx.origin' in findings[0].affected_code


def test_phase13_static_analysis_endpoint_disabled_mode():
    response = client.post('/scan/static-analysis', json={
        'solidity_code': 'pragma solidity ^0.8.20; contract A { function x() external {} }',
        'project_name': 'Endpoint Disabled Mode',
        'file_name': 'A.sol',
        'tools': ['slither'],
        'authorization_confirmed': True,
        'real_only_acknowledged': True,
    })
    assert response.status_code == 200
    data = response.json()
    assert data['module_score']['module'] == 'static_analysis'
    assert data['engine_version'] == 'web3guard-static-analysis-engine-v13.0'
    assert data['scan_metadata']['real_only_note'].startswith('Only parsed output')
