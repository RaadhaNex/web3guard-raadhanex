from app.services.professional_external_validation_i import (
    append_reviewer_confirmation,
    direct_competition_readiness_gate,
    external_validation_status,
    reviewer_consensus,
    run_sanitized_external_suite,
    validate_external_case,
)


def test_phase_i_status_and_sanitized_suite_runs():
    status = external_validation_status()
    assert status["ok"] is True
    assert status["phase"] == "Professional Scanner Phase I"
    assert status["scanner_claim_policy"]["certified_audit_claim_allowed"] is False
    result = run_sanitized_external_suite()
    assert result["ok"] is True
    assert result["cases_total"] >= 4
    assert "recall" in result
    assert result["direct_competition_public_claim_allowed"] is False


def test_phase_i_validates_external_case_without_fake_claim():
    result = validate_external_case(
        {
            "case_id": "UNIT-REENTRANCY",
            "case_type": "vulnerable",
            "family": "reentrancy",
            "solidity_code": """
pragma solidity ^0.8.20;
contract Vault {
    mapping(address => uint256) public balance;
    function withdraw(uint256 amount) external {
        require(balance[msg.sender] >= amount);
        (bool ok,) = msg.sender.call{value: amount}("");
        require(ok);
        balance[msg.sender] -= amount;
    }
}
""",
            "expected_rule_ids": [],
            "authorization_confirmed": True,
            "real_only_acknowledged": True,
        }
    )
    assert result["ok"] is True
    assert result["case_id"] == "UNIT-REENTRANCY"
    assert result["findings_count"] >= 1
    assert result["public_claim_allowed"] is False


def test_phase_i_reviewer_confirmation_and_consensus():
    a = append_reviewer_confirmation(
        {
            "case_id": "UNIT-CONSENSUS",
            "rule_id": "WG-SOL-REENTRANCY-001",
            "reviewer_id": "rev-a",
            "decision": "confirmed",
            "confidence": "high",
            "real_only_acknowledged": True,
        }
    )
    b = append_reviewer_confirmation(
        {
            "case_id": "UNIT-CONSENSUS",
            "rule_id": "WG-SOL-REENTRANCY-001",
            "reviewer_id": "rev-b",
            "decision": "confirmed",
            "confidence": "high",
            "real_only_acknowledged": True,
        }
    )
    assert a["id"].startswith("EXTREV-")
    assert b["id"].startswith("EXTREV-")
    consensus = reviewer_consensus(case_id="UNIT-CONSENSUS")
    assert consensus["ok"] is True
    assert consensus["summary"].get("externally_confirmed", 0) >= 1
    assert consensus["public_claim_allowed"] is False


def test_phase_i_direct_competition_gate_is_controlled():
    gate = direct_competition_readiness_gate()
    assert gate["ok"] is True
    assert gate["public_claim_allowed"] is False
    assert "gates" in gate
    assert gate["next_phase"].startswith("Phase J")
