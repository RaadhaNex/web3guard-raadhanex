from __future__ import annotations

from pathlib import Path
from typing import Any

from app.core.config import settings

ESSENTIAL_FRONTEND_ROUTES = [
    "/",
    "/scanner",
    "/scanner/unified-url",
    "/scanner/github",
    "/scanner/address",
    "/scanner/permission-map",
    "/scanner/static-analysis",
    "/scanner/contract",
    "/scanner/website",
    "/scanner/dapp",
    "/scanner/api",
    "/scanner/wallet",
    "/scanner/admin-opsec",
    "/report",
    "/report/professional",
    "/report/public",
    "/pricing",
    "/methodology",
    "/sample-reports",
    "/trust",
    "/ownership-verification",
    "/feature-status",
    "/scope-refund",
    "/responsible-use",
    "/privacy",
    "/terms",
    "/contact",
    "/admin/leads",
    "/admin/payments",
    "/billing",
    "/local-qa",
    "/launch-pack",
    "/auth/login",
    "/auth/signup",
    "/dashboard",
    "/dashboard/projects",
    "/dashboard/projects/[id]",
    "/dashboard/scans",
    "/dashboard/workspace",
    "/dashboard/workspace/[id]",
    "/dashboard/scans/[id]",
    "/dashboard/reports/[id]",
    "/dashboard/securescore",
    "/dashboard/findings",
    "/cicd",
    "/learning",
    "/admin/super",
]

ESSENTIAL_BACKEND_ENDPOINTS = [
    {"method": "GET", "path": "/", "purpose": "Root service status"},
    {"method": "GET", "path": "/health", "purpose": "Basic backend health"},
    {"method": "GET", "path": "/health/readiness", "purpose": "Environment and storage readiness"},
    {"method": "GET", "path": "/qa/status", "purpose": "Web3Guard local QA status"},
    {"method": "GET", "path": "/launch/pack", "purpose": "Web3Guard deploy and launch pack"},
    {"method": "GET", "path": "/db/status", "purpose": "Web3Guard database/Supabase readiness status"},
    {"method": "GET", "path": "/dashboard/overview", "purpose": "Web3Guard user dashboard overview"},
    {"method": "GET", "path": "/workspace/status", "purpose": "Web3Guard organization/team workspace status"},
    {"method": "GET", "path": "/securescore/status", "purpose": "Web3Guard SecureScore Pro readiness status"},
    {"method": "GET", "path": "/securescore/overview", "purpose": "Web3Guard SecureScore dashboard overview from saved scans"},
    {"method": "GET", "path": "/findings", "purpose": "Web3Guard saved finding list with workflow statuses"},
    {"method": "POST", "path": "/organizations", "purpose": "Web3Guard create organization workspace"},
    {"method": "GET", "path": "/organizations", "purpose": "Web3Guard list user organizations"},
    {"method": "GET", "path": "/organizations/{organization_id}", "purpose": "Web3Guard workspace overview"},
    {"method": "POST", "path": "/organizations/{organization_id}/members", "purpose": "Web3Guard save manual member invite record"},
    {"method": "POST", "path": "/workspace/finding-tasks", "purpose": "Web3Guard create finding remediation task"},
    {"method": "POST", "path": "/workspace/comments", "purpose": "Web3Guard add workspace comment"},
    {"method": "POST", "path": "/profile", "purpose": "Web3Guard profile upsert"},
    {"method": "POST", "path": "/projects", "purpose": "Web3Guard project persistence"},
    {"method": "GET", "path": "/projects/{project_id}", "purpose": "Web3Guard project detail with scans/reports/activity"},
    {"method": "PATCH", "path": "/projects/{project_id}", "purpose": "Web3Guard project notes/status update"},
    {"method": "POST", "path": "/scan-history", "purpose": "Web3Guard scan history persistence"},
    {"method": "GET", "path": "/scan-history/{scan_id}", "purpose": "Web3Guard scan detail payload view"},
    {"method": "PATCH", "path": "/scan-history/{scan_id}", "purpose": "Web3Guard scan workflow status update"},
    {"method": "POST", "path": "/saved-reports", "purpose": "Web3Guard saved report persistence"},
    {"method": "GET", "path": "/saved-reports/{saved_report_id}", "purpose": "Web3Guard saved report detail"},
    {"method": "PATCH", "path": "/saved-reports/{saved_report_id}", "purpose": "Web3Guard report visibility/status update"},
    {"method": "GET", "path": "/packages", "purpose": "Pricing/package list"},
    {"method": "POST", "path": "/payment-intent", "purpose": "Web3Guard Razorpay/UPI payment intent"},
    {"method": "GET", "path": "/payments/status", "purpose": "Web3Guard payment gateway readiness status"},
    {"method": "POST", "path": "/payments/razorpay/verify", "purpose": "Verify Razorpay Checkout signature"},
    {"method": "POST", "path": "/payments/webhook/razorpay", "purpose": "Verify Razorpay webhook signature"},
    {"method": "GET", "path": "/subscriptions", "purpose": "List current subscription records"},
    {"method": "GET", "path": "/scan/github/status", "purpose": "Web3Guard GitHub repo scanner status"},
    {"method": "GET", "path": "/scan/contract-address/status", "purpose": "Web3Guard verified contract address scanner status"},
    {"method": "GET", "path": "/scan/permission-map/status", "purpose": "Web3Guard permission map and centralization scanner status"},
    {"method": "GET", "path": "/scan/static-analysis/status", "purpose": "Web3Guard Slither/Aderyn/Semgrep real tool status"},
    {"method": "POST", "path": "/scan/github-repo", "purpose": "Web3Guard public GitHub repository scanner"},
    {"method": "POST", "path": "/scan/contract", "purpose": "Solidity rule-engine scan"},
    {"method": "POST", "path": "/scan/static-analysis", "purpose": "Web3Guard real static-analysis tool runner"},
    {"method": "POST", "path": "/scan/permission-map", "purpose": "Web3Guard permission map and founder transparency report"},
    {"method": "POST", "path": "/scan/website", "purpose": "Passive website surface scan"},
    {"method": "POST", "path": "/scan/unified-url", "purpose": "Real-only unified URL launch scanner"},
    {"method": "POST", "path": "/scan/dapp-checklist", "purpose": "dApp checklist/code-hint scan"},
    {"method": "POST", "path": "/scan/api-checklist", "purpose": "API checklist/code-hint scan"},
    {"method": "POST", "path": "/scan/wallet-checklist", "purpose": "Wallet flow checklist scan"},
    {"method": "POST", "path": "/scan/admin-opsec", "purpose": "Founder/admin OpSec checklist scan"},
    {"method": "POST", "path": "/report/combined", "purpose": "Combined readiness report builder"},
    {"method": "POST", "path": "/report/professional", "purpose": "Web3Guard combined report plus delivery artifacts"},
    {"method": "POST", "path": "/report/export/pdf", "purpose": "Web3Guard server-side PDF report export"},
    {"method": "POST", "path": "/report/publication", "purpose": "Web3Guard public/private report record"},
    {"method": "GET", "path": "/report/delivery-policy", "purpose": "Web3Guard report delivery policy"},
    {"method": "POST", "path": "/lead", "purpose": "Manual review lead capture"},
    {"method": "GET", "path": "/admin/leads", "purpose": "Admin leads CRM; requires ADMIN_TOKEN"},
    {"method": "GET", "path": "/admin/leads.csv", "purpose": "CSV export; requires ADMIN_TOKEN"},
    {"method": "GET", "path": "/cicd/status", "purpose": "Web3Guard CI/CD template status"},
    {"method": "POST", "path": "/cicd/template", "purpose": "Web3Guard generate GitHub Action/Web3Guard CI templates"},
    {"method": "POST", "path": "/cicd/validate", "purpose": "Web3Guard validate CI config text without executing workflow"},
    {"method": "GET", "path": "/learning/status", "purpose": "Web3Guard Learning Center status"},
    {"method": "GET", "path": "/learning/lessons", "purpose": "Web3Guard list Hinglish/English security lessons"},
    {"method": "POST", "path": "/learning/progress", "purpose": "Web3Guard save real user lesson progress"},
    {"method": "GET", "path": "/admin/super/dashboard", "purpose": "Web3Guard admin super dashboard; requires ADMIN_TOKEN"},
    {"method": "GET", "path": "/admin/super/system-health", "purpose": "Web3Guard admin storage/provider health snapshot; requires ADMIN_TOKEN"},
    {"method": "GET", "path": "/ownership/policy", "purpose": "Ownership policy"},
    {"method": "POST", "path": "/ownership/challenge", "purpose": "DNS/.well-known ownership challenge"},

    {"method": "GET", "path": "/security-hardening/status", "purpose": "Web3Guard platform security hardening status"},
    {"method": "GET", "path": "/security-hardening/headers-preview", "purpose": "Web3Guard security headers preview"},
    {"method": "GET", "path": "/production-qa/status", "purpose": "Web3Guard final production QA status"},
    {"method": "GET", "path": "/production-qa/final-checklist", "purpose": "Web3Guard final launch checklist"},
    {"method": "GET", "path": "/production-qa/account-setup", "purpose": "Web3Guard manual account/env setup matrix"},
]

RUN_COMMANDS = {
    "backend_windows": [
        "cd backend",
        "py -3.12 -m venv .venv",
        r".\\.venv\\Scripts\\activate",
        "python -m pip install --upgrade pip setuptools wheel",
        "pip install -r requirements.txt",
        "copy .env.example .env",
        "uvicorn main:app --reload --host 0.0.0.0 --port 8000",
    ],
    "frontend_windows": [
        "cd frontend",
        "npm install",
        "copy .env.local.example .env.local",
        "npm run dev",
    ],
    "backend_linux_mac": [
        "cd backend",
        "python3.12 -m venv .venv",
        "source .venv/bin/activate",
        "python -m pip install --upgrade pip setuptools wheel",
        "pip install -r requirements.txt",
        "cp .env.example .env",
        "uvicorn main:app --reload --host 0.0.0.0 --port 8000",
    ],
    "frontend_linux_mac": [
        "cd frontend",
        "npm install",
        "cp .env.local.example .env.local",
        "npm run dev",
    ],
}


def _path_status(path_value: str, *, should_be_file: bool = True) -> dict[str, Any]:
    path = Path(path_value)
    parent = path.parent if should_be_file else path
    parent_exists = parent.exists()
    writable = False
    try:
        parent.mkdir(parents=True, exist_ok=True)
        probe = parent / ".web3guard_write_probe"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink(missing_ok=True)
        writable = True
    except Exception:
        writable = False
    return {
        "path": str(path),
        "parent": str(parent),
        "parent_exists": parent_exists,
        "writable": writable,
    }


def validate_environment() -> dict[str, Any]:
    admin_token_default = settings.admin_token in {"change-this-admin-token", "raadweb3_admin_1486_change_this", ""}
    upi_placeholder = settings.raadhanex_upi_id in {"raadhanex@upi", "yourupi@bank", ""}
    ai_configured = bool(settings.ai_enabled and settings.ai_provider != "none" and settings.ai_api_key)
    razorpay_configured = bool(settings.razorpay_enabled and settings.razorpay_key_id and settings.razorpay_key_secret)

    checks = [
        {
            "key": "python_runtime",
            "status": "pass",
            "label": "Python runtime pinned for deployment",
            "detail": "runtime.txt requires python-3.12.8. Local development should use Python 3.12.",
        },
        {
            "key": "admin_token",
            "status": "warning" if admin_token_default else "pass",
            "label": "Admin token configured",
            "detail": "Change ADMIN_TOKEN before production." if admin_token_default else "ADMIN_TOKEN is not the default placeholder.",
        },
        {
            "key": "upi_id",
            "status": "warning" if upi_placeholder else "pass",
            "label": "UPI payment receiver configured",
            "detail": "Replace RAADHANEX_UPI_ID/NEXT_PUBLIC_UPI_ID before real payment testing." if upi_placeholder else f"UPI receiver configured as {settings.raadhanex_upi_id}.",
        },
        {
            "key": "razorpay_mode",
            "status": "pass" if not settings.razorpay_enabled or razorpay_configured else "warning",
            "label": "Razorpay payment gateway",
            "detail": "Razorpay disabled; manual UPI fallback is active." if not settings.razorpay_enabled else ("Razorpay key ID/secret configured. Webhook secret still required for webhook verification." if razorpay_configured else "RAZORPAY_ENABLED=true but key ID/secret missing."),
        },
        {
            "key": "ai_mode",
            "status": "pass" if not settings.ai_enabled or ai_configured else "warning",
            "label": "AI provider mode is honest",
            "detail": "AI is disabled; fallback explanations are used." if not settings.ai_enabled else ("AI provider key is configured." if ai_configured else "AI_ENABLED=true but provider key is missing."),
        },
        {
            "key": "cors_origin",
            "status": "pass" if settings.frontend_origin.startswith("http") else "warning",
            "label": "Frontend origin configured",
            "detail": settings.frontend_origin,
        },
        {
            "key": "leads_storage",
            "status": "pass" if _path_status(settings.leads_file)["writable"] else "fail",
            "label": "Lead storage writable",
            "detail": _path_status(settings.leads_file),
        },
        {
            "key": "ownership_storage",
            "status": "pass" if _path_status(settings.ownership_challenges_file)["writable"] else "fail",
            "label": "Ownership challenge storage writable",
            "detail": _path_status(settings.ownership_challenges_file),
        },
        {
            "key": "public_report_storage",
            "status": "pass" if _path_status(settings.public_reports_file)["writable"] else "fail",
            "label": "Public/private report storage writable",
            "detail": _path_status(settings.public_reports_file),
        },
        {
            "key": "scanner_limits",
            "status": "pass",
            "label": "Scanner safety limits loaded",
            "detail": {
                "max_url_scan_per_hour": settings.max_url_scan_per_hour,
                "max_contract_scan_per_hour": settings.max_contract_scan_per_hour,
                "max_checklist_scan_per_hour": settings.max_checklist_scan_per_hour,
                "max_github_scan_per_hour": settings.max_github_scan_per_hour,
                "max_github_files": settings.max_github_files,
                "website_timeout_seconds": settings.website_scan_timeout_seconds,
                "max_body_bytes": settings.website_scan_max_body_bytes,
            },
        },
    ]
    failed = sum(1 for check in checks if check["status"] == "fail")
    warnings = sum(1 for check in checks if check["status"] == "warning")
    return {
        "ok": failed == 0,
        "version": "1.0",
        "environment": settings.app_env,
        "frontend_origin": settings.frontend_origin,
        "backend_url": settings.backend_url,
        "ai_enabled": settings.ai_enabled,
        "manual_upi_verification": True,
        "razorpay_enabled": settings.razorpay_enabled,
        "razorpay_configured": razorpay_configured,
        "certified_audit": False,
        "summary": {"failed": failed, "warnings": warnings, "passed": sum(1 for check in checks if check["status"] == "pass")},
        "checks": checks,
    }


def qa_runbook() -> dict[str, Any]:
    return {
        "local_urls": {
            "backend_health": f"{settings.backend_url}/health",
            "backend_readiness": f"{settings.backend_url}/health/readiness",
            "frontend": settings.frontend_origin,
            "frontend_qa": f"{settings.frontend_origin}/local-qa",
        },
        "run_commands": RUN_COMMANDS,
        "essential_frontend_routes": ESSENTIAL_FRONTEND_ROUTES,
        "essential_backend_endpoints": ESSENTIAL_BACKEND_ENDPOINTS,
        "manual_test_order": [
            "Open /health, /health/readiness, and /db/status.",
            "Open frontend /local-qa, /auth/signup, /auth/login, and /dashboard.",
            "Run one contract scan with sample Solidity.",
            "Run one unified URL scan with a site you own or are authorized to test.",
            "Open /launch-pack and compare deployment checklist against /launch/pack.",
            "Open /billing and /payments/status to check gateway mode.",
            "Create a payment intent from Pricing; Razorpay order should only appear when keys are configured.",
            "Submit a lead request with the payment reference field.",
            "Open /admin/leads using ADMIN_TOKEN and verify the lead appears.",
            "Export leads CSV.",
            "Generate/preview a combined report and use browser Print / Save as PDF.",
        ],
    }
