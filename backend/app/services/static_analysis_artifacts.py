from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from app.models.schemas import Finding, ModuleScore, ScanResponse
from app.services.scoring import priority_actions, risk_label, score_findings, severity_breakdown
from app.services.solidity_utils import sha12

ENGINE_VERSION = "web3guard-static-artifact-bridge-v1.0"
SUPPORTED_ARTIFACTS = ("slither", "semgrep", "aderyn")


def _as_json(raw: str | None) -> tuple[Any | None, str | None]:
    if not raw or not raw.strip():
        return None, None
    try:
        return json.loads(raw), None
    except json.JSONDecodeError as exc:
        return None, f"Invalid JSON artifact: {exc.msg} at line {exc.lineno}, column {exc.colno}"


def _text(value: Any, fallback: str = "") -> str:
    if value is None:
        return fallback
    text = str(value).strip()
    return text or fallback


def _severity_from_slither(value: Any) -> str:
    text = _text(value, "informational").lower()
    return {"critical": "critical", "high": "high", "medium": "medium", "low": "low", "informational": "info", "optimization": "info"}.get(text, "medium")


def _severity_from_semgrep(extra: dict[str, Any]) -> str:
    metadata = extra.get("metadata") if isinstance(extra.get("metadata"), dict) else {}
    raw = _text(extra.get("severity") or metadata.get("severity") or "WARNING").upper()
    return {"ERROR": "high", "WARNING": "medium", "INFO": "info", "CRITICAL": "critical", "HIGH": "high", "MEDIUM": "medium", "LOW": "low"}.get(raw, "medium")


def _line_from_slither(item: dict[str, Any]) -> int | None:
    elements = item.get("elements") if isinstance(item.get("elements"), list) else []
    if not elements:
        return None
    first = elements[0] if isinstance(elements[0], dict) else {}
    mapping = first.get("source_mapping") if isinstance(first.get("source_mapping"), dict) else {}
    lines = mapping.get("lines") if isinstance(mapping.get("lines"), list) else []
    return lines[0] if lines and isinstance(lines[0], int) else None


def _artifact_finding(
    idx: int,
    *,
    tool: str,
    severity: str,
    title: str,
    description: str,
    rule_id: str,
    line: int | None = None,
    code: str | None = None,
    confidence: str = "medium",
) -> Finding:
    return Finding(
        id=f"artifact-{tool}-{idx:03d}",
        module="static_analysis",  # type: ignore[arg-type]
        severity=severity,  # type: ignore[arg-type]
        title=title[:180],
        description=description[:3000],
        affected_line=line,
        affected_function=None,
        affected_code=code[:1200] if code else None,
        confidence=confidence,  # type: ignore[arg-type]
        source=f"User-Supplied {tool.title()} JSON Artifact",
        category="static_analysis_artifact",
        rule_id=rule_id[:160],
        fingerprint=sha12(f"artifact|{tool}|{rule_id}|{line}|{title}|{description[:160]}"),
        business_impact="This finding came from a supplied static-analysis artifact. It is stronger than a UI hint, but still needs developer/manual triage before launch.",
        developer_explanation="Web3Guard parsed a Slither/Semgrep/Aderyn JSON artifact instead of inventing a finding. The backend did not claim it independently executed this tool unless tool_runs also show a backend run.",
        recommendation="Review the rule output, confirm true/false positive status in the source code, patch the issue, then rerun the tool and Web3Guard scan.",
        references=[tool, "user-supplied-static-analysis-artifact"],
        paid_review_recommended=severity in {"critical", "high"},
    )


def _status_finding(idx: int, tool: str, message: str) -> Finding:
    return Finding(
        id=f"artifact-{tool}-status-{idx:03d}",
        module="static_analysis",  # type: ignore[arg-type]
        severity="info",
        title=f"{tool.title()} Artifact Not Parsed",
        description=message,
        affected_line=None,
        affected_function=None,
        affected_code=None,
        confidence="high",
        source="Static Analysis Artifact Status",
        category="tool_status",
        rule_id=f"WG-ARTIFACT-STATUS-{tool.upper()}",
        fingerprint=sha12(f"artifact-status|{tool}|{message}"),
        business_impact="This status does not create a fake vulnerability; it explains why artifact evidence was not used.",
        developer_explanation="Only valid Slither/Semgrep/Aderyn JSON shapes are converted into static-analysis findings.",
        recommendation="Paste the raw JSON output from the real tool, not screenshots or formatted text, then rerun the scan.",
        references=["Web3Guard real-only artifact parser"],
        paid_review_recommended=False,
    )


def _parse_slither(data: Any, start_idx: int = 1) -> tuple[list[Finding], dict[str, Any]]:
    findings: list[Finding] = []
    detectors = []
    if isinstance(data, dict):
        results = data.get("results") if isinstance(data.get("results"), dict) else {}
        if isinstance(results.get("detectors"), list):
            detectors = results["detectors"]
    for local_idx, item in enumerate(detectors[:60], start=start_idx):
        if not isinstance(item, dict):
            continue
        check = _text(item.get("check"), "slither-detector")
        description = _text(item.get("description") or item.get("markdown"), "Slither reported a potential issue.")
        findings.append(_artifact_finding(
            local_idx,
            tool="slither",
            severity=_severity_from_slither(item.get("impact")),
            title=check.replace("-", " ").title(),
            description=description,
            rule_id=f"SLITHER-{check}",
            line=_line_from_slither(item),
            confidence="high",
        ))
    return findings, {"artifact_shape": "slither.results.detectors", "raw_detector_count": len(detectors), "parsed_findings": len(findings)}


def _parse_semgrep(data: Any, start_idx: int = 1) -> tuple[list[Finding], dict[str, Any]]:
    findings: list[Finding] = []
    results = data.get("results") if isinstance(data, dict) and isinstance(data.get("results"), list) else []
    for local_idx, item in enumerate(results[:80], start=start_idx):
        if not isinstance(item, dict):
            continue
        extra = item.get("extra") if isinstance(item.get("extra"), dict) else {}
        start = item.get("start") if isinstance(item.get("start"), dict) else {}
        rule_id = _text(item.get("check_id"), "semgrep-rule")
        findings.append(_artifact_finding(
            local_idx,
            tool="semgrep",
            severity=_severity_from_semgrep(extra),
            title=rule_id.split(".")[-1].replace("-", " ").title(),
            description=_text(extra.get("message"), "Semgrep reported a pattern match."),
            rule_id=f"SEMGREP-{rule_id}",
            line=start.get("line") if isinstance(start.get("line"), int) else None,
            code=extra.get("lines") if isinstance(extra.get("lines"), str) else None,
            confidence="medium",
        ))
    return findings, {"artifact_shape": "semgrep.results", "raw_result_count": len(results), "parsed_findings": len(findings)}


def _candidate_aderyn_items(data: Any) -> list[Any]:
    if not isinstance(data, dict):
        return []
    for key in ("issues", "results", "detectors", "findings"):
        if isinstance(data.get(key), list):
            return data[key]
    report = data.get("report")
    if isinstance(report, dict):
        for key in ("issues", "results", "detectors", "findings"):
            if isinstance(report.get(key), list):
                return report[key]
    return []


def _parse_aderyn(data: Any, start_idx: int = 1) -> tuple[list[Finding], dict[str, Any]]:
    findings: list[Finding] = []
    items = _candidate_aderyn_items(data)
    for local_idx, item in enumerate(items[:60], start=start_idx):
        if not isinstance(item, dict):
            continue
        title = _text(item.get("title") or item.get("name") or item.get("check"), "Aderyn Finding")
        desc = _text(item.get("description") or item.get("message") or item.get("body"), "Aderyn reported a potential issue.")
        sev = _text(item.get("severity") or item.get("impact"), "medium").lower()
        severity = {"critical": "critical", "high": "high", "medium": "medium", "low": "low", "info": "info", "informational": "info"}.get(sev, "medium")
        line = item.get("line") or item.get("line_number")
        findings.append(_artifact_finding(
            local_idx,
            tool="aderyn",
            severity=severity,
            title=title,
            description=desc,
            rule_id=f"ADERYN-{sha12(title)[:8]}",
            line=line if isinstance(line, int) else None,
            confidence="medium",
        ))
    return findings, {"artifact_shape": "aderyn.issues/results/findings", "raw_item_count": len(items), "parsed_findings": len(findings)}


def analyze_static_artifacts(
    *,
    slither_json: str | None = None,
    semgrep_json: str | None = None,
    aderyn_json: str | None = None,
    project_name: str | None = None,
) -> ScanResponse | None:
    supplied = {
        "slither": slither_json,
        "semgrep": semgrep_json,
        "aderyn": aderyn_json,
    }
    if not any(value and value.strip() for value in supplied.values()):
        return None

    findings: list[Finding] = []
    artifact_runs: dict[str, Any] = {}
    idx = 1
    for tool, raw in supplied.items():
        if not raw or not raw.strip():
            artifact_runs[tool] = {"state": "Not Supplied", "parsed_findings": 0}
            continue
        data, error = _as_json(raw)
        if error:
            findings.append(_status_finding(idx, tool, error)); idx += 1
            artifact_runs[tool] = {"state": "Invalid Artifact", "parsed_findings": 0, "error": error}
            continue
        if tool == "slither":
            parsed, meta = _parse_slither(data, idx)
        elif tool == "semgrep":
            parsed, meta = _parse_semgrep(data, idx)
        else:
            parsed, meta = _parse_aderyn(data, idx)
        idx += max(len(parsed), 1)
        findings.extend(parsed)
        if parsed:
            artifact_runs[tool] = {"state": "User Artifact Parsed", **meta}
        else:
            message = f"A {tool} JSON artifact was supplied but no supported finding array was parsed."
            findings.append(_status_finding(idx, tool, message)); idx += 1
            artifact_runs[tool] = {"state": "No Findings Parsed", **meta}

    non_status = [finding for finding in findings if finding.category != "tool_status"]
    score = score_findings(non_status) if non_status else 98
    return ScanResponse(
        report_id=f"WG-STATIC-ARTIFACT-{uuid4().hex[:12]}",
        generated_at=datetime.now(timezone.utc),
        project_name=project_name,
        module_score=ModuleScore(module="static_analysis", score=score, risk_label=risk_label(score), assessed=bool(non_status)),  # type: ignore[arg-type]
        findings=findings,
        severity_breakdown=severity_breakdown(non_status),
        priority_actions=priority_actions(non_status),
        input_hash=sha12("|".join(raw or "" for raw in supplied.values())),
        engine_version=ENGINE_VERSION,
        scan_metadata={
            "artifact_runs": artifact_runs,
            "real_only_note": "Findings were parsed from user-supplied JSON artifacts. Web3Guard does not claim independent backend execution for these artifact findings.",
            "artifact_trust_level": "user_supplied_tool_output",
            "safety_controls": {
                "executes_code": False,
                "installs_dependencies": False,
                "clones_repos": False,
                "collects_private_keys": False,
                "real_only": True,
            },
        },
    )


def static_artifact_status() -> dict[str, Any]:
    return {
        "ok": True,
        "engine_version": ENGINE_VERSION,
        "purpose": "Parse real Slither/Semgrep/Aderyn JSON artifacts when backend tools are unavailable or were run locally by the project owner.",
        "supported_artifacts": list(SUPPORTED_ARTIFACTS),
        "trust_boundary": "User-supplied artifact findings are real evidence inputs, not a Web3Guard-certified audit and not proof that Web3Guard independently executed the tool.",
        "blocked_claims": [
            "No certified audit claim",
            "No all-bugs-found claim",
            "No fake backend tool execution claim",
            "No exploit automation",
        ],
    }
