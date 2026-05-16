from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.core.config import settings
from app.services.database_store import active_storage_mode, supabase_configured

PHASE_G_NOTE = (
    " is a production hardening and launch QA layer. It does not make external services real by itself; "
    "it verifies which integrations are configured and clearly marks missing items as manual or not configured."
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _path(raw: str) -> Path:
    path = Path(raw)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text("", encoding="utf-8")
    return path


def _read_jsonl(raw: str) -> list[dict[str, Any]]:
    path = _path(raw)
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows


def _append_jsonl(raw: str, row: dict[str, Any]) -> None:
    path = _path(raw)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")


def _check_item(key: str, label: str, passed: bool, severity: str, evidence: str, fix: str) -> dict[str, Any]:
    return {
        "key": key,
        "label": label,
        "passed": bool(passed),
        "severity": severity,
        "status": "pass" if passed else "action_required",
        "evidence": evidence,
        "fix": fix,
    }


def admin_token_is_safe() -> bool:
    weak = {"change-this-admin-token", "raadweb3_admin_1486_change_this", "admin", "password", "test"}
    token = (settings.admin_token or "").strip()
    return len(token) >= 24 and token not in weak


def production_security_checks() -> list[dict[str, Any]]:
    frontend_origin = settings.frontend_origin or ""
    storage = active_storage_mode()
    return [
        _check_item(
            "admin_token_changed",
            "Admin token is changed from defaults",
            admin_token_is_safe(),
            "critical",
            "ADMIN_TOKEN length/default check only; token value is never returned.",
            "Set a long random ADMIN_TOKEN in backend .env and never commit it.",
        ),
        _check_item(
            "app_env_production",
            "APP_ENV is set to production for public launch",
            settings.app_env.lower() == "production",
            "medium",
            f"APP_ENV={settings.app_env}",
            "Set APP_ENV=production only when deploying the public production backend.",
        ),
        _check_item(
            "cors_locked",
            "CORS origin is locked to a real frontend domain",
            frontend_origin.startswith("https://") and "localhost" not in frontend_origin and "*" not in frontend_origin,
            "high",
            f"FRONTEND_ORIGIN={frontend_origin}",
            "Set FRONTEND_ORIGIN=https://your-real-domain and remove localhost from production deployment config.",
        ),
        _check_item(
            "supabase_production_storage",
            "Supabase service-role storage is configured for production records",
            storage == "supabase" and supabase_configured(require_service_role=True),
            "high",
            f"active_storage_mode={storage}; supabase_configured={supabase_configured(require_service_role=True)}",
            "Run Supabase migrations and set STORAGE_MODE=supabase, SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_ROLE_KEY.",
        ),
        _check_item(
            "supabase_jwt_verification",
            "Supabase JWT verification is enabled for protected production APIs",
            bool(settings.supabase_jwt_verify_enabled),
            "high",
            f"SUPABASE_JWT_VERIFY_ENABLED={settings.supabase_jwt_verify_enabled}",
            "Enable JWT verification before exposing user-specific APIs publicly.",
        ),
        _check_item(
            "razorpay_webhook",
            "Razorpay webhook secret is configured for verified paid state",
            bool(settings.razorpay_enabled and settings.razorpay_key_id and settings.razorpay_key_secret and settings.razorpay_webhook_secret),
            "high",
            f"razorpay_enabled={settings.razorpay_enabled}; webhook_secret_configured={bool(settings.razorpay_webhook_secret)}",
            "Configure Razorpay keys + webhook secret. Without webhook/signature verification, keep payments manual/pending.",
        ),
        _check_item(
            "ai_privacy_default",
            "AI code sharing is disabled by default",
            not settings.ai_send_code and not settings.ai_fix_send_code,
            "medium",
            f"AI_SEND_CODE={settings.ai_send_code}; AI_FIX_SEND_CODE={settings.ai_fix_send_code}",
            "Keep AI_SEND_CODE=false unless user explicitly opts in and privacy terms are updated.",
        ),
        _check_item(
            "deep_tools_sandboxed",
            "Deep analysis does not allow dependency install/network by default",
            not settings.deep_analysis_network_enabled and not settings.deep_analysis_allow_dependency_install,
            "critical",
            f"network={settings.deep_analysis_network_enabled}; dependency_install={settings.deep_analysis_allow_dependency_install}",
            "Run deep tools only in isolated workers. Keep network/dependency install disabled by default.",
        ),
        _check_item(
            "data_retention_policy",
            "Data-retention controls are documented/configured",
            settings.data_retention_enabled and settings.code_upload_retention_days <= 30 and settings.user_data_delete_request_sla_days <= 30,
            "medium",
            f"code_upload_retention_days={settings.code_upload_retention_days}; delete_sla_days={settings.user_data_delete_request_sla_days}",
            "Keep short code retention and publish data deletion/export process before launch.",
        ),
        _check_item(
            "backup_policy",
            "Backup policy is configured",
            bool(settings.backup_policy_enabled),
            "medium",
            f"backup_policy_enabled={settings.backup_policy_enabled}; provider={settings.backup_provider}",
            "Configure database backups before paid/public production launch.",
        ),
        _check_item(
            "error_monitoring",
            "Error monitoring is configured",
            bool(settings.sentry_enabled and settings.sentry_dsn),
            "low",
            f"sentry_enabled={settings.sentry_enabled}; dsn_configured={bool(settings.sentry_dsn)}",
            "Configure Sentry or equivalent error monitoring.",
        ),
        _check_item(
            "uptime_monitoring",
            "Uptime monitoring is configured",
            bool(settings.uptime_monitoring_enabled),
            "low",
            f"uptime_monitoring_enabled={settings.uptime_monitoring_enabled}",
            "Configure UptimeRobot/BetterStack/StatusCake or similar.",
        ),
    ]


def security_status() -> dict[str, Any]:
    checks = production_security_checks()
    failed = [c for c in checks if not c["passed"]]
    critical_failed = [c for c in failed if c["severity"] == "critical"]
    high_failed = [c for c in failed if c["severity"] == "high"]
    if critical_failed:
        readiness = "blocked"
    elif high_failed:
        readiness = "not_ready"
    elif failed:
        readiness = "needs_review"
    else:
        readiness = "ready_for_controlled_launch"
    return {
        "ok": True,
        "phase": "Mega Phase G - Platform Security Hardening + Final Production QA",
        "version": "1.0",
        "readiness": readiness,
        "score": max(0, round(100 - len(critical_failed) * 25 - len(high_failed) * 15 - (len(failed) - len(critical_failed) - len(high_failed)) * 5)),
        "passed": len(checks) - len(failed),
        "total": len(checks),
        "checks": checks,
        "real_only_note": PHASE_G_NOTE,
    }


def security_headers_policy() -> dict[str, Any]:
    headers = {
        "Strict-Transport-Security": f"max-age={settings.strict_transport_security_max_age}; includeSubDomains; preload",
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Permissions-Policy": "camera=(), microphone=(), geolocation=(), payment=(self)",
        "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline' https://checkout.razorpay.com; connect-src 'self' https://api.razorpay.com https://*.supabase.co; img-src 'self' data: https:; style-src 'self' 'unsafe-inline'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'",
    }
    return {
        "ok": True,
        "enabled": settings.security_headers_enabled,
        "report_only": settings.content_security_policy_report_only,
        "recommended_headers": headers,
        "deployment_note": "Apply these at Vercel/Render/Cloudflare/Nginx layer. Keep CSP report-only first, then enforce after testing.",
    }


def data_retention_policy() -> dict[str, Any]:
    return {
        "ok": True,
        "enabled": settings.data_retention_enabled,
        "retention_days": {
            "code_uploads_and_temp_workspaces": settings.code_upload_retention_days,
            "scan_history": settings.scan_history_retention_days,
            "leads": settings.lead_retention_days,
            "payment_records": settings.payment_record_retention_days,
            "admin_audit_logs": settings.audit_log_retention_days,
        },
        "delete_request_sla_days": settings.user_data_delete_request_sla_days,
        "manual_actions_required": [
            "Create a public data deletion request email/process.",
            "Enable Supabase row-level security before production.",
            "Configure backups and retention in Supabase/host provider.",
            "Do not store seed phrases/private keys; reject them in forms and docs.",
        ],
    }


def platform_boundary_matrix() -> dict[str, Any]:
    return {
        "ok": True,
        "boundaries": [
            {"module": "Website scanners", "allowed": "Passive public HTTP/HTML/header checks", "blocked": "Exploit payloads, login bypass, brute force, destructive tests"},
            {"module": "GitHub scanner", "allowed": "Read-only public repo static analysis", "blocked": "Clone/execute/dependency install on main backend"},
            {"module": "Contract address scanner", "allowed": "Explorer verified source/ABI read", "blocked": "Wallet connection, signing, private key use"},
            {"module": "Static/deep tools", "allowed": "Optional installed tools in controlled temp workspace", "blocked": "Fake tool output, networked arbitrary execution, secret access"},
            {"module": "AI Fix Assistant", "allowed": "Opt-in AI suggestions/fallback guidance", "blocked": "Guaranteed fixes, exploit generation, auto-apply without user approval"},
            {"module": "Payments", "allowed": "Razorpay verified or manual UPI pending/verified by admin", "blocked": "Fake payment success"},
        ],
    }


def log_security_event(event_type: str, actor: str, note: str) -> dict[str, Any]:
    row = {"id": f"sec_{int(datetime.now(timezone.utc).timestamp())}", "created_at": _now(), "event_type": event_type, "actor": actor, "note": note}
    _append_jsonl(settings.security_audit_log_file, row)
    return row


def recent_security_events(limit: int = 100) -> list[dict[str, Any]]:
    rows = _read_jsonl(settings.security_audit_log_file)
    return list(reversed(rows[-limit:]))
