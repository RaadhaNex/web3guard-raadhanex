from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_phase36_status_closes_build_phase_and_keeps_truth_rules():
    response = client.get('/mvp-launch/status')
    assert response.status_code == 200
    data = response.json()
    assert data['ok'] is True
    assert data['phase'] == 'phase_36_mvp_launch_pack_first_10_users_sprint'
    assert 'Stop adding new feature phases' in data['build_phase_status']
    assert data['primary_goal'].startswith('Get 10 real founder sessions')
    assert data['no_fake_claims'] is True
    assert 'certified audit' in data['blocked_claim_patterns']


def test_phase36_launch_checklist_requires_apply_test_deploy_users():
    response = client.get('/mvp-launch/launch-checklist')
    assert response.status_code == 200
    data = response.json()
    groups = [item['group'] for item in data['checklist']]
    assert 'Apply and verify code' in groups
    assert 'First 10 users' in groups
    assert any('Razorpay test checkout' in item for item in data['exit_criteria'])


def test_phase36_outreach_kit_is_preaudit_and_authorized_scope_only():
    response = client.get('/mvp-launch/outreach-kit')
    assert response.status_code == 200
    data = response.json()
    joined = ' '.join(template['message'] for template in data['templates'])
    assert 'pre-audit' in joined
    assert 'certified audit' in data['daily_action_plan'][-1]
    assert 'hackathon teams' in data['target_segments']


def test_phase36_sample_report_contains_limitations_and_no_wallet_policy():
    response = client.get('/mvp-launch/sample-report')
    assert response.status_code == 200
    data = response.json()
    sections = data['template']['required_sections']
    assert any('Not Assessed' in section for section in sections)
    assert any('No private key' in section for section in sections)
    assert data['report_price_anchor_inr'] == 999
    assert 'not a certified audit' in data['template']['safe_opening_copy']


def test_phase36_claim_check_blocks_unsafe_launch_copy():
    response = client.post('/mvp-launch/claim-check', json={'text': 'Web3Guard is a certified audit and 100% secure product'})
    assert response.status_code == 200
    data = response.json()
    assert data['allowed'] is False
    assert '100% secure' in data['blocked_terms']
    assert 'certified audit' in data['blocked_terms']


def test_phase36_first_10_tracker_accepts_safe_record():
    response = client.post('/mvp-launch/first-10', json={
        'project_name': 'Pilot dApp Alpha',
        'founder_segment': 'hackathon team',
        'source_channel': 'ETHIndia Discord',
        'stage': 'report requested',
        'paid_intent': 'maybe ₹999',
        'highest_friction': 'Needs clearer Tool Not Installed copy',
        'next_action': 'send pilot report sample',
    })
    assert response.status_code == 200
    data = response.json()
    assert data['accepted'] is True
    assert data['pilot_id'].startswith('mvp_')
    assert data['remaining'] <= 10


def test_phase36_first_10_tracker_rejects_secret_like_record():
    response = client.post('/mvp-launch/first-10', json={
        'project_name': 'Unsafe input',
        'highest_friction': 'Here is my private key 0x' + 'a' * 64,
    })
    assert response.status_code == 200
    data = response.json()
    assert data['accepted'] is False
    assert 'private key' in data['reason'].lower()


def test_phase36_public_beta_checklist_blocks_fake_launch():
    response = client.get('/mvp-launch/public-beta-checklist')
    assert response.status_code == 200
    data = response.json()
    assert any('SAMPLE' in item for item in data['public_beta_assets'])
    assert any('certified audit' in item for item in data['do_not_launch_if'])


def test_phase36_claim_guidance_positions_against_enterprise_audits_safely():
    response = client.get('/mvp-launch/claim-guidance')
    assert response.status_code == 200
    data = response.json()
    assert any('pre-audit launch readiness scanner' in item for item in data['what_to_say'])
    assert any('100% secure' in item for item in data['what_not_to_claim'])
    assert 'not a replacement' in data['positioning']
