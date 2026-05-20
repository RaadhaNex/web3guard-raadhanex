from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

PHASE43_VERSION = "web3guard-scanner-correlation-v43.0"

REQUIRED_DISCLAIMER = (
    "Scanner Correlation prioritizes evidence from configured scanners, CVE/CWE mappings, and project context. "
    "It is not exploitation, not a certified audit, and does not guarantee that all vulnerabilities are found."
)

SAFE_STATUSES = [
    "Correlated",
    "Needs evidence",
    "Manual review required",
    "Known exploited priority",
    "Internet-exposed priority",
    "Human audit recommended",
    "Not assessed",
]

BLOCKED_CLAIMS = [
    "finds all bugs",
    "all vulnerabilities found",
    "100% secure",
    "99% secure",
    "exploit this site",
    "rce exploitation",
    "credential stuffing",
    "password spraying",
    "brute force",
    "dos attack",
    "ddos",
    "delete files",
    "extract data",
    "private key collection",
    "seed phrase collection",
    "wallet signing",
    "certified audit",
    "audited by web3guard",
]

DETECTION_SURFACES: list[dict[str, Any]] = [
    {
        "id": "smart_contract_static",
        "label": "Smart contract static analysis",
        "sources": ["Slither", "Aderyn", "OpenZeppelin Pattern Intelligence", "imported JSON"],
        "best_for": ["reentrancy", "access control", "unchecked calls", "unsafe upgradeability", "token-standard drift"],
        "limitations": ["economic attacks", "custom tokenomics", "oracle assumptions", "cross-chain bridge logic"],
    },
    {
        "id": "web_api_static",
        "label": "Web/API code pattern analysis",
        "sources": ["Semgrep", "manual evidence", "repository rules"],
        "best_for": ["BOLA/IDOR patterns", "auth/session risks", "webhook verification gaps", "dangerous sinks", "secrets"],
        "limitations": ["deep business logic", "real authorization proof without tests", "production-only config drift"],
    },
    {
        "id": "advisory_intelligence",
        "label": "Dependency and exploited-CVE intelligence",
        "sources": ["OSV", "NVD/CVSS", "CISA KEV", "GitHub Advisory", "EPSS if configured"],
        "best_for": ["known vulnerable packages", "exploited-in-wild CVEs", "patch urgency", "dependency risk context"],
        "limitations": ["zero-days", "unpublished vulnerabilities", "vendor-specific patches not in public databases"],
    },
    {
        "id": "authorized_web_dast",
        "label": "Verified authorized web DAST baseline",
        "sources": ["Web DAST baseline", "HTTP safe checks", "ZAP baseline readiness"],
        "best_for": ["headers", "CORS", "cookies", "safe open redirect signal", "directory listing", "surface exposure"],
        "limitations": ["destructive exploitation", "brute force", "DoS/stress", "data extraction"],
    },
    {
        "id": "governance_trust",
        "label": "Governance and trust readiness",
        "sources": ["admin pentest governance", "risk intelligence", "security passport", "manual review"],
        "best_for": ["scope gaps", "unsafe claims", "missing incident controls", "manual audit handoff"],
        "limitations": ["legal validation", "brand trust without real users", "human auditor judgment"],
    },
]

ATTACK_PATH_TEMPLATES: list[dict[str, Any]] = [
    {
        "id": "AP-001",
        "title": "Internet-exposed dependency to backend compromise",
        "signals": ["cve", "dependency", "osv", "kev", "public api", "backend", "rce"],
        "severity": "critical",
        "impact": "A known vulnerable internet-facing dependency may become a direct compromise path if reachable in production.",
        "future_risk": "Risk grows quickly when the service becomes public, receives traffic, or handles payment/user data.",
        "fix": "Patch or remove the vulnerable dependency, confirm fixed version, and retest with OSV/NVD/CISA matching.",
    },
    {
        "id": "AP-002",
        "title": "Webhook verification gap to fake paid access",
        "signals": ["webhook", "payment", "razorpay", "signature", "idempotency"],
        "severity": "critical",
        "impact": "A spoofed webhook can unlock paid reports or subscription access without real payment.",
        "future_risk": "Revenue fraud, corrupted audit trail, and customer trust loss can compound after launch.",
        "fix": "Verify webhook signature server-side, store event IDs for idempotency, and never trust frontend-only payment success.",
    },
    {
        "id": "AP-003",
        "title": "Unprotected admin function to fund/control takeover",
        "signals": ["access control", "onlyowner", "onlyrole", "admin", "mint", "withdraw", "upgrade"],
        "severity": "critical",
        "impact": "A missing role check on privileged functions can allow unauthorized minting, withdrawals, upgrades, or configuration changes.",
        "future_risk": "Impact rises as TVL, token supply, users, or treasury balance grows.",
        "fix": "Protect privileged functions with Ownable2Step/AccessControl/multisig/timelock and add negative authorization tests.",
    },
    {
        "id": "AP-004",
        "title": "Reentrancy path to balance drain",
        "signals": ["reentrancy", "external call", "call{", "withdraw", "vault", "staking"],
        "severity": "critical",
        "impact": "External calls before safe state finalization can allow repeated execution and fund loss.",
        "future_risk": "A low-TVL issue can become catastrophic after liquidity or integrations increase.",
        "fix": "Use checks-effects-interactions, ReentrancyGuard/nonReentrant, and malicious receiver tests.",
    },
    {
        "id": "AP-005",
        "title": "BOLA/IDOR to account or project data exposure",
        "signals": ["bola", "idor", "object level", "authorization", "user_id", "project_id", "api"],
        "severity": "high",
        "impact": "Object identifiers without ownership checks can expose or modify another user's project data.",
        "future_risk": "The blast radius grows with every new customer, report, payment record, and workspace.",
        "fix": "Enforce server-side object ownership checks for every API route and add negative tests for cross-account access.",
    },
]

PLAYBOOKS: list[dict[str, Any]] = [
    {
        "id": "P0-LAUNCH-BLOCKER",
        "title": "P0 launch blocker response",
        "when_to_use": "Any internet-exposed, known-exploited, fund-moving, payment-unlocking, or admin-takeover path.",
        "steps": [
            "Stop public launch or paid onboarding until the finding is fixed or formally accepted by leadership.",
            "Collect evidence: scanner output, file/line, endpoint, package version, affected asset, and configuration state.",
            "Patch the root cause, not just the symptom.",
            "Re-run the same scanner and add a manual verification note.",
            "Keep the report wording honest: not a certified audit, no security guarantee.",
        ],
    },
    {
        "id": "P1-PRE-AUDIT-FIX",
        "title": "P1 pre-audit fix workflow",
        "when_to_use": "High-impact but not proven internet-exploitable findings.",
        "steps": [
            "Create a fix ticket with owner and deadline.",
            "Add unit/integration tests that fail before the fix and pass after the fix.",
            "Document remaining manual-review questions for the auditor handoff pack.",
            "Re-run scanner and compare before/after findings.",
        ],
    },
    {
        "id": "MANUAL-REVIEW",
        "title": "Manual review escalation",
        "when_to_use": "Business logic, economic security, cross-chain, oracle, governance, or ambiguous findings.",
        "steps": [
            "Mark the issue Manual Review Required instead of guessing.",
            "Ask the founder for architecture, roles, admin controls, and threat model.",
            "Attach source/evidence and route to human reviewer or audit partner.",
        ],
    },
]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        return str(value).lower()
    return str(value).lower()


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _normalize_severity(value: Any) -> str:
    severity = str(value or "info").lower().strip()
    if severity in {"critical", "high", "medium", "low", "info"}:
        return severity
    if severity in {"warn", "warning"}:
        return "medium"
    return "info"


def _base_priority_score(severity: str) -> int:
    return {"critical": 90, "high": 72, "medium": 48, "low": 24, "info": 8}.get(severity, 8)


def _priority_label(score: int) -> str:
    if score >= 90:
        return "P0"
    if score >= 70:
        return "P1"
    if score >= 45:
        return "P2"
    return "P3"


def _confidence(value: Any) -> str:
    normalized = str(value or "medium").lower().strip()
    return normalized if normalized in {"high", "medium", "low"} else "medium"


def _finding_text(finding: dict[str, Any]) -> str:
    parts = [
        finding.get("title"),
        finding.get("description"),
        finding.get("module"),
        finding.get("source"),
        finding.get("rule_id"),
        finding.get("cwe_ids"),
        finding.get("cve_ids"),
        finding.get("evidence"),
        finding.get("file"),
    ]
    return " ".join(_text(item) for item in parts)


def _context_flags(payload: dict[str, Any], finding: dict[str, Any]) -> dict[str, bool]:
    context = payload.get("asset_context") if isinstance(payload.get("asset_context"), dict) else {}
    text = _finding_text(finding)
    cve_ids = _as_list(finding.get("cve_ids"))
    cwe_ids = _as_list(finding.get("cwe_ids"))
    tags = [str(item).lower() for item in _as_list(finding.get("tags"))]
    return {
        "internet_exposed": bool(context.get("internet_exposed")) or any(word in text for word in ["public", "internet", "external", "api", "frontend", "website"]),
        "holds_funds_or_unlocks_value": bool(context.get("holds_funds")) or any(word in text for word in ["fund", "withdraw", "mint", "treasury", "payment", "webhook", "razorpay", "wallet", "token", "vault"]),
        "known_exploited": bool(finding.get("known_exploited")) or "kev" in text or "cisa" in text or "known exploited" in text,
        "has_cve": bool(cve_ids) or "cve-" in text,
        "has_cwe": bool(cwe_ids) or "cwe-" in text,
        "public_poc_or_exploit_likely": bool(finding.get("public_poc")) or any(word in text for word in ["poc", "exploit", "metasploit", "rce"]),
        "requires_auth": bool(finding.get("requires_auth")) or "authenticated" in text,
        "manual_review_required": bool(finding.get("human_review_required")) or any(word in text for word in ["business logic", "economic", "oracle", "governance", "bridge", "manual"]),
        "source_verified": str(finding.get("status") or "").lower() in {"assessed", "correlated", "openzeppelin pattern detected", "passive baseline complete", "light active complete"} or bool(finding.get("evidence")),
        "scanner_imported": any(str(finding.get("source") or "").lower().startswith(prefix) for prefix in ["slither", "semgrep", "osv", "cisa", "aderyn", "web dast", "openzeppelin"]),
        "api_top10_related": any(word in text or word in tags for word in ["bola", "idor", "broken authentication", "authorization", "mass assignment", "api"]),
    }


def _score_finding(payload: dict[str, Any], finding: dict[str, Any]) -> dict[str, Any]:
    severity = _normalize_severity(finding.get("severity"))
    flags = _context_flags(payload, finding)
    score = _base_priority_score(severity)
    reasons: list[str] = [f"Base severity mapped from {severity}."]

    adjustments = [
        ("known_exploited", 18, "Known exploited / CISA KEV style signal."),
        ("internet_exposed", 10, "Internet-exposed or public attack surface signal."),
        ("holds_funds_or_unlocks_value", 12, "Can affect funds, token supply, payments, or paid access."),
        ("public_poc_or_exploit_likely", 8, "Public PoC/exploit/RCE-style signal."),
        ("api_top10_related", 6, "OWASP API Top 10 style access-control/auth/API signal."),
        ("source_verified", 5, "Finding has evidence or assessed source output."),
        ("manual_review_required", 5, "Manual-review risk can hide business/economic impact."),
    ]
    for flag, delta, reason in adjustments:
        if flags.get(flag):
            score += delta
            reasons.append(reason)

    if flags.get("requires_auth") and not flags.get("known_exploited"):
        score -= 5
        reasons.append("Requires authentication, so priority is reduced unless other exposure signals exist.")

    score = max(0, min(score, 100))
    priority = _priority_label(score)
    attack_paths = _matched_attack_paths(finding)

    return {
        "id": finding.get("id") or f"corr_{uuid4().hex[:10]}",
        "title": finding.get("title") or "Untitled finding",
        "source": finding.get("source") or "Imported evidence",
        "module": finding.get("module") or "unknown",
        "severity": severity,
        "confidence": _confidence(finding.get("confidence")),
        "priority": priority,
        "priority_score": score,
        "correlation_status": "Correlated" if flags.get("source_verified") or flags.get("scanner_imported") else "Needs evidence",
        "risk_flags": flags,
        "correlation_reasons": reasons,
        "matched_attack_paths": attack_paths,
        "impact": finding.get("impact") or _impact_from_flags(flags),
        "future_risk": finding.get("future_risk") or _future_risk_from_flags(flags),
        "fix_plan": finding.get("fix_plan") or _fix_plan_from_flags(flags),
        "verification_steps": finding.get("verification_steps") or _verification_from_flags(flags),
        "human_review_required": bool(flags.get("manual_review_required") or priority in {"P0", "P1"}),
        "safe_limitation": "Correlation is evidence prioritization only. It does not run exploitation and does not prove the project is secure.",
        "original_finding": finding,
    }


def _matched_attack_paths(finding: dict[str, Any]) -> list[dict[str, Any]]:
    text = _finding_text(finding)
    matches: list[dict[str, Any]] = []
    for template in ATTACK_PATH_TEMPLATES:
        hit_count = sum(1 for signal in template["signals"] if signal in text)
        if hit_count >= 2:
            matches.append({
                "id": template["id"],
                "title": template["title"],
                "match_strength": "high" if hit_count >= 3 else "medium",
                "impact": template["impact"],
                "future_risk": template["future_risk"],
                "fix": template["fix"],
            })
    return matches


def _impact_from_flags(flags: dict[str, bool]) -> str:
    if flags.get("holds_funds_or_unlocks_value"):
        return "This can affect funds, payments, token supply, wallet trust, or paid access if it is reachable in production."
    if flags.get("api_top10_related"):
        return "This can expose or modify project/user data if object-level or function-level authorization is weak."
    if flags.get("has_cve"):
        return "This may be a publicly documented vulnerability. Patch urgency depends on reachability, exploitability, and exposure."
    return "This finding may reduce launch readiness and should be validated with evidence before public release."


def _future_risk_from_flags(flags: dict[str, bool]) -> str:
    if flags.get("known_exploited"):
        return "Known-exploited signals can become urgent because attackers may already have tooling or playbooks."
    if flags.get("internet_exposed"):
        return "Risk grows after public traffic, marketing, investor review, or token launch increases visibility."
    if flags.get("manual_review_required"):
        return "Manual-review gaps can hide business logic or economic failures that scanners may not understand."
    return "Risk increases as users, integrations, treasury value, and operational complexity grow."


def _fix_plan_from_flags(flags: dict[str, bool]) -> dict[str, Any]:
    if flags.get("has_cve") or flags.get("known_exploited"):
        summary = "Patch or remove the affected dependency/component, confirm fixed version, and rerun advisory matching."
    elif flags.get("api_top10_related"):
        summary = "Add server-side authorization checks, negative tests, and logging for every affected object/function path."
    elif flags.get("holds_funds_or_unlocks_value"):
        summary = "Fix the fund/payment/admin control path first, add tests, and require manual review before launch."
    else:
        summary = "Collect stronger evidence, fix the root cause, and rerun the relevant scanner."
    return {"summary": summary, "owner": "engineering/security", "target_sla": "before public launch for P0/P1"}


def _verification_from_flags(flags: dict[str, bool]) -> list[str]:
    steps = ["Re-run the exact scanner/source that produced the finding", "Attach evidence before/after fix"]
    if flags.get("has_cve"):
        steps.append("Confirm patched dependency version and no remaining OSV/NVD/CISA match")
    if flags.get("api_top10_related"):
        steps.append("Add a negative authorization test for a second user/project/workspace")
    if flags.get("holds_funds_or_unlocks_value"):
        steps.append("Add tests for failed/unauthorized fund, payment, or admin-control attempts")
    return steps


def scanner_correlation_status() -> dict[str, Any]:
    return {
        "ok": True,
        "version": PHASE43_VERSION,
        "purpose": "Correlate findings from multiple scanners and context sources into prioritized attack paths and fix playbooks.",
        "safe_status_labels": SAFE_STATUSES,
        "detection_surfaces": DETECTION_SURFACES,
        "not_supported": [
            "exploit execution",
            "brute force or credential stuffing",
            "DoS/stress testing",
            "data extraction",
            "wallet signing",
            "private key/seed collection",
            "all-bug guarantee",
            "certified audit claim",
        ],
        "required_disclaimer": REQUIRED_DISCLAIMER,
        "references": {
            "cvss_note": "CVSS is severity, not full risk; context and exposure still matter.",
            "epss_note": "EPSS-style probability can be added when configured to prioritize likely exploitation within a time window.",
            "api_top10_note": "API authorization/authentication findings should be treated as high-priority launch-readiness risks.",
        },
    }


def scanner_correlation_playbook() -> dict[str, Any]:
    return {
        "ok": True,
        "version": PHASE43_VERSION,
        "playbooks": PLAYBOOKS,
        "attack_path_templates": ATTACK_PATH_TEMPLATES,
        "safe_wording": "Correlation prioritizes evidence and attack paths. It does not perform exploitation and does not replace professional security review.",
    }


def prioritize_findings(payload: dict[str, Any]) -> dict[str, Any]:
    if not bool(payload.get("real_only_acknowledged", True)):
        return {
            "ok": False,
            "status": "Manual review required",
            "message": "Real-only acknowledgement is required. Web3Guard will not fake security or all-bug claims.",
        }
    findings = [item for item in _as_list(payload.get("findings")) if isinstance(item, dict)]
    correlated = [_score_finding(payload, item) for item in findings]
    correlated.sort(key=lambda item: item["priority_score"], reverse=True)

    summary = {"p0": 0, "p1": 0, "p2": 0, "p3": 0}
    for item in correlated:
        summary[item["priority"].lower()] = summary.get(item["priority"].lower(), 0) + 1

    modules = sorted({str(item.get("module") or "unknown") for item in correlated})
    attack_paths = []
    seen_paths: set[str] = set()
    for item in correlated:
        for path in item.get("matched_attack_paths", []):
            if path["id"] not in seen_paths:
                attack_paths.append(path)
                seen_paths.add(path["id"])

    coverage_gaps = _coverage_gaps(payload, modules, correlated)
    recommended_next_action = _recommended_action(summary, coverage_gaps)

    return {
        "ok": True,
        "version": PHASE43_VERSION,
        "correlation_id": f"corr_{uuid4().hex[:12]}",
        "project_name": payload.get("project_name") or "Untitled scanner correlation",
        "generated_at": _now_iso(),
        "input_findings_count": len(findings),
        "correlated_findings_count": len(correlated),
        "priority_summary": summary,
        "top_priority": correlated[0]["priority"] if correlated else "Not assessed",
        "modules_seen": modules,
        "correlated_findings": correlated,
        "attack_paths": attack_paths,
        "coverage_gaps": coverage_gaps,
        "recommended_next_action": recommended_next_action,
        "report_wording": "Web3Guard correlated scanner evidence into prioritized launch-readiness risks. This is not exploitation, not a certified audit, and not an all-bug guarantee.",
        "required_disclaimer": REQUIRED_DISCLAIMER,
    }


def build_attack_path(payload: dict[str, Any]) -> dict[str, Any]:
    result = prioritize_findings(payload)
    if not result.get("ok"):
        return result
    correlated = result.get("correlated_findings", [])
    p0_p1 = [item for item in correlated if item.get("priority") in {"P0", "P1"}]
    chain_steps = []
    for item in p0_p1[:5]:
        chain_steps.append({
            "finding_id": item["id"],
            "title": item["title"],
            "why_it_can_chain": item["correlation_reasons"][:3],
            "stop_condition": item["fix_plan"].get("summary") if isinstance(item.get("fix_plan"), dict) else "Fix and retest",
        })
    return {
        "ok": True,
        "version": PHASE43_VERSION,
        "attack_path_id": f"apath_{uuid4().hex[:12]}",
        "project_name": result.get("project_name"),
        "generated_at": _now_iso(),
        "chainable_findings_count": len(p0_p1),
        "chain_steps": chain_steps,
        "manual_review_required": bool(chain_steps),
        "safe_limitation": "This is a hypothetical attack-path prioritization map. Web3Guard does not exploit or validate destructive impact automatically.",
    }


def _coverage_gaps(payload: dict[str, Any], modules: list[str], correlated: list[dict[str, Any]]) -> list[dict[str, Any]]:
    assessed = payload.get("assessed_modules") if isinstance(payload.get("assessed_modules"), dict) else {}
    required = {
        "slither_or_contract_static": "Smart contract static evidence is needed for Solidity/Vyper risk confidence.",
        "semgrep_or_code_static": "Frontend/backend/API code-pattern evidence is needed for app-layer confidence.",
        "osv_nvd_cisa": "Dependency/CVE/known-exploited intelligence is needed for public vulnerability priority.",
        "authorized_web_dast": "Verified web DAST baseline is needed for website/config exposure confidence.",
        "manual_business_logic_review": "Manual review is required for economic, governance, oracle, bridge, and business logic risk.",
    }
    gaps = []
    for key, reason in required.items():
        if not bool(assessed.get(key)):
            gaps.append({"module": key, "status": "Not assessed", "reason": reason})
    if not correlated:
        gaps.append({"module": "findings_evidence", "status": "Needs evidence", "reason": "No findings were supplied, so Web3Guard cannot claim the project is secure."})
    return gaps


def _recommended_action(summary: dict[str, int], gaps: list[dict[str, Any]]) -> str:
    if summary.get("p0", 0) > 0:
        return "Block public launch until P0 findings are fixed, retested, and manually reviewed."
    if summary.get("p1", 0) > 0:
        return "Fix P1 findings before paid/public launch and add verification evidence to the report."
    if gaps:
        return "Do not claim security. Complete missing scanner evidence and manual-review gates before launch."
    return "No high-priority correlation found in supplied evidence, but this is not a certified audit or all-bug guarantee."


def scanner_correlation_claim_check(text: str) -> dict[str, Any]:
    lowered = text.lower()
    violations = [claim for claim in BLOCKED_CLAIMS if claim in lowered]
    return {
        "ok": len(violations) == 0,
        "violations": violations,
        "allowed_rewrite": (
            "Web3Guard correlates configured scanner evidence, CVE/CWE context, and project exposure into prioritized pre-audit risks. "
            "It does not perform destructive exploitation, does not guarantee that all bugs are found, and does not replace a professional audit."
        ),
        "required_disclaimer": REQUIRED_DISCLAIMER,
    }
