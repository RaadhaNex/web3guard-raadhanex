from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

PHASE42_VERSION = "web3guard-openzeppelin-pattern-v42.0"

SAFE_STATUSES = [
    "Assessed",
    "Not assessed yet",
    "OpenZeppelin pattern detected",
    "Custom implementation detected",
    "Manual review required",
    "Imported evidence",
]

REQUIRED_DISCLAIMER = (
    "OpenZeppelin Pattern Intelligence compares supplied source/evidence against common secure patterns. "
    "It is not OpenZeppelin certification, not an official OpenZeppelin scanner, and not a certified audit."
)

BLOCKED_CLAIMS = [
    "openzeppelin certified",
    "certified by openzeppelin",
    "audited by openzeppelin",
    "official openzeppelin scanner",
    "openzeppelin partner",
    "openzeppelin-level audit",
    "guaranteed openzeppelin safe",
    "100% secure",
    "finds all bugs",
    "all vulnerabilities found",
]

OPENZEPPELIN_IMPORT_PATTERNS = {
    "ERC20": [r"@openzeppelin/contracts(?:-upgradeable)?/token/ERC20", r"\bERC20Upgradeable\b", r"\bERC20\b"],
    "ERC721": [r"@openzeppelin/contracts(?:-upgradeable)?/token/ERC721", r"\bERC721Upgradeable\b", r"\bERC721\b"],
    "ERC1155": [r"@openzeppelin/contracts(?:-upgradeable)?/token/ERC1155", r"\bERC1155Upgradeable\b", r"\bERC1155\b"],
    "Ownable": [r"@openzeppelin/contracts(?:-upgradeable)?/access/Ownable", r"\bOwnableUpgradeable\b", r"\bOwnable\b"],
    "Ownable2Step": [r"@openzeppelin/contracts(?:-upgradeable)?/access/Ownable2Step", r"\bOwnable2StepUpgradeable\b", r"\bOwnable2Step\b"],
    "AccessControl": [r"@openzeppelin/contracts(?:-upgradeable)?/access/AccessControl", r"\bAccessControlUpgradeable\b", r"\bAccessControl\b"],
    "ReentrancyGuard": [r"@openzeppelin/contracts(?:-upgradeable)?/utils/ReentrancyGuard", r"\bReentrancyGuardUpgradeable\b", r"\bReentrancyGuard\b", r"\bnonReentrant\b"],
    "Pausable": [r"@openzeppelin/contracts(?:-upgradeable)?/utils/Pausable", r"\bPausableUpgradeable\b", r"\bPausable\b", r"\bwhenNotPaused\b"],
    "SafeERC20": [r"@openzeppelin/contracts(?:-upgradeable)?/token/ERC20/utils/SafeERC20", r"using\s+SafeERC20", r"\bSafeERC20\b"],
    "UUPSUpgradeable": [r"@openzeppelin/contracts-upgradeable/proxy/utils/UUPSUpgradeable", r"\bUUPSUpgradeable\b"],
    "Initializable": [r"@openzeppelin/contracts-upgradeable/proxy/utils/Initializable", r"\binitializer\b", r"\breinitializer\b", r"\b_disableInitializers\b"],
    "TimelockController": [r"@openzeppelin/contracts(?:-upgradeable)?/governance/TimelockController", r"\bTimelockController\b"],
}

RULE_CATALOG: list[dict[str, Any]] = [
    {
        "id": "OZ-STD-001",
        "title": "Use standard OpenZeppelin token implementation when possible",
        "family": "token_standard",
        "severity": "medium",
        "confidence": "medium",
        "cwe_ids": ["CWE-710"],
        "why_it_matters": "Custom token logic is a common source of transfer, approval, mint, burn, and accounting mistakes.",
        "future_risk": "As exchanges, wallets, bridges, or DeFi integrations grow, non-standard behavior can create stuck funds, broken integrations, or exploitable accounting paths.",
        "fix": "Prefer OpenZeppelin ERC20/ERC721/ERC1155 base contracts or document and test every intentional deviation from the standard.",
        "verify": ["Compare custom transfer/approval/mint/burn behavior against OpenZeppelin references", "Run Slither and unit tests", "Add integration tests for wallets/exchanges if relevant"],
    },
    {
        "id": "OZ-ACL-001",
        "title": "Protect privileged functions with Ownable, AccessControl, multisig, or timelock controls",
        "family": "access_control",
        "severity": "high",
        "confidence": "medium",
        "cwe_ids": ["CWE-284", "CWE-862", "CWE-863"],
        "why_it_matters": "Unprotected admin functions can allow unauthorized minting, pausing, treasury movement, upgrades, or configuration changes.",
        "future_risk": "One exposed privileged path can become critical after liquidity, treasury balance, or user count grows.",
        "fix": "Add onlyOwner, role-based AccessControl, multisig ownership, and timelock for high-impact operations.",
        "verify": ["Add tests that unauthorized callers revert", "Review every mint/burn/pause/upgrade/withdraw/config function", "Confirm admin is multisig/timelock for production"],
    },
    {
        "id": "OZ-REENT-001",
        "title": "Use ReentrancyGuard or checks-effects-interactions around external calls",
        "family": "reentrancy",
        "severity": "critical",
        "confidence": "medium",
        "cwe_ids": ["CWE-841", "CWE-362"],
        "why_it_matters": "External calls can allow attacker-controlled contracts to re-enter before state is finalized.",
        "future_risk": "This risk becomes severe when the contract holds funds or is integrated into vault, staking, reward, lending, or bridge flows.",
        "fix": "Use ReentrancyGuard/nonReentrant, update state before external calls, and add malicious receiver tests.",
        "verify": ["Run Slither reentrancy detectors", "Add Foundry test with attacker contract", "Review every call/transfer/send path"],
    },
    {
        "id": "OZ-UPG-001",
        "title": "Protect upgradeable contracts with initializer and upgrade authorization patterns",
        "family": "upgradeability",
        "severity": "high",
        "confidence": "medium",
        "cwe_ids": ["CWE-665", "CWE-284"],
        "why_it_matters": "Incorrect initializer or upgrade authorization can leave contracts takeoverable or permanently misconfigured.",
        "future_risk": "A proxy or implementation takeover can compromise the full protocol after launch.",
        "fix": "Use Initializable/UUPSUpgradeable patterns correctly, disable implementation initializers, and guard _authorizeUpgrade.",
        "verify": ["Run OpenZeppelin Upgrades validation if available", "Test initializer cannot be called twice", "Confirm _authorizeUpgrade is access-controlled"],
    },
    {
        "id": "OZ-PAUSE-001",
        "title": "Add emergency pause controls for high-impact flows",
        "family": "emergency_controls",
        "severity": "medium",
        "confidence": "medium",
        "cwe_ids": ["CWE-693"],
        "why_it_matters": "Without a safe pause path, founders may be unable to stop damage during an incident.",
        "future_risk": "Incident response becomes slower as TVL/users grow, increasing fund loss and reputational damage.",
        "fix": "Use Pausable/whenNotPaused for high-risk external user flows and document when admins can pause.",
        "verify": ["Test pause/unpause behavior", "Confirm only authorized pause roles", "Document pause policy in the public report"],
    },
    {
        "id": "OZ-SAFEERC20-001",
        "title": "Use SafeERC20 wrappers for token transfers",
        "family": "token_integration",
        "severity": "medium",
        "confidence": "medium",
        "cwe_ids": ["CWE-252", "CWE-754"],
        "why_it_matters": "Some ERC20 tokens do not return standard boolean values, so raw transfer calls can fail silently or behave unexpectedly.",
        "future_risk": "Token integration bugs can create stuck funds, failed withdrawals, or accounting drift after more tokens are supported.",
        "fix": "Use SafeERC20.safeTransfer/safeTransferFrom/safeApprove patterns where token interactions occur.",
        "verify": ["Search for raw IERC20.transfer/transferFrom", "Add tests with non-standard ERC20 mocks", "Run Slither unchecked-transfer detectors"],
    },
]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _combined_source(payload: dict[str, Any]) -> str:
    pieces: list[str] = []
    for key in ("contract_source", "readme", "notes"):
        value = payload.get(key)
        if isinstance(value, str):
            pieces.append(value)
    for key in ("imports", "file_names"):
        value = payload.get(key) or []
        if isinstance(value, list):
            pieces.extend(str(item) for item in value)
    files = payload.get("files") or []
    if isinstance(files, list):
        for item in files:
            if isinstance(item, dict):
                pieces.append(str(item.get("path") or ""))
                pieces.append(str(item.get("content") or ""))
            else:
                pieces.append(str(item))
    return "\n".join(pieces)


def _has(pattern: str, source: str) -> bool:
    return re.search(pattern, source, flags=re.IGNORECASE | re.MULTILINE) is not None


def _detect_openzeppelin_usage(source: str) -> dict[str, bool]:
    return {
        name: any(_has(pattern, source) for pattern in patterns)
        for name, patterns in OPENZEPPELIN_IMPORT_PATTERNS.items()
    }


def _rule(rule_id: str) -> dict[str, Any]:
    for item in RULE_CATALOG:
        if item["id"] == rule_id:
            return item
    raise KeyError(rule_id)


def _finding(rule_id: str, evidence: str, status: str = "Manual review required", confidence: str | None = None) -> dict[str, Any]:
    rule = _rule(rule_id)
    severity = rule["severity"]
    priority = "P0" if severity == "critical" else "P1" if severity == "high" else "P2" if severity == "medium" else "P3"
    return {
        "id": f"WG-{rule_id}",
        "rule_id": rule_id,
        "title": rule["title"],
        "family": rule["family"],
        "status": status,
        "severity": severity,
        "priority": priority,
        "confidence": confidence or rule["confidence"],
        "cwe_ids": rule["cwe_ids"],
        "evidence": evidence,
        "impact": rule["why_it_matters"],
        "future_risk": rule["future_risk"],
        "fix_plan": {
            "summary": rule["fix"],
            "verify_steps": rule["verify"],
        },
        "human_review_required": True,
        "limitation": "Pattern-based source/evidence analysis. Confirm with Slither, tests, and manual audit review before launch.",
    }


def _missing_modules(oz: dict[str, bool]) -> list[str]:
    return [name for name, used in oz.items() if not used]


def openzeppelin_pattern_status() -> dict[str, Any]:
    return {
        "ok": True,
        "version": PHASE42_VERSION,
        "purpose": "Compare supplied Solidity/source evidence against OpenZeppelin-style secure contract patterns without claiming OpenZeppelin certification.",
        "safe_status_labels": SAFE_STATUSES,
        "supported_pattern_families": [item["family"] for item in RULE_CATALOG],
        "blocked_claims": BLOCKED_CLAIMS,
        "required_disclaimer": REQUIRED_DISCLAIMER,
        "not_supported": [
            "official OpenZeppelin certification",
            "OpenZeppelin partnership claim",
            "all-bug guarantee",
            "replacement for human audit",
            "destructive exploit execution",
        ],
    }


def openzeppelin_rule_catalog() -> dict[str, Any]:
    return {
        "ok": True,
        "version": PHASE42_VERSION,
        "rules": RULE_CATALOG,
        "pattern_modules": sorted(OPENZEPPELIN_IMPORT_PATTERNS.keys()),
        "safe_wording": "OpenZeppelin Pattern Intelligence checks whether supplied contracts follow common OpenZeppelin-style secure patterns. It is not an official OpenZeppelin audit or certification.",
    }


def analyze_openzeppelin_patterns(payload: dict[str, Any]) -> dict[str, Any]:
    source = _combined_source(payload)
    project_name = str(payload.get("project_name") or "Untitled contract review")
    real_only_ack = bool(payload.get("real_only_acknowledged", True))
    if not real_only_ack:
        return {
            "ok": False,
            "status": "Manual review required",
            "message": "Real-only acknowledgement is required. Web3Guard will not create fake OpenZeppelin certification or fake audit claims.",
        }

    oz = _detect_openzeppelin_usage(source)
    lowered = source.lower()
    findings: list[dict[str, Any]] = []

    has_token_signals = any(word in lowered for word in ["erc20", "erc721", "erc1155", "transfer(", "approve(", "mint(", "burn(", "token"])
    uses_any_standard_token = oz["ERC20"] or oz["ERC721"] or oz["ERC1155"]
    has_custom_contract = "contract " in lowered

    if has_token_signals and has_custom_contract and not uses_any_standard_token:
        findings.append(_finding("OZ-STD-001", "Token-like custom contract signals found, but no OpenZeppelin ERC20/ERC721/ERC1155 pattern was detected.", status="Custom implementation detected"))

    privileged_signals = any(word in lowered for word in ["mint(", "burn(", "pause(", "unpause(", "upgrade", "withdraw", "setfee", "setowner", "treasury", "admin"])
    guarded = any(token in lowered for token in ["onlyowner", "onlyrole", "accesscontrol", "owner()", "msg.sender == owner", "hasrole"])
    if privileged_signals and not guarded:
        findings.append(_finding("OZ-ACL-001", "Privileged operation signals were found without clear Ownable/AccessControl/role guard evidence.", status="Manual review required"))
    elif privileged_signals and oz["Ownable"] and not oz["Ownable2Step"]:
        advisory = _finding("OZ-ACL-001", "Ownable is detected. Consider Ownable2Step/multisig/timelock for production admin transfer safety.", status="OpenZeppelin pattern detected", confidence="medium")
        advisory["severity"] = "medium"
        advisory["priority"] = "P2"
        findings.append(advisory)

    external_call_signals = any(word in lowered for word in [".call{", ".call(", ".send(", ".transfer(", "call.value"])
    if external_call_signals and not oz["ReentrancyGuard"]:
        findings.append(_finding("OZ-REENT-001", "External call/transfer signals found without ReentrancyGuard/nonReentrant evidence.", status="Manual review required"))

    upgrade_signals = any(word in lowered for word in ["uups", "proxy", "upgradeable", "_authorizeupgrade", "initializer", "reinitializer"])
    if upgrade_signals and not oz["Initializable"]:
        findings.append(_finding("OZ-UPG-001", "Upgradeable/proxy signals found without clear Initializable/initializer evidence.", status="Manual review required"))
    if "_authorizeupgrade" in lowered and not guarded:
        findings.append(_finding("OZ-UPG-001", "_authorizeUpgrade signal found without clear access-control guard evidence.", status="Manual review required"))

    high_impact_flows = any(word in lowered for word in ["withdraw", "deposit", "mint(", "burn(", "transferfrom", "treasury", "vault", "staking"])
    if high_impact_flows and not oz["Pausable"]:
        findings.append(_finding("OZ-PAUSE-001", "High-impact token/fund flow signals found without Pausable/whenNotPaused evidence.", status="Not assessed yet"))

    erc20_interaction = any(word in lowered for word in ["ierc20", ".transfer(", ".transferfrom(", ".approve("])
    if erc20_interaction and not oz["SafeERC20"]:
        findings.append(_finding("OZ-SAFEERC20-001", "ERC20 transfer/approval interaction signals found without SafeERC20 evidence.", status="Manual review required"))

    if not source.strip():
        findings.append({
            "id": "WG-OZ-EVIDENCE-000",
            "rule_id": "OZ-EVIDENCE-000",
            "title": "No Solidity/source evidence supplied",
            "family": "evidence",
            "status": "Not assessed yet",
            "severity": "info",
            "priority": "P3",
            "confidence": "high",
            "cwe_ids": [],
            "evidence": "No contract source/imports/files were supplied for OpenZeppelin pattern analysis.",
            "impact": "Web3Guard cannot compare patterns without source or imported evidence.",
            "future_risk": "A blank scan can create false confidence if presented as a pass.",
            "fix_plan": {"summary": "Upload Solidity source, import list, or verified explorer source before running this module.", "verify_steps": ["Supply contract source", "Run Slither", "Run this pattern check again"]},
            "human_review_required": True,
            "limitation": "No evidence means no assessment.",
        })

    severity_breakdown: dict[str, int] = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
    for item in findings:
        severity = str(item.get("severity", "info")).lower()
        severity_breakdown[severity] = severity_breakdown.get(severity, 0) + 1

    detected_modules = [name for name, used in oz.items() if used]
    coverage_notes = [
        "Pattern detection is based on supplied source/import evidence, not official OpenZeppelin validation.",
        "Custom business logic, tokenomics, oracle assumptions, and economic attacks still need manual audit.",
        "Use Slither/Foundry/Echidna/Mythril plus expert review before public launch.",
    ]

    return {
        "ok": True,
        "version": PHASE42_VERSION,
        "analysis_id": f"ozpat_{uuid4().hex[:12]}",
        "project_name": project_name,
        "generated_at": _now_iso(),
        "openzeppelin_modules_detected": detected_modules,
        "openzeppelin_modules_missing_or_not_detected": _missing_modules(oz),
        "pattern_summary": {
            "uses_openzeppelin_contracts": bool(detected_modules),
            "uses_token_standard_pattern": uses_any_standard_token,
            "uses_access_control_pattern": oz["Ownable"] or oz["AccessControl"],
            "uses_reentrancy_guard_pattern": oz["ReentrancyGuard"],
            "uses_upgradeability_pattern": oz["UUPSUpgradeable"] or oz["Initializable"],
            "uses_emergency_pause_pattern": oz["Pausable"],
            "uses_safe_erc20_pattern": oz["SafeERC20"],
        },
        "findings_count": len(findings),
        "severity_breakdown": severity_breakdown,
        "findings": findings,
        "coverage_notes": coverage_notes,
        "recommended_next_action": "Treat these as pre-audit pattern checks. Confirm with real scanner output, unit/fuzz tests, and human review before launch.",
        "safe_report_wording": "OpenZeppelin Pattern Intelligence reviewed supplied source evidence for common secure-contract patterns. This is not OpenZeppelin certification and not a certified audit.",
        "required_disclaimer": REQUIRED_DISCLAIMER,
    }


def openzeppelin_claim_check(text: str) -> dict[str, Any]:
    lowered = text.lower()
    violations = [claim for claim in BLOCKED_CLAIMS if claim in lowered]
    return {
        "ok": len(violations) == 0,
        "violations": violations,
        "allowed_rewrite": (
            "Web3Guard checks supplied contracts against common OpenZeppelin-style secure patterns and reports evidence, gaps, and fix guidance. "
            "It is not an official OpenZeppelin scanner, not OpenZeppelin-certified, and not a certified audit."
        ),
        "required_disclaimer": REQUIRED_DISCLAIMER,
    }
