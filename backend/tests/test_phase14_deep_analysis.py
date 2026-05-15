from fastapi.testclient import TestClient

from main import app
from app.services import deep_analysis_tools as svc

client = TestClient(app)


def test_phase14_deep_analysis_status_real_only():
    response = client.get('/scan/deep-analysis/status')
    assert response.status_code == 200
    data = response.json()
    assert data['engine_version'] == 'web3guard-deep-analysis-engine-v14.0'
    assert data['safety_controls']['collects_private_keys'] is False
    assert data['safety_controls']['touches_mainnet'] is False
    assert 'mythril' in data['tools']
    assert 'No fake Mythril/Manticore/Echidna output' in data['not_claimed']


def test_phase14_endpoint_requires_real_only_acknowledgement():
    response = client.post('/scan/deep-analysis', json={
        'solidity_code': 'pragma solidity ^0.8.20; contract A { function x() external {} }',
        'project_name': 'No real only',
        'file_name': 'A.sol',
        'tools': ['mythril'],
        'authorization_confirmed': True,
        'real_only_acknowledged': False,
    })
    assert response.status_code == 400
    assert 'Real-only' in response.json()['detail']


def test_phase14_standard_depth_requires_ownership():
    response = client.post('/scan/deep-analysis', json={
        'solidity_code': 'pragma solidity ^0.8.20; contract A { function x() external {} }',
        'project_name': 'Ownership required',
        'file_name': 'A.sol',
        'tools': ['mythril'],
        'scan_depth': 'standard',
        'authorization_confirmed': True,
        'real_only_acknowledged': True,
        'ownership_verified': False,
    })
    assert response.status_code == 400
    assert 'ownership verification' in response.json()['detail']


def test_phase14_disabled_tools_generate_status_only_no_fake_vulns(monkeypatch):
    monkeypatch.setattr(svc.settings, 'deep_analysis_enabled', False)
    result = svc.run_deep_analysis(
        'pragma solidity ^0.8.20; contract A { function x() external {} }',
        project_name='Disabled Deep Tool Status',
        file_name='A.sol',
        requested_tools=['mythril', 'echidna'],
    )
    assert result.engine_version == 'web3guard-deep-analysis-engine-v14.0'
    assert result.module_score.module == 'deep_analysis'
    assert result.module_score.score >= 90
    assert all(f.category == 'tool_status' for f in result.findings)
    assert any('DEEP_ANALYSIS_ENABLED is false' in f.description for f in result.findings)


def test_phase14_mythril_parser_maps_real_json_output():
    raw = '{"issues":[{"title":"External Call To User-Supplied Address","severity":"High","lineno":12,"description":"Potential reentrancy","swc-id":"107","code":"msg.sender.call()"}]}'
    findings = svc._parse_mythril_json(raw)
    assert len(findings) == 1
    assert findings[0].severity == 'high'
    assert findings[0].affected_line == 12
    assert 'reentrancy' in findings[0].description.lower()


def test_phase14_echidna_parser_maps_failed_property():
    raw = '{"tests":[{"name":"echidna_balance_never_decreases","status":"falsified","error":"counterexample found"}]}'
    findings = svc._parse_echidna_json(raw)
    assert len(findings) == 1
    assert findings[0].severity == 'high'
    assert 'Property Failed' in findings[0].title


def test_phase14_deep_analysis_endpoint_disabled_mode():
    response = client.post('/scan/deep-analysis', json={
        'solidity_code': 'pragma solidity ^0.8.20; contract A { function x() external {} }',
        'project_name': 'Endpoint Disabled Mode',
        'file_name': 'A.sol',
        'tools': ['mythril'],
        'authorization_confirmed': True,
        'real_only_acknowledged': True,
    })
    assert response.status_code == 200
    data = response.json()
    assert data['module_score']['module'] == 'deep_analysis'
    assert data['engine_version'] == 'web3guard-deep-analysis-engine-v14.0'
    assert data['scan_metadata']['real_only_note'].startswith('Only parsed output')
