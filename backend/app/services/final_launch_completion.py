from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from app.core.config import settings
from app.services.payment_store import payment_status


@dataclass(frozen=True)
class CompletionItem:
    area: str
    status: str
    priority: str
    owner: str
    what_is_done: str
    remaining_work: str
    how_to_complete: str
    verify: str


def _configured(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        clean = value.strip()
        if not clean:
            return False
        return clean.lower() not in {"change-this-admin-token", "yourupi@bank", "raadhanex@upi", "none", "null", "placeholder"}
    return bool(value)


def _status(done: bool, partial: bool = False) -> str:
    if done:
        return "done"
    if partial:
        return "manual_remaining"
    return "pending"


def external_provider_status() -> dict[str, Any]:
    payments = payment_status()
    return {
        "ok": True,
        "real_only_rule": "A provider is considered live only when required env keys exist and the backend can verify the provider output. Missing providers must show Not configured / Manual / Not assessed, not fake success.",
        "providers": [
            {
                "provider": "Supabase Auth + Database",
                "status": _status(_configured(settings.supabase_url) and _configured(settings.supabase_anon_key) and _configured(settings.supabase_service_role_key)),
                "required_env": ["SUPABASE_URL", "SUPABASE_ANON_KEY", "SUPABASE_SERVICE_ROLE_KEY", "SUPABASE_AUTH_REQUIRED", "SUPABASE_JWT_VERIFY_ENABLED"],
                "verify": "Signup, confirm email, login, create project, save scan, create report. Supabase rows should belong to the logged-in user.",
            },
            {
                "provider": "Razorpay Test/Live",
                "status": _status(bool(payments.get("razorpay_configured") and payments.get("razorpay_webhook_configured")), partial=bool(payments.get("razorpay_enabled"))),
                "required_env": ["RAZORPAY_ENABLED", "PAYMENT_MODE", "RAZORPAY_KEY_ID", "RAZORPAY_KEY_SECRET", "RAZORPAY_WEBHOOK_SECRET"],
                "verify": "Create Razorpay order in test mode, complete checkout, verify backend signature, receive webhook, then confirm payment_intents/subscriptions update only after verification.",
            },
            {
                "provider": "Manual UPI",
                "status": _status(_configured(settings.raadhanex_upi_id), partial=True),
                "required_env": ["RAADHANEX_UPI_ID", "RAADHANEX_UPI_NAME", "NEXT_PUBLIC_UPI_ID", "NEXT_PUBLIC_UPI_NAME"],
                "verify": "UPI link opens with correct receiver. Admin verification requires a reference ID and audit note before activation.",
            },
            {
                "provider": "AI Fix Assistant",
                "status": _status(bool(settings.ai_enabled and (settings.openai_api_key or settings.anthropic_api_key))),
                "required_env": ["AI_ENABLED", "AI_PROVIDER", "OPENAI_API_KEY or ANTHROPIC_API_KEY", "AI_SEND_CODE", "AI_FIX_ENABLED", "AI_FIX_SEND_CODE"],
                "verify": "Without keys, UI must say Provider Not Configured. With keys, AI output must not claim certified audit and must respect code-sharing limits.",
            },
            {
                "provider": "Static Analysis Tools",
                "status": _status(bool(settings.static_analysis_enabled and (settings.slither_binary or settings.aderyn_binary or settings.semgrep_binary)), partial=bool(settings.static_analysis_enabled)),
                "required_env": ["STATIC_ANALYSIS_ENABLED", "SLITHER_BINARY", "ADERYN_BINARY", "SEMGREP_BINARY"],
                "verify": "If binaries are missing, output must say Tool Not Installed. If installed, tool output must be parsed from real execution.",
            },
            {
                "provider": "Deep Analysis Worker",
                "status": _status(bool(settings.deep_analysis_enabled and not settings.mythril_worker_required)),
                "required_env": ["DEEP_ANALYSIS_ENABLED", "MYTHRIL_WORKER_REQUIRED", "MYTHRIL_ALLOW_LOCAL_EXECUTION", "MYTHRIL_DOCKER_ENABLED"],
                "verify": "Mythril/deep tools should remain Worker Required unless isolated worker/Docker is intentionally configured. No fake deep-analysis result.",
            },
            {
                "provider": "Etherscan V2",
                "status": _status(_configured(settings.etherscan_api_key)),
                "required_env": ["ETHERSCAN_API_KEY", "ETHERSCAN_V2_API_BASE"],
                "verify": "Scan a verified testnet contract and an unverified/invalid address. Missing key must show Needs API Key.",
            },
            {
                "provider": "GitHub Repo Scanner",
                "status": _status(_configured(settings.github_api_token), partial=True),
                "required_env": ["GITHUB_API_TOKEN optional", "GITHUB_API_BASE"],
                "verify": "Public repos should scan without token within public rate limits. Token increases rate limits but must never be exposed to frontend.",
            },
            {
                "provider": "Monitoring RPC",
                "status": _status(bool(settings.monitoring_enabled and (settings.ethereum_rpc_url or settings.polygon_rpc_url or settings.base_rpc_url))),
                "required_env": ["MONITORING_ENABLED", "ETHEREUM_RPC_URL", "POLYGON_RPC_URL", "BASE_RPC_URL"],
                "verify": "Monitoring remains disabled/manual until RPC URLs are configured. Missing RPC must not create fake alerts.",
            },
            {
                "provider": "Custom Domain + SMTP",
                "status": "external_manual",
                "required_env": ["Vercel domain settings", "Supabase Auth URL config", "custom SMTP provider settings"],
                "verify": "Custom domain opens site, auth redirect URLs match domain, email confirmation arrives from branded SMTP sender.",
            },
        ],
    }


def remaining_work_items() -> list[dict[str, str]]:
    items = [
        CompletionItem(
            area="Razorpay Test Mode",
            status="pending_external_config" if not settings.razorpay_enabled else "manual_verify",
            priority="high",
            owner="founder/devops",
            what_is_done="Backend supports real order creation, checkout signature verification, webhook endpoint, and manual UPI fallback.",
            remaining_work="Add Razorpay test keys + webhook secret in Render, add public key in Vercel, configure webhook URL in Razorpay dashboard.",
            how_to_complete="Set RAZORPAY_ENABLED=true, PAYMENT_MODE=razorpay_or_upi_manual, RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET, RAZORPAY_WEBHOOK_SECRET. Webhook URL: /payments/webhook/razorpay.",
            verify="Use Razorpay test mode. Payment must become verified only after backend signature/webhook verification.",
        ),
        CompletionItem(
            area="Supabase SMTP Branding",
            status="pending_external_config",
            priority="medium",
            owner="founder/devops",
            what_is_done="Supabase Auth flow, /auth/callback and frontend auth pages are wired.",
            remaining_work="Configure custom SMTP and final auth redirect URLs for custom domain.",
            how_to_complete="Supabase → Authentication → SMTP Settings; set sender domain, SMTP credentials, Site URL and Redirect URLs.",
            verify="Create a new account and confirm that verification email arrives from branded sender and redirects to /auth/callback.",
        ),
        CompletionItem(
            area="Custom Domain + CSP",
            status="pending_external_config",
            priority="medium",
            owner="founder/devops",
            what_is_done="Vercel domain and security headers are code-ready for the default Vercel domain.",
            remaining_work="Add custom domain in Vercel and update CSP/connect-src/frame-src if backend/frontend domains change.",
            how_to_complete="Add domain in Vercel, update FRONTEND_ORIGIN in Render, update Supabase Site URL/Redirect URLs, then re-run header scan.",
            verify="curl -I custom-domain; login/signup/scan still works; CSP does not block Supabase, backend or Razorpay.",
        ),
        CompletionItem(
            area="AI Fix Assistant Provider",
            status="pending_paid_provider",
            priority="medium",
            owner="founder/devops",
            what_is_done="AI endpoints/UI are designed to be honest when provider is missing.",
            remaining_work="Add OpenAI or Anthropic API key and decide whether source code can be sent to provider.",
            how_to_complete="Set AI_ENABLED=true, AI_PROVIDER=openai/anthropic, provider API key, AI_FIX_ENABLED=true, and keep AI_FIX_SEND_CODE=false unless user explicitly opts in.",
            verify="Without code-sharing, AI explains fix guidance only. With opt-in, it can analyze provided snippets but must not claim certified audit.",
        ),
        CompletionItem(
            area="Slither/Aderyn/Semgrep Tooling",
            status="pending_worker_or_binary",
            priority="medium",
            owner="security/devops",
            what_is_done="Tool runner policy is real-only and can say Tool Not Installed when binaries are missing.",
            remaining_work="Install tools on an isolated worker or configure binaries safely.",
            how_to_complete="Prefer isolated worker/Docker for heavy analysis. Configure SLITHER_BINARY/ADERYN_BINARY/SEMGREP_BINARY only after testing.",
            verify="Run known vulnerable sample contract. Output must include real tool command status and parsed findings.",
        ),
        CompletionItem(
            area="Manual BOLA/IDOR QA",
            status="manual_test_required",
            priority="high",
            owner="security/qa",
            what_is_done="Dashboard routes and tests are hardened to require ownership checks.",
            remaining_work="Run two-user manual verification on live deployment.",
            how_to_complete="Create user A and user B. Save project/report as A. Login as B and try direct URL/object ID access.",
            verify="B must receive 403/404 and must not see A's objects.",
        ),
        CompletionItem(
            area="Public Launch QA",
            status="manual_test_required",
            priority="high",
            owner="founder/qa",
            what_is_done="Scripts and final QA pages are included.",
            remaining_work="Run final live QA after every GitHub push and deployment.",
            how_to_complete="Run scripts/final_live_qa.ps1 and manually test signup → login → scan → save → report export → logout.",
            verify="All health/readiness endpoints pass, Vercel/Render latest deploys are Ready/Live, and no fake/demo user is visible.",
        ),
    ]
    return [asdict(item) for item in items]


def final_completion_summary() -> dict[str, Any]:
    providers = external_provider_status()["providers"]
    pending = [p for p in providers if p["status"] not in {"done"}]
    remaining = remaining_work_items()
    high_pending = [item for item in remaining if item["priority"] == "high" and not item["status"].startswith("done")]
    return {
        "ok": True,
        "product": settings.app_name,
        "environment": settings.app_env,
        "code_side_status": "launch-critical hardening patches completed; remaining work is mostly provider configuration and manual QA",
        "external_provider_pending_count": len(pending),
        "high_priority_remaining_count": len(high_pending),
        "remaining_work": remaining,
        "providers": providers,
        "blocked_claims": [
            "Do not claim certified audit.",
            "Do not claim 100% secure.",
            "Do not show fake scan/tool/payment success.",
            "Do not collect private key, seed phrase or mnemonic.",
            "Do not run exploit automation against third-party targets.",
        ],
        "next_safe_tests": [
            "Own Vercel URL passive scan",
            "Own Render health endpoint passive scan",
            "Local OWASP Juice Shop with local backend/frontend only",
            "Sepolia/testnet verified contract scan",
            "Razorpay test mode payment + webhook verification",
        ],
    }


def next_chat_handoff_text() -> str:
    return """Continue Web3Guard AI by RAADHANEX from the latest working live deployment.

Current state:
- Replaced heavy old web3guard(1).zip source with clean web3guard-v2-final(1).zip lineage.
- GitHub, Vercel frontend and Render backend are live.
- Supabase Auth/DB is configured; login/signup/dashboard real session flow was fixed.
- Scanner is login-gated, real-only, shows progress, and avoids fake scores for missing inputs.
- Production Hardening Phase 1-5 were being applied:
  Phase 1: CSP/security headers, production docs behavior, scan auth/rate-limit foundation.
  Phase 2: security fix-guidance catalog and cleaner Security Hardening UI.
  Phase 3: saved scan → report export flow and BOLA/IDOR tests.
  Phase 4: admin payment hardening, payment audit migration, final QA script.
  Phase 5: final completion/readiness endpoints and provider/manual QA handoff.

Rules:
- Everything must be real; no fake/dummy/stub success.
- Missing providers/tools must show Provider Not Configured / Tool Not Installed / Needs API Key / Manual / Not Assessed.
- Do not claim certified audit or 100% secure.
- Do not collect private key, seed phrase or mnemonic.
- No exploit automation or third-party scanning without authorization.

Next likely work:
- Apply latest patch and run frontend npm run build + backend compileall/pytest.
- Push to GitHub, verify Vercel + Render redeploy.
- Configure external providers: Razorpay test mode/webhook, SMTP/custom domain, OpenAI/Claude, Slither/Aderyn worker.
- Run final live QA: signup → login → scan → save → report export → logout → BOLA manual test.

Upload latest clean source ZIP or latest build/deploy error logs if continuing."""
