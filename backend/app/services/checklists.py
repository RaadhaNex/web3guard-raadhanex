from datetime import datetime, timezone
from app.models.schemas import ChecklistItem, Finding, ModuleScore, ScanResponse
from app.services.scoring import risk_label, score_findings

CHECKLIST_RULES = {
    "dapp": {
        "secrets": ("high", "Exposed Frontend Secret Risk", "API keys or secrets should not be exposed in frontend bundles."),
        "chain_check": ("medium", "Missing Chain ID Check", "Users may sign transactions on the wrong network."),
        "tx_preview": ("medium", "Missing Transaction Preview", "Users need a clear preview of amount, token, spender, and contract."),
        "dangerous_html": ("high", "Unsafe HTML Rendering Risk", "dangerouslySetInnerHTML, eval, or unsafe rendering can create frontend security risk."),
        "auto_connect": ("medium", "Wallet Auto-Connect Needs Review", "Wallet prompts should be user-triggered and clearly explained."),
        "approval_warning": ("high", "Approval Warning Missing", "Unlimited approvals and setApprovalForAll flows need clear warnings."),
        "verified_contract": ("medium", "Verified Contract Display Missing", "Users should see contract address, chain, and explorer verification before signing."),
        "dependency_review": ("medium", "Frontend Dependency Review Missing", "Wallet and Web3 dependencies should be reviewed before launch."),
    },
    "api": {
        "rate_limit": ("high", "Missing Rate Limit", "APIs without rate limits are easier to abuse."),
        "auth": ("high", "Auth Checklist Incomplete", "Sensitive API routes need authentication and authorization."),
        "cors": ("medium", "CORS Policy Needs Review", "Overly open CORS can expose user sessions or APIs."),
        "webhook_signature": ("high", "Webhook Signature Missing", "Payment/chain webhooks need signature verification."),
        "docs_exposure": ("medium", "API Docs Exposure Needs Review", "Public docs, Swagger, OpenAPI, and GraphQL endpoints should be intentionally scoped."),
        "error_masking": ("medium", "Error Masking Missing", "Stack traces and internal errors should not leak in production."),
        "input_validation": ("medium", "Input Validation Checklist Missing", "Public endpoints need strict request validation."),
        "audit_logs": ("medium", "Audit Logs Missing", "Admin/payment/security actions should be logged."),
        "idor_review": ("high", "BOLA/IDOR Review Missing", "Object-level authorization must be reviewed for user/project resources."),
    },
    "wallet": {
        "domain_verify": ("medium", "Wallet Domain Verification Missing", "Users should see verified, consistent dApp domains."),
        "allowance_warning": ("high", "Unlimited Approval Warning Missing", "Unlimited token approvals can expose user funds."),
        "spender_display": ("medium", "Spender Address Not Clearly Displayed", "Users need clarity on which address gets approval."),
        "permit_warning": ("medium", "Permit Signature Risk Not Explained", "Permit signatures can grant approvals without normal transactions."),
    },
    "admin_opsec": {
        "multisig": ("critical", "Multisig Missing", "Single owner wallets are a major launch risk."),
        "timelock": ("high", "Timelock Missing", "Critical admin changes should have delay where appropriate."),
        "mfa": ("medium", "MFA Checklist Missing", "Admin accounts should use strong MFA."),
        "incident_response": ("medium", "Incident Response Plan Missing", "Teams need a clear emergency process before launch."),
    },
}

MODULE_COPY = {
    "dapp": ("dApp Frontend", "Frontend issues can make users sign the wrong transaction or expose sensitive config."),
    "api": ("API Backend", "API weaknesses can expose project data, rewards, allowlists, or admin routes."),
    "wallet": ("Wallet Flow", "Wallet UX mistakes can create approval, phishing, and blind-signing risk."),
    "admin_opsec": ("Admin OpSec", "Founder/admin key and role mistakes can become catastrophic launch risks."),
}


def scan_checklist(module: str, checklist: list[ChecklistItem], project_name: str | None = None) -> ScanResponse:
    answers = {item.key: item.answer for item in checklist}
    findings: list[Finding] = []
    idx = 1
    for key, (severity, title, desc) in CHECKLIST_RULES[module].items():
        answer = answers.get(key, "unknown")
        if answer in {"no", "unknown"}:
            confidence = "high" if answer == "no" else "low"
            findings.append(Finding(
                id=f"{module}-{idx}",
                module=module,
                severity=severity,
                title=title,
                description=desc,
                confidence=confidence,
                source="Checklist Engine",
                business_impact=MODULE_COPY[module][1],
                developer_explanation=f"Checklist answer for {key}: {answer}. This should be confirmed before launch.",
                recommendation="Document the current setup, fix gaps, and request manual review for high-risk launch flows.",
                paid_review_recommended=severity in {"critical", "high"},
            ))
            idx += 1
    score = score_findings(findings)
    return ScanResponse(
        report_id=f"W3G-{module.upper()}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
        generated_at=datetime.now(timezone.utc),
        project_name=project_name,
        module_score=ModuleScore(module=module, score=score, risk_label=risk_label(score)),
        findings=findings,
    )


def checklist_template(module: str) -> list[dict]:
    labels = {
        "secrets": "No frontend-exposed secrets/API keys",
        "chain_check": "dApp checks chain ID before transaction",
        "tx_preview": "Transaction preview clearly shows token/amount/spender",
        "dangerous_html": "No unsafe HTML rendering in sensitive pages",
        "auto_connect": "Wallet does not auto-connect or auto-trigger transactions on page load",
        "approval_warning": "Unlimited approvals/setApprovalForAll are clearly warned and minimized",
        "verified_contract": "UI shows verified contract address, network, and explorer link",
        "dependency_review": "Frontend dependencies are reviewed before launch",
        "docs_exposure": "Public docs/admin/debug endpoints are intentionally scoped",
        "error_masking": "Errors do not leak stack traces, secrets, or internal IDs",
        "input_validation": "Request validation exists for all public endpoints",
        "audit_logs": "Admin/payment/security actions are audit logged",
        "idor_review": "BOLA/IDOR object-level authorization is reviewed",
        "rate_limit": "API has rate limiting",
        "auth": "Sensitive API routes require auth + authorization",
        "cors": "CORS is restricted to trusted origins",
        "webhook_signature": "Webhooks verify signatures",
        "domain_verify": "WalletConnect/domain verification is planned",
        "allowance_warning": "Unlimited approval warning is shown",
        "spender_display": "Spender address is clearly displayed",
        "permit_warning": "Permit/signature risks are explained",
        "multisig": "Owner/admin wallet uses multisig",
        "timelock": "Critical changes use timelock where needed",
        "mfa": "Admin tools use MFA",
        "incident_response": "Incident response plan exists",
    }
    return [{"key": key, "label": labels.get(key, key), "answer": "unknown"} for key in CHECKLIST_RULES[module]]
