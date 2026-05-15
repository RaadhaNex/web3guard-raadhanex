from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone
from typing import Any

from app.models.schemas import Finding, ModuleScore, ScanResponse
from app.services.scoring import priority_actions, risk_label, score_findings, severity_breakdown
from app.services.solidity_utils import all_match_lines, extract_functions, line_text, sha12

ENGINE_VERSION = "web3guard-upgrade-safety-engine-v1.0-megaA"

PROXY_PATTERNS = [
    ("uups", [r"UUPSUpgradeable", r"_authorizeUpgrade", r"upgradeTo\s*\(", r"upgradeToAndCall\s*\("]),
    ("transparent", [r"TransparentUpgradeableProxy", r"ProxyAdmin", r"changeAdmin\s*\("]),
    ("beacon", [r"BeaconProxy", r"UpgradeableBeacon", r"implementation\s*\("]),
    ("minimal_proxy", [r"Clones", r"cloneDeterministic", r"EIP1167"]),
]

STATE_VAR_RE = re.compile(r"^\s*(?:mapping\s*\([^;]+\)|(?:address|uint\d*|int\d*|bool|string|bytes\d*|bytes))\s+(?:public\s+|private\s+|internal\s+|constant\s+|immutable\s+)*([A-Za-z_][A-Za-z0-9_]*)", re.MULTILINE)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _report_id(project_name: str | None) -> str:
    return f"W3G-UPGRADE-{sha12((project_name or 'upgrade') + str(_now()))}-{_now().strftime('%Y%m%d%H%M%S')}".upper()


def upgrade_safety_status() -> dict[str, Any]:
    return {
        "ok": True,
        "phase": "Mega Phase A - Phase 19 Upgrade Safety Analyzer",
        "engine_version": ENGINE_VERSION,
        "mode": "read_only_proxy_initializer_storage_hints",
        "live_capabilities": [
            "Proxy pattern hints: UUPS, Transparent, Beacon, minimal proxy",
            "Initializer/reinitializer safety checks",
            "Upgrade authorization hints",
            "Old/new storage variable order comparison when both versions are provided",
        ],
        "not_claimed": [
            "Does not replace compiler-generated storage layout JSON",
            "Does not prove upgrade is safe",
            "Does not deploy, upgrade, sign, or connect to admin wallets",
        ],
    }


def _detect_proxy_types(code: str) -> list[dict[str, Any]]:
    detected = []
    for key, patterns in PROXY_PATTERNS:
        evidence = []
        for pattern in patterns:
            for line_no, _ in all_match_lines(code, pattern):
                evidence.append({"line": line_no, "snippet": line_text(code, line_no), "pattern": pattern})
                break
        if evidence:
            detected.append({"type": key, "evidence": evidence})
    return detected


def _state_vars(code: str) -> list[dict[str, Any]]:
    vars_: list[dict[str, Any]] = []
    for match in STATE_VAR_RE.finditer(code):
        line_no = code[: match.start()].count("\n") + 1
        line = line_text(code, line_no)
        # Skip function/local lines and constants likely not storage layout relevant.
        if "function " in line or " event " in line or " error " in line:
            continue
        vars_.append({"name": match.group(1), "line": line_no, "snippet": line})
    return vars_[:120]


def _make_finding(idx: int, *, severity: str, title: str, description: str, category: str, rule_id: str, line: int | None = None, snippet: str | None = None, business: str, dev: str, fix: str, confidence: str = "medium") -> Finding:
    return Finding(
        id=f"upgrade-safety-{idx:03d}",
        module="upgrade_safety",  # type: ignore[arg-type]
        severity=severity,  # type: ignore[arg-type]
        title=title,
        description=description,
        affected_line=line,
        affected_code=snippet,
        confidence=confidence,  # type: ignore[arg-type]
        source="Web3Guard Upgrade Safety Engine v1",
        category=category,
        rule_id=rule_id,
        fingerprint=hashlib.sha1(f"{rule_id}:{line}:{snippet}".encode()).hexdigest()[:16],
        business_impact=business,
        developer_explanation=dev,
        recommendation=fix,
        paid_review_recommended=severity in {"critical", "high", "medium"},
    )


def build_upgrade_safety_report(
    *,
    project_name: str | None,
    current_code: str,
    previous_code: str | None,
    proxy_admin_notes: str | None,
    ownership_verified: bool,
) -> ScanResponse:
    if len(current_code.strip()) < 20:
        raise ValueError("Current Solidity source is required. No fake upgrade-safety report will be generated.")
    if len(current_code) + len(previous_code or "") > 420000:
        raise ValueError("Upgrade safety input is too large for MVP scanner limits.")

    proxy_types = _detect_proxy_types(current_code)
    functions = extract_functions(current_code)
    findings: list[Finding] = []
    idx = 1

    if not proxy_types:
        findings.append(_make_finding(
            idx,
            severity="info",
            title="No proxy pattern detected from provided source",
            description="The scanner did not detect common upgrade proxy patterns. This may be a non-upgradeable contract or source may be incomplete.",
            category="proxy_detection",
            rule_id="UPGRADE_NO_PROXY_DETECTED",
            business="If the project is upgradeable, missing proxy evidence means the launch report is incomplete.",
            dev="Provide proxy/implementation/admin source or explorer metadata for better assessment.",
            fix="If upgradeable, provide implementation + proxy/admin details and run this scan again.",
            confidence="low",
        ))
        idx += 1
    else:
        for proxy in proxy_types:
            ev = proxy["evidence"][0]
            findings.append(_make_finding(
                idx,
                severity="medium" if proxy["type"] != "uups" else "high",
                title=f"{proxy['type'].upper()} upgrade pattern detected",
                description=f"A {proxy['type']} upgrade pattern was detected. Upgrade admin, initializer safety, and storage layout need review.",
                category="proxy_detection",
                rule_id=f"UPGRADE_PROXY_{proxy['type'].upper()}",
                line=ev.get("line"),
                snippet=ev.get("snippet"),
                business="Upgradeable contracts can change behavior after launch and require strong governance disclosure.",
                dev="Confirm proxy admin, implementation address, upgrade authorization, and storage layout compatibility.",
                fix="Use multisig + timelock, publish upgrade policy, and compare storage layout before every upgrade.",
            ))
            idx += 1

    has_initializer = bool(re.search(r"\binitialize\s*\(", current_code))
    has_initializer_modifier = bool(re.search(r"\binitializer\b", current_code))
    has_disable_initializers = bool(re.search(r"_disableInitializers\s*\(", current_code))
    if proxy_types and not has_initializer:
        findings.append(_make_finding(
            idx, severity="high", title="Upgradeable pattern without visible initialize() function", description="Proxy-style contracts usually need initializer flow instead of constructor initialization.", category="initializer", rule_id="UPGRADE_INITIALIZER_MISSING", business="Incorrect initialization can leave contracts unusable or admin state unset.", dev="Review constructor/initializer pattern for upgradeable contracts.", fix="Use OpenZeppelin Initializable pattern and call initializer during deployment.", confidence="medium")); idx += 1
    if has_initializer and not has_initializer_modifier:
        line = next((ln for ln, _ in all_match_lines(current_code, r"\binitialize\s*\(")), None)
        findings.append(_make_finding(
            idx, severity="high", title="initialize() without initializer modifier evidence", description="An initialize() function was detected without clear initializer modifier evidence.", category="initializer", rule_id="UPGRADE_INITIALIZER_UNGUARDED", line=line, snippet=line_text(current_code, line) if line else None, business="An unguarded initializer can allow unauthorized re-initialization.", dev="Use initializer/reinitializer guards and disable initializers in implementation constructor when appropriate.", fix="Add initializer guard and test repeated initialize calls fail.", confidence="medium")); idx += 1
    if proxy_types and not has_disable_initializers:
        findings.append(_make_finding(
            idx, severity="medium", title="Implementation disable-initializers evidence not found", description="_disableInitializers() was not detected. Implementation contracts should usually lock initialization.", category="initializer", rule_id="UPGRADE_DISABLE_INITIALIZERS_MISSING", business="An unlocked implementation can create confusing or exploitable admin assumptions.", dev="OpenZeppelin recommends disabling initializers in implementation constructors for upgradeable implementations.", fix="Add constructor with _disableInitializers() where suitable and test proxy initialization separately.", confidence="low")); idx += 1

    if proxy_types and not re.search(r"_authorizeUpgrade\s*\(|onlyOwner|onlyRole|ProxyAdmin|DEFAULT_ADMIN_ROLE", current_code, re.I):
        findings.append(_make_finding(
            idx, severity="critical", title="Upgrade authorization evidence not found", description="Upgrade pattern detected but no clear upgrade authorization gate was found from provided source.", category="upgrade_authorization", rule_id="UPGRADE_AUTHORIZATION_MISSING", business="Unauthorized upgrades can fully compromise project logic and user funds.", dev="UUPS upgrades require _authorizeUpgrade access control; transparent proxies need secure ProxyAdmin ownership.", fix="Add strict upgrade authorization, multisig admin, timelock, and tests for unauthorized upgrade attempts.", confidence="medium")); idx += 1

    if proxy_admin_notes:
        lowered = proxy_admin_notes.lower()
        if "single" in lowered or "eoa" in lowered or "hot wallet" in lowered:
            findings.append(_make_finding(
                idx, severity="high", title="Proxy admin notes indicate single/hot wallet risk", description="Founder notes mention single signer/EOA/hot wallet style proxy admin risk.", category="proxy_admin", rule_id="UPGRADE_SINGLE_ADMIN_RISK", business="A compromised admin can upgrade implementation maliciously.", dev="Use a multisig/timelock for proxy admin ownership.", fix="Move proxy admin to multisig + timelock before public launch.", confidence="high")); idx += 1
        if "multisig" not in lowered:
            findings.append(_make_finding(
                idx, severity="medium", title="Proxy admin multisig evidence not provided", description="Proxy admin notes do not provide multisig evidence.", category="proxy_admin", rule_id="UPGRADE_MULTISIG_EVIDENCE_MISSING", business="Investors/users may ask who can upgrade the contract.", dev="Document admin address and signer policy.", fix="Publish multisig address or provide governance transition plan.", confidence="medium")); idx += 1

    current_vars = _state_vars(current_code)
    previous_vars = _state_vars(previous_code or "") if previous_code else []
    storage_changes: list[dict[str, Any]] = []
    if previous_vars:
        previous_names = [item["name"] for item in previous_vars]
        current_names = [item["name"] for item in current_vars]
        min_len = min(len(previous_names), len(current_names))
        for i in range(min_len):
            if previous_names[i] != current_names[i]:
                storage_changes.append({"slot_index_hint": i, "previous": previous_names[i], "current": current_names[i]})
        if len(current_names) < len(previous_names):
            storage_changes.append({"type": "storage_removed_or_shortened", "previous_count": len(previous_names), "current_count": len(current_names)})
        if storage_changes:
            findings.append(_make_finding(
                idx, severity="critical", title="Storage layout order changed between versions", description="Old/new state variable order appears changed. This is dangerous for upgradeable contracts.", category="storage_layout", rule_id="UPGRADE_STORAGE_LAYOUT_CHANGED", business="Storage collision can corrupt balances, ownership, treasury, or governance state after upgrade.", dev="Use compiler storage layout output for final verification; append new variables only and preserve order/types.", fix="Do not reorder/remove state variables. Generate storage layout JSON and compare before upgrade.", confidence="medium")); idx += 1
        elif len(current_names) > len(previous_names):
            findings.append(_make_finding(
                idx, severity="info", title="New storage variables appended", description="New state variables appear appended after previous variables. Still verify compiler storage layout.", category="storage_layout", rule_id="UPGRADE_STORAGE_APPENDED", business="Appending storage can be safe if order/types are preserved, but must be verified.", dev="Run compiler storage-layout comparison before upgrade.", fix="Confirm storage layout JSON and test upgrade migration.", confidence="low")); idx += 1

    score = score_findings(findings)
    return ScanResponse(
        report_id=_report_id(project_name),
        generated_at=_now(),
        project_name=project_name,
        module_score=ModuleScore(module="upgrade_safety", score=score, risk_label=risk_label(score)),  # type: ignore[arg-type]
        findings=findings,
        severity_breakdown=severity_breakdown(findings),
        priority_actions=priority_actions(findings),
        input_hash=_hash((previous_code or "") + "\n---CURRENT---\n" + current_code + "\n" + (proxy_admin_notes or "")),
        engine_version=ENGINE_VERSION,
        scan_metadata={
            "phase": "Mega Phase A / Phase 19",
            "real_only_note": "Read-only upgrade safety hints only. No deployment, signing, or certified storage proof.",
            "proxy_types_detected": proxy_types,
            "initializer_evidence": {"has_initialize": has_initializer, "has_initializer_modifier": has_initializer_modifier, "has_disable_initializers": has_disable_initializers},
            "storage_layout_hint": {"previous_variables": previous_vars, "current_variables": current_vars, "changes": storage_changes, "requires_compiler_storage_layout": True},
            "ownership_verified": ownership_verified,
            "manual_review_note": "For production upgrades, compare compiler storageLayout output and run manual review before execution.",
        },
    )
