from __future__ import annotations

from typing import Any

from app.core.config import settings
from app.services.deep_analysis_tools import deep_analysis_status
from app.services.scan_contract_address import explorer_status
from app.services.scan_github_repo import github_scanner_status
from app.services.static_analysis_tools import static_analysis_status
from app.services.wallet_risk_integrations import wallet_risk_api_status

ENGINE_DEPTH_VERSION = "web3guard-real-engine-depth-v9.0"


def _status_label(*, enabled: bool, installed: bool | None = None, configured: bool | None = None, will_run: bool | None = None) -> str:
    if will_run:
        return "Ready"
    if not enabled:
        return "Provider Not Configured"
    if installed is False:
        return "Tool Not Installed"
    if configured is False:
        return "Needs API Key"
    return "Manual / Not Assessed"


def engine_depth_status() -> dict[str, Any]:
    static = static_analysis_status()
    deep = deep_analysis_status()
    github = github_scanner_status()
    explorer = explorer_status()
    wallet = wallet_risk_api_status()

    static_tools = []
    for name, data in static.get("tools", {}).items():
        static_tools.append({
            "name": name,
            "category": "static_analysis",
            "status": _status_label(
                enabled=bool(static.get("static_analysis_enabled") and data.get("enabled_by_env")),
                installed=bool(data.get("installed")),
                will_run=bool(data.get("will_run")),
            ),
            "installed": bool(data.get("installed")),
            "enabled_by_env": bool(data.get("enabled_by_env")),
            "will_run": bool(data.get("will_run")),
            "path": data.get("path"),
            "safe_note": "Runs only real subprocess output from a temp workspace when enabled and installed.",
        })

    deep_tools = []
    for name, data in deep.get("tools", {}).items():
        worker = data.get("worker_status") or {}
        deep_tools.append({
            "name": name,
            "category": "deep_analysis",
            "status": _status_label(
                enabled=bool(deep.get("deep_analysis_enabled") and data.get("enabled_by_env")),
                installed=bool(data.get("installed")),
                will_run=bool(data.get("will_run")),
            ),
            "installed": bool(data.get("installed")),
            "enabled_by_env": bool(data.get("enabled_by_env")),
            "will_run": bool(data.get("will_run")),
            "worker_status": worker,
            "safe_note": "Deep tools stay worker-gated; Mythril remains Docker/worker-required unless explicitly allowed.",
        })

    provider_integrations = [
        {
            "name": "GitHub public repo scanner",
            "category": "repo_intelligence",
            "status": "Ready",
            "configured": True,
            "safe_note": "Read-only GitHub API tree/content scan with file and byte limits. Does not clone, install, or execute repo code.",
            "details": github,
        },
        {
            "name": "Etherscan-compatible explorer",
            "category": "verified_source",
            "status": _status_label(enabled=bool(settings.etherscan_api_key), configured=bool(settings.etherscan_api_key)),
            "configured": bool(settings.etherscan_api_key),
            "safe_note": "Fetches verified public source only when API key is configured. Missing key remains Needs API Key.",
            "details": explorer,
        },
        {
            "name": "GoPlus/token-wallet risk",
            "category": "wallet_token_risk",
            "status": _status_label(enabled=bool(wallet.get("goplus_enabled")), configured=bool(wallet.get("goplus_enabled"))),
            "configured": bool(wallet.get("goplus_enabled")),
            "safe_note": "Read-only provider integration only. No wallet connect, no signing, no private keys.",
            "details": wallet,
        },
    ]

    ready_count = sum(1 for item in [*static_tools, *deep_tools, *provider_integrations] if item.get("status") == "Ready")
    total_count = len(static_tools) + len(deep_tools) + len(provider_integrations)

    return {
        "ok": True,
        "version": ENGINE_DEPTH_VERSION,
        "ready_count": ready_count,
        "total_count": total_count,
        "readiness_label": "Real engine depth partially ready" if ready_count else "Engine integrations not configured",
        "static_tools": static_tools,
        "deep_tools": deep_tools,
        "provider_integrations": provider_integrations,
        "recommended_next_env": [
            "STATIC_ANALYSIS_ENABLED=true only on an isolated worker with Slither/Aderyn/Semgrep installed.",
            "DEEP_ANALYSIS_ENABLED=true only with worker policy, strict timeout, and no secrets in workspace.",
            "ETHERSCAN_API_KEY for verified public contract source fetching.",
            "GITHUB_API_TOKEN only if private/limited-rate repo access is explicitly authorized.",
            "GoPlus/provider keys only for read-only token/wallet risk checks.",
        ],
        "safety_boundaries": {
            "no_fake_tool_output": True,
            "no_dependency_install_by_default": True,
            "no_repo_clone": True,
            "no_wallet_signing": True,
            "no_private_key_collection": True,
            "no_exploit_automation": True,
            "not_certified_audit": True,
        },
    }
