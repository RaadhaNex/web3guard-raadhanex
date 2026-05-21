"""Professional Scanner Phase F — benchmark + false-positive accuracy engine.

This module is intentionally local/offline by default. It gives Web3Guard a
repeatable, measurable scanner-quality loop without making certified-audit or
100%-secure claims.
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal
from uuid import uuid4

from app.core.config import settings
from app.models.schemas import Finding
from app.services.scan_contract import available_contract_rules, scan_solidity

SEVERITY_RANK: dict[str, int] = {"critical": 5, "high": 4, "medium": 3, "low": 2, "info": 1}
CONFIDENCE_RANK: dict[str, int] = {"high": 3, "medium": 2, "low": 1}

BenchmarkClass = Literal["vulnerable", "clean", "regression"]
FeedbackVerdict = Literal["confirmed", "false_positive", "accepted_risk", "fixed", "missed", "needs_evidence"]


@dataclass(frozen=True)
class AccuracyBenchmarkCase:
    case_id: str
    title: str
    case_class: BenchmarkClass
    code: str
    expected_rule_ids: set[str]
    expected_min_severity: str | None = None
    forbidden_rule_ids: set[str] | None = None
    forbidden_high_or_critical_rule_ids: set[str] | None = None
    notes: str = ""
    project_name: str | None = None


VULNERABLE_REENTRANCY = """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
contract ReentrancyVault {
    mapping(address => uint256) public balance;
    function deposit() external payable { balance[msg.sender] += msg.value; }
    function withdraw() external {
        uint256 amount = balance[msg.sender];
        (bool ok,) = msg.sender.call{value: amount}("");
        require(ok, "send failed");
        balance[msg.sender] = 0;
    }
}
"""

VULNERABLE_AUTH = """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
contract AuthRisk {
    address public owner;
    constructor() { owner = msg.sender; }
    function emergencyWithdraw(address payable to) public {
        to.transfer(address(this).balance);
    }
    function trustedOnly() external view returns (bool) {
        return tx.origin == owner;
    }
}
"""

VULNERABLE_ORACLE = """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
interface AggregatorV3Interface { function latestRoundData() external view returns (uint80,int256,uint256,uint256,uint80); function decimals() external view returns(uint8); }
contract OracleRisk {
    AggregatorV3Interface public priceFeed;
    function price() external view returns (int256) {
        (, int256 answer,,,) = priceFeed.latestRoundData();
        return answer;
    }
}
"""

VULNERABLE_SWAP = """
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

VULNERABLE_SIG = """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
contract SignatureRisk {
    mapping(bytes32 => bool) public used;
    function claim(bytes32 digest, uint8 v, bytes32 r, bytes32 s) external {
        address signer = ecrecover(digest, v, r, s);
        require(signer != address(0), "bad sig");
    }
}
"""

VULNERABLE_UPGRADE = """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
contract UUPSRisk {
    address public owner;
    bool public initialized;
    function initialize(address newOwner) public { owner = newOwner; initialized = true; }
    function upgradeTo(address impl) external { _authorizeUpgrade(impl); }
    function _authorizeUpgrade(address) internal {}
}
"""

VULNERABLE_XCHAIN = """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
contract BridgeReceiver {
    address public messenger;
    function receiveMessage(address target, bytes calldata data) external {
        require(msg.sender == messenger, "messenger");
        (bool ok,) = target.call(data);
        require(ok, "call failed");
    }
}
"""

CLEAN_OWNABLE = """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
contract CleanOwnable {
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
"""

CLEAN_PULL_PAYMENT = """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
contract CleanPullPayment {
    mapping(address => uint256) public credit;
    bool private locked;
    modifier nonReentrant() { require(!locked, "locked"); locked = true; _; locked = false; }
    function deposit() external payable { credit[msg.sender] += msg.value; }
    function withdraw() external nonReentrant {
        uint256 amount = credit[msg.sender];
        credit[msg.sender] = 0;
        (bool ok,) = msg.sender.call{value: amount}("");
        require(ok, "send failed");
    }
}
"""

CLEAN_ORACLE = """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
interface AggregatorV3Interface { function latestRoundData() external view returns (uint80,int256,uint256,uint256,uint80); function decimals() external view returns(uint8); }
contract CleanOracle {
    AggregatorV3Interface public priceFeed;
    uint256 public constant MAX_STALENESS = 1 hours;
    function price() external view returns (uint256) {
        (, int256 answer,, uint256 updatedAt,) = priceFeed.latestRoundData();
        require(answer > 0, "bad price");
        require(updatedAt >= block.timestamp - MAX_STALENESS, "stale");
        uint8 d = priceFeed.decimals();
        if (d < 18) { return uint256(answer) * (10 ** (18 - d)); }
        return uint256(answer) / (10 ** (d - 18));
    }
}
"""

CLEAN_SIG = """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
contract CleanSignature {
    mapping(address => uint256) public nonces;
    function claim(bytes32 digest, uint8 v, bytes32 r, bytes32 s, uint256 deadline) external {
        require(block.timestamp <= deadline, "expired");
        address signer = ecrecover(digest, v, r, s);
        require(signer != address(0), "bad sig");
        nonces[signer] += 1;
    }
}
"""

BENCHMARK_CASES: list[AccuracyBenchmarkCase] = [
    AccuracyBenchmarkCase(
        case_id="f_reentrancy_external_call_before_state_update",
        title="Reentrancy: value transfer before balance update",
        case_class="vulnerable",
        project_name="ReentrancyVault",
        expected_rule_ids={"WG-SOL-REENT-001", "WG-SOL-REENT-002"},
        expected_min_severity="high",
        code=VULNERABLE_REENTRANCY,
        notes="Known dangerous external call ordering. A professional scanner should catch this reliably.",
    ),
    AccuracyBenchmarkCase(
        case_id="f_auth_public_emergency_withdraw_tx_origin",
        title="Access control: public emergency withdraw and tx.origin",
        case_class="vulnerable",
        project_name="AuthRisk",
        expected_rule_ids={"WG-SOL-AUTH-001", "WG-SOL-AUTH-002"},
        expected_min_severity="high",
        code=VULNERABLE_AUTH,
    ),
    AccuracyBenchmarkCase(
        case_id="f_oracle_stale_decimal",
        title="Oracle: missing stale price and decimal handling",
        case_class="vulnerable",
        project_name="OracleRisk",
        expected_rule_ids={"WG-SOL-ORACLE-001", "WG-SOL-ORACLE-002"},
        expected_min_severity="medium",
        code=VULNERABLE_ORACLE,
    ),
    AccuracyBenchmarkCase(
        case_id="f_swap_zero_min_weak_deadline",
        title="MEV: zero min output and weak deadline",
        case_class="vulnerable",
        project_name="SwapRisk",
        expected_rule_ids={"WG-SOL-MEV-001", "WG-SOL-MEV-002"},
        expected_min_severity="high",
        code=VULNERABLE_SWAP,
    ),
    AccuracyBenchmarkCase(
        case_id="f_signature_nonce_expiry_malleability",
        title="Signature: replay and raw ecrecover review",
        case_class="vulnerable",
        project_name="SignatureRisk",
        expected_rule_ids={"WG-SOL-SIG-004", "WG-SOL-SIG-005"},
        expected_min_severity="medium",
        code=VULNERABLE_SIG,
    ),
    AccuracyBenchmarkCase(
        case_id="f_upgradeable_initializer_auth",
        title="Upgradeable: public initializer and empty authorize upgrade hook",
        case_class="vulnerable",
        project_name="UUPSRisk",
        expected_rule_ids={"WG-SOL-UPGRADE-002", "WG-SOL-UPGRADE-003", "WG-SOL-UPGRADE-004"},
        expected_min_severity="high",
        code=VULNERABLE_UPGRADE,
    ),
    AccuracyBenchmarkCase(
        case_id="f_xchain_target_call_sender_validation",
        title="Cross-chain: messenger path needs original sender validation",
        case_class="vulnerable",
        project_name="BridgeReceiver",
        expected_rule_ids={"WG-SOL-XCHAIN-001"},
        expected_min_severity="high",
        code=VULNERABLE_XCHAIN,
    ),
    AccuracyBenchmarkCase(
        case_id="f_clean_ownable_no_severe_false_positive",
        title="Clean: ownable transfer with event and zero address check",
        case_class="clean",
        project_name="CleanOwnable",
        expected_rule_ids=set(),
        forbidden_high_or_critical_rule_ids={
            "WG-SOL-REENT-001", "WG-SOL-AUTH-001", "WG-SOL-AUTH-002", "WG-SOL-ORACLE-001",
            "WG-SOL-MEV-001", "WG-SOL-UPGRADE-003", "WG-SOL-XCHAIN-001",
        },
        code=CLEAN_OWNABLE,
    ),
    AccuracyBenchmarkCase(
        case_id="f_clean_pull_payment_no_reentrancy_fp",
        title="Clean: pull payment with state update before call and reentrancy lock",
        case_class="clean",
        project_name="CleanPullPayment",
        expected_rule_ids=set(),
        forbidden_high_or_critical_rule_ids={"WG-SOL-REENT-001", "WG-SOL-REENT-002"},
        code=CLEAN_PULL_PAYMENT,
    ),
    AccuracyBenchmarkCase(
        case_id="f_clean_oracle_no_oracle_high_fp",
        title="Clean: oracle with stale price and decimal normalization",
        case_class="clean",
        project_name="CleanOracle",
        expected_rule_ids=set(),
        forbidden_rule_ids={"WG-SOL-ORACLE-001", "WG-SOL-ORACLE-002"},
        code=CLEAN_ORACLE,
    ),
    AccuracyBenchmarkCase(
        case_id="f_clean_signature_no_expiry_nonce_fp",
        title="Clean: signature path with deadline and nonce update",
        case_class="clean",
        project_name="CleanSignature",
        expected_rule_ids=set(),
        forbidden_rule_ids={"WG-SOL-SIG-003", "WG-SOL-SIG-004"},
        code=CLEAN_SIG,
    ),
]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _rule_map() -> dict[str, dict[str, str]]:
    return {item["id"]: item for item in available_contract_rules()}


def _highest_severity(findings: list[Finding]) -> str | None:
    if not findings:
        return None
    best = max(findings, key=lambda item: SEVERITY_RANK.get(str(item.severity), 0))
    return str(best.severity)


def _severity_meets(actual: str | None, minimum: str | None) -> bool:
    if not minimum:
        return True
    return SEVERITY_RANK.get(str(actual or "info"), 0) >= SEVERITY_RANK.get(minimum, 0)


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
    }


def _run_case(case: AccuracyBenchmarkCase) -> dict[str, Any]:
    response = scan_solidity(case.code, project_name=case.project_name or case.title)
    findings = [f for f in response.findings if getattr(f, "category", "") != "tool_status"]
    detected_rule_ids = {str(f.rule_id) for f in findings if f.rule_id}
    by_rule: dict[str, list[Finding]] = defaultdict(list)
    for f in findings:
        if f.rule_id:
            by_rule[str(f.rule_id)].append(f)

    expected_detected = sorted(case.expected_rule_ids.intersection(detected_rule_ids))
    missed = sorted(case.expected_rule_ids.difference(detected_rule_ids))
    expected_findings = [f for rid in case.expected_rule_ids for f in by_rule.get(rid, [])]
    highest_expected_severity = _highest_severity(expected_findings)
    severity_ok = _severity_meets(highest_expected_severity, case.expected_min_severity)

    forbidden_hits = sorted((case.forbidden_rule_ids or set()).intersection(detected_rule_ids))
    severe_forbidden_hits: list[str] = []
    for rule_id in case.forbidden_high_or_critical_rule_ids or set():
        for finding in by_rule.get(rule_id, []):
            if finding.severity in {"critical", "high"}:
                severe_forbidden_hits.append(rule_id)
                break
    severe_forbidden_hits = sorted(set(severe_forbidden_hits))

    pass_expected = not missed and severity_ok
    pass_clean = not forbidden_hits and not severe_forbidden_hits
    passed = pass_expected and pass_clean

    return {
        "case_id": case.case_id,
        "title": case.title,
        "case_class": case.case_class,
        "notes": case.notes,
        "expected_rule_ids": sorted(case.expected_rule_ids),
        "detected_expected_rule_ids": expected_detected,
        "missed_rule_ids": missed,
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
        "top_findings": [_finding_brief(f) for f in findings[:8]],
        "scan_metadata": response.scan_metadata,
    }


def run_professional_accuracy_benchmark() -> dict[str, Any]:
    cases = [_run_case(case) for case in BENCHMARK_CASES]
    vulnerable_cases = [c for c in cases if c["case_class"] == "vulnerable"]
    clean_cases = [c for c in cases if c["case_class"] == "clean"]
    expected_total = sum(len(c["expected_rule_ids"]) for c in cases)
    expected_detected = sum(len(c["detected_expected_rule_ids"]) for c in cases)
    missed_total = sum(len(c["missed_rule_ids"]) for c in cases)
    false_positive_cases = sum(1 for c in clean_cases if c["forbidden_rule_hits"] or c["forbidden_high_or_critical_hits"])
    severity_fail_cases = sum(1 for c in vulnerable_cases if not c["severity_ok"])
    passed_cases = sum(1 for c in cases if c["passed"])

    recall = round(expected_detected / expected_total, 4) if expected_total else 1.0
    clean_specificity = round((len(clean_cases) - false_positive_cases) / len(clean_cases), 4) if clean_cases else 1.0
    pass_rate = round(passed_cases / len(cases), 4) if cases else 0.0
    accuracy_score = round((recall * 0.50 + clean_specificity * 0.35 + pass_rate * 0.15) * 100, 2)

    noisy_rules = Counter(rule_id for c in clean_cases for rule_id in c["forbidden_rule_hits"] + c["forbidden_high_or_critical_hits"])
    missed_rules = Counter(rule_id for c in cases for rule_id in c["missed_rule_ids"])

    return {
        "ok": missed_total == 0 and false_positive_cases == 0 and severity_fail_cases == 0,
        "phase": "Professional Scanner Phase F",
        "benchmark_id": "web3guard_professional_accuracy_v1",
        "generated_at": _now_iso(),
        "purpose": "Repeatable scanner accuracy loop for benchmark recall, false-positive tuning and severity calibration. Synthetic/local fixtures only; not a certified audit claim.",
        "case_count": len(cases),
        "vulnerable_case_count": len(vulnerable_cases),
        "clean_case_count": len(clean_cases),
        "expected_rule_signals": expected_total,
        "detected_expected_rule_signals": expected_detected,
        "missed_expected_rule_signals": missed_total,
        "false_positive_cases": false_positive_cases,
        "severity_fail_cases": severity_fail_cases,
        "passed_cases": passed_cases,
        "synthetic_recall": recall,
        "clean_specificity": clean_specificity,
        "pass_rate": pass_rate,
        "accuracy_score": accuracy_score,
        "noisy_rules": dict(noisy_rules),
        "missed_rules": dict(missed_rules),
        "quality_gate": _quality_gate(accuracy_score, recall, clean_specificity, false_positive_cases, missed_total),
        "rule_count": len(available_contract_rules()),
        "cases": cases,
        "blocked_claim": "Do not present this benchmark as certified audit accuracy. It is an internal accuracy guardrail and improvement signal.",
    }


def _quality_gate(accuracy_score: float, recall: float, clean_specificity: float, false_positive_cases: int, missed_total: int) -> dict[str, Any]:
    launch_ready = accuracy_score >= 85 and recall >= 0.85 and clean_specificity >= 0.75
    direct_competition_ready = accuracy_score >= 95 and recall >= 0.95 and clean_specificity >= 0.90 and false_positive_cases == 0 and missed_total == 0
    if direct_competition_ready:
        label = "strong_internal_benchmark_ready"
    elif launch_ready:
        label = "professional_beta_ready"
    else:
        label = "needs_tuning"
    return {
        "label": label,
        "professional_beta_ready": launch_ready,
        "direct_competition_claim_allowed": False,
        "direct_competition_engine_progress": direct_competition_ready,
        "reason": "Certification/audit-company parity requires independent validation, human review, legal process and public report history; this gate only measures scanner-engine quality.",
        "required_next_steps": [
            "Run larger real-world vulnerable/clean dataset.",
            "Review every false positive and missed rule.",
            "Add third-party validation before public accuracy claims.",
            "Keep public wording as evidence-first pre-audit readiness unless reviewed by qualified auditors.",
        ],
    }


def _feedback_path() -> Path:
    return Path(settings.professional_accuracy_feedback_file)


def _ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def append_accuracy_feedback(payload: dict[str, Any]) -> dict[str, Any]:
    record = {
        "id": f"AF-{uuid4().hex[:12]}",
        "created_at": _now_iso(),
        "finding_id": str(payload.get("finding_id") or "").strip()[:160],
        "rule_id": str(payload.get("rule_id") or "").strip()[:160],
        "verdict": str(payload.get("verdict") or "needs_evidence").strip(),
        "severity": str(payload.get("severity") or "").strip()[:40] or None,
        "source": str(payload.get("source") or "manual_reviewer").strip()[:160],
        "evidence": str(payload.get("evidence") or "").strip()[:3000],
        "notes": str(payload.get("notes") or "").strip()[:3000],
        "project_id": str(payload.get("project_id") or "").strip()[:160] or None,
        "reviewer": str(payload.get("reviewer") or "").strip()[:160] or None,
        "safe_for_training": bool(payload.get("safe_for_training", False)),
    }
    if record["verdict"] not in {"confirmed", "false_positive", "accepted_risk", "fixed", "missed", "needs_evidence"}:
        record["verdict"] = "needs_evidence"
    path = _feedback_path()
    _ensure_parent(path)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    return record


def list_accuracy_feedback(limit: int = 100) -> list[dict[str, Any]]:
    path = _feedback_path()
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            try:
                rows.append(json.loads(line))
            except Exception:
                continue
    return rows[-max(1, min(limit, 500)):][::-1]


def feedback_summary(limit: int = 500) -> dict[str, Any]:
    rows = list_accuracy_feedback(limit=limit)
    verdict_counts = Counter(str(row.get("verdict")) for row in rows)
    rule_counts = Counter(str(row.get("rule_id") or "unknown") for row in rows)
    false_positive_rules = Counter(str(row.get("rule_id") or "unknown") for row in rows if row.get("verdict") == "false_positive")
    missed_rules = Counter(str(row.get("rule_id") or "unknown") for row in rows if row.get("verdict") == "missed")
    confirmed_rules = Counter(str(row.get("rule_id") or "unknown") for row in rows if row.get("verdict") == "confirmed")
    return {
        "total_feedback": len(rows),
        "verdict_counts": dict(verdict_counts),
        "top_rules_by_feedback": dict(rule_counts.most_common(20)),
        "false_positive_rules": dict(false_positive_rules.most_common(20)),
        "missed_rules": dict(missed_rules.most_common(20)),
        "confirmed_rules": dict(confirmed_rules.most_common(20)),
        "feedback_file": str(_feedback_path()),
        "privacy_rule": "Only store reviewer-approved non-sensitive evidence. Never store private keys, seed phrases or secrets.",
    }


def calibration_report() -> dict[str, Any]:
    benchmark = run_professional_accuracy_benchmark()
    feedback = feedback_summary()
    rule_details = _rule_map()
    rule_actions: dict[str, dict[str, Any]] = {}

    for rule_id, count in benchmark.get("missed_rules", {}).items():
        rule_actions.setdefault(rule_id, _empty_rule_action(rule_id, rule_details)).setdefault("signals", []).append(f"missed_in_benchmark:{count}")
    for rule_id, count in benchmark.get("noisy_rules", {}).items():
        rule_actions.setdefault(rule_id, _empty_rule_action(rule_id, rule_details)).setdefault("signals", []).append(f"false_positive_in_clean_fixture:{count}")
    for rule_id, count in feedback.get("false_positive_rules", {}).items():
        rule_actions.setdefault(rule_id, _empty_rule_action(rule_id, rule_details)).setdefault("signals", []).append(f"manual_false_positive_feedback:{count}")
    for rule_id, count in feedback.get("missed_rules", {}).items():
        rule_actions.setdefault(rule_id, _empty_rule_action(rule_id, rule_details)).setdefault("signals", []).append(f"manual_missed_feedback:{count}")

    for rule_id, action in rule_actions.items():
        signals = action.get("signals", [])
        if any("false_positive" in s for s in signals):
            action["recommended_action"] = "tighten_pattern_or_lower_confidence"
            action["priority"] = "high"
        elif any("missed" in s for s in signals):
            action["recommended_action"] = "expand_detection_or_add_parser_context"
            action["priority"] = "high"
        else:
            action["recommended_action"] = "monitor"
            action["priority"] = "medium"

    return {
        "phase": "Professional Scanner Phase F",
        "generated_at": _now_iso(),
        "benchmark_quality_gate": benchmark.get("quality_gate", {}),
        "accuracy_score": benchmark.get("accuracy_score"),
        "synthetic_recall": benchmark.get("synthetic_recall"),
        "clean_specificity": benchmark.get("clean_specificity"),
        "feedback_summary": feedback,
        "rule_calibration_actions": sorted(rule_actions.values(), key=lambda item: (item.get("priority") != "high", item.get("rule_id", ""))),
        "public_claim_policy": "Use this to improve the scanner internally. Do not claim certified audit equivalence from synthetic/local benchmarks.",
    }


def _empty_rule_action(rule_id: str, rule_details: dict[str, dict[str, str]]) -> dict[str, Any]:
    detail = rule_details.get(rule_id, {})
    return {
        "rule_id": rule_id,
        "name": detail.get("name", "Unknown rule"),
        "category": detail.get("category", "unknown"),
        "signals": [],
        "recommended_action": "monitor",
        "priority": "medium",
    }


def accuracy_readiness_summary() -> dict[str, Any]:
    """Cheap summary for scan payloads without running the full benchmark every scan."""
    feedback = feedback_summary(limit=200)
    return {
        "phase": "Professional Scanner Phase F",
        "status": "active",
        "goal": "Benchmark every critical rule family, track false positives/missed findings, and calibrate severities before stronger market claims.",
        "benchmark_endpoint": "/professional-accuracy/benchmark",
        "calibration_endpoint": "/professional-accuracy/calibration",
        "feedback_endpoint": "/professional-accuracy/feedback",
        "real_world_benchmark_endpoint": "/professional-benchmark/run",
        "phase_g_tuning_endpoint": "/professional-benchmark/tuning-pack",
        "tracked_feedback_count": feedback.get("total_feedback", 0),
        "public_claim_allowed": False,
        "direct_competition_path": [
            "Use Phase G real-world-style benchmark dataset for broader scanner calibration.",
            "Grow benchmark dataset from sanitized fixtures to independently reviewed audited cases.",
            "Record reviewer feedback and retest fixed findings.",
            "Publish proof reports only after approval gates pass.",
            "Use human-verified wording for paid reviewed reports.",
        ],
        "disclaimer": "Accuracy engine improves scanner quality. It is not a certified-audit claim.",
    }


def run_custom_contract_case(code: str, expected_rule_ids: list[str] | None = None, forbidden_rule_ids: list[str] | None = None, project_name: str | None = None) -> dict[str, Any]:
    expected = {rid.strip() for rid in expected_rule_ids or [] if rid.strip()}
    forbidden = {rid.strip() for rid in forbidden_rule_ids or [] if rid.strip()}
    case = AccuracyBenchmarkCase(
        case_id=f"custom_{uuid4().hex[:10]}",
        title="Custom contract benchmark case",
        case_class="regression",
        project_name=project_name or "CustomBenchmark",
        expected_rule_ids=expected,
        forbidden_rule_ids=forbidden,
        code=code,
        notes="User-supplied regression case. Do not store unless separately submitted as feedback.",
    )
    return _run_case(case)
