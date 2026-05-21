import pytest
from fastapi.testclient import TestClient

import app.services.scan_contract_address as svc
from main import app

client = TestClient(app)


def test_phase12_status_is_real_only():
    response = client.get('/scan/contract-address/status')
    assert response.status_code == 200
    data = response.json()
    assert data['ok'] is True
    assert 'No private key collection' in data['not_enabled_or_not_claimed']
    assert any(item['chain_id'] == '1' for item in data['supported_chains'])


def test_phase12_validates_evm_address_and_chain():
    assert svc.validate_evm_address('0x' + 'a' * 40) == '0x' + 'a' * 40
    assert svc.normalize_chain_id('polygon') == '137'
    assert svc.normalize_chain_id('56') == '56'
    with pytest.raises(ValueError):
        svc.validate_evm_address('0x123')
    with pytest.raises(ValueError):
        svc.normalize_chain_id('not-a-chain')


@pytest.mark.asyncio
async def test_phase12_contract_address_scan_with_mocked_verified_source(monkeypatch):
    monkeypatch.setattr(svc.settings, 'etherscan_api_key', 'test-key')

    async def fake_fetch_contract_source(address, chain_id):
        return {
            'SourceCode': '''// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
contract VerifiedRisk {
    address public owner;
    constructor(){ owner = msg.sender; }
    function withdraw(address payable to) external {
        require(tx.origin == owner, "no");
        to.call{value: address(this).balance}("");
    }
    function upgradeTo(address newImplementation) external {}
}
''',
            'ABI': '[{"type":"function","name":"owner"},{"type":"function","name":"upgradeTo"}]',
            'ContractName': 'VerifiedRisk',
            'CompilerVersion': 'v0.8.20+commit.a1b79de6',
            'OptimizationUsed': '0',
            'Runs': '200',
            'LicenseType': 'MIT',
            'Proxy': '0',
            'Implementation': '',
            'ConstructorArguments': '',
            'EVMVersion': 'Default',
        }

    monkeypatch.setattr(svc, 'fetch_contract_source', fake_fetch_contract_source)
    result = await svc.scan_contract_address('0x' + 'b' * 40, chain='ethereum', project_name='Verified Risk')
    assert result.engine_version == 'web3guard-contract-address-engine-v13.0'
    assert result.scan_metadata['source_verified'] is True
    assert result.scan_metadata['chain_id'] == '1'
    assert result.module_score.module == 'contract'
    titles = {finding.title for finding in result.findings}
    assert any('tx.origin' in title for title in titles)
    assert 'Admin-Like ABI Functions Detected' in titles
    assert result.scan_metadata['safety_controls']['private_key_collection'] is False


@pytest.mark.asyncio
async def test_phase12_unverified_source_gets_transparency_finding(monkeypatch):
    monkeypatch.setattr(svc.settings, 'etherscan_api_key', 'test-key')

    async def fake_fetch_contract_source(address, chain_id):
        return {'SourceCode': '', 'ContractName': '', 'CompilerVersion': '', 'Proxy': '0', 'Implementation': ''}

    async def fake_fetch_contract_abi(address, chain_id):
        return None

    monkeypatch.setattr(svc, 'fetch_contract_source', fake_fetch_contract_source)
    monkeypatch.setattr(svc, 'fetch_contract_abi', fake_fetch_contract_abi)
    result = await svc.scan_contract_address('0x' + 'c' * 40, chain='polygon', project_name='Unverified')
    assert result.scan_metadata['source_verified'] is False
    assert result.findings[0].title == 'Contract Source Not Verified On Explorer'
    assert result.findings[0].severity == 'high'


def test_phase12_endpoint_requires_real_only_acknowledgement():
    response = client.post('/scan/contract-address', json={
        'address': '0x' + 'd' * 40,
        'chain': 'ethereum',
        'project_name': 'No Real Only',
        'authorization_confirmed': True,
        'real_only_acknowledged': False,
    })
    assert response.status_code == 400
    assert 'Real-only' in response.json()['detail']
