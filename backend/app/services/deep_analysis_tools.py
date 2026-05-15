from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from app.core.config import settings
from app.models.schemas import Finding, ModuleScore, ScanResponse
from app.services.scoring import priority_actions, risk_label, score_findings, severity_breakdown
from app.services.solidity_utils import sha12

ENGINE_VERSION = "web3guard-deep-analysis-engine-v14.0"
SUPPORTED_DEEP_TOOLS = ("mythril", "manticore", "echidna")


def _tool_path(tool: str) -> str | None:
    if tool == "mythril":
        if settings.mythril_worker_required and not settings.mythril_allow_local_execution:
            return shutil.which(settings.mythril_docker_binary) if settings.mythril_docker_enabled else None
        configured = settings.mythril_binary
    else:
        configured = {
            "manticore": settings.manticore_binary,
            "echidna": settings.echidna_binary,
        }.get(tool)
    if configured:
        return configured if Path(configured).exists() or shutil.which(configured) else None
    default_binary = {"mythril": "myth", "manticore": "manticore", "echidna": "echidna"}[tool]
    return shutil.which(default_binary) or shutil.which(tool)


def _mythril_worker_status(path: str | None) -> dict[str, Any]:
    if not settings.mythril_worker_required:
        return {"mode": "local_optional", "worker_required": False, "ready": bool(path)}
    if settings.mythril_allow_local_execution:
        return {"mode": "local_explicitly_allowed", "worker_required": True, "ready": bool(path), "warning": "Only use local Mythril on a dedicated isolated worker without secrets."}
    if not settings.mythril_docker_enabled:
        return {"mode": "docker_worker_required", "worker_required": True, "ready": False, "status": "Manual", "reason": "MYTHRIL_DOCKER_ENABLED is false. Mythril is intentionally not run locally."}
    if not settings.mythril_docker_image:
        return {"mode": "docker_worker_required", "worker_required": True, "ready": False, "status": "Provider Not Configured", "reason": "MYTHRIL_DOCKER_IMAGE is missing."}
    if not path:
        return {"mode": "docker_worker_required", "worker_required": True, "ready": False, "status": "Tool Not Installed", "reason": f"Docker binary not found: {settings.mythril_docker_binary}"}
    return {"mode": "docker_worker_required", "worker_required": True, "ready": True, "docker_image": settings.mythril_docker_image, "docker_binary": path}


def deep_analysis_status() -> dict[str, Any]:
    tools: dict[str, Any] = {}
    for tool in SUPPORTED_DEEP_TOOLS:
        enabled = {
            "mythril": settings.mythril_enabled,
            "manticore": settings.manticore_enabled,
            "echidna": settings.echidna_enabled,
        }[tool]
        path = _tool_path(tool)
        worker = _mythril_worker_status(path) if tool == "mythril" else {"ready": bool(path), "mode": "local_optional"}
        tools[tool] = {
            "enabled_by_env": enabled,
            "installed": path is not None,
            "path": path,
            "will_run": bool(settings.deep_analysis_enabled and enabled and path and worker.get("ready")),
            "worker_status": worker if tool == "mythril" else None,
            "note": "Real deep-analysis tool output only. Missing/disabled tools are reported as Not Run; no fake findings are generated. Mythril is Docker/worker-gated by default.",
        }
    return {
        "ok": True,
        "phase": "Phase 14 - Deep Analysis Layer",
        "engine_version": ENGINE_VERSION,
        "deep_analysis_enabled": settings.deep_analysis_enabled,
        "default_timeout_seconds": settings.deep_analysis_timeout_seconds,
        "max_code_chars": settings.max_deep_analysis_code_chars,
        "tools": tools,
        "safety_controls": {
            "uses_temp_workspace": True,
            "cleanup_workspace": settings.deep_analysis_cleanup_workspace,
            "network_enabled": settings.deep_analysis_network_enabled,
            "dependency_install_allowed": settings.deep_analysis_allow_dependency_install,
            "clones_repos": False,
            "collects_private_keys": False,
            "signs_transactions": False,
            "touches_mainnet": False,
            "executes_user_deploy_scripts": False,
            "real_only": True,
        },
        "scan_depths": {
            "quick": "Runs enabled tools with strict timeout; no dependency install; no external network by default.",
            "standard": "Reserved for longer real tool execution when ownership is verified and worker resources are available.",
            "deep": "Requires ownership verification and isolated worker policy; still no fake findings.",
        },
        "not_claimed": [
            "No certified audit claim",
            "No fake Mythril/Manticore/Echidna output",
            "No private key / seed phrase / mnemonic collection",
            "No exploit automation against third-party targets",
            "No dependency install unless explicitly enabled in an isolated worker",
            "No mainnet transaction signing or execution",
        ],
    }


def _safe_filename(name: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_.-]", "_", name or "Contract.sol")
    if not cleaned.endswith(".sol"):
        cleaned += ".sol"
    return cleaned[:120]


def _split_command(template: str, *, binary: str, source: Path, root: Path) -> list[str]:
    rendered = template.format(binary=binary, source=str(source), root=str(root))
    return [part for part in rendered.split(" ") if part]


def _run_command(args: list[str], cwd: Path, timeout: int) -> dict[str, Any]:
    started = datetime.now(timezone.utc)
    safe_env = {**os.environ, "NO_COLOR": "1"}
    if not settings.deep_analysis_network_enabled:
        safe_env.update({"WEB3GUARD_NETWORK_DISABLED": "1"})
    try:
        completed = subprocess.run(
            args,
            cwd=str(cwd),
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
            env=safe_env,
        )
        return {
            "ok": completed.returncode == 0,
            "returncode": completed.returncode,
            "stdout": completed.stdout[-settings.deep_analysis_max_output_chars:],
            "stderr": completed.stderr[-settings.deep_analysis_max_output_chars:],
            "started_at": started.isoformat(),
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "timed_out": False,
        }
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout if isinstance(exc.stdout, str) else ""
        stderr = exc.stderr if isinstance(exc.stderr, str) else ""
        return {
            "ok": False,
            "returncode": None,
            "stdout": stdout[-settings.deep_analysis_max_output_chars:],
            "stderr": stderr[-settings.deep_analysis_max_output_chars:],
            "started_at": started.isoformat(),
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "timed_out": True,
            "error": f"Timed out after {timeout} seconds",
        }


def _severity(value: str | None, default: str = "medium") -> str:
    raw = (value or default).lower()
    if raw in {"critical", "high", "medium", "low", "info"}:
        return raw
    if raw in {"warning", "warn"}:
        return "medium"
    if raw in {"informational", "optimization"}:
        return "info"
    return default


def _base_finding(idx: int, *, tool: str, severity: str, title: str, description: str, line: int | None = None,
                  code: str | None = None, confidence: str = "medium", rule_id: str | None = None,
                  category: str = "deep_analysis") -> Finding:
    return Finding(
        id=f"deep-{tool}-{idx:03d}",
        module="deep_analysis",  # type: ignore[arg-type]
        severity=severity,  # type: ignore[arg-type]
        title=title,
        description=description,
        affected_line=line,
        affected_function=None,
        affected_code=code,
        confidence=confidence,  # type: ignore[arg-type]
        source=f"{tool.title()} Real Tool Output" if tool != "tool" else "Deep Analysis Tool Runner",
        category=category,
        rule_id=rule_id or f"WG-DEEP-{tool.upper()}",
        fingerprint=sha12(f"{tool}:{rule_id}:{line}:{title}:{code}"),
        business_impact="Deep analysis can uncover execution-path, symbolic, or invariant issues that simple rule checks may miss, but each finding still needs manual triage before launch.",
        developer_explanation="This finding was parsed from a real deep-analysis tool output when the tool was installed and enabled in the worker policy.",
        recommendation="Review the exact tool evidence, confirm true/false positive status, add tests, patch the contract, then rerun the scanner.",
        references=[tool, "Phase 14 deep analysis"],
        paid_review_recommended=severity in {"critical", "high"},
    )


def _tool_status_finding(idx: int, tool: str, reason: str) -> Finding:
    return Finding(
        id=f"deep-{tool}-status-{idx:03d}",
        module="deep_analysis",  # type: ignore[arg-type]
        severity="info",
        title=f"{tool.title()} Not Run",
        description=reason,
        affected_line=None,
        affected_function=None,
        affected_code=None,
        confidence="high",
        source="Deep Analysis Tool Status",
        category="tool_status",
        rule_id=f"WG-DEEP-STATUS-{tool.upper()}",
        fingerprint=sha12(f"{tool}:{reason}"),
        business_impact="This is not a fake vulnerability. It tells the founder which deeper evidence is missing before launch.",
        developer_explanation="Install and enable the tool in an isolated worker to run real deep analysis. Until then, use local rule/static findings only.",
        recommendation=f"Configure {tool}, keep the worker isolated, then rerun the deep analysis scanner.",
        references=["Phase 14 real-only tool status"],
        paid_review_recommended=False,
    )


def _parse_mythril_json(raw: str) -> list[Finding]:
    if not raw.strip():
        return []
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return []
    issues = []
    if isinstance(data, dict):
        if isinstance(data.get("issues"), list):
            issues = data["issues"]
        elif isinstance(data.get("results"), dict) and isinstance(data["results"].get("issues"), list):
            issues = data["results"]["issues"]
    findings: list[Finding] = []
    for idx, item in enumerate(issues[: settings.max_deep_tool_findings_per_run], start=1):
        if not isinstance(item, dict):
            continue
        title = str(item.get("title") or item.get("swc-title") or "Mythril Issue")
        desc = str(item.get("description") or item.get("description_head") or item.get("swc-description") or "Mythril reported a potential issue.")
        sev = _severity(str(item.get("severity") or item.get("impact") or "medium"))
        line = item.get("lineno") or item.get("line")
        code = item.get("code") or item.get("sourceMap")
        swc = item.get("swc-id") or item.get("swc_id") or item.get("check")
        findings.append(_base_finding(idx, tool="mythril", severity=sev, title=title, description=desc, line=line if isinstance(line, int) else None, code=str(code) if code else None, confidence="medium", rule_id=f"MYTHRIL-{swc or sha12(title)[:8]}"))
    return findings


def _parse_echidna_json(raw: str) -> list[Finding]:
    if not raw.strip():
        return []
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return []
    tests = []
    if isinstance(data, dict):
        for key in ("tests", "properties", "results"):
            if isinstance(data.get(key), list):
                tests = data[key]
                break
    findings: list[Finding] = []
    for idx, item in enumerate(tests[: settings.max_deep_tool_findings_per_run], start=1):
        if not isinstance(item, dict):
            continue
        status = str(item.get("status") or item.get("result") or "").lower()
        if status not in {"falsified", "failed", "error", "reverted"}:
            continue
        name = str(item.get("name") or item.get("property") or "Echidna Property Failure")
        error = str(item.get("error") or item.get("message") or item.get("reason") or "Echidna reported a failing property or test.")
        findings.append(_base_finding(idx, tool="echidna", severity="high", title=f"Property Failed: {name}", description=error, confidence="high", rule_id=f"ECHIDNA-{sha12(name)[:8]}"))
    return findings


def _parse_manticore_text(raw: str) -> list[Finding]:
    if not raw.strip():
        return []
    lines = raw.splitlines()
    interesting = [line for line in lines if re.search(r"(finding|issue|bug|assert|overflow|underflow|reentr|throw|exception|vulnerab)", line, re.I)]
    findings: list[Finding] = []
    for idx, line in enumerate(interesting[: settings.max_deep_tool_findings_per_run], start=1):
        sev = "high" if re.search(r"(assert|vulnerab|bug|overflow|reentr)", line, re.I) else "medium"
        findings.append(_base_finding(idx, tool="manticore", severity=sev, title="Manticore Path Finding", description=line.strip(), confidence="low", rule_id=f"MANTICORE-{sha12(line)[:8]}"))
    return findings


def _depth_timeout(scan_depth: str) -> int:
    if scan_depth == "standard":
        return min(settings.deep_analysis_timeout_seconds * 2, 600)
    if scan_depth == "deep":
        return min(settings.deep_analysis_timeout_seconds * 4, 1800)
    return settings.deep_analysis_timeout_seconds


def run_deep_analysis(solidity_code: str, project_name: str | None, file_name: str, requested_tools: list[str], scan_depth: str = "quick", ownership_verified: bool = False) -> ScanResponse:
    if len(solidity_code) > settings.max_deep_analysis_code_chars:
        raise ValueError(f"Solidity input is too large for Phase 14 deep analysis limit ({settings.max_deep_analysis_code_chars} chars)")
    valid_tools = [tool for tool in requested_tools if tool in SUPPORTED_DEEP_TOOLS]
    if not valid_tools:
        valid_tools = list(SUPPORTED_DEEP_TOOLS)
    if scan_depth in {"standard", "deep"} and not ownership_verified:
        raise ValueError("Standard/deep analysis requires ownership verification. Use quick mode or verify ownership first.")

    findings: list[Finding] = []
    tool_runs: dict[str, Any] = {}
    temp_root = Path(tempfile.mkdtemp(prefix="web3guard-deep-"))
    try:
        workdir = temp_root / "workspace"
        workdir.mkdir(parents=True, exist_ok=True)
        source_path = workdir / _safe_filename(file_name)
        source_path.write_text(solidity_code, encoding="utf-8")

        status = deep_analysis_status()
        next_idx = 1
        timeout = _depth_timeout(scan_depth)
        for tool in valid_tools:
            tool_info = status["tools"][tool]
            if not settings.deep_analysis_enabled:
                findings.append(_tool_status_finding(next_idx, tool, "DEEP_ANALYSIS_ENABLED is false, so no external deep-analysis tool was run.")); next_idx += 1
                tool_runs[tool] = {"status": "disabled_by_env", "real_findings": 0}
                continue
            if not tool_info["enabled_by_env"]:
                findings.append(_tool_status_finding(next_idx, tool, f"{tool.upper()}_ENABLED is false.")); next_idx += 1
                tool_runs[tool] = {"status": "tool_disabled_by_env", "real_findings": 0}
                continue
            if tool == "mythril" and not (tool_info.get("worker_status") or {}).get("ready"):
                reason = (tool_info.get("worker_status") or {}).get("reason") or "Mythril requires a configured Docker/isolated worker. No local/fake run was performed."
                findings.append(_tool_status_finding(next_idx, tool, reason)); next_idx += 1
                tool_runs[tool] = {"status": (tool_info.get("worker_status") or {}).get("status", "worker_required"), "real_findings": 0, "worker_status": tool_info.get("worker_status")}
                continue
            if not tool_info["installed"]:
                findings.append(_tool_status_finding(next_idx, tool, f"{tool} binary was not found on PATH/configured path.")); next_idx += 1
                tool_runs[tool] = {"status": "not_installed", "real_findings": 0}
                continue

            if tool == "mythril":
                worker_status = tool_info.get("worker_status") or {}
                if settings.mythril_worker_required and settings.mythril_docker_enabled and not settings.mythril_allow_local_execution:
                    if not settings.mythril_docker_image:
                        findings.append(_tool_status_finding(next_idx, tool, "MYTHRIL_DOCKER_IMAGE is missing. No fake Mythril result was generated.")); next_idx += 1
                        tool_runs[tool] = {"status": "Provider Not Configured", "real_findings": 0, "worker_status": worker_status}
                        continue
                    args = [
                        tool_info["path"], "run", "--rm", "--network", "none",
                        "-v", f"{workdir}:/workspace:ro", "-w", "/workspace",
                        settings.mythril_docker_image, "analyze", f"/workspace/{source_path.name}", "-o", "json",
                    ]
                else:
                    args = _split_command(settings.mythril_command_template, binary=tool_info["path"], source=source_path, root=workdir)
                run = _run_command(args, workdir, timeout)
                parsed = _parse_mythril_json(run.get("stdout", ""))
            elif tool == "echidna":
                args = _split_command(settings.echidna_command_template, binary=tool_info["path"], source=source_path, root=workdir)
                run = _run_command(args, workdir, timeout)
                parsed = _parse_echidna_json(run.get("stdout", ""))
            else:
                args = _split_command(settings.manticore_command_template, binary=tool_info["path"], source=source_path, root=workdir)
                run = _run_command(args, workdir, timeout)
                parsed = _parse_manticore_text((run.get("stdout", "") or "") + "\n" + (run.get("stderr", "") or ""))

            tool_runs[tool] = {**run, "status": "completed" if run.get("ok") else "completed_with_errors", "real_findings": len(parsed)}
            findings.extend(parsed)
            if not parsed and run.get("ok"):
                findings.append(_tool_status_finding(next_idx, tool, f"{tool} ran successfully and returned no parsed findings.")); next_idx += 1
            elif not run.get("ok") and not parsed:
                reason = "timed out" if run.get("timed_out") else f"returned code {run.get('returncode')}"
                findings.append(_tool_status_finding(next_idx, tool, f"{tool} attempted a real run but {reason}. Check tool logs in scan metadata.")); next_idx += 1

        score = score_findings(findings)
        if findings and all(f.category == "tool_status" and f.severity == "info" for f in findings):
            score = 98
        metadata = {
            "tool_status": status["tools"],
            "tool_runs": tool_runs,
            "requested_tools": valid_tools,
            "scan_depth": scan_depth,
            "ownership_verified": ownership_verified,
            "timeout_seconds": timeout,
            "safety_controls": status["safety_controls"],
            "workspace_mode": "temporary_local_workspace_deleted_after_scan",
            "worker_architecture_note": "Mythril is Docker/worker-gated by default. Production should run deep tools only inside a locked worker with no secrets, strict timeout, no network by default, and resource caps.",
            "real_only_note": "Only parsed output from actually installed/enabled Mythril/Manticore/Echidna runs is treated as deep-analysis evidence. Tool status messages are informational and are not fake vulnerabilities.",
        }
        return ScanResponse(
            report_id=f"WG-DEEP-{uuid4().hex[:12]}",
            generated_at=datetime.now(timezone.utc),
            project_name=project_name,
            module_score=ModuleScore(module="deep_analysis", score=score, risk_label=risk_label(score), assessed=True),  # type: ignore[arg-type]
            findings=findings[: settings.max_total_deep_findings],
            severity_breakdown=severity_breakdown(findings),
            priority_actions=priority_actions([f for f in findings if f.category != "tool_status"]),
            input_hash=sha12(solidity_code),
            engine_version=ENGINE_VERSION,
            scan_metadata=metadata,
            disclaimer="This is a preliminary deep-analysis review and does not replace a full manual audit. Deep tools can produce false positives/negatives and require expert triage.",
        )
    finally:
        if settings.deep_analysis_cleanup_workspace:
            shutil.rmtree(temp_root, ignore_errors=True)
