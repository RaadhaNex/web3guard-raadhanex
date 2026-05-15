from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import re
from typing import Literal

from app.models.schemas import ChecklistItem, Finding, ModuleScore, ScanResponse
from app.services.scoring import priority_actions, risk_label, score_findings, severity_breakdown

WalletOrAdminModule = Literal["wallet", "admin_opsec"]

WALLET_RULES: dict[str, tuple[str, str, str, str, str, bool]] = {
    "domain_verify": ("medium", "WalletConnect / Domain Verification Missing", "Users should see a verified, consistent dApp domain before connecting wallets.", "domain", "WALLET-CHECK-DOMAIN-VERIFY", False),
    "chain_check": ("medium", "Chain ID / Network Check Missing", "Wallet flow should verify the expected chain before any transaction or signature prompt.", "chain", "WALLET-CHECK-CHAIN", False),
    "spender_display": ("medium", "Spender Address Not Clearly Displayed", "Approval flows must clearly show which spender/operator receives token permission.", "spender", "WALLET-CHECK-SPENDER", False),
    "amount_preview": ("medium", "Token / Amount Preview Missing", "Users should see token, amount, recipient/spender, contract, and chain before wallet opens.", "transaction_preview", "WALLET-CHECK-AMOUNT-PREVIEW", False),
    "allowance_warning": ("high", "Unlimited Approval Warning Missing", "Unlimited token approvals can expose user funds if spender/operator is compromised.", "approval", "WALLET-CHECK-ALLOWANCE", True),
    "set_approval_for_all": ("high", "setApprovalForAll Risk Explanation Missing", "NFT operator approvals can transfer all assets in a collection and need a very clear warning.", "approval", "WALLET-CHECK-SET-APPROVAL-FOR-ALL", True),
    "permit_warning": ("medium", "Permit / Permit2 Signature Risk Not Explained", "Permit signatures can grant approvals without a normal on-chain approval transaction.", "signature", "WALLET-CHECK-PERMIT", False),
    "blind_signing": ("high", "Blind Signing Protection Missing", "Users need clear, human-readable signing purpose and should avoid raw opaque signatures.", "signature", "WALLET-CHECK-BLIND-SIGNING", True),
    "typed_data": ("medium", "Typed Data / Human-Readable Signature Missing", "Typed structured data is easier to review than opaque messages.", "signature", "WALLET-CHECK-TYPED-DATA", False),
    "session_disconnect": ("low", "Wallet Session Disconnect Guidance Missing", "Users should be able to disconnect sessions and understand wallet connection persistence.", "session", "WALLET-CHECK-DISCONNECT", False),
    "verified_contract": ("medium", "Verified Contract Link Missing", "Wallet flow should show explorer links and verified contract/address context.", "contract_verification", "WALLET-CHECK-VERIFIED-CONTRACT", False),
    "no_auto_prompt": ("medium", "Auto Wallet Prompt Risk", "Wallet prompts should be triggered by explicit user action, not on page load.", "wallet_ux", "WALLET-CHECK-NO-AUTO-PROMPT", False),
}

ADMIN_RULES: dict[str, tuple[str, str, str, str, str, bool]] = {
    "multisig": ("critical", "Multisig Missing for Owner/Admin", "Single owner wallets are a major launch risk for upgrades, minting, pausing, and treasury actions.", "wallet_security", "ADMIN-CHECK-MULTISIG", True),
    "timelock": ("high", "Timelock Missing for Critical Changes", "Critical admin actions should have delay where appropriate so users can react.", "governance", "ADMIN-CHECK-TIMELOCK", True),
    "role_separation": ("high", "Role Separation Missing", "Deployer, owner, pauser, minter, upgrader, and treasury roles should not all depend on one hot wallet.", "access_control", "ADMIN-CHECK-ROLE-SEPARATION", True),
    "emergency_pause": ("medium", "Emergency Pause Process Missing", "High-risk launch flows need a documented pause/emergency process.", "incident_response", "ADMIN-CHECK-PAUSE", False),
    "upgrade_admin": ("high", "Proxy / Upgrade Admin Risk Not Controlled", "Upgradeable projects need multisig/timelock controls and upgrade documentation.", "upgradeability", "ADMIN-CHECK-UPGRADE-ADMIN", True),
    "treasury_separate": ("high", "Treasury Wallet Separation Missing", "Treasury funds should not sit in the same wallet used for deploy/admin operations.", "treasury", "ADMIN-CHECK-TREASURY", True),
    "hardware_wallet": ("medium", "Hardware Wallet Policy Missing", "Founder/admin signer keys should use hardware wallets or secure custody where practical.", "key_management", "ADMIN-CHECK-HARDWARE-WALLET", False),
    "private_key_policy": ("critical", "Private Key Storage Policy Missing", "Private keys, seed phrases, and deployer secrets must never be stored in chats, cloud notes, screenshots, or frontend repos.", "key_management", "ADMIN-CHECK-PRIVATE-KEY-POLICY", True),
    "mfa": ("medium", "MFA Checklist Missing", "Admin dashboards, GitHub, registrar, hosting, and email accounts should use strong MFA.", "account_security", "ADMIN-CHECK-MFA", False),
    "audit_logs": ("medium", "Admin Audit Logs Missing", "Admin/payment/security actions should be logged for incident review.", "logging", "ADMIN-CHECK-AUDIT-LOGS", False),
    "signer_rotation": ("medium", "Signer Rotation / Offboarding Process Missing", "Teams need a way to rotate signers and remove old team access safely.", "operations", "ADMIN-CHECK-SIGNER-ROTATION", False),
    "incident_response": ("medium", "Incident Response Plan Missing", "Teams need emergency contacts, severity levels, pause steps, and public communication templates before launch.", "incident_response", "ADMIN-CHECK-INCIDENT-RESPONSE", False),
    "backup_admin": ("low", "Backup Admin Recovery Plan Missing", "A safe recovery process reduces lockout risk without adding unsafe shared keys.", "operations", "ADMIN-CHECK-BACKUP-ADMIN", False),
}

TEMPLATE_LABELS = {
    # wallet
    "domain_verify": "WalletConnect/domain verification is planned and domain matches official links",
    "chain_check": "Wallet flow checks chain ID before transaction/signature",
    "spender_display": "Approval spender/operator address is clearly displayed",
    "amount_preview": "Transaction preview shows token, amount, recipient/spender, contract, and chain",
    "allowance_warning": "Unlimited approvals are minimized and clearly warned",
    "set_approval_for_all": "setApprovalForAll/NFT operator approvals have a strong warning",
    "permit_warning": "Permit/Permit2 signatures are explained clearly",
    "blind_signing": "Blind signing/raw opaque signatures are avoided or clearly flagged",
    "typed_data": "Signature flow uses typed/human-readable data where possible",
    "session_disconnect": "Users can disconnect wallet sessions and understand persistence",
    "verified_contract": "UI shows verified contract address and explorer link",
    "no_auto_prompt": "Wallet prompts happen only after explicit user action",
    # admin
    "multisig": "Owner/admin wallet uses multisig for critical actions",
    "timelock": "Critical changes use timelock where needed",
    "role_separation": "Owner, pauser, minter, upgrader, deployer, and treasury roles are separated",
    "emergency_pause": "Emergency pause and recovery process exists",
    "upgrade_admin": "Proxy/upgrade admin is controlled by multisig/timelock and documented",
    "treasury_separate": "Treasury wallet is separate from deployer/admin wallet",
    "hardware_wallet": "Founder/admin signers use hardware wallets or secure custody",
    "private_key_policy": "Private key/seed phrase storage policy exists and is enforced",
    "mfa": "Admin tools, GitHub, registrar, hosting, and email use strong MFA",
    "audit_logs": "Admin/payment/security actions are audit logged",
    "signer_rotation": "Signer rotation and team offboarding process exists",
    "incident_response": "Incident response plan exists",
    "backup_admin": "Safe backup admin/recovery process exists",
}

WALLET_PATTERNS: list[tuple[re.Pattern[str], str, str, str, str, str, str, bool, list[str]]] = [
    (re.compile(r"\b(MaxUint256|uint256\.max|unlimited approval|infinite approval|approve\s*all)\b", re.I), "high", "Unlimited Approval Pattern Mentioned", "The provided wallet-flow notes/code mention unlimited approval or maximum allowance.", "approval", "WALLET-NOTES-UNLIMITED-APPROVAL", "Use exact allowance where possible, show spender, amount, token, chain, and a revoke link/education note.", True, ["token approval", "spender risk"]),
    (re.compile(r"\bsetApprovalForAll\b|operator approval|approve all nfts", re.I), "high", "NFT Operator Approval Risk Mentioned", "setApprovalForAll/operator approvals can allow all NFTs in a collection to be moved by the operator.", "approval", "WALLET-NOTES-SET-APPROVAL-FOR-ALL", "Add strong warning copy, verified operator address, collection scope, and avoid broad operator approvals unless essential.", True, ["NFT approval"]),
    (re.compile(r"\b(Permit2|permit\(|EIP-2612|permit signature)\b", re.I), "medium", "Permit Signature Flow Needs Extra Clarity", "Permit flows can grant approvals via signatures and users may not see a normal approval transaction.", "signature", "WALLET-NOTES-PERMIT", "Show human-readable purpose, spender, token, allowance, deadline, chain, and revoke guidance.", False, ["permit signature"]),
    (re.compile(r"\b(personal_sign|eth_sign|blind sign|blind signing|raw signature|opaque signature)\b", re.I), "high", "Blind / Raw Signature Risk Mentioned", "Raw or opaque signatures are difficult for users to verify and are commonly abused in phishing.", "signature", "WALLET-NOTES-BLIND-SIGNING", "Prefer typed structured signatures and show clear domain, purpose, expiry, nonce, and consequences.", True, ["blind signing"]),
    (re.compile(r"\b(auto.?connect|connect on load|prompt on load|auto prompt|on page load)\b", re.I), "medium", "Wallet Prompt May Trigger Too Early", "Wallet connection/signing prompts should follow explicit user action, not page load.", "wallet_ux", "WALLET-NOTES-AUTO-PROMPT", "Require a clear user click before connect/sign/transaction and explain why the wallet is needed.", False, ["wallet UX"]),
    (re.compile(r"\b(wrong chain|chain mismatch|no chain check|without chain id|chainid missing)\b", re.I), "medium", "Chain Mismatch Risk Mentioned", "The notes suggest chain mismatch or missing network validation.", "chain", "WALLET-NOTES-CHAIN-MISMATCH", "Validate expected chain ID before transaction/signature and provide safe network switching.", False, ["chain mismatch"]),
    (re.compile(r"\b(fake mint|fake claim|claim button|mint button)\b", re.I), "medium", "Mint/Claim Flow Needs Transaction Clarity", "Mint/claim flows are common phishing targets and need strong preview and domain trust cues.", "transaction_preview", "WALLET-NOTES-MINT-CLAIM", "Show verified contract, method, price, token/amount, chain, recipient/spender, and failure states before wallet opens.", False, ["mint/claim UX"]),
]

ADMIN_PATTERNS: list[tuple[re.Pattern[str], str, str, str, str, str, str, bool, list[str]]] = [
    (re.compile(r"\b(single owner|single admin|only owner|EOA owner|owner is deployer|deployer controls|one wallet)\b", re.I), "critical", "Single Owner / EOA Admin Risk Mentioned", "The provided notes suggest one wallet may control privileged actions.", "wallet_security", "ADMIN-NOTES-SINGLE-OWNER", "Move privileged ownership to a multisig, document signer policy, and consider timelock for high-impact actions.", True, ["multisig", "centralization"]),
    (re.compile(r"\b(no multisig|without multisig|multisig missing)\b", re.I), "critical", "No Multisig Mentioned", "Missing multisig is one of the most common founder OpSec launch risks.", "wallet_security", "ADMIN-NOTES-NO-MULTISIG", "Use Safe/Gnosis-style multisig for owner/admin/treasury where practical before mainnet launch.", True, ["multisig"]),
    (re.compile(r"\b(no timelock|without timelock|timelock missing|instant upgrade|instant admin change)\b", re.I), "high", "No Timelock / Instant Critical Change Risk", "Critical changes without delay can surprise users and increase governance/admin risk.", "governance", "ADMIN-NOTES-NO-TIMELOCK", "Add timelock for upgrades/critical parameter changes where the project model supports it.", True, ["timelock"]),
    (re.compile(r"\b(private key|seed phrase|mnemonic)\b.*\b(\.env|telegram|discord|whatsapp|google drive|notion|screenshot|shared|email|frontend|github)\b|\b(\.env|telegram|discord|whatsapp|google drive|notion|screenshot|shared|email|frontend|github)\b.*\b(private key|seed phrase|mnemonic)\b", re.I), "critical", "Unsafe Private Key / Seed Phrase Storage Mentioned", "The notes suggest private keys or seed phrases may be stored in unsafe places.", "key_management", "ADMIN-NOTES-UNSAFE-KEY-STORAGE", "Move keys to hardware wallet/secure custody, rotate exposed keys, remove secrets from repos/chats/cloud notes, and review deployment history.", True, ["key management"]),
    (re.compile(r"\b(hot wallet|metamask deployer|browser wallet deployer)\b", re.I), "high", "Hot Wallet Deployer/Admin Risk", "Hot wallets are more exposed to browser, malware, phishing, and device compromise risk.", "key_management", "ADMIN-NOTES-HOT-WALLET", "Use hardware wallet or multisig for admin ownership and separate deployer from treasury/owner roles.", True, ["hardware wallet"]),
    (re.compile(r"\b(no mfa|mfa missing|2fa missing|without 2fa|no 2fa)\b", re.I), "medium", "MFA Gap Mentioned", "Admin-related accounts without MFA increase takeover risk.", "account_security", "ADMIN-NOTES-NO-MFA", "Enable strong MFA on GitHub, hosting, registrar, email, cloud, admin dashboards, and payment tools.", False, ["account security"]),
    (re.compile(r"\b(no incident response|incident response missing|no emergency plan|no pause plan)\b", re.I), "medium", "Incident Response Gap Mentioned", "Launch teams need a clear emergency plan before funds/users are involved.", "incident_response", "ADMIN-NOTES-NO-IR", "Prepare emergency contacts, pause steps, communication template, severity levels, and evidence preservation process.", False, ["incident response"]),
    (re.compile(r"\b(treasury same|same wallet treasury|deployer treasury|owner treasury)\b", re.I), "high", "Treasury and Admin Wallet Separation Risk", "The notes suggest treasury and admin/deployer functions may use the same wallet.", "treasury", "ADMIN-NOTES-TREASURY-SAME", "Separate treasury from deploy/admin wallet and control treasury with multisig plus accounting process.", True, ["treasury"]),
    (re.compile(r"\b(upgradeable|proxy|UUPS|transparent proxy|proxy admin)\b", re.I), "medium", "Upgradeable Contract Admin Requires Review", "Upgradeable projects need clear proxy admin ownership, timelock policy, and upgrade runbooks.", "upgradeability", "ADMIN-NOTES-UPGRADEABLE", "Document proxy admin, implementation upgrade process, storage layout review, signer approval flow, and public disclosure.", True, ["upgradeability"]),
]


def wallet_admin_checklist_template(module: WalletOrAdminModule) -> list[dict]:
    rules = WALLET_RULES if module == "wallet" else ADMIN_RULES
    return [{"key": key, "label": TEMPLATE_LABELS[key], "answer": "unknown"} for key in rules]


def _finding(
    *,
    module: WalletOrAdminModule,
    idx: int,
    severity: str,
    title: str,
    description: str,
    category: str,
    rule_id: str,
    confidence: str,
    source: str,
    business_impact: str,
    developer_explanation: str,
    recommendation: str,
    paid: bool,
    affected_line: int | None = None,
    affected_code: str | None = None,
    references: list[str] | None = None,
) -> Finding:
    return Finding(
        id=f"{module}-{idx}",
        module=module,
        severity=severity,
        title=title,
        description=description,
        affected_line=affected_line,
        affected_code=affected_code,
        confidence=confidence,
        source=source,
        category=category,
        rule_id=rule_id,
        fingerprint=hashlib.sha256(f"{module}:{rule_id}:{title}:{affected_line or ''}".encode()).hexdigest()[:12],
        business_impact=business_impact,
        developer_explanation=developer_explanation,
        recommendation=recommendation,
        references=references or [],
        paid_review_recommended=paid,
    )


def _base_findings(module: WalletOrAdminModule, checklist: list[ChecklistItem]) -> list[Finding]:
    rules = WALLET_RULES if module == "wallet" else ADMIN_RULES
    answers = {item.key: item.answer for item in checklist}
    findings: list[Finding] = []
    idx = 1
    for key, (severity, title, description, category, rule_id, paid) in rules.items():
        answer = answers.get(key, "unknown")
        if answer in {"no", "unknown"}:
            confidence = "high" if answer == "no" else "low"
            if module == "wallet":
                business = "Wallet-flow gaps can make users approve unsafe permissions, sign unclear messages, or lose trust during launch."
                dev = f"Checklist answer for {key}: {answer}. Confirm wallet UI copy, chain checks, spender display, and signature behavior before launch."
            else:
                business = "Founder/admin OpSec gaps can turn one compromised device, wallet, or admin account into a launch-ending incident."
                dev = f"Checklist answer for {key}: {answer}. Confirm wallet ownership, signer process, role controls, and incident workflow before launch."
            findings.append(_finding(
                module=module,
                idx=idx,
                severity=severity,
                title=title,
                description=description,
                category=category,
                rule_id=rule_id,
                confidence=confidence,
                source="Wallet/Admin Checklist Engine",
                business_impact=business,
                developer_explanation=dev,
                recommendation="Document the current setup, fix the gap, collect evidence, and request manual review for high-risk launch flows.",
                paid=paid,
                references=[category],
            ))
            idx += 1
    return findings


def _line_for(text: str, pattern: re.Pattern[str]) -> tuple[int | None, str | None]:
    match = pattern.search(text)
    if not match:
        return None, None
    line = text[:match.start()].count("\n") + 1
    lines = text.splitlines()
    snippet = "\n".join(lines[max(0, line - 2): min(len(lines), line + 1)])
    return line, snippet.strip()


def _pattern_findings(module: WalletOrAdminModule, notes: str, start_idx: int) -> list[Finding]:
    patterns = WALLET_PATTERNS if module == "wallet" else ADMIN_PATTERNS
    findings: list[Finding] = []
    idx = start_idx
    for pattern, severity, title, desc, category, rule_id, rec, paid, refs in patterns:
        line, snippet = _line_for(notes, pattern)
        if line:
            business = "Wallet signing/approval mistakes can directly affect user funds and conversion trust." if module == "wallet" else "Admin/key-management mistakes can directly affect protocol funds, ownership, upgrades, and launch credibility."
            findings.append(_finding(
                module=module,
                idx=idx,
                severity=severity,
                title=title,
                description=desc,
                category=category,
                rule_id=rule_id,
                confidence="high",
                source="Wallet/Admin Notes Hint Engine",
                business_impact=business,
                developer_explanation=f"Pattern detected in provided notes near line {line}. This is a static launch-readiness hint, not a full manual security review.",
                recommendation=rec,
                paid=paid,
                affected_line=line,
                affected_code=snippet,
                references=refs,
            ))
            idx += 1
    return findings


def _readiness_map(module: WalletOrAdminModule, checklist: list[ChecklistItem]) -> dict:
    answers = {item.key: item.answer for item in checklist}
    if module == "wallet":
        groups = {
            "identity_and_domain": ["domain_verify", "verified_contract"],
            "network_and_preview": ["chain_check", "amount_preview", "spender_display"],
            "approval_safety": ["allowance_warning", "set_approval_for_all", "permit_warning"],
            "signature_safety": ["blind_signing", "typed_data"],
            "session_and_prompt_ux": ["session_disconnect", "no_auto_prompt"],
        }
    else:
        groups = {
            "ownership_controls": ["multisig", "timelock", "role_separation", "upgrade_admin"],
            "key_management": ["hardware_wallet", "private_key_policy", "signer_rotation"],
            "treasury_and_ops": ["treasury_separate", "backup_admin"],
            "platform_security": ["mfa", "audit_logs"],
            "incident_response": ["emergency_pause", "incident_response"],
        }
    result = {}
    for group, keys in groups.items():
        group_answers = [answers.get(key, "unknown") for key in keys]
        result[group] = {
            "ready": group_answers.count("yes"),
            "missing": group_answers.count("no"),
            "unknown": group_answers.count("unknown"),
            "total": len(keys),
        }
    return result


def scan_wallet_flow(*, checklist: list[ChecklistItem], project_name: str | None = None, notes: str | None = None) -> ScanResponse:
    return _scan_wallet_or_admin("wallet", checklist=checklist, project_name=project_name, notes=notes)


def scan_admin_opsec(*, checklist: list[ChecklistItem], project_name: str | None = None, notes: str | None = None) -> ScanResponse:
    return _scan_wallet_or_admin("admin_opsec", checklist=checklist, project_name=project_name, notes=notes)


def _scan_wallet_or_admin(module: WalletOrAdminModule, *, checklist: list[ChecklistItem], project_name: str | None, notes: str | None) -> ScanResponse:
    findings = _base_findings(module, checklist)
    if notes and notes.strip():
        findings.extend(_pattern_findings(module, notes, len(findings) + 1))

    score = score_findings(findings)
    input_hash = hashlib.sha256((notes or "").encode()).hexdigest()[:16] if notes else None
    engine = "web3guard-wallet-flow-engine-v2.7" if module == "wallet" else "web3guard-admin-opsec-engine-v2.7"
    prefix = "WALLET" if module == "wallet" else "ADMIN"
    metadata = {
        "mode": "checklist_plus_notes_hints",
        "notes_provided": bool(notes and notes.strip()),
        "readiness_map": _readiness_map(module, checklist),
        "safety_controls": {
            "static_hints_only": True,
            "no_wallet_connection": True,
            "no_transaction_signing": True,
            "no_private_key_collection": True,
            "no_seed_phrase_collection": True,
            "manual_review_recommended_for_critical_admin_or_approval_risk": True,
        },
    }
    return ScanResponse(
        report_id=f"W3G-{prefix}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
        generated_at=datetime.now(timezone.utc),
        project_name=project_name,
        module_score=ModuleScore(module=module, score=score, risk_label=risk_label(score)),
        findings=findings,
        severity_breakdown=severity_breakdown(findings),
        priority_actions=priority_actions(findings),
        input_hash=input_hash,
        engine_version=engine,
        scan_metadata=metadata,
    )
