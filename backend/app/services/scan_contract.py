import re
from datetime import datetime, timezone

from app.models.schemas import Finding, ModuleScore, ScanResponse
from app.services.scoring import priority_actions, risk_label, score_findings, severity_breakdown
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

ENGINE_VERSION = "web3guard-solidity-rule-engine-v2.0"

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
        {"id": "WG-SOL-RAND-001", "name": "Weak randomness/time dependency", "category": "randomness"},
        {"id": "WG-SOL-ADMIN-001", "name": "Owner/admin centralization", "category": "centralization"},
        {"id": "WG-SOL-ADMIN-002", "name": "Hardcoded privileged address", "category": "centralization"},
        {"id": "WG-SOL-UPGRADE-001", "name": "Upgradeable proxy review", "category": "upgradeability"},
        {"id": "WG-SOL-UPGRADE-002", "name": "Initializer protection", "category": "upgradeability"},
        {"id": "WG-SOL-EVENT-001", "name": "Sensitive function no event", "category": "observability"},
        {"id": "WG-SOL-GAS-001", "name": "Unbounded loop", "category": "gas"},
        {"id": "WG-SOL-TOKEN-001", "name": "ERC20 approve education", "category": "token_standard"},
    ]
