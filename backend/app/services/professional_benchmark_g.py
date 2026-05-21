"""Professional Scanner Phase G — real-world style benchmark + rule tuning pack.

This engine is offline by default. It uses sanitized, real-world-inspired Solidity
fixtures to measure scanner recall, false-positive risk, severity drift and rule
family coverage. It does not claim certified-audit parity.
"""
from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal
from uuid import uuid4

from app.core.config import settings
from app.models.schemas import Finding
from app.services.scan_contract import available_contract_rules, scan_solidity

CaseClass = Literal["vulnerable", "clean", "regression"]
SEVERITY_RANK: dict[str, int] = {"critical": 5, "high": 4, "medium": 3, "low": 2, "info": 1}


@dataclass(frozen=True)
class RealWorldBenchmarkCase:
    case_id: str
    title: str
    case_class: CaseClass
    family: str
    project_name: str
    code: str
    expected_rule_ids: set[str] = field(default_factory=set)
    expected_min_severity: str | None = None
    forbidden_rule_ids: set[str] = field(default_factory=set)
    forbidden_high_or_critical_rule_ids: set[str] = field(default_factory=set)
    threat_model: str = ""
    reviewer_note: str = ""
    source_type: str = "sanitized_real_world_inspired_fixture"


VULN_RUG_TOKEN = """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
contract OwnerMintDrainToken {
    address public owner;
    mapping(address => bool) public blacklist;
    mapping(address => uint256) public balanceOf;
    event Transfer(address indexed from, address indexed to, uint256 amount);
    modifier onlyOwner(){ require(msg.sender == owner, "owner"); _; }
    constructor(){ owner = msg.sender; }
    function mint(address to, uint256 amount) external onlyOwner { balanceOf[to] += amount; emit Transfer(address(0), to, amount); }
    function setBlacklist(address user, bool blocked) external onlyOwner { blacklist[user] = blocked; }
    function emergencySweep(address payable to) external onlyOwner { to.transfer(address(this).balance); }
}
"""

VULN_DEX_ROUTER = """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
interface Router { function swapExactTokensForTokens(uint,uint,address[] calldata,address,uint) external returns(uint[] memory); }
contract ThinDexAdapter {
    Router public router;
    function swapAny(address[] calldata path) external {
        router.swapExactTokensForTokens(100 ether, 0, path, msg.sender, block.timestamp);
    }
}
"""

VULN_PROXY = """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
contract UpgradeableVault {
    address public owner;
    bool public initialized;
    function initialize(address newOwner) public { owner = newOwner; initialized = true; }
    function upgradeTo(address impl) external { _authorizeUpgrade(impl); }
    function _authorizeUpgrade(address) internal {}
}
"""

VULN_ORACLE_LENDING = """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
interface AggregatorV3Interface { function latestRoundData() external view returns (uint80,int256,uint256,uint256,uint80); function decimals() external view returns(uint8); }
contract OracleLending {
    AggregatorV3Interface public feed;
    mapping(address => uint256) public debt;
    function borrowLimit(address user) external view returns (uint256) {
        (, int256 price,,,) = feed.latestRoundData();
        return debt[user] * uint256(price);
    }
}
"""

VULN_BRIDGE = """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
contract BridgeExecutor {
    address public messenger;
    function execute(address target, bytes calldata payload) external {
        require(msg.sender == messenger, "messenger");
        (bool ok,) = target.call(payload);
        require(ok, "exec failed");
    }
}
"""

VULN_SIGNATURE_DROP = """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
contract SignatureAirdrop {
    function claim(bytes32 digest, uint8 v, bytes32 r, bytes32 s) external {
        address signer = ecrecover(digest, v, r, s);
        require(signer != address(0), "sig");
    }
}
"""

VULN_VAULT = """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
contract ShareVault {
    uint256 public totalAssets;
    uint256 public totalSupply;
    mapping(address => uint256) public balanceOf;
    function deposit(uint256 assets) external returns (uint256 shares) {
        shares = totalSupply == 0 ? assets : assets * totalSupply / totalAssets;
        balanceOf[msg.sender] += shares;
        totalAssets += assets;
        totalSupply += shares;
    }
}
"""

VULN_RANDOM_NFT = """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
contract RandomMint {
    function tokenId() external view returns (uint256) {
        return uint256(keccak256(abi.encodePacked(block.timestamp, blockhash(block.number - 1), msg.sender)));
    }
}
"""

VULN_MULTICALL = """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
contract MulticallValue {
    function multicall(bytes[] calldata calls) external payable returns (bytes[] memory results) {
        results = new bytes[](calls.length);
        for (uint256 i; i < calls.length; i++) {
            (bool ok, bytes memory data) = address(this).delegatecall(calls[i]);
            require(ok, "call failed");
            results[i] = data;
        }
    }
}
"""

VULN_GOVERNANCE = """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
interface IERC20 { function balanceOf(address) external view returns(uint256); }
contract FlashLoanGovernance {
    IERC20 public governanceToken;
    function propose(bytes calldata action) external {
        require(governanceToken.balanceOf(msg.sender) > 1_000_000 ether, "votes");
    }
}
"""

VULN_ACCESS_TRANSFERFROM = """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
interface IERC20 { function transferFrom(address,address,uint256) external returns(bool); }
contract RewardClaimer {
    IERC20 public token;
    function rescueFrom(address from, address to, uint256 amount) external {
        token.transferFrom(from, to, amount);
    }
}
"""

VULN_PRE_08 = """
// SPDX-License-Identifier: MIT
pragma solidity ^0.7.6;
contract OldMath {
    uint256 public total;
    function add(uint256 x) external { total = total + x; }
}
"""

CLEAN_TOKEN = """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
contract CleanCappedToken {
    address public owner;
    uint256 public immutable cap;
    uint256 public totalSupply;
    mapping(address => uint256) public balanceOf;
    event Transfer(address indexed from, address indexed to, uint256 amount);
    event OwnerTransferred(address indexed oldOwner, address indexed newOwner);
    modifier onlyOwner(){ require(msg.sender == owner, "owner"); _; }
    constructor(uint256 _cap){ owner = msg.sender; cap = _cap; }
    function mint(address to, uint256 amount) external onlyOwner {
        require(to != address(0), "zero");
        require(totalSupply + amount <= cap, "cap");
        totalSupply += amount; balanceOf[to] += amount; emit Transfer(address(0), to, amount);
    }
    function transferOwnership(address newOwner) external onlyOwner { require(newOwner != address(0), "zero"); emit OwnerTransferred(owner, newOwner); owner = newOwner; }
}
"""

CLEAN_ORACLE = """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
interface AggregatorV3Interface { function latestRoundData() external view returns (uint80,int256,uint256,uint256,uint80); function decimals() external view returns(uint8); }
contract CleanOracleConsumer {
    AggregatorV3Interface public feed;
    uint256 public constant MAX_STALE = 3600;
    function price() external view returns (uint256) {
        (, int256 answer,, uint256 updatedAt,) = feed.latestRoundData();
        require(answer > 0, "bad");
        require(updatedAt >= block.timestamp - MAX_STALE, "stale");
        uint8 d = feed.decimals();
        return d < 18 ? uint256(answer) * (10 ** (18 - d)) : uint256(answer) / (10 ** (d - 18));
    }
}
"""

CLEAN_REENTRANCY_GUARD = """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
contract CleanWithdraw {
    mapping(address => uint256) public credit;
    bool private locked;
    modifier nonReentrant(){ require(!locked, "locked"); locked = true; _; locked = false; }
    function deposit() external payable { credit[msg.sender] += msg.value; }
    function withdraw() external nonReentrant {
        uint256 amount = credit[msg.sender];
        credit[msg.sender] = 0;
        (bool ok,) = msg.sender.call{value: amount}("");
        require(ok, "send");
    }
}
"""

CLEAN_SIGNATURE = """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
contract CleanPermitLike {
    mapping(address => uint256) public nonces;
    bytes32 public immutable DOMAIN_SEPARATOR;
    constructor(){ DOMAIN_SEPARATOR = keccak256(abi.encode(block.chainid, address(this))); }
    function claim(bytes32 digest, uint8 v, bytes32 r, bytes32 s, uint256 deadline) external {
        require(block.timestamp <= deadline, "expired");
        address signer = ecrecover(keccak256(abi.encodePacked(DOMAIN_SEPARATOR, digest, nonces[msg.sender])), v, r, s);
        require(signer == msg.sender, "bad");
        nonces[msg.sender] += 1;
    }
}
"""

CLEAN_BRIDGE = """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
contract CleanBridgeReceiver {
    address public messenger;
    mapping(bytes32 => bool) public processed;
    function receiveMessage(address originalSender, bytes32 messageId, address target, bytes calldata payload) external {
        require(msg.sender == messenger, "messenger");
        require(originalSender != address(0), "sender");
        require(!processed[messageId], "done");
        processed[messageId] = true;
        (bool ok,) = target.call(payload);
        require(ok, "exec failed");
    }
}
"""

CLEAN_VAULT = """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
contract CleanShareVault {
    uint256 public constant MIN_SHARES = 1000;
    uint256 public totalAssets;
    uint256 public totalSupply;
    mapping(address => uint256) public balanceOf;
    function previewDeposit(uint256 assets) public view returns(uint256){ return totalSupply == 0 ? assets : assets * totalSupply / totalAssets; }
    function deposit(uint256 assets) external returns (uint256 shares) {
        shares = previewDeposit(assets);
        require(shares >= MIN_SHARES, "inflation");
        balanceOf[msg.sender] += shares; totalAssets += assets; totalSupply += shares;
    }
}
"""

CLEAN_TIMELOCK_ADMIN = """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
contract CleanAdminConfig {
    address public owner;
    address public pendingTreasury;
    uint256 public queuedAt;
    uint256 public constant DELAY = 2 days;
    uint256 public maxFeeBps = 500;
    event TreasuryQueued(address indexed treasury);
    event FeeUpdated(uint256 feeBps);
    modifier onlyOwner(){ require(msg.sender == owner, "owner"); _; }
    constructor(){ owner = msg.sender; }
    function queueTreasury(address t) external onlyOwner { require(t != address(0), "zero"); pendingTreasury = t; queuedAt = block.timestamp; emit TreasuryQueued(t); }
    function setFee(uint256 feeBps) external onlyOwner { require(feeBps <= maxFeeBps, "cap"); emit FeeUpdated(feeBps); }
}
"""

CLEAN_DEX = """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
interface Router { function swapExactTokensForTokens(uint,uint,address[] calldata,address,uint) external returns(uint[] memory); }
contract CleanDexAdapter {
    Router public router;
    function swap(address[] calldata path, uint256 minOut, uint256 deadline) external {
        require(minOut > 0, "slippage");
        require(deadline > block.timestamp + 60, "deadline");
        router.swapExactTokensForTokens(100 ether, minOut, path, msg.sender, deadline);
    }
}
"""

REAL_WORLD_BENCHMARK_CASES: list[RealWorldBenchmarkCase] = [
    RealWorldBenchmarkCase(
        case_id="g_token_owner_mint_blacklist_sweep",
        title="Token owner mint/blacklist/emergency sweep risk",
        case_class="vulnerable",
        family="token_admin_rug",
        project_name="OwnerMintDrainToken",
        expected_rule_ids={"WG-SOL-TOKEN-002", "WG-SOL-ADMIN-003", "WG-SOL-RUG-001", "WG-SOL-RUG-002"},
        expected_min_severity="medium",
        code=VULN_RUG_TOKEN,
        threat_model="Owner can change token supply, block users or sweep funds. Needs disclosure, cap, timelock or governance controls.",
    ),
    RealWorldBenchmarkCase(
        case_id="g_dex_zero_slippage_deadline",
        title="DEX adapter zero slippage and weak deadline",
        case_class="vulnerable",
        family="mev_swap",
        project_name="ThinDexAdapter",
        expected_rule_ids={"WG-SOL-MEV-001", "WG-SOL-MEV-002", "WG-SOL-FRONT-001"},
        expected_min_severity="high",
        code=VULN_DEX_ROUTER,
        threat_model="Sandwich/front-run risk from zero minimum output and current-block deadline.",
    ),
    RealWorldBenchmarkCase(
        case_id="g_proxy_initializer_upgrade_auth",
        title="Upgradeable implementation initializer and authorization review",
        case_class="vulnerable",
        family="upgradeability",
        project_name="UpgradeableVault",
        expected_rule_ids={"WG-SOL-UPGRADE-002", "WG-SOL-UPGRADE-003", "WG-SOL-UPGRADE-004"},
        expected_min_severity="high",
        code=VULN_PROXY,
        threat_model="Upgradeable implementation can be initialized or upgraded without a clear protected authorization path.",
    ),
    RealWorldBenchmarkCase(
        case_id="g_oracle_lending_stale_decimal",
        title="Lending oracle missing freshness and decimal normalization",
        case_class="vulnerable",
        family="oracle_lending",
        project_name="OracleLending",
        expected_rule_ids={"WG-SOL-ORACLE-001", "WG-SOL-ORACLE-002", "WG-SOL-DEFI-002"},
        expected_min_severity="medium",
        code=VULN_ORACLE_LENDING,
        threat_model="Bad oracle assumptions can inflate borrow limits or misprice collateral.",
    ),
    RealWorldBenchmarkCase(
        case_id="g_bridge_sender_validation",
        title="Bridge executor validates messenger but not original sender/replay",
        case_class="vulnerable",
        family="bridge_crosschain",
        project_name="BridgeExecutor",
        expected_rule_ids={"WG-SOL-XCHAIN-001", "WG-SOL-CALL-003"},
        expected_min_severity="high",
        code=VULN_BRIDGE,
        threat_model="Cross-chain receivers need both messenger and original sender/message replay validation.",
    ),
    RealWorldBenchmarkCase(
        case_id="g_signature_replay_raw_ecrecover",
        title="Signature claim path without nonce/deadline and raw ecrecover",
        case_class="vulnerable",
        family="signature_replay",
        project_name="SignatureAirdrop",
        expected_rule_ids={"WG-SOL-SIG-003", "WG-SOL-SIG-004", "WG-SOL-SIG-005", "WG-SOL-SIG-001"},
        expected_min_severity="medium",
        code=VULN_SIGNATURE_DROP,
        threat_model="Signed claims can be replayed if nonce/deadline/domain separation is missing.",
    ),
    RealWorldBenchmarkCase(
        case_id="g_erc4626_inflation_rounding",
        title="Vault share math requires inflation and rounding review",
        case_class="vulnerable",
        family="vault_erc4626",
        project_name="ShareVault",
        expected_rule_ids={"WG-SOL-VAULT-001", "WG-SOL-VAULT-002"},
        expected_min_severity="medium",
        code=VULN_VAULT,
        threat_model="First depositor / donation style inflation and rounding can dilute users.",
    ),
    RealWorldBenchmarkCase(
        case_id="g_random_nft_timestamp_blockhash",
        title="NFT/randomness uses block timestamp and blockhash",
        case_class="vulnerable",
        family="nft_randomness",
        project_name="RandomMint",
        expected_rule_ids={"WG-SOL-RAND-001"},
        expected_min_severity="medium",
        code=VULN_RANDOM_NFT,
        threat_model="Miner/validator-influenceable randomness can be gamed for mint outcomes.",
    ),
    RealWorldBenchmarkCase(
        case_id="g_multicall_msg_value_delegatecall",
        title="Multicall delegatecall path with msg.value reuse review",
        case_class="vulnerable",
        family="multicall_value",
        project_name="MulticallValue",
        expected_rule_ids={"WG-SOL-MULTI-001", "WG-SOL-CALL-001"},
        expected_min_severity="medium",
        code=VULN_MULTICALL,
        threat_model="Payable multicall/delegatecall patterns can reuse msg.value across internal calls.",
    ),
    RealWorldBenchmarkCase(
        case_id="g_governance_flashloan_votes",
        title="Governance proposal threshold reads current token balance",
        case_class="vulnerable",
        family="governance_flashloan",
        project_name="FlashLoanGovernance",
        expected_rule_ids={"WG-SOL-GOV-001", "WG-SOL-DEFI-001"},
        expected_min_severity="medium",
        code=VULN_GOVERNANCE,
        threat_model="Flash-loaned governance token balances can pass threshold without snapshots/time locks.",
    ),
    RealWorldBenchmarkCase(
        case_id="g_arbitrary_transfer_from",
        title="Public arbitrary transferFrom call path",
        case_class="vulnerable",
        family="access_control_token_transfer",
        project_name="RewardClaimer",
        expected_rule_ids={"WG-SOL-ARBTRF-001"},
        expected_min_severity="high",
        code=VULN_ACCESS_TRANSFERFROM,
        threat_model="Unrestricted transferFrom paths can move approved user funds.",
    ),
    RealWorldBenchmarkCase(
        case_id="g_old_compiler_overflow",
        title="Pre-0.8 compiler arithmetic requires overflow review",
        case_class="vulnerable",
        family="old_compiler_math",
        project_name="OldMath",
        expected_rule_ids={"WG-SOL-OVFL-001", "WG-SOL-META-004"},
        expected_min_severity="medium",
        code=VULN_PRE_08,
        threat_model="Solidity before 0.8 does not have built-in overflow checks.",
    ),
    RealWorldBenchmarkCase(
        case_id="g_clean_capped_token",
        title="Clean capped token with owner event and cap",
        case_class="clean",
        family="clean_token_admin",
        project_name="CleanCappedToken",
        forbidden_high_or_critical_rule_ids={"WG-SOL-RUG-001", "WG-SOL-RUG-002", "WG-SOL-ADMIN-003"},
        code=CLEAN_TOKEN,
        reviewer_note="Clean fixtures may still produce low/info transparency notes, but should not produce severe rug/admin findings.",
    ),
    RealWorldBenchmarkCase(
        case_id="g_clean_oracle",
        title="Clean oracle consumer with freshness and decimals",
        case_class="clean",
        family="clean_oracle",
        project_name="CleanOracleConsumer",
        forbidden_rule_ids={"WG-SOL-ORACLE-001", "WG-SOL-ORACLE-002"},
        code=CLEAN_ORACLE,
    ),
    RealWorldBenchmarkCase(
        case_id="g_clean_reentrancy_guard",
        title="Clean withdrawal with state update and reentrancy guard",
        case_class="clean",
        family="clean_reentrancy",
        project_name="CleanWithdraw",
        forbidden_high_or_critical_rule_ids={"WG-SOL-REENT-001", "WG-SOL-REENT-002"},
        code=CLEAN_REENTRANCY_GUARD,
    ),
    RealWorldBenchmarkCase(
        case_id="g_clean_signature",
        title="Clean signature path with nonce, deadline and chain-aware domain",
        case_class="clean",
        family="clean_signature",
        project_name="CleanPermitLike",
        forbidden_rule_ids={"WG-SOL-SIG-003", "WG-SOL-SIG-004", "WG-SOL-SIG-002"},
        code=CLEAN_SIGNATURE,
    ),
    RealWorldBenchmarkCase(
        case_id="g_clean_bridge",
        title="Clean bridge receiver with original sender and replay tracking",
        case_class="clean",
        family="clean_bridge",
        project_name="CleanBridgeReceiver",
        forbidden_rule_ids={"WG-SOL-XCHAIN-001"},
        code=CLEAN_BRIDGE,
    ),
    RealWorldBenchmarkCase(
        case_id="g_clean_vault",
        title="Clean vault with minimum shares and preview policy",
        case_class="clean",
        family="clean_vault",
        project_name="CleanShareVault",
        forbidden_rule_ids={"WG-SOL-VAULT-001", "WG-SOL-VAULT-002"},
        code=CLEAN_VAULT,
    ),
    RealWorldBenchmarkCase(
        case_id="g_clean_timelock_admin",
        title="Clean admin config with cap, event and queued treasury",
        case_class="clean",
        family="clean_admin_config",
        project_name="CleanAdminConfig",
        forbidden_high_or_critical_rule_ids={"WG-SOL-ADMIN-005", "WG-SOL-ADMIN-006"},
        code=CLEAN_TIMELOCK_ADMIN,
    ),
    RealWorldBenchmarkCase(
        case_id="g_clean_dex",
        title="Clean DEX adapter with minOut and future deadline",
        case_class="clean",
        family="clean_mev_swap",
        project_name="CleanDexAdapter",
        forbidden_rule_ids={"WG-SOL-MEV-001", "WG-SOL-MEV-002", "WG-SOL-FRONT-001"},
        code=CLEAN_DEX,
    ),
]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _case_hash(code: str) -> str:
    return hashlib.sha256(code.encode("utf-8", errors="ignore")).hexdigest()[:16]


def _severity_meets(actual: str | None, minimum: str | None) -> bool:
    if not minimum:
        return True
    return SEVERITY_RANK.get(str(actual or "info"), 0) >= SEVERITY_RANK.get(minimum, 0)


def _highest(findings: list[Finding]) -> str | None:
    if not findings:
        return None
    return str(max(findings, key=lambda f: SEVERITY_RANK.get(str(f.severity), 0)).severity)


def _finding_brief(finding: Finding) -> dict[str, Any]:
    return {
        "id": finding.id,
        "rule_id": finding.rule_id,
        "title": finding.title,
        "severity": finding.severity,
        "confidence": finding.confidence,
        "category": finding.category,
        "affected_file": finding.affected_file,
        "affected_line": finding.affected_line,
        "source_tools": finding.source_tools,
        "verification_status": finding.verification_status,
        "remediation_priority": finding.remediation_priority,
    }


def _scan_case(case: RealWorldBenchmarkCase) -> dict[str, Any]:
    response = scan_solidity(case.code, project_name=case.project_name)
    findings = [f for f in response.findings if getattr(f, "category", "") != "tool_status"]
    by_rule: dict[str, list[Finding]] = defaultdict(list)
    for finding in findings:
        if finding.rule_id:
            by_rule[str(finding.rule_id)].append(finding)
    detected_rule_ids = set(by_rule.keys())

    expected_detected = sorted(case.expected_rule_ids.intersection(detected_rule_ids))
    missed_rule_ids = sorted(case.expected_rule_ids.difference(detected_rule_ids))
    expected_findings = [f for rid in case.expected_rule_ids for f in by_rule.get(rid, [])]
    highest_expected_severity = _highest(expected_findings)
    severity_ok = _severity_meets(highest_expected_severity, case.expected_min_severity)

    forbidden_hits = sorted(case.forbidden_rule_ids.intersection(detected_rule_ids))
    severe_forbidden_hits: list[str] = []
    for rule_id in case.forbidden_high_or_critical_rule_ids:
        for finding in by_rule.get(rule_id, []):
            if finding.severity in {"critical", "high"}:
                severe_forbidden_hits.append(rule_id)
                break
    severe_forbidden_hits = sorted(set(severe_forbidden_hits))

    passed = not missed_rule_ids and severity_ok and not forbidden_hits and not severe_forbidden_hits
    return {
        "case_id": case.case_id,
        "title": case.title,
        "case_class": case.case_class,
        "family": case.family,
        "source_type": case.source_type,
        "code_sha256_16": _case_hash(case.code),
        "expected_rule_ids": sorted(case.expected_rule_ids),
        "detected_expected_rule_ids": expected_detected,
        "missed_rule_ids": missed_rule_ids,
        "expected_min_severity": case.expected_min_severity,
        "highest_expected_severity": highest_expected_severity,
        "severity_ok": severity_ok,
        "forbidden_rule_hits": forbidden_hits,
        "forbidden_high_or_critical_hits": severe_forbidden_hits,
        "passed": passed,
        "score": response.module_score.score,
        "risk_label": response.module_score.risk_label,
        "total_findings": len(findings),
        "severity_breakdown": response.severity_breakdown,
        "top_findings": [_finding_brief(f) for f in findings[:10]],
        "threat_model": case.threat_model,
        "reviewer_note": case.reviewer_note,
    }


def _family_metrics(case_results: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for result in case_results:
        grouped[str(result["family"])].append(result)
    metrics: dict[str, dict[str, Any]] = {}
    for family, rows in grouped.items():
        expected = sum(len(r["expected_rule_ids"]) for r in rows)
        detected = sum(len(r["detected_expected_rule_ids"]) for r in rows)
        clean_rows = [r for r in rows if r["case_class"] == "clean"]
        fp_rows = [r for r in clean_rows if r["forbidden_rule_hits"] or r["forbidden_high_or_critical_hits"]]
        metrics[family] = {
            "case_count": len(rows),
            "expected_signals": expected,
            "detected_expected_signals": detected,
            "recall": round(detected / expected, 4) if expected else None,
            "false_positive_case_count": len(fp_rows),
            "passed_case_count": sum(1 for r in rows if r["passed"]),
            "case_ids": [r["case_id"] for r in rows],
        }
    return metrics


def _rule_family_map() -> dict[str, str]:
    mapping: dict[str, str] = {}
    for rule in available_contract_rules():
        rid = str(rule.get("id") or "")
        if rid:
            mapping[rid] = str(rule.get("category") or "unknown")
    return mapping


def _build_tuning_pack(case_results: list[dict[str, Any]]) -> dict[str, Any]:
    rule_family = _rule_family_map()
    missed = Counter(rule for row in case_results for rule in row["missed_rule_ids"])
    noisy = Counter(rule for row in case_results for rule in row["forbidden_rule_hits"] + row["forbidden_high_or_critical_hits"])
    severity_drift = Counter(
        rule
        for row in case_results
        if row["expected_rule_ids"] and not row["severity_ok"]
        for rule in row["expected_rule_ids"]
    )
    tickets: list[dict[str, Any]] = []
    for rule_id, count in missed.items():
        tickets.append({
            "ticket_id": f"TUNE-MISS-{rule_id}",
            "rule_id": rule_id,
            "family": rule_family.get(rule_id, "unknown"),
            "priority": "critical" if count >= 2 else "high",
            "issue_type": "missed_detection",
            "evidence_count": count,
            "recommended_action": "expand_pattern_context_or_add_ast_level_detector",
            "safe_next_step": "Add one regression fixture before changing severity.",
        })
    for rule_id, count in noisy.items():
        tickets.append({
            "ticket_id": f"TUNE-FP-{rule_id}",
            "rule_id": rule_id,
            "family": rule_family.get(rule_id, "unknown"),
            "priority": "high",
            "issue_type": "false_positive",
            "evidence_count": count,
            "recommended_action": "tighten_guard_conditions_or_lower_confidence",
            "safe_next_step": "Verify if clean fixture has mitigating controls such as cap, timelock, nonce or minOut.",
        })
    for rule_id, count in severity_drift.items():
        tickets.append({
            "ticket_id": f"TUNE-SEV-{rule_id}",
            "rule_id": rule_id,
            "family": rule_family.get(rule_id, "unknown"),
            "priority": "medium",
            "issue_type": "severity_drift",
            "evidence_count": count,
            "recommended_action": "review severity mapping for benchmark threat model",
            "safe_next_step": "Do not raise severity unless impact and exploitability are both supported by evidence.",
        })
    tickets.sort(key=lambda item: ({"critical": 0, "high": 1, "medium": 2, "low": 3}.get(str(item["priority"]), 4), item["rule_id"]))
    return {
        "generated_at": _now_iso(),
        "missed_rules": dict(missed),
        "noisy_rules": dict(noisy),
        "severity_drift_rules": dict(severity_drift),
        "tuning_ticket_count": len(tickets),
        "tickets": tickets[:80],
        "policy": "Tuning suggestions are internal QA guidance. They do not certify any project as safe.",
    }


def _quality_gate(recall: float, clean_specificity: float, pass_rate: float, family_metrics: dict[str, dict[str, Any]], missed_total: int, fp_case_count: int) -> dict[str, Any]:
    weighted_score = round((recall * 0.45 + clean_specificity * 0.35 + pass_rate * 0.20) * 100, 2)
    weak_families = sorted(
        family for family, metrics in family_metrics.items()
        if metrics.get("recall") is not None and float(metrics.get("recall") or 0) < 0.80
    )
    professional_engine_ready = weighted_score >= 88 and recall >= 0.85 and clean_specificity >= 0.80 and len(weak_families) <= 3
    direct_level_engine_progress = weighted_score >= 96 and recall >= 0.95 and clean_specificity >= 0.92 and missed_total == 0 and fp_case_count == 0
    return {
        "label": "direct_level_engine_progress" if direct_level_engine_progress else ("professional_engine_ready" if professional_engine_ready else "needs_tuning"),
        "score": weighted_score,
        "professional_engine_ready": professional_engine_ready,
        "direct_level_engine_progress": direct_level_engine_progress,
        "direct_competition_public_claim_allowed": False,
        "weak_families": weak_families,
        "why_no_public_direct_claim_yet": [
            "Dataset is curated/sanitized and must be expanded with independently reviewed real cases.",
            "Certified audit competition requires human auditors, legal review, public report history and external validation.",
            "This benchmark proves scanner-engine progress only, not certified-audit equivalence.",
        ],
    }


def run_real_world_benchmark() -> dict[str, Any]:
    results = [_scan_case(case) for case in REAL_WORLD_BENCHMARK_CASES]
    vulnerable = [r for r in results if r["case_class"] == "vulnerable"]
    clean = [r for r in results if r["case_class"] == "clean"]
    expected_total = sum(len(r["expected_rule_ids"]) for r in results)
    detected_total = sum(len(r["detected_expected_rule_ids"]) for r in results)
    missed_total = sum(len(r["missed_rule_ids"]) for r in results)
    fp_cases = [r for r in clean if r["forbidden_rule_hits"] or r["forbidden_high_or_critical_hits"]]
    severity_fail_cases = [r for r in vulnerable if not r["severity_ok"]]
    passed = sum(1 for r in results if r["passed"])
    recall = round(detected_total / expected_total, 4) if expected_total else 1.0
    clean_specificity = round((len(clean) - len(fp_cases)) / len(clean), 4) if clean else 1.0
    pass_rate = round(passed / len(results), 4) if results else 0.0
    family_metrics = _family_metrics(results)
    tuning_pack = _build_tuning_pack(results)
    gate = _quality_gate(recall, clean_specificity, pass_rate, family_metrics, missed_total, len(fp_cases))
    return {
        "ok": missed_total == 0 and not fp_cases and not severity_fail_cases,
        "phase": "Professional Scanner Phase G",
        "benchmark_id": "web3guard_real_world_style_contract_benchmark_v1",
        "generated_at": _now_iso(),
        "dataset_policy": "Sanitized real-world-inspired fixtures. No private project code, secrets or exploit automation. Not a certified-audit dataset.",
        "case_count": len(results),
        "vulnerable_case_count": len(vulnerable),
        "clean_case_count": len(clean),
        "family_count": len(family_metrics),
        "expected_rule_signals": expected_total,
        "detected_expected_rule_signals": detected_total,
        "missed_expected_rule_signals": missed_total,
        "false_positive_case_count": len(fp_cases),
        "severity_fail_case_count": len(severity_fail_cases),
        "passed_case_count": passed,
        "real_world_style_recall": recall,
        "clean_specificity": clean_specificity,
        "pass_rate": pass_rate,
        "quality_gate": gate,
        "family_metrics": family_metrics,
        "tuning_pack": tuning_pack,
        "cases": results,
        "direct_competition_path": [
            "Expand dataset with audited public reports and CTF/lab fixtures.",
            "Convert every miss/false-positive into regression tests.",
            "Add independent reviewer confirmation before any stronger market claim.",
            "Pair scanner output with Phase E human review and Phase D proof reports.",
        ],
        "blocked_claim": "Do not claim CertiK/OpenZeppelin/Hacken parity from this benchmark alone.",
    }


def dataset_catalog() -> dict[str, Any]:
    return {
        "phase": "Professional Scanner Phase G",
        "dataset_id": "web3guard_real_world_style_contract_benchmark_v1",
        "case_count": len(REAL_WORLD_BENCHMARK_CASES),
        "families": sorted({case.family for case in REAL_WORLD_BENCHMARK_CASES}),
        "cases": [
            {
                "case_id": case.case_id,
                "title": case.title,
                "case_class": case.case_class,
                "family": case.family,
                "project_name": case.project_name,
                "expected_rule_ids": sorted(case.expected_rule_ids),
                "forbidden_rule_ids": sorted(case.forbidden_rule_ids),
                "forbidden_high_or_critical_rule_ids": sorted(case.forbidden_high_or_critical_rule_ids),
                "code_sha256_16": _case_hash(case.code),
                "source_type": case.source_type,
            }
            for case in REAL_WORLD_BENCHMARK_CASES
        ],
        "privacy": "Catalog intentionally excludes full code unless /run is called by an authorized backend user/test.",
    }


def _regression_path() -> Path:
    return Path(settings.professional_benchmark_regression_file)


def append_regression_case(payload: dict[str, Any]) -> dict[str, Any]:
    code = str(payload.get("solidity_code") or "")
    record = {
        "id": f"RB-{uuid4().hex[:12]}",
        "created_at": _now_iso(),
        "title": str(payload.get("title") or "Custom regression case").strip()[:180],
        "case_class": str(payload.get("case_class") or "regression").strip()[:40],
        "family": str(payload.get("family") or "custom").strip()[:80],
        "expected_rule_ids": [str(x).strip() for x in payload.get("expected_rule_ids") or [] if str(x).strip()][:80],
        "forbidden_rule_ids": [str(x).strip() for x in payload.get("forbidden_rule_ids") or [] if str(x).strip()][:80],
        "notes": str(payload.get("notes") or "").strip()[:3000],
        "code_sha256": hashlib.sha256(code.encode("utf-8", errors="ignore")).hexdigest() if code else None,
        "code_stored": bool(payload.get("store_code", False)) and bool(code),
        "solidity_code": code[:220000] if payload.get("store_code", False) else None,
        "privacy_rule": "Store code only when reviewer confirms it is sanitized and approved for internal regression use.",
    }
    path = _regression_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    return record


def list_regression_cases(limit: int = 100) -> list[dict[str, Any]]:
    path = _regression_path()
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            try:
                item = json.loads(line)
            except Exception:
                continue
            item.pop("solidity_code", None)
            rows.append(item)
    return rows[-max(1, min(limit, 500)):][::-1]


def run_custom_real_world_case(solidity_code: str, expected_rule_ids: list[str] | None = None, forbidden_rule_ids: list[str] | None = None, family: str = "custom") -> dict[str, Any]:
    case = RealWorldBenchmarkCase(
        case_id=f"custom_g_{uuid4().hex[:10]}",
        title="Custom Phase G benchmark case",
        case_class="regression",
        family=family or "custom",
        project_name="CustomPhaseGCase",
        expected_rule_ids={x.strip() for x in expected_rule_ids or [] if x.strip()},
        forbidden_rule_ids={x.strip() for x in forbidden_rule_ids or [] if x.strip()},
        code=solidity_code,
        source_type="user_supplied_regression_case_not_stored_by_default",
    )
    return _scan_case(case)


def phase_g_readiness_summary() -> dict[str, Any]:
    return {
        "phase": "Professional Scanner Phase G",
        "status": "active",
        "benchmark_endpoint": "/professional-benchmark/run",
        "dataset_endpoint": "/professional-benchmark/dataset",
        "tuning_endpoint": "/professional-benchmark/tuning-pack",
        "case_count": len(REAL_WORLD_BENCHMARK_CASES),
        "families_tracked": len({case.family for case in REAL_WORLD_BENCHMARK_CASES}),
        "public_claim_allowed": False,
        "goal": "Move from synthetic unit fixtures to broader real-world-style scanner calibration before stronger competition claims.",
    }
