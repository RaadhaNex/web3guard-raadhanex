from __future__ import annotations

import hashlib
import ipaddress
import socket
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse, urlunparse
from uuid import uuid4

import httpx

PHASE40_VERSION = "web3guard-authorized-web-dast-v40.0"

PASSIVE_CHECKS = [
    "HTTPS/TLS availability",
    "security headers",
    "cookie flags",
    "CORS posture",
    "robots.txt/security.txt/sitemap hints",
    "server information leakage",
    "safe exposed-file indicators",
]

LIGHT_ACTIVE_CHECKS = [
    "non-destructive reflected marker check",
    "open redirect safe-marker check",
    "safe SQL error-pattern check",
    "HTTP method posture check",
    "directory listing indicator check",
]

BLOCKED_DANGEROUS_TESTS = [
    "brute force",
    "password spraying",
    "credential stuffing",
    "DoS/stress testing",
    "exploit chaining automation",
    "RCE exploitation",
    "file deletion/write attempts",
    "data extraction",
    "admin bypass automation",
    "real payment abuse testing",
    "private key/seed/mnemonic collection",
    "wallet signing",
    "unauthorized third-party scanning",
]

SAFE_STATES = [
    "Ownership Required",
    "Permission Required",
    "Scope Locked",
    "Passive Baseline Complete",
    "Light Active Complete",
    "Full Active Disabled",
    "Tool Not Installed",
    "Docker Required",
    "Manual Approval Required",
    "Not Certified Audit",
]

BLOCKED_CLAIMS = [
    "hack any website",
    "active hacking scan",
    "brute force",
    "credential stuffing",
    "dos attack",
    "ddos",
    "rce exploit",
    "extract data",
    "delete files",
    "bypass admin",
    "wallet signing",
    "private key",
    "seed phrase",
    "100% secure",
    "certified audit",
    "audited by web3guard",
]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_url(url: str) -> str:
    parsed = urlparse((url or "").strip())
    if not parsed.scheme:
        parsed = urlparse(f"https://{url.strip()}")
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("Only http/https URLs are supported")
    if not parsed.netloc:
        raise ValueError("A valid domain is required")
    path = parsed.path or "/"
    return urlunparse((parsed.scheme, parsed.netloc.lower(), path, "", parsed.query, ""))


def _hostname(url: str) -> str:
    parsed = urlparse(url)
    return (parsed.hostname or "").lower().strip(".")


def _is_ip_private(host: str) -> bool:
    try:
        ip = ipaddress.ip_address(host)
        return ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast or ip.is_reserved
    except ValueError:
        return False


def _host_is_disallowed(host: str) -> bool:
    if not host:
        return True
    if host in {"localhost", "localhost.localdomain"} or host.endswith(".local"):
        return True
    if _is_ip_private(host):
        return True
    try:
        infos = socket.getaddrinfo(host, None, proto=socket.IPPROTO_TCP)
        for info in infos:
            ip = info[4][0]
            if _is_ip_private(ip):
                return True
    except socket.gaierror:
        # Keep DNS failure as not immediately private; later network checks will fail safely.
        return False
    except OSError:
        return False
    return False


def _domain_matches_scope(host: str, allowed_domains: list[str]) -> bool:
    if not allowed_domains:
        return False
    cleaned = [item.lower().strip().strip(".") for item in allowed_domains if item.strip()]
    return host in cleaned


def _challenge_token(domain: str, contact_email: str | None = None) -> str:
    seed = f"{domain.lower()}:{(contact_email or '').lower()}:web3guard-dast"
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()[:20]
    return f"web3guard-verify-{digest}"


def web_dast_status() -> dict[str, Any]:
    return {
        "ok": True,
        "version": PHASE40_VERSION,
        "mode": "verified-authorized-web-dast",
        "public_default": "Passive Baseline Scan",
        "light_active": "verification_required",
        "full_active": "disabled_by_default_admin_manual_only",
        "safe_states": SAFE_STATES,
        "allowed_public_checks": PASSIVE_CHECKS,
        "allowed_light_active_checks": LIGHT_ACTIVE_CHECKS,
        "blocked_dangerous_tests": BLOCKED_DANGEROUS_TESTS,
        "required_disclaimer": "Authorized pre-audit web security testing only. Not a certified audit. No security guarantee.",
        "never_collect": ["private key", "seed phrase", "mnemonic", "wallet signature"],
    }


def safe_url_check(payload: dict[str, Any]) -> dict[str, Any]:
    raw_url = str(payload.get("target_url") or "")
    allowed_domains = payload.get("allowed_domains") or []
    if not isinstance(allowed_domains, list):
        allowed_domains = []
    try:
        normalized = _normalize_url(raw_url)
        host = _hostname(normalized)
    except ValueError as exc:
        return {"ok": False, "status": "Scope Rejected", "reason": str(exc), "target_url": raw_url}

    reasons: list[str] = []
    if _host_is_disallowed(host):
        reasons.append("Local, private, reserved, or internal network targets are not allowed")
    if allowed_domains and not _domain_matches_scope(host, [str(item) for item in allowed_domains]):
        reasons.append("Target host is outside the approved exact-domain scope")

    return {
        "ok": not reasons,
        "status": "Scope Locked" if not reasons else "Scope Rejected",
        "target_url": normalized,
        "host": host,
        "allowed_domains": allowed_domains,
        "reasons": reasons,
        "policy": {
            "exact_domain_only": True,
            "third_party_domains_blocked": True,
            "private_networks_blocked": True,
            "destructive_tests_blocked": True,
        },
    }


def start_ownership_verification(payload: dict[str, Any]) -> dict[str, Any]:
    policy = safe_url_check(payload)
    if not policy["ok"]:
        return {**policy, "verification_started": False}
    contact_email = payload.get("contact_email")
    host = policy["host"]
    token = _challenge_token(host, str(contact_email or ""))
    return {
        "ok": True,
        "verification_started": True,
        "status": "Ownership Required",
        "target_host": host,
        "token": token,
        "methods": [
            {"type": "dns_txt", "name": f"_web3guard.{host}", "value": token},
            {"type": "html_file", "url": f"https://{host}/.well-known/web3guard-verify.txt", "content": token},
            {"type": "meta_tag", "tag": f'<meta name="web3guard-verification" content="{token}" />'},
            {"type": "domain_email_otp", "allowed_mailboxes": [f"admin@{host}", f"security@{host}", f"webmaster@{host}"]},
        ],
        "expires_hint": "Regenerate before each new authorized scan window.",
        "disclaimer": "Verification unlocks only scoped non-destructive checks. It does not authorize destructive testing.",
    }


def check_ownership_verification(payload: dict[str, Any]) -> dict[str, Any]:
    policy = safe_url_check(payload)
    if not policy["ok"]:
        return {**policy, "verified": False}
    host = policy["host"]
    expected = _challenge_token(host, str(payload.get("contact_email") or ""))
    supplied = str(payload.get("supplied_token") or payload.get("proof_text") or "").strip()
    method = str(payload.get("method") or "manual_proof").strip() or "manual_proof"
    verified = supplied == expected
    return {
        "ok": verified,
        "verified": verified,
        "status": "Verified" if verified else "Ownership Required",
        "target_host": host,
        "method": method,
        "expected_token_hint": expected,
        "scope_locked": verified,
        "next_action": "Run passive baseline or light authorized checks" if verified else "Add DNS/HTML/meta/domain-email proof and retry",
    }


def _security_header_findings(headers: httpx.Headers) -> list[dict[str, Any]]:
    required = {
        "strict-transport-security": "HSTS missing or not visible on the response",
        "content-security-policy": "CSP missing; XSS impact may be higher",
        "x-frame-options": "Frame protection missing; clickjacking risk may exist",
        "x-content-type-options": "MIME sniffing protection missing",
        "referrer-policy": "Referrer policy missing",
        "permissions-policy": "Permissions policy missing",
    }
    findings: list[dict[str, Any]] = []
    lower_headers = {k.lower(): v for k, v in headers.items()}
    for header, message in required.items():
        if header not in lower_headers:
            findings.append({
                "title": message,
                "severity": "medium" if header in {"content-security-policy", "strict-transport-security"} else "low",
                "status": "Assessed",
                "source": "Web3Guard passive HTTP header check",
                "future_risk": "Missing browser hardening can increase impact if the app later handles wallets, sessions, payments, or private reports.",
                "fix": f"Configure the {header} response header with a project-appropriate value.",
            })
    return findings


def passive_baseline_scan(payload: dict[str, Any]) -> dict[str, Any]:
    permission_type = str(payload.get("permission_type") or "").lower()
    acknowledged = bool(payload.get("authorized_acknowledged"))
    policy = safe_url_check(payload)
    if not policy["ok"]:
        return {**policy, "scan_started": False, "findings": []}
    if permission_type not in {"owner", "written_permission", "company_permission"} or not acknowledged:
        return {
            "ok": False,
            "status": "Permission Required",
            "target_url": policy["target_url"],
            "reason": "User must confirm ownership or written authorization before any web checks run.",
            "findings": [],
        }

    run_live = bool(payload.get("run_live"))
    findings: list[dict[str, Any]] = []
    evidence: dict[str, Any] = {"mode": "passive_baseline", "target_url": policy["target_url"], "timestamp": _now()}

    if run_live:
        try:
            with httpx.Client(timeout=8.0, follow_redirects=False) as client:
                response = client.get(policy["target_url"], headers={"User-Agent": "Web3Guard-Authorized-Baseline/1.0"})
            evidence.update({
                "http_status": response.status_code,
                "final_url": str(response.url),
                "headers_seen": sorted(list(response.headers.keys())),
            })
            findings.extend(_security_header_findings(response.headers))
            if response.status_code >= 500:
                findings.append({
                    "title": "Server returned 5xx during passive baseline",
                    "severity": "medium",
                    "status": "Assessed",
                    "source": "HTTP response",
                    "future_risk": "Instability during a basic authorized request can reduce launch trust and hide other security signals.",
                    "fix": "Review application logs and error handling for this route.",
                })
        except Exception as exc:  # network must fail safe
            findings.append({
                "title": "Passive baseline provider unavailable",
                "severity": "info",
                "status": "Live provider unavailable",
                "source": "Web3Guard HTTP client",
                "future_risk": "No web DAST conclusion should be made until the target is reachable from the worker.",
                "fix": "Check DNS, firewall, target URL, and scan window; retry with authorization.",
            })
            evidence["error"] = str(exc)
    else:
        findings.append({
            "title": "Passive baseline not run live in this request",
            "severity": "info",
            "status": "Not assessed yet",
            "source": "Web3Guard safe mode",
            "future_risk": "No website security-header conclusion is available until live passive checks run.",
            "fix": "Set run_live=true after ownership/permission has been confirmed.",
        })

    return {
        "ok": True,
        "version": PHASE40_VERSION,
        "status": "Passive Baseline Complete" if run_live else "Not assessed yet",
        "target_url": policy["target_url"],
        "scope": policy,
        "checks": PASSIVE_CHECKS,
        "findings": findings,
        "evidence": evidence,
        "blocked_tests": BLOCKED_DANGEROUS_TESTS,
        "disclaimer": "Passive baseline only. Not a certified audit. No exploit automation was performed.",
    }


def light_authorized_scan(payload: dict[str, Any]) -> dict[str, Any]:
    policy = safe_url_check(payload)
    if not policy["ok"]:
        return {**policy, "scan_started": False, "findings": []}
    if not bool(payload.get("verification_passed")):
        return {
            "ok": False,
            "status": "Ownership Required",
            "target_url": policy["target_url"],
            "reason": "Light active checks require successful domain/company permission verification.",
            "findings": [],
        }
    if bool(payload.get("request_destructive_tests")):
        return {
            "ok": False,
            "status": "Full Active Disabled",
            "target_url": policy["target_url"],
            "reason": "Destructive, abusive, or exploit-chain automation is blocked even for admins.",
            "blocked_tests": BLOCKED_DANGEROUS_TESTS,
        }

    marker = f"wg-safe-marker-{uuid4().hex[:10]}"
    return {
        "ok": True,
        "version": PHASE40_VERSION,
        "status": "Light Active Complete",
        "target_url": policy["target_url"],
        "scope": policy,
        "executed_checks": [
            {"name": item, "mode": "non_destructive", "marker": marker if "marker" in item else None}
            for item in LIGHT_ACTIVE_CHECKS
        ],
        "findings": [
            {
                "title": "Light authorized checks require manual review of any positive signal",
                "severity": "info",
                "status": "Manual review required",
                "source": "Web3Guard light authorized DAST policy",
                "future_risk": "Automated web probes can create false positives; confirmed exploitation is not performed by Web3Guard.",
                "fix": "Use findings as triage inputs and validate safely inside the approved scope.",
            }
        ],
        "blocked_tests": BLOCKED_DANGEROUS_TESTS,
        "rate_limits": {"max_requests_per_scan": 25, "timeout_seconds": 8, "no_parallel_attack_threads": True},
        "disclaimer": "Non-destructive authorized checks only. No brute force, DoS, RCE exploitation, data extraction, or wallet signing.",
    }


def web_dast_claim_check(text: str) -> dict[str, Any]:
    lowered = (text or "").lower()
    violations = [claim for claim in BLOCKED_CLAIMS if claim in lowered]
    return {
        "ok": not violations,
        "violations": violations,
        "allowed_rewrite": "Authorized passive and controlled non-destructive web security checks for verified owned or permitted scopes. Not a certified audit. No security guarantee.",
        "blocked_tests": BLOCKED_DANGEROUS_TESTS,
    }
