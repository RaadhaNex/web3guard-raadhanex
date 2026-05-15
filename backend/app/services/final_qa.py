from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.core.config import settings
from app.services.security_hardening import security_status


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _path(raw: str) -> Path:
    path = Path(raw)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text("", encoding="utf-8")
    return path


def _append_jsonl(raw: str, row: dict[str, Any]) -> None:
    path = _path(raw)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, default=str, ensure_ascii=False) + "\n")


def manual_accounts_needed() -> list[dict[str, str]]:
    return [
        {"service": "Supabase", "needed_for": "Auth, database, RLS, scan history, reports", "env_keys": "SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_ROLE_KEY"},
        {"service": "Razorpay", "needed_for": "Real UPI/card checkout, webhook verified paid state", "env_keys": "RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET, RAZORPAY_WEBHOOK_SECRET"},
        {"service": "Etherscan", "needed_for": "Verified contract source/ABI by address", "env_keys": "ETHERSCAN_API_KEY"},
        {"service": "GitHub", "needed_for": "Higher-rate public repo scanning and future private repo scan", "env_keys": "GITHUB_API_TOKEN"},
        {"service": "OpenAI or Anthropic", "needed_for": "Real AI fix suggestions", "env_keys": "OPENAI_API_KEY or ANTHROPIC_API_KEY"},
        {"service": "RPC provider: Alchemy/Infura/QuickNode", "needed_for": "Monitoring Lite read-only log checks", "env_keys": "ETHEREUM_RPC_URL, POLYGON_RPC_URL, etc."},
        {"service": "SMTP/Resend/SendGrid", "needed_for": "Real email notifications", "env_keys": "SMTP_* or provider keys"},
        {"service": "Telegram BotFather", "needed_for": "Telegram alerts", "env_keys": "TELEGRAM_BOT_TOKEN"},
        {"service": "Discord", "needed_for": "Discord webhook alerts", "env_keys": "DISCORD_WEBHOOK_URL"},
        {"service": "GoPlus", "needed_for": "Optional token/spender risk lookups", "env_keys": "GOPLUS_ACCESS_TOKEN optional"},
        {"service": "Sentry/Uptime monitor", "needed_for": "Production monitoring", "env_keys": "SENTRY_DSN / provider config"},
        {"service": "Legal/CA review", "needed_for": "Terms, privacy, refund/scope, compliance and GST readiness review", "env_keys": "manual professional review"},
    ]


def implementation_map() -> dict[str, Any]:
    return {
        "ok": True,
        "real_live_now": [
            "Local FastAPI + Next.js app", "Rule-engine contract scans", "Passive website scans", "dApp/API/wallet/admin checklist scans", "Combined reports", "Lead capture", "Manual UPI flow", "Admin dashboards", "GitHub public repo read-only scanner", "Etherscan source fetch when API key is set", "Optional tool runners when tools are installed", "Optional AI provider when keys/privacy are configured",
        ],
        "manual_setup_required": manual_accounts_needed(),
        "manual_admin_actions": [
            "Verify manual UPI payments before marking paid", "Review critical findings before sending to clients", "Approve public registry publications", "Triage bug bounty submissions", "Curate threat intelligence entries", "Review compliance docs with lawyer/CA",
        ],
        "never_collect": ["private keys", "seed phrases", "mnemonics", "wallet signing requests", "custodial funds"],
        "real_only_rule": "Anything not configured must show disabled/manual/not assessed, never fake success or fake audit output.",
    }


def final_launch_checklist() -> list[dict[str, Any]]:
    return [
        {"area": "Local QA", "items": ["backend /health works", "frontend npm run build passes locally", "scanner pages load", "admin token flow works", "UPI link/manual payment status works"]},
        {"area": "Production env", "items": ["APP_ENV=production", "FRONTEND_ORIGIN=https domain", "ADMIN_TOKEN rotated", "secrets set in host dashboard not committed"]},
        {"area": "Database/Auth", "items": ["Supabase migrations applied", "RLS enabled", "service-role key backend only", "JWT verification enabled"]},
        {"area": "Payments", "items": ["Razorpay test order works", "webhook verified", "manual UPI fallback tested", "refund/scope policy published"]},
        {"area": "Security boundaries", "items": ["No fake audit/certification wording", "deep scan gated", "private/internal URL blocking tested", "rate limits configured", "AI code sharing opt-in only"]},
        {"area": "Legal/trust", "items": ["Terms/privacy/refund reviewed", "pre-audit disclaimers visible", "no 100% secure claims", "responsible use policy published"]},
        {"area": "Monitoring", "items": ["Sentry/error monitor configured", "uptime monitor configured", "backup policy configured", "incident contact/process ready"]},
    ]


def launch_readiness() -> dict[str, Any]:
    sec = security_status()
    manual_blockers = []
    if not settings.production_launch_approved:
        manual_blockers.append("PRODUCTION_LAUNCH_APPROVED is false. This is intentional until final manual review is complete.")
    if sec["readiness"] in {"blocked", "not_ready"}:
        manual_blockers.append("Security hardening checks still have critical/high action items.")
    return {
        "ok": True,
        "phase": "Mega Phase G - Final Production Launch QA",
        "launch_readiness": "ready_for_private_beta" if not manual_blockers else "not_ready_for_public_launch",
        "security_readiness": sec["readiness"],
        "security_score": sec["score"],
        "manual_blockers": manual_blockers,
        "checklist": final_launch_checklist(),
        "manual_accounts_needed": manual_accounts_needed(),
        "real_only_note": "Final QA does not approve production automatically. RAADHANEX admin must review accounts, policies, payments, database, and legal docs before public launch.",
    }


def record_qa_run(actor: str = "local-admin", note: str = "manual QA snapshot") -> dict[str, Any]:
    data = launch_readiness()
    row = {"id": f"qa_{int(datetime.now(timezone.utc).timestamp())}", "created_at": _now(), "actor": actor, "note": note, "readiness": data["launch_readiness"], "security_score": data["security_score"]}
    _append_jsonl(settings.final_qa_last_run_file, row)
    return {"ok": True, "qa_run": row, "readiness": data}
