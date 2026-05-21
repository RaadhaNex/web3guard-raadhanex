from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from app.core.config import settings
from app.services import professional_direct_level_k as direct_level
from app.services import professional_final_stabilization_l as final_l
from app.services import professional_monitoring_j as monitoring
from app.services import professional_ops_n_to_s as ops

REAL_ONLY_NOTE = (
    "Phase T is a real setup assistant only. It does not enable unsafe tools, does not claim certified audit status, "
    "does not request private keys or seed phrases, and does not run exploit automation. Missing tools/providers remain "
    "Not Assessed / Provider Not Configured / Tool Not Installed."
)


def _bool(name: str, default: bool = False) -> bool:
    return bool(getattr(settings, name, default))


def _text(name: str, default: str | None = None) -> str | None:
    value = getattr(settings, name, default)
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _mask_secret(value: Any) -> str | None:
    if value is None or value == "":
        return None
    text = str(value)
    if len(text) <= 8:
        return "configured"
    return f"{text[:4]}…{text[-4:]}"


def _tool_installed(binary: str | None) -> bool:
    if not binary:
        return False
    return bool(shutil.which(binary)) or Path(str(binary)).exists()


def _check(key: str, label: str, configured: bool, required: bool = True, current: Any = None, fix: str = "") -> dict[str, Any]:
    if configured:
        state = "Ready"
    elif required:
        state = "Missing"
    else:
        state = "Optional"
    return {
        "key": key,
        "label": label,
        "required": required,
        "configured": bool(configured),
        "state": state,
        "current": current if configured else None,
        "fix": fix,
    }


def _worker_runner_enabled() -> bool:
    # Phase T supports both names because the product docs often say PROFESSIONAL_WORKER_ENABLED,
    # while the Phase N-S runner originally used PROFESSIONAL_WORKER_RUNNER_ENABLED.
    return _bool("professional_worker_runner_enabled") or _bool("professional_worker_enabled")


def _env_snippets() -> dict[str, str]:
    backend = """FRONTEND_ORIGIN=https://web3guard-raadhanex.vercel.app
FRONTEND_URL=https://web3guard-raadhanex.vercel.app
BACKEND_URL=https://web3guard-raadhanex-backend.onrender.com
ADMIN_TOKEN=<generate-strong-secret>
PUBLIC_PROOF_SIGNING_SECRET=<generate-strong-secret>
GITHUB_WEBHOOK_SECRET=<generate-strong-secret>
ONCHAIN_WEBHOOK_SECRET=<generate-strong-secret>
PROFESSIONAL_DIRECT_LEVEL_NETWORK_ENABLED=false
PROFESSIONAL_WORKER_ENABLED=false
PROFESSIONAL_WORKER_RUNNER_ENABLED=false
WORKER_EXECUTION_ENABLED=false"""
    frontend = """NEXT_PUBLIC_API_BASE_URL=https://web3guard-raadhanex-backend.onrender.com
NEXT_PUBLIC_APP_URL=https://web3guard-raadhanex.vercel.app"""
    worker_off = """PROFESSIONAL_WORKER_ENABLED=false
PROFESSIONAL_WORKER_RUNNER_ENABLED=false
WORKER_EXECUTION_ENABLED=false
FOUNDRY_ENABLED=false
ECHIDNA_ENABLED=false"""
    worker_on_only_after_isolation = """# Use these only on a separate isolated worker service, not on the main public API service.
PROFESSIONAL_WORKER_SERVICE_ROLE=isolated_worker
PROFESSIONAL_WORKER_ISOLATED_RUNTIME_CONFIRMED=true
PROFESSIONAL_WORKER_ENABLED=true
PROFESSIONAL_WORKER_RUNNER_ENABLED=true
WORKER_EXECUTION_ENABLED=true
PROFESSIONAL_WORKER_ALLOW_LOCAL_EXECUTION=true
PROFESSIONAL_WORKER_NETWORK_ENABLED=false
PROFESSIONAL_WORKER_CLEANUP_WORKSPACE=true
FOUNDRY_ENABLED=true
FOUNDRY_BINARY=forge
ECHIDNA_ENABLED=true
ECHIDNA_BINARY=echidna"""
    return {
        "backend_render_minimum": backend,
        "frontend_vercel_minimum": frontend,
        "safe_worker_default_off": worker_off,
        "safe_worker_on_after_isolated_runtime": worker_on_only_after_isolation,
    }


def env_checklist() -> dict[str, Any]:
    backend_url = _text("backend_url", "")
    frontend_origin = _text("frontend_origin", "")
    checks = [
        _check("BACKEND_URL", "Backend public URL", bool(backend_url and not backend_url.startswith("http://localhost")), True, backend_url, "Set BACKEND_URL to your Render backend URL."),
        _check("FRONTEND_ORIGIN", "Frontend public origin", bool(frontend_origin and not frontend_origin.startswith("http://localhost")), True, frontend_origin, "Set FRONTEND_ORIGIN to your Vercel URL."),
        _check("ADMIN_TOKEN", "Admin token", bool(_text("admin_token") and _text("admin_token") != "change-this-admin-token"), True, _mask_secret(_text("admin_token")), "Generate a strong ADMIN_TOKEN."),
        _check("PUBLIC_PROOF_SIGNING_SECRET", "Proof signing secret", bool(_text("public_proof_signing_secret")), True, _mask_secret(_text("public_proof_signing_secret")), "Set a strong PUBLIC_PROOF_SIGNING_SECRET before public proof reports."),
        _check("GITHUB_WEBHOOK_SECRET", "GitHub webhook secret", bool(_text("github_webhook_secret")), True, _mask_secret(_text("github_webhook_secret")), "Set GitHub webhook secret and use same value in GitHub webhook settings."),
        _check("ONCHAIN_WEBHOOK_SECRET", "On-chain webhook secret", bool(_text("onchain_webhook_secret")), True, _mask_secret(_text("onchain_webhook_secret")), "Set on-chain provider webhook secret."),
        _check("ETHERSCAN_API_KEY", "Explorer source API key", bool(_text("etherscan_api_key") or _text("polygonscan_api_key") or _text("bscscan_api_key") or _text("basescan_api_key")), False, "configured", "Set at least ETHERSCAN_API_KEY for verified contract source scans."),
        _check("GITHUB_API_TOKEN", "GitHub API token", bool(_text("github_api_token")), False, _mask_secret(_text("github_api_token")), "Optional but recommended to avoid GitHub rate limits."),
        _check("STATIC_ANALYSIS_ENABLED", "Static tools globally enabled", _bool("static_analysis_enabled"), False, _bool("static_analysis_enabled"), "Enable only after Slither/Semgrep/Aderyn install is confirmed."),
        _check("PROFESSIONAL_DIRECT_LEVEL_NETWORK_ENABLED", "Live snapshot network", _bool("professional_direct_level_network_enabled"), False, _bool("professional_direct_level_network_enabled"), "Keep false until you intentionally enable live passive snapshots."),
    ]
    ready_required = [item for item in checks if item["required"]]
    missing_required = [item for item in ready_required if not item["configured"]]
    return {
        "ok": True,
        "phase": "T",
        "name": "Real Setup Assistant Checklist",
        "required_ready": len(missing_required) == 0,
        "missing_required_count": len(missing_required),
        "ready_count": len([item for item in checks if item["configured"]]),
        "checks": checks,
        "snippets": _env_snippets(),
        "real_only_note": REAL_ONLY_NOTE,
    }


def webhook_readiness() -> dict[str, Any]:
    github = ops.github_webhook_setup_status()
    onchain = ops.onchain_webhook_setup_status()
    return {
        "ok": True,
        "phase": "T",
        "github": {
            "configured": github.get("configured"),
            "webhook_url": github.get("webhook_url"),
            "events_seen": len(github.get("recent_events", []) or []),
            "setup_steps": github.get("setup_steps", []),
        },
        "onchain": {
            "configured": onchain.get("configured"),
            "webhook_url": onchain.get("webhook_url"),
            "events_seen": len(onchain.get("recent_events", []) or []),
            "setup_steps": onchain.get("setup_steps", []),
        },
        "real_only_note": "Webhook readiness means setup evidence exists. It is not a certified audit or safety guarantee.",
    }


def worker_enablement_gate() -> dict[str, Any]:
    foundry_binary = _text("foundry_binary") or shutil.which("forge")
    echidna_binary = _text("echidna_binary") or shutil.which("echidna")
    foundry_installed = _tool_installed(foundry_binary)
    echidna_installed = _tool_installed(echidna_binary)
    service_role = (_text("professional_worker_service_role", "api") or "api").lower()
    isolated_confirmed = _bool("professional_worker_isolated_runtime_confirmed")
    local_execution = _bool("professional_worker_allow_local_execution")
    cleanup = _bool("professional_worker_cleanup_workspace", True)
    network_enabled = _bool("professional_worker_network_enabled")
    timeout = int(getattr(settings, "professional_worker_timeout_seconds", 90))
    runner_enabled = _worker_runner_enabled()
    old_worker_enabled = _bool("worker_execution_enabled")
    foundry_enabled = _bool("foundry_enabled")
    echidna_enabled = _bool("echidna_enabled")

    blockers: list[str] = []
    warnings: list[str] = []
    if service_role != "isolated_worker":
        blockers.append("PROFESSIONAL_WORKER_SERVICE_ROLE must be isolated_worker before enabling real local execution.")
    if not isolated_confirmed:
        blockers.append("PROFESSIONAL_WORKER_ISOLATED_RUNTIME_CONFIRMED must be true after separate sandbox/worker isolation is verified.")
    if not local_execution:
        blockers.append("PROFESSIONAL_WORKER_ALLOW_LOCAL_EXECUTION must be true only inside the isolated worker service.")
    if not cleanup:
        blockers.append("PROFESSIONAL_WORKER_CLEANUP_WORKSPACE should stay true to remove temporary user code workspaces.")
    if timeout > 180:
        warnings.append("Worker timeout is high; keep PROFESSIONAL_WORKER_TIMEOUT_SECONDS <= 180 for first production rollout.")
    if network_enabled:
        warnings.append("PROFESSIONAL_WORKER_NETWORK_ENABLED is true. Keep it false unless dependency/network access is intentionally sandboxed.")
    if foundry_enabled and not foundry_installed:
        blockers.append("FOUNDRY_ENABLED is true but forge was not found from FOUNDRY_BINARY/PATH.")
    if echidna_enabled and not echidna_installed:
        blockers.append("ECHIDNA_ENABLED is true but echidna was not found from ECHIDNA_BINARY/PATH.")
    if not foundry_enabled and not echidna_enabled:
        warnings.append("Neither Foundry nor Echidna is enabled. Runner can be enabled later, but no tool will run now.")

    safe_to_turn_true = len(blockers) == 0 and (foundry_enabled or echidna_enabled) and (foundry_installed or echidna_installed)
    return {
        "ok": True,
        "phase": "T",
        "name": "Safe Worker Enablement Gate",
        "safe_to_turn_true": safe_to_turn_true,
        "currently_enabled": {
            "PROFESSIONAL_WORKER_ENABLED": _bool("professional_worker_enabled"),
            "PROFESSIONAL_WORKER_RUNNER_ENABLED": _bool("professional_worker_runner_enabled"),
            "WORKER_EXECUTION_ENABLED": old_worker_enabled,
            "effective_professional_runner_enabled": runner_enabled,
        },
        "required_before_true": [
            "Separate isolated worker service/runtime, not main public API server.",
            "No private keys, seed phrases, mnemonics, or wallet signing in inputs.",
            "Temporary workspace cleanup enabled.",
            "Strict timeout/output/code-size limits.",
            "Foundry/Echidna binaries installed and version checked.",
            "Network disabled unless intentionally sandboxed.",
        ],
        "tool_status": {
            "foundry": {"enabled": foundry_enabled, "binary": foundry_binary, "installed": foundry_installed, "state": "Ready" if foundry_enabled and foundry_installed else "Tool Not Installed" if foundry_enabled else "Provider Not Configured"},
            "echidna": {"enabled": echidna_enabled, "binary": echidna_binary, "installed": echidna_installed, "state": "Ready" if echidna_enabled and echidna_installed else "Tool Not Installed" if echidna_enabled else "Provider Not Configured"},
        },
        "blockers": blockers,
        "warnings": warnings,
        "recommended_default": _env_snippets()["safe_worker_default_off"],
        "enable_only_after_ready": _env_snippets()["safe_worker_on_after_isolated_runtime"],
        "answer_to_user_env_question": {
            "PROFESSIONAL_WORKER_ENABLED": "Set true only after worker gate is green. Phase T supports it as alias for PROFESSIONAL_WORKER_RUNNER_ENABLED.",
            "WORKER_EXECUTION_ENABLED": "Set true only on the isolated worker service if you also want the older worker/probe layer enabled. Keep false on main API.",
            "FOUNDRY_BINARY=forge": "Correct only when forge is installed and available in PATH inside the worker service.",
            "ECHIDNA_BINARY=echidna": "Correct only when echidna is installed and available in PATH inside the worker service.",
        },
        "real_only_note": REAL_ONLY_NOTE,
    }


def production_readiness() -> dict[str, Any]:
    env = env_checklist()
    worker = worker_enablement_gate()
    webhooks = webhook_readiness()
    final_gate = final_l.production_gate()
    direct_gate = direct_level.direct_competition_readiness_gate()
    monitoring_ready = monitoring.readiness()
    blockers: list[str] = []
    warnings: list[str] = []
    if not env.get("required_ready"):
        blockers.append("required_env_missing")
    if not webhooks.get("github", {}).get("configured"):
        warnings.append("github_webhook_secret_missing_or_not_configured")
    if not webhooks.get("onchain", {}).get("configured"):
        warnings.append("onchain_webhook_secret_or_provider_missing")
    if worker.get("currently_enabled", {}).get("effective_professional_runner_enabled") and not worker.get("safe_to_turn_true"):
        blockers.append("worker_enabled_before_safe_gate")
    if final_gate.get("production_ready") is False:
        warnings.extend(final_gate.get("blockers", [])[:8])

    score = 100
    score -= len(blockers) * 20
    score -= len(warnings) * 5
    score = max(0, min(100, score))
    return {
        "ok": True,
        "phase": "T",
        "name": "Production Readiness Dashboard",
        "readiness_score": score,
        "production_ready_for_public_beta": len(blockers) == 0,
        "certified_audit_claim_allowed": False,
        "direct_competition_public_claim_allowed": False,
        "blockers": blockers,
        "warnings": warnings,
        "env": {"required_ready": env.get("required_ready"), "missing_required_count": env.get("missing_required_count")},
        "webhooks": webhooks,
        "worker_gate": worker,
        "final_stabilization_gate": final_gate,
        "direct_level_gate": direct_gate,
        "monitoring_readiness": monitoring_ready,
        "next_actions": manual_actions()["actions"],
        "real_only_note": REAL_ONLY_NOTE,
    }


def manual_actions() -> dict[str, Any]:
    return {
        "ok": True,
        "phase": "T",
        "actions": [
            {"order": 1, "title": "Add Render backend env", "owner": "user", "path": "Render → Backend service → Environment", "done_signal": "GET /professional-setup/env-checklist shows required_ready true."},
            {"order": 2, "title": "Add Vercel frontend env", "owner": "user", "path": "Vercel → Project Settings → Environment Variables", "done_signal": "Frontend can call backend without localhost."},
            {"order": 3, "title": "Create GitHub webhook", "owner": "user", "path": "Repo Settings → Webhooks", "done_signal": "/professional-setup/webhooks shows github events_seen > 0."},
            {"order": 4, "title": "Create on-chain provider webhook", "owner": "user", "path": "Alchemy/Tenderly/Defender provider", "done_signal": "/professional-setup/webhooks shows onchain configured/events."},
            {"order": 5, "title": "Keep worker disabled on main API", "owner": "user", "path": "Render main API env", "done_signal": "Worker gate shows disabled or safe_to_turn_true false without runtime risk."},
            {"order": 6, "title": "Create separate isolated worker service", "owner": "user + developer", "path": "Separate Render/Docker service", "done_signal": "Worker gate safe_to_turn_true true after binaries and isolation are confirmed."},
            {"order": 7, "title": "Run real pilot scans", "owner": "user", "path": "Scanner + reviewer workflow + proof report", "done_signal": "Proof report, monitoring baseline, and client delivery exist."},
        ],
        "real_only_note": REAL_ONLY_NOTE,
    }


def phase_status() -> dict[str, Any]:
    env = env_checklist()
    readiness = production_readiness()
    worker = worker_enablement_gate()
    return {
        "ok": True,
        "phase": "T",
        "name": "Real Setup Assistant + Production Readiness Dashboard",
        "modules": {
            "env_checklist": True,
            "webhook_readiness": True,
            "safe_worker_enablement_gate": True,
            "production_readiness_dashboard": True,
            "manual_action_plan": True,
        },
        "required_env_ready": env.get("required_ready"),
        "readiness_score": readiness.get("readiness_score"),
        "worker_safe_to_enable": worker.get("safe_to_turn_true"),
        "certified_audit_claim_allowed": False,
        "direct_competition_public_claim_allowed": False,
        "real_only_note": REAL_ONLY_NOTE,
    }
