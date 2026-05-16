from __future__ import annotations

from dataclasses import dataclass
from typing import Any

REAL_ONLY_NOTE = (
    "This guidance is rule-based hardening guidance. It does not prove a vulnerability is exploitable, "
    "does not run exploit automation, and is not a certified audit. Verify every fix in your own environment."
)


@dataclass(frozen=True)
class GuidanceItem:
    key: str
    label: str
    severity: str
    module: str
    where_to_fix: str
    why_it_matters: str
    how_to_fix: str
    verify: str
    safe_test: str
    status: str = "action_required"

    def to_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "label": self.label,
            "severity": self.severity,
            "module": self.module,
            "where_to_fix": self.where_to_fix,
            "why_it_matters": self.why_it_matters,
            "how_to_fix": self.how_to_fix,
            "verify": self.verify,
            "safe_test": self.safe_test,
            "status": self.status,
        }


GUIDANCE: list[GuidanceItem] = [
    GuidanceItem(
        key="csp_missing",
        label="Content-Security-Policy missing or weak",
        severity="high",
        module="frontend",
        where_to_fix="frontend/next.config.mjs or CDN/security headers layer",
        why_it_matters="CSP reduces the blast radius of XSS by restricting script, frame, image, style, and connection sources.",
        how_to_fix="Start with report-only CSP, allow self, Supabase, Render backend API, and Razorpay checkout only if enabled. Then enforce after testing login, scanner, and payments.",
        verify="curl -I https://web3guard-raadhanex.vercel.app | findstr /i content-security-policy",
        safe_test="Open login, dashboard, scanner, and Razorpay test checkout after CSP is enabled. Nothing should be blocked in browser console.",
    ),
    GuidanceItem(
        key="bola_idor",
        label="BOLA / IDOR ownership enforcement",
        severity="critical",
        module="backend",
        where_to_fix="backend project/report/scan detail routers and database access helpers",
        why_it_matters="A logged-in user must never access another user's projects, scans, reports, payments, or workspace records by guessing an ID.",
        how_to_fix="Resolve the user from the Supabase JWT on every protected endpoint and filter records by owner user_id. Return 403 or 404 on mismatch. Do not trust user_id from frontend alone.",
        verify="Create two test users. Save a project as user A. Login as user B and request user A project/report/scan id. Expected: 403 or 404.",
        safe_test="Use only your own test users and records. Do not test on third-party accounts.",
    ),
    GuidanceItem(
        key="rate_limit_enforcement",
        label="Scan and payment rate limits",
        severity="high",
        module="backend",
        where_to_fix="backend/app/services/rate_limit.py and scan/payment routers",
        why_it_matters="Without server-side rate limits, attackers can burn hosting quota, overload scanners, and spam payment/order creation.",
        how_to_fix="Apply per-user and per-client limits to scan, GitHub, contract, save report, and payment endpoints. Return 429 with a readable JSON error.",
        verify="Send repeated requests with the same user/token and confirm the API returns 429 after the configured limit.",
        safe_test="Use a local backend or your own staging deployment. Do not load-test public services without permission.",
    ),
    GuidanceItem(
        key="razorpay_webhook_signature",
        label="Razorpay webhook signature verification",
        severity="critical",
        module="payments",
        where_to_fix="backend/app/routers/payments.py and payment store/update functions",
        why_it_matters="Payment/subscription status must not be trusted from frontend callbacks. Only verified Razorpay signatures should mark paid/active states.",
        how_to_fix="Use raw request body + X-Razorpay-Signature + RAZORPAY_WEBHOOK_SECRET. Reject invalid signatures. Keep payments pending/manual if webhook is not configured.",
        verify="Use Razorpay test webhooks. Valid signature updates payment_intents/subscriptions. Invalid signature returns 400/401 and does not update paid state.",
        safe_test="Use Razorpay Test Mode only. Do not use real money until full test-mode flow passes.",
    ),
    GuidanceItem(
        key="api_docs_production",
        label="API docs exposure in production",
        severity="medium",
        module="backend",
        where_to_fix="backend/main.py FastAPI app configuration",
        why_it_matters="Public /docs, /redoc, and /openapi.json expose endpoint structure and make reconnaissance easier.",
        how_to_fix="Disable docs when APP_ENV=production or put them behind admin authentication in staging/internal environments.",
        verify="Open /docs, /redoc, and /openapi.json on production. Expected: 404 or protected.",
        safe_test="Use your own production URL only.",
    ),
    GuidanceItem(
        key="admin_access_control",
        label="Admin surface access control",
        severity="critical",
        module="admin",
        where_to_fix="frontend admin routes and backend admin dependencies",
        why_it_matters="Admin pages can expose leads, payments, reports, manual verification, and feature flags.",
        how_to_fix="Hide admin routes from normal users, require admin token/role server-side, and log every admin write action.",
        verify="Open admin routes logged out and as normal user. Expected: blocked. Admin writes should appear in audit log.",
        safe_test="Use test admin token and test user only.",
    ),
    GuidanceItem(
        key="scanner_result_evidence",
        label="Scanner evidence and fix guidance quality",
        severity="medium",
        module="scanner",
        where_to_fix="backend scanner services and frontend scanner result components",
        why_it_matters="A scanner is only useful if each finding includes evidence, risk reason, fix path, and verification steps.",
        how_to_fix="For every finding return title, severity, evidence, why, how_to_fix, where_to_fix, verify, and status. Mark missing modules as Not Assessed, not zero-scored.",
        verify="Run scan against your Vercel site and local OWASP Juice Shop. Every finding should include actionable fix guidance and no fake exploit claim.",
        safe_test="Use owned URLs or intentionally vulnerable local labs only.",
    ),
    GuidanceItem(
        key="supabase_rls",
        label="Supabase RLS and service-role separation",
        severity="high",
        module="database",
        where_to_fix="Supabase SQL policies and Render/Vercel environment separation",
        why_it_matters="Frontend must never have service-role access. User-owned records need RLS or backend ownership enforcement.",
        how_to_fix="Keep SUPABASE_SERVICE_ROLE_KEY only on Render. Use anon key on Vercel. Enable RLS for user data tables and write owner policies.",
        verify="Check Vercel env does not contain service-role key. In Supabase, verify RLS enabled on projects/scans/reports/payment tables.",
        safe_test="Use Supabase dashboard policy simulator or test users.",
    ),
]


def list_fix_guidance() -> dict[str, Any]:
    items = [item.to_dict() for item in GUIDANCE]
    by_severity: dict[str, int] = {}
    for item in items:
        by_severity[item["severity"]] = by_severity.get(item["severity"], 0) + 1
    return {
        "ok": True,
        "version": "2.0",
        "items": items,
        "summary": {
            "total": len(items),
            "by_severity": by_severity,
            "critical": by_severity.get("critical", 0),
            "high": by_severity.get("high", 0),
        },
        "real_only_note": REAL_ONLY_NOTE,
    }


def build_action_plan() -> dict[str, Any]:
    priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    ordered = sorted(GUIDANCE, key=lambda item: (priority_order.get(item.severity, 9), item.module, item.key))
    phases = [
        {
            "phase": "P0 — block fake/unsafe states",
            "goal": "Keep production honest and safe before deeper scanners/payments.",
            "items": [item.to_dict() for item in ordered if item.key in {"bola_idor", "admin_access_control", "razorpay_webhook_signature"}],
        },
        {
            "phase": "P1 — harden public surface",
            "goal": "Reduce exposure of frontend/backend public entry points.",
            "items": [item.to_dict() for item in ordered if item.key in {"csp_missing", "rate_limit_enforcement", "api_docs_production", "supabase_rls"}],
        },
        {
            "phase": "P2 — improve scanner usefulness",
            "goal": "Make output actionable for real launch fixes.",
            "items": [item.to_dict() for item in ordered if item.key in {"scanner_result_evidence"}],
        },
    ]
    return {
        "ok": True,
        "version": "2.0",
        "phases": phases,
        "next_recommended_patch": "BOLA/IDOR endpoint tests + report export from saved scan results",
        "safe_testing_targets": [
            "Own Vercel frontend URL",
            "Own Render backend health URL",
            "Local OWASP Juice Shop only",
            "Sepolia/testnet smart contracts owned by you",
        ],
        "blocked_testing": [
            "Random public websites without permission",
            "Banks, exchanges, government sites, production third-party apps",
            "Exploit automation or brute-force attempts",
            "Wallet signing/private key/seed phrase collection",
        ],
        "real_only_note": REAL_ONLY_NOTE,
    }
