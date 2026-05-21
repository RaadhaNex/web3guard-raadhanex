from fastapi.testclient import TestClient

from main import app
from app.services import professional_final_stabilization_l as phase_l

client = TestClient(app)


def test_phase_l_status_endpoint_is_wired():
    response = client.get('/professional-final-stabilization/status')
    assert response.status_code == 200
    data = response.json()
    assert data['ok'] is True
    assert data['phase'] == 'Professional Scanner Phase L'
    assert data['real_only_controls']['private_key_collection'] is False
    assert data['real_only_controls']['certified_audit_claim'] is False


def test_phase_l_module_matrix_has_phase_a_to_k_bridge():
    data = phase_l.phase_module_matrix()
    assert data['ok'] is True
    phases = {item['phase'] for item in data['modules']}
    assert {'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K'}.issubset(phases)
    assert '/professional-final-stabilization' in data['endpoint_groups_expected']


def test_phase_l_claim_gate_blocks_unsafe_claims():
    safe = client.get('/professional-final-stabilization/claim-gate', params={'candidate_claim': 'Evidence-first pre-audit readiness proof'})
    unsafe = client.get('/professional-final-stabilization/claim-gate', params={'candidate_claim': '100% secure certified audit and CertiK replacement'})
    assert safe.status_code == 200
    assert safe.json()['ok'] is True
    assert unsafe.status_code == 200
    unsafe_data = unsafe.json()
    assert unsafe_data['ok'] is False
    assert unsafe_data['public_certified_audit_claim_allowed'] is False
    assert unsafe_data['direct_competition_replacement_claim_allowed'] is False
    assert '100% secure' in unsafe_data['blocked_hits']


def test_phase_l_remaining_work_is_explicit_and_honest():
    response = client.get('/professional-final-stabilization/remaining')
    assert response.status_code == 200
    data = response.json()
    ids = {item['id'] for item in data['remaining']}
    assert 'external_audited_dataset' in ids
    assert 'reviewer_identity_and_qa' in ids
    assert 'public_proof_ui' in ids
    assert 'certified-audit competitor status requires real reviewers' in data['honest_market_status']


def test_phase_l_production_gate_reports_safe_claim_blocker():
    response = client.get('/professional-final-stabilization/production-gate', params={'candidate_claim': 'Hacken replacement certified audit'})
    assert response.status_code == 200
    data = response.json()
    assert data['ok'] is False
    assert 'unsafe_public_claim' in data['blockers']
    assert data['claim_ok'] is False
