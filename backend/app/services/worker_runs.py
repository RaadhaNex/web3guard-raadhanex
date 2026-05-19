from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Any

from app.core.config import settings
from app.services.solidity_utils import sha12
from app.services.static_analysis_tools import run_static_analysis, static_analysis_status
from app.services.worker_execution import SUPPORTED_WORKER_TOOLS, worker_execution_status

PHASE33_VERSION = "web3guard-real-worker-run-engine-v33.0"
SAFE_STATUS_LABELS = (
    "Ready",
    "Assessed",
    "Not assessed yet",
    "Tool Not Installed",
    "Provider Not Configured",
    "Needs API Key",
    "Manual review required",
    "Failed",
    "Timeout",
    "Imported evidence",
)
STATIC_EXECUTION_TOOLS = ("slither", "aderyn", "semgrep")
DEEP_WORKER_TOOLS = ("foundry", "echidna", "mythril")
SEVERITY_MAP = {
    "critical": "critical",
    "high": "high",
    "medium": "medium",
    "moderate": "medium",
    "warning": "medium",
    "warn": "medium",
    "low": "low",
    "info": "info",
    "informational": "info",
    "optimization": "info",
}
_SECRET_PATTERNS = [
    re.compile(r"(?i)(private[_-]?key|mnemonic|seed[_ -]?phrase)\s*[:=]\s*['\"][^'\"]{8,}"),
    re.compile(r"(?i)(razorpay|supabase|openai|anthropic|github)[_-]?(secret|token|key)\s*[:=]\s*['\"][^'\"]{8,}"),
]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _severity(value: Any, default: str = "medium") -> str:
    return SEVERITY_MAP.get(str(value or default).strip().lower(), default)


def _safe_short(value: Any, limit: int = 700) -> str:
    text = str(value or "").strip()
    return text[:limit] + ("…" if len(text) > limit else "")


def _json_loads(text: str) -> Any:
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError("tool_json is not valid JSON") from exc


def _has_secret_like_input(value: str | None) -> bool:
    text = value or ""
    return any(pattern.search(text) for pattern in _SECRET_PATTERNS)


def _tool_matrix() -> list[dict[str, Any]]:
    status = worker_execution_status()
    return status.get("tools", [])


def _matrix_by_key() -> dict[str, dict[str, Any]]:
    return {item["key"]: item for item in _tool_matrix()}


def worker_run_status() -> dict[str, Any]:
    tools = _tool_matrix()
    static_status = static_analysis_status()
    runnable_static = [
        key for key, item in static_status.get("tools", {}).items()
        if bool(item.get("will_run"))
    ]
    return {
        "ok": True,
        "version": PHASE33_VERSION,
        "purpose": "Run or import real worker evidence for founder-owned code only. Missing tools stay status-only.",
        "safe_status_labels": list(SAFE_STATUS_LABELS),
        "static_execution_ready_tools": runnable_static,
        "static_analysis_enabled": bool(settings.static_analysis_enabled),
        "worker_execution_enabled": bool(settings.worker_execution_enabled),
        "deep_analysis_enabled": bool(settings.deep_analysis_enabled),
        "mythril_policy": "Docker/isolated worker required by default" if settings.mythril_worker_required and not settings.mythril_allow_local_execution else "Local Mythril execution allowed by env",
        "tools": tools,
        "execution_modes": {
            "static_solidity": "Slither/Aderyn/Semgrep can run only when installed, enabled, and explicitly requested.",
            "deep_manifest": "Foundry/Echidna/Mythril commands are generated with safety requirements and do not create findings until real output exists.",
            "import_json": "Existing worker output can be imported and normalized as imported evidence; it is not claimed as Web3Guard-generated unless produced by configured worker.",
        },
        "safety_boundaries": {
            "no_fake_findings": True,
            "no_private_key_collection": True,
            "no_seed_phrase_collection": True,
            "no_wallet_signing": True,
            "no_exploit_automation": True,
            "no_unauthorized_active_scanning": True,
            "not_certified_audit": True,
            "tool_output_required_for_tool_findings": True,
        },
        "blocked_claims": ["100% secure", "certified audit", "audited by Web3Guard", "exploit automation", "wallet signing"],
    }


def worker_manifest(project_name: str | None = None, project_type: str | None = None, tools: list[str] | None = None) -> dict[str, Any]:
    selected = [tool for tool in (tools or list(SUPPORTED_WORKER_TOOLS)) if tool in SUPPORTED_WORKER_TOOLS]
    if not selected:
        selected = list(SUPPORTED_WORKER_TOOLS)
    matrix = _matrix_by_key()
    steps: list[dict[str, Any]] = []
    for order, tool in enumerate(selected, start=1):
        info = matrix.get(tool, {})
        steps.append({
            "order": order,
            "tool": tool,
            "name": info.get("name") or tool,
            "status": info.get("status") or "Not assessed yet",
            "will_run_now": bool(info.get("will_run")),
            "installed": bool(info.get("installed")),
            "command_template": info.get("command_template") or "Manual / Not Assessed",
            "evidence_policy": "Only stdout/stderr/JSON from an actually executed configured worker may create tool findings.",
            "timeout_policy": _timeout_policy(tool),
            "storage_policy": "Store input hash, command fingerprint, tool version, return code, timestamps, parser version, and raw evidence reference. Do not store secrets.",
            "when_missing": "Show Tool Not Installed / Provider Not Configured / Manual review required. Do not invent findings.",
            "next_action": info.get("next_action") or "Configure a safe worker before execution.",
        })
    return {
        "ok": True,
        "version": PHASE33_VERSION,
        "project_name": project_name or "Untitled project",
        "project_type": project_type or "founder-owned Solidity/Web3 workspace",
        "steps": steps,
        "recommended_runtime": {
            "api": "FastAPI validates scope, limits, acknowledgement, and creates a job.",
            "worker": "Separate isolated worker/container runs one tool at a time with no secrets injected.",
            "network": "Disabled for code analyzers by default; provider APIs remain separate explicit calls.",
            "cleanup": "Temporary workspace is deleted after run unless user explicitly saves report evidence.",
        },
        "blocked_actions": [
            "No private key / seed phrase / mnemonic input",
            "No wallet signing",
            "No exploit automation",
            "No unauthorized active scanning",
            "No fake scanner output",
            "No certified audit wording",
        ],
    }


def _timeout_policy(tool: str) -> dict[str, Any]:
    if tool in STATIC_EXECUTION_TOOLS:
        return {"seconds": settings.audit_tool_timeout_seconds, "source": "AUDIT_TOOL_TIMEOUT_SECONDS"}
    if tool in {"echidna", "mythril"}:
        return {"seconds": settings.deep_analysis_timeout_seconds, "source": "DEEP_ANALYSIS_TIMEOUT_SECONDS"}
    return {"seconds": settings.worker_probe_timeout_seconds, "source": "WORKER_PROBE_TIMEOUT_SECONDS"}


def _normalize_static_finding(item: Any) -> dict[str, Any]:
    source = getattr(item, "source", None) or "Static worker output"
    title = getattr(item, "title", None) or "Static worker finding"
    severity = _severity(getattr(item, "severity", None), "info")
    return {
        "id": getattr(item, "id", None) or f"worker-static-{sha12(str(title))}",
        "tool": _tool_from_source(source),
        "module": getattr(item, "module", None) or "static_analysis",
        "kind": "tool_finding" if getattr(item, "category", "static_analysis") != "tool_status" else "tool_status",
        "status": "Assessed" if getattr(item, "category", "static_analysis") != "tool_status" else "Not assessed yet",
        "severity": severity,
        "title": title,
        "description": _safe_short(getattr(item, "description", None), 900),
        "source": source,
        "rule_id": getattr(item, "rule_id", None),
        "confidence": getattr(item, "confidence", None) or "medium",
        "affected_line": getattr(item, "affected_line", None),
        "affected_code": getattr(item, "affected_code", None),
        "evidence_id": f"EVID-WORKER-{sha12(str(source) + str(title) + str(getattr(item, 'fingerprint', '')))}",
        "limitation": "Real static tool evidence when produced by an installed/enabled worker; still not a certified audit.",
        "recommendation": getattr(item, "recommendation", None) or "Review the raw tool evidence and manually triage true/false positive status.",
    }


def _tool_from_source(source: str) -> str:
    value = source.lower()
    for tool in SUPPORTED_WORKER_TOOLS:
        if tool in value:
            return tool
    return "static"


def run_static_worker(source_code: str, project_name: str | None, file_name: str | None, tools: list[str] | None, execute: bool) -> dict[str, Any]:
    if _has_secret_like_input(source_code):
        raise ValueError("Source appears to contain a private key, seed phrase, mnemonic, or provider secret. Remove secrets before worker execution.")
    selected = [tool for tool in (tools or list(STATIC_EXECUTION_TOOLS)) if tool in STATIC_EXECUTION_TOOLS]
    if not selected:
        selected = list(STATIC_EXECUTION_TOOLS)
    if not execute:
        return {
            "ok": True,
            "version": PHASE33_VERSION,
            "mode": "plan_only",
            "status": "Not assessed yet",
            "input_hash": sha12(source_code),
            "requested_tools": selected,
            "manifest": worker_manifest(project_name, "Solidity static worker", selected),
            "findings": [],
            "real_findings_count": 0,
            "note": "execute=false, so no subprocess tool was run and no fake findings were generated.",
        }
    response = run_static_analysis(source_code, project_name, file_name or "Contract.sol", selected)
    findings = [_normalize_static_finding(item) for item in response.findings]
    real_findings = [item for item in findings if item.get("kind") != "tool_status"]
    return {
        "ok": True,
        "version": PHASE33_VERSION,
        "mode": "executed_static_worker",
        "status": "Assessed" if real_findings else "Not assessed yet",
        "report_id": response.report_id,
        "generated_at": response.generated_at.isoformat(),
        "input_hash": response.input_hash,
        "requested_tools": selected,
        "score_label": "Readiness signal only — not an audit score",
        "module_score": response.module_score.model_dump(mode="json"),
        "severity_breakdown": response.severity_breakdown,
        "tool_runs": response.scan_metadata.get("tool_runs", {}),
        "tool_status": response.scan_metadata.get("tool_status", {}),
        "findings": findings,
        "real_findings_count": len(real_findings),
        "evidence": _evidence_from_findings(findings, response.input_hash),
        "limitation": "Only tools installed/enabled in this runtime were executed. Missing tools remain Not Assessed / Tool Not Installed and do not create fake findings.",
    }


def _evidence_from_findings(findings: list[dict[str, Any]], input_hash: str) -> list[dict[str, Any]]:
    evidence = [{
        "evidence_id": f"EVID-INPUT-{input_hash}",
        "source": "Submitted Solidity input hash",
        "status": "Imported evidence",
        "created_at": _now_iso(),
        "limitation": "Hash proves the submitted input payload, not that the project is secure.",
    }]
    seen = {evidence[0]["evidence_id"]}
    for item in findings:
        evid = item.get("evidence_id")
        if evid and evid not in seen:
            evidence.append({
                "evidence_id": evid,
                "source": item.get("source") or "Worker output",
                "status": item.get("status") or "Assessed",
                "created_at": _now_iso(),
                "limitation": item.get("limitation") or "Tool evidence requires manual triage.",
            })
            seen.add(evid)
    return evidence


def import_worker_json(tool: str, tool_json: str, generated_by_web3guard_worker: bool = False) -> dict[str, Any]:
    if tool not in SUPPORTED_WORKER_TOOLS:
        raise ValueError("Unsupported worker tool")
    data = _json_loads(tool_json)
    if tool == "slither":
        findings = _parse_slither(data)
    elif tool == "semgrep":
        findings = _parse_semgrep(data)
    elif tool == "mythril":
        findings = _parse_mythril(data)
    elif tool == "echidna":
        findings = _parse_echidna(data)
    elif tool == "foundry":
        findings = _parse_foundry(data)
    elif tool == "aderyn":
        findings = _parse_aderyn(data)
    else:
        findings = []
    mode = "web3guard_worker_evidence" if generated_by_web3guard_worker else "imported_worker_evidence"
    for item in findings:
        item["evidence_mode"] = mode
        if not generated_by_web3guard_worker:
            item["limitation"] = "Imported tool JSON. Verify against a trusted Web3Guard worker run before treating this as production evidence."
    return {
        "ok": True,
        "version": PHASE33_VERSION,
        "tool": tool,
        "status": "Assessed" if findings else "Imported evidence",
        "evidence_mode": mode,
        "input_hash": sha12(tool_json),
        "findings": findings,
        "real_findings_count": len(findings),
        "evidence": _evidence_from_findings(findings, sha12(tool_json)),
        "not_claimed": ["Not a certified audit", "No 100% secure claim", "Imported evidence is not automatically Web3Guard-generated evidence"],
    }


def _parse_slither(data: Any) -> list[dict[str, Any]]:
    detectors = data.get("results", {}).get("detectors", []) if isinstance(data, dict) else []
    findings = []
    for idx, item in enumerate(detectors[: settings.max_tool_findings_per_run], start=1):
        if not isinstance(item, dict):
            continue
        check = str(item.get("check") or "slither-detector")
        impact = _severity(item.get("impact"), "medium")
        description = _safe_short(item.get("description") or item.get("markdown") or "Slither reported a potential issue.", 900)
        findings.append(_worker_finding(idx, "slither", impact, check.replace("-", " ").title(), description, f"SLITHER-{check}"))
    return findings


def _parse_semgrep(data: Any) -> list[dict[str, Any]]:
    results = data.get("results", []) if isinstance(data, dict) else []
    findings = []
    for idx, item in enumerate(results[: settings.max_tool_findings_per_run], start=1):
        if not isinstance(item, dict):
            continue
        extra = item.get("extra") or {}
        rule_id = str(item.get("check_id") or "semgrep-rule")
        sev = _severity(extra.get("severity"), "medium")
        findings.append(_worker_finding(idx, "semgrep", sev, rule_id.split(".")[-1].replace("-", " ").title(), extra.get("message") or "Semgrep reported a match.", f"SEMGREP-{rule_id}"))
    return findings


def _parse_aderyn(data: Any) -> list[dict[str, Any]]:
    candidates: list[Any] = []
    if isinstance(data, dict):
        for key in ("issues", "results", "detectors", "findings"):
            if isinstance(data.get(key), list):
                candidates = data[key]
                break
    findings = []
    for idx, item in enumerate(candidates[: settings.max_tool_findings_per_run], start=1):
        if not isinstance(item, dict):
            continue
        title = str(item.get("title") or item.get("name") or item.get("check") or "Aderyn Finding")
        findings.append(_worker_finding(idx, "aderyn", _severity(item.get("severity") or item.get("impact")), title, item.get("description") or item.get("message") or "Aderyn reported a potential issue.", f"ADERYN-{sha12(title)[:8]}"))
    return findings


def _parse_mythril(data: Any) -> list[dict[str, Any]]:
    issues = data.get("issues", []) if isinstance(data, dict) else []
    findings = []
    for idx, item in enumerate(issues[: settings.max_deep_tool_findings_per_run], start=1):
        if not isinstance(item, dict):
            continue
        title = str(item.get("title") or item.get("swc-title") or "Mythril symbolic execution issue")
        swc = str(item.get("swc-id") or item.get("swcID") or "MYTHRIL")
        findings.append(_worker_finding(idx, "mythril", _severity(item.get("severity"), "medium"), title, item.get("description") or item.get("description-head") or "Mythril reported a symbolic execution issue.", f"MYTHRIL-{swc}"))
    return findings


def _parse_echidna(data: Any) -> list[dict[str, Any]]:
    tests: list[Any] = []
    if isinstance(data, dict):
        for key in ("tests", "testResults", "results"):
            if isinstance(data.get(key), list):
                tests = data[key]
                break
    findings = []
    for idx, item in enumerate(tests[: settings.max_deep_tool_findings_per_run], start=1):
        if not isinstance(item, dict):
            continue
        status = str(item.get("status") or item.get("result") or "").lower()
        if status not in {"fail", "failed", "falsified", "error"}:
            continue
        name = str(item.get("name") or item.get("test") or item.get("property") or "Echidna property failed")
        findings.append(_worker_finding(idx, "echidna", "high", name, item.get("message") or item.get("error") or "Echidna reported a failing property/fuzz test.", f"ECHIDNA-{sha12(name)[:8]}"))
    return findings


def _parse_foundry(data: Any) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    if isinstance(data, dict):
        raw = data.get("test_results") or data.get("tests") or data.get("results")
        if isinstance(raw, list):
            candidates = [item for item in raw if isinstance(item, dict)]
        elif isinstance(raw, dict):
            for file_value in raw.values():
                if isinstance(file_value, dict):
                    for contract_value in file_value.values():
                        if isinstance(contract_value, dict):
                            for test_name, test_value in contract_value.items():
                                if isinstance(test_value, dict):
                                    candidates.append({"name": test_name, **test_value})
    findings = []
    for idx, item in enumerate(candidates[: settings.max_deep_tool_findings_per_run], start=1):
        status = str(item.get("status") or item.get("success") or "").lower()
        failed = status in {"fail", "failed", "false"} or item.get("success") is False
        if not failed:
            continue
        name = str(item.get("name") or item.get("test") or "Foundry test failed")
        findings.append(_worker_finding(idx, "foundry", "high", name, item.get("reason") or item.get("message") or "Foundry reported a failing test.", f"FOUNDRY-{sha12(name)[:8]}"))
    return findings


def _worker_finding(idx: int, tool: str, severity: str, title: str, description: Any, rule_id: str) -> dict[str, Any]:
    desc = _safe_short(description, 900)
    return {
        "id": f"worker-{tool}-{idx:03d}",
        "tool": tool,
        "module": "worker_execution",
        "kind": "tool_finding",
        "status": "Assessed",
        "severity": _severity(severity, "medium"),
        "title": title,
        "description": desc,
        "source": f"{tool.title()} worker JSON output",
        "rule_id": rule_id,
        "confidence": "high" if tool in {"slither", "semgrep", "mythril"} else "medium",
        "evidence_id": f"EVID-{tool.upper()}-{sha12(tool + title + desc)}",
        "limitation": "Tool evidence requires manual security triage and does not equal a certified audit.",
        "recommendation": "Review raw worker evidence, confirm true/false positive status, patch, and rerun before launch.",
    }
