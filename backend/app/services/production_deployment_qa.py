from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse

from app.core.config import settings
from app.services.database_store import active_storage_mode, supabase_configured


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _is_https_url(value: str | None) -> bool:
    if not value:
        return False
    try:
        parsed = urlparse(value)
        return parsed.scheme == "https" and bool(parsed.netloc)
    except Exception:
        return False


def _is_local(value: str | None) -> bool:
    clean = (value or "").lower()
    return "localhost" in clean or "127.0.0.1" in clean or clean.startswith("http://")


def _check(
    key: str,
    label: str,
    passed: bool,
    severity: str,
    evidence: str,
    action: str,
    area: str,
) -> dict[str, Any]:
    return {
        "key": key,
        "area": area,
        "label": label,
        "passed": bool(passed),
        "severity": severity,
        "status": "pass" if passed else "action_required",
        "evidence": evidence,
        "action": action,
    }


def deployment_checks() -> list[dict[str, Any]]:
    storage_mode = active_storage_mode()
    supabase_ready = supabase_configured(require_service_role=True)
    frontend_origin = settings.frontend_origin
    backend_url = settings.backend_url
    admin_token = (settings.admin_token or "").strip()
    weak_admin_tokens = {"change-this-admin-token", "admin", "password", "test", "raadweb3_admin_1486_change_this"}

    return [
        _check(
            "frontend_origin_https",
            "Frontend origin uses HTTPS production domain",
            _is_https_url(frontend_origin) and not _is_local(frontend_origin),
            "high",
            f"FRONTEND_ORIGIN={frontend_origin}",
            "Set FRONTEND_ORIGIN to the live Vercel/custom domain. Keep localhost only for local development.",
            "Environment",
        ),
        _check(
            "backend_url_https",
            "Backend URL uses HTTPS production domain",
            _is_https_url(backend_url) and not _is_local(backend_url),
            "high",
            f"BACKEND_URL={backend_url}",
            "Set BACKEND_URL to the live Render/custom backend URL.",
            "Environment",
        ),
        _check(
            "app_env_production",
            "Backend APP_ENV is production or staging for public traffic",
            settings.app_env.lower() in {"production", "staging"},
            "medium",
            f"APP_ENV={settings.app_env}",
            "Use APP_ENV=production for public launch. Docs/OpenAPI are disabled in production/staging by main.py.",
            "Environment",
        ),
        _check(
            "admin_token_rotated",
            "Admin token is rotated from defaults",
            len(admin_token) >= 24 and admin_token not in weak_admin_tokens,
            "critical",
            "ADMIN_TOKEN length/default check only; value is never returned.",
            "Set a long random ADMIN_TOKEN in Render secret env. Do not commit it.",
            "Security",
        ),
        _check(
            "supabase_service_role_ready",
            "Supabase service-role storage is configured",
            storage_mode == "supabase" and supabase_ready,
            "high",
            f"active_storage_mode={storage_mode}; supabase_service_role_configured={supabase_ready}",
            "Use STORAGE_MODE=supabase and set SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_ROLE_KEY on backend only.",
            "Supabase",
        ),
        _check(
            "supabase_jwt_verify_enabled",
            "Supabase JWT verification is enabled",
            bool(settings.supabase_jwt_verify_enabled),
            "high",
            f"SUPABASE_JWT_VERIFY_ENABLED={settings.supabase_jwt_verify_enabled}",
            "Enable JWT verification before exposing user-specific APIs to public traffic.",
            "Supabase",
        ),
        _check(
            "security_headers_enabled",
            "Backend security headers middleware is enabled",
            bool(settings.security_headers_enabled),
            "medium",
            f"SECURITY_HEADERS_ENABLED={settings.security_headers_enabled}; CSP configured={bool(settings.security_csp)}",
            "Keep security headers enabled and verify response headers from the live Render URL.",
            "Security",
        ),
        _check(
            "hsts_enabled_when_custom_domain_ready",
            "HSTS is enabled when production HTTPS/custom domain is ready",
            bool(settings.hsts_enabled or settings.app_env.lower() != "production"),
            "medium",
            f"HSTS_ENABLED={settings.hsts_enabled}; APP_ENV={settings.app_env}",
            "Enable HSTS only after confirming HTTPS works on the final production domain.",
            "Security",
        ),
        _check(
            "payment_deferred",
            "Payment remains deferred until real webhook verification",
            not settings.razorpay_enabled or bool(settings.razorpay_webhook_secret),
            "critical",
            f"RAZORPAY_ENABLED={settings.razorpay_enabled}; webhook_secret_configured={bool(settings.razorpay_webhook_secret)}",
            "Do not show paid/subscription success until Razorpay order, checkout, signature, webhook, and audit logs are verified.",
            "Payments",
        ),
        _check(
            "ai_privacy_safe",
            "AI provider does not receive code by default",
            not settings.ai_send_code and not settings.ai_fix_send_code,
            "high",
            f"AI_SEND_CODE={settings.ai_send_code}; AI_FIX_SEND_CODE={settings.ai_fix_send_code}",
            "Keep AI code sharing opt-in only and update privacy wording before enabling provider-based code analysis.",
            "AI / Providers",
        ),
        _check(
            "deep_tools_safe_defaults",
            "Deep tools keep network/dependency install disabled",
            not settings.deep_analysis_network_enabled and not settings.deep_analysis_allow_dependency_install,
            "critical",
            f"deep_network={settings.deep_analysis_network_enabled}; dependency_install={settings.deep_analysis_allow_dependency_install}",
            "Run Mythril/Manticore/Echidna only in isolated workers; never install dependencies from user input inside the main backend.",
            "Tooling",
        ),
        _check(
            "data_retention_ready",
            "Data retention limits are configured",
            settings.data_retention_enabled and settings.code_upload_retention_days <= 30 and settings.user_data_delete_request_sla_days <= 30,
            "medium",
            f"code_upload_retention_days={settings.code_upload_retention_days}; delete_request_sla_days={settings.user_data_delete_request_sla_days}",
            "Keep short code retention and publish deletion/export request workflow.",
            "Privacy",
        ),
        _check(
            "backup_policy_ready",
            "Backup policy is configured before paid launch",
            bool(settings.backup_policy_enabled) or not settings.razorpay_enabled,
            "medium",
            f"BACKUP_POLICY_ENABLED={settings.backup_policy_enabled}; RAZORPAY_ENABLED={settings.razorpay_enabled}",
            "Before paid launch, configure Supabase backup policy and document restore owner/frequency.",
            "Operations",
        ),
        _check(
            "error_monitoring_ready",
            "Error monitoring is configured before scaled traffic",
            bool(settings.sentry_enabled and settings.sentry_dsn) or settings.app_env.lower() != "production",
            "low",
            f"SENTRY_ENABLED={settings.sentry_enabled}; dsn_configured={bool(settings.sentry_dsn)}",
            "Configure Sentry or equivalent before marketing push.",
            "Operations",
        ),
        _check(
            "uptime_monitoring_ready",
            "Uptime monitoring is configured before public launch",
            bool(settings.uptime_monitoring_enabled) or settings.app_env.lower() != "production",
            "low",
            f"UPTIME_MONITORING_ENABLED={settings.uptime_monitoring_enabled}",
            "Add BetterStack/UptimeRobot/StatusCake checks for frontend, backend /health, and Supabase heartbeat.",
            "Operations",
        ),
        _check(
            "manual_launch_approval",
            "Manual production launch approval is acknowledged",
            bool(settings.production_launch_approved),
            "medium",
            f"PRODUCTION_LAUNCH_APPROVED={settings.production_launch_approved}",
            "Set this only after live Vercel, Render, Supabase, legal copy, and support paths are reviewed.",
            "Launch Approval",
        ),
    ]


def _score_from_checks(checks: list[dict[str, Any]]) -> int:
    deductions = {"critical": 24, "high": 14, "medium": 7, "low": 3}
    score = 100
    for item in checks:
        if not item["passed"]:
            score -= deductions.get(item["severity"], 5)
    return max(0, score)


def _readiness_label(checks: list[dict[str, Any]]) -> str:
    failed = [item for item in checks if not item["passed"]]
    if any(item["severity"] == "critical" for item in failed):
        return "Blocked for public launch"
    if any(item["severity"] == "high" for item in failed):
        return "Private beta only"
    if any(item["severity"] == "medium" for item in failed):
        return "Controlled public beta"
    if failed:
        return "Ready with monitoring review"
    return "Ready for public beta"


def manual_live_qa_routes() -> list[dict[str, str]]:
    return [
        {"path": "/", "purpose": "landing, hero, header, footer, disclaimers"},
        {"path": "/scanner/unified-url", "purpose": "primary scan flow, validation, Not Assessed wording"},
        {"path": "/scanner", "purpose": "module navigation and mobile layout"},
        {"path": "/report/professional", "purpose": "export UI and report traceability"},
        {"path": "/report/verify", "purpose": "hash verification and evidence summary"},
        {"path": "/dashboard", "purpose": "Supabase session and real stored records only"},
        {"path": "/dashboard/workflow", "purpose": "timeline, trend, finding workflow empty/real states"},
        {"path": "/feature-status", "purpose": "provider/tool honesty"},
        {"path": "/engine-depth", "purpose": "real tool readiness matrix"},
        {"path": "/provider-readiness", "purpose": "Etherscan/GoPlus/GitHub readiness"},
        {"path": "/free-tools", "purpose": "free founder tools"},
        {"path": "/methodology", "purpose": "score explanation and Not Assessed policy"},
        {"path": "/limitations", "purpose": "pre-audit boundaries"},
        {"path": "/privacy", "purpose": "data handling and no secret submission"},
        {"path": "/terms", "purpose": "public beta use rules"},
        {"path": "/security", "purpose": "security contact and posture"},
        {"path": "/pricing", "purpose": "free beta / payments deferred copy"},
        {"path": "/launch-qa", "purpose": "manual deployment QA board"},
    ]


def deployment_command_checklist() -> dict[str, list[str]]:
    return {
        "backend": ["cd backend", "python -m pytest -q"],
        "frontend": ["cd frontend", "npm run typecheck", "npm run build"],
        "git": [
            "cd C:\\web\\web3guard",
            "git status",
            "git add .",
            'git commit -m "Run production deployment QA pass"',
            "git push origin main",
        ],
        "live_manual": [
            "Open Vercel deployment URL and test the route list.",
            "Open Render backend /health and /production-deployment-qa/status.",
            "Confirm GitHub Actions Supabase heartbeat result.",
            "Check browser console for hydration/runtime errors on mobile width.",
        ],
    }


def production_deployment_qa_status() -> dict[str, Any]:
    checks = deployment_checks()
    failed = [item for item in checks if not item["passed"]]
    score = _score_from_checks(checks)
    return {
        "ok": True,
        "generated_at": _now(),
        "readiness_label": _readiness_label(checks),
        "score": score,
        "passed": len(checks) - len(failed),
        "total": len(checks),
        "production_ready": score >= 85 and not any(item["severity"] in {"critical", "high"} for item in failed),
        "checks": checks,
        "manual_live_qa_routes": manual_live_qa_routes(),
        "commands": deployment_command_checklist(),
        "real_only_note": "This endpoint does not certify security or approve launch automatically. It checks configuration posture and tells the team what must be manually verified before public beta traffic.",
    }
