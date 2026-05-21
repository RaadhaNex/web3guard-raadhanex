from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any

import httpx

from app.core.config import settings
from app.models.schemas import Finding, ModuleScore, ScanResponse
from app.services.finding_normalizer import prepare_professional_findings
from app.services.scoring import priority_actions, risk_label, score_findings, severity_breakdown
from app.services.solidity_utils import sha12

ENGINE_VERSION = "web3guard-isolated-static-worker-bridge-v1.0"
SUPPORTED_TOOLS = ("slither", "semgrep", "aderyn")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _mask_url(url: str | None) -> str | None:
    if not url:
        return None
    clean = str(url).rstrip("/")
    return clean[:120]


def _hash_payload(value: Any) -> str:
    return hashlib.sha256(str(value).encode("utf-8", errors="ignore")).hexdigest()


def isolated_static_worker_status() -> dict[str, Any]:
    configured = bool(settings.static_worker_enabled and settings.static_worker_url and settings.static_worker_token)
    auto_dispatch = bool(configured and settings.static_worker_auto_dispatch_enabled)
    return {
        "ok": True,
        "engine_version": ENGINE_VERSION,
        "configured": configured,
        "enabled": bool(settings.static_worker_enabled),
        "auto_dispatch_enabled": bool(settings.static_worker_auto_dispatch_enabled),
        "will_auto_run": auto_dispatch,
        "worker_url_configured": bool(settings.static_worker_url),
        "worker_url_preview": _mask_url(settings.static_worker_url),
        "shared_token_configured": bool(settings.static_worker_token),
        "timeout_seconds": int(settings.static_worker_timeout_seconds),
        "max_files": int(settings.static_worker_max_files),
        "max_total_chars": int(settings.static_worker_max_total_chars),
        "main_backend_executes_tools": False,
        "real_only_note": "Main backend only sends safe source files to a separately deployed isolated worker. If the worker is missing/disabled, the result remains Not Assessed and no fake Slither/Semgrep/Aderyn findings are generated.",
        "required_main_backend_env": [
            "STATIC_WORKER_ENABLED=true",
            "STATIC_WORKER_AUTO_DISPATCH_ENABLED=true",
            "STATIC_WORKER_URL=https://your-worker.onrender.com",
            "STATIC_WORKER_TOKEN=<same strong secret as worker>",
        ],
        "required_worker_env": [
            "STATIC_ANALYSIS_ENABLED=true",
            "STATIC_WORKER_TOKEN=<same strong secret>",
            "PROFESSIONAL_WORKER_SERVICE_ROLE=isolated_worker",
            "PROFESSIONAL_WORKER_ISOLATED_RUNTIME_CONFIRMED=true",
            "PROFESSIONAL_WORKER_ALLOW_LOCAL_EXECUTION=true",
            "SLITHER_ENABLED=true",
            "SEMGREP_ENABLED=true",
            "ADERYN_ENABLED=true only after aderyn is installed",
        ],
    }


def _sanitize_source_files(source_files: list[dict[str, str]]) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    cleaned: list[dict[str, str]] = []
    rejected: list[dict[str, str]] = []
    total_chars = 0
    max_files = int(settings.static_worker_max_files)
    max_total_chars = int(settings.static_worker_max_total_chars)
    for item in source_files[: max_files + 8]:
        raw_path = str(item.get("path") or "Contract.sol").replace("\\", "/").strip().lstrip("/")
        content = str(item.get("content") or "")
        if not content.strip():
            rejected.append({"path": raw_path, "reason": "empty content"})
            continue
        if ".." in raw_path.split("/") or raw_path.startswith("."):
            rejected.append({"path": raw_path, "reason": "unsafe path"})
            continue
        if not raw_path.endswith(".sol"):
            rejected.append({"path": raw_path, "reason": "only Solidity .sol files are sent to the static-analysis worker in this phase"})
            continue
        total_chars += len(content)
        if len(cleaned) >= max_files:
            rejected.append({"path": raw_path, "reason": "file limit reached"})
            continue
        if total_chars > max_total_chars:
            rejected.append({"path": raw_path, "reason": "total source size limit reached"})
            continue
        cleaned.append({"path": raw_path[:240], "content": content})
    return cleaned, rejected


def _finding_from_worker(raw: dict[str, Any], idx: int) -> Finding:
    source_tools = raw.get("source_tools") if isinstance(raw.get("source_tools"), list) else []
    tool = str(source_tools[0] if source_tools else raw.get("tool") or "isolated_worker")[:60]
    severity = str(raw.get("severity") or "info").lower()
    if severity not in {"critical", "high", "medium", "low", "info"}:
        severity = "medium"
    title = str(raw.get("title") or f"{tool.title()} Finding")[:220]
    description = str(raw.get("description") or raw.get("message") or "Isolated worker reported a tool finding.")[:2200]
    affected_line = raw.get("affected_line") or raw.get("line")
    return Finding(
        id=str(raw.get("id") or f"isolated-static-{idx:03d}"),
        module="static_analysis",  # type: ignore[arg-type]
        severity=severity,  # type: ignore[arg-type]
        title=title,
        description=description,
        affected_file=str(raw.get("affected_file") or raw.get("file") or "")[:260] or None,
        affected_line=affected_line if isinstance(affected_line, int) else None,
        affected_column=raw.get("affected_column") if isinstance(raw.get("affected_column"), int) else None,
        affected_code=str(raw.get("affected_code") or raw.get("code") or "")[:1400] or None,
        evidence=str(raw.get("evidence") or description)[:1800],
        impact=str(raw.get("impact") or "A real static-analysis worker reported a code-level issue that needs triage.")[:1200],
        fix=str(raw.get("fix") or raw.get("recommendation") or "Review the cited file/line, patch the code, add a regression test, and rerun the worker.")[:1600],
        source_tools=[tool],
        repro_steps=raw.get("repro_steps") if isinstance(raw.get("repro_steps"), list) else ["Run the isolated static-analysis worker on the same source files and review the cited tool output."],
        verification_status=str(raw.get("verification_status") or "tool_detected_needs_triage")[:80],
        confidence=str(raw.get("confidence") or "medium")[:40],  # type: ignore[arg-type]
        source=str(raw.get("source") or "Isolated Static Analysis Worker")[:160],
        category=str(raw.get("category") or "static_analysis")[:120],
        rule_id=str(raw.get("rule_id") or f"WG-ISOLATED-{tool.upper()}")[:160],
        fingerprint=str(raw.get("fingerprint") or sha12(f"{tool}:{title}:{affected_line}:{description}")),
        business_impact=str(raw.get("business_impact") or "Static analyzer evidence improves pre-audit readiness, but a human reviewer still needs to confirm true/false positive status.")[:1200],
        developer_explanation=str(raw.get("developer_explanation") or "This was parsed from an actually executed tool inside the isolated worker service.")[:1600],
        recommendation=str(raw.get("recommendation") or "Triage, patch, test, and rerun the worker before public launch.")[:1600],
        references=raw.get("references") if isinstance(raw.get("references"), list) else [tool],
        paid_review_recommended=severity in {"critical", "high"},
    )


def _build_scan_response(worker_payload: dict[str, Any], *, project_name: str | None, source_label: str, input_files: list[dict[str, str]], rejected_files: list[dict[str, str]]) -> ScanResponse:
    raw_findings = worker_payload.get("findings") if isinstance(worker_payload.get("findings"), list) else []
    findings = [_finding_from_worker(item, idx) for idx, item in enumerate(raw_findings, start=1) if isinstance(item, dict)]
    findings = prepare_professional_findings(findings, default_source_tool="isolated_static_worker")
    score = score_findings(findings) if findings else 98
    metadata = {
        "engine_version": ENGINE_VERSION,
        "worker_engine_version": worker_payload.get("engine_version"),
        "worker_run_id": worker_payload.get("run_id"),
        "source_label": source_label,
        "tool_status": worker_payload.get("tool_status") if isinstance(worker_payload.get("tool_status"), dict) else {},
        "tool_runs": worker_payload.get("tool_runs") if isinstance(worker_payload.get("tool_runs"), dict) else {},
        "worker_summary": worker_payload.get("summary") if isinstance(worker_payload.get("summary"), dict) else {},
        "source_files_written": [item["path"] for item in input_files],
        "source_file_count": len(input_files),
        "rejected_files": rejected_files,
        "evidence_source": "isolated_static_worker_service",
        "main_backend_executes_tools": False,
        "real_only_note": "Findings are counted only when returned by a separately deployed isolated static-analysis worker that actually executed tools. Missing/disabled worker states are not converted into vulnerabilities.",
    }
    return ScanResponse(
        report_id=f"WG-STATIC-WORKER-{_now_iso().replace(':', '').replace('-', '')[:15]}",
        generated_at=datetime.now(timezone.utc),
        project_name=project_name,
        module_score=ModuleScore(module="static_analysis", score=score, risk_label=risk_label(score), assessed=True),  # type: ignore[arg-type]
        findings=findings,
        severity_breakdown=severity_breakdown(findings),
        priority_actions=priority_actions(findings),
        input_hash=_hash_payload("|".join(item["path"] + item["content"] for item in input_files)),
        engine_version=ENGINE_VERSION,
        scan_metadata=metadata,
    )


async def run_isolated_static_worker_files(
    source_files: list[dict[str, str]],
    *,
    project_name: str | None,
    requested_tools: list[str] | None = None,
    source_label: str = "auto_discovered_source",
) -> ScanResponse | None:
    """Dispatch source files to the isolated worker service when explicitly configured.

    Returns None when the bridge is disabled/misconfigured so existing local/static-artifact
    behavior remains unchanged. It never runs tools inside the main backend process.
    """
    status = isolated_static_worker_status()
    if not status["will_auto_run"]:
        return None
    cleaned, rejected = _sanitize_source_files(source_files)
    if not cleaned:
        return None
    worker_url = str(settings.static_worker_url or "").rstrip("/")
    if not worker_url or not settings.static_worker_token:
        return None
    payload = {
        "project_name": project_name,
        "source_label": source_label,
        "files": cleaned,
        "tools": [tool for tool in (requested_tools or list(SUPPORTED_TOOLS)) if tool in SUPPORTED_TOOLS],
        "authorization_confirmed": True,
        "real_only_acknowledged": True,
    }
    headers = {
        "Authorization": f"Bearer {settings.static_worker_token}",
        "X-Web3Guard-Worker-Bridge": ENGINE_VERSION,
    }
    timeout = httpx.Timeout(float(settings.static_worker_timeout_seconds))
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            response = await client.post(f"{worker_url}/static-analysis/run", json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPError as exc:
            raise RuntimeError(f"Isolated static-analysis worker request failed: {exc}") from exc
    if not isinstance(data, dict) or not data.get("ok"):
        reason = data.get("reason") if isinstance(data, dict) else "worker returned a non-object response"
        raise RuntimeError(f"Isolated static-analysis worker did not complete: {reason}")
    data.setdefault("tool_status", {})
    data.setdefault("tool_runs", {})
    return _build_scan_response(data, project_name=project_name, source_label=source_label, input_files=cleaned, rejected_files=rejected)
