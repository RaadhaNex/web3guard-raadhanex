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

ENGINE_VERSION = "web3guard-static-analysis-engine-v13.0"
SUPPORTED_TOOLS = ("slither", "aderyn", "semgrep")

SEMGRP_RULE_DIR = Path(__file__).resolve().parents[1] / "data" / "semgrep"
SEMGRP_RULE_FILE = SEMGRP_RULE_DIR / "solidity_security.yml"


def _bool(value: bool) -> bool:
    return bool(value)


def _tool_path(tool: str) -> str | None:
    configured = {
        "slither": settings.slither_binary,
        "aderyn": settings.aderyn_binary,
        "semgrep": settings.semgrep_binary,
    }.get(tool)
    if configured:
        return configured if Path(configured).exists() or shutil.which(configured) else None
    return shutil.which(tool)


def static_analysis_status() -> dict[str, Any]:
    tools: dict[str, Any] = {}
    for tool in SUPPORTED_TOOLS:
        path = _tool_path(tool)
        enabled = {
            "slither": settings.slither_enabled,
            "aderyn": settings.aderyn_enabled,
            "semgrep": settings.semgrep_enabled,
        }[tool]
        tools[tool] = {
            "enabled_by_env": enabled,
            "installed": path is not None,
            "path": path,
            "will_run": bool(settings.static_analysis_enabled and enabled and path),
            "note": "Real subprocess tool output only. If disabled or not installed, no fake findings are generated; status becomes Tool Not Installed / Provider Not Configured.",
        }
    return {
        "ok": True,
        "phase": "Mega Final Patch H - Real Static Analysis Engine",
        "integration_level": "actual subprocess execution when tool is installed/enabled",
        "not_regex_only": True,
        "engine_version": ENGINE_VERSION,
        "static_analysis_enabled": settings.static_analysis_enabled,
        "default_timeout_seconds": settings.audit_tool_timeout_seconds,
        "max_code_chars": settings.max_static_analysis_code_chars,
        "tools": tools,
        "safety_controls": {
            "executes_contract_code": False,
            "installs_dependencies": False,
            "clones_repos": False,
            "collects_private_keys": False,
            "uses_temp_workspace": True,
            "real_only": True,
        },
        "not_claimed": [
            "No certified audit claim",
            "No fake Slither/Aderyn/Semgrep output",
            "No dependency install or npm/pip execution",
            "No private key / seed phrase / mnemonic collection",
            "No exploit automation or destructive testing",
        ],
    }


def _safe_filename(name: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_.-]", "_", name or "Contract.sol")
    if not cleaned.endswith(".sol"):
        cleaned += ".sol"
    return cleaned[:120]


def _base_finding(idx: int, *, tool: str, severity: str, title: str, description: str, code: str | None = None,
                  line: int | None = None, confidence: str = "medium", rule_id: str | None = None,
                  category: str = "static_analysis") -> Finding:
    return Finding(
        id=f"static-{tool}-{idx:03d}",
        module="static_analysis",  # type: ignore[arg-type]
        severity=severity,  # type: ignore[arg-type]
        title=title,
        description=description,
        affected_line=line,
        affected_function=None,
        affected_code=code,
        confidence=confidence,  # type: ignore[arg-type]
        source=f"{tool.title()} Real Tool Output" if tool != "tool" else "Static Analysis Tool Runner",
        category=category,
        rule_id=rule_id or f"WG-STATIC-{tool.upper()}",
        fingerprint=sha12(f"{tool}:{rule_id}:{line}:{title}:{code}"),
        business_impact="Static analyzers can uncover issues missed by simple pattern checks, but results still require manual triage before launch.",
        developer_explanation="This finding was parsed from a real static-analysis tool output when the tool was installed and enabled.",
        recommendation="Review the underlying tool evidence, confirm true/false positive status, then patch and rerun the scanner.",
        references=[tool],
        paid_review_recommended=severity in {"critical", "high"},
    )


def _run_command(args: list[str], cwd: Path, timeout: int) -> dict[str, Any]:
    started = datetime.now(timezone.utc)
    try:
        completed = subprocess.run(
            args,
            cwd=str(cwd),
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
            env={**os.environ, "NO_COLOR": "1"},
        )
        return {
            "ok": completed.returncode == 0,
            "returncode": completed.returncode,
            "stdout": completed.stdout[-settings.audit_tool_max_output_chars:],
            "stderr": completed.stderr[-settings.audit_tool_max_output_chars:],
            "started_at": started.isoformat(),
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "timed_out": False,
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "ok": False,
            "returncode": None,
            "stdout": (exc.stdout or "")[-settings.audit_tool_max_output_chars:] if isinstance(exc.stdout, str) else "",
            "stderr": (exc.stderr or "")[-settings.audit_tool_max_output_chars:] if isinstance(exc.stderr, str) else "",
            "started_at": started.isoformat(),
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "timed_out": True,
            "error": f"Timed out after {timeout} seconds",
        }


def _parse_slither_json(path: Path) -> list[Finding]:
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8", errors="replace") or "{}")
    detectors = data.get("results", {}).get("detectors", []) if isinstance(data, dict) else []
    findings: list[Finding] = []
    for idx, item in enumerate(detectors[: settings.max_tool_findings_per_run], start=1):
        impact = str(item.get("impact") or "informational").lower()
        severity = {"high": "high", "medium": "medium", "low": "low", "informational": "info", "optimization": "info"}.get(impact, "medium")
        elements = item.get("elements") or []
        first = elements[0] if elements else {}
        source_mapping = first.get("source_mapping", {}) if isinstance(first, dict) else {}
        line = None
        if isinstance(source_mapping, dict):
            lines = source_mapping.get("lines") or []
            line = lines[0] if lines else None
        check = str(item.get("check") or "slither-detector")
        description = str(item.get("description") or item.get("markdown") or "Slither reported a potential issue.")
        findings.append(_base_finding(idx, tool="slither", severity=severity, title=check.replace("-", " ").title(), description=description, line=line, confidence="high", rule_id=f"SLITHER-{check}"))
    return findings


def _parse_semgrep_json(raw: str) -> list[Finding]:
    if not raw.strip():
        return []
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return []
    results = data.get("results", []) if isinstance(data, dict) else []
    findings: list[Finding] = []
    for idx, item in enumerate(results[: settings.max_tool_findings_per_run], start=1):
        extra = item.get("extra") or {}
        metadata = extra.get("metadata") or {}
        raw_sev = str(extra.get("severity") or metadata.get("severity") or "WARNING").upper()
        severity = {"ERROR": "high", "WARNING": "medium", "INFO": "info"}.get(raw_sev, "medium")
        start = item.get("start") or {}
        line = start.get("line") if isinstance(start, dict) else None
        code = extra.get("lines")
        rule_id = str(item.get("check_id") or "semgrep-rule")
        message = str(extra.get("message") or "Semgrep reported a pattern match.")
        findings.append(_base_finding(idx, tool="semgrep", severity=severity, title=rule_id.split(".")[-1].replace("-", " ").title(), description=message, code=code, line=line, confidence="medium", rule_id=f"SEMGREP-{rule_id}"))
    return findings


def _parse_aderyn_json(path: Path) -> list[Finding]:
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8", errors="replace") or "{}")
    except json.JSONDecodeError:
        return []
    findings: list[Finding] = []
    candidates: list[Any] = []
    if isinstance(data, dict):
        for key in ("issues", "results", "detectors", "findings"):
            if isinstance(data.get(key), list):
                candidates = data[key]
                break
        if not candidates and isinstance(data.get("report"), dict):
            for key in ("issues", "results", "detectors", "findings"):
                if isinstance(data["report"].get(key), list):
                    candidates = data["report"][key]
                    break
    for idx, item in enumerate(candidates[: settings.max_tool_findings_per_run], start=1):
        if not isinstance(item, dict):
            continue
        title = str(item.get("title") or item.get("name") or item.get("check") or "Aderyn Finding")
        desc = str(item.get("description") or item.get("message") or item.get("body") or "Aderyn reported a potential issue.")
        sev_raw = str(item.get("severity") or item.get("impact") or "medium").lower()
        severity = {"critical": "critical", "high": "high", "medium": "medium", "low": "low", "info": "info", "informational": "info"}.get(sev_raw, "medium")
        line = item.get("line") or item.get("line_number")
        findings.append(_base_finding(idx, tool="aderyn", severity=severity, title=title, description=desc, line=line if isinstance(line, int) else None, confidence="medium", rule_id=f"ADERYN-{sha12(title)[:8]}"))
    return findings


def _tool_disabled_finding(idx: int, tool: str, reason: str) -> Finding:
    return Finding(
        id=f"static-{tool}-status-{idx:03d}",
        module="static_analysis",  # type: ignore[arg-type]
        severity="info",
        title=f"{tool.title()} Not Run",
        description=reason,
        affected_line=None,
        affected_function=None,
        affected_code=None,
        confidence="high",
        source="Static Analysis Tool Status",
        category="tool_status",
        rule_id=f"WG-STATIC-STATUS-{tool.upper()}",
        fingerprint=sha12(f"{tool}:{reason}"),
        business_impact="This does not create a fake vulnerability score; it tells the founder which real tool evidence is missing.",
        developer_explanation="Install and enable the tool to run real static analysis. Until then, only local rule-engine/checklist findings are available.",
        recommendation=f"Install/configure {tool} and set the related environment flags, then rerun the static analysis scanner.",
        references=["Phase 13 real-only tool status"],
        paid_review_recommended=False,
    )


def run_static_analysis(solidity_code: str, project_name: str | None, file_name: str, requested_tools: list[str]) -> ScanResponse:
    if len(solidity_code) > settings.max_static_analysis_code_chars:
        raise ValueError(f"Solidity input is too large for Phase 13 static analysis limit ({settings.max_static_analysis_code_chars} chars)")
    valid_tools = [tool for tool in requested_tools if tool in SUPPORTED_TOOLS]
    if not valid_tools:
        valid_tools = list(SUPPORTED_TOOLS)

    findings: list[Finding] = []
    tool_runs: dict[str, Any] = {}
    temp_root = Path(tempfile.mkdtemp(prefix="web3guard-static-"))
    try:
        workdir = temp_root / "workspace"
        workdir.mkdir(parents=True, exist_ok=True)
        source_path = workdir / _safe_filename(file_name)
        source_path.write_text(solidity_code, encoding="utf-8")

        status = static_analysis_status()
        next_idx = 1
        for tool in valid_tools:
            tool_info = status["tools"][tool]
            if not settings.static_analysis_enabled:
                findings.append(_tool_disabled_finding(next_idx, tool, "STATIC_ANALYSIS_ENABLED is false, so no external tool was run.")); next_idx += 1
                tool_runs[tool] = {"status": "disabled_by_env", "real_findings": 0}
                continue
            if not tool_info["enabled_by_env"]:
                findings.append(_tool_disabled_finding(next_idx, tool, f"{tool.upper()}_ENABLED is false.")); next_idx += 1
                tool_runs[tool] = {"status": "tool_disabled_by_env", "real_findings": 0}
                continue
            if not tool_info["installed"]:
                findings.append(_tool_disabled_finding(next_idx, tool, f"{tool} binary was not found on PATH/configured path.")); next_idx += 1
                tool_runs[tool] = {"status": "not_installed", "real_findings": 0}
                continue

            if tool == "slither":
                out = workdir / "slither.json"
                args = [tool_info["path"], str(source_path), "--json", str(out), "--disable-color"]
                run = _run_command(args, workdir, settings.audit_tool_timeout_seconds)
                parsed = _parse_slither_json(out)
            elif tool == "semgrep":
                args = [tool_info["path"], "--config", str(SEMGRP_RULE_FILE), "--json", "--no-git-ignore", str(workdir)]
                run = _run_command(args, workdir, settings.audit_tool_timeout_seconds)
                parsed = _parse_semgrep_json(run.get("stdout", ""))
            else:
                out = workdir / "aderyn.json"
                template = settings.aderyn_command_template
                args = [part for part in template.format(binary=tool_info["path"], root=str(workdir), output=str(out)).split(" ") if part]
                run = _run_command(args, workdir, settings.audit_tool_timeout_seconds)
                parsed = _parse_aderyn_json(out)

            tool_runs[tool] = {**run, "status": "completed" if run.get("ok") else "completed_with_errors", "real_findings": len(parsed)}
            findings.extend(parsed)
            if not parsed and run.get("ok"):
                findings.append(_tool_disabled_finding(next_idx, tool, f"{tool} ran successfully and returned no parsed findings.")); next_idx += 1
            elif not run.get("ok") and not parsed:
                reason = "timed out" if run.get("timed_out") else f"returned code {run.get('returncode')}"
                findings.append(_tool_disabled_finding(next_idx, tool, f"{tool} attempted a real run but {reason}. Check tool logs in scan metadata.")); next_idx += 1

        # If only tool status info findings exist, keep a high score but mark evidence limited.
        score = score_findings(findings)
        if findings and all(f.category == "tool_status" and f.severity == "info" for f in findings):
            score = 98
        metadata = {
            "tool_status": status["tools"],
            "tool_runs": tool_runs,
            "requested_tools": valid_tools,
            "safety_controls": status["safety_controls"],
            "workspace_mode": "temporary_local_workspace_deleted_after_scan",
            "real_only_note": "Only parsed output from actually installed/enabled tools is treated as tool evidence. Tool status messages are informational and are not fake vulnerabilities.",
        }
        return ScanResponse(
            report_id=f"WG-STATIC-{uuid4().hex[:12]}",
            generated_at=datetime.now(timezone.utc),
            project_name=project_name,
            module_score=ModuleScore(module="static_analysis", score=score, risk_label=risk_label(score), assessed=True),  # type: ignore[arg-type]
            findings=findings[: settings.max_total_static_findings],
            severity_breakdown=severity_breakdown(findings),
            priority_actions=priority_actions([f for f in findings if f.category != "tool_status"]),
            input_hash=sha12(solidity_code),
            engine_version=ENGINE_VERSION,
            scan_metadata=metadata,
        )
    finally:
        if settings.audit_tool_cleanup_workspace:
            shutil.rmtree(temp_root, ignore_errors=True)
