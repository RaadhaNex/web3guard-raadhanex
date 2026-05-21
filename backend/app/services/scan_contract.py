import re
from datetime import datetime, timezone

from app.models.schemas import Finding, ModuleScore, ScanResponse
from app.services.scoring import priority_actions, risk_label, score_findings, severity_breakdown
from app.services.finding_normalizer import audit_grade_summary, prepare_professional_findings
from app.services.solidity_utils import (
    all_match_lines,
    contains_state_write,
    emits_event,
    extract_functions,
    external_call_line_offsets,
    first_match_line,
    function_at_line,
    has_access_control,
    is_publicly_reachable,
    line_text,
    lines,
    sha12,
    sensitive_function_name,
)

ENGINE_VERSION = "web3guard-solidity-rule-engine-v2.1-phase-b"

SECURITY_REFERENCES = {
    "reentrancy": ["SWC-107", "Checks-Effects-Interactions", "OpenZeppelin ReentrancyGuard"],
    "access_control": ["OWASP SC01 Access Control", "OpenZeppelin AccessControl/Ownable"],
    "tx_origin": ["SWC-115 tx.origin Authentication"],
    "selfdestruct": ["SWC-106 Unprotected SELFDESTRUCT", "EIP-6780 behavior note"],
    "delegatecall": ["SWC-112 Delegatecall to Untrusted Callee"],
    "randomness": ["SWC-120 Weak Sources of Randomness"],
    "low_level_call": ["SWC-104 Unchecked Call Return Value"],
    "upgradeability": ["UUPS/Transparent proxy review required"],
    "centralization": ["Admin key / governance risk disclosure"],
    "gas": ["Unbounded loop / gas griefing launch-readiness check"],
}


def _fingerprint(rule_id: str, line: int | None, evidence: str | None) -> str:
    return sha12(f"{rule_id}:{line}:{evidence or ''}")


def _finding(
    idx: int,
    *,
    severity: str,
    title: str,
    description: str,
    line: int | None,
    code: str | None,
    business: str,
    dev: str,
    fix: str,
    confidence: str = "medium",
    category: str = "general",
    rule_id: str | None = None,
    fn: str | None = None,
    references: list[str] | None = None,
) -> Finding:
    return Finding(
        id=f"contract-{idx:03d}",
        module="contract",
        severity=severity,  # type: ignore[arg-type]
        title=title,
        description=description,
        affected_line=line,
        affected_function=fn,
        affected_code=code,
        evidence=code or description[:420],
        impact=business,
        fix=fix,
        source_tools=["web3guard_local_rules"],
        repro_steps=[f"Review Solidity line {line} and confirm the rule evidence." if line else "Review the submitted Solidity source and confirm the rule evidence."],
        verification_status="rule_detected_needs_triage",
        confidence=confidence,  # type: ignore[arg-type]
        source="Web3Guard Solidity Rule Engine v2",
        category=category,
        rule_id=rule_id,
        fingerprint=_fingerprint(rule_id or title, line, code),
        business_impact=business,
        developer_explanation=dev,
        recommendation=fix,
        references=references or SECURITY_REFERENCES.get(category, []),
        paid_review_recommended=severity in {"critical", "high"},
    )


def _add_unique(findings: list[Finding], finding: Finding) -> None:
    seen = {(item.rule_id, item.affected_line, item.affected_function) for item in findings}
    key = (finding.rule_id, finding.affected_line, finding.affected_function)
    if key not in seen:
        findings.append(finding)


def _pragma_checks(code: str, findings: list[Finding], start_idx: int) -> int:
    idx = start_idx
    pragma_line, pragma_match = first_match_line(code, r"pragma\s+solidity\s+([^;]+);")
    if "SPDX-License-Identifier" not in code:
        _add_unique(findings, _finding(
            idx,
            severity="low",
            title="Missing SPDX License Identifier",
            description="The Solidity file does not declare an SPDX license identifier.",
            line=None,
            code=None,
            business="Auditors, exchanges, and investors may treat incomplete contract metadata as a readiness issue.",
            dev="SPDX license identifiers help verification and dependency/compliance tracking.",
            fix="Add an SPDX line at the top, for example: // SPDX-License-Identifier: MIT",
            confidence="high",
            category="metadata",
            rule_id="WG-SOL-META-001",
            references=["Solidity SPDX license identifier"],
        ))
        idx += 1

    if not pragma_match:
        _add_unique(findings, _finding(
            idx,
            severity="medium",
            title="Missing Solidity Pragma",
            description="The compiler version is not clearly declared.",
            line=None,
            code=None,
            business="Build reproducibility becomes weaker and launch review becomes harder.",
            dev="Solidity files should declare the intended compiler range or exact version.",
            fix="Pin a tested compiler version, for example: pragma solidity ^0.8.20; or an exact version for reproducible builds.",
            confidence="high",
            category="metadata",
            rule_id="WG-SOL-META-002",
        ))
        return idx + 1

    pragma_value = pragma_match.group(1).strip()
    if any(token in pragma_value for token in ["^", ">", "<", "*"]):
        _add_unique(findings, _finding(
            idx,
            severity="low",
            title="Floating Compiler Version",
            description=f"The pragma uses a flexible compiler range: {pragma_value}.",
            line=pragma_line,
            code=line_text(code, pragma_line),
            business="Different compiler versions may produce different behavior or warnings during deployment.",
            dev="Floating pragmas are common in libraries but launch contracts should be tested against a specific compiler version.",
            fix="For final deployment, document the exact compiler version used and verify contract source with that version.",
            confidence="medium",
            category="metadata",
            rule_id="WG-SOL-META-003",
        ))
        idx += 1

    version_match = re.search(r"(\d+)\.(\d+)\.(\d+)", pragma_value)
    if version_match:
        major, minor, _patch = map(int, version_match.groups())
        if major == 0 and minor < 8:
            _add_unique(findings, _finding(
                idx,
                severity="high",
                title="Old Solidity Compiler Family",
                description=f"The pragma appears to allow Solidity {version_match.group(0)}, which is before Solidity 0.8.x overflow checks.",
                line=pragma_line,
                code=line_text(code, pragma_line),
                business="Older compiler families can increase arithmetic and tooling risk for launches.",
                dev="Solidity 0.8.x includes checked arithmetic by default and newer security/tooling support.",
                fix="Upgrade to a current Solidity 0.8.x compiler after running tests and migration review.",
                confidence="high",
                category="metadata",
                rule_id="WG-SOL-META-004",
            ))
            idx += 1
    return idx


def _global_pattern_checks(code: str, findings: list[Finding], start_idx: int) -> int:
    idx = start_idx
    global_rules = [
        (r"\btx\.origin\b", "high", "tx.origin Authorization Risk", "tx.origin is used in the contract.", "A phishing-style flow can trick a privileged wallet into authorizing an unintended action.", "tx.origin checks rely on the original EOA instead of the immediate caller and can be unsafe for authorization.", "Use msg.sender or _msgSender() with role-based access control instead of tx.origin.", "high", "tx_origin", "WG-SOL-AUTH-001"),
        (r"\bselfdestruct\s*\(", "critical", "Selfdestruct Usage", "selfdestruct is present in the contract.", "A compromised or mistaken admin flow can destroy functionality, break integrations, or cause major trust loss.", "Destructive lifecycle logic requires strict manual review and is usually unnecessary for modern launch contracts.", "Remove selfdestruct unless there is a reviewed, documented shutdown process with multisig/timelock controls.", "high", "selfdestruct", "WG-SOL-LIFE-001"),
        (r"\.delegatecall\s*\(", "high", "Delegatecall Usage", "delegatecall executes code in the storage context of the caller.", "Unsafe delegatecall can lead to storage corruption, fund loss, or full takeover.", "delegatecall is normally only acceptable inside carefully reviewed proxy/plugin patterns.", "Use audited proxy patterns and restrict implementation/plugin targets. Manual review is recommended.", "high", "delegatecall", "WG-SOL-CALL-001"),
        (r"block\.timestamp|blockhash\s*\(|block\.prevrandao", "medium", "Weak Randomness / Time Dependency", "Block values are used in security-sensitive logic or randomness-like code.", "NFT reveals, games, lotteries, or reward distribution can be manipulated or predicted.", "Block values are not secure random sources and can be influenced within limits.", "Use VRF, commit-reveal, or a reviewed randomness design for value-bearing outcomes.", "medium", "randomness", "WG-SOL-RAND-001"),
        (r"\.transfer\s*\(|\.send\s*\(", "low", "transfer/send Compatibility Warning", "transfer/send is used for ETH movement.", "Withdrawals can fail due to gas stipend changes or receiving contract behavior.", "transfer/send forward limited gas and may break composability.", "Prefer call with success handling, pull-payment pattern, and reentrancy protection.", "medium", "low_level_call", "WG-SOL-CALL-002"),
        (r"abi\.encodePacked\s*\(", "info", "abi.encodePacked Review Needed", "abi.encodePacked is used.", "Packed encoding can create collision risks when dynamic values are hashed for signatures or IDs.", "This is not always unsafe, but it needs context review when used with multiple dynamic values.", "Use abi.encode for typed structured data or ensure collision-safe encoding.", "low", "encoding", "WG-SOL-ENC-001"),
        (r"\bunchecked\s*\{", "info", "Unchecked Arithmetic Block", "An unchecked arithmetic block is present.", "Unchecked arithmetic can hide over/underflow assumptions if not documented.", "Unchecked blocks are sometimes gas optimizations but should be justified and tested.", "Add comments/tests proving the unchecked math is bounded and safe.", "medium", "arithmetic", "WG-SOL-MATH-001"),
    ]

    for pattern, severity, title, desc, business, dev, fix, confidence, category, rule_id in global_rules:
        matches = all_match_lines(code, pattern)
        for line, _match in matches[:5]:
            fn = function_at_line(extract_functions(code), line)
            _add_unique(findings, _finding(
                idx,
                severity=severity,
                title=title,
                description=desc,
                line=line,
                code=line_text(code, line),
                business=business,
                dev=dev,
                fix=fix,
                confidence=confidence,
                category=category,
                rule_id=rule_id,
                fn=fn.name if fn else None,
            ))
            idx += 1
    return idx


def _access_control_checks(code: str, findings: list[Finding], start_idx: int) -> int:
    idx = start_idx
    for fn in extract_functions(code):
        if not is_publicly_reachable(fn):
            continue
        if not sensitive_function_name(fn.name):
            continue
        if has_access_control(fn):
            continue
        severity = "critical" if re.search(r"mint|upgrade|withdraw|sweep|rescue|grant|revoke|initialize", fn.name, flags=re.IGNORECASE) else "high"
        _add_unique(findings, _finding(
            idx,
            severity=severity,
            title=f"Sensitive Function May Lack Access Control: {fn.name}",
            description=f"The public/external function `{fn.name}` looks sensitive but no obvious access control was detected.",
            line=fn.start_line,
            code=fn.signature,
            business="A public sensitive function can allow unauthorized minting, fund movement, admin changes, or project takeover.",
            dev="The scanner looked for common modifiers and require checks such as onlyOwner, onlyRole, msg.sender owner/admin checks, or hasRole.",
            fix="Add explicit role-based access control, tests for unauthorized callers, and events for sensitive state changes.",
            confidence="medium",
            category="access_control",
            rule_id="WG-SOL-AUTH-002",
            fn=fn.name,
        ))
        idx += 1
    return idx


def _external_call_checks(code: str, findings: list[Finding], start_idx: int) -> int:
    idx = start_idx
    for fn in extract_functions(code):
        call_offsets = external_call_line_offsets(fn)
        if not call_offsets:
            continue
        fn_lines = fn.body.splitlines()
        for offset in call_offsets[:3]:
            actual_line = fn.start_line + offset
            call_line = fn_lines[offset].strip() if offset < len(fn_lines) else line_text(code, actual_line)
            has_non_reentrant = "nonReentrant" in fn.signature or "nonReentrant" in fn.body
            after_call = "\n".join(fn_lines[offset + 1:])
            before_call = "\n".join(fn_lines[:offset])
            success_checked_nearby = bool(re.search(r"(bool\s+success|success\s*=|require\s*\(\s*success|if\s*\(\s*!success)", fn.body, re.IGNORECASE))

            if ".call" in call_line and not success_checked_nearby:
                _add_unique(findings, _finding(
                    idx,
                    severity="medium",
                    title="Unchecked Low-Level Call Result",
                    description="A low-level call appears without clear success handling.",
                    line=actual_line,
                    code=call_line,
                    business="Failed transfers or external calls can silently break withdrawals, claims, or accounting.",
                    dev="Low-level calls return (success, data). Ignoring success can hide failures.",
                    fix="Capture the success boolean and revert or handle failure explicitly: (bool success,) = to.call{value: amount}(\"\"); require(success, \"ETH transfer failed\");",
                    confidence="medium",
                    category="low_level_call",
                    rule_id="WG-SOL-CALL-003",
                    fn=fn.name,
                ))
                idx += 1

            if contains_state_write(after_call) and not has_non_reentrant:
                _add_unique(findings, _finding(
                    idx,
                    severity="high",
                    title="External Call Before State Update",
                    description="The function appears to make an external call before later state updates.",
                    line=actual_line,
                    code=call_line,
                    business="This can create reentrancy-style fund loss or inconsistent accounting risk.",
                    dev="Follow Checks-Effects-Interactions: validate first, update internal state, then call external addresses.",
                    fix="Move state updates before the external call and add ReentrancyGuard/nonReentrant where value transfer or callbacks are possible.",
                    confidence="medium",
                    category="reentrancy",
                    rule_id="WG-SOL-REENT-001",
                    fn=fn.name,
                ))
                idx += 1

            if not has_non_reentrant and re.search(r"\.call\s*(\{|\()|\.send\s*\(|\.transfer\s*\(", call_line):
                if re.search(r"withdraw|claim|redeem|swap|unstake|refund", fn.name, re.IGNORECASE) or contains_state_write(before_call + after_call):
                    _add_unique(findings, _finding(
                        idx,
                        severity="medium",
                        title="Value Transfer Function Without Reentrancy Guard",
                        description="A value-transfer style function does not show an obvious nonReentrant guard.",
                        line=fn.start_line,
                        code=fn.signature,
                        business="Withdrawal and claim flows are common targets for reentrancy and accounting abuse.",
                        dev="This is a heuristic warning. Some functions are safe without a guard if state is updated before calls and external calls are controlled.",
                        fix="Use Checks-Effects-Interactions and consider OpenZeppelin ReentrancyGuard for withdrawal/claim flows.",
                        confidence="low",
                        category="reentrancy",
                        rule_id="WG-SOL-REENT-002",
                        fn=fn.name,
                    ))
                    idx += 1
    return idx


def _centralization_and_admin_checks(code: str, findings: list[Finding], start_idx: int) -> int:
    idx = start_idx
    if re.search(r"\bOwnable\b|\bonlyOwner\b|\bowner\s*=\s*msg\.sender|owner\s*=\s*_msgSender", code, re.IGNORECASE):
        has_multisig_hint = bool(re.search(r"multisig|GnosisSafe|Safe\b|timelock|TimeLock", code, re.IGNORECASE))
        _add_unique(findings, _finding(
            idx,
            severity="info" if has_multisig_hint else "low",
            title="Owner/Admin Centralization Disclosure Needed",
            description="Owner/admin control is detected. This is common but should be disclosed and protected.",
            line=first_match_line(code, r"\bOwnable\b|\bonlyOwner\b|owner\s*=")[0],
            code=line_text(code, first_match_line(code, r"\bOwnable\b|\bonlyOwner\b|owner\s*=")[0]),
            business="Users, investors, and exchanges often ask who can mint, pause, upgrade, or move treasury funds.",
            dev="Admin roles should be explicit, minimized, and covered by tests and operational controls.",
            fix="Use multisig for privileged roles, add timelock for critical changes where practical, and disclose owner powers in docs.",
            confidence="medium",
            category="centralization",
            rule_id="WG-SOL-ADMIN-001",
        ))
        idx += 1

    hardcoded_matches = all_match_lines(code, r"address\s+(public\s+|private\s+|internal\s+)?[A-Za-z_][A-Za-z0-9_]*\s*=\s*0x[a-fA-F0-9]{40}")
    for line, _match in hardcoded_matches[:5]:
        _add_unique(findings, _finding(
            idx,
            severity="medium",
            title="Hardcoded Privileged Address Review",
            description="A hardcoded address was detected in contract state initialization.",
            line=line,
            code=line_text(code, line),
            business="Hardcoded privileged wallets can make migrations, ownership transfer, or incident response harder.",
            dev="Hardcoded addresses are sometimes valid for treasury/oracle/router references, but they need chain-specific verification.",
            fix="Document the address purpose, verify it per chain, add zero-address checks, and avoid hardcoding deployer/private wallets.",
            confidence="medium",
            category="centralization",
            rule_id="WG-SOL-ADMIN-002",
        ))
        idx += 1

    if re.search(r"\bupgradeTo\b|\bUUPSUpgradeable\b|\bTransparentUpgradeableProxy\b|\bBeaconProxy\b|\bimplementation\b", code, re.IGNORECASE):
        _add_unique(findings, _finding(
            idx,
            severity="high",
            title="Upgradeable Proxy / Implementation Risk",
            description="Upgradeability-related code or naming was detected.",
            line=first_match_line(code, r"upgradeTo|UUPSUpgradeable|TransparentUpgradeableProxy|BeaconProxy|implementation")[0],
            code=line_text(code, first_match_line(code, r"upgradeTo|UUPSUpgradeable|TransparentUpgradeableProxy|BeaconProxy|implementation")[0]),
            business="Upgradeable contracts can be fixed, but also create admin takeover and storage collision risk.",
            dev="Upgrade authorization, storage layout, initializer safety, and admin controls require manual review.",
            fix="Use audited proxy patterns, protect upgrade functions with multisig/timelock, and run storage layout diff before every upgrade.",
            confidence="medium",
            category="upgradeability",
            rule_id="WG-SOL-UPGRADE-001",
        ))
        idx += 1

    return idx


def _event_and_payable_checks(code: str, findings: list[Finding], start_idx: int) -> int:
    idx = start_idx
    has_any_event = "event " in code
    for fn in extract_functions(code):
        if not is_publicly_reachable(fn):
            continue
        if sensitive_function_name(fn.name) and not emits_event(fn):
            _add_unique(findings, _finding(
                idx,
                severity="low",
                title=f"Sensitive Function Has No Event: {fn.name}",
                description="A sensitive function does not appear to emit an event.",
                line=fn.start_line,
                code=fn.signature,
                business="Monitoring tools, users, and incident responders may miss important admin or fund movement actions.",
                dev="Events are essential for transparent launch operations and off-chain monitoring.",
                fix="Emit structured events for mint/burn, pause/unpause, role changes, upgrades, treasury updates, and withdrawals.",
                confidence="medium",
                category="observability",
                rule_id="WG-SOL-EVENT-001",
                fn=fn.name,
                references=["Solidity events", "Operational monitoring readiness"],
            ))
            idx += 1

        if "payable" in fn.signature and not emits_event(fn):
            _add_unique(findings, _finding(
                idx,
                severity="low",
                title=f"Payable Function Without Event: {fn.name}",
                description="A payable public/external function does not appear to emit an event.",
                line=fn.start_line,
                code=fn.signature,
                business="Funds can enter the contract without clear off-chain monitoring signals.",
                dev="Payable functions should emit deposit/purchase/mint events with useful indexed fields.",
                fix="Emit an event containing sender, value, important IDs, and resulting state where applicable.",
                confidence="medium",
                category="observability",
                rule_id="WG-SOL-EVENT-002",
                fn=fn.name,
            ))
            idx += 1

    if not has_any_event:
        _add_unique(findings, _finding(
            idx,
            severity="low",
            title="No Events Declared",
            description="No event declarations were detected in the contract.",
            line=None,
            code=None,
            business="Launch transparency and monitoring become weaker without events.",
            dev="Events are the primary low-cost way to support dashboards, monitoring, and incident response.",
            fix="Add events for sensitive state changes and value movement.",
            confidence="medium",
            category="observability",
            rule_id="WG-SOL-EVENT-003",
        ))
        idx += 1
    return idx


def _gas_and_launch_readiness_checks(code: str, findings: list[Finding], start_idx: int) -> int:
    idx = start_idx
    for fn in extract_functions(code):
        if not is_publicly_reachable(fn):
            continue
        if re.search(r"for\s*\([^;]+;[^;]+\.length\s*;|while\s*\(", fn.body):
            _add_unique(findings, _finding(
                idx,
                severity="medium",
                title=f"Potential Unbounded Loop in Public Function: {fn.name}",
                description="A public/external function appears to loop over dynamic length or uses while-loop logic.",
                line=fn.start_line,
                code=fn.signature,
                business="Large input/state sizes can make transactions fail, block claims, or create denial-of-service risk.",
                dev="Unbounded loops in user/admin flows can become impossible to execute as data grows.",
                fix="Use pagination, pull-based claiming, capped batch sizes, or off-chain indexing instead of unbounded loops.",
                confidence="low",
                category="gas",
                rule_id="WG-SOL-GAS-001",
                fn=fn.name,
            ))
            idx += 1

    if re.search(r"function\s+initialize\s*\(", code, re.IGNORECASE):
        for fn in extract_functions(code):
            if fn.name.lower() == "initialize" and "initializer" not in fn.signature and not has_access_control(fn):
                _add_unique(findings, _finding(
                    idx,
                    severity="critical",
                    title="Initializer May Be Unprotected",
                    description="An initialize function was found without an obvious initializer modifier or access control.",
                    line=fn.start_line,
                    code=fn.signature,
                    business="Unprotected initializers can allow attackers to take ownership of upgradeable contracts.",
                    dev="Upgradeable contracts must protect initialization and prevent re-initialization.",
                    fix="Use OpenZeppelin initializer/reinitializer modifiers and verify deployment scripts initialize exactly once.",
                    confidence="medium",
                    category="upgradeability",
                    rule_id="WG-SOL-UPGRADE-002",
                    fn=fn.name,
                ))
                idx += 1
    return idx


def _token_specific_checks(code: str, findings: list[Finding], start_idx: int, contract_type: str | None) -> int:
    idx = start_idx
    tokenish = bool(re.search(r"ERC20|IERC20|balanceOf|allowance|approve|transferFrom|mint|burn", code, re.IGNORECASE)) or (contract_type or "").lower() in {"erc20", "token"}
    nftish = bool(re.search(r"ERC721|ERC1155|setApprovalForAll|tokenURI|baseURI|safeMint", code, re.IGNORECASE)) or (contract_type or "").lower() in {"nft", "erc721", "erc1155"}

    if tokenish and re.search(r"function\s+approve\s*\(", code, re.IGNORECASE):
        line, _ = first_match_line(code, r"function\s+approve\s*\(")
        _add_unique(findings, _finding(
            idx,
            severity="info",
            title="ERC20 Approve Race-Condition Education",
            description="An approve function or ERC20 approval flow is present.",
            line=line,
            code=line_text(code, line),
            business="Users can misunderstand allowance behavior; some integrations are vulnerable to allowance race-condition UX issues.",
            dev="The classic ERC20 approve flow can be front-run when changing non-zero allowance to another non-zero value.",
            fix="Consider increaseAllowance/decreaseAllowance UX, permit warnings, or require zero-reset before allowance changes where appropriate.",
            confidence="low",
            category="token_standard",
            rule_id="WG-SOL-TOKEN-001",
            references=["ERC20 approve allowance race-condition"],
        ))
        idx += 1

    if tokenish and re.search(r"function\s+mint\s*\(", code, re.IGNORECASE):
        line, _ = first_match_line(code, r"function\s+mint\s*\(")
        _add_unique(findings, _finding(
            idx,
            severity="medium",
            title="Mint Authority Disclosure Needed",
            description="Minting capability is present and should be clearly disclosed.",
            line=line,
            code=line_text(code, line),
            business="Unlimited or unclear mint authority can damage token trust and listing/investor confidence.",
            dev="Even if access controlled, mint functions need cap, role, event, and governance review.",
            fix="Document who can mint, add supply caps where appropriate, emit events, and protect minter roles with multisig/timelock.",
            confidence="medium",
            category="centralization",
            rule_id="WG-SOL-TOKEN-002",
        ))
        idx += 1

    if nftish and re.search(r"setBaseURI|_baseURI|baseURI\s*=|tokenURI", code, re.IGNORECASE):
        line, _ = first_match_line(code, r"setBaseURI|_baseURI|baseURI\s*=|tokenURI")
        _add_unique(findings, _finding(
            idx,
            severity="info",
            title="NFT Metadata Mutability Review",
            description="NFT metadata/baseURI logic appears present.",
            line=line,
            code=line_text(code, line),
            business="Mutable metadata can reduce buyer trust if not clearly disclosed.",
            dev="NFT projects should clarify whether metadata is frozen, revealable, or admin-mutable.",
            fix="Add metadata freeze/reveal policy and emit events when base URI changes.",
            confidence="low",
            category="nft_metadata",
            rule_id="WG-SOL-NFT-001",
        ))
        idx += 1
    return idx




# ── Professional Scanner Phase B: deeper audit-grade Solidity heuristics ─────────────────────────────────────────────

def _upgrade_authorization_deep_checks(code: str, findings: list[Finding], idx: int) -> int:
    """Upgradeable contract controls, implementation lock, and storage-layout readiness."""
    upgradeable = bool(re.search(r"UUPSUpgradeable|Initializable|Upgradeable|TransparentUpgradeableProxy|BeaconProxy|upgradeTo\s*\(|upgradeToAndCall\s*\(", code, re.IGNORECASE))
    if not upgradeable:
        return idx

    if re.search(r"upgradeTo\s*\(|upgradeToAndCall\s*\(", code, re.IGNORECASE) and not re.search(r"function\s+_authorizeUpgrade\s*\(", code):
        line, _ = first_match_line(code, r"upgradeTo\s*\(|upgradeToAndCall\s*\(")
        _add_unique(findings, _finding(
            idx, severity="critical",
            title="Upgradeable Contract Without Clear _authorizeUpgrade Hook",
            description="Upgradeability is detected, but the UUPS authorization hook is not visible in the submitted source.",
            line=line, code=line_text(code, line),
            business="If upgrade authorization is missing or weak, an attacker or mistaken operator can replace the implementation and take over funds or roles.",
            dev="UUPS implementations must override _authorizeUpgrade and protect it with onlyOwner/onlyRole/multisig/timelock controls.",
            fix="Implement _authorizeUpgrade(address newImplementation) internal override onlyOwner/onlyRole and protect the owner role with multisig/timelock.",
            confidence="medium", category="upgradeability", rule_id="WG-SOL-UPGRADE-003",
            references=["OpenZeppelin UUPSUpgradeable _authorizeUpgrade", "Proxy upgrade access control"],
        ))
        idx += 1

    if re.search(r"Initializable|initializer|__\w+_init", code) and not re.search(r"_disableInitializers\s*\(", code):
        line, _ = first_match_line(code, r"Initializable|initializer|__\w+_init")
        _add_unique(findings, _finding(
            idx, severity="high",
            title="Upgradeable Implementation May Not Disable Initializers",
            description="Initializable upgrade pattern is present but _disableInitializers() was not detected in a constructor.",
            line=line, code=line_text(code, line),
            business="A public implementation contract that remains initializable can be taken over, confusing integrations and sometimes enabling upgrade abuse.",
            dev="OpenZeppelin upgradeable implementations should call _disableInitializers() in the implementation constructor.",
            fix="Add constructor() { _disableInitializers(); } to the implementation contract and keep proxy initialization separate.",
            confidence="medium", category="upgradeability", rule_id="WG-SOL-UPGRADE-004",
            references=["OpenZeppelin Initializable", "Implementation contract initialization risk"],
        ))
        idx += 1

    if re.search(r"Upgradeable|Initializable|__\w+_init", code) and not re.search(r"uint256\s*\[[0-9]+\]\s+private\s+__gap", code):
        _add_unique(findings, _finding(
            idx, severity="medium",
            title="Upgradeable Storage Gap Not Detected",
            description="Upgradeable-style code is present but a reserved storage gap was not detected.",
            line=None, code=None,
            business="Future upgrades can accidentally shift storage layout and corrupt balances, owners, or protocol configuration.",
            dev="Upgradeable contracts commonly reserve storage slots using uint256[__] private __gap; and require storage-layout review per upgrade.",
            fix="Add an appropriate __gap storage reserve and verify layout compatibility before every upgrade.",
            confidence="low", category="upgradeability", rule_id="WG-SOL-UPGRADE-005",
            references=["OpenZeppelin upgradeable storage gaps", "Storage layout compatibility"],
        ))
        idx += 1
    return idx


def _oracle_staleness_and_decimal_checks(code: str, findings: list[Finding], idx: int) -> int:
    """Chainlink/oracle freshness, round validation, decimal normalization."""
    oracle_like = bool(re.search(r"latestRoundData|latestAnswer|AggregatorV3Interface|priceFeed|oracle\.|getPrice", code, re.IGNORECASE))
    if not oracle_like:
        return idx

    line, _ = first_match_line(code, r"latestRoundData|latestAnswer|AggregatorV3Interface|priceFeed|oracle\.|getPrice")
    if re.search(r"latestRoundData\s*\(", code) and not re.search(r"updatedAt|answeredInRound|roundId", code):
        _add_unique(findings, _finding(
            idx, severity="high",
            title="Oracle latestRoundData Used Without Freshness Validation",
            description="Chainlink-style latestRoundData appears to be used without visible updatedAt/round validation.",
            line=line, code=line_text(code, line),
            business="Stale oracle prices can cause bad liquidations, undercollateralized borrows, or incorrect swaps.",
            dev="Validate updatedAt, answer > 0, and completed round data before using oracle prices in value-bearing logic.",
            fix="Require answer > 0 and updatedAt >= block.timestamp - MAX_STALENESS. Consider checking answeredInRound >= roundId where relevant.",
            confidence="medium", category="oracle", rule_id="WG-SOL-ORACLE-001",
            references=["Chainlink latestRoundData freshness checks", "Oracle manipulation risk"],
        ))
        idx += 1

    if re.search(r"latestRoundData|AggregatorV3Interface|decimals\s*\(", code, re.IGNORECASE) and not re.search(r"decimals\s*\(|10\s*\*\*\s*\w*decimals|1e8|1e18", code):
        _add_unique(findings, _finding(
            idx, severity="medium",
            title="Oracle Decimal Normalization Not Obvious",
            description="Oracle price usage is present, but decimal normalization is not obvious in the submitted source.",
            line=line, code=line_text(code, line),
            business="Decimal mismatch can overvalue or undervalue collateral and break DeFi accounting.",
            dev="Different oracle feeds can use different decimals. Token decimals and oracle decimals must be normalized explicitly.",
            fix="Read oracle decimals or document feed decimals, then normalize all prices to the protocol's accounting precision.",
            confidence="low", category="oracle", rule_id="WG-SOL-ORACLE-002",
            references=["Chainlink feed decimals", "DeFi accounting precision"],
        ))
        idx += 1
    return idx


def _dex_and_slippage_deep_checks(code: str, findings: list[Finding], idx: int) -> int:
    """DEX router slippage and deadline anti-MEV checks."""
    swap_like = bool(re.search(r"swapExact|exactInput|exactOutput|amountOutMin|amountInMaximum|ISwapRouter|IUniswap|PancakeRouter", code, re.IGNORECASE))
    if not swap_like:
        return idx

    zero_min_pattern = r"amountOutMin\s*[,=]\s*0|amountOutMinimum\s*[:=]\s*0|minAmountOut\s*[:=]\s*0|swapExact\w+\s*\([^;]{0,180},\s*0\s*,"
    if re.search(zero_min_pattern, code, re.IGNORECASE | re.DOTALL):
        line, _ = first_match_line(code, zero_min_pattern)
        _add_unique(findings, _finding(
            idx, severity="high",
            title="Swap Allows Zero Minimum Output",
            description="A swap path appears to allow amountOutMin / amountOutMinimum to be zero.",
            line=line, code=line_text(code, line),
            business="Users or protocol funds can receive almost nothing during MEV, sandwich attacks, or bad routing.",
            dev="Zero slippage protection is unsafe for value-bearing swaps. The caller should provide a minimum output from a quote with slippage bounds.",
            fix="Require a non-zero minimum output and pass user-approved slippage settings. Reject stale quotes.",
            confidence="medium", category="mev", rule_id="WG-SOL-MEV-001",
            references=["DEX slippage protection", "MEV sandwich attack"],
        ))
        idx += 1

    if re.search(r"deadline\s*[:=,]\s*block\.timestamp|deadline\s*[:=,]\s*type\(uint256\)\.max", code):
        line, _ = first_match_line(code, r"deadline\s*[:=,]\s*block\.timestamp|deadline\s*[:=,]\s*type\(uint256\)\.max")
        _add_unique(findings, _finding(
            idx, severity="medium",
            title="Weak Swap Deadline Handling",
            description="A swap deadline appears to be block.timestamp or an unlimited max value.",
            line=line, code=line_text(code, line),
            business="Weak deadlines make stale transactions easier to execute in unfavorable market conditions.",
            dev="Deadline should be caller-provided and bounded. Unlimited deadlines are unsafe for swaps.",
            fix="Require deadline >= block.timestamp and deadline <= block.timestamp + MAX_DEADLINE_WINDOW.",
            confidence="medium", category="mev", rule_id="WG-SOL-MEV-002",
            references=["Uniswap router deadline usage", "Stale transaction risk"],
        ))
        idx += 1
    return idx


def _permit_nonce_deadline_deep_checks(code: str, findings: list[Finding], idx: int) -> int:
    """Signature replay and malleability checks beyond basic EIP-712 domain checks."""
    signature_like = bool(re.search(r"permit\s*\(|ecrecover\s*\(|ECDSA|_hashTypedData|SignatureChecker", code, re.IGNORECASE))
    if not signature_like:
        return idx

    line, _ = first_match_line(code, r"permit\s*\(|ecrecover\s*\(|ECDSA|_hashTypedData|SignatureChecker")
    if not re.search(r"nonce|nonces\s*\[|_useNonce|_nonces", code, re.IGNORECASE):
        _add_unique(findings, _finding(
            idx, severity="high",
            title="Signature Flow Missing Obvious Nonce Protection",
            description="Signature verification is present, but nonce usage was not detected.",
            line=line, code=line_text(code, line),
            business="A valid signature may be replayed multiple times to drain funds, repeat approvals, or bypass one-time authorization.",
            dev="Every off-chain authorization should bind a unique nonce and consume it exactly once.",
            fix="Include nonce in the signed struct/hash and increment or consume nonce before/with execution.",
            confidence="medium", category="signature", rule_id="WG-SOL-SIG-003",
            references=["EIP-2612 permit nonce", "Signature replay protection"],
        ))
        idx += 1

    if re.search(r"permit\s*\(|ecrecover\s*\(|_hashTypedData", code, re.IGNORECASE) and not re.search(r"deadline|expiry|expiresAt|validUntil", code, re.IGNORECASE):
        _add_unique(findings, _finding(
            idx, severity="medium",
            title="Signature Flow Missing Expiry / Deadline",
            description="Signature authorization is present, but no expiry/deadline field was detected.",
            line=line, code=line_text(code, line),
            business="Long-lived signatures increase damage if leaked or signed by mistake.",
            dev="Permits and meta-transactions should include a deadline and reject expired signatures.",
            fix="Add deadline/expiry to the signed data and require(block.timestamp <= deadline).",
            confidence="medium", category="signature", rule_id="WG-SOL-SIG-004",
            references=["EIP-2612 deadline", "EIP-712 signed data expiry"],
        ))
        idx += 1

    if re.search(r"ecrecover\s*\(", code) and not re.search(r"ECDSA\.recover|SignatureChecker|s\s*<=|v\s*==\s*27|v\s*==\s*28", code):
        _add_unique(findings, _finding(
            idx, severity="medium",
            title="Raw ecrecover Without Obvious Malleability Guards",
            description="Raw ecrecover is used without obvious v/s malleability checks or OpenZeppelin ECDSA wrapper.",
            line=line, code=line_text(code, line),
            business="Signature malleability can break signature uniqueness assumptions and complicate replay prevention.",
            dev="Use OpenZeppelin ECDSA.recover or validate v and low-s per EIP-2.",
            fix="Replace raw ecrecover with ECDSA.recover from OpenZeppelin or enforce strict v and low-s checks.",
            confidence="medium", category="signature", rule_id="WG-SOL-SIG-005",
            references=["OpenZeppelin ECDSA", "EIP-2 low-s signatures"],
        ))
        idx += 1
    return idx


def _erc4626_vault_deep_checks(code: str, findings: list[Finding], idx: int) -> int:
    """ERC4626/share vault rounding, donation, and initialization risk signals."""
    vault_like = bool(re.search(r"ERC4626|totalAssets\s*\(|convertToShares\s*\(|previewDeposit\s*\(|previewRedeem\s*\(|deposit\s*\(|redeem\s*\(", code))
    if not vault_like:
        return idx

    line, _ = first_match_line(code, r"ERC4626|convertToShares\s*\(|previewDeposit\s*\(|deposit\s*\(")
    if not re.search(r"virtualAssets|virtualShares|_decimalsOffset|MINIMUM_LIQUIDITY|seed|initialDeposit", code, re.IGNORECASE):
        _add_unique(findings, _finding(
            idx, severity="high",
            title="ERC4626 / Vault Inflation Protection Not Obvious",
            description="Vault/share accounting is detected, but common first-deposit or donation attack protections were not obvious.",
            line=line, code=line_text(code, line),
            business="An attacker may manipulate share price during the first deposit and steal value from later depositors.",
            dev="ERC4626-style vaults need inflation/donation attack defenses such as virtual shares/assets, decimal offset, or seeded liquidity.",
            fix="Add virtual share/asset accounting, seed initial liquidity safely, and add tests for first-deposit/donation attacks.",
            confidence="medium", category="vault", rule_id="WG-SOL-VAULT-001",
            references=["ERC4626 inflation attack", "OpenZeppelin ERC4626 virtual offset"],
        ))
        idx += 1

    if re.search(r"convertToShares|convertToAssets|previewDeposit|previewMint", code) and not re.search(r"Math\.Rounding|rounding|mulDiv", code):
        _add_unique(findings, _finding(
            idx, severity="medium",
            title="Vault Share Rounding Policy Not Obvious",
            description="Vault conversion/preview functions are present without an obvious rounding policy.",
            line=line, code=line_text(code, line),
            business="Rounding mistakes can leak value, harm users, or create profitable edge-case arbitrage.",
            dev="Share math should use reviewed mulDiv and explicit rounding direction per function.",
            fix="Use Math.mulDiv with explicit Math.Rounding and add tests for small deposits, large deposits, zero supply, and donation scenarios.",
            confidence="low", category="vault", rule_id="WG-SOL-VAULT-002",
            references=["ERC4626 rounding requirements", "OpenZeppelin Math.mulDiv"],
        ))
        idx += 1
    return idx


def _admin_parameter_cap_checks(code: str, findings: list[Finding], idx: int) -> int:
    """Owner-adjustable fees/limits without caps, delay, or events."""
    setter_matches = re.finditer(
        r"function\s+(set|update|change)(Fee|Tax|Rate|Limit|Cap|Treasury|Router|Oracle)\w*\s*\([^)]*\)\s*(?:external|public)[^{]*\{(?P<body>[^}]*)\}",
        code,
        re.IGNORECASE | re.DOTALL,
    )
    for match in list(setter_matches)[:4]:
        body = match.group("body")
        line = code[:match.start()].count("\n") + 1
        function_source = match.group(0)[:800]
        has_cap = bool(re.search(r"require\s*\([^;]*(<=|<)\s*(MAX|max|[0-9_]+)", body))
        has_event = bool(re.search(r"emit\s+\w+", body))
        has_delay = bool(re.search(r"timelock|delay|eta|queued|schedule", function_source, re.IGNORECASE))
        if not (has_cap and has_event):
            _add_unique(findings, _finding(
                idx, severity="medium",
                title="Admin Parameter Setter Needs Cap/Event Review",
                description="A privileged-looking parameter setter lacks an obvious cap and/or event emission.",
                line=line, code=line_text(code, line),
                business="Silent or uncapped parameter changes can create rug-pull, fee abuse, oracle switch, or governance trust risk.",
                dev="Critical setters should enforce maximum bounds, emit events, and ideally be protected by timelock/multisig.",
                fix="Add require(value <= MAX_ALLOWED), emit an event, and route critical changes through multisig/timelock. Document admin powers.",
                confidence="medium", category="centralization", rule_id="WG-SOL-ADMIN-005",
                references=["Admin parameter bounds", "Timelock governance controls"],
            ))
            idx += 1
            break
        if not has_delay and re.search(r"Oracle|Router|Treasury", match.group(0), re.IGNORECASE):
            _add_unique(findings, _finding(
                idx, severity="low",
                title="Critical Address Setter Without Timelock Signal",
                description="A setter for oracle/router/treasury-like address does not show an obvious timelock signal.",
                line=line, code=line_text(code, line),
                business="Critical infrastructure address changes can redirect funds or manipulate prices if executed instantly.",
                dev="This may be acceptable for early beta, but production protocols should use multisig/timelock or governance delay.",
                fix="Move critical address setters behind multisig and timelock, and emit events for monitoring.",
                confidence="low", category="centralization", rule_id="WG-SOL-ADMIN-006",
                references=["Timelock Controller", "Protocol admin operations"],
            ))
            idx += 1
            break
    return idx


def _l2_crosschain_sender_checks(code: str, findings: list[Finding], idx: int) -> int:
    """Cross-chain messenger and bridge sender validation."""
    if not re.search(r"xDomainMessageSender|ICrossDomainMessenger|IInbox|ArbSys|LayerZero|lzReceive|ccipReceive|Any2EVMMessage|bridge|relayMessage", code, re.IGNORECASE):
        return idx
    if not re.search(r"xDomainMessageSender\s*\(\)|trustedRemote|trustedSender|sourceChainSelector|onlyMessenger|msg\.sender\s*==\s*\w*Messenger", code, re.IGNORECASE):
        line, _ = first_match_line(code, r"xDomainMessageSender|ICrossDomainMessenger|LayerZero|lzReceive|ccipReceive|bridge|relayMessage")
        _add_unique(findings, _finding(
            idx, severity="high",
            title="Cross-Chain Message Sender Validation Not Obvious",
            description="Cross-chain messaging or bridge code is detected without obvious trusted sender/source validation.",
            line=line, code=line_text(code, line),
            business="Forged or misrouted cross-chain messages can mint assets, unlock bridge funds, or execute admin actions on the destination chain.",
            dev="Destination handlers must validate the messenger contract, source chain, and original sender/remote endpoint.",
            fix="Require msg.sender == trusted messenger and verify source chain + trusted remote/original sender before executing messages.",
            confidence="medium", category="crosschain", rule_id="WG-SOL-XCHAIN-001",
            references=["Cross-chain bridge message validation", "LayerZero trusted remote", "Optimism xDomainMessageSender"],
        ))
        idx += 1
    return idx


def _phase_b_rule_coverage_summary(code: str, findings: list[Finding]) -> dict:
    """Non-finding metadata for benchmark/report readiness."""
    categories = sorted({f.category for f in findings if f.category})
    phase_b_ids = [f.rule_id for f in findings if f.rule_id and f.rule_id.startswith(("WG-SOL-ORACLE", "WG-SOL-MEV", "WG-SOL-VAULT", "WG-SOL-XCHAIN"))]
    return {
        "phase": "professional_scanner_phase_b",
        "new_rule_families": ["upgradeability", "oracle", "mev_slippage", "signature_replay", "erc4626_vault", "admin_parameter_controls", "crosschain"],
        "triggered_phase_b_rule_ids": sorted(set(phase_b_ids)),
        "finding_categories": categories,
        "line_count": len(lines(code)),
        "note": "Heuristic findings are evidence-first pre-audit signals and require reviewer triage before certified-audit wording.",
    }


def scan_solidity(solidity_code: str, project_name: str | None = None, contract_type: str | None = None) -> ScanResponse:
    code = solidity_code.strip()
    findings: list[Finding] = []
    idx = 1

    if len(lines(code)) > 1800:
        findings.append(_finding(
            idx,
            severity="info",
            title="Large Contract Submitted",
            description="This contract is large for a preliminary rule engine review.",
            line=None,
            code=None,
            business="Large codebases are more likely to need full manual review and tool-assisted analysis.",
            dev="Rule engines are useful for early warnings but large projects need Slither/Aderyn/tests/manual review.",
            fix="Run a full pre-audit package with repository context, dependencies, tests, and deployment scripts.",
            confidence="high",
            category="scope",
            rule_id="WG-SOL-SCOPE-001",
        ))
        idx += 1

    idx = _pragma_checks(code, findings, idx)
    idx = _global_pattern_checks(code, findings, idx)
    idx = _access_control_checks(code, findings, idx)
    idx = _external_call_checks(code, findings, idx)
    idx = _centralization_and_admin_checks(code, findings, idx)
    idx = _event_and_payable_checks(code, findings, idx)
    idx = _gas_and_launch_readiness_checks(code, findings, idx)
    idx = _token_specific_checks(code, findings, idx, contract_type)
    idx = _defi_and_oracle_checks(code, findings, idx)
    idx = _access_pattern_checks(code, findings, idx)
    idx = _integer_and_math_checks(code, findings, idx)
    idx = _signature_and_permit_checks(code, findings, idx)
    idx = _randomness_and_dos_checks(code, findings, idx)
    idx = _zero_address_and_deprecated_checks(code, findings, idx)
    idx = _frontrunning_and_locked_ether(code, findings, idx)
    idx = _equality_and_shadowing_checks(code, findings, idx)
    idx = _rug_pull_pattern_checks(code, findings, idx)
    idx = _gas_and_storage_checks(code, findings, idx)
    idx = _compliance_and_disclosure_checks(code, findings, idx)
    idx = _cross_function_reentrancy(code, findings, idx)
    idx = _arbitrary_transferfrom(code, findings, idx)
    idx = _price_manipulation_same_tx(code, findings, idx)
    idx = _integer_overflow_old_solidity(code, findings, idx)
    idx = _governance_attack_checks(code, findings, idx)
    idx = _erc20_return_value_check(code, findings, idx)
    idx = _missing_event_on_critical_ops(code, findings, idx)
    idx = _centralized_bridge_risk(code, findings, idx)
    idx = _nft_reentrancy_on_transfer(code, findings, idx)
    idx = _immutable_and_constant_checks(code, findings, idx)
    idx = _eip712_domain_separator_checks(code, findings, idx)
    idx = _multicall_reentrancy(code, findings, idx)
    idx = _upgrade_authorization_deep_checks(code, findings, idx)
    idx = _oracle_staleness_and_decimal_checks(code, findings, idx)
    idx = _dex_and_slippage_deep_checks(code, findings, idx)
    idx = _permit_nonce_deadline_deep_checks(code, findings, idx)
    idx = _erc4626_vault_deep_checks(code, findings, idx)
    idx = _admin_parameter_cap_checks(code, findings, idx)
    idx = _l2_crosschain_sender_checks(code, findings, idx)

    findings = prepare_professional_findings(findings, default_source_tool="web3guard_local_rules")
    score = score_findings(findings)
    digest = sha12(code)
    return ScanResponse(
        report_id=f"W3G-CONTRACT-{digest}",
        generated_at=datetime.now(timezone.utc),
        project_name=project_name,
        module_score=ModuleScore(module="contract", score=score, risk_label=risk_label(score)),
        findings=findings,
        severity_breakdown=severity_breakdown(findings),
        priority_actions=priority_actions(findings),
        input_hash=digest,
        engine_version=ENGINE_VERSION,
        scan_metadata={
            "audit_grade_finding_summary": audit_grade_summary(findings),
            "phase_b_rule_coverage": _phase_b_rule_coverage_summary(code, findings),
            "finding_engine": "professional_normalized_rule_engine_phase_b",
            "real_only_note": "Local Solidity rules produce preliminary evidence only; findings require triage before certified-audit wording.",
        },
    )


def available_contract_rules() -> list[dict[str, str]]:
    return [
        {"id": "WG-SOL-META-001", "name": "Missing SPDX", "category": "metadata"},
        {"id": "WG-SOL-META-002", "name": "Missing pragma", "category": "metadata"},
        {"id": "WG-SOL-META-003", "name": "Floating pragma", "category": "metadata"},
        {"id": "WG-SOL-META-004", "name": "Old compiler family", "category": "metadata"},
        {"id": "WG-SOL-AUTH-001", "name": "tx.origin authorization", "category": "access_control"},
        {"id": "WG-SOL-AUTH-002", "name": "Sensitive function without access control", "category": "access_control"},
        {"id": "WG-SOL-REENT-001", "name": "External call before state update", "category": "reentrancy"},
        {"id": "WG-SOL-REENT-002", "name": "Value transfer without reentrancy guard", "category": "reentrancy"},
        {"id": "WG-SOL-CALL-001", "name": "Delegatecall usage", "category": "low_level_call"},
        {"id": "WG-SOL-CALL-003", "name": "Unchecked low-level call", "category": "low_level_call"},
        {"id": "WG-SOL-ADMIN-001", "name": "Owner/admin centralization", "category": "centralization"},
        {"id": "WG-SOL-ADMIN-002", "name": "Hardcoded privileged address", "category": "centralization"},
        {"id": "WG-SOL-UPGRADE-001", "name": "Upgradeable proxy review", "category": "upgradeability"},
        {"id": "WG-SOL-UPGRADE-002", "name": "Initializer protection", "category": "upgradeability"},
        {"id": "WG-SOL-EVENT-001", "name": "Sensitive function no event", "category": "observability"},
        {"id": "WG-SOL-GAS-001", "name": "Unbounded loop", "category": "gas"},
        {"id": "WG-SOL-TOKEN-001", "name": "ERC20 approve education", "category": "token_standard"},
        {"id": "WG-SOL-TOKEN-002", "name": "Mint authority disclosure", "category": "centralization"},
        {"id": "WG-SOL-NFT-001",   "name": "NFT metadata mutability", "category": "nft_metadata"},
        {"id": "WG-SOL-DEFI-001",  "name": "Flash loan sensitive function", "category": "defi"},
        {"id": "WG-SOL-DEFI-002",  "name": "Oracle price feed dependency", "category": "defi"},
        {"id": "WG-SOL-DEFI-003",  "name": "Unlimited approval (max uint)", "category": "defi"},
        {"id": "WG-SOL-TAX-001",   "name": "Fee-on-transfer / tax token", "category": "token_standard"},
        {"id": "WG-SOL-ADMIN-003", "name": "Blacklist centralization", "category": "centralization"},
        {"id": "WG-SOL-ADMIN-004", "name": "Pausable admin power", "category": "centralization"},
        {"id": "WG-SOL-MATH-001",  "name": "Division before multiplication", "category": "math"},
        {"id": "WG-SOL-MATH-002",  "name": "Unchecked arithmetic block", "category": "math"},
        {"id": "WG-SOL-SIG-001",   "name": "Signature/permit replay risk", "category": "signature"},
        {"id": "WG-SOL-RAND-001", "name": "Weak randomness (block.timestamp/blockhash)", "category": "randomness"},
        {"id": "WG-SOL-DOS-001",  "name": "Unbounded loop — DoS risk", "category": "dos"},
        {"id": "WG-SOL-ZERO-001", "name": "Missing zero-address check", "category": "validation"},
        {"id": "WG-SOL-DEPR-001", "name": "Deprecated .transfer()/.send()", "category": "compatibility"},
        {"id": "WG-SOL-FRONT-001","name": "Front-running — missing deadline/slippage", "category": "mev"},
        {"id": "WG-SOL-LOCK-001", "name": "Locked ether — no withdrawal function", "category": "funds"},
        {"id": "WG-SOL-EQ-001",   "name": "Dangerous equality on contract balance", "category": "logic"},
        {"id": "WG-SOL-SHADOW-001","name": "State variable shadowing", "category": "logic"},
        {"id": "WG-SOL-RUG-001",    "name": "Owner drain / emergency sweep", "category": "rug_pull"},
        {"id": "WG-SOL-RUG-002",    "name": "Mint without supply cap", "category": "rug_pull"},
        {"id": "WG-SOL-GAS-003",    "name": "Storage read in loop", "category": "gas"},
        {"id": "WG-SOL-GAS-004",    "name": "String mapping key inefficiency", "category": "gas"},
        {"id": "WG-SOL-COMP-001",    "name": "No KYC/compliance hook disclosure", "category": "compliance"},
        {"id": "WG-SOL-REENT-003",   "name": "Cross-function reentrancy", "category": "reentrancy"},
        {"id": "WG-SOL-ARBTRF-001",  "name": "Arbitrary transferFrom", "category": "access_control"},
        {"id": "WG-SOL-PRICE-001",   "name": "Spot price manipulation", "category": "defi"},
        {"id": "WG-SOL-OVFL-001",    "name": "Integer overflow (pre-0.8.0)", "category": "math"},
        {"id": "WG-SOL-GOV-001",     "name": "Governance flash loan attack", "category": "governance"},
        {"id": "WG-SOL-ERC20-001",   "name": "Unsafe ERC20 transfer", "category": "compatibility"},
        {"id": "WG-SOL-EVT-004",     "name": "Missing event on setter function", "category": "observability"},
        {"id": "WG-SOL-BRIDGE-001",  "name": "Bridge single validator risk", "category": "centralization"},
        {"id": "WG-SOL-NFT-002",     "name": "NFT reentrancy via onERC721Received", "category": "reentrancy"},
        {"id": "WG-SOL-GAS-005",     "name": "Address should be immutable", "category": "gas"},
        {"id": "WG-SOL-SIG-002",     "name": "EIP-712 missing chainId", "category": "signature"},
        {"id": "WG-SOL-MULTI-001",   "name": "Multicall msg.value reuse", "category": "defi"},
        {"id": "WG-SOL-UPGRADE-003", "name": "UUPS authorize upgrade hook", "category": "upgradeability"},
        {"id": "WG-SOL-UPGRADE-004", "name": "Disable implementation initializers", "category": "upgradeability"},
        {"id": "WG-SOL-UPGRADE-005", "name": "Upgradeable storage gap", "category": "upgradeability"},
        {"id": "WG-SOL-ORACLE-001", "name": "Oracle freshness validation", "category": "oracle"},
        {"id": "WG-SOL-ORACLE-002", "name": "Oracle decimal normalization", "category": "oracle"},
        {"id": "WG-SOL-MEV-001", "name": "Zero minimum swap output", "category": "mev"},
        {"id": "WG-SOL-MEV-002", "name": "Weak swap deadline", "category": "mev"},
        {"id": "WG-SOL-SIG-003", "name": "Signature nonce protection", "category": "signature"},
        {"id": "WG-SOL-SIG-004", "name": "Signature expiry/deadline", "category": "signature"},
        {"id": "WG-SOL-SIG-005", "name": "Raw ecrecover malleability", "category": "signature"},
        {"id": "WG-SOL-VAULT-001", "name": "ERC4626 inflation protection", "category": "vault"},
        {"id": "WG-SOL-VAULT-002", "name": "Vault rounding policy", "category": "vault"},
        {"id": "WG-SOL-ADMIN-005", "name": "Admin parameter cap/event", "category": "centralization"},
        {"id": "WG-SOL-ADMIN-006", "name": "Critical address timelock", "category": "centralization"},
        {"id": "WG-SOL-XCHAIN-001", "name": "Cross-chain sender validation", "category": "crosschain"},
    ]


# ── 7 Additional Real Rules (WG-SOL-DEFI through WG-SOL-SIG) ──────────────────────────────────────────────────────────

def _defi_and_oracle_checks(code: str, findings: list[Finding], idx: int) -> int:
    """Flash loan sensitivity, oracle dependency, and unlimited approval checks."""

    # Flash loan sensitive patterns
    if re.search(r"flashLoan|flashloan|FLASH_LOAN|IFlashLoan|executeOperation|onFlashLoan", code, re.IGNORECASE):
        line, _ = first_match_line(code, r"flashLoan|flashloan|FLASH_LOAN|IFlashLoan|executeOperation|onFlashLoan")
        _add_unique(findings, _finding(
            idx,
            severity="high",
            title="Flash Loan Sensitive Function Detected",
            description="The contract contains flash loan callback or integration patterns. Flash loan attacks can manipulate prices, drain pools, or bypass access controls within a single transaction.",
            line=line,
            code=line_text(code, line),
            business="Flash loan attacks are responsible for hundreds of millions in DeFi losses. A vulnerable flash loan integration can drain all protocol funds instantly.",
            dev="Ensure flash loan callbacks validate the initiator, validate repayment, and are protected against reentrancy. Avoid using spot prices during flash loan callbacks.",
            fix="Add initiator check, reentrancy guard, and validate all state after the flash loan callback completes. Never use spot reserves as price oracles inside flash loan flows.",
            confidence="medium",
            category="defi",
            rule_id="WG-SOL-DEFI-001",
            references=["SWC-107", "Flash Loan Attack Patterns", "Checks-Effects-Interactions"],
        ))
        idx += 1

    # Oracle price dependency
    if re.search(r"getPrice|latestRoundData|latestAnswer|priceFeed|AggregatorV3|IOracle|oracle\.", code, re.IGNORECASE):
        line, _ = first_match_line(code, r"getPrice|latestRoundData|latestAnswer|priceFeed|AggregatorV3|IOracle|oracle\.")
        _add_unique(findings, _finding(
            idx,
            severity="medium",
            title="Oracle Price Feed Dependency",
            description="The contract depends on an external price oracle. If the oracle is stale, manipulated, or returns incorrect data, the contract logic may be exploited.",
            line=line,
            code=line_text(code, line),
            business="Oracle manipulation is one of the most common DeFi attack vectors. Stale or manipulated prices can allow attackers to profit at protocol expense.",
            dev="Always validate oracle freshness (check updatedAt timestamp), handle roundId correctly, and consider using TWAP prices rather than spot prices for critical calculations.",
            fix="Add staleness check: require(updatedAt >= block.timestamp - MAX_STALENESS). Consider using multiple oracle sources or TWAP. Add circuit breakers for extreme price moves.",
            confidence="medium",
            category="defi",
            rule_id="WG-SOL-DEFI-002",
            references=["Chainlink Oracle Best Practices", "Oracle Manipulation Attacks"],
        ))
        idx += 1

    # Unlimited approval pattern
    if re.search(r"type\(uint256\)\.max|type\(uint\)\.max|MAX_INT|UINT_MAX|2\*\*256\s*-\s*1", code):
        line, _ = first_match_line(code, r"type\(uint256\)\.max|type\(uint\)\.max|MAX_INT|UINT_MAX|2\*\*256\s*-\s*1")
        _add_unique(findings, _finding(
            idx,
            severity="medium",
            title="Unlimited Approval (Max Uint) Usage",
            description="The contract uses unlimited approval amounts (type(uint256).max). While common in DeFi integrations, this pattern warrants disclosure and careful spender verification.",
            line=line,
            code=line_text(code, line),
            business="Unlimited approvals mean a compromised or malicious spender can drain all user tokens. Users should understand the risk before approving.",
            dev="Add a warning in the UI when requesting unlimited approvals. Verify spender contract is immutable, audited, and trusted before requesting max approval.",
            fix="Document all unlimited approval use cases. Add UI warnings. Consider time-limited or amount-limited approvals where possible.",
            confidence="medium",
            category="defi",
            rule_id="WG-SOL-DEFI-003",
            references=["ERC20 Approval Risk Disclosure", "Permit2 safer alternatives"],
        ))
        idx += 1

    return idx


def _access_pattern_checks(code: str, findings: list[Finding], idx: int) -> int:
    """Fee-on-transfer tax, blacklist, selfdestruct improvements."""

    # Hidden tax / fee on transfer
    if re.search(r"_taxFee|_liquidityFee|taxFee|buyFee|sellFee|transferFee|_fee\s*=|feePercent|_reflectionFee|marketingFee", code, re.IGNORECASE):
        line, _ = first_match_line(code, r"_taxFee|_liquidityFee|taxFee|buyFee|sellFee|transferFee|_fee\s*=|feePercent|_reflectionFee|marketingFee")
        _add_unique(findings, _finding(
            idx,
            severity="medium",
            title="Fee-on-Transfer / Tax Token Pattern",
            description="The contract includes transfer fee or tax logic. Tax tokens require special handling in DeFi integrations and must be clearly disclosed.",
            line=line,
            code=line_text(code, line),
            business="DEX routers and DeFi protocols typically do not support fee-on-transfer tokens without special configuration. Undisclosed fees cause integration failures and user trust issues.",
            dev="Ensure fees are capped, clearly documented, and emitted in events. DEX integrations require enabling fee-on-transfer support. Max fee cap should be enforced in code.",
            fix="Add maximum fee cap enforced in constructor/setter. Emit event on fee change. Document fee structure prominently in project materials.",
            confidence="medium",
            category="token_standard",
            rule_id="WG-SOL-TAX-001",
            references=["Fee-on-Transfer Token ERC20 compatibility", "SWC Tax Token Disclosure"],
        ))
        idx += 1

    # Blacklist/whitelist pattern
    if re.search(r"blacklist|blacklisted|isBlacklisted|addBlacklist|whitelist|isWhitelisted|blocked\[|_blocked\[", code, re.IGNORECASE):
        line, _ = first_match_line(code, r"blacklist|blacklisted|isBlacklisted|addBlacklist")
        if line:
            _add_unique(findings, _finding(
                idx,
                severity="medium",
                title="Blacklist/Whitelist Centralization",
                description="The contract has blacklisting or whitelisting functionality controlled by an admin. This gives admin significant power over who can use the token.",
                line=line,
                code=line_text(code, line),
                business="Blacklist functionality means admin can freeze any user's funds. This is a centralization risk that may concern exchanges, investors, and regulators.",
                dev="Blacklist should be governed by multisig/DAO with timelock. Log all blacklist actions with events. Consider limiting scope to compliance-only use.",
                fix="Protect blacklist changes with multisig/timelock. Emit events for all blacklist actions. Document intended governance process. Consider allowing users to appeal.",
                confidence="high",
                category="centralization",
                rule_id="WG-SOL-ADMIN-003",
                references=["Centralization Risk Disclosure", "OFAC compliance patterns"],
            ))
            idx += 1

    # Pausable without timelock
    if re.search(r"pause\(\)|_pause\(\)|whenNotPaused|Pausable", code, re.IGNORECASE):
        line, _ = first_match_line(code, r"pause\(\)|_pause\(\)|whenNotPaused|Pausable")
        _add_unique(findings, _finding(
            idx,
            severity="low",
            title="Pausable Contract — Admin Power Disclosure",
            description="The contract inherits or implements pausable functionality. Admin can halt all transfers or operations.",
            line=line,
            code=line_text(code, line),
            business="Pause capability means admin can stop all token transfers or protocol operations instantly. This should be disclosed and protected by governance.",
            dev="Protect pause with multisig. Add unpausing timelock. Document pause conditions in contract documentation. Consider emitting reason in pause event.",
            fix="Add governance protection for pause. Emit reason. Document emergency response process.",
            confidence="medium",
            category="centralization",
            rule_id="WG-SOL-ADMIN-004",
            references=["OpenZeppelin Pausable", "Emergency pause governance best practices"],
        ))
        idx += 1

    return idx


def _integer_and_math_checks(code: str, findings: list[Finding], idx: int) -> int:
    """Division precision loss, unchecked arithmetic, dangerous casting."""

    # Division before multiplication (precision loss)
    if re.search(r"/\s*\w+\s*\*|\/\s*\d+\s*\*", code):
        line, _ = first_match_line(code, r"/\s*\w+\s*\*|\/\s*\d+\s*\*")
        if line:
            _add_unique(findings, _finding(
                idx,
                severity="medium",
                title="Division Before Multiplication — Precision Loss Risk",
                description="A division operation appears before a multiplication in an expression. In Solidity integer math, this causes precision loss because integer division truncates toward zero.",
                line=line,
                code=line_text(code, line),
                business="Precision loss can cause incorrect fee calculations, reward distributions, or collateral calculations — leading to user fund shortfalls.",
                dev="Always multiply before dividing in Solidity. Use uint256 scale factors (1e18) to maintain precision. Consider using FixedPoint math libraries for financial calculations.",
                fix="Reorder to multiply before divide: result = (a * b) / c instead of (a / c) * b. Use mulDiv or PRBMath for precise fixed-point arithmetic.",
                confidence="low",
                category="math",
                rule_id="WG-SOL-MATH-001",
                references=["Solidity integer arithmetic precision", "PRBMath library"],
            ))
            idx += 1

    # Unchecked block usage
    if re.search(r"\bunchecked\b\s*\{", code):
        line, _ = first_match_line(code, r"\bunchecked\b\s*\{")
        _add_unique(findings, _finding(
            idx,
            severity="low",
            title="Unchecked Arithmetic Block Used",
            description="The contract uses unchecked{} blocks which disable Solidity 0.8.x overflow/underflow protection for gas savings.",
            line=line,
            code=line_text(code, line),
            business="Unchecked blocks can reintroduce integer overflow/underflow vulnerabilities if used incorrectly, potentially causing loss of funds.",
            dev="Unchecked is safe only for operations guaranteed not to overflow by prior logic (e.g., counter increment after bounds check). Review each unchecked block carefully.",
            fix="Document why each unchecked block is safe. Add explicit bounds check comments. Avoid unchecked in financial calculation paths unless mathematically proven safe.",
            confidence="low",
            category="math",
            rule_id="WG-SOL-MATH-002",
            references=["SWC-101 Integer Overflow", "Solidity 0.8.x unchecked blocks"],
        ))
        idx += 1

    return idx


def _signature_and_permit_checks(code: str, findings: list[Finding], idx: int) -> int:
    """EIP-712 permit signature replay and deadline checks."""

    if re.search(r"\bpermit\b|EIP712|_hashTypedData|ecrecover|DOMAIN_SEPARATOR|ERC20Permit|EIP2612", code):
        line, _ = first_match_line(code, r"\bpermit\b|EIP712|_hashTypedData|ecrecover|DOMAIN_SEPARATOR|ERC20Permit|EIP2612")
        _add_unique(findings, _finding(
            idx,
            severity="medium",
            title="Signature / Permit Functionality — Replay Risk Review",
            description="The contract uses permit, ecrecover, or EIP-712 signed messages. Improper nonce or deadline handling enables signature replay attacks.",
            line=line,
            code=line_text(code, line),
            business="Signature replay attacks can allow malicious actors to re-use a valid user signature to drain approvals or execute unauthorized transactions.",
            dev="Ensure all signed messages include: unique nonce per user (auto-incrementing), deadline/expiry, chainId in domain separator, and contract address. Use OpenZeppelin EIP712 implementation.",
            fix="Use OpenZeppelin's ERC20Permit or EIP712 library. Verify nonces are incremented atomically. Check deadline on-chain: require(block.timestamp <= deadline). Include chainId in all domain separators.",
            confidence="medium",
            category="signature",
            rule_id="WG-SOL-SIG-001",
            references=["EIP-712 Typed Structured Data Signing", "EIP-2612 permit", "SWC-121 Missing Protection Against Signature Replay"],
        ))
        idx += 1

    return idx


# ── 8 New Rules — Competitor Gap Bridge (WG-SOL-RAND-001 through WG-SOL-SHADOW-001) ─────────────────────────────────

_INLINE_FIXES: dict[str, str] = {
    "WG-SOL-RAND-001": (
        "// ❌ AVOID:\n"
        "// uint256 rand = uint256(blockhash(block.number - 1)) % 100;\n"
        "// uint256 rand = block.timestamp % entries.length;\n\n"
        "// ✅ SAFER (commit-reveal for low-stakes):\n"
        "// bytes32 commitment;\n"
        "// function commit(bytes32 hash) external { commitment = hash; }\n"
        "// function reveal(uint256 secret) external {\n"
        "//   require(keccak256(abi.encodePacked(secret)) == commitment);\n"
        "//   // use secret for selection\n"
        "// }"
    ),
    "WG-SOL-DOS-001": (
        "// ❌ AVOID unbounded loop over user-controlled array:\n"
        "// for (uint i = 0; i < users.length; i++) { distribute(users[i]); }\n\n"
        "// ✅ USE pull-over-push pattern:\n"
        "// mapping(address => uint256) public pendingRewards;\n"
        "// function claimReward() external {\n"
        "//   uint256 amount = pendingRewards[msg.sender];\n"
        "//   pendingRewards[msg.sender] = 0;\n"
        "//   payable(msg.sender).transfer(amount);\n"
        "// }"
    ),
    "WG-SOL-ZERO-001": (
        "// ✅ Add zero address checks to critical functions:\n"
        "// require(newOwner != address(0), 'zero address');\n"
        "// require(token != address(0), 'zero token');\n"
        "// require(recipient != address(0), 'zero recipient');"
    ),
    "WG-SOL-DEPR-001": (
        "// ❌ AVOID transfer() and send() — they forward 2300 gas (breaks with multisig/contract receivers):\n"
        "// payable(recipient).transfer(amount); // RISKY\n\n"
        "// ✅ USE call with success check:\n"
        "// (bool ok, ) = payable(recipient).call{value: amount}('');\n"
        "// require(ok, 'ETH transfer failed');"
    ),
    "WG-SOL-FRONT-001": (
        "// ❌ VULNERABLE: predictable outcome before tx mines:\n"
        "// function buy(uint256 price) external { require(price >= currentPrice); }\n\n"
        "// ✅ ADD slippage tolerance + deadline:\n"
        "// function buy(uint256 maxPrice, uint256 deadline) external {\n"
        "//   require(block.timestamp <= deadline, 'expired');\n"
        "//   require(currentPrice <= maxPrice, 'slippage exceeded');\n"
        "// }"
    ),
    "WG-SOL-LOCK-001": (
        "// Contract accepts ETH (payable) but has no withdrawal function.\n"
        "// ✅ Add an emergency withdrawal:\n"
        "// function rescueETH() external onlyOwner {\n"
        "//   (bool ok,) = msg.sender.call{value: address(this).balance}('');\n"
        "//   require(ok);\n"
        "// }"
    ),
    "WG-SOL-EQ-001": (
        "// ❌ AVOID strict equality on balances/block numbers:\n"
        "// require(address(this).balance == TARGET); // can be blocked\n\n"
        "// ✅ USE >= comparisons:\n"
        "// require(address(this).balance >= TARGET, 'insufficient');"
    ),
    "WG-SOL-SHADOW-001": (
        "// ❌ Local variable shadows state variable:\n"
        "// uint256 public owner; // state\n"
        "// function fn() { uint256 owner = 1; } // shadows!\n\n"
        "// ✅ Rename to avoid confusion:\n"
        "// function fn() { uint256 localOwner = 1; }"
    ),
}


def _randomness_and_dos_checks(code: str, findings: list[Finding], idx: int) -> int:
    # Weak randomness
    if re.search(r"blockhash|block\.timestamp|block\.difficulty|block\.prevrandao", code):
        line, _ = first_match_line(code, r"blockhash|block\.timestamp|block\.difficulty")
        snippet = line_text(code, line)
        # Only flag if used in arithmetic/modulo (likely randomness)
        if re.search(r"(blockhash|block\.timestamp|block\.difficulty)\s*[\)%\*\+\-]|%\s*\w+\s*;", code):
            _add_unique(findings, _finding(
                idx, severity="high",
                title="Weak Randomness — block.timestamp / blockhash",
                description="The contract uses block.timestamp or blockhash as a source of randomness. Miners can manipulate these values within a small window.",
                line=line, code=snippet,
                business="Lottery, NFT mint order, or game outcomes can be predicted or manipulated by miners, undermining fairness.",
                dev="block.timestamp and blockhash are not cryptographically secure randomness sources. Use commit-reveal or a verifiable randomness provider.",
                fix=_INLINE_FIXES["WG-SOL-RAND-001"],
                confidence="medium", category="randomness", rule_id="WG-SOL-RAND-001",
                references=["SWC-120 Weak Sources of Randomness", "Chainlink VRF documentation"],
            ))
            idx += 1

    # DoS — unbounded loop
    if re.search(r"for\s*\(.*\.length", code):
        line, _ = first_match_line(code, r"for\s*\(.*\.length")
        snippet = line_text(code, line)
        _add_unique(findings, _finding(
            idx, severity="medium",
            title="Unbounded Loop — Denial of Service Risk",
            description="A loop iterates over a dynamic-length array. If the array grows large, the transaction will exceed the block gas limit and permanently revert.",
            line=line, code=snippet,
            business="A DoS via gas exhaustion can permanently freeze distribution, staking rewards, or governance functions.",
            dev="Avoid loops over user-controlled or unbounded arrays. Use pull-over-push (claimable mappings) or paginated processing.",
            fix=_INLINE_FIXES["WG-SOL-DOS-001"],
            confidence="medium", category="dos", rule_id="WG-SOL-DOS-001",
            references=["SWC-128 DoS With Block Gas Limit", "Pull-over-push pattern"],
        ))
        idx += 1
    return idx


def _zero_address_and_deprecated_checks(code: str, findings: list[Finding], idx: int) -> int:
    # Missing zero-address check on owner/address params
    if re.search(r"function\s+\w+\s*\([^)]*address\s+\w+", code):
        if not re.search(r"address\(0\)|address(0)", code):
            line, _ = first_match_line(code, r"function\s+\w+\s*\([^)]*address\s+\w+")
            snippet = line_text(code, line)
            _add_unique(findings, _finding(
                idx, severity="low",
                title="Missing Zero-Address Check on Address Parameter",
                description="Functions accept address parameters but do not check for address(0). Accidentally passing zero address can lock funds or break ownership.",
                line=line, code=snippet,
                business="Sending to zero address burns tokens permanently. Setting owner to zero address locks all admin functions forever.",
                dev="Add require(param != address(0), 'zero address') at the start of functions that accept critical address arguments.",
                fix=_INLINE_FIXES["WG-SOL-ZERO-001"],
                confidence="medium", category="validation", rule_id="WG-SOL-ZERO-001",
                references=["SWC-115 Authorization through tx.origin"],
            ))
            idx += 1

    # Deprecated transfer/send
    if re.search(r"\.\s*transfer\s*\(|\.\s*send\s*\(", code):
        line, _ = first_match_line(code, r"\.\s*transfer\s*\(|\.\s*send\s*\(")
        snippet = line_text(code, line)
        _add_unique(findings, _finding(
            idx, severity="medium",
            title="Use of Deprecated .transfer() / .send() — 2300 Gas Limit Risk",
            description=".transfer() and .send() forward only 2300 gas. Since EIP-1884 increased gas costs, contracts that receive ETH (multisigs, smart wallets) will fail.",
            line=line, code=snippet,
            business="Payments to multisig wallets, smart contract wallets, or any receiver with logic will silently fail, blocking withdrawals.",
            dev="Replace .transfer()/.send() with .call{value:}('') and handle the return value explicitly.",
            fix=_INLINE_FIXES["WG-SOL-DEPR-001"],
            confidence="high", category="compatibility", rule_id="WG-SOL-DEPR-001",
            references=["SWC-134 Message call with hardcoded gas", "EIP-1884"],
        ))
        idx += 1
    return idx


def _frontrunning_and_locked_ether(code: str, findings: list[Finding], idx: int) -> int:
    # Front-running: function with price param but no deadline/slippage
    if re.search(r"function\s+\w*(buy|sell|swap|mint|bid)\w*\s*\([^)]*uint", code, re.IGNORECASE):
        if not re.search(r"deadline|expiry|maxPrice|minAmount|slippage", code, re.IGNORECASE):
            line, _ = first_match_line(code, r"function\s+\w*(buy|sell|swap|mint|bid)\w*\s*\(", flags=re.IGNORECASE)
            snippet = line_text(code, line)
            _add_unique(findings, _finding(
                idx, severity="medium",
                title="Potential Front-Running — Missing Deadline / Slippage Protection",
                description="Trade, mint, or auction functions lack deadline or slippage parameters. Bots can observe the mempool and insert transactions at worse prices.",
                line=line, code=snippet,
                business="Users receive worse prices than expected. MEV bots extract value directly from user transactions.",
                dev="Add a deadline timestamp check and a maxPrice/minAmountOut parameter so users can set acceptable bounds.",
                fix=_INLINE_FIXES["WG-SOL-FRONT-001"],
                confidence="low", category="mev", rule_id="WG-SOL-FRONT-001",
                references=["MEV and front-running protection patterns", "Uniswap deadline pattern"],
            ))
            idx += 1

    # Locked ether: payable function(s) but no withdrawal
    has_payable = bool(re.search(r"\bpayable\b", code))
    has_withdraw = bool(re.search(r"function\s+\w*(withdraw|rescue|reclaim|pull)\w*", code, re.IGNORECASE))
    if has_payable and not has_withdraw:
        _add_unique(findings, _finding(
            idx, severity="high",
            title="Locked Ether — Payable Contract Has No Withdrawal Function",
            description="The contract accepts ETH via payable functions but does not have a function to withdraw ETH. Funds sent to this contract may be permanently locked.",
            line=None, code=None,
            business="Any ETH accidentally sent or intentionally deposited cannot be recovered. This is a common cause of permanent fund loss.",
            dev="Add an authorized withdrawal function or ensure payable is only on functions that consume the ETH immediately.",
            fix=_INLINE_FIXES["WG-SOL-LOCK-001"],
            confidence="medium", category="funds", rule_id="WG-SOL-LOCK-001",
            references=["SWC-132 Unexpected Ether Balance"],
        ))
        idx += 1
    return idx


def _equality_and_shadowing_checks(code: str, findings: list[Finding], idx: int) -> int:
    # Dangerous equality on balance
    if re.search(r"==\s*address\(this\)\.balance|\.balance\s*==", code):
        line, _ = first_match_line(code, r"==\s*address\(this\)\.balance|\.balance\s*==")
        snippet = line_text(code, line)
        _add_unique(findings, _finding(
            idx, severity="medium",
            title="Dangerous Strict Equality on Contract Balance",
            description="Using == to compare contract balance is risky. An attacker can selfdestruct a contract and forcefully send ETH to change the balance, breaking the invariant.",
            line=line, code=snippet,
            business="Logic gated on exact balance (== TARGET) can be broken by sending 1 wei, permanently locking or bypassing contract state.",
            dev="Replace == balance check with >= comparison. Do not gate critical logic on exact ETH balance.",
            fix=_INLINE_FIXES["WG-SOL-EQ-001"],
            confidence="medium", category="logic", rule_id="WG-SOL-EQ-001",
            references=["SWC-132 Unexpected Ether Balance"],
        ))
        idx += 1

    # State variable shadowing (local var same name as state)
    state_vars = re.findall(r"^\s+(?:uint\d*|int\d*|address|bool|bytes\d*|string)\s+public\s+(\w+)", code, re.MULTILINE)
    for var in state_vars:
        pattern = rf"function\s+\w+[^{{]*\{{[^}}]*(?:uint\d*|int\d*|address|bool)\s+{re.escape(var)}\s*="
        if re.search(pattern, code, re.DOTALL):
            _add_unique(findings, _finding(
                idx, severity="low",
                title=f"State Variable Shadowing — '{var}'",
                description=f"A local variable named '{var}' inside a function shadows the state variable of the same name. This can cause subtle logic bugs.",
                line=None, code=None,
                business="Shadowing causes developers to accidentally read/write local variable instead of intended state, creating hidden logic errors.",
                dev=f"Rename local variable to avoid collision with state variable '{var}'.",
                fix=_INLINE_FIXES["WG-SOL-SHADOW-001"],
                confidence="low", category="logic", rule_id="WG-SOL-SHADOW-001",
                references=["SWC-119 Shadowing State Variables"],
            ))
            idx += 1
            break
    return idx


# ── 6 More Advanced Rules — v3.1 ─────────────────────────────────────────────

def _rug_pull_pattern_checks(code: str, findings: list[Finding], idx: int) -> int:
    """Detect rug pull risk patterns: hidden mint, owner drain, liquidity trap."""

    # Owner can drain liquidity / sweep all ETH without condition
    if re.search(r"function\s+\w*(?:sweep|drain|rugpull|emergency|withdraw[Aa]ll|ownerWithdraw)\w*\s*\([^)]*\)\s*(?:external|public)\s*(?:onlyOwner|onlyAdmin)", code, re.IGNORECASE):
        line, _ = first_match_line(code, r"function\s+\w*(?:sweep|drain|emergency|withdraw[Aa]ll|ownerWithdraw)\w*", flags=re.IGNORECASE)
        _add_unique(findings, _finding(
            idx, severity="high",
            title="Owner Drain / Emergency Sweep Function",
            description="The contract has a function that allows the owner to withdraw all ETH or tokens without restriction. This is a common rug pull vector.",
            line=line, code=line_text(code, line),
            business="Investors and users can lose all funds if the owner calls this function. Exchanges and launchpads will flag this as a rug pull risk.",
            dev="Add a timelock delay, community governance, or hard limit (e.g., max 10% of liquidity). Document the emergency use case clearly.",
            fix="// Add timelock: require(block.timestamp >= lastSweepRequest + 48 hours);\n// Or remove function and use multisig governance instead.",
            confidence="high", category="rug_pull", rule_id="WG-SOL-RUG-001",
            references=["Token Sniffer rug pull patterns", "GoPlus token security API"],
        ))
        idx += 1

    # Mint with no max supply cap
    has_mint = bool(re.search(r"function\s+\w*mint\w*\s*\([^)]*address[^)]*uint", code, re.IGNORECASE))
    has_max_supply = bool(re.search(r"maxSupply|MAX_SUPPLY|totalSupply\s*\+\s*amount\s*<=|cap\s*=", code, re.IGNORECASE))
    if has_mint and not has_max_supply:
        _add_unique(findings, _finding(
            idx, severity="medium",
            title="Mint Function Without Supply Cap",
            description="The contract has a public or permissioned mint function but no maximum supply enforcement in the minting logic.",
            line=None, code=None,
            business="Unlimited mint authority allows token dilution at any time, destroying token value. Investors expect a hard supply cap.",
            dev="Add: require(totalSupply() + amount <= MAX_SUPPLY, 'cap exceeded'); in the mint function.",
            fix="// Add to mint function:\nuint256 public constant MAX_SUPPLY = 1_000_000 * 1e18;\nrequire(totalSupply() + amount <= MAX_SUPPLY, 'Cap exceeded');",
            confidence="medium", category="rug_pull", rule_id="WG-SOL-RUG-002",
            references=["ERC20 supply cap best practices"],
        ))
        idx += 1

    return idx


def _gas_and_storage_checks(code: str, findings: list[Finding], idx: int) -> int:
    """Gas inefficiency patterns that cost users real money."""

    # Multiple SLOAD of same variable in loop
    if re.search(r"for\s*\([^)]+\)\s*\{[^}]*storage[^}]*\}", code, re.DOTALL):
        _add_unique(findings, _finding(
            idx, severity="info",
            title="Potential Storage Read in Loop — Gas Optimization",
            description="Reading from storage inside a loop costs 2100 gas per read. Caching in a local variable saves significant gas.",
            line=None, code=None,
            business="Higher gas costs mean users pay more per transaction. For high-frequency operations this can make your dApp unusable.",
            dev="Cache storage reads before the loop: uint256 _total = total; then use _total inside the loop.",
            fix="// ❌ EXPENSIVE:\n// for(uint i=0; i<arr.length; i++) { total += storageVar; }\n// ✅ CACHE:\n// uint256 _storageVar = storageVar;\n// for(uint i=0; i<arr.length; i++) { total += _storageVar; }",
            confidence="low", category="gas", rule_id="WG-SOL-GAS-003",
            references=["Solidity gas optimization patterns"],
        ))
        idx += 1

    # Using string in events/mappings (expensive vs bytes32)
    if re.search(r"mapping\s*\(\s*string", code):
        _add_unique(findings, _finding(
            idx, severity="info",
            title="String Used as Mapping Key — Use bytes32 for Gas Savings",
            description="Using string as a mapping key is more expensive than bytes32 because strings are dynamically sized.",
            line=None, code=None,
            business="Higher deployment and interaction costs — especially noticeable for registry or name-based contracts.",
            dev="Replace mapping(string => ...) with mapping(bytes32 => ...) and use keccak256(abi.encodePacked(name)) as the key.",
            fix="// ❌ mapping(string => address) public registry;\n// ✅ mapping(bytes32 => address) public registry;\n// Usage: registry[keccak256(abi.encodePacked(name))]",
            confidence="medium", category="gas", rule_id="WG-SOL-GAS-004",
            references=["Solidity storage layout optimization"],
        ))
        idx += 1

    return idx


def _compliance_and_disclosure_checks(code: str, findings: list[Finding], idx: int) -> int:
    """Regulatory compliance hints — FATF, India VDA, MiCA relevant."""

    # No KYC/AML hook in token contract (compliance disclosure)
    if re.search(r"pragma solidity", code, re.IGNORECASE):
        has_compliance = bool(re.search(r"kyc|aml|whitelist|isKYCed|verified|compliance", code, re.IGNORECASE))
        is_token = bool(re.search(r"ERC20|IERC20|transfer\s*\(|balanceOf", code))
        if is_token and not has_compliance and "DeFi" not in (code[:200]):
            _add_unique(findings, _finding(
                idx, severity="info",
                title="No KYC/Compliance Hook — Regulatory Disclosure",
                description="This token contract has no KYC/AML or compliance hook. In regulated jurisdictions (India VDA framework, EU MiCA), token issuers may need to implement compliance controls.",
                line=None, code=None,
                business="Without any compliance hook, this token may face regulatory challenges in India (PMLA/VDA rules) and EU (MiCA 2024) for public offerings.",
                dev="Consider adding a compliance hook interface that can be activated by governance if required. Document your legal opinion on token classification.",
                fix="// Optional compliance hook (can be no-op initially):\n// function _beforeTokenTransfer(address from, address to, uint256 amount) internal virtual {\n//   if (complianceContract != address(0)) ICompliance(complianceContract).check(from, to, amount);\n// }",
                confidence="low", category="compliance", rule_id="WG-SOL-COMP-001",
                references=["India VDA framework 2023", "EU MiCA Regulation 2024", "FATF guidance on virtual assets"],
            ))
            idx += 1

    return idx


# ══════════════════════════════════════════════════════════════════════════════
# ADVANCED RULE ENGINE v3.2 — 15 new rules — No competitor has all of these
# ══════════════════════════════════════════════════════════════════════════════

def _cross_function_reentrancy(code: str, findings: list[Finding], idx: int) -> int:
    """Cross-function reentrancy — harder to detect, often missed by basic tools."""
    has_state_write_after_call = bool(
        re.search(r"\.call\{[^}]*\}|\.call\(", code) and
        re.search(r"balances\[|balance\[|_balance|userBalance|credited\[|shares\[", code)
    )
    funcs = extract_functions(code)
    if len(funcs) >= 2 and has_state_write_after_call:
        if not re.search(r"nonReentrant|ReentrancyGuard|_status\s*=\s*_ENTERED", code):
            _add_unique(findings, _finding(
                idx, severity="high",
                title="Cross-Function Reentrancy Risk — No ReentrancyGuard",
                description="Multiple functions share state variables and external calls exist. Without ReentrancyGuard, a malicious contract can re-enter a different function before state is settled.",
                line=None, code=None,
                business="Cross-function reentrancy is harder to spot than simple reentrancy but equally devastating — attacker can drain funds across multiple function calls in one transaction.",
                dev="Import OpenZeppelin ReentrancyGuard and add nonReentrant modifier to all state-changing functions that involve external calls or token transfers.",
                fix="// ✅ Fix:\nimport '@openzeppelin/contracts/security/ReentrancyGuard.sol';\ncontract YourContract is ReentrancyGuard {\n  function withdraw() external nonReentrant {\n    // your logic\n  }\n}",
                confidence="medium", category="reentrancy", rule_id="WG-SOL-REENT-003",
                references=["Cross-function reentrancy attacks", "The DAO hack analysis", "OpenZeppelin ReentrancyGuard"],
            ))
            idx += 1
    return idx


def _arbitrary_transferfrom(code: str, findings: list[Finding], idx: int) -> int:
    """Arbitrary from address in transferFrom — common DeFi exploit."""
    if re.search(r"transferFrom\s*\(\s*\w+\s*,", code):
        # Check if the 'from' address comes from a parameter (not msg.sender or this)
        if re.search(r"transferFrom\s*\(\s*(?!msg\.sender|address\(this\))\w+", code):
            line, _ = first_match_line(code, r"transferFrom\s*\(")
            _add_unique(findings, _finding(
                idx, severity="critical",
                title="Arbitrary transferFrom — Attacker Can Drain Any Approved Wallet",
                description="transferFrom is called with a user-controlled 'from' address. If any user has approved this contract, an attacker can drain their tokens by passing the victim as 'from'.",
                line=line, code=line_text(code, line),
                business="This is one of the most dangerous DeFi patterns. Attacker passes victim address as 'from' and drains their entire approved balance. Responsible for multiple $1M+ exploits.",
                dev="Always use msg.sender as the 'from' address in transferFrom, or verify that the caller is the token owner or has explicit permission.",
                fix="// ❌ DANGEROUS:\n// token.transferFrom(userAddress, dest, amount); // userAddress is attacker-controlled\n// ✅ SAFE:\n// token.transferFrom(msg.sender, dest, amount); // always use caller",
                confidence="high", category="access_control", rule_id="WG-SOL-ARBTRF-001",
                references=["SWC-105 Unprotected Ether Withdrawal", "Arbitrary transferFrom exploit pattern"],
            ))
            idx += 1
    return idx


def _price_manipulation_same_tx(code: str, findings: list[Finding], idx: int) -> int:
    """Same-transaction price manipulation using spot prices."""
    if re.search(r"getReserves\(\)|reserve0|reserve1|getAmountsOut|token0\.balanceOf|balanceOf\(address\(this\)\)", code):
        if re.search(r"function\s+\w*(?:borrow|deposit|mint|swap|liquidat|flash)\w*", code, re.IGNORECASE):
            line, _ = first_match_line(code, r"getReserves\(\)|getAmountsOut|balanceOf\(address\(this\)\)")
            _add_unique(findings, _finding(
                idx, severity="critical",
                title="Spot Price Used in DeFi Logic — Price Manipulation Risk",
                description="The contract reads spot reserves or balance for pricing inside a DeFi function. Flash loans can manipulate these values within the same transaction.",
                line=line, code=line_text(code, line),
                business="Price manipulation attacks have caused $100M+ in losses. Attacker uses flash loan to skew the spot price, executes a trade at manipulated price, repays loan — profit extracted from your protocol.",
                dev="Never use spot reserves as a price oracle for critical calculations. Use a TWAP (time-weighted average price) from Uniswap V3, or a trusted external oracle like Chainlink.",
                fix="// ❌ AVOID spot price:\n// (uint r0, uint r1,) = pair.getReserves();\n// uint price = r1 / r0;\n// ✅ USE TWAP or Chainlink:\n// uint price = oracle.getTWAP(token, 30 minutes);",
                confidence="medium", category="defi", rule_id="WG-SOL-PRICE-001",
                references=["Flash loan price manipulation", "TWAP oracle pattern", "Chainlink price feeds"],
            ))
            idx += 1
    return idx


def _integer_overflow_old_solidity(code: str, findings: list[Finding], idx: int) -> int:
    """Integer overflow — relevant for pre-0.8.0 or unchecked blocks."""
    pragma_match = re.search(r"pragma solidity\s+[^;]+;", code)
    if pragma_match:
        pragma_str = pragma_match.group()
        is_old = bool(re.search(r"0\.[0-7]\.", pragma_str))
        if is_old:
            if re.search(r"\+\s*\d|\*\s*\d|uint\d*\s+\w+\s*=\s*\w+\s*\+", code):
                _add_unique(findings, _finding(
                    idx, severity="critical",
                    title="Integer Overflow/Underflow — Pre-0.8.0 Solidity",
                    description="This contract uses a Solidity version older than 0.8.0 which does NOT have built-in overflow protection. Integer overflow/underflow can silently wrap around.",
                    line=None, code=None,
                    business="Classic token hack: attacker subtracts more tokens than they have, balance wraps to max uint256, they now have infinite tokens. This is SWC-101 — responsible for many early DeFi hacks.",
                    dev="Either upgrade to Solidity 0.8.x (overflow checked by default) or import OpenZeppelin SafeMath library for all arithmetic operations.",
                    fix="// Option 1: Upgrade pragma\npragma solidity ^0.8.0; // overflow protection built-in\n\n// Option 2 (if stuck on old version):\nusing SafeMath for uint256;\nuint256 result = a.add(b); // reverts on overflow",
                    confidence="high", category="math", rule_id="WG-SOL-OVFL-001",
                    references=["SWC-101 Integer Overflow and Underflow", "OpenZeppelin SafeMath"],
                ))
                idx += 1
    return idx


def _governance_attack_checks(code: str, findings: list[Finding], idx: int) -> int:
    """Governance flash loan attacks and vote manipulation."""
    has_governance = bool(re.search(r"function\s+\w*(?:vote|propose|execute|castVote|queue)\w*", code, re.IGNORECASE))
    has_token_balance_check = bool(re.search(r"balanceOf|getVotes|getPriorVotes|votingPower", code, re.IGNORECASE))
    if has_governance and has_token_balance_check:
        if not re.search(r"getPriorVotes|getPastVotes|checkpoints|block\.number\s*-\s*1", code):
            _add_unique(findings, _finding(
                idx, severity="high",
                title="Governance — Snapshot Missing, Flash Loan Vote Attack Possible",
                description="The governance contract checks token balance at vote time without a historical snapshot. An attacker can flash-borrow governance tokens, vote, and repay in one transaction.",
                line=None, code=None,
                business="Governance flash loan attack: borrow 51% of tokens, pass malicious proposal, drain treasury, repay loan — all in one transaction. Has drained multiple DAOs.",
                dev="Use ERC20Votes with getPastVotes(voter, block.number - 1) instead of current balanceOf. Lock voting power at proposal creation block.",
                fix="// ✅ Use snapshot-based voting:\n// import '@openzeppelin/contracts/governance/Governor.sol';\n// Uses getPastVotes(account, proposalSnapshot) automatically",
                confidence="medium", category="governance", rule_id="WG-SOL-GOV-001",
                references=["Governance flash loan attacks", "Compound Governor Bravo", "OpenZeppelin Governor"],
            ))
            idx += 1
    return idx


def _erc20_return_value_check(code: str, findings: list[Finding], idx: int) -> int:
    """ERC20 tokens that don't return bool (USDT, BNB) — unsafe transfer."""
    if re.search(r"\.transfer\s*\(|\.transferFrom\s*\(|\.approve\s*\(", code):
        if not re.search(r"SafeERC20|safeTransfer|safeTransferFrom|safeApprove|IERC20", code):
            if re.search(r"USDT|Tether|BNB|BEP20|ERC20\s*token\s*=|IERC20\s+\w+\s*=", code, re.IGNORECASE):
                line, _ = first_match_line(code, r"\.transfer\s*\(|\.transferFrom\s*\(")
                _add_unique(findings, _finding(
                    idx, severity="high",
                    title="Unsafe ERC20 Transfer — Use SafeERC20",
                    description="Direct .transfer()/.transferFrom() calls on ERC20 tokens like USDT do not return bool. The call silently fails without reverting, causing accounting errors.",
                    line=line, code=line_text(code, line),
                    business="USDT and some BNB tokens do not return bool on transfer. Your contract may think a transfer succeeded when it silently failed, leading to fund loss or accounting corruption.",
                    dev="Use OpenZeppelin SafeERC20.safeTransfer() and safeTransferFrom() which handles both returning and non-returning ERC20 tokens correctly.",
                    fix="// ❌ UNSAFE:\n// token.transfer(to, amount);\n// ✅ SAFE:\nimport '@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol';\nusing SafeERC20 for IERC20;\ntoken.safeTransfer(to, amount);",
                    confidence="medium", category="compatibility", rule_id="WG-SOL-ERC20-001",
                    references=["SafeERC20 pattern", "USDT non-standard ERC20 behavior", "SWC-104"],
                ))
                idx += 1
    return idx


def _missing_event_on_critical_ops(code: str, findings: list[Finding], idx: int) -> int:
    """Missing events on ownership transfer, fee changes, critical parameter updates."""
    critical_setters = re.findall(
        r"function\s+(set\w+|update\w+|change\w+|modify\w+)\s*\([^)]*\)\s*(?:external|public)(?:\s+onlyOwner|\s+onlyAdmin)?",
        code, re.IGNORECASE
    )
    for fn_name in critical_setters[:3]:  # Check first 3
        fn_pattern = rf"function\s+{re.escape(fn_name)}\s*\([^{{]*\{{([^}}]*)\}}"
        fn_match = re.search(fn_pattern, code, re.DOTALL | re.IGNORECASE)
        if fn_match:
            fn_body = fn_match.group(1)
            if not re.search(r"emit\s+\w+", fn_body):
                _add_unique(findings, _finding(
                    idx, severity="medium",
                    title=f"Missing Event in {fn_name}() — Off-Chain Monitoring Blind",
                    description=f"The function {fn_name}() makes state changes but emits no event. Block explorers, monitoring tools, and users cannot track these changes.",
                    line=None, code=None,
                    business="Investors and users cannot detect silent changes to fees, addresses, or protocol parameters. This is a transparency and audit trail gap.",
                    dev=f"Add an event definition and emit it inside {fn_name}() whenever a critical parameter changes.",
                    fix=f"// Add event:\nevent {fn_name[0].upper()}{fn_name[1:]}Updated(address indexed by, /* params */);\n// Emit in function:\nemit {fn_name[0].upper()}{fn_name[1:]}Updated(msg.sender, /* params */);",
                    confidence="medium", category="observability", rule_id="WG-SOL-EVT-004",
                    references=["Solidity event best practices", "OpenZeppelin auditing events"],
                ))
                idx += 1
                break
    return idx


def _centralized_bridge_risk(code: str, findings: list[Finding], idx: int) -> int:
    """Bridge contracts with centralized validator or single signer."""
    is_bridge = bool(re.search(r"bridge|crosschain|cross.chain|l2|relay|deposit.*withdraw|lock.*unlock", code, re.IGNORECASE))
    if is_bridge:
        if re.search(r"require\s*\(\s*msg\.sender\s*==\s*(?:owner|validator|relayer|operator)", code, re.IGNORECASE):
            if not re.search(r"threshold|multisig|signatures\s*>=|require.*\d\s*signatures", code, re.IGNORECASE):
                _add_unique(findings, _finding(
                    idx, severity="critical",
                    title="Bridge with Single Validator — Centralization Attack Risk",
                    description="This bridge contract has a single validator or relayer. If the validator key is compromised, all bridged funds can be drained instantly.",
                    line=None, code=None,
                    business="The Ronin bridge ($625M hack) used 5 of 9 validators. A single-validator bridge can be drained by compromising one key. This is the highest-severity bridge risk.",
                    dev="Implement multi-signature threshold validation. Require M of N validators to sign bridge transactions. Use a time-delay for large withdrawals.",
                    fix="// Require multiple signatures:\nrequire(validSignatures >= threshold, 'insufficient signatures');\n// Add large withdrawal delay:\nif (amount > LARGE_AMOUNT) require(block.timestamp >= requestTime + 24 hours);",
                    confidence="medium", category="centralization", rule_id="WG-SOL-BRIDGE-001",
                    references=["Ronin Bridge hack $625M", "Multi-sig bridge patterns", "EIP-2535 Diamond standard"],
                ))
                idx += 1
    return idx


def _nft_reentrancy_on_transfer(code: str, findings: list[Finding], idx: int) -> int:
    """NFT reentrancy via onERC721Received callback."""
    if re.search(r"ERC721|_safeMint|_safeTransfer|safeTransferFrom|onERC721Received", code):
        has_state_before_mint = bool(re.search(r"_safeMint|_safeTransfer", code))
        if has_state_before_mint and not re.search(r"nonReentrant|ReentrancyGuard", code):
            line, _ = first_match_line(code, r"_safeMint|_safeTransfer")
            _add_unique(findings, _finding(
                idx, severity="high",
                title="NFT Reentrancy via onERC721Received Callback",
                description="_safeMint and _safeTransfer call onERC721Received on the recipient if it's a contract. Without ReentrancyGuard, the recipient can re-enter mint/transfer during this callback.",
                line=line, code=line_text(code, line),
                business="NFT reentrancy allows minting more NFTs than the maxSupply limit by re-entering during the onERC721Received callback. Several NFT projects have been exploited this way.",
                dev="Add nonReentrant modifier to all mint and transfer functions. Update all state (tokenCount, ownership records) BEFORE calling _safeMint.",
                fix="import '@openzeppelin/contracts/security/ReentrancyGuard.sol';\n// Add nonReentrant to mint:\nfunction mint() external payable nonReentrant {\n  require(totalSupply() < maxSupply, 'sold out');\n  _safeMint(msg.sender, ++tokenId);\n}",
                confidence="medium", category="reentrancy", rule_id="WG-SOL-NFT-002",
                references=["NFT reentrancy via onERC721Received", "OpenZeppelin ReentrancyGuard", "Fomo3D reentrancy"],
            ))
            idx += 1
    return idx


def _immutable_and_constant_checks(code: str, findings: list[Finding], idx: int) -> int:
    """Gas savings: state vars set once should be immutable."""
    # Find state variables assigned only in constructor
    constructor_only = re.findall(
        r"address\s+(?:public\s+)?(\w+)\s*;", code
    )
    for var in constructor_only[:5]:
        # Check it's set in constructor and not elsewhere
        set_in_constructor = bool(re.search(
            rf"constructor[^{{]*\{{[^}}]*{re.escape(var)}\s*=",
            code, re.DOTALL
        ))
        set_elsewhere = bool(re.search(
            rf"function\s+\w+[^{{]*\{{[^}}]*{re.escape(var)}\s*=",
            code, re.DOTALL
        ))
        is_immutable = bool(re.search(rf"address\s+immutable\s+{re.escape(var)}", code))
        if set_in_constructor and not set_elsewhere and not is_immutable and var not in ('owner',):
            _add_unique(findings, _finding(
                idx, severity="info",
                title=f"Variable '{var}' Should Be immutable — Gas Optimization",
                description=f"The address variable '{var}' is only set in the constructor and never changed. Marking it as 'immutable' saves ~2100 gas per read (SLOAD vs hardcoded in bytecode).",
                line=None, code=None,
                business="Lower gas costs make your dApp cheaper to use. For frequently-called functions, this can save users significant cumulative gas.",
                dev=f"Change 'address public {var}' to 'address public immutable {var}'. Works for any value set only in constructor.",
                fix=f"// ❌ CURRENT:\naddress public {var};\n// ✅ BETTER:\naddress public immutable {var}; // saves ~2100 gas per read",
                confidence="low", category="gas", rule_id="WG-SOL-GAS-005",
                references=["Solidity immutable keyword", "EVM SLOAD gas costs", "Gas optimization patterns"],
            ))
            idx += 1
            break
    return idx


def _eip712_domain_separator_checks(code: str, findings: list[Finding], idx: int) -> int:
    """EIP-712 domain separator missing chainId — replay on forks."""
    if re.search(r"DOMAIN_SEPARATOR|domainSeparator|EIP712|_hashTypedData", code):
        if not re.search(r"block\.chainid|chainId|CHAIN_ID", code, re.IGNORECASE):
            _add_unique(findings, _finding(
                idx, severity="high",
                title="EIP-712 Domain Separator Missing chainId — Fork Replay Risk",
                description="The EIP-712 domain separator does not include chainId. Signed messages are valid on all forks of this chain, enabling cross-chain replay attacks.",
                line=None, code=None,
                business="If Ethereum forks (like ETH/ETC split), signatures created on one chain are valid on the other. Attackers can replay signatures on the forked chain to drain funds.",
                dev="Always include chainId in EIP-712 domain separator. Use block.chainid (Solidity 0.8.x) or the assembly chainid() opcode.",
                fix="// ✅ Include chainId in domain:\nbytes32 DOMAIN_SEPARATOR = keccak256(abi.encode(\n  keccak256('EIP712Domain(string name,string version,uint256 chainId,address verifyingContract)'),\n  keccak256(bytes(name)),\n  keccak256(bytes('1')),\n  block.chainid, // ← required\n  address(this)\n));",
                confidence="high", category="signature", rule_id="WG-SOL-SIG-002",
                references=["EIP-712 domain separator specification", "Replay attack protection"],
            ))
            idx += 1
    return idx


def _multicall_reentrancy(code: str, findings: list[Finding], idx: int) -> int:
    """Multicall + reentrancy combo — msg.value reuse attack."""
    if re.search(r"multicall|multiCall|multiExecute|batchExecute", code, re.IGNORECASE):
        if re.search(r"msg\.value", code):
            if not re.search(r"nonReentrant|_checkMsgValue|valueUsed", code):
                _add_unique(findings, _finding(
                    idx, severity="critical",
                    title="Multicall with msg.value — ETH Reuse Attack Vector",
                    description="A multicall function that uses msg.value allows attackers to reuse the same ETH across multiple calls in one transaction, effectively multiplying their payment.",
                    line=None, code=None,
                    business="Attacker sends 1 ETH via multicall, executes 5 deposit calls each claiming 1 ETH. Protocol credits 5 ETH but only received 1 ETH. Uniswap's Universal Router addressed this specifically.",
                    dev="Never use msg.value inside a loop or multicall. Track ETH value explicitly per call with a local variable, not msg.value.",
                    fix="// ❌ DANGEROUS:\n// function multicall(bytes[] calldata data) external payable {\n//   for (uint i = 0; i < data.length; i++) {\n//     (bool ok,) = address(this).delegatecall(data[i]); // msg.value reused!\n// ✅ SAFE: Use Uniswap V3's approach — pass value per call, not globally",
                    confidence="medium", category="defi", rule_id="WG-SOL-MULTI-001",
                    references=["Uniswap multicall msg.value bug", "msg.value in loops", "Smart contract security pitfalls"],
                ))
                idx += 1
    return idx
