from app.services.contract_benchmark import run_contract_benchmark
from app.services.scan_contract import available_contract_rules, scan_solidity


def _rule_ids(response):
    return {f.rule_id for f in response.findings if f.rule_id}


def test_phase_b_oracle_staleness_rule_triggers():
    code = """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
interface AggregatorV3Interface { function latestRoundData() external view returns (uint80,int256,uint256,uint256,uint80); }
contract OracleRisk {
    AggregatorV3Interface public priceFeed;
    function value() external view returns (int256) {
        (, int256 answer,,,) = priceFeed.latestRoundData();
        return answer;
    }
}
"""
    response = scan_solidity(code, "OracleRisk")
    assert "WG-SOL-ORACLE-001" in _rule_ids(response)
    meta = response.scan_metadata.get("phase_b_rule_coverage", {})
    assert meta.get("phase") == "professional_scanner_phase_b"


def test_phase_b_signature_replay_rules_trigger():
    code = """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
contract SignatureRisk {
    function claim(bytes32 digest, uint8 v, bytes32 r, bytes32 s) external {
        address signer = ecrecover(digest, v, r, s);
        require(signer != address(0), "bad sig");
    }
}
"""
    response = scan_solidity(code, "SignatureRisk")
    ids = _rule_ids(response)
    assert "WG-SOL-SIG-003" in ids
    assert "WG-SOL-SIG-004" in ids
    assert "WG-SOL-SIG-005" in ids


def test_phase_b_dex_slippage_rule_triggers():
    code = """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
interface Router { function swapExactTokensForTokens(uint,uint,address[] calldata,address,uint) external returns (uint[] memory); }
contract SwapRisk {
    Router public router;
    function swap(address[] calldata path) external {
        router.swapExactTokensForTokens(1 ether, 0, path, msg.sender, block.timestamp);
    }
}
"""
    response = scan_solidity(code, "SwapRisk")
    assert "WG-SOL-MEV-001" in _rule_ids(response)


def test_phase_b_benchmark_runs_without_network():
    result = run_contract_benchmark()
    assert result["benchmark_id"] == "web3guard_contract_phase_b_synthetic_v1"
    assert result["case_count"] >= 5
    assert result["synthetic_recall"] >= 0.75
    assert result["missed_expected_rule_signals"] == 0


def test_phase_b_rules_are_listed_in_catalog():
    ids = {rule["id"] for rule in available_contract_rules()}
    assert "WG-SOL-ORACLE-001" in ids
    assert "WG-SOL-MEV-001" in ids
    assert "WG-SOL-SIG-003" in ids
    assert "WG-SOL-VAULT-001" in ids
