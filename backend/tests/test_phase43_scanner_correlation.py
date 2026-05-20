from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_scanner_correlation_status_blocks_destructive_automation():
    res = client.get('/scanner-correlation/status')
    assert res.status_code == 200
    data = res.json()
    assert data['ok'] is True
    assert data['version'].startswith('web3guard-scanner-correlation')
    assert 'exploit execution' in data['not_supported']
    assert 'not a certified audit' in data['required_disclaimer']


def test_playbook_has_p0_launch_blocker_and_attack_templates():
    res = client.get('/scanner-correlation/playbook')
    assert res.status_code == 200
    data = res.json()
    assert any(item['id'] == 'P0-LAUNCH-BLOCKER' for item in data['playbooks'])
    assert any(item['id'] == 'AP-004' for item in data['attack_path_templates'])
    assert 'does not perform exploitation' in data['safe_wording']


def test_prioritize_escalates_known_exploited_public_dependency():
    payload = {
        'project_name': 'Public API',
        'asset_context': {'internet_exposed': True, 'holds_funds': False},
        'assessed_modules': {'osv_nvd_cisa': True},
        'findings': [
            {
                'title': 'CVE in backend dependency from OSV and CISA KEV',
                'description': 'Known exploited CVE affects public API dependency',
                'severity': 'high',
                'source': 'OSV',
                'module': 'dependency',
                'cve_ids': ['CVE-2024-0001'],
                'known_exploited': True,
                'status': 'Assessed',
            }
        ],
        'real_only_acknowledged': True,
    }
    res = client.post('/scanner-correlation/prioritize', json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data['ok'] is True
    assert data['priority_summary']['p0'] == 1
    finding = data['correlated_findings'][0]
    assert finding['priority'] == 'P0'
    assert finding['risk_flags']['known_exploited'] is True
    assert finding['risk_flags']['internet_exposed'] is True
    assert 'not a certified audit' in data['required_disclaimer']


def test_prioritize_webhook_payment_gap_matches_attack_path():
    res = client.post('/scanner-correlation/prioritize', json={
        'project_name': 'Paid report flow',
        'asset_context': {'internet_exposed': True, 'holds_funds': True},
        'findings': [{
            'title': 'Razorpay webhook signature missing',
            'description': 'Payment webhook lacks signature verification and idempotency check',
            'severity': 'high',
            'source': 'Semgrep',
            'module': 'payment_backend',
            'status': 'Assessed',
        }],
        'real_only_acknowledged': True,
    })
    assert res.status_code == 200
    data = res.json()
    assert data['top_priority'] == 'P0'
    assert any(path['id'] == 'AP-002' for path in data['attack_paths'])
    assert data['recommended_next_action'].startswith('Block public launch')


def test_attack_path_builder_is_hypothetical_not_exploit():
    res = client.post('/scanner-correlation/attack-path', json={
        'project_name': 'Vault',
        'asset_context': {'internet_exposed': True, 'holds_funds': True},
        'findings': [{
            'title': 'Reentrancy in withdraw vault external call',
            'description': 'withdraw performs external call before state update',
            'severity': 'critical',
            'source': 'Slither',
            'module': 'smart_contract',
            'status': 'Assessed',
        }]
    })
    assert res.status_code == 200
    data = res.json()
    assert data['ok'] is True
    assert data['chainable_findings_count'] == 1
    assert 'does not exploit' in data['safe_limitation']


def test_empty_prioritization_does_not_claim_secure():
    res = client.post('/scanner-correlation/prioritize', json={'project_name': 'Blank', 'findings': [], 'assessed_modules': {}, 'real_only_acknowledged': True})
    assert res.status_code == 200
    data = res.json()
    assert data['correlated_findings_count'] == 0
    assert data['top_priority'] == 'Not assessed'
    assert any(gap['module'] == 'findings_evidence' for gap in data['coverage_gaps'])
    assert 'Do not claim security' in data['recommended_next_action']


def test_claim_checker_blocks_all_bug_and_hacking_claims():
    res = client.post('/scanner-correlation/claim-check', json={'text': 'Web3Guard finds all bugs, is 100% secure, and can brute force login', 'real_only_acknowledged': True})
    assert res.status_code == 200
    data = res.json()
    assert data['ok'] is False
    assert 'finds all bugs' in data['violations']
    assert '100% secure' in data['violations']
    assert 'brute force' in data['violations']
    assert 'does not guarantee' in data['allowed_rewrite']
