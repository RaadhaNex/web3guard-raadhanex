from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

PHASE39_VERSION = "web3guard-risk-intelligence-v39.0"
CWE_TOTAL_REFERENCE = 944
NVD_CVE_RECORDS_REFERENCE = 351451
SAFE_STATUSES = {
    "Assessed",
    "Not assessed yet",
    "Needs API Key",
    "Tool Not Installed",
    "Provider Not Configured",
    "Manual review required",
    "Live provider unavailable",
    "Failed",
    "Timeout",
    "Imported evidence",
}
SEVERITIES = {"critical", "high", "medium", "low", "info"}
BLOCKED_CLAIMS = [
    "finds all bugs",
    "find all bugs",
    "all vulnerabilities found",
    "guaranteed secure",
    "100% secure",
    "99% secure",
    "certified audit",
    "audited by web3guard",
    "audit passed",
    "zero risk",
    "no vulnerabilities",
    "complete security guarantee",
]

RISK_FAMILIES: list[dict[str, Any]] = [
    {
        "key": "smart_contract_static",
        "label": "Smart contract static risks",
        "bug_examples": [
            "reentrancy",
            "unchecked external call",
            "tx.origin authorization",
            "weak randomness",
            "uninitialized proxy/initializer",
            "delegatecall misuse",
            "dangerous upgradeability",
            "storage collision",
            "timestamp dependence",
            "unchecked ERC20 transfer",
        ],
        "detectable_by": ["Slither", "Aderyn", "Mythril Docker", "custom Solidity rules"],
        "confidence": "medium-high when real tool output exists",
        "limitation": "Business logic, economic design, and protocol-specific invariants still need manual audit.",
    },
    {
        "key": "web_api_appsec",
        "label": "Website, dApp, API, and backend risks",
        "bug_examples": [
            "broken access control",
            "IDOR/BOLA",
            "injection",
            "SSRF",
            "XSS",
            "CORS misconfiguration",
            "missing rate limit",
            "unsafe webhook verification",
            "sensitive data exposure",
            "insecure file upload",
        ],
        "detectable_by": ["Semgrep", "passive header checks", "API readiness rules", "manual review gates"],
        "confidence": "medium when source/config evidence exists",
        "limitation": "Deep authorization and business-logic abuse often require role-based/manual testing.",
    },
    {
        "key": "dependency_advisory",
        "label": "Dependency and known-vulnerability intelligence",
        "bug_examples": [
            "known vulnerable npm/pip packages",
            "GHSA/CVE matches",
            "known exploited CVE via CISA KEV",
            "outdated high-risk dependency",
            "supply-chain package risk",
        ],
        "detectable_by": ["OSV", "NVD/CVE mapping", "GitHub Advisory mapping", "CISA KEV"],
        "confidence": "high for exact package/version advisory matches",
        "limitation": "Advisory match does not always prove exploitability in this project without usage review.",
    },
    {
        "key": "github_devops",
        "label": "GitHub, CI/CD, secrets, and deployment hygiene",
        "bug_examples": [
            "committed secrets",
            "missing security policy",
            "unsafe GitHub Actions permissions",
            "public sensitive files",
            "missing branch protection",
            "Docker/env exposure",
        ],
        "detectable_by": ["Semgrep", "GitHub hygiene checks", "secret scan rules", "manual review"],
        "confidence": "medium when repo metadata/source evidence is provided",
        "limitation": "Private settings and organization policies require authorized access and manual confirmation.",
    },
    {
        "key": "wallet_admin_opsec",
        "label": "Wallet UX, admin OpSec, and launch trust risks",
        "bug_examples": [
            "blind signing UX",
            "unlimited approvals",
            "wrong chain warning missing",
            "seed/private-key collection",
            "single-admin key risk",
            "missing multisig/timelock",
            "missing incident response",
            "unsafe trust claims",
        ],
        "detectable_by": ["manual wallet checklist", "admin OpSec checklist", "safe claim checker", "report evidence"],
        "confidence": "manual/medium unless evidence screenshots and policies are supplied",
        "limitation": "This area cannot be fully automated without human review and real product-flow evidence.",
    },
]

KEYWORD_RULES: list[dict[str, Any]] = [
    {
        "keywords": ["reentrancy", "external call", "call.value", "withdraw"],
        "family": "smart_contract_static",
        "cwe_ids": ["CWE-841", "CWE-362"],
        "impact": "Funds or state can be manipulated through unexpected repeated execution before state is finalized.",
        "future_risk": "Risk can become critical as TVL grows or when the contract is integrated with lending, staking, or vault flows.",
        "exploit_scenario": "An attacker contract may repeatedly call back into the vulnerable function and drain funds or duplicate state changes.",
        "fix": "Use checks-effects-interactions, ReentrancyGuard, and update internal state before external calls.",
        "verify": ["Add a malicious receiver/attacker test", "Run Slither again", "Run Foundry tests for repeated withdrawal paths"],
    },
    {
        "keywords": ["access control", "onlyowner", "owner", "admin", "authorization", "role"],
        "family": "smart_contract_static",
        "cwe_ids": ["CWE-284", "CWE-862", "CWE-863"],
        "impact": "Unauthorized users may execute privileged actions or admin-only flows.",
        "future_risk": "One exposed privileged function can lead to minting, pausing, treasury movement, upgrade takeover, or user-data exposure.",
        "exploit_scenario": "Attacker calls an unprotected privileged endpoint/function or abuses weak role checks.",
        "fix": "Enforce least-privilege role checks, test negative cases, and document admin powers publicly.",
        "verify": ["Add tests for unauthorized caller rejection", "Review owner/minter/pauser/upgrader roles", "Confirm multisig/timelock for critical powers"],
    },
    {
        "keywords": ["oracle", "price", "twap", "flash loan", "liquidity"],
        "family": "smart_contract_static",
        "cwe_ids": ["CWE-345", "CWE-682"],
        "impact": "Incorrect or manipulable price data can break accounting, collateral, swap, reward, or liquidation logic.",
        "future_risk": "Economic exploits become more likely when liquidity grows or when the protocol is composed with other DeFi apps.",
        "exploit_scenario": "Attacker manipulates a thin-liquidity price source and triggers profitable mint/borrow/swap/reward behavior.",
        "fix": "Use robust oracle design, TWAP/medianized sources, stale-price checks, and circuit breakers.",
        "verify": ["Add oracle manipulation tests", "Review liquidity depth assumptions", "Manually review economic model"],
    },
    {
        "keywords": ["xss", "innerhtml", "script", "cross-site scripting"],
        "family": "web_api_appsec",
        "cwe_ids": ["CWE-79"],
        "impact": "Malicious scripts can execute in users' browsers and steal sessions, redirect users, or alter dApp UI.",
        "future_risk": "A wallet/dApp XSS can become severe if it influences transaction prompts or tricks users into approvals.",
        "exploit_scenario": "Attacker injects script through user-controlled content or unsafe HTML rendering.",
        "fix": "Sanitize untrusted content, avoid unsafe HTML injection, enforce CSP, and encode output.",
        "verify": ["Add Semgrep/XSS rules", "Test untrusted input rendering", "Check CSP headers"],
    },
    {
        "keywords": ["idor", "bola", "object authorization", "broken access"],
        "family": "web_api_appsec",
        "cwe_ids": ["CWE-639", "CWE-862", "CWE-863"],
        "impact": "Users may access or modify another user's project, scan, report, billing, or admin object.",
        "future_risk": "This becomes critical when paid reports, private findings, client data, or admin workflows go live.",
        "exploit_scenario": "Attacker changes an ID in the URL/API request and receives another user's data.",
        "fix": "Enforce object-level authorization on every read/update/delete and add two-user tests.",
        "verify": ["Run two-user BOLA tests", "Check all project/report IDs", "Add backend authorization tests"],
    },
    {
        "keywords": ["webhook", "razorpay", "signature", "payment"],
        "family": "web_api_appsec",
        "cwe_ids": ["CWE-347", "CWE-345"],
        "impact": "Payment status can be spoofed if webhook signatures or event IDs are not verified.",
        "future_risk": "Attackers may unlock paid reports without real payment, causing revenue loss and corrupted trust records.",
        "exploit_scenario": "Attacker posts fake payment-success events or replays old events.",
        "fix": "Verify Razorpay signatures server-side, store event IDs for idempotency, and never trust frontend-only payment success.",
        "verify": ["Send wrong-signature webhook", "Replay same event ID", "Confirm unlock happens only after verified backend event"],
    },
    {
        "keywords": ["dependency", "osv", "cve", "ghsa", "vulnerable package", "npm", "pip"],
        "family": "dependency_advisory",
        "cwe_ids": ["CWE-1104", "CWE-937"],
        "impact": "A known vulnerable dependency can expose the app to public exploits or supply-chain compromise.",
        "future_risk": "Known exploited CVEs can be abused quickly after public launch because exploit knowledge is already available.",
        "exploit_scenario": "Attacker targets a public vulnerable package version used by the frontend/backend/tooling.",
        "fix": "Upgrade to a fixed version, remove unused packages, and document advisory evidence in the report.",
        "verify": ["Run OSV query again", "Check lockfile version", "Confirm CISA KEV match is cleared or mitigated"],
    },
    {
        "keywords": ["secret", "api key", "token", ".env", "private key", "seed phrase", "mnemonic"],
        "family": "github_devops",
        "cwe_ids": ["CWE-798", "CWE-200", "CWE-522"],
        "impact": "Leaked secrets can let attackers access providers, deploy infrastructure, drain wallets, or impersonate services.",
        "future_risk": "A leaked key may remain exploitable even after code changes if it is not rotated and audited.",
        "exploit_scenario": "Attacker finds exposed credentials in repo, logs, frontend bundle, or screenshots.",
        "fix": "Remove secret, rotate it immediately, move to secure env storage, and audit access logs.",
        "verify": ["Run secret scan", "Rotate the affected key", "Confirm no secret appears in frontend bundle or repo history"],
    },
    {
        "keywords": ["cors", "origin", "csrf", "cookie", "session"],
        "family": "web_api_appsec",
        "cwe_ids": ["CWE-942", "CWE-352", "CWE-614"],
        "impact": "Browser/API trust boundaries may allow unwanted cross-origin access or session abuse.",
        "future_risk": "Misconfigured CORS/session policies can expose private scan/report/payment data after user onboarding.",
        "exploit_scenario": "Malicious site sends browser requests that are accepted due to weak origin/cookie controls.",
        "fix": "Restrict allowed origins, set secure cookies, require CSRF protection where relevant, and avoid wildcard credentials.",
        "verify": ["Test from unauthorized origin", "Check cookie flags", "Review CORS middleware settings"],
    },
    {
        "keywords": ["blind signing", "unlimited approval", "approval", "wallet", "signature", "permit"],
        "family": "wallet_admin_opsec",
        "cwe_ids": ["CWE-345", "CWE-451"],
        "impact": "Users can be tricked into signing unclear approvals or transactions that transfer assets.",
        "future_risk": "As users grow, wallet UX mistakes can create phishing losses and severe brand damage.",
        "exploit_scenario": "User signs a misleading approval/signature because the dApp does not explain spender, amount, chain, or action.",
        "fix": "Show spender, amount, chain, contract address, revoke guidance, and warnings before wallet actions.",
        "verify": ["Review wallet UX screenshots", "Test wrong-chain and approval flows", "Confirm no private key/seed input exists"],
    },
]

DEFAULT_RULE = {
    "family": "web_api_appsec",
    "cwe_ids": ["CWE-710"],
    "impact": "This issue may reduce security, reliability, or launch trust depending on where it appears in the project.",
    "future_risk": "If left unresolved before public launch, this can create technical debt, user trust damage, or exploit surface expansion.",
    "exploit_scenario": "An attacker or user may abuse the weak control if it is reachable in production context.",
    "fix": "Review the evidence, confirm true/false positive, apply least-privilege/safe-default controls, and retest.",
    "verify": ["Retest the affected module", "Attach evidence after fix", "Escalate to manual review if business logic is involved"],
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_status(value: str | None) -> str:
    status = str(value or "Assessed").strip()
    if status in SAFE_STATUSES:
        return status
    lowered = status.lower()
    if "not installed" in lowered:
        return "Tool Not Installed"
    if "api key" in lowered:
        return "Needs API Key"
    if "manual" in lowered:
        return "Manual review required"
    if "config" in lowered:
        return "Provider Not Configured"
    if "fail" in lowered or "error" in lowered:
        return "Failed"
    return "Not assessed yet"


def _safe_severity(value: str | None) -> str:
    severity = str(value or "info").strip().lower()
    return severity if severity in SEVERITIES else "info"


def _text_blob(item: dict[str, Any]) -> str:
    return " ".join(str(item.get(key) or "") for key in ["title", "description", "module", "source", "rule_id", "category"]).lower()


def _match_rule(item: dict[str, Any]) -> dict[str, Any]:
    blob = _text_blob(item)
    for rule in KEYWORD_RULES:
        if any(keyword in blob for keyword in rule["keywords"]):
            return rule
    return DEFAULT_RULE


def _normalize_cwe_ids(item: dict[str, Any], rule: dict[str, Any]) -> list[str]:
    supplied = item.get("cwe_ids") or item.get("cwe") or []
    if isinstance(supplied, str):
        supplied = [supplied]
    ids = [str(value).upper() for value in supplied if str(value).strip()]
    if not ids:
        ids = list(rule.get("cwe_ids") or [])
    return ids[:8]


def _normalize_cve_ids(item: dict[str, Any]) -> list[str]:
    supplied = item.get("cve_ids") or item.get("cves") or item.get("aliases") or []
    if isinstance(supplied, str):
        supplied = [supplied]
    ids: list[str] = []
    for value in supplied:
        text = str(value).upper().strip()
        if re.match(r"CVE-\d{4}-\d{4,}$", text):
            ids.append(text)
    return ids[:12]


def _priority(severity: str, cve_ids: list[str], family: str) -> str:
    if severity == "critical" or cve_ids:
        return "P0"
    if severity == "high":
        return "P1"
    if severity == "medium" or family in {"wallet_admin_opsec", "dependency_advisory"}:
        return "P2"
    return "P3"


def _human_review_needed(item: dict[str, Any], rule: dict[str, Any]) -> bool:
    family = rule.get("family")
    blob = _text_blob(item)
    manual_keywords = ["business logic", "oracle", "governance", "economic", "wallet", "admin", "manual", "upgrade"]
    return family in {"wallet_admin_opsec"} or any(word in blob for word in manual_keywords)


def _enhance_finding(item: dict[str, Any], index: int) -> dict[str, Any]:
    rule = _match_rule(item)
    severity = _safe_severity(item.get("severity"))
    status = _safe_status(item.get("status"))
    cwe_ids = _normalize_cwe_ids(item, rule)
    cve_ids = _normalize_cve_ids(item)
    family = str(rule.get("family") or "web_api_appsec")
    title = str(item.get("title") or item.get("rule_id") or f"Risk finding {index}").strip()
    description = str(item.get("description") or "Evidence-backed finding supplied by a scanner/provider/manual review.").strip()
    priority = _priority(severity, cve_ids, family)
    return {
        "id": item.get("id") or f"WG-RISK-{index:03d}-{uuid4().hex[:8]}",
        "title": title,
        "description": description,
        "module": item.get("module") or family,
        "risk_family": family,
        "status": status,
        "severity": severity,
        "confidence": item.get("confidence") or ("high" if item.get("source") in {"OSV", "CISA KEV"} else "medium"),
        "source": item.get("source") or "Web3Guard normalized evidence",
        "rule_id": item.get("rule_id"),
        "cwe_ids": cwe_ids,
        "cve_ids": cve_ids,
        "affected_file": item.get("file") or item.get("affected_file"),
        "affected_line": item.get("line") or item.get("affected_line"),
        "package": item.get("package"),
        "priority": priority,
        "impact": item.get("impact") or rule["impact"],
        "future_risk": item.get("future_risk") or rule["future_risk"],
        "exploit_scenario": item.get("exploit_scenario") or rule["exploit_scenario"],
        "fix_plan": {
            "summary": item.get("recommendation") or item.get("fix") or rule["fix"],
            "priority": priority,
            "owner": "developer/security reviewer",
            "verify_steps": item.get("verify_steps") or rule["verify"],
        },
        "needs_human_review": _human_review_needed(item, rule),
        "limitation": "This is risk intelligence from configured evidence. It is not a certified audit and cannot prove all bugs are found.",
    }


def _count_by_severity(items: list[dict[str, Any]]) -> dict[str, int]:
    counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
    for item in items:
        severity = _safe_severity(item.get("severity"))
        counts[severity] += 1
    return counts


def _family_counts(items: list[dict[str, Any]]) -> dict[str, int]:
    counts = {family["key"]: 0 for family in RISK_FAMILIES}
    for item in items:
        family = str(item.get("risk_family") or "web_api_appsec")
        counts[family] = counts.get(family, 0) + 1
    return counts


def _coverage_gaps(assessed_modules: dict[str, Any]) -> list[dict[str, str]]:
    gaps: list[dict[str, str]] = []
    expected = {
        "slither": "Smart contract static analysis",
        "semgrep": "App/API/backend static analysis",
        "osv": "Dependency advisory lookup",
        "cisa_kev": "Known exploited CVE matching",
        "github": "GitHub hygiene",
        "website": "Website/dApp passive checks",
        "api": "API authorization/config review",
        "wallet_ux": "Wallet UX/manual review",
        "admin_opsec": "Admin OpSec/manual review",
        "foundry": "Foundry tests",
        "echidna": "Echidna fuzz/invariants",
        "mythril": "Mythril Docker symbolic analysis",
    }
    for key, label in expected.items():
        if not bool(assessed_modules.get(key)):
            status = "Manual review required" if key in {"wallet_ux", "admin_opsec"} else "Not assessed yet"
            if key in {"slither", "semgrep", "foundry", "echidna", "mythril"}:
                status = "Tool Not Installed / Not assessed yet"
            if key in {"osv", "cisa_kev"}:
                status = "Provider Not Configured / Not assessed yet"
            gaps.append({
                "module": key,
                "label": label,
                "status": status,
                "why_it_matters": "This module is not counted toward bug discovery until real evidence exists.",
            })
    return gaps


def risk_intelligence_status() -> dict[str, Any]:
    return {
        "ok": True,
        "version": PHASE39_VERSION,
        "purpose": "Map scanner/provider/manual findings to detailed impact, future risk, exploit scenario, fix plan, and coverage limitations.",
        "reference_scope": {
            "cwe_total_weakness_types": CWE_TOTAL_REFERENCE,
            "nvd_documented_cve_records_snapshot": NVD_CVE_RECORDS_REFERENCE,
            "meaning": "Reference taxonomy coverage only. Web3Guard does not claim it can find every CWE/CVE in every project automatically.",
        },
        "detectable_when_configured": [family["label"] for family in RISK_FAMILIES],
        "safe_status_labels": sorted(SAFE_STATUSES),
        "blocked_claims": BLOCKED_CLAIMS,
        "required_disclaimer": "Pre-audit readiness only. Not a certified audit. No security guarantee. Does not replace professional security review.",
    }


def risk_taxonomy_map() -> dict[str, Any]:
    return {
        "ok": True,
        "version": PHASE39_VERSION,
        "reference_scope": {
            "cwe_total_weakness_types": CWE_TOTAL_REFERENCE,
            "nvd_documented_cve_records_snapshot": NVD_CVE_RECORDS_REFERENCE,
            "note": "The engine is CWE/NVD map-aware, not all-bug guaranteed. Exact live CVE count changes over time.",
        },
        "families": RISK_FAMILIES,
        "not_fully_automatable": [
            "business logic bugs",
            "economic attacks",
            "oracle manipulation",
            "cross-chain bridge logic",
            "governance abuse",
            "social engineering",
            "zero-days not present in public advisory databases",
            "custom cryptography flaws",
            "insider/admin process failures",
        ],
        "safe_product_wording": "CWE/NVD-aware pre-audit risk intelligence across configured scanners and evidence sources.",
    }


def analyze_risk_intelligence(payload: dict[str, Any]) -> dict[str, Any]:
    raw_findings = payload.get("findings") or []
    if not isinstance(raw_findings, list):
        raw_findings = []
    enhanced = [_enhance_finding(item if isinstance(item, dict) else {"title": str(item)}, idx) for idx, item in enumerate(raw_findings[:250], start=1)]
    assessed_modules = payload.get("assessed_modules") or {}
    if not isinstance(assessed_modules, dict):
        assessed_modules = {}
    severity_counts = _count_by_severity(enhanced)
    p0_count = len([item for item in enhanced if item["priority"] == "P0"])
    p1_count = len([item for item in enhanced if item["priority"] == "P1"])
    recommended_action = "No real findings were supplied. Do not claim the project is secure; run configured scanners/providers first."
    if p0_count:
        recommended_action = "Stop launch until P0 issues are fixed or manually cleared with evidence."
    elif p1_count:
        recommended_action = "Fix high-priority issues before paid/public launch and rerun scanner evidence."
    elif enhanced:
        recommended_action = "Resolve medium/low issues, document accepted risk, and rerun evidence before public launch."
    return {
        "ok": True,
        "version": PHASE39_VERSION,
        "analysis_id": f"RISK-{uuid4().hex[:12]}",
        "project_name": payload.get("project_name") or "Unnamed Web3 project",
        "generated_at": _now_iso(),
        "input_findings_count": len(raw_findings),
        "enhanced_findings_count": len(enhanced),
        "severity_breakdown": severity_counts,
        "risk_family_breakdown": _family_counts(enhanced),
        "priority_summary": {"p0": p0_count, "p1": p1_count, "p2": len([i for i in enhanced if i["priority"] == "P2"]), "p3": len([i for i in enhanced if i["priority"] == "P3"])},
        "findings": enhanced,
        "coverage_gaps": _coverage_gaps(assessed_modules),
        "taxonomy_reference": {
            "cwe_total_weakness_types": CWE_TOTAL_REFERENCE,
            "nvd_documented_cve_records_snapshot": NVD_CVE_RECORDS_REFERENCE,
            "claim_boundary": "Mapped/reference-aware; not a guarantee that all bug types were scanned or found.",
        },
        "recommended_next_action": recommended_action,
        "safe_report_wording": "This report explains evidence-backed risks and future impact. It is not a certified audit and does not guarantee all vulnerabilities are found.",
    }


def explain_single_finding(payload: dict[str, Any]) -> dict[str, Any]:
    item = _enhance_finding(payload, 1)
    return {
        "ok": True,
        "version": PHASE39_VERSION,
        "finding": item,
        "report_sections": [
            {"title": "What is the bug?", "text": item["description"]},
            {"title": "Why it matters", "text": item["impact"]},
            {"title": "Possible future problem", "text": item["future_risk"]},
            {"title": "How attacker may use it", "text": item["exploit_scenario"]},
            {"title": "How to fix", "text": item["fix_plan"]["summary"]},
            {"title": "How to verify", "text": " | ".join(item["fix_plan"]["verify_steps"])},
        ],
        "manual_review_note": "Manual validation is recommended before launch, especially for business logic, economic, wallet, and admin risks.",
    }


def risk_claim_check(text: str) -> dict[str, Any]:
    lowered = text.lower()
    violations = [claim for claim in BLOCKED_CLAIMS if claim in lowered]
    all_bug_phrases = ["all bugs", "sare bugs", "har bug", "sab bugs", "everything", "complete guarantee"]
    violations.extend([phrase for phrase in all_bug_phrases if phrase in lowered and phrase not in violations])
    return {
        "ok": not violations,
        "version": PHASE39_VERSION,
        "violations": sorted(set(violations)),
        "allowed_rewrite": "Web3Guard provides CWE/NVD-aware pre-audit risk intelligence across configured scanners and evidence sources. It does not guarantee that all bugs are found and does not replace a professional audit.",
        "required_disclaimer": "Pre-audit readiness only. Not a certified audit. No security guarantee.",
    }
