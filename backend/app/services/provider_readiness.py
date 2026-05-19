from __future__ import annotations

from typing import Any

from app.core.config import settings
from app.services.scan_contract_address import SUPPORTED_CHAINS, explorer_status
from app.services.wallet_risk_integrations import wallet_risk_api_status

PROVIDER_READINESS_VERSION = "web3guard-provider-readiness-v10.0"


def _state(*, configured: bool, enabled: bool = True) -> str:
    if not enabled:
        return "Provider Not Configured"
    if not configured:
        return "Needs API Key"
    return "Ready"


def _masked(value: str | None) -> str | None:
    if not value:
        return None
    if len(value) <= 8:
        return "configured"
    return f"{value[:4]}...{value[-4:]}"


def provider_readiness_status() -> dict[str, Any]:
    explorer = explorer_status()
    wallet = wallet_risk_api_status()

    etherscan_configured = bool(settings.etherscan_api_key)
    github_configured = bool(settings.github_api_token)
    goplus_enabled = bool(settings.goplus_enabled)
    goplus_auth_configured = bool(settings.goplus_access_token)

    providers = [
        {
            "key": "etherscan_v2",
            "name": "Etherscan V2 / compatible explorer",
            "status": _state(configured=etherscan_configured),
            "configured": etherscan_configured,
            "masked_credential": _masked(settings.etherscan_api_key),
            "api_base": settings.etherscan_v2_api_base,
            "live_endpoint": "/scan/contract-address",
            "what_it_enables": [
                "Verified public source fetch by contract address",
                "ABI/metadata summary",
                "Local rule-engine scan against verified source",
                "Proxy/compiler/license/admin-surface evidence hints",
            ],
            "not_claimed": [
                "No bytecode decompilation",
                "No wallet signing",
                "No certified audit score",
                "No Slither/Aderyn/Mythril execution inside address scan",
            ],
            "details": explorer,
        },
        {
            "key": "goplus",
            "name": "GoPlus token / wallet / approval risk",
            "status": "Ready" if goplus_enabled else "Provider Not Configured",
            "configured": goplus_enabled,
            "masked_credential": _masked(settings.goplus_access_token),
            "api_base": settings.goplus_api_base,
            "live_endpoint": "/scan/wallet-risk",
            "what_it_enables": [
                "Token security flags when token address is provided",
                "Address security flags for wallet or spender addresses",
                "Approval contract security status when approval contract is provided",
                "Provider failures shown honestly instead of fake risk results",
            ],
            "not_claimed": [
                "No wallet connect",
                "No seed/private key collection",
                "No transaction signing",
                "No automatic revoke transaction",
            ],
            "details": wallet,
        },
        {
            "key": "github_public_repo",
            "name": "GitHub public repository scanner",
            "status": "Ready",
            "configured": True,
            "masked_credential": _masked(settings.github_api_token),
            "api_base": settings.github_api_base,
            "live_endpoint": "/scan/github",
            "what_it_enables": [
                "Read-only repository tree scan",
                "CI/security policy/license/lockfile/test evidence summary",
                "Solidity/API/frontend file pattern review within strict byte limits",
                "Optional token only for rate limit / authorized access",
            ],
            "not_claimed": [
                "No repo clone",
                "No dependency install",
                "No code execution",
                "No private repo scan without authorization",
            ],
            "details": {
                "token_configured": github_configured,
                "max_files": settings.max_github_files,
                "max_total_bytes": settings.max_github_total_bytes,
                "timeout_seconds": settings.github_scan_timeout_seconds,
            },
        },
    ]

    ready_count = sum(1 for item in providers if item["status"] == "Ready")

    return {
        "ok": True,
        "version": PROVIDER_READINESS_VERSION,
        "ready_count": ready_count,
        "total_count": len(providers),
        "readiness_label": "Provider layer ready" if ready_count == len(providers) else "Provider layer partially configured",
        "providers": providers,
        "chain_matrix": {
            "etherscan_supported_chains": SUPPORTED_CHAINS,
            "goplus_local_aliases": wallet.get("supported_local_chain_aliases"),
        },
        "safe_env_to_add": [
            "ETHERSCAN_API_KEY for verified source fetching.",
            "GOPLUS_ENABLED=true only when you want real GoPlus provider calls.",
            "GOPLUS_ACCESS_TOKEN only if your GoPlus plan requires Authorization.",
            "GITHUB_API_TOKEN optional for rate limit/authorized repository access.",
        ],
        "safety_boundaries": {
            "no_fake_provider_data": True,
            "no_wallet_signing": True,
            "no_private_key_collection": True,
            "no_seed_phrase_collection": True,
            "no_exploit_automation": True,
            "not_certified_audit": True,
        },
    }
