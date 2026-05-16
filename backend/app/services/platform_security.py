from __future__ import annotations

from pathlib import Path
from typing import Any

from app.core.config import settings
from app.services.local_qa import ESSENTIAL_BACKEND_ENDPOINTS, ESSENTIAL_FRONTEND_ROUTES, validate_environment
from app.services.mega_phase_e_store import read_jsonl, storage_path

PRODUCTION_BLOCKER_LEVELS = {"critical", "high"}


def _configured(value: Any) -> bool:
    return bool(value and str(value).strip() and str(value).strip().lower() not in {"none", "change-this-admin-token", "yourupi@bank", "raadhanex@upi"})


def security_hardening_status() -> dict[str, Any]:
    checks = [
        {
            "key": "security_headers",
            "status": "pass" if settings.security_headers_enabled else "warning",
            "title": "Security headers middleware",
            "detail": "API responses include nosniff, frame deny, referrer policy, permissions policy, CSP, request ID, and pre-audit disclaimer header." if settings.security_headers_enabled else "Enable SECURITY_HEADERS_ENABLED before public launch.",
        },
        {
            "key": "admin_token",
            "status": "pass" if _configured(settings.admin_token) else "critical",
            "title": "Admin token changed",
            "detail": "ADMIN_TOKEN must be unique and private before public deployment.",
        },
        {
            "key": "cors_origin",
            "status": "pass" if settings.frontend_origin.startswith("https://") or settings.app_env == "development" else "high",
            "title": "CORS origin configured",
            "detail": f"FRONTEND_ORIGIN={settings.frontend_origin}. Production should use exact https domain, not wildcard.",
        },
        {
            "key": "body_limit",
            "status": "pass" if settings.max_request_body_bytes <= 5_000_000 else "warning",
            "title": "Request body limit",
            "detail": f"MAX_REQUEST_BODY_BYTES={settings.max_request_body_bytes}. Large code/repo scans should use worker/upload flow later.",
        },
        {
            "key": "ssrf_controls",
            "status": "pass",
            "title": "SSRF/private network blocking",
            "detail": "URL validators block localhost/private/link-local/reserved IPs and only allow http/https.",
        },
        {
            "key": "rate_limit_mode",
            "status": "warning" if settings.rate_limit_backend == "memory" else "pass",
            "title": "Rate limit backend",
            "detail": "In-memory limiter is okay for local/MVP. Production multi-instance deployment should use Redis/Upstash.",
        },
        {
            "key": "secrets_frontend",
            "status": "pass",
            "title": "Secrets backend-only policy",
            "detail": "AI, Razorpay secret, Etherscan, GitHub token, SMTP/Telegram/Discord/WhatsApp credentials must remain backend-only.",
        },
        {
            "key": "data_retention",
            "status": "warning" if settings.storage_mode == "local" else "pass",
            "title": "Data retention and deletion",
            "detail": "Local JSONL mode is for MVP/dev. Production should use Supabase with retention/deletion policies and backups.",
        },
        {
            "key": "audit_tools_sandbox",
            "status": "warning" if settings.static_analysis_enabled or settings.deep_analysis_enabled else "pass",
            "title": "Audit tool sandboxing",
            "detail": "Static/deep tools should run inside isolated worker containers before public untrusted scans. Current tool runners are optional and disabled by default.",
        },
        {
            "key": "payment_verification",
            "status": "pass" if (settings.razorpay_enabled and settings.razorpay_webhook_secret) or settings.payment_mode == "upi_manual" else "warning",
            "title": "Payment verification honesty",
            "detail": "Manual UPI must remain manual verification. Razorpay success requires signature/webhook verification.",
        },
    ]
    blockers = [c for c in checks if c["status"] in PRODUCTION_BLOCKER_LEVELS]
    warnings = [c for c in checks if c["status"] == "warning"]
    return {
        "ok": len(blockers) == 0,
        "version": "1.0",
        "production_ready": len(blockers) == 0 and len(warnings) == 0,
        "blocker_count": len(blockers),
        "warning_count": len(warnings),
        "checks": checks,
        "real_only_note": "This is a hardening checklist/status, not a penetration test or compliance certification.",
    }


def security_headers_preview() -> dict[str, Any]:
    return {
        "enabled": settings.security_headers_enabled,
        "headers": {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "camera=(), microphone=(), geolocation=(), payment=(), usb=()",
            "Content-Security-Policy": settings.security_csp,
            "Strict-Transport-Security": f"max-age={settings.hsts_max_age}; includeSubDomains" if settings.hsts_enabled else "disabled until enabled/staging/production",
            "X-Web3Guard-Disclaimer": "pre-audit-readiness-not-certified-audit",
        },
        "frontend_note": "Next/Vercel also has security headers in frontend/vercel.json for browser pages.",
    }


def data_retention_plan() -> dict[str, Any]:
    return {
        "default_mode": settings.storage_mode,
        "retention_days": settings.default_data_retention_days,
        "code_storage_policy": "Do not store private keys/seed phrases. Code/source scan payloads should be minimized and deleted on user request.",
        "delete_request_flow": [
            "User submits deletion request from Privacy/Data page or support email.",
            "Admin verifies requester identity/account/project ownership.",
            "Delete local/Supabase project, scan, report, lead, payment metadata as allowed by law/accounting requirements.",
            "Keep minimal legal invoice/payment records where required.",
            "Record deletion audit event without storing sensitive content.",
        ],
        "production_required": ["Supabase row-level deletion policies", "backup retention policy", "admin audit log", "privacy contact email", "CA/lawyer review"],
    }


def final_qa_status() -> dict[str, Any]:
    env = validate_environment()
    security = security_hardening_status()
    required_accounts = account_setup_matrix()
    account_blockers = [a for a in required_accounts if a["required_for_public_launch"] and not a["configured"]]
    return {
        "ok": env.get("ok") and security.get("ok"),
        "version": "1.0",
        "frontend_route_count": len(ESSENTIAL_FRONTEND_ROUTES),
        "backend_endpoint_count": len(ESSENTIAL_BACKEND_ENDPOINTS) + 12,
        "environment_ok": env.get("ok"),
        "security_ok": security.get("ok"),
        "production_ready": env.get("ok") and security.get("production_ready") and not account_blockers,
        "account_blockers": account_blockers,
        "honest_launch_label": "MVP beta-ready after local QA + provider setup; not certified audit platform.",
    }


def final_launch_checklist() -> list[dict[str, Any]]:
    return [
        {"area": "Local QA", "items": ["Backend /health passes", "Frontend npm run build passes locally", "All scanner pages open", "No horizontal mobile overflow", "Admin token works"]},
        {"area": "Security", "items": ["ADMIN_TOKEN changed", "CORS exact production domain", "Security headers enabled", "No secrets in frontend env", "SSRF tests pass", "Rate limit production backend selected"]},
        {"area": "Payments", "items": ["UPI ID verified", "Razorpay test order verified", "Webhook signature verified", "Manual UPI status does not auto-activate plan"]},
        {"area": "Database", "items": ["Supabase migrations applied", "RLS policies reviewed", "Backups configured", "Deletion/export policy documented"]},
        {"area": "Legal/trust", "items": ["Terms/privacy/refund/responsible-use reviewed", "No certified-audit wording", "No 100% secure claims", "Pre-audit disclaimer visible"]},
        {"area": "Security tools", "items": ["Slither/Aderyn/Semgrep installed only in worker", "Deep tools disabled unless worker/sandbox ready", "No private key collection"]},
        {"area": "Launch", "items": ["Vercel env set", "Render env set", "Domain/HTTPS ready", "Support/contact email ready", "First sample report published"]},
    ]


def account_setup_matrix() -> list[dict[str, Any]]:
    return [
        {"service": "Supabase", "purpose": "Auth, database, RLS, scan/report persistence", "required_for_public_launch": True, "configured": bool(settings.supabase_url and settings.supabase_anon_key and settings.supabase_service_role_key), "env": ["SUPABASE_URL", "SUPABASE_ANON_KEY", "SUPABASE_SERVICE_ROLE_KEY"]},
        {"service": "Razorpay", "purpose": "Real checkout, UPI/cards, payment verification, subscriptions", "required_for_public_launch": True, "configured": bool(settings.razorpay_key_id and settings.razorpay_key_secret and settings.razorpay_webhook_secret), "env": ["RAZORPAY_KEY_ID", "RAZORPAY_KEY_SECRET", "RAZORPAY_WEBHOOK_SECRET"]},
        {"service": "UPI", "purpose": "Manual payment fallback", "required_for_public_launch": True, "configured": _configured(settings.raadhanex_upi_id), "env": ["RAADHANEX_UPI_ID", "RAADHANEX_UPI_NAME", "NEXT_PUBLIC_UPI_ID"]},
        {"service": "Etherscan", "purpose": "Verified contract source/ABI scan", "required_for_public_launch": False, "configured": _configured(settings.etherscan_api_key), "env": ["ETHERSCAN_API_KEY"]},
        {"service": "GitHub", "purpose": "Higher public repo API rate limits", "required_for_public_launch": False, "configured": _configured(settings.github_api_token), "env": ["GITHUB_API_TOKEN"]},
        {"service": "OpenAI/Anthropic", "purpose": "Real AI fix assistant", "required_for_public_launch": False, "configured": bool(settings.ai_enabled and (settings.openai_api_key or settings.anthropic_api_key or settings.ai_api_key)), "env": ["AI_ENABLED", "OPENAI_API_KEY", "ANTHROPIC_API_KEY"]},
        {"service": "RPC provider", "purpose": "Monitoring Lite read-only logs", "required_for_public_launch": False, "configured": any([settings.ethereum_rpc_url, settings.polygon_rpc_url, settings.bsc_rpc_url]), "env": ["ETHEREUM_RPC_URL", "POLYGON_RPC_URL", "BSC_RPC_URL"]},
        {"service": "Email/Telegram/Discord", "purpose": "Real notifications", "required_for_public_launch": False, "configured": bool((settings.smtp_enabled and settings.smtp_host) or (settings.telegram_enabled and settings.telegram_bot_token) or (settings.discord_enabled and settings.discord_webhook_url)), "env": ["SMTP_*", "TELEGRAM_*", "DISCORD_WEBHOOK_URL"]},
        {"service": "Legal/CA review", "purpose": "Terms, privacy, refund, GST/compliance review", "required_for_public_launch": True, "configured": False, "env": ["manual_account_or_professional_review_required"]},
    ]
