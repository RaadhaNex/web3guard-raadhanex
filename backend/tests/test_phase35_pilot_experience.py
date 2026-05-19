from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_phase35_status_keeps_seven_visible_paths_and_no_fake_claims():
    response = client.get('/pilot-experience/status')
    assert response.status_code == 200
    data = response.json()
    assert data['ok'] is True
    assert data['phase'] == 'phase_35_ui_cleanup_pilot_experience_polish'
    assert data['visible_path_count'] == 7
    assert data['no_fake_claims'] is True
    assert '100% secure' in data['blocked_copy_patterns']


def test_phase35_journey_prioritizes_scan_to_report_flow():
    response = client.get('/pilot-experience/journey')
    assert response.status_code == 200
    data = response.json()
    labels = [item['label'] for item in data['journey']]
    assert labels[:4] == ['Scan', 'Results', 'Fix Plan', 'Report']
    assert '/worker-runs' in data['do_not_add_to_primary_nav']
    assert 'scan -> results -> fix plan' in data['first_user_rule']


def test_phase35_state_copy_turns_missing_tool_into_setup_gap():
    response = client.get('/pilot-experience/state-copy')
    assert response.status_code == 200
    data = response.json()
    assert data['states']['Tool Not Installed']['headline'] == 'Worker tool is missing.'
    assert data['states']['Needs API Key']['next_action'].startswith('Add the provider key')
    assert 'not a finding' in data['ux_rule']


def test_phase35_feedback_accepts_normal_pilot_note():
    response = client.post('/pilot-experience/feedback', json={
        'page_path': '/results',
        'role': 'founder',
        'friction_area': 'result clarity',
        'message': 'The results were useful, but I need a clearer next step after Not Assessed modules.',
        'can_contact': False,
    })
    assert response.status_code == 200
    data = response.json()
    assert data['accepted'] is True
    assert data['stored_as'] == 'local_jsonl'
    assert data['feedback_id'].startswith('pux_')


def test_phase35_feedback_rejects_secret_like_input():
    response = client.post('/pilot-experience/feedback', json={
        'page_path': '/scanner',
        'role': 'founder',
        'friction_area': 'security',
        'message': 'Here is my private key 0x' + 'a' * 64,
    })
    assert response.status_code == 200
    data = response.json()
    assert data['accepted'] is False
    assert 'private key' in data['reason'].lower()


def test_phase35_claim_check_blocks_unsafe_copy():
    response = client.post('/pilot-experience/claim-check', json={'text': 'Web3Guard certified audit gives 100% secure results'})
    assert response.status_code == 200
    data = response.json()
    assert data['allowed'] is False
    assert '100% secure' in data['blocked_terms']
    assert 'certified audit' in data['blocked_terms']


def test_phase35_conversion_checklist_keeps_payment_truth():
    response = client.get('/pilot-experience/conversion-checklist')
    assert response.status_code == 200
    data = response.json()
    assert data['ok'] is True
    assert any('Payment CTA' in item['item'] for item in data['checklist'])
    assert 'first 10 users' in data['goal']
