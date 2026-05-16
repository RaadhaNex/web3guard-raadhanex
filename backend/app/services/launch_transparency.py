from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone
from typing import Any

from app.models.schemas import Finding, ModuleScore, ScanResponse
from app.services.scoring import priority_actions, risk_label, score_findings, severity_breakdown
from app.services.solidity_utils import all_match_lines, extract_functions, line_text, sha12

ENGINE_VERSION = "web3guard-launch-transparency-engine-v1.0-megaA"

PROJECT_CHECKLISTS: dict[str, list[str]] = {
    "erc20": [
        "max supply and mint authority disclosed",
        "owner/admin powers disclosed",
        "fee/tax caps disclosed",
        "pause/blacklist powers disclosed",
        "liquidity lock or treasury policy provided",
        "ownership/multisig/timelock plan documented",
    ],
    "nft": [
        "max supply disclosed",
        "mint/airdrop authority disclosed",
        "metadata mutability/freeze status disclosed",
        "royalty/admin powers disclosed",
        "withdrawal/treasury policy provided",
        "allowlist/claim mechanics documented",
    ],
    "staking": [
        "reward source and emission schedule disclosed",
        "admin reward update powers disclosed",
        "emergency withdrawal policy documented",
        "pause/admin/timelock controls disclosed",
        "treasury and fee receiver disclosed",
    ],
    "dao": [
        "proposal/voting rules disclosed",
        "timelock governance documented",
        "admin override powers disclosed",
        "quorum and flash-loan governance risks reviewed",
    ],
    "presale": [
        "sale caps and refund policy disclosed",
        "claim schedule documented",
        "treasury recipient disclosed",
        "owner pause/withdraw powers disclosed",
        "KYC/compliance limitations documented if relevant",
    ],
    "airdrop": [
        "claim contract address disclosed",
        "eligibility and merkle root update authority disclosed",
        "claim deadline and unclaimed-token policy disclosed",
        "signature/permit risks reviewed",
    ],
    "marketplace": [
        "fee recipient disclosed",
        "admin fee-change powers disclosed",
        "escrow/custody assumptions documented",
        "royalty policy disclosed",
    ],
}

TRANSPARENCY_RULES = [
    {
        "key": "unlimited_mint",
        "title": "Mint authority requires launch disclosure",
        "severity": "high",
        "category": "supply_control",
        "patterns": [r"\bmint\s*\(", r"\bsafeMint\s*\(", r"MINTER_ROLE"],
        "business": "Token/NFT buyers need to know who can increase supply after launch.",
        "dev": "Mint functions or minter roles were detected. Verify access control and publish max-supply/mint policy.",
        "fix": "Add hard caps where possible, emit events, require multisig/timelock for post-launch minting, and disclose mint authority.",
    },
    {
        "key": "pause_or_freeze",
        "title": "Pause/freeze powers require clear user disclosure",
        "severity": "medium",
        "category": "transfer_control",
        "patterns": [r"\bpause\s*\(", r"\bunpause\s*\(", r"Pausable", r"blacklist", r"blocklist", r"freeze"],
        "business": "Pause/freeze features can protect users during incidents, but can also stop transfers or claims.",
        "dev": "Emergency or compliance controls appear present. Review controller role and event logging.",
        "fix": "Publish emergency-use policy, ensure multisig/timelock where practical, and show these powers in the transparency report.",
    },
    {
        "key": "fee_tax_control",
        "title": "Fee/tax change authority needs cap and disclosure",
        "severity": "medium",
        "category": "economic_control",
        "patterns": [r"\bsetFee\s*\(", r"\bsetTax\s*\(", r"buyTax", r"sellTax", r"feeBps", r"taxFee"],
        "business": "Admin-controlled fees can materially change token economics after launch.",
        "dev": "Fee/tax variables or setters were detected. Check for max caps and events.",
        "fix": "Add maximum fee caps, delay sensitive changes, emit events, and disclose fee-change authority.",
    },
    {
        "key": "withdraw_treasury",
        "title": "Treasury/withdrawal controls need separation and policy",
        "severity": "medium",
        "category": "treasury_control",
        "patterns": [r"\bwithdraw\s*\(", r"\bsweep\s*\(", r"\brescue\s*\(", r"treasury", r"feeReceiver"],
        "business": "Treasury controls affect user funds, sale proceeds, fees, and recovery paths.",
        "dev": "Withdrawal/treasury-like code was detected. Confirm access control, recipient, and logging.",
        "fix": "Separate deployer/admin/treasury wallets, use multisig, and publish withdrawal/rescue policy.",
    },
    {
        "key": "upgradeable_control",
        "title": "Upgradeability must be disclosed before launch",
        "severity": "high",
        "category": "upgrade_control",
        "patterns": [r"UUPSUpgradeable", r"TransparentUpgradeableProxy", r"BeaconProxy", r"\bupgradeTo\s*\(", r"_authorizeUpgrade"],
        "business": "Upgradeable contracts can change logic after users trust the launch.",
        "dev": "Proxy/upgrade patterns were detected. Verify upgrade admin, initializer safety, and storage layout process.",
        "fix": "Use multisig + timelock for upgrades, publish proxy type/admin, and run storage-layout checks before upgrades.",
    },
    {
        "key": "metadata_mutability",
        "title": "NFT metadata mutability needs freeze/status disclosure",
        "severity": "medium",
        "category": "metadata_control",
        "patterns": [r"setBaseURI", r"baseURI", r"tokenURI", r"setURI", r"contractURI"],
        "business": "Mutable metadata can change collection appearance or trust assumptions after mint.",
        "dev": "Metadata URI controls were detected. Check who can update metadata and whether freeze is possible.",
        "fix": "Disclose metadata mutability, freeze plan, IPFS/Arweave storage, and admin controls.",
    },
    {
        "key": "allowlist_claim",
        "title": "Allowlist/claim mechanics require public rules",
        "severity": "low",
        "category": "claim_mechanics",
        "patterns": [r"merkleRoot", r"MerkleProof", r"claim\s*\(", r"allowlist", r"whitelist"],
        "business": "Users need clear eligibility, deadline, and claim safety information.",
        "dev": "Claim/allowlist patterns were detected. Review root update authority and replay/signature risks.",
        "fix": "Document eligibility source, root update controls, deadline, and unclaimed-token handling.",
    },
]


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _report_id(project_name: str | None) -> str:
    return f"W3G-TRANSPARENCY-{sha12((project_name or 'launch') + str(_now()))}-{_now().strftime('%Y%m%d%H%M%S')}".upper()


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def launch_transparency_status() -> dict[str, Any]:
    return {
        "ok": True,
        "version": "1.0",
        "engine_version": ENGINE_VERSION,
        "mode": "read_only_source_and_founder_input",
        "live_capabilities": [
            "Project-type launch checklist",
            "Source-based owner power disclosure hints",
            "Token/NFT centralization and admin-control transparency findings",
            "No rug-pull accusation, no legal/investment advice, no fake score without input",
        ],
        "not_claimed": [
            "Does not certify a token/NFT as safe",
            "Does not verify live liquidity locks without external proof",
            "Does not replace legal disclosure review or manual audit",
        ],
    }


def _project_type_key(project_type: str | None, code: str) -> str:
    raw = (project_type or "").lower()
    if "721" in code or "erc721" in code.lower() or "nft" in raw:
        return "nft"
    if "staking" in raw or re.search(r"\bstake\s*\(", code, re.I):
        return "staking"
    if "dao" in raw or "governance" in raw:
        return "dao"
    if "presale" in raw or "sale" in raw:
        return "presale"
    if "airdrop" in raw or "claim" in raw:
        return "airdrop"
    if "market" in raw:
        return "marketplace"
    return "erc20"


def _make_finding(idx: int, rule: dict[str, Any], line_no: int | None, fn: str | None, snippet: str | None) -> Finding:
    return Finding(
        id=f"launch-transparency-{idx:03d}",
        module="launch_transparency",  # type: ignore[arg-type]
        severity=rule["severity"],  # type: ignore[arg-type]
        title=rule["title"],
        description=f"{rule['title']} was identified from provided launch source/input. This is a transparency/disclosure finding, not a fraud accusation.",
        affected_line=line_no,
        affected_function=fn,
        affected_code=snippet,
        confidence="medium",
        source="Web3Guard Launch Transparency Engine v1",
        category=rule["category"],
        rule_id=f"TRANSPARENCY_{rule['key'].upper()}",
        fingerprint=hashlib.sha1(f"{rule['key']}:{line_no}:{snippet}".encode()).hexdigest()[:16],
        business_impact=rule["business"],
        developer_explanation=rule["dev"],
        recommendation=rule["fix"],
        references=["Founder disclosure checklist", "Pre-audit readiness scope"],
        paid_review_recommended=rule["severity"] in {"critical", "high", "medium"},
    )


def build_launch_transparency_report(
    *,
    project_name: str | None,
    project_type: str | None,
    solidity_code: str | None,
    website_text: str | None,
    tokenomics_notes: str | None,
    liquidity_lock_evidence: str | None,
    metadata_freeze_evidence: str | None,
    owner_power_notes: str | None,
    multisig_enabled: bool | None,
    timelock_enabled: bool | None,
) -> ScanResponse:
    combined_input = "\n".join(filter(None, [solidity_code, website_text, tokenomics_notes, liquidity_lock_evidence, metadata_freeze_evidence, owner_power_notes]))
    if not combined_input.strip():
        raise ValueError("No real launch transparency input provided. Paste Solidity code, website copy, tokenomics notes, or founder disclosures. No fake transparency report will be generated.")
    if len(combined_input) > 260000:
        raise ValueError("Launch transparency input is too large for MVP scanner limits.")

    code = solidity_code or ""
    text_blob = combined_input
    fns = extract_functions(code) if code else []
    findings: list[Finding] = []
    detected_controls: list[dict[str, Any]] = []
    idx = 1
    for rule in TRANSPARENCY_RULES:
        first_evidence: tuple[int | None, str | None, str | None] | None = None
        for pattern in rule["patterns"]:
            matched = False
            if code:
                for line_no, _ in all_match_lines(code, pattern):
                    fn = next((item for item in fns if item.start_line <= line_no <= item.end_line), None)
                    first_evidence = (line_no, fn.name if fn else None, line_text(code, line_no))
                    matched = True
                    break
            if not matched and re.search(pattern, text_blob, flags=re.IGNORECASE):
                first_evidence = (None, None, f"Founder/input text matched: {pattern}")
                matched = True
            if matched and first_evidence:
                findings.append(_make_finding(idx, rule, *first_evidence))
                detected_controls.append({"key": rule["key"], "title": rule["title"], "severity": rule["severity"], "evidence": first_evidence[2]})
                idx += 1
                break

    if multisig_enabled is False and detected_controls:
        findings.append(Finding(
            id=f"launch-transparency-{idx:03d}",
            module="launch_transparency",  # type: ignore[arg-type]
            severity="high",
            title="Privileged launch controls without multisig evidence",
            description="Founder input says multisig is not enabled while privileged controls were detected. This should be fixed or disclosed before launch.",
            confidence="high",
            source="Web3Guard Launch Transparency Engine v1",
            category="governance_controls",
            rule_id="TRANSPARENCY_MULTISIG_MISSING",
            fingerprint=hashlib.sha1(b"launch-transparency-multisig").hexdigest()[:16],
            business_impact="A single compromised EOA can control important launch powers.",
            developer_explanation="Move owner/admin roles to multisig or provide a clear governance transition plan.",
            recommendation="Use multisig for owner/admin roles before production launch and disclose signer policy.",
            paid_review_recommended=True,
        ))
        idx += 1
    if timelock_enabled is False and any(item["key"] in {"upgradeable_control", "fee_tax_control", "oracle_admin"} for item in detected_controls):
        findings.append(Finding(
            id=f"launch-transparency-{idx:03d}",
            module="launch_transparency",  # type: ignore[arg-type]
            severity="medium",
            title="Sensitive controls without timelock evidence",
            description="Fee/upgrade/oracle-style controls should normally include delay, governance, or public notice.",
            confidence="medium",
            source="Web3Guard Launch Transparency Engine v1",
            category="governance_controls",
            rule_id="TRANSPARENCY_TIMELOCK_MISSING",
            fingerprint=hashlib.sha1(b"launch-transparency-timelock").hexdigest()[:16],
            business_impact="Users may not have time to react to risky admin changes.",
            developer_explanation="Add timelock or documented governance process for sensitive post-launch changes.",
            recommendation="Use timelock for upgrades/fee/oracle updates or publish a clear emergency-only policy.",
            paid_review_recommended=True,
        ))

    checklist_key = _project_type_key(project_type, code + "\n" + text_blob)
    checklist = PROJECT_CHECKLISTS.get(checklist_key, PROJECT_CHECKLISTS["erc20"])
    provided_evidence = {
        "liquidity_lock_evidence_provided": bool((liquidity_lock_evidence or "").strip()),
        "metadata_freeze_evidence_provided": bool((metadata_freeze_evidence or "").strip()),
        "owner_power_notes_provided": bool((owner_power_notes or "").strip()),
        "tokenomics_notes_provided": bool((tokenomics_notes or "").strip()),
        "multisig_evidence": multisig_enabled,
        "timelock_evidence": timelock_enabled,
    }
    score = score_findings(findings)
    report_id = _report_id(project_name)
    return ScanResponse(
        report_id=report_id,
        generated_at=_now(),
        project_name=project_name,
        module_score=ModuleScore(module="launch_transparency", score=score, risk_label=risk_label(score)),  # type: ignore[arg-type]
        findings=findings,
        severity_breakdown=severity_breakdown(findings),
        priority_actions=priority_actions(findings),
        input_hash=_hash(combined_input),
        engine_version=ENGINE_VERSION,
        scan_metadata={
            "version": "1.0",
            "real_only_note": "Generated only from provided source/text/founder evidence. It does not accuse, certify, or invent facts.",
            "project_type_detected": checklist_key,
            "launch_checklist": checklist,
            "detected_controls": detected_controls,
            "provided_evidence": provided_evidence,
            "disclosure_summary": {
                "must_disclose": [item["title"] for item in detected_controls] or ["No privileged launch controls detected from provided input."],
                "manual_review_note": "A human reviewer should confirm tokenomics, liquidity, metadata, and governance disclosures before public launch.",
            },
        },
    )
