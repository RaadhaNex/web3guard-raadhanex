from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

ENGINE_VERSION = "web3guard-isolated-static-worker-v1.1-stdlib-asgi"
SUPPORTED_TOOLS = ("slither", "semgrep", "aderyn")
SAFE_EXTENSIONS = {
    ".sol",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".mjs",
    ".cjs",
    ".py",
    ".yml",
    ".yaml",
    ".json",
    ".toml",
    ".env.example",
}
SOLIDITY_EXTENSIONS = {".sol"}
RULE_DIR = Path(__file__).resolve().parent / "rules"
RULE_FILE = RULE_DIR / "solidity_security.yml"
WEB_RULE_FILE = RULE_DIR / "web_security.yml"
PRIVATE_KEY_PATTERNS = [
    re.compile(r"\bprivate[_-]?key\b\s*[:=]", re.I),
    re.compile(r"\bmnemonic\b\s*[:=]", re.I),
    re.compile(r"\bseed\s+phrase\b\s*[:=]", re.I),
]
SECRET_ENV_HINTS = ("SECRET", "TOKEN", "PASSWORD", "PRIVATE", "MNEMONIC", "SEED", "OPENAI", "ANTHROPIC", "SUPABASE")


@dataclass(frozen=True)
class Settings:
    app_env: str = "development"
    static_analysis_enabled: bool = False
    static_worker_token: str | None = None
    professional_worker_service_role: str = "api"
    professional_worker_isolated_runtime_confirmed: bool = False
    professional_worker_allow_local_execution: bool = False
    professional_worker_network_enabled: bool = False
    static_worker_cleanup_workspace: bool = True
    static_worker_timeout_seconds: int = 75
    static_worker_max_output_chars: int = 16000
    static_worker_max_total_chars: int = 180000
    static_worker_max_files: int = 12
    slither_enabled: bool = True
    slither_binary: str = "slither"
    semgrep_enabled: bool = True
    semgrep_binary: str = "semgrep"
    aderyn_enabled: bool = False
    aderyn_binary: str = "aderyn"
    aderyn_command_template: str = "{binary} --root {root} --output {output}"


def _env_bool(key: str, default: bool = False) -> bool:
    raw = os.getenv(key)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "y", "on"}


def _env_int(key: str, default: int) -> int:
    raw = os.getenv(key)
    if raw is None:
        return default
    try:
        return int(raw)
    except (TypeError, ValueError):
        return default


def _settings() -> Settings:
    return Settings(
        app_env=os.getenv("APP_ENV", "development"),
        static_analysis_enabled=_env_bool("STATIC_ANALYSIS_ENABLED", False),
        static_worker_token=os.getenv("STATIC_WORKER_TOKEN"),
        professional_worker_service_role=os.getenv("PROFESSIONAL_WORKER_SERVICE_ROLE", "api"),
        professional_worker_isolated_runtime_confirmed=_env_bool("PROFESSIONAL_WORKER_ISOLATED_RUNTIME_CONFIRMED", False),
        professional_worker_allow_local_execution=_env_bool("PROFESSIONAL_WORKER_ALLOW_LOCAL_EXECUTION", False),
        professional_worker_network_enabled=_env_bool("PROFESSIONAL_WORKER_NETWORK_ENABLED", False),
        static_worker_cleanup_workspace=_env_bool("STATIC_WORKER_CLEANUP_WORKSPACE", True),
        static_worker_timeout_seconds=_env_int("STATIC_WORKER_TIMEOUT_SECONDS", 75),
        static_worker_max_output_chars=_env_int("STATIC_WORKER_MAX_OUTPUT_CHARS", 16000),
        static_worker_max_total_chars=_env_int("STATIC_WORKER_MAX_TOTAL_CHARS", 180000),
        static_worker_max_files=_env_int("STATIC_WORKER_MAX_FILES", 12),
        slither_enabled=_env_bool("SLITHER_ENABLED", True),
        slither_binary=os.getenv("SLITHER_BINARY", "slither"),
        semgrep_enabled=_env_bool("SEMGREP_ENABLED", True),
        semgrep_binary=os.getenv("SEMGREP_BINARY", "semgrep"),
        aderyn_enabled=_env_bool("ADERYN_ENABLED", False),
        aderyn_binary=os.getenv("ADERYN_BINARY", "aderyn"),
        aderyn_command_template=os.getenv("ADERYN_COMMAND_TEMPLATE", "{binary} --root {root} --output {output}"),
    )


settings = _settings()


class WorkerHttpError(Exception):
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, default=str).encode("utf-8")).hexdigest()


def _tool_path(tool: str) -> str | None:
    configured = {
        "slither": settings.slither_binary,
        "semgrep": settings.semgrep_binary,
        "aderyn": settings.aderyn_binary,
    }[tool]
    if configured and (Path(configured).exists() or shutil.which(configured)):
        return configured
    return shutil.which(tool)


def _tool_enabled(tool: str) -> bool:
    return bool({"slither": settings.slither_enabled, "semgrep": settings.semgrep_enabled, "aderyn": settings.aderyn_enabled}[tool])


def _worker_safe_to_execute() -> bool:
    return bool(
        settings.static_analysis_enabled
        and settings.professional_worker_service_role == "isolated_worker"
        and settings.professional_worker_isolated_runtime_confirmed
        and settings.professional_worker_allow_local_execution
    )


def _tool_status() -> dict[str, Any]:
    safe = _worker_safe_to_execute()
    tools: dict[str, Any] = {}
    for tool in SUPPORTED_TOOLS:
        path = _tool_path(tool)
        enabled = _tool_enabled(tool)
        tools[tool] = {
            "enabled_by_env": enabled,
            "installed": path is not None,
            "path": path,
            "will_run": bool(safe and enabled and path),
            "state": "Ready" if safe and enabled and path else ("Provider Not Configured" if not safe or not enabled else "Tool Not Installed"),
        }
    return tools


def _auth(authorization: str | None) -> None:
    expected = settings.static_worker_token
    if not expected:
        raise WorkerHttpError(503, "STATIC_WORKER_TOKEN is not configured on worker.")
    if authorization != f"Bearer {expected}":
        raise WorkerHttpError(401, "Worker token rejected.")


def _safe_env() -> dict[str, str]:
    keep = {"PATH", "SystemRoot", "WINDIR", "HOME", "USERPROFILE", "TMP", "TEMP", "LANG", "LC_ALL"}
    safe = {key: value for key, value in os.environ.items() if key in keep and not any(h in key.upper() for h in SECRET_ENV_HINTS)}
    safe["NO_COLOR"] = "1"
    safe["WEB3GUARD_ISOLATED_WORKER"] = "1"
    if not settings.professional_worker_network_enabled:
        safe["FOUNDRY_DISABLE_NIGHTLY_WARNING"] = "1"
    return safe


def _sanitize_path(raw: str, fallback: str) -> Path:
    clean = (raw or fallback).replace("\\", "/").strip().lstrip("/")
    parts: list[str] = []
    for part in clean.split("/"):
        if not part or part in {".", ".."}:
            continue
        parts.append(re.sub(r"[^A-Za-z0-9_.-]", "_", part)[:100] or "file")
    if not parts:
        parts = [fallback]
    if not Path(parts[-1]).suffix:
        parts[-1] = f"{parts[-1]}.txt"
    return Path(*parts)


def _safe_source_files(raw_files: Any) -> list[dict[str, str]]:
    files = raw_files if isinstance(raw_files, list) else []
    clean: list[dict[str, str]] = []
    for item in files:
        if not isinstance(item, dict):
            continue
        path = item.get("path")
        content = item.get("content")
        if isinstance(path, str) and isinstance(content, str) and path.strip() and content.strip():
            clean.append({"path": path[:240], "content": content[:180000]})
    return clean


def _safe_tools(raw_tools: Any) -> list[str]:
    if not isinstance(raw_tools, list):
        return list(SUPPORTED_TOOLS)
    tools = [tool for tool in raw_tools if isinstance(tool, str) and tool in SUPPORTED_TOOLS]
    return tools or list(SUPPORTED_TOOLS)


def _sanitize_files(files: list[dict[str, str]]) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    cleaned: list[dict[str, str]] = []
    rejected: list[dict[str, str]] = []
    total = 0
    for idx, item in enumerate(files[: settings.static_worker_max_files + 8], start=1):
        path = item["path"].replace("\\", "/").lstrip("/")
        content = item["content"]
        suffix = Path(path).suffix.lower()
        if suffix not in SAFE_EXTENSIONS:
            rejected.append({"path": path, "reason": "Unsupported file type for isolated worker. Semgrep accepts web/config files; Slither/Aderyn require .sol."})
            continue
        if ".." in Path(path).parts or path.startswith("."):
            rejected.append({"path": path, "reason": "Unsafe path."})
            continue
        if any(pattern.search(content) for pattern in PRIVATE_KEY_PATTERNS):
            rejected.append({"path": path, "reason": "Potential private key/seed text detected."})
            continue
        total += len(content)
        if len(cleaned) >= settings.static_worker_max_files:
            rejected.append({"path": path, "reason": "File limit reached."})
            continue
        if total > settings.static_worker_max_total_chars:
            rejected.append({"path": path, "reason": "Total source size limit reached."})
            continue
        cleaned.append({"path": str(_sanitize_path(path, f"Source{idx}.txt")), "content": content})
    return cleaned, rejected


def _write_workspace(root: Path, files: list[dict[str, str]]) -> list[Path]:
    written: list[Path] = []
    for item in files:
        target = (root / item["path"]).resolve()
        if root not in target.parents and target != root:
            raise ValueError("Unsafe file path after normalization.")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(item["content"], encoding="utf-8")
        written.append(target)
    return written


def _run(args: list[str], cwd: Path) -> dict[str, Any]:
    started = _now_iso()
    try:
        completed = subprocess.run(
            args,
            cwd=str(cwd),
            text=True,
            capture_output=True,
            timeout=int(settings.static_worker_timeout_seconds),
            check=False,
            env=_safe_env(),
        )
        return {
            "status": "completed" if completed.returncode == 0 else "completed_with_errors",
            "ok": completed.returncode == 0,
            "returncode": completed.returncode,
            "stdout": (completed.stdout or "")[-settings.static_worker_max_output_chars :],
            "stderr": (completed.stderr or "")[-settings.static_worker_max_output_chars :],
            "started_at": started,
            "completed_at": _now_iso(),
            "timed_out": False,
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "status": "timeout",
            "ok": False,
            "returncode": None,
            "stdout": str(exc.stdout or "")[-settings.static_worker_max_output_chars :],
            "stderr": "Tool timed out.",
            "started_at": started,
            "completed_at": _now_iso(),
            "timed_out": True,
        }


def _base_finding(tool: str, idx: int, title: str, description: str, severity: str, *, file: str | None = None, line: int | None = None, rule_id: str | None = None, code: str | None = None) -> dict[str, Any]:
    severity = severity if severity in {"critical", "high", "medium", "low", "info"} else "medium"
    return {
        "id": f"worker-{tool}-{idx:03d}",
        "module": "static_analysis",
        "severity": severity,
        "title": title[:220],
        "description": description[:1800],
        "affected_file": file,
        "affected_line": line,
        "affected_code": code[:1200] if isinstance(code, str) else None,
        "evidence": (code or description)[:1600],
        "impact": "A real static-analysis tool reported a code-level issue that may affect launch readiness.",
        "fix": "Review the cited file/line, patch the code, add a regression test, and rerun the worker.",
        "source_tools": [tool],
        "source": f"Isolated {tool.title()} Worker Output",
        "category": "static_analysis",
        "rule_id": rule_id or f"WORKER-{tool.upper()}",
        "verification_status": "tool_detected_needs_triage",
        "confidence": "high" if tool == "slither" else "medium",
        "fingerprint": _sha({"tool": tool, "title": title, "file": file, "line": line, "rule_id": rule_id}),
        "business_impact": "Tool evidence improves pre-audit readiness, but a human reviewer should still confirm true/false-positive status.",
        "developer_explanation": "This finding was parsed from actual tool output inside the isolated worker service.",
        "recommendation": "Patch, test, rerun, then submit for human review if severity is high/critical.",
        "references": [tool],
    }


def _parse_slither(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8", errors="replace") or "{}")
    except json.JSONDecodeError:
        return []
    detectors = data.get("results", {}).get("detectors", []) if isinstance(data, dict) else []
    findings: list[dict[str, Any]] = []
    for idx, item in enumerate(detectors[:40], start=1):
        impact = str(item.get("impact") or "informational").lower()
        severity = {"high": "high", "medium": "medium", "low": "low", "informational": "info", "optimization": "info"}.get(impact, "medium")
        elements = item.get("elements") or []
        first = elements[0] if elements else {}
        mapping = first.get("source_mapping", {}) if isinstance(first, dict) else {}
        lines = mapping.get("lines") if isinstance(mapping, dict) else []
        line = lines[0] if isinstance(lines, list) and lines else None
        file = mapping.get("filename_relative") or mapping.get("filename_used") or mapping.get("filename") if isinstance(mapping, dict) else None
        check = str(item.get("check") or "slither-detector")
        desc = str(item.get("description") or item.get("markdown") or "Slither reported a potential issue.")
        findings.append(_base_finding("slither", idx, check.replace("-", " ").title(), desc, severity, file=file, line=line if isinstance(line, int) else None, rule_id=f"SLITHER-{check}"))
    return findings


def _parse_semgrep(raw: str) -> list[dict[str, Any]]:
    if not raw.strip():
        return []
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return []
    results = data.get("results", []) if isinstance(data, dict) else []
    findings: list[dict[str, Any]] = []
    for idx, item in enumerate(results[:40], start=1):
        extra = item.get("extra") or {}
        raw_sev = str(extra.get("severity") or "WARNING").upper()
        severity = {"ERROR": "high", "WARNING": "medium", "INFO": "info"}.get(raw_sev, "medium")
        start = item.get("start") or {}
        line = start.get("line") if isinstance(start, dict) else None
        rule_id = str(item.get("check_id") or "semgrep-rule")
        message = str(extra.get("message") or "Semgrep reported a pattern match.")
        findings.append(_base_finding("semgrep", idx, rule_id.split(".")[-1].replace("-", " ").title(), message, severity, file=item.get("path") if isinstance(item.get("path"), str) else None, line=line if isinstance(line, int) else None, rule_id=f"SEMGREP-{rule_id}", code=extra.get("lines")))
    return findings


def _parse_aderyn(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8", errors="replace") or "{}")
    except json.JSONDecodeError:
        return []
    candidates: list[Any] = []
    if isinstance(data, dict):
        for key in ("issues", "results", "detectors", "findings"):
            if isinstance(data.get(key), list):
                candidates = data[key]
                break
    findings: list[dict[str, Any]] = []
    for idx, item in enumerate(candidates[:40], start=1):
        if not isinstance(item, dict):
            continue
        title = str(item.get("title") or item.get("name") or item.get("check") or "Aderyn Finding")
        desc = str(item.get("description") or item.get("message") or item.get("body") or "Aderyn reported a potential issue.")
        sev = str(item.get("severity") or item.get("impact") or "medium").lower()
        severity = {"critical": "critical", "high": "high", "medium": "medium", "low": "low", "info": "info", "informational": "info"}.get(sev, "medium")
        loc = item.get("location") if isinstance(item.get("location"), dict) else {}
        file = item.get("path") or item.get("file") or loc.get("file") if isinstance(loc, dict) else None
        line = item.get("line") or loc.get("line") if isinstance(loc, dict) else item.get("line")
        findings.append(_base_finding("aderyn", idx, title, desc, severity, file=file if isinstance(file, str) else None, line=line if isinstance(line, int) else None, rule_id=f"ADERYN-{_sha(title)[:8]}"))
    return findings


def _run_tool(tool: str, workdir: Path, primary_source: Path, info: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    path = info.get("path")
    if not info.get("will_run") or not path:
        return {"status": "not_run", "real_findings": 0, "reason": info.get("state")}, []
    sol_files = list(workdir.rglob("*.sol"))
    if tool in {"slither", "aderyn"} and not sol_files:
        return {"status": "not_run", "real_findings": 0, "reason": "No Solidity .sol files were supplied. This tool is contract-only."}, []
    if tool == "slither":
        out = workdir / "slither.json"
        target = sol_files[0] if sol_files else primary_source
        run = _run([str(path), str(target), "--json", str(out), "--disable-color"], workdir)
        findings = _parse_slither(out)
    elif tool == "semgrep":
        rule_file = WEB_RULE_FILE if WEB_RULE_FILE.exists() else RULE_FILE
        run = _run([str(path), "--config", str(rule_file), "--json", "--no-git-ignore", str(workdir)], workdir)
        findings = _parse_semgrep(run.get("stdout") or "")
    else:
        out = workdir / "aderyn.json"
        cmd = [part for part in settings.aderyn_command_template.format(binary=str(path), root=str(workdir), output=str(out)).split(" ") if part]
        run = _run(cmd, workdir)
        findings = _parse_aderyn(out)
    run["real_findings"] = len(findings)
    return run, findings


def _health_payload() -> dict[str, Any]:
    return {
        "ok": True,
        "service": "web3guard-isolated-static-analysis-worker",
        "engine_version": ENGINE_VERSION,
        "static_analysis_enabled": bool(settings.static_analysis_enabled),
        "safe_to_execute": _worker_safe_to_execute(),
        "certified_audit": False,
    }


def _status_payload(authorization: str | None) -> dict[str, Any]:
    if settings.static_worker_token:
        _auth(authorization)
    return {
        "ok": True,
        "engine_version": ENGINE_VERSION,
        "safe_to_execute": _worker_safe_to_execute(),
        "static_analysis_enabled": bool(settings.static_analysis_enabled),
        "service_role": settings.professional_worker_service_role,
        "isolated_runtime_confirmed": bool(settings.professional_worker_isolated_runtime_confirmed),
        "allow_local_execution": bool(settings.professional_worker_allow_local_execution),
        "network_enabled": bool(settings.professional_worker_network_enabled),
        "tool_status": _tool_status(),
        "safety_controls": {
            "main_backend_executes_tools": False,
            "clones_repos": False,
            "installs_dependencies": False,
            "collects_private_keys": False,
            "wallet_signing": False,
            "exploit_automation": False,
            "temporary_workspace": True,
        },
        "not_claimed": ["Not a certified audit", "No 100% secure claim", "No fake tool output"],
    }


def _run_payload(payload: dict[str, Any], authorization: str | None) -> dict[str, Any]:
    _auth(authorization)
    if not payload.get("authorization_confirmed") or not payload.get("real_only_acknowledged", True):
        raise WorkerHttpError(400, "authorization_confirmed and real_only_acknowledged are required")
    if not _worker_safe_to_execute():
        return {
            "ok": True,
            "status": "Provider Not Configured",
            "engine_version": ENGINE_VERSION,
            "reason": "Worker safety env is not fully enabled. No tool was executed and no fake findings were generated.",
            "tool_status": _tool_status(),
            "tool_runs": {},
            "findings": [],
            "summary": {"real_findings_count": 0},
        }
    cleaned, rejected = _sanitize_files(_safe_source_files(payload.get("files")))
    tools = _safe_tools(payload.get("tools"))
    if not cleaned:
        return {
            "ok": True,
            "status": "Not Assessed",
            "engine_version": ENGINE_VERSION,
            "reason": "No safe source files supplied. Semgrep accepts web/config files; Slither/Aderyn require Solidity.",
            "rejected_files": rejected,
            "tool_status": _tool_status(),
            "tool_runs": {},
            "findings": [],
            "summary": {"real_findings_count": 0},
        }
    run_id = f"isw_{uuid4().hex[:12]}"
    workdir = Path(tempfile.mkdtemp(prefix="web3guard_static_worker_"))
    tool_status = _tool_status()
    tool_runs: dict[str, Any] = {}
    findings: list[dict[str, Any]] = []
    try:
        written = _write_workspace(workdir, cleaned)
        primary = written[0]
        for tool in tools:
            run_meta, parsed = _run_tool(tool, workdir, primary, tool_status[tool])
            tool_runs[tool] = run_meta
            findings.extend(parsed)
    finally:
        if settings.static_worker_cleanup_workspace:
            shutil.rmtree(workdir, ignore_errors=True)
    return {
        "ok": True,
        "status": "Assessed" if any(run.get("status") in {"completed", "completed_with_errors"} for run in tool_runs.values()) else "Not Assessed",
        "run_id": run_id,
        "engine_version": ENGINE_VERSION,
        "generated_at": _now_iso(),
        "source_label": str(payload.get("source_label") or "auto_discovered_source")[:120],
        "tool_status": tool_status,
        "tool_runs": tool_runs,
        "findings": findings,
        "rejected_files": rejected,
        "summary": {
            "files_written": [item["path"] for item in cleaned],
            "real_findings_count": len(findings),
            "tools_requested": tools,
            "tools_completed": [tool for tool, run in tool_runs.items() if run.get("status") in {"completed", "completed_with_errors"}],
        },
        "real_only_note": "Only actual Slither/Semgrep/Aderyn process output is returned. Semgrep can scan web/config files; Slither/Aderyn run only on Solidity. Not-run/missing tools are not converted into fake vulnerabilities.",
    }


async def _read_body(receive: Any) -> bytes:
    chunks: list[bytes] = []
    more = True
    while more:
        message = await receive()
        if message.get("type") != "http.request":
            continue
        chunks.append(message.get("body", b""))
        more = bool(message.get("more_body", False))
    return b"".join(chunks)


async def _send_json(send: Any, status_code: int, payload: dict[str, Any]) -> None:
    body = json.dumps(payload, ensure_ascii=False, default=str).encode("utf-8")
    await send(
        {
            "type": "http.response.start",
            "status": status_code,
            "headers": [
                (b"content-type", b"application/json; charset=utf-8"),
                (b"cache-control", b"no-store"),
            ],
        }
    )
    await send({"type": "http.response.body", "body": body})


def _header(headers: list[tuple[bytes, bytes]], name: str) -> str | None:
    key = name.lower().encode("latin-1")
    for raw_key, raw_value in headers:
        if raw_key.lower() == key:
            return raw_value.decode("latin-1")
    return None


async def app(scope: dict[str, Any], receive: Any, send: Any) -> None:
    if scope.get("type") != "http":
        await _send_json(send, 404, {"detail": "Unsupported scope."})
        return
    method = str(scope.get("method") or "GET").upper()
    path = str(scope.get("path") or "/")
    headers = scope.get("headers") or []
    authorization = _header(headers, "authorization")
    try:
        if method == "GET" and path == "/health":
            await _send_json(send, 200, _health_payload())
            return
        if method == "GET" and path == "/static-analysis/status":
            await _send_json(send, 200, _status_payload(authorization))
            return
        if method == "POST" and path == "/static-analysis/run":
            body = await _read_body(receive)
            try:
                payload = json.loads(body.decode("utf-8") or "{}")
            except json.JSONDecodeError:
                raise WorkerHttpError(400, "Invalid JSON payload.")
            if not isinstance(payload, dict):
                raise WorkerHttpError(400, "JSON object payload is required.")
            await _send_json(send, 200, _run_payload(payload, authorization))
            return
        await _send_json(send, 404, {"detail": "Not Found", "available_routes": ["GET /health", "GET /static-analysis/status", "POST /static-analysis/run"]})
    except WorkerHttpError as exc:
        await _send_json(send, exc.status_code, {"detail": exc.detail})
    except Exception as exc:  # defensive: never expose secrets, never fake output
        await _send_json(send, 500, {"detail": "Worker internal error", "error_type": type(exc).__name__})
