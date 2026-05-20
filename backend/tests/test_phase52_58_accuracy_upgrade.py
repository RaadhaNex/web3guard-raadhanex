import pytest

from app.services.accuracy_upgrade import (
    build_business_logic_review,
    build_reviewed_report_confirmation,
    run_authorized_api_evidence_runner,
    run_defi_simulation_framework,
    run_dependency_osv_engine,
    run_static_worker_bridge,
    run_wallet_ux_evidence_engine,
)


@pytest.mark.asyncio
async def test_phase52_dependency_osv_does_not_fake_when_no_dependencies():
    result = await run_dependency_osv_engine()
    assert result["phase"] == "52"
    assert result["state"] == "Not Assessed"
    assert result["osv"]["vulnerabilities"] == []


def test_phase53_static_worker_reports_not_assessed_without_source():
    result = run_static_worker_bridge(None)
    assert result["phase"] == "53"
    assert result["state"] == "Not Assessed"


def test_phase54_authorized_api_evidence_flags_bola_proof():
    result = run_authorized_api_evidence_runner(observations=[{
        "endpoint": "/api/orders/other-user-order",
        "role": "userA",
        "status_code": 200,
        "expected_access": "userB only",
        "response_hash": "sha256-real-evidence",
        "cross_account_access_proved": True,
    }])
    assert result["phase"] == "54"
    assert result["state"] == "Assessed"
    assert any("BOLA" in item["title"] for item in result["findings"])


def test_phase55_wallet_engine_flags_seed_phrase_and_unlimited_approval():
    result = run_wallet_ux_evidence_engine(
        wallet_evidence={"copy": "Enter seed phrase to continue", "expected_chain_id": "1"},
        transaction_samples=[{"chain_id": "137", "approval": "unlimited"}],
    )
    titles = [item["title"] for item in result["findings"]]
    assert "Wallet Flow Mentions Private Key / Seed Phrase Collection" in titles
    assert "Unlimited Token Approval Evidence" in titles
    assert "Wallet Chain Mismatch Evidence" in titles


def test_phase56_business_logic_creates_manual_test_cases():
    result = build_business_logic_review({"critical_actions": ["unlock paid report"], "asset_flows": ["payment to export"]})
    assert result["phase"] == "56"
    assert result["test_cases"]
    assert result["state"] == "Manual Review Required"


def test_phase57_defi_simulation_uses_supplied_failed_invariant_only():
    result = run_defi_simulation_framework(simulation_result={"invariants": [{"name": "assets conserved", "passed": False, "evidence": "local fork trace"}]})
    assert result["phase"] == "57"
    assert result["confirmed_simulation_findings"]


def test_phase58_reviewed_confirmation_requires_gates():
    not_ready = build_reviewed_report_confirmation({"reviewer": "A", "triaged_findings_count": 3, "unresolved_critical_high_count": 1, "payment_verified": True})
    ready = build_reviewed_report_confirmation({"reviewer": "A", "triaged_findings_count": 3, "unresolved_critical_high_count": 0, "payment_verified": True})
    assert not_ready["state"] == "Not Ready"
    assert ready["state"] == "Reviewed Report Ready"
    assert "certified audit" in ready["blocked_wording"]
