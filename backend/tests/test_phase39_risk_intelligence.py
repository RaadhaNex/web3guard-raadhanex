from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_risk_intelligence_status_has_cwe_nvd_reference():
    res = client.get('/risk-intelligence/status')
    assert res.status_code == 200
    data = res.json()
    assert data['ok'] is True
    assert data['reference_scope']['cwe_total_weakness_types'] == 944
    assert data['reference_scope']['nvd_documented_cve_records_snapshot'] >= 351000
    assert 'Not a certified audit' in data['required_disclaimer']


def test_taxonomy_map_does_not_claim_all_bug_detection():
    res = client.get('/risk-intelligence/taxonomy')
    assert res.status_code == 200
    data = res.json()
    assert data['ok'] is True
    assert len(data['families']) >= 5
    assert any('business logic' in item for item in data['not_fully_automatable'])
    assert 'not all-bug guaranteed' in data['reference_scope']['note']


def test_analyze_enhances_reentrancy_and_payment_findings():
    payload = {
        'project_name': 'Pilot vault',
        'real_only_acknowledged': True,
        'assessed_modules': {'slither': True, 'semgrep': True, 'osv': True, 'cisa_kev': False},
        'findings': [
            {
                'title': 'Reentrancy risk in withdraw',
                'description': 'External call before state update in Vault.withdraw',
                'severity': 'critical',
                'module': 'smart_contract',
                'source': 'Slither',
                'rule_id': 'reentrancy-eth',
                'file': 'contracts/Vault.sol',
                'line': 88,
            },
            {
                'title': 'Razorpay webhook signature missing',
                'description': 'Payment webhook accepts success without signature verification',
                'severity': 'high',
                'module': 'payment_backend',
                'source': 'Semgrep',
            },
        ],
    }
    res = client.post('/risk-intelligence/analyze', json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data['enhanced_findings_count'] == 2
    assert data['priority_summary']['p0'] == 1
    assert data['findings'][0]['priority'] == 'P0'
    assert 'future_risk' in data['findings'][0]
    assert data['findings'][1]['fix_plan']['summary']
    assert any(gap['module'] == 'cisa_kev' for gap in data['coverage_gaps'])


def test_analyze_empty_findings_does_not_fake_security():
    res = client.post('/risk-intelligence/analyze', json={'project_name': 'Empty scan', 'findings': [], 'assessed_modules': {}, 'real_only_acknowledged': True})
    assert res.status_code == 200
    data = res.json()
    assert data['enhanced_findings_count'] == 0
    assert 'Do not claim the project is secure' in data['recommended_next_action']
    assert len(data['coverage_gaps']) >= 5


def test_claim_checker_blocks_all_bug_guarantee():
    res = client.post('/risk-intelligence/claim-check', json={'text': 'Our scanner finds all bugs and makes you 100% secure', 'real_only_acknowledged': True})
    assert res.status_code == 200
    data = res.json()
    assert data['ok'] is False
    assert any('100% secure' == violation for violation in data['violations'])
    assert 'does not guarantee' in data['allowed_rewrite'].lower()


def test_finding_impact_explains_dependency_risk():
    res = client.post('/risk-intelligence/finding-impact', json={'title': 'OSV CVE dependency advisory', 'description': 'lodash vulnerable package', 'severity': 'high', 'source': 'OSV', 'cve_ids': ['CVE-2020-8203']})
    assert res.status_code == 200
    data = res.json()
    assert data['ok'] is True
    assert data['finding']['priority'] == 'P0'
    assert len(data['report_sections']) >= 5
