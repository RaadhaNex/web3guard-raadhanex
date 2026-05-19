from __future__ import annotations

from typing import Any

from app.core.config import settings
from app.services.deep_analysis_tools import deep_analysis_status
from app.services.scan_contract_address import explorer_status
from app.services.scan_github_repo import github_scanner_status
from app.services.static_analysis_tools import static_analysis_status
from app.services.wallet_risk_integrations import wallet_risk_api_status


def _status(title: str, status: str, evidence: str, next_step: str, *, live: bool = False) -> dict[str, Any]:
    return {
        "title": title,
        "status": status,
        "live": live,
        "evidence": evidence,
        "next_step": next_step,
    }


def _tool_status_from_static(static: dict[str, Any], tool: str) -> str:
    data = (static.get("tools") or {}).get(tool) or {}
    if data.get("will_run"):
        return "Live"
    if data.get("installed") and data.get("enabled_by_env") and not static.get("static_analysis_enabled"):
        return "Provider Not Configured"
    if data.get("installed"):
        return "Provider Not Configured"
    return "Tool Not Installed"


def _tool_status_from_deep(deep: dict[str, Any], tool: str) -> str:
    data = (deep.get("tools") or {}).get(tool) or {}
    if data.get("will_run"):
        return "Live"
    if tool == "mythril" and not data.get("will_run"):
        return "Worker Required / Not Assessed"
    if data.get("installed"):
        return "Provider Not Configured"
    return "Tool Not Installed"


def public_beta_readiness_status() -> dict[str, Any]:
    static = static_analysis_status()
    deep = deep_analysis_status()
    explorer = explorer_status()
    github = github_scanner_status()
    wallet = wallet_risk_api_status()

    ai_key_configured = bool(settings.ai_api_key or settings.openai_api_key or settings.anthropic_api_key)
    ai_provider_ready = bool(settings.ai_enabled and settings.ai_provider != "none" and ai_key_configured)

    rows = [
        _status(
            "Etherscan / explorer verified-source readiness",
            "Live" if explorer.get("etherscan_v2_enabled") else "Needs API Key",
            "Explorer scanner status comes from backend config and verified-source availability; no fake source is generated.",
            "Set ETHERSCAN_API_KEY and test /scan/contract-address/status plus one verified address.",
            live=bool(explorer.get("etherscan_v2_enabled")),
        ),
        _status(
            "GitHub public repo scanner/status",
            "Live for public repos" if github.get("ok") else "Manual",
            "Read-only public repository scanner is available. Token only improves rate limits/private authorized workflows later.",
            "Set GITHUB_API_TOKEN for better rate limits if needed; never scan private repos without authorization.",
            live=bool(github.get("ok")),
        ),
        _status(
            "Slither",
            _tool_status_from_static(static, "slither"),
            "Static analysis uses real subprocess output only. Missing binary stays Tool Not Installed.",
            "Install Slither on an isolated worker and enable STATIC_ANALYSIS_ENABLED only after verification.",
            live=_tool_status_from_static(static, "slither") == "Live",
        ),
        _status(
            "Aderyn",
            _tool_status_from_static(static, "aderyn"),
            "Aderyn is optional and must not emit fake findings when not installed.",
            "Install Aderyn and set ADERYN_ENABLED plus binary/env values when ready.",
            live=_tool_status_from_static(static, "aderyn") == "Live",
        ),
        _status(
            "Mythril",
            _tool_status_from_deep(deep, "mythril"),
            "Mythril remains worker/Docker gated by default; no fake symbolic execution output.",
            "Use an isolated worker with strict timeout and ownership verification.",
            live=_tool_status_from_deep(deep, "mythril") == "Live",
        ),
        _status(
            "AI provider",
            "Live" if ai_provider_ready else "Provider Not Configured / Needs API Key",
            "AI is optional and backend-only. Local fix guidance remains available without AI.",
            "Set AI_ENABLED=true, AI_PROVIDER, and provider key only after data-sharing policy is approved.",
            live=ai_provider_ready,
        ),
        _status(
            "GoPlus/token/wallet risk readiness",
            "Live optional provider" if settings.goplus_enabled else "Provider Not Configured",
            "Wallet risk integration is read-only. No wallet connect, no signing, no seed/private-key collection.",
            "Enable GOPLUS only after provider terms/privacy review; otherwise use wallet UX checklist.",
            live=bool(settings.goplus_enabled),
        ),
        _status(
            "Payment / UPI / Razorpay",
            "Deferred",
            "Payment is intentionally deferred. No paid/subscription success should be shown from frontend-only state.",
            "Finish Razorpay order, checkout, webhook signature verification, admin audit log, and UTR fallback in final phase.",
            live=False,
        ),
    ]

    return {
        "ok": True,
        "phase": "non_payment_public_beta_readiness",
        "real_only": True,
        "payments_deferred": True,
        "blocked_claims": [
            "certified audit",
            "100% secure",
            "AI verified/audited",
            "payment successful without verified flow",
            "subscription active without verified backend state",
            "wallet signed/approved",
            "exploit-proof",
        ],
        "readiness": rows,
        "raw_status": {
            "explorer": explorer,
            "github": github,
            "static_analysis": static,
            "deep_analysis": deep,
            "wallet_risk": wallet,
        },
    }
