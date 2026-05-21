"""Professional scanner benchmark harness for Solidity rule accuracy.

This module is intentionally self-contained and uses small synthetic fixtures so it
can run in CI/Render without network access or external tools. It does not claim
certified-audit accuracy; it measures whether the local rule engine catches known
training signals and avoids severe findings on a simple clean contract.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.services.scan_contract import scan_solidity


@dataclass(frozen=True)
class BenchmarkCase:
    case_id: str
    title: str
    code: str
    expected_rule_ids: set[str]
    forbidden_high_or_critical_rule_ids: set[str] | None = None
    project_name: str | None = None


BENCHMARK_CASES: list[BenchmarkCase] = [
    BenchmarkCase(
        case_id="phase_b_oracle_stale",
        title="Oracle latestRoundData without freshness checks",
        project_name="OracleRisk",
        expected_rule_ids={"WG-SOL-ORACLE-001"},
        code="""
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
""",
    ),
    BenchmarkCase(
        case_id="phase_b_swap_zero_min",
        title="Swap with zero amountOutMin",
        project_name="SwapRisk",
        expected_rule_ids={"WG-SOL-MEV-001"},
        code="""
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
interface Router { function swapExactTokensForTokens(uint,uint,address[] calldata,address,uint) external returns (uint[] memory); }
contract SwapRisk {
    Router public router;
    function swap(address[] calldata path) external {
        router.swapExactTokensForTokens(1 ether, 0, path, msg.sender, block.timestamp);
    }
}
""",
    ),
    BenchmarkCase(
        case_id="phase_b_signature_replay",
        title="Raw ecrecover without nonce/deadline",
        project_name="SignatureRisk",
        expected_rule_ids={"WG-SOL-SIG-003", "WG-SOL-SIG-004", "WG-SOL-SIG-005"},
        code="""
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
contract SignatureRisk {
    function claim(bytes32 digest, uint8 v, bytes32 r, bytes32 s) external {
        address signer = ecrecover(digest, v, r, s);
        require(signer != address(0), "bad sig");
    }
}
""",
    ),
    BenchmarkCase(
        case_id="phase_b_vault_inflation",
        title="ERC4626-style vault without inflation defense",
        project_name="VaultRisk",
        expected_rule_ids={"WG-SOL-VAULT-001"},
        code="""
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
contract VaultRisk {
    function totalAssets() public view returns (uint256) { return address(this).balance; }
    function convertToShares(uint256 assets) public view returns (uint256) { return assets * 1e18 / totalAssets(); }
    function previewDeposit(uint256 assets) external view returns (uint256) { return convertToShares(assets); }
    function deposit() external payable {}
}
""",
    ),
    BenchmarkCase(
        case_id="phase_b_clean_minimal",
        title="Clean minimal ownership contract should avoid severe Phase B rules",
        project_name="CleanMinimal",
        expected_rule_ids=set(),
        forbidden_high_or_critical_rule_ids={
            "WG-SOL-ORACLE-001",
            "WG-SOL-MEV-001",
            "WG-SOL-SIG-003",
            "WG-SOL-VAULT-001",
            "WG-SOL-XCHAIN-001",
        },
        code="""
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
contract CleanMinimal {
    address public owner;
    event OwnerTransferred(address indexed oldOwner, address indexed newOwner);
    modifier onlyOwner() { require(msg.sender == owner, "not owner"); _; }
    constructor() { owner = msg.sender; }
    function transferOwnership(address newOwner) external onlyOwner {
        require(newOwner != address(0), "zero");
        emit OwnerTransferred(owner, newOwner);
        owner = newOwner;
    }
}
""",
    ),
]


def run_contract_benchmark() -> dict[str, Any]:
    cases: list[dict[str, Any]] = []
    total_expected = 0
    total_detected_expected = 0
    total_missed = 0
    false_positive_cases = 0

    for case in BENCHMARK_CASES:
        response = scan_solidity(case.code, project_name=case.project_name)
        detected_rule_ids = {f.rule_id for f in response.findings if f.rule_id}
        severities_by_rule = {f.rule_id: f.severity for f in response.findings if f.rule_id}
        expected_detected = sorted(case.expected_rule_ids.intersection(detected_rule_ids))
        missed = sorted(case.expected_rule_ids.difference(detected_rule_ids))
        forbidden_hit = []
        for rule_id in case.forbidden_high_or_critical_rule_ids or set():
            sev = severities_by_rule.get(rule_id)
            if sev in {"critical", "high"}:
                forbidden_hit.append(rule_id)

        total_expected += len(case.expected_rule_ids)
        total_detected_expected += len(expected_detected)
        total_missed += len(missed)
        if forbidden_hit:
            false_positive_cases += 1

        cases.append({
            "case_id": case.case_id,
            "title": case.title,
            "expected_rule_ids": sorted(case.expected_rule_ids),
            "detected_expected_rule_ids": expected_detected,
            "missed_rule_ids": missed,
            "forbidden_high_or_critical_hits": sorted(forbidden_hit),
            "score": response.module_score.score,
            "risk_label": response.module_score.risk_label,
            "total_findings": len(response.findings),
            "severity_breakdown": response.severity_breakdown,
        })

    recall = round(total_detected_expected / total_expected, 4) if total_expected else 1.0
    return {
        "ok": total_missed == 0 and false_positive_cases == 0,
        "benchmark_id": "web3guard_contract_phase_b_synthetic_v1",
        "purpose": "CI-safe benchmark for professional scanner Phase B rule coverage. Synthetic cases only; not a certified-audit benchmark.",
        "case_count": len(BENCHMARK_CASES),
        "expected_rule_signals": total_expected,
        "detected_expected_rule_signals": total_detected_expected,
        "missed_expected_rule_signals": total_missed,
        "false_positive_cases": false_positive_cases,
        "synthetic_recall": recall,
        "cases": cases,
    }
