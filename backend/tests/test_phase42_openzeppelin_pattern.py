from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_openzeppelin_pattern_status_is_not_official_certification():
    res = client.get('/openzeppelin-pattern/status')
    assert res.status_code == 200
    data = res.json()
    assert data['ok'] is True
    assert data['version'].startswith('web3guard-openzeppelin-pattern')
    assert 'official OpenZeppelin certification' in data['not_supported']
    assert 'not a certified audit' in data['required_disclaimer']


def test_openzeppelin_rule_catalog_has_core_security_patterns():
    res = client.get('/openzeppelin-pattern/rules')
    assert res.status_code == 200
    data = res.json()
    rule_ids = {rule['id'] for rule in data['rules']}
    assert 'OZ-ACL-001' in rule_ids
    assert 'OZ-REENT-001' in rule_ids
    assert 'OZ-UPG-001' in rule_ids
    assert 'OpenZeppelin audit' in data['safe_wording']


def test_analyze_detects_custom_token_and_missing_guards():
    source = '''
    pragma solidity ^0.8.20;
    contract MyToken {
      mapping(address => uint256) public balanceOf;
      function mint(address to, uint256 amount) external { balanceOf[to] += amount; }
      function withdraw(uint256 amount) external { (bool ok,) = msg.sender.call{value: amount}(""); require(ok); }
      function approve(address spender, uint256 amount) external returns (bool) { return true; }
    }
    '''
    res = client.post('/openzeppelin-pattern/analyze', json={
        'project_name': 'Custom token',
        'contract_source': source,
        'real_only_acknowledged': True,
    })
    assert res.status_code == 200
    data = res.json()
    assert data['ok'] is True
    assert data['pattern_summary']['uses_openzeppelin_contracts'] is False
    ids = {finding['rule_id'] for finding in data['findings']}
    assert 'OZ-STD-001' in ids
    assert 'OZ-ACL-001' in ids
    assert 'OZ-REENT-001' in ids
    assert data['severity_breakdown']['critical'] >= 1
    assert 'not OpenZeppelin certification' in data['safe_report_wording']


def test_analyze_detects_openzeppelin_modules_and_ownable2step_advisory():
    source = '''
    pragma solidity ^0.8.20;
    import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
    import "@openzeppelin/contracts/access/Ownable.sol";
    import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
    import "@openzeppelin/contracts/utils/Pausable.sol";
    contract SafeToken is ERC20, Ownable, ReentrancyGuard, Pausable {
      function mint(address to, uint256 amount) external onlyOwner { _mint(to, amount); }
    }
    '''
    res = client.post('/openzeppelin-pattern/analyze', json={'project_name': 'OZ token', 'contract_source': source})
    assert res.status_code == 200
    data = res.json()
    assert data['pattern_summary']['uses_openzeppelin_contracts'] is True
    assert 'ERC20' in data['openzeppelin_modules_detected']
    assert data['pattern_summary']['uses_reentrancy_guard_pattern'] is True
    assert any('Ownable2Step' in finding['evidence'] for finding in data['findings'])


def test_empty_source_does_not_fake_assessment():
    res = client.post('/openzeppelin-pattern/analyze', json={'project_name': 'Blank', 'contract_source': ''})
    assert res.status_code == 200
    data = res.json()
    assert data['findings_count'] == 1
    assert data['findings'][0]['status'] == 'Not assessed yet'
    assert 'No Solidity/source evidence supplied' == data['findings'][0]['title']


def test_claim_checker_blocks_openzeppelin_certification_wording():
    res = client.post('/openzeppelin-pattern/claim-check', json={'text': 'Web3Guard is an official OpenZeppelin scanner and OpenZeppelin certified audit', 'real_only_acknowledged': True})
    assert res.status_code == 200
    data = res.json()
    assert data['ok'] is False
    assert 'official openzeppelin scanner' in data['violations']
    assert 'openzeppelin certified' in data['violations']
    assert 'not an official OpenZeppelin scanner' in data['allowed_rewrite']
