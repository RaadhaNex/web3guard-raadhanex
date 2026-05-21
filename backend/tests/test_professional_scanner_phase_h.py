from app.services.professional_benchmark_g import run_real_world_benchmark
from app.services.professional_rule_tuning_h import phase_h_status, run_phase_h_tuning_validation
from app.services.scan_contract import scan_solidity


def test_phase_h_benchmark_gate_has_zero_misses_and_zero_clean_false_positives():
    result = run_real_world_benchmark()
    assert result["missed_expected_rule_signals"] == 0
    assert result["false_positive_case_count"] == 0
    assert result["severity_fail_case_count"] == 0
    assert result["real_world_style_recall"] == 1.0
    assert result["clean_specificity"] == 1.0
    assert result["quality_gate"]["direct_level_engine_progress"] is True
    assert result["quality_gate"]["direct_competition_public_claim_allowed"] is False


def test_phase_h_validation_endpoint_payload_blocks_public_parity_claim():
    status = phase_h_status()
    assert status["public_claim_allowed"] is False
    assert "WG-SOL-ORACLE-002" in status["tuned_rule_ids"]
    assert "bridge_crosschain" in status["tuned_families"]

    result = run_phase_h_tuning_validation()
    assert result["ok"] is True
    assert result["phase_h_passed"] is True
    assert result["direct_level_engine_progress"] is True
    assert result["public_direct_competition_claim_allowed"] is False
    assert result["remaining_tuned_family_issues"] == {}


def test_phase_h_tuned_rules_detect_prior_weak_families():
    code = """
    // SPDX-License-Identifier: MIT
    pragma solidity ^0.7.6;
    interface AggregatorV3Interface { function latestRoundData() external view returns (uint80,int256,uint256,uint256,uint80); }
    contract TunedWeakFamilies {
        address public messenger;
        function upgradeTo(address impl) external { _authorizeUpgrade(impl); }
        function _authorizeUpgrade(address) internal {}
        function initialize(address owner) public {}
        function price(AggregatorV3Interface feed) external view returns(uint256) { (, int256 p,,,) = feed.latestRoundData(); return uint256(p); }
        function swap(address router, bytes calldata data) external { (bool ok,) = router.call(data); require(ok); }
        function bridgeExecute(address target, bytes calldata payload) external { require(msg.sender == messenger); (bool ok,) = target.call(payload); require(ok); }
        function multicall(bytes[] calldata calls) external payable { for (uint256 i; i < calls.length; i++) { address(this).delegatecall(calls[i]); } }
        function add(uint256 x) external returns(uint256) { return x + 1; }
    }
    """
    response = scan_solidity(code, project_name="TunedWeakFamilies")
    rule_ids = {f.rule_id for f in response.findings}
    assert "WG-SOL-UPGRADE-003" in rule_ids
    assert "WG-SOL-UPGRADE-004" in rule_ids
    assert "WG-SOL-ORACLE-002" in rule_ids
    assert "WG-SOL-XCHAIN-001" in rule_ids
    assert "WG-SOL-MULTI-001" in rule_ids
    assert "WG-SOL-OVFL-001" in rule_ids
