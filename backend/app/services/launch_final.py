from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from app.core.config import settings
from app.services.final_launch_completion import (
    external_provider_status,
    final_completion_summary,
    remaining_work_items,
)
from app.services.production_deployment_qa import production_deployment_qa_status

PHASE30_VERSION = "web3guard-launch-final-v30.0"
SAFE_RELEASE_WORDING = (
    "Web3Guard AI is a pre-audit launch readiness command center. Public release notes, trust pages, "
    "reports, and metrics must not claim certified audit status, 100% security, guaranteed safety, "
    "or Web3Guard discovery unless a real Web3Guard finding record exists."
)

BLOCKED_RELEASE_CLAIMS = [
    "certified audit",
    "certified auditor",
    "100% secure",
    "100 percent secure",
    "fully secure",
    "guaranteed secure",
    "hack proof",
    "exploit proof",
    "audited by web3guard",
    "web3guard audited",
    "official audit by web3guard",
    "verified auditor",
    "discovered by web3guard",
    "found by web3guard",
    "we discovered",
    "we found this vulnerability",
]

PROHIBITED_INPUTS = [
    "private key",
    "seed phrase",
    "mnemonic",
    "wallet signing request",
    "custodial funds",
]

SAFE_MISSING_LABELS = [
    "Tool Not Installed",
    "Provider Not Configured",
    "Needs API Key",
    "Manual",
    "Not Assessed",
]


@dataclass(frozen=True)
class LaunchGate:
    key: str
    area: str
    label: str
    status: str
    severity: str
    passed: bool
    evidence: str
    action: str


def _contains_blocked_claim(text: str | None) -> str | None:
    clean = (text or "").lower()
    for claim in BLOCKED_RELEASE_CLAIMS:
        if claim in clean:
            return claim
    return None


def _configured(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        clean = value.strip()
        if not clean:
            return False
        return clean.lower() not in {
            "change-this-admin-token",
            "yourupi@bank",
            "raadhanex@upi",
            "none",
            "null",
            "placeholder",
        }
    return bool(value)


def release_claim_check(text: str) -> dict[str, Any]:
    blocked = _contains_blocked_claim(text)
    return {
        "ok": True,
        "safe": blocked is None,
        "blocked_claim": blocked,
        "safe_release_wording": SAFE_RELEASE_WORDING,
        "rewrite_hint": None
        if blocked is None
        else "Use wording like: pre-audit launch readiness review, evidence snapshot, manual QA status, or provider configured/not configured. Do not imply certified audit or guaranteed security.",
    }


def public_release_gates() -> list[dict[str, Any]]:
    deployment = production_deployment_qa_status()
    failed_checks = [item for item in deployment["checks"] if not item.get("passed")]
    critical_failed = [item for item in failed_checks if item.get("severity") == "critical"]
    high_failed = [item for item in failed_checks if item.get("severity") == "high"]
    provider_data = external_provider_status()
    providers = provider_data["providers"]
    supabase_provider = next((p for p in providers if p["provider"].startswith("Supabase")), None)
    razorpay_provider = next((p for p in providers if p["provider"].startswith("Razorpay")), None)
    ai_provider = next((p for p in providers if p["provider"].startswith("AI")), None)

    gates = [
        LaunchGate(
            key="deployment_posture",
            area="Vercel + Render + Supabase",
            label="Production deployment QA posture",
            status="Ready" if deployment.get("production_ready") else "Manual / Action Required",
            severity="critical" if critical_failed else "high" if high_failed else "medium" if failed_checks else "low",
            passed=bool(deployment.get("production_ready")),
            evidence=f"{deployment.get('passed')}/{deployment.get('total')} deployment checks passed; readiness={deployment.get('readiness_label')}",
            action="Run /production-deployment-qa/status on the live backend and fix every critical/high item before public traffic.",
        ),
        LaunchGate(
            key="manual_approval",
            area="Launch approval",
            label="Manual public launch approval",
            status="Approved" if settings.production_launch_approved else "Manual",
            severity="high",
            passed=bool(settings.production_launch_approved),
            evidence=f"PRODUCTION_LAUNCH_APPROVED={settings.production_launch_approved}",
            action="Set PRODUCTION_LAUNCH_APPROVED=true only after founder/admin verifies live routes, legal pages, payments, auth, support, and incident process.",
        ),
        LaunchGate(
            key="supabase_live_auth",
            area="Auth + database",
            label="Supabase live auth/database configured",
            status=str(supabase_provider.get("status")) if supabase_provider else "Provider Not Configured",
            severity="high",
            passed=bool(supabase_provider and supabase_provider.get("status") == "Configured" and settings.supabase_jwt_verify_enabled),
            evidence="SUPABASE_URL/ANON/SERVICE_ROLE + SUPABASE_JWT_VERIFY_ENABLED required; service role backend-only.",
            action="Verify signup → email redirect → login → create project → save scan → report export with two-user access isolation.",
        ),
        LaunchGate(
            key="payment_live_verification",
            area="Payments",
            label="Razorpay/webhook or manual UPI is safely gated",
            status=str(razorpay_provider.get("status")) if razorpay_provider else "Manual",
            severity="critical" if settings.razorpay_enabled and not settings.razorpay_webhook_secret else "medium",
            passed=bool((not settings.razorpay_enabled) or settings.razorpay_webhook_secret),
            evidence=f"RAZORPAY_ENABLED={settings.razorpay_enabled}; webhook_secret_configured={bool(settings.razorpay_webhook_secret)}",
            action="Do not activate paid access unless backend order, signature, amount, currency, status, webhook secret, and idempotency are verified.",
        ),
        LaunchGate(
            key="safe_public_claims",
            area="Legal + trust copy",
            label="Public copy blocks unsafe audit/security claims",
            status="Ready",
            severity="critical",
            passed=True,
            evidence="Blocked wording includes certified audit, audited by Web3Guard, 100% secure, discovered by Web3Guard, and guaranteed secure.",
            action="Run the claim checker before publishing landing pages, trust pages, launch posts, or client handoff copy.",
        ),
        LaunchGate(
            key="provider_truthfulness",
            area="Providers + tools",
            label="Missing integrations use safe truthful labels",
            status="Ready",
            severity="high",
            passed=True,
            evidence=", ".join(SAFE_MISSING_LABELS),
            action="Keep provider/tool output as Not Assessed / Needs API Key / Tool Not Installed until live verified output exists.",
        ),
        LaunchGate(
            key="ai_privacy_gate",
            area="AI provider",
            label="AI code-sharing remains opt-in",
            status=str(ai_provider.get("status")) if ai_provider else "Provider Not Configured",
            severity="high",
            passed=not settings.ai_send_code and not settings.ai_fix_send_code,
            evidence=f"AI_SEND_CODE={settings.ai_send_code}; AI_FIX_SEND_CODE={settings.ai_fix_send_code}",
            action="Do not send user code to AI providers unless the user explicitly opts in and privacy copy is updated.",
        ),
    ]
    return [asdict(gate) for gate in gates]


def release_status() -> dict[str, Any]:
    gates = public_release_gates()
    failed = [gate for gate in gates if not gate["passed"]]
    critical = [gate for gate in failed if gate["severity"] == "critical"]
    high = [gate for gate in failed if gate["severity"] == "high"]
    if critical:
        label = "blocked_for_public_launch"
    elif high:
        label = "private_beta_or_internal_qa_only"
    elif failed:
        label = "controlled_public_beta_after_manual_review"
    else:
        label = "ready_for_public_beta_after_live_smoke_test"

    completion = final_completion_summary()
    return {
        "ok": True,
        "version": PHASE30_VERSION,
        "release_readiness": label,
        "passed_gates": len(gates) - len(failed),
        "total_gates": len(gates),
        "manual_approval_required": not bool(settings.production_launch_approved),
        "critical_blocker_count": len(critical),
        "high_blocker_count": len(high),
        "gates": gates,
        "remaining_high_priority_count": completion.get("high_priority_remaining_count", 0),
        "safe_release_wording": SAFE_RELEASE_WORDING,
        "safe_missing_labels": SAFE_MISSING_LABELS,
        "never_collect": PROHIBITED_INPUTS,
        "not_claimed": [
            "Not a certified audit company claim.",
            "Not a guarantee that the project is secure.",
            "Not a fake monitoring or fake provider output layer.",
            "Not a wallet-signing, private-key, seed-phrase, or exploit automation tool.",
        ],
    }


def public_release_checklist() -> dict[str, Any]:
    return {
        "ok": True,
        "version": PHASE30_VERSION,
        "sections": [
            {
                "area": "Local build verification",
                "required": True,
                "items": [
                    "cd backend && python -m pytest -q",
                    "cd frontend && npm run typecheck",
                    "cd frontend && npm run build",
                    "Open /launch-final, /production-deployment-qa, /scanner, /dashboard, /billing on mobile width.",
                ],
            },
            {
                "area": "Live deployment smoke test",
                "required": True,
                "items": [
                    "Open Vercel frontend on the latest deployment URL.",
                    "Open Render backend /health and /launch-final/status.",
                    "Verify CORS uses final FRONTEND_ORIGIN.",
                    "Check browser console for hydration/runtime errors.",
                ],
            },
            {
                "area": "Auth + data isolation",
                "required": True,
                "items": [
                    "Create user A and user B.",
                    "User A creates project, scan, report, and passport/trust page record.",
                    "User B must not access User A objects by direct URL/object ID.",
                    "Service role key must exist only on backend hosting.",
                ],
            },
            {
                "area": "Payments",
                "required": False,
                "items": [
                    "Run Razorpay test order only with test keys.",
                    "Confirm checkout signature and webhook verification before paid access.",
                    "Manual UPI remains Manual until admin verifies reference ID and audit note.",
                ],
            },
            {
                "area": "Public trust + legal copy",
                "required": True,
                "items": [
                    "Verify Terms, Privacy, Responsible Use, Limitations, Methodology, Security, and Refund/Scope copy.",
                    "Run /launch-final/claim-check before publishing marketing/client copy.",
                    "Keep pre-audit disclaimers visible on reports, trust pages, passport, metrics, and scanner output.",
                ],
            },
            {
                "area": "Ops readiness",
                "required": True,
                "items": [
                    "Configure uptime/error monitoring before marketing push.",
                    "Confirm backup/restore owner and data retention windows.",
                    "Prepare incident contact path and support inbox.",
                ],
            },
        ],
    }


def deploy_verification_plan() -> dict[str, Any]:
    return {
        "ok": True,
        "commands": {
            "backend": ["cd backend", "python -m pytest -q"],
            "frontend": ["cd frontend", "npm run typecheck", "npm run build"],
            "git": [
                "git status",
                "git add .",
                'git commit -m "Add launch final QA and public release layer"',
                "git push origin main",
            ],
        },
        "live_checks": [
            {"target": "Vercel", "check": "latest frontend deployment is Ready and public pages render without console runtime errors"},
            {"target": "Render", "check": "/health, /launch-final/status, /production-deployment-qa/status return 200"},
            {"target": "Supabase", "check": "Auth redirect URLs match production domain and RLS/user isolation is verified"},
            {"target": "Razorpay", "check": "test mode order/signature/webhook verified before live mode"},
            {"target": "SEO/security", "check": "robots.txt, sitemap.xml, manifest, security.txt, security headers, and metadata verified"},
        ],
    }


def safe_release_notes() -> dict[str, Any]:
    return {
        "ok": True,
        "title": "Web3Guard AI by RAADHANEX — Public Beta Release Notes",
        "safe_intro": (
            "Web3Guard AI is an India-first Web3 Founder Security OS for pre-audit launch readiness. "
            "It helps founders organize evidence, scanner output, provider readiness, reports, trust pages, monitoring status, community review, and public-safe metrics before a professional audit or launch review."
        ),
        "included_layers": [
            "Scanner + report foundation",
            "Real Engine Depth readiness matrix",
            "Provider Readiness and Live Integration hub",
            "Professional Report Verification",
            "Dashboard Workflow",
            "Production Deployment QA",
            "Razorpay/UPI payment safety layer",
            "Sentinel Monitoring + Vulnerability Intelligence foundation",
            "EON Risk Graph + Autonomous Fix Plan",
            "Security Test Generator",
            "Public Trust Page Generator",
            "Continuous Monitoring Lite",
            "Launch Trust Readiness",
            "India Launch Pack",
            "Security Copilot Workspace",
            "Community Review Layer",
            "Security Passport / Trust Network",
            "Performance + Launch Hardening Sprint",
            "Enterprise / Agency Launch Layer",
            "Real Worker Execution readiness layer",
            "Real Provider Live Integration",
            "Trust Metrics Engine",
            "Launch Final QA + Public Release layer",
        ],
        "not_claimed": [
            "Not a certified audit.",
            "Not 100% secure or guaranteed safe.",
            "Not exploit automation.",
            "Not wallet signing.",
            "No private key, seed phrase, or mnemonic collection.",
        ],
        "release_gate": "Publish only after live build, live auth, live payment mode, legal copy, support path, and two-user isolation checks are manually verified.",
    }


def remaining_after_phase30() -> dict[str, Any]:
    return {
        "ok": True,
        "summary": "Code-side Phase 30 public-release layer is now present. Remaining work is mostly live provider configuration, real worker hosting, manual QA, legal/ops setup, and market launch proof.",
        "remaining_work": remaining_work_items(),
        "next_deep_workstreams": [
            {
                "area": "Live deploy verification",
                "priority": "critical",
                "work": "Apply patches, push GitHub, verify Vercel and Render deployment logs, then run /health, /launch-final/status, /production-deployment-qa/status.",
            },
            {
                "area": "Supabase production auth + RLS proof",
                "priority": "critical",
                "work": "Two-user manual BOLA/IDOR test: user B must not read user A projects, scans, reports, passport, metrics, agency records, or reviews.",
            },
            {
                "area": "Razorpay live/payment ops",
                "priority": "high",
                "work": "Test mode order/signature/webhook/idempotency first; only then switch live keys. Manual UPI stays admin-verified.",
            },
            {
                "area": "Real worker execution hosting",
                "priority": "high",
                "work": "Move Slither/Aderyn/Semgrep/Foundry/Echidna/Mythril from readiness/probe to isolated Docker/worker execution with real logs and timeout/cleanup policy.",
            },
            {
                "area": "Provider depth",
                "priority": "medium",
                "work": "Add explorer chain selection, GoPlus live token/wallet checks, GitHub deeper file scanning, OSV/NVD/GitHub Advisory/CISA KEV ingestion after keys/rate limits are configured.",
            },
            {
                "area": "Legal + trust operations",
                "priority": "high",
                "work": "Professional review of Terms, Privacy, Refund/Scope, responsible use, disclosure process, GST/invoicing, and security contact flow.",
            },
            {
                "area": "Real market trust",
                "priority": "medium",
                "work": "Pilot with real friendly projects, collect permitted testimonials/case studies, and never show fake enterprise/customer logos.",
            },
        ],
    }
