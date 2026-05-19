from __future__ import annotations

import os
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.core.config import settings

WORKER_EXECUTION_VERSION = "web3guard-real-worker-execution-v27.0"
SUPPORTED_WORKER_TOOLS = ("slither", "aderyn", "semgrep", "foundry", "echidna", "mythril")
_SECRET_HINTS = (
    "SECRET",
    "TOKEN",
    "PASSWORD",
    "PRIVATE",
    "MNEMONIC",
    "SEED",
    "KEY",
    "RAZORPAY",
    "SUPABASE",
    "OPENAI",
    "ANTHROPIC",
)


def _configured_binary(tool: str) -> str | None:
    return {
        "slither": settings.slither_binary,
        "aderyn": settings.aderyn_binary,
        "semgrep": settings.semgrep_binary,
        "foundry": settings.foundry_binary,
        "echidna": settings.echidna_binary,
        "mythril": settings.mythril_docker_binary if settings.mythril_worker_required and not settings.mythril_allow_local_execution else settings.mythril_binary,
    }.get(tool)


def _default_binary(tool: str) -> str:
    return {
        "slither": "slither",
        "aderyn": "aderyn",
        "semgrep": "semgrep",
        "foundry": "forge",
        "echidna": "echidna",
        "mythril": "docker" if settings.mythril_worker_required and not settings.mythril_allow_local_execution else "myth",
    }[tool]


def _resolve_binary(tool: str) -> str | None:
    configured = _configured_binary(tool)
    if configured:
        configured_path = Path(configured)
        if configured_path.exists():
            return str(configured_path)
        return shutil.which(configured)
    return shutil.which(_default_binary(tool))


def _group_enabled(tool: str) -> bool:
    if tool in {"slither", "aderyn", "semgrep"}:
        return bool(settings.static_analysis_enabled)
    if tool in {"echidna", "mythril"}:
        return bool(settings.deep_analysis_enabled)
    if tool == "foundry":
        return bool(settings.worker_execution_enabled)
    return False


def _tool_enabled(tool: str) -> bool:
    return {
        "slither": bool(settings.slither_enabled),
        "aderyn": bool(settings.aderyn_enabled),
        "semgrep": bool(settings.semgrep_enabled),
        "foundry": bool(settings.foundry_enabled),
        "echidna": bool(settings.echidna_enabled),
        "mythril": bool(settings.mythril_enabled),
    }[tool]


def _tool_category(tool: str) -> str:
    if tool in {"slither", "aderyn", "semgrep"}:
        return "static_worker"
    if tool == "foundry":
        return "test_worker"
    return "deep_worker"


def _tool_title(tool: str) -> str:
    return {
        "slither": "Slither static worker",
        "aderyn": "Aderyn static worker",
        "semgrep": "Semgrep rules worker",
        "foundry": "Foundry test runner",
        "echidna": "Echidna fuzz worker",
        "mythril": "Mythril Docker worker",
    }[tool]


def _tool_purpose(tool: str) -> str:
    return {
        "slither": "Parse real Slither JSON output from uploaded Solidity source.",
        "aderyn": "Parse real Aderyn JSON output from uploaded Solidity workspace.",
        "semgrep": "Run local Web3Guard Semgrep Solidity rules and parse JSON matches.",
        "foundry": "Run founder-owned Foundry tests inside an isolated worker when configured.",
        "echidna": "Run founder-owned Echidna property/fuzz tests inside an isolated worker when configured.",
        "mythril": "Run Mythril only through Docker/isolated worker policy by default.",
    }[tool]


def _command_template(tool: str) -> str:
    if tool == "slither":
        return "{binary} <Contract.sol> --json <slither.json> --disable-color"
    if tool == "aderyn":
        return settings.aderyn_command_template
    if tool == "semgrep":
        return "{binary} --config app/data/semgrep/solidity_security.yml --json --no-git-ignore <workspace>"
    if tool == "foundry":
        return "{binary} test --json"
    if tool == "echidna":
        return settings.echidna_command_template
    if tool == "mythril":
        if settings.mythril_worker_required and settings.mythril_docker_enabled and not settings.mythril_allow_local_execution:
            return "{docker} run --rm --network none -v <workspace>:/workspace:ro -w /workspace <MYTHRIL_DOCKER_IMAGE> analyze /workspace/Contract.sol -o json"
        return settings.mythril_command_template
    return "Manual / Not Assessed"


def _status_label(tool: str, installed: bool) -> str:
    if not _group_enabled(tool):
        return "Provider Not Configured"
    if not _tool_enabled(tool):
        return "Provider Not Configured"
    if tool == "mythril":
        if settings.mythril_worker_required and not settings.mythril_allow_local_execution:
            if not settings.mythril_docker_enabled:
                return "Manual"
            if not settings.mythril_docker_image:
                return "Provider Not Configured"
    if not installed:
        return "Tool Not Installed"
    return "Ready"


def _next_action(tool: str, label: str) -> str:
    if label == "Ready":
        return "Run only with authorized code in an isolated worker; persist raw logs as evidence."
    if label == "Tool Not Installed":
        return f"Install {_default_binary(tool)} on the worker image or set the explicit binary path env."
    if label == "Provider Not Configured":
        if tool in {"slither", "aderyn", "semgrep"}:
            return "Set STATIC_ANALYSIS_ENABLED=true and the tool-specific *_ENABLED flag only after worker isolation is ready."
        if tool == "foundry":
            return "Set WORKER_EXECUTION_ENABLED=true and FOUNDRY_ENABLED=true only on the worker runtime."
        if tool == "mythril":
            return "Configure DEEP_ANALYSIS_ENABLED=true, MYTHRIL_ENABLED=true, MYTHRIL_DOCKER_ENABLED=true, and MYTHRIL_DOCKER_IMAGE."
        return "Set DEEP_ANALYSIS_ENABLED=true and the tool-specific *_ENABLED flag only after worker isolation is ready."
    return "Keep this item Manual / Not Assessed until a safe worker policy is configured."


def _version_args(tool: str, binary: str) -> list[str]:
    if tool == "mythril" and settings.mythril_worker_required and not settings.mythril_allow_local_execution:
        return [binary, "--version"]
    return [binary, "--version"]


def _safe_probe_env() -> dict[str, str]:
    safe: dict[str, str] = {}
    keep = {"PATH", "SystemRoot", "WINDIR", "HOME", "USERPROFILE", "TMP", "TEMP", "LANG", "LC_ALL"}
    for key, value in os.environ.items():
        key_upper = key.upper()
        if key in keep and not any(hint in key_upper for hint in _SECRET_HINTS):
            safe[key] = value
    safe["NO_COLOR"] = "1"
    safe["WEB3GUARD_WORKER_PROBE_ONLY"] = "1"
    return safe


def _run_probe(tool: str, binary: str) -> dict[str, Any]:
    started = datetime.now(timezone.utc)
    try:
        completed = subprocess.run(
            _version_args(tool, binary),
            cwd=str(Path.cwd()),
            text=True,
            capture_output=True,
            timeout=settings.worker_probe_timeout_seconds,
            check=False,
            env=_safe_probe_env(),
        )
        return {
            "tool": tool,
            "status": "completed" if completed.returncode == 0 else "completed_with_errors",
            "returncode": completed.returncode,
            "stdout": completed.stdout[-settings.worker_probe_max_output_chars:],
            "stderr": completed.stderr[-settings.worker_probe_max_output_chars:],
            "started_at": started.isoformat(),
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "timed_out": False,
            "probe_only": True,
        }
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout if isinstance(exc.stdout, str) else ""
        stderr = exc.stderr if isinstance(exc.stderr, str) else ""
        return {
            "tool": tool,
            "status": "timeout",
            "returncode": None,
            "stdout": stdout[-settings.worker_probe_max_output_chars:],
            "stderr": stderr[-settings.worker_probe_max_output_chars:],
            "started_at": started.isoformat(),
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "timed_out": True,
            "probe_only": True,
        }


def _tool_status(tool: str) -> dict[str, Any]:
    path = _resolve_binary(tool)
    installed = path is not None
    status = _status_label(tool, installed)
    return {
        "key": tool,
        "name": _tool_title(tool),
        "category": _tool_category(tool),
        "purpose": _tool_purpose(tool),
        "status": status,
        "installed": installed,
        "path": path,
        "group_enabled": _group_enabled(tool),
        "enabled_by_env": _tool_enabled(tool),
        "will_run": status == "Ready",
        "binary_default": _default_binary(tool),
        "command_template": _command_template(tool),
        "next_action": _next_action(tool, status),
        "real_only_note": "This item is treated as evidence only when the binary is actually installed, enabled, and returns real output. Missing tools remain status-only.",
    }


def worker_execution_status() -> dict[str, Any]:
    tools = [_tool_status(tool) for tool in SUPPORTED_WORKER_TOOLS]
    ready_count = sum(1 for tool in tools if tool["status"] == "Ready")
    return {
        "ok": True,
        "version": WORKER_EXECUTION_VERSION,
        "worker_execution_enabled": settings.worker_execution_enabled,
        "ready_count": ready_count,
        "total_count": len(tools),
        "readiness_label": "Worker probes ready" if ready_count else "Worker execution not configured",
        "tools": tools,
        "phase_27_scope": [
            "Slither real worker",
            "Aderyn real worker",
            "Semgrep real rules",
            "Foundry runner readiness",
            "Echidna fuzzing readiness",
            "Mythril Docker/worker readiness",
        ],
        "safety_boundaries": {
            "no_fake_tool_output": True,
            "probe_only_endpoint": True,
            "no_dependency_install": True,
            "no_repo_clone": True,
            "no_wallet_signing": True,
            "no_private_key_collection": True,
            "no_exploit_automation": True,
            "not_certified_audit": True,
            "isolated_runtime_recommended": settings.worker_require_isolated_runtime,
        },
        "production_notes": [
            "Do not run long tool jobs inside the Vercel frontend process.",
            "Render web dynos can expose cold-start/timeouts; use a separate worker service for long scans.",
            "Keep uploaded code in a temporary workspace and delete it after execution unless the user explicitly saves a report.",
            "Never inject env secrets into subprocesses; worker probes use a stripped environment.",
        ],
    }


def worker_execution_plan(project_type: str | None = None, requested_tools: list[str] | None = None) -> dict[str, Any]:
    selected = [tool for tool in (requested_tools or list(SUPPORTED_WORKER_TOOLS)) if tool in SUPPORTED_WORKER_TOOLS]
    if not selected:
        selected = list(SUPPORTED_WORKER_TOOLS)
    status_by_key = {tool["key"]: tool for tool in worker_execution_status()["tools"]}
    steps = []
    for order, tool in enumerate(selected, start=1):
        item = status_by_key[tool]
        steps.append({
            "order": order,
            "tool": tool,
            "status": item["status"],
            "command_template": item["command_template"],
            "evidence_policy": "Store raw stdout/stderr, return code, started/completed timestamps, parser version, and input hash only. Do not invent findings.",
            "when_missing": "Show Tool Not Installed / Provider Not Configured / Manual / Not Assessed instead of fake output.",
            "next_action": item["next_action"],
        })
    return {
        "ok": True,
        "version": WORKER_EXECUTION_VERSION,
        "project_type": project_type or "founder-owned Solidity/project workspace",
        "requested_tools": selected,
        "steps": steps,
        "queue_design": {
            "api_layer": "FastAPI validates authorization, real-only acknowledgement, size limits, and creates a worker job.",
            "worker_layer": "Isolated process/container runs one tool with strict timeout, no secrets, no wallet signing, and no dependency install by default.",
            "result_layer": "Parser stores real output metadata and parsed findings; status-only entries stay informational.",
        },
        "blocked_actions": [
            "No fake scanner output",
            "No exploit automation",
            "No private key / seed phrase / mnemonic collection",
            "No wallet signing",
            "No automatic dependency install on user code",
            "No unauthorized active scanning",
        ],
    }


def probe_worker_tools(requested_tools: list[str] | None = None) -> dict[str, Any]:
    if not settings.worker_allow_version_probe:
        return {
            "ok": True,
            "version": WORKER_EXECUTION_VERSION,
            "probe_status": "Manual / Not Assessed",
            "results": {},
            "note": "WORKER_ALLOW_VERSION_PROBE is false. No subprocess probe was executed.",
        }
    selected = [tool for tool in (requested_tools or list(SUPPORTED_WORKER_TOOLS)) if tool in SUPPORTED_WORKER_TOOLS]
    if not selected:
        selected = list(SUPPORTED_WORKER_TOOLS)
    status_by_key = {tool["key"]: tool for tool in worker_execution_status()["tools"]}
    results: dict[str, Any] = {}
    for tool in selected:
        item = status_by_key[tool]
        if item["status"] != "Ready" or not item.get("path"):
            results[tool] = {
                "tool": tool,
                "status": item["status"],
                "probe_only": True,
                "real_findings": 0,
                "reason": item["next_action"],
            }
            continue
        results[tool] = _run_probe(tool, item["path"])
    return {
        "ok": True,
        "version": WORKER_EXECUTION_VERSION,
        "probe_status": "completed",
        "results": results,
        "real_only_note": "This endpoint only probes installed tool versions. It does not analyze code, generate findings, clone repos, install dependencies, or sign transactions.",
    }
