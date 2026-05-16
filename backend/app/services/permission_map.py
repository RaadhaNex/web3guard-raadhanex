from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from typing import Any

from app.models.schemas import Finding, ModuleScore, ScanResponse
from app.services.scoring import priority_actions, risk_label, score_findings, severity_breakdown
from app.services.solidity_utils import all_match_lines, extract_functions, line_text, sha12

ENGINE_VERSION = "web3guard-permission-map-engine-v1.0-phase16"

CAPABILITY_RULES = [
    {
        "key": "owner_admin",
        "label": "Owner / primary admin",
        "source_patterns": [r"\bonlyOwner\b", r"\bOwnable\b", r"\bowner\s*\(", r"\b_owner\b", r"\btransferOwnership\s*\("],
        "abi_names": ["owner", "transferOwnership", "renounceOwnership"],
        "controller_hint": "owner / onlyOwner",
        "risk": "medium",
        "recommendation": "Disclose the owner address, use a multisig for production, and document ownership-transfer/renounce policy.",
    },
    {
        "key": "role_admin",
        "label": "Role administrator",
        "source_patterns": [r"DEFAULT_ADMIN_ROLE", r"\bgrantRole\s*\(", r"\brevokeRole\s*\(", r"\bsetRoleAdmin\s*\("],
        "abi_names": ["grantRole", "revokeRole", "renounceRole", "getRoleAdmin", "DEFAULT_ADMIN_ROLE"],
        "controller_hint": "AccessControl role admin",
        "risk": "high",
        "recommendation": "Use a multisig/timelock for role admin powers and keep an audit log of grants/revocations.",
    },
    {
        "key": "minter",
        "label": "Mint / supply controller",
        "source_patterns": [r"MINTER_ROLE", r"\bmint\s*\(", r"\bsafeMint\s*\(", r"\bairdrop\s*\("],
        "abi_names": ["mint", "safeMint", "airdrop"],
        "controller_hint": "minter / owner / role",
        "risk": "high",
        "recommendation": "Define max supply, mint authority, mint pause conditions, and disclose who can mint after launch.",
    },
    {
        "key": "pauser",
        "label": "Pause / emergency controller",
        "source_patterns": [r"PAUSER_ROLE", r"\bPausable\b", r"\bpause\s*\(", r"\bunpause\s*\(", r"whenNotPaused"],
        "abi_names": ["pause", "unpause", "paused"],
        "controller_hint": "pauser / owner / role",
        "risk": "medium",
        "recommendation": "Publish the emergency-pause policy and ensure pause/unpause powers are multisig-governed.",
    },
    {
        "key": "upgrader",
        "label": "Upgrade / proxy controller",
        "source_patterns": [r"UPGRADER_ROLE", r"\bUUPSUpgradeable\b", r"\bTransparentUpgradeableProxy\b", r"\bBeaconProxy\b", r"\bupgradeTo\s*\(", r"\bupgradeToAndCall\s*\(", r"\b_authorizeUpgrade\s*\("],
        "abi_names": ["upgradeTo", "upgradeToAndCall", "implementation", "admin", "changeAdmin"],
        "controller_hint": "proxy admin / upgrader",
        "risk": "high",
        "recommendation": "Use multisig + timelock for upgrades, document proxy type, and compare storage layout before upgrades.",
    },
    {
        "key": "treasury",
        "label": "Treasury / withdrawal controller",
        "source_patterns": [r"\btreasury\b", r"\bfeeReceiver\b", r"\bwithdraw\s*\(", r"\bsweep\s*\(", r"\brescue\s*\(", r"\bwithdrawERC20\s*\("],
        "abi_names": ["treasury", "setTreasury", "withdraw", "sweep", "rescue", "withdrawERC20"],
        "controller_hint": "treasury / owner / finance admin",
        "risk": "medium",
        "recommendation": "Separate deployer, treasury, and operations wallets. Publish treasury wallet and withdrawal rules where appropriate.",
    },
    {
        "key": "blacklist_freeze",
        "label": "Blacklist / freeze controller",
        "source_patterns": [r"blacklist", r"blocklist", r"\bfreeze\b", r"\bunfreeze\b", r"isBlacklisted", r"frozen"],
        "abi_names": ["blacklist", "blocklist", "freeze", "unfreeze", "setBlacklist", "isBlacklisted"],
        "controller_hint": "compliance / admin role",
        "risk": "medium",
        "recommendation": "Disclose freeze/blacklist powers clearly. Define governance and emergency-use conditions before launch.",
    },
    {
        "key": "fee_manager",
        "label": "Fee / tax controller",
        "source_patterns": [r"\bsetFee\s*\(", r"\bsetTax\s*\(", r"\bsetBuyTax\s*\(", r"\bsetSellTax\s*\(", r"\btaxFee\b", r"\bfeeBps\b"],
        "abi_names": ["setFee", "setTax", "setBuyTax", "setSellTax", "feeBps", "taxFee"],
        "controller_hint": "fee manager / owner",
        "risk": "medium",
        "recommendation": "Add maximum fee caps, events, delay/timelock for fee changes, and public disclosure of fee-change powers.",
    },
    {
        "key": "oracle_admin",
        "label": "Oracle / price-feed controller",
        "source_patterns": [r"\bsetOracle\s*\(", r"\bupdateOracle\s*\(", r"\bpriceFeed\b", r"\bAggregatorV3Interface\b", r"\boracle\b"],
        "abi_names": ["setOracle", "updateOracle", "priceFeed", "oracle"],
        "controller_hint": "oracle admin / owner",
        "risk": "high",
        "recommendation": "Use trusted oracle sources, document oracle-change authority, and add timelock/manual review for oracle updates.",
    },
]


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _report_id(project_name: str | None) -> str:
    suffix = sha12(project_name or str(_now())).upper()
    return f"W3G-PERM-{suffix}-{_now().strftime('%Y%m%d%H%M%S')}"


def permission_map_status() -> dict[str, Any]:
    return {
        "ok": True,
        "version": "1.0",
        "engine_version": ENGINE_VERSION,
        "mode": "read_only_static_source_and_abi_analysis",
        "live_capabilities": [
            "Solidity source role/capability detection",
            "ABI function capability detection",
            "manual owner/treasury/multisig/timelock facts",
            "centralization risk score",
            "founder transparency disclosure checklist",
            "No wallet connection, no private key collection, no on-chain mutation",
        ],
        "not_claimed": [
            "Does not prove the live owner is a multisig without explorer/on-chain provider integration",
            "Does not certify governance safety",
            "Does not replace manual audit or legal disclosure review",
        ],
    }


def _parse_abi(abi_json: str | None) -> list[dict[str, Any]]:
    if not abi_json or not abi_json.strip():
        return []
    try:
        parsed = json.loads(abi_json)
    except json.JSONDecodeError as exc:
        raise ValueError("ABI JSON is invalid. Paste a verified ABI array or explorer ABI JSON string.") from exc
    if isinstance(parsed, str):
        try:
            parsed = json.loads(parsed)
        except json.JSONDecodeError:
            return []
    if isinstance(parsed, dict):
        for key in ("abi", "ABI", "result"):
            if key in parsed:
                return _parse_abi(json.dumps(parsed[key]))
        return []
    if not isinstance(parsed, list):
        return []
    return [item for item in parsed if isinstance(item, dict)]


def _abi_function_names(abi: list[dict[str, Any]]) -> set[str]:
    names: set[str] = set()
    for item in abi:
        if item.get("type") in {"function", "event"} and item.get("name"):
            names.add(str(item["name"]))
    return names


def _find_capabilities(solidity_code: str | None, abi_json: str | None, manual: dict[str, Any]) -> list[dict[str, Any]]:
    code = solidity_code or ""
    abi = _parse_abi(abi_json)
    abi_names = _abi_function_names(abi)
    functions = extract_functions(code) if code else []
    capabilities: list[dict[str, Any]] = []

    for rule in CAPABILITY_RULES:
        evidence: list[dict[str, Any]] = []
        for pattern in rule["source_patterns"]:
            for line_no, match in all_match_lines(code, pattern):
                fn = next((item for item in functions if item.start_line <= line_no <= item.end_line), None)
                evidence.append({
                    "type": "source",
                    "line": line_no,
                    "function": fn.name if fn else None,
                    "snippet": line_text(code, line_no),
                    "pattern": pattern,
                })
                if len(evidence) >= 8:
                    break
            if len(evidence) >= 8:
                break

        abi_matches = sorted(name for name in abi_names if any(name.lower() == target.lower() for target in rule["abi_names"]))
        for name in abi_matches[:8]:
            evidence.append({"type": "abi", "function": name, "snippet": f"ABI exposes {name}()"})

        if evidence:
            controller = _controller_for_capability(rule["key"], code, manual)
            capabilities.append({
                "key": rule["key"],
                "label": rule["label"],
                "status": "detected",
                "controller_hint": controller,
                "default_controller_hint": rule["controller_hint"],
                "risk_level": rule["risk"],
                "evidence": evidence,
                "recommendation": rule["recommendation"],
            })

    if manual.get("owner_address") and not any(item["key"] == "owner_admin" for item in capabilities):
        capabilities.insert(0, {
            "key": "owner_admin",
            "label": "Owner / primary admin",
            "status": "manual",
            "controller_hint": f"manual owner address: {manual['owner_address']}",
            "default_controller_hint": "manual owner address",
            "risk_level": "medium",
            "evidence": [{"type": "manual", "snippet": "Owner address provided by user."}],
            "recommendation": "Verify whether this owner is a multisig/timelock-controlled address before launch.",
        })
    if manual.get("treasury_address") and not any(item["key"] == "treasury" for item in capabilities):
        capabilities.append({
            "key": "treasury",
            "label": "Treasury / withdrawal controller",
            "status": "manual",
            "controller_hint": f"manual treasury address: {manual['treasury_address']}",
            "default_controller_hint": "manual treasury address",
            "risk_level": "medium",
            "evidence": [{"type": "manual", "snippet": "Treasury address provided by user."}],
            "recommendation": "Keep treasury separate from deployer/admin wallet and publish withdrawal policy where appropriate.",
        })
    return capabilities


def _controller_for_capability(key: str, code: str, manual: dict[str, Any]) -> str:
    owner = manual.get("owner_address")
    treasury = manual.get("treasury_address")
    if key == "treasury" and treasury:
        return f"treasury address: {treasury}"
    if owner and key in {"owner_admin", "minter", "pauser", "upgrader", "role_admin", "fee_manager", "blacklist_freeze", "oracle_admin"}:
        return f"likely owner/admin controlled: {owner}"
    if re.search(r"\bonlyRole\s*\(", code or "", flags=re.IGNORECASE):
        return "role-based controller detected; verify role holders manually"
    if re.search(r"\bonlyOwner\b", code or "", flags=re.IGNORECASE):
        return "owner-controlled; owner address must be verified"
    return "controller identity not verified from provided input"


def _make_finding(idx: int, *, severity: str, title: str, description: str, category: str, rule_id: str, confidence: str, evidence: dict[str, Any] | None, business: str, dev: str, fix: str) -> Finding:
    line = evidence.get("line") if evidence else None
    snippet = evidence.get("snippet") if evidence else None
    fn = evidence.get("function") if evidence else None
    return Finding(
        id=f"permission-map-{idx:03d}",
        module="permission_map",  # type: ignore[arg-type]
        severity=severity,  # type: ignore[arg-type]
        title=title,
        description=description,
        affected_line=line,
        affected_function=fn,
        affected_code=snippet,
        confidence=confidence,  # type: ignore[arg-type]
        source="Web3Guard Permission Map Engine v1",
        category=category,
        rule_id=rule_id,
        fingerprint=sha12(f"{rule_id}:{line}:{snippet}"),
        business_impact=business,
        developer_explanation=dev,
        recommendation=fix,
        references=["OpenZeppelin AccessControl/Ownable", "Multisig + timelock governance review", "Founder transparency disclosure"],
        paid_review_recommended=severity in {"critical", "high"},
    )


def _build_findings(capabilities: list[dict[str, Any]], manual: dict[str, Any], code: str | None, abi_json: str | None) -> list[Finding]:
    findings: list[Finding] = []
    idx = 1
    keys = {item["key"] for item in capabilities}
    high_power_keys = keys & {"minter", "upgrader", "role_admin", "oracle_admin"}
    admin_like_count = len(keys & {"owner_admin", "role_admin", "minter", "pauser", "upgrader", "treasury", "blacklist_freeze", "fee_manager", "oracle_admin"})
    has_multisig = manual.get("multisig_enabled") is True if manual.get("multisig_enabled") is not None else bool(re.search(r"multisig|gnosis|safe", manual.get("governance_notes") or "", re.IGNORECASE))
    has_timelock = manual.get("timelock_enabled") is True if manual.get("timelock_enabled") is not None else bool(re.search(r"timelock|delay", (manual.get("governance_notes") or "") + "\n" + (code or ""), re.IGNORECASE))

    if admin_like_count >= 3 and not has_multisig:
        findings.append(_make_finding(
            idx,
            severity="high",
            title="Multiple privileged capabilities without multisig evidence",
            description="The provided input shows several privileged powers, but no multisig evidence was provided.",
            category="centralization",
            rule_id="WG-PERM-CENT-001",
            confidence="high" if manual.get("multisig_enabled") is False else "medium",
            evidence=capabilities[0]["evidence"][0] if capabilities and capabilities[0].get("evidence") else None,
            business="A compromised or mismanaged admin key could affect supply, upgrades, treasury, or user trust.",
            dev="Centralized admin capabilities should be controlled through multisig and documented operational procedures.",
            fix="Move privileged roles to a multisig, document signers, and add launch disclosure before public release.",
        ))
        idx += 1

    if high_power_keys and not has_timelock:
        findings.append(_make_finding(
            idx,
            severity="medium",
            title="High-impact admin actions lack timelock evidence",
            description="Minting, upgrade, role-admin, or oracle powers were detected, but no timelock/delay evidence was provided.",
            category="centralization",
            rule_id="WG-PERM-CENT-002",
            confidence="medium",
            evidence=next((item["evidence"][0] for item in capabilities if item["key"] in high_power_keys and item.get("evidence")), None),
            business="Users and partners may have no time to react to sensitive admin changes.",
            dev="Timelocks make privileged changes observable before they execute.",
            fix="Add a timelock or publish an explicit no-timelock risk disclosure for privileged functions.",
        ))
        idx += 1

    for cap in capabilities:
        first_evidence = cap["evidence"][0] if cap.get("evidence") else None
        if cap["key"] == "minter":
            findings.append(_make_finding(
                idx,
                severity="high",
                title="Mint authority requires supply transparency",
                description="Mint capability was detected from source/ABI/manual input.",
                category="supply_control",
                rule_id="WG-PERM-MINT-001",
                confidence="high",
                evidence=first_evidence,
                business="Unexpected minting can dilute holders and damage launch trust.",
                dev="Mint authority should be capped, role-controlled, event-logged, and documented.",
                fix="Add max supply/role controls, disclose mint policy, and prefer multisig-controlled minting.",
            ))
            idx += 1
        elif cap["key"] == "upgrader":
            findings.append(_make_finding(
                idx,
                severity="high",
                title="Upgradeable contract authority needs governance review",
                description="Upgrade/proxy capability was detected.",
                category="upgradeability",
                rule_id="WG-PERM-UPGRADE-001",
                confidence="high",
                evidence=first_evidence,
                business="An unsafe upgrade can replace logic, alter user funds, or break integrations.",
                dev="Upgrade authority, proxy pattern, storage layout, and initializer controls require dedicated review.",
                fix="Use multisig + timelock upgrade admin, document proxy type, and run storage-layout comparison before upgrades.",
            ))
            idx += 1
        elif cap["key"] == "blacklist_freeze":
            findings.append(_make_finding(
                idx,
                severity="medium",
                title="Blacklist/freeze powers need public disclosure",
                description="Blacklist, blocklist, or freeze capability was detected.",
                category="transparency",
                rule_id="WG-PERM-FREEZE-001",
                confidence="medium",
                evidence=first_evidence,
                business="Users may treat undisclosed freeze powers as a trust and compliance risk.",
                dev="Freeze/blacklist logic should be tightly scoped, event-logged, and role-controlled.",
                fix="Document when this power can be used, who controls it, and how users can verify actions.",
            ))
            idx += 1
        elif cap["key"] == "fee_manager":
            findings.append(_make_finding(
                idx,
                severity="medium",
                title="Fee/tax controls require caps and events",
                description="Fee or tax setter capability was detected.",
                category="economic_control",
                rule_id="WG-PERM-FEE-001",
                confidence="medium",
                evidence=first_evidence,
                business="Uncapped fee changes can create holder/investor trust issues.",
                dev="Economic parameters should have max caps, event emission, and preferably timelock governance.",
                fix="Add fee caps, emit update events, and publish fee-change governance rules.",
            ))
            idx += 1
        elif cap["key"] == "oracle_admin":
            findings.append(_make_finding(
                idx,
                severity="high",
                title="Oracle admin power can create economic attack risk",
                description="Oracle or price-feed control capability was detected.",
                category="oracle_control",
                rule_id="WG-PERM-ORACLE-001",
                confidence="medium",
                evidence=first_evidence,
                business="Unsafe oracle changes can impact pricing, liquidations, rewards, and protocol solvency.",
                dev="Oracle authority should be multisig/timelock controlled and validated by integration tests.",
                fix="Document oracle sources, restrict update authority, add timelock/manual review, and monitor oracle-change events.",
            ))
            idx += 1
        elif cap["key"] == "treasury":
            findings.append(_make_finding(
                idx,
                severity="medium",
                title="Treasury/withdrawal authority must be separated and disclosed",
                description="Treasury or withdrawal control was detected.",
                category="treasury_control",
                rule_id="WG-PERM-TREASURY-001",
                confidence="medium",
                evidence=first_evidence,
                business="Treasury key compromise or unclear withdrawal policy can affect funds and trust.",
                dev="Treasury withdrawals should be role-controlled, event-logged, and separated from deployer/admin keys.",
                fix="Use dedicated treasury multisig, publish withdrawal rules, and add event monitoring.",
            ))
            idx += 1

    if capabilities and not manual.get("owner_address"):
        findings.append(_make_finding(
            idx,
            severity="info",
            title="Controller addresses not provided",
            description="Privileged capabilities were detected, but owner/admin/treasury addresses were not provided in the scan request.",
            category="transparency",
            rule_id="WG-PERM-DISCLOSE-001",
            confidence="high",
            evidence=None,
            business="A launch report is incomplete unless privileged controller addresses are disclosed or verified.",
            dev="Source code can show permissions, but live controller addresses must be verified from deployment/on-chain state.",
            fix="Add owner/admin/treasury addresses or run the contract address scanner when explorer/on-chain data is available.",
        ))

    if not capabilities and (code or abi_json):
        findings.append(_make_finding(
            idx,
            severity="info",
            title="No privileged capability detected from provided input",
            description="The permission-map engine did not detect common owner/minter/pauser/upgrader/treasury patterns.",
            category="coverage",
            rule_id="WG-PERM-COVERAGE-001",
            confidence="low",
            evidence=None,
            business="This does not prove there are no privileged controls; manual review is still needed.",
            dev="Heuristic source/ABI parsing can miss custom authorization patterns.",
            fix="Review custom modifiers, inherited contracts, deployment scripts, and verified on-chain role holders.",
        ))
    return findings


def _centralization_report(capabilities: list[dict[str, Any]], manual: dict[str, Any], findings: list[Finding]) -> dict[str, Any]:
    score = score_findings(findings)
    keys = [item["key"] for item in capabilities]
    high_risk_count = sum(1 for item in capabilities if item.get("risk_level") == "high")
    has_multisig = manual.get("multisig_enabled") is True if manual.get("multisig_enabled") is not None else bool(re.search(r"multisig|gnosis|safe", manual.get("governance_notes") or "", re.IGNORECASE))
    has_timelock = manual.get("timelock_enabled") is True if manual.get("timelock_enabled") is not None else bool(re.search(r"timelock|delay", manual.get("governance_notes") or "", re.IGNORECASE))
    if score >= 85:
        label = "Low centralization risk from provided evidence"
    elif score >= 70:
        label = "Moderate centralization risk"
    elif score >= 50:
        label = "High centralization risk"
    else:
        label = "Critical centralization risk"
    return {
        "centralization_score": score,
        "centralization_label": label,
        "capability_count": len(capabilities),
        "high_risk_capability_count": high_risk_count,
        "detected_capabilities": keys,
        "multisig_evidence": bool(has_multisig),
        "timelock_evidence": bool(has_timelock),
        "manual_owner_address_provided": bool(manual.get("owner_address")),
        "manual_treasury_address_provided": bool(manual.get("treasury_address")),
        "real_only_note": "This score is based only on provided source/ABI/manual facts. Live owner role holders require contract address/on-chain/explorer verification.",
    }


def _transparency_report(capabilities: list[dict[str, Any]], manual: dict[str, Any]) -> dict[str, Any]:
    detected = {item["key"] for item in capabilities}
    disclosures: list[str] = []
    missing: list[str] = []
    checks = [
        ("owner_admin", "Publish owner/admin address and whether it is multisig-controlled."),
        ("minter", "Publish mint policy, max supply, and who can mint."),
        ("upgrader", "Publish proxy type, upgrade authority, and timelock/multisig policy."),
        ("pauser", "Publish emergency-pause policy and who can unpause."),
        ("blacklist_freeze", "Publish freeze/blacklist policy and allowed use cases."),
        ("fee_manager", "Publish fee/tax maximums and change process."),
        ("treasury", "Publish treasury wallet and withdrawal process where appropriate."),
        ("oracle_admin", "Publish oracle sources and who can update them."),
    ]
    for key, text in checks:
        if key in detected:
            missing.append(text)
        else:
            disclosures.append(f"No common {key.replace('_', ' ')} capability detected from provided evidence.")
    if manual.get("governance_notes"):
        disclosures.append("Governance notes provided by user; manual reviewer should verify them against deployment/on-chain facts.")
    return {"required_disclosures": missing, "positive_notes": disclosures[:6], "manual_review_note": "Founder transparency report is not legal advice and should be reviewed before public publication."}


def build_permission_map(
    *,
    project_name: str | None,
    solidity_code: str | None,
    abi_json: str | None,
    contract_address: str | None,
    chain: str | None,
    owner_address: str | None,
    treasury_address: str | None,
    multisig_enabled: bool | None,
    timelock_enabled: bool | None,
    governance_notes: str | None,
) -> ScanResponse:
    if not (solidity_code and solidity_code.strip()) and not (abi_json and abi_json.strip()) and not owner_address and not treasury_address:
        raise ValueError("Provide Solidity source, ABI JSON, or manual owner/treasury facts to build a real permission map. No fake permission map will be generated.")

    manual = {
        "owner_address": owner_address.strip() if owner_address else None,
        "treasury_address": treasury_address.strip() if treasury_address else None,
        "multisig_enabled": multisig_enabled,
        "timelock_enabled": timelock_enabled,
        "governance_notes": governance_notes or "",
    }
    capabilities = _find_capabilities(solidity_code, abi_json, manual)
    findings = _build_findings(capabilities, manual, solidity_code, abi_json)
    score = score_findings(findings)
    metadata = {
        "version": "1.0-current",
        "contract_address": contract_address,
        "chain": chain,
        "permission_map": {"capabilities": capabilities},
        "centralization_report": _centralization_report(capabilities, manual, findings),
        "founder_transparency_report": _transparency_report(capabilities, manual),
        "coverage": {
            "source_provided": bool(solidity_code),
            "abi_provided": bool(abi_json),
            "manual_owner_provided": bool(owner_address),
            "manual_treasury_provided": bool(treasury_address),
            "assessed_from_real_input": True,
        },
        "real_only_note": "No role holder is invented. Unknown controllers remain unknown until explorer/on-chain/manual evidence is supplied.",
    }
    input_material = json.dumps({
        "source": solidity_code or "",
        "abi": abi_json or "",
        "contract_address": contract_address or "",
        "chain": chain or "",
        "owner_address": owner_address or "",
        "treasury_address": treasury_address or "",
        "governance_notes": governance_notes or "",
    }, sort_keys=True)
    return ScanResponse(
        report_id=_report_id(project_name),
        generated_at=_now(),
        project_name=project_name,
        module_score=ModuleScore(module="permission_map", score=score, risk_label=risk_label(score), assessed=True),  # type: ignore[arg-type]
        findings=findings,
        severity_breakdown=severity_breakdown(findings),
        priority_actions=priority_actions(findings),
        input_hash=_hash(input_material),
        engine_version=ENGINE_VERSION,
        scan_metadata=metadata,
        disclaimer="This is a preliminary permission and centralization review. It does not prove live role holders and does not replace manual audit, governance review, or legal disclosure review.",
    )
