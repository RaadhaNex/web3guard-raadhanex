from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from urllib.parse import urlparse

from app.models.schemas import ChecklistItem, Finding, ModuleScore, ScanResponse
from app.services.checklists import CHECKLIST_RULES, MODULE_COPY
from app.services.scoring import priority_actions, risk_label, score_findings, severity_breakdown
from app.services.scan_website import validate_public_http_url

EVM_ADDRESS_RE = re.compile(r"0x[a-fA-F0-9]{40}")
NEXT_PUBLIC_SECRET_RE = re.compile(r"NEXT_PUBLIC_[A-Z0-9_]*(?:SECRET|PRIVATE|TOKEN|KEY|API)[A-Z0-9_]*", re.I)
RPC_PROVIDER_RE = re.compile(r"https://[^\s'\"]*(?:alchemy|infura|quicknode|ankr|moralis|thirdweb|rpc)[^\s'\"]*", re.I)
UNLIMITED_APPROVAL_RE = re.compile(r"(?:MaxUint256|constants\.MaxUint256|setApprovalForAll\s*\([^)]*true|approve\s*\([^)]*(?:2\s*\*\*\s*256|0xffff))", re.I | re.S)
AUTO_CONNECT_RE = re.compile(r"(?:autoConnect\s*[:=]\s*true|connect\s*\(\s*\)|enable\s*\(\s*\))", re.I)
CHAIN_CHECK_RE = re.compile(r"(?:chainId|wallet_switchEthereumChain|switchNetwork|switchChain|expectedChain|supportedChains)", re.I)
TX_PREVIEW_RE = re.compile(r"(?:spender|allowance|amount|recipient|toAddress|transactionPreview|previewTransaction|estimatedGas)", re.I)
DANGEROUS_RENDER_RE = re.compile(r"(?:dangerouslySetInnerHTML|innerHTML\s*=|eval\s*\(|new\s+Function\s*\()", re.I)
BLIND_SIGN_RE = re.compile(r"(?:eth_sign|personal_sign|signMessage\s*\(|signTypedData)", re.I)

CORS_WILDCARD_RE = re.compile(r"(?:allow_origins\s*=\s*\[\s*['\"]\*['\"]\s*\]|Access-Control-Allow-Origin\s*[:=]\s*['\"]\*|cors\s*\(\s*\))", re.I)
RATE_LIMIT_RE = re.compile(r"(?:rate.?limit|slowapi|limiter|express-rate-limit|throttle|django-ratelimit|Flask-Limiter)", re.I)
AUTH_RE = re.compile(r"(?:Depends\s*\([^)]*auth|Authorization|Bearer|jwt|session|requireAuth|isAuthenticated|authMiddleware)", re.I)
WEBHOOK_SIG_RE = re.compile(r"(?:signature|x-razorpay-signature|stripe-signature|webhookSecret|verifyWebhook|hmac)", re.I)
DEBUG_RE = re.compile(r"(?:debug\s*=\s*true|DEBUG\s*=\s*True|app\.run\s*\([^)]*debug\s*=\s*True)", re.I)
DOCS_RE = re.compile(r"(?:/docs|/swagger|openapi\.json|swaggerUi|graphiql|graphql)", re.I)
HARDCODED_SECRET_RE = re.compile(r"(?:JWT_SECRET|SECRET_KEY|API_KEY|PRIVATE_KEY)\s*[:=]\s*['\"][^'\"]{8,}['\"]", re.I)
IDOR_HINT_RE = re.compile(r"(?:/users?/\{?id\}?|user_id|customer_id|owner_id|project_id)", re.I)

DAPP_CHECKLIST_LABELS = {
    "secrets": "No frontend-exposed secrets/API keys",
    "chain_check": "dApp checks chain ID before transaction",
    "tx_preview": "Transaction preview clearly shows token/amount/spender",
    "dangerous_html": "No unsafe HTML rendering in sensitive pages",
    "auto_connect": "Wallet does not auto-connect or auto-trigger transactions on page load",
    "approval_warning": "Unlimited approvals/setApprovalForAll are clearly warned and minimized",
    "verified_contract": "UI shows verified contract address, network, and explorer link",
    "dependency_review": "Frontend dependencies are reviewed before launch",
}

API_CHECKLIST_LABELS = {
    "rate_limit": "API has rate limiting",
    "auth": "Sensitive API routes require auth + authorization",
    "cors": "CORS is restricted to trusted origins",
    "webhook_signature": "Webhooks verify signatures",
    "docs_exposure": "Public docs/admin/debug endpoints are intentionally scoped",
    "error_masking": "Errors do not leak stack traces, secrets, or internal IDs",
    "input_validation": "Request validation exists for all public endpoints",
    "audit_logs": "Admin/payment/security actions are audit logged",
    "idor_review": "BOLA/IDOR object-level authorization is reviewed",
}


def _base_findings_from_checklist(module: str, checklist: list[ChecklistItem]) -> list[Finding]:
    answers = {item.key: item.answer for item in checklist}
    findings: list[Finding] = []
    idx = 1
    rules = CHECKLIST_RULES.get(module, {})
    for key, (severity, title, desc) in rules.items():
        answer = answers.get(key, "unknown")
        if answer in {"no", "unknown"}:
            confidence = "high" if answer == "no" else "low"
            findings.append(_finding(
                module=module,
                idx=idx,
                severity=severity,
                title=title,
                description=desc,
                category=f"checklist:{key}",
                rule_id=f"{module.upper()}-CHECK-{key.upper()}",
                confidence=confidence,
                source="Checklist Engine",
                business_impact=MODULE_COPY[module][1],
                developer_explanation=f"Checklist answer for {key}: {answer}. Confirm this before public launch.",
                recommendation="Document the current setup, fix gaps, and request manual review for high-risk launch flows.",
                paid=severity in {"critical", "high"},
            ))
            idx += 1
    return findings


def _finding(*, module: str, idx: int, severity: str, title: str, description: str, category: str, rule_id: str,
             confidence: str, source: str, business_impact: str, developer_explanation: str, recommendation: str,
             paid: bool = False, affected_line: int | None = None, affected_code: str | None = None,
             references: list[str] | None = None) -> Finding:
    fingerprint = hashlib.sha1(f"{module}:{rule_id}:{title}:{affected_line}:{affected_code or ''}".encode()).hexdigest()[:14]
    return Finding(
        id=f"{module}-{idx}-{fingerprint}",
        module=module,  # type: ignore[arg-type]
        severity=severity,  # type: ignore[arg-type]
        title=title,
        description=description,
        affected_line=affected_line,
        affected_code=affected_code,
        confidence=confidence,  # type: ignore[arg-type]
        source=source,
        category=category,
        rule_id=rule_id,
        fingerprint=fingerprint,
        business_impact=business_impact,
        developer_explanation=developer_explanation,
        recommendation=recommendation,
        references=references or [],
        paid_review_recommended=paid,
    )


def _line_for(code: str, pattern: re.Pattern[str]) -> tuple[int | None, str | None]:
    match = pattern.search(code)
    if not match:
        return None, None
    line = code[:match.start()].count("\n") + 1
    start = max(0, match.start() - 80)
    end = min(len(code), match.end() + 80)
    return line, code[start:end].strip()


def _safe_json(text: str | None) -> dict:
    if not text or not text.strip():
        return {}
    try:
        parsed = json.loads(text)
        return parsed if isinstance(parsed, dict) else {}
    except json.JSONDecodeError:
        return {}


def _dependency_version(deps: dict, name: str) -> str | None:
    value = deps.get(name)
    return str(value) if value is not None else None


def scan_dapp_frontend(
    *,
    checklist: list[ChecklistItem],
    project_name: str | None = None,
    frontend_code: str | None = None,
    package_json: str | None = None,
    notes: str | None = None,
) -> ScanResponse:
    code = "\n".join(part for part in [frontend_code or "", notes or ""] if part)
    findings = _base_findings_from_checklist("dapp", checklist)
    idx = len(findings) + 1

    if code:
        checks: list[tuple[re.Pattern[str], str, str, str, str, str, str, bool, list[str]]] = [
            (NEXT_PUBLIC_SECRET_RE, "high", "Frontend-Exposed Secret Naming Risk", "NEXT_PUBLIC variables are bundled into the browser. Secrets, private keys, privileged API keys, or admin tokens must not use public env prefixes.", "secrets", "DAPP-CODE-NEXT-PUBLIC-SECRET", "Move sensitive keys to backend-only environment variables and expose only limited public config.", True, ["Next.js public env variables"]),
            (RPC_PROVIDER_RE, "medium", "Hardcoded RPC Provider URL", "Provider URLs/API keys in frontend can be scraped, abused, or rate-limited by attackers.", "config", "DAPP-CODE-RPC", "Use backend proxy or restricted/public-safe keys with domain restrictions and quota limits.", False, ["RPC key exposure"]),
            (EVM_ADDRESS_RE, "low", "Hardcoded Contract Address Found", "Hardcoded addresses are not always wrong, but users need chain ID, explorer link, and verified address clarity.", "contract_address", "DAPP-CODE-ADDRESS", "Pair every address with chain ID, explorer link, config file, and deployment environment checks.", False, ["contract verification"]),
            (DANGEROUS_RENDER_RE, "high", "Unsafe Frontend Rendering / Eval Pattern", "Unsafe rendering can create XSS or transaction manipulation risk on mint/claim pages.", "xss", "DAPP-CODE-DANGEROUS-RENDER", "Remove eval/new Function/innerHTML and sanitize any unavoidable rich content.", True, ["XSS risk"]),
            (UNLIMITED_APPROVAL_RE, "high", "Unlimited Approval / setApprovalForAll Pattern", "Unlimited approvals or setApprovalForAll can expose user funds if spender or operator is compromised.", "approval", "DAPP-CODE-UNLIMITED-APPROVAL", "Ask only for required allowance, show spender, amount, token, and a clear warning.", True, ["approval risk"]),
            (AUTO_CONNECT_RE, "medium", "Wallet Auto-Connect / Auto-Trigger Hint", "Auto-connecting wallets or triggering wallet prompts too early can look phishing-like and reduce trust.", "wallet_ux", "DAPP-CODE-AUTO-CONNECT", "Use explicit user action before connecting or requesting signatures/transactions.", False, ["wallet UX"]),
            (BLIND_SIGN_RE, "medium", "Signature Flow Needs Clarity", "Signature methods can be abused if the user does not clearly understand what they are signing.", "signature", "DAPP-CODE-SIGNATURE", "Use typed data where possible, show human-readable message purpose, domain, and expiry.", False, ["blind signing"]),
        ]
        for pattern, severity, title, desc, category, rule_id, rec, paid, refs in checks:
            line, snippet = _line_for(code, pattern)
            if line:
                findings.append(_finding(
                    module="dapp",
                    idx=idx,
                    severity=severity,
                    title=title,
                    description=desc,
                    category=category,
                    rule_id=rule_id,
                    confidence="high",
                    source="dApp Code Hint Engine",
                    business_impact="Frontend risk can make users sign the wrong transaction, expose project infrastructure, or damage launch trust.",
                    developer_explanation=f"Pattern detected near line {line}. This is a preliminary code hint, not a full source audit.",
                    recommendation=rec,
                    paid=paid,
                    affected_line=line,
                    affected_code=snippet,
                    references=refs,
                ))
                idx += 1

        if not CHAIN_CHECK_RE.search(code):
            findings.append(_finding(
                module="dapp", idx=idx, severity="medium", title="Chain ID Check Not Evident in Provided Code", description="No obvious chain/network validation pattern was found in the provided frontend snippet.", category="chain", rule_id="DAPP-CODE-MISSING-CHAIN-CHECK", confidence="medium", source="dApp Code Hint Engine", business_impact="Users may sign transactions on the wrong network, leading to failed launches or user confusion.", developer_explanation="The code hint engine did not see chainId, switchNetwork, switchChain, or similar checks.", recommendation="Validate expected chain ID before any transaction, and offer safe network switching with clear copy.", references=["chain mismatch"],
            ))
            idx += 1
        if not TX_PREVIEW_RE.search(code):
            findings.append(_finding(
                module="dapp", idx=idx, severity="medium", title="Transaction Preview Not Evident in Provided Code", description="No obvious token/amount/spender/recipient preview pattern was found.", category="transaction_preview", rule_id="DAPP-CODE-MISSING-TX-PREVIEW", confidence="medium", source="dApp Code Hint Engine", business_impact="Users may approve or send assets without understanding amount, spender, recipient, or contract risk.", developer_explanation="The scanner checks for preview-related labels/variables, but manual UX review is still required.", recommendation="Show contract address, token, amount, spender/recipient, chain, and risk notes before opening the wallet.", references=["transaction UX"],
            ))
            idx += 1

    pkg = _safe_json(package_json)
    deps = {}
    for key in ["dependencies", "devDependencies"]:
        if isinstance(pkg.get(key), dict):
            deps.update(pkg[key])
    if deps:
        risky_deps = []
        for dep in ["web3modal", "@walletconnect/client", "@walletconnect/web3-provider"]:
            version = _dependency_version(deps, dep)
            if version and re.search(r"(?:\^|~)?1\.", version):
                risky_deps.append(f"{dep}@{version}")
        for dep in ["ethereumjs-wallet", "bip39", "hdkey"]:
            version = _dependency_version(deps, dep)
            if version:
                risky_deps.append(f"{dep}@{version}")
        if risky_deps:
            findings.append(_finding(
                module="dapp", idx=idx, severity="medium", title="Frontend Dependency Review Needed", description="Wallet/seed/key-management related or older Web3 dependencies were found in package.json.", category="dependencies", rule_id="DAPP-PKG-DEPENDENCY-REVIEW", confidence="medium", source="package.json Hint Engine", business_impact="Dependency issues can affect wallet connection security, bundle trust, and user signing safety.", developer_explanation=f"Detected dependencies: {', '.join(risky_deps)}", recommendation="Review package versions, remove client-side seed/key libraries unless absolutely required, and run npm audit plus manual dependency review.", references=["dependency risk"],
            ))
            idx += 1

    score = score_findings(findings)
    input_hash = hashlib.sha256((code + (package_json or "")).encode()).hexdigest()[:16] if (code or package_json) else None
    return ScanResponse(
        report_id=f"W3G-DAPP-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
        generated_at=datetime.now(timezone.utc),
        project_name=project_name,
        module_score=ModuleScore(module="dapp", score=score, risk_label=risk_label(score)),
        findings=findings,
        severity_breakdown=severity_breakdown(findings),
        priority_actions=priority_actions(findings),
        input_hash=input_hash,
        engine_version="web3guard-dapp-frontend-engine-v2.6",
        scan_metadata={
            "mode": "checklist_plus_optional_code_package_hints",
            "code_provided": bool(frontend_code),
            "package_json_provided": bool(package_json),
            "notes_provided": bool(notes),
            "safety_controls": {
                "no_exploit_execution": True,
                "no_package_install": True,
                "static_hints_only": True,
                "manual_review_recommended_for_high_risk_flows": True,
            },
        },
    )


def scan_api_backend(
    *,
    checklist: list[ChecklistItem],
    project_name: str | None = None,
    api_base_url: str | None = None,
    api_code: str | None = None,
    notes: str | None = None,
) -> ScanResponse:
    code = "\n".join(part for part in [api_code or "", notes or ""] if part)
    findings = _base_findings_from_checklist("api", checklist)
    idx = len(findings) + 1
    metadata: dict = {
        "mode": "checklist_plus_optional_config_url_hints",
        "api_url_provided": bool(api_base_url),
        "api_code_provided": bool(api_code),
        "notes_provided": bool(notes),
        "safety_controls": {
            "passive_only": True,
            "no_auth_bypass": True,
            "no_fuzzing": True,
            "no_payload_testing": True,
        },
    }

    if api_base_url:
        safe_url = validate_public_http_url(api_base_url)
        parsed = urlparse(safe_url)
        metadata["validated_api_base"] = f"{parsed.scheme}://{parsed.netloc}"
        metadata["docs_endpoint_hints"] = ["/docs", "/swagger", "/openapi.json", "/graphql"]
        findings.append(_finding(
            module="api", idx=idx, severity="info", title="API URL Accepted for Passive Checklist Review", description="The API base URL passed public URL safety validation. Web3Guard does not fuzz or probe authenticated APIs.", category="api_url", rule_id="API-URL-SAFE-VALIDATED", confidence="high", source="API URL Safety Validator", business_impact="Safe URL validation reduces abuse risk while keeping the scanner useful for launch readiness.", developer_explanation="The scanner validates public http/https URL and blocks localhost/private/internal network targets.", recommendation="For deeper API scanning, add ownership verification and explicit scope before enabling active checks.", references=["passive API review"],
        ))
        idx += 1

    if code:
        checks: list[tuple[re.Pattern[str], str, str, str, str, str, str, bool, list[str]]] = [
            (CORS_WILDCARD_RE, "high", "Overly Open CORS Pattern", "Wildcard or unconfigured CORS can expose APIs to untrusted origins, especially when cookies or tokens are involved.", "cors", "API-CODE-WILDCARD-CORS", "Restrict CORS to trusted frontend domains and avoid credentials with wildcard origins.", True, ["CORS"]),
            (DEBUG_RE, "high", "Debug Mode / Verbose Error Risk", "Debug mode can leak stack traces, environment details, and internal routes.", "debug", "API-CODE-DEBUG", "Disable debug mode in production and return sanitized errors.", True, ["error leakage"]),
            (HARDCODED_SECRET_RE, "critical", "Hardcoded Backend Secret Pattern", "Backend secrets in code can compromise auth, payments, webhooks, or admin access if leaked.", "secrets", "API-CODE-HARDCODED-SECRET", "Move secrets to backend environment variables or a secret manager, rotate exposed secrets, and avoid committing .env files.", True, ["secret management"]),
            (DOCS_RE, "medium", "Public Docs/GraphQL Endpoint Needs Scope Review", "Public docs and GraphQL endpoints are useful, but they can reveal internal API shape if not scoped.", "docs", "API-CODE-DOCS", "Disable or protect docs in production, or provide limited public documentation only.", False, ["API docs exposure"]),
        ]
        for pattern, severity, title, desc, category, rule_id, rec, paid, refs in checks:
            line, snippet = _line_for(code, pattern)
            if line:
                findings.append(_finding(
                    module="api", idx=idx, severity=severity, title=title, description=desc, category=category, rule_id=rule_id, confidence="high", source="API Code Hint Engine", business_impact="API risk can expose allowlists, rewards, payment state, admin actions, or user/project data.", developer_explanation=f"Pattern detected near line {line}. This is a preliminary config/code hint, not an authenticated penetration test.", recommendation=rec, paid=paid, affected_line=line, affected_code=snippet, references=refs,
                ))
                idx += 1

        if not RATE_LIMIT_RE.search(code):
            findings.append(_finding(
                module="api", idx=idx, severity="high", title="Rate Limiting Not Evident in Provided API Code", description="No obvious rate limiting/throttling middleware was found in the provided API snippet.", category="rate_limit", rule_id="API-CODE-MISSING-RATE-LIMIT", confidence="medium", source="API Code Hint Engine", business_impact="Public APIs can be abused for scraping, spam, wallet allowlist abuse, payment reference spam, or denial-of-service.", developer_explanation="The scanner looks for common rate-limit library/middleware names. Confirm manually if rate limiting lives elsewhere.", recommendation="Add per-IP and per-account rate limits for public scan, lead, auth, payment, and webhook endpoints.", paid=True, references=["abuse prevention"],
            ))
            idx += 1
        if not AUTH_RE.search(code):
            findings.append(_finding(
                module="api", idx=idx, severity="high", title="Authentication/Authorization Not Evident", description="No obvious auth middleware, token, session, or authorization dependency was found in the provided API snippet.", category="auth", rule_id="API-CODE-MISSING-AUTH", confidence="medium", source="API Code Hint Engine", business_impact="Sensitive project/admin endpoints may expose data or state-changing actions without proper authorization.", developer_explanation="Auth may be in another file; still, every sensitive endpoint should have object-level authorization checks.", recommendation="Add auth middleware and explicit object-level authorization for user/project/admin resources.", paid=True, references=["BOLA/IDOR"],
            ))
            idx += 1
        if not WEBHOOK_SIG_RE.search(code) and re.search(r"webhook|razorpay|stripe|payment", code, re.I):
            findings.append(_finding(
                module="api", idx=idx, severity="high", title="Webhook Signature Verification Not Evident", description="Payment or webhook code appears present, but no obvious signature verification pattern was found.", category="webhook", rule_id="API-CODE-MISSING-WEBHOOK-SIGNATURE", confidence="medium", source="API Code Hint Engine", business_impact="Attackers may forge payment/status callbacks if webhook signatures are not verified.", developer_explanation="The scanner checks for common signature/HMAC fields; confirm manually if verification happens elsewhere.", recommendation="Verify Razorpay/Stripe/third-party webhook signatures before trusting any event payload.", paid=True, references=["webhook security"],
            ))
            idx += 1
        if IDOR_HINT_RE.search(code) and not re.search(r"owner|permission|authorize|org_id|tenant", code, re.I):
            findings.append(_finding(
                module="api", idx=idx, severity="medium", title="BOLA/IDOR Authorization Review Needed", description="Object identifiers appear in routes or parameters; object-level authorization must be verified.", category="idor", rule_id="API-CODE-IDOR-REVIEW", confidence="medium", source="API Code Hint Engine", business_impact="Users may access another project/user/resource if object-level authorization is missing.", developer_explanation="IDOR/BOLA cannot be proven from snippets alone, so this is a manual review prompt.", recommendation="For every object ID, verify the requester owns or is authorized for that object before returning or modifying data.", paid=False, references=["BOLA", "IDOR"],
            ))
            idx += 1

    score = score_findings(findings)
    input_hash = hashlib.sha256((code + (api_base_url or "")).encode()).hexdigest()[:16] if (code or api_base_url) else None
    return ScanResponse(
        report_id=f"W3G-API-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
        generated_at=datetime.now(timezone.utc),
        project_name=project_name,
        module_score=ModuleScore(module="api", score=score, risk_label=risk_label(score)),
        findings=findings,
        severity_breakdown=severity_breakdown(findings),
        priority_actions=priority_actions(findings),
        input_hash=input_hash,
        engine_version="web3guard-api-backend-engine-v2.6",
        scan_metadata=metadata,
    )


def enhanced_checklist_template(module: str) -> list[dict]:
    if module == "dapp":
        return [{"key": key, "label": label, "answer": "unknown"} for key, label in DAPP_CHECKLIST_LABELS.items()]
    if module == "api":
        return [{"key": key, "label": label, "answer": "unknown"} for key, label in API_CHECKLIST_LABELS.items()]
    raise ValueError("Enhanced template only supports dapp/api")
