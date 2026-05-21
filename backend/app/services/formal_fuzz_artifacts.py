from __future__ import annotations

"""Professional formal/fuzz artifact engine.

This module is evidence-only: it parses user-supplied Foundry/Echidna/invariant
artifacts and converts real failures into report-ready findings. It does not run
forge, echidna, or any exploit automation on the server.
"""

import hashlib
import json
import re
from datetime import datetime, timezone
from typing import Any, Iterable

from app.models.schemas import Finding, ModuleScore, ScanResponse
from app.services.finding_normalizer import prepare_professional_findings
from app.services.scoring import priority_actions, risk_label, score_findings, severity_breakdown

FAIL_WORDS = re.compile(r"(?i)\b(fail(?:ed|ure|ing)?|falsif(?:ied|y)|counterexample|invariant.*(?:break|fail)|assert(?:ion)?\s*(?:fail|error)|panic|revert|property.*fail)\b")
PASS_WORDS = re.compile(r"(?i)\b(pass(?:ed)?|ok|success|succeed(?:ed)?|green)\b")
FILE_LINE_RE = re.compile(r"(?P<file>[A-Za-z0-9_./\\-]+\.sol):(?P<line>\d+)(?::(?P<col>\d+))?")
HEX_ADDR_RE = re.compile(r"0x[a-fA-F0-9]{40}")

SEVERITY_ALLOWED = {"critical", "high", "medium", "low", "info"}


def _sha(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8", errors="ignore")).hexdigest()[:12]


def _short(value: Any, limit: int = 1400) -> str:
    if value is None:
        return ""
    if not isinstance(value, str):
        try:
            value = json.dumps(value, ensure_ascii=False, default=str)
        except Exception:
            value = str(value)
    text = value.strip()
    return text if len(text) <= limit else text[:limit] + "..."


def _json_load(raw: str | None) -> Any | None:
    if not raw or not raw.strip():
        return None
    try:
        return json.loads(raw)
    except Exception:
        return None


def _iter_dicts(value: Any, *, depth: int = 0, max_depth: int = 8) -> Iterable[dict[str, Any]]:
    if depth > max_depth:
        return
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _iter_dicts(child, depth=depth + 1, max_depth=max_depth)
    elif isinstance(value, list):
        for item in value:
            yield from _iter_dicts(item, depth=depth + 1, max_depth=max_depth)


def _safe_severity(value: Any, default: str = "high") -> str:
    text = str(value or default).lower().strip()
    if text in SEVERITY_ALLOWED:
        return text
    if "critical" in text:
        return "critical"
    if "high" in text:
        return "high"
    if "medium" in text:
        return "medium"
    if "low" in text:
        return "low"
    if "info" in text:
        return "info"
    return default


def _location_from_text(*values: Any) -> tuple[str | None, int | None, int | None]:
    joined = "\n".join(_short(v, 500) for v in values if v is not None)
    match = FILE_LINE_RE.search(joined)
    if not match:
        return None, None, None
    return match.group("file"), int(match.group("line")), int(match.group("col")) if match.group("col") else None


def _location_from_dict(item: dict[str, Any]) -> tuple[str | None, int | None, int | None]:
    file_value = item.get("file") or item.get("filename") or item.get("path") or item.get("source") or item.get("contract")
    line_value = item.get("line") or item.get("lineNumber") or item.get("line_number") or item.get("startLine")
    col_value = item.get("column") or item.get("col") or item.get("startColumn")
    if file_value or line_value:
        try:
            line = int(line_value) if line_value is not None and str(line_value).isdigit() else None
        except Exception:
            line = None
        try:
            col = int(col_value) if col_value is not None and str(col_value).isdigit() else None
        except Exception:
            col = None
        return str(file_value) if file_value else None, line, col
    return _location_from_text(item.get("message"), item.get("error"), item.get("trace"), item.get("logs"), item.get("reason"))


def _make_finding(
    *,
    source_tool: str,
    title: str,
    description: str,
    evidence: Any,
    severity: str = "high",
    category: str = "formal_fuzz_artifact",
    rule_id: str | None = None,
    affected_file: str | None = None,
    affected_line: int | None = None,
    affected_column: int | None = None,
    fix: str | None = None,
    confidence: str = "high",
) -> Finding:
    sev = _safe_severity(severity, "high")
    evidence_text = _short(evidence, 1800)
    rid = rule_id or f"W3G-{source_tool.upper()}-{_sha(title + evidence_text)[:8]}"
    return Finding(
        id=f"{source_tool}-{_sha(rid + title + evidence_text)}",
        module="deep_analysis",
        severity=sev,
        title=title[:220],
        description=description[:2400],
        affected_file=affected_file,
        affected_line=affected_line,
        affected_column=affected_column,
        confidence=confidence if confidence in {"high", "medium", "low"} else "medium",
        source=f"{source_tool.title()} Artifact Parser",
        category=category,
        rule_id=rid,
        evidence=evidence_text,
        impact=_impact_for_category(category, sev),
        fix=fix or _fix_for_tool(source_tool, category),
        source_tools=[source_tool],
        repro_steps=_repro_steps(source_tool, affected_file, affected_line),
        verification_status="artifact_detected_needs_triage",
        exploitability="high" if sev in {"critical", "high"} else "medium" if sev == "medium" else "low",
        remediation_priority="fix_before_launch" if sev in {"critical", "high"} else "review_before_launch",
        business_impact=_impact_for_category(category, sev),
        developer_explanation=description[:1200],
        recommendation=fix or _fix_for_tool(source_tool, category),
        references=_refs_for_tool(source_tool),
        paid_review_recommended=sev in {"critical", "high"},
    )


def _impact_for_category(category: str, severity: str) -> str:
    if category in {"foundry_test_failure", "echidna_property_failure", "invariant_failure"}:
        return "A failing test/property/invariant means the submitted project evidence already contains a reproducible correctness or safety failure. Treat high-severity failures as launch blockers until reproduced, fixed, and rerun."
    if category == "counterexample":
        return "The artifact includes counterexample evidence, which can demonstrate a reachable path that violates an intended property."
    return f"The supplied formal/fuzz artifact contains {severity} evidence that requires manual triage before launch."


def _fix_for_tool(source_tool: str, category: str) -> str:
    if source_tool == "foundry":
        return "Reproduce with `forge test -vvv`, patch the failing condition, add a regression test, and rerun before launch."
    if source_tool == "echidna":
        return "Reproduce with the same Echidna config/corpus, minimize the counterexample, patch the invariant violation, and rerun until properties pass."
    return "Reproduce the supplied invariant failure, confirm whether it is expected behavior or a real bug, then patch or document accepted risk with reviewer sign-off."


def _refs_for_tool(source_tool: str) -> list[str]:
    if source_tool == "foundry":
        return ["Foundry forge test output", "Web3Guard supplied artifact evidence"]
    if source_tool == "echidna":
        return ["Echidna property/fuzz output", "Web3Guard supplied artifact evidence"]
    return ["Supplied invariant/simulation artifact", "Web3Guard supplied artifact evidence"]


def _repro_steps(source_tool: str, file_path: str | None, line: int | None) -> list[str]:
    steps = []
    if source_tool == "foundry":
        steps.append("Run the same Foundry command locally, preferably `forge test -vvv --json` or `forge test -vvv`.")
    elif source_tool == "echidna":
        steps.append("Run the same Echidna config/corpus locally and confirm the failing property/counterexample.")
    else:
        steps.append("Open the supplied invariant/simulation artifact and verify the failing property evidence.")
    if file_path and line:
        steps.append(f"Review {file_path} around line {line}.")
    steps.append("Patch the root cause, rerun the same artifact-producing test, and attach passing output before report approval.")
    return steps


def parse_foundry_output(raw: str | None) -> tuple[list[Finding], dict[str, Any]]:
    if not raw or not raw.strip():
        return [], {"state": "Not Assessed", "reason": "No Foundry output supplied."}
    findings: list[Finding] = []
    parsed = _json_load(raw)
    if parsed is not None:
        for item in _iter_dicts(parsed):
            item_text = _short(item, 2200)
            status = str(item.get("status") or item.get("result") or item.get("success") or item.get("passed") or "").lower()
            failure_text = " ".join(str(item.get(key) or "") for key in ("failure", "error", "reason", "message", "logs", "trace", "counterexample"))
            is_failure = status in {"fail", "failed", "failure", "false", "0"} or item.get("success") is False or item.get("passed") is False or FAIL_WORDS.search(failure_text)
            name = item.get("name") or item.get("test") or item.get("function") or item.get("label") or item.get("contract")
            if is_failure and name:
                affected_file, affected_line, affected_column = _location_from_dict(item)
                category = "counterexample" if "counterexample" in item_text.lower() else "foundry_test_failure"
                findings.append(_make_finding(
                    source_tool="foundry",
                    title=f"Foundry Test Failed: {name}",
                    description="User-supplied Foundry output reports a failing test, invariant, revert, panic, or counterexample. This is real supplied evidence and must be reproduced before launch.",
                    evidence=item,
                    severity=_safe_severity(item.get("severity"), "high"),
                    category=category,
                    affected_file=affected_file,
                    affected_line=affected_line,
                    affected_column=affected_column,
                ))
    else:
        findings.extend(_parse_foundry_text(raw))
    if not findings and FAIL_WORDS.search(raw):
        findings.extend(_parse_foundry_text(raw))
    return _unique_findings(findings), {
        "state": "Assessed",
        "artifact_type": "foundry",
        "raw_format": "json" if parsed is not None else "text",
        "failure_count": len(_unique_findings(findings)),
        "parsed": True,
    }


def _parse_foundry_text(raw: str) -> list[Finding]:
    findings: list[Finding] = []
    lines = raw.splitlines()
    fail_indexes = [idx for idx, line in enumerate(lines) if FAIL_WORDS.search(line)]
    for position, idx in enumerate(fail_indexes[:25], start=1):
        window = "\n".join(lines[max(0, idx - 4): min(len(lines), idx + 10)])
        affected_file, affected_line, affected_column = _location_from_text(window)
        title_match = re.search(r"(?i)(test[A-Za-z0-9_]+|invariant_[A-Za-z0-9_]+|echidna_[A-Za-z0-9_]+|\[[A-Z]+\].*)", window)
        title_part = title_match.group(1) if title_match else f"failure-{position}"
        severity = "critical" if re.search(r"(?i)(invariant|counterexample|fund|drain|panic|assert)", window) else "high"
        findings.append(_make_finding(
            source_tool="foundry",
            title=f"Foundry Failure Evidence: {title_part}",
            description="User-supplied Foundry text output contains a failing test/invariant/counterexample signal. Web3Guard did not run this test; it parsed supplied evidence only.",
            evidence=window,
            severity=severity,
            category="counterexample" if "counterexample" in window.lower() else "foundry_test_failure",
            affected_file=affected_file,
            affected_line=affected_line,
            affected_column=affected_column,
        ))
    return findings


def parse_echidna_output(raw: str | None) -> tuple[list[Finding], dict[str, Any]]:
    if not raw or not raw.strip():
        return [], {"state": "Not Assessed", "reason": "No Echidna JSON/text output supplied."}
    findings: list[Finding] = []
    parsed = _json_load(raw)
    source = parsed if parsed is not None else raw
    if parsed is not None:
        for item in _iter_dicts(parsed):
            item_text = _short(item, 2200)
            status = str(item.get("status") or item.get("result") or item.get("state") or item.get("success") or item.get("passed") or "").lower()
            is_failure = status in {"falsified", "failed", "fail", "failure", "false"} or item.get("success") is False or item.get("passed") is False or FAIL_WORDS.search(item_text)
            name = item.get("name") or item.get("property") or item.get("test") or item.get("function") or item.get("label")
            if is_failure and name:
                affected_file, affected_line, affected_column = _location_from_dict(item)
                category = "counterexample" if re.search(r"(?i)(counterexample|transactions|sequence)", item_text) else "echidna_property_failure"
                findings.append(_make_finding(
                    source_tool="echidna",
                    title=f"Echidna Property Failed: {name}",
                    description="User-supplied Echidna artifact reports a failing/falsified property or counterexample. This evidence should be treated as a launch blocker until reproduced and fixed.",
                    evidence=item,
                    severity=_safe_severity(item.get("severity"), "critical" if category == "counterexample" else "high"),
                    category=category,
                    affected_file=affected_file,
                    affected_line=affected_line,
                    affected_column=affected_column,
                ))
    else:
        for position, match in enumerate(FAIL_WORDS.finditer(raw), start=1):
            start = max(0, match.start() - 500)
            end = min(len(raw), match.end() + 900)
            window = raw[start:end]
            affected_file, affected_line, affected_column = _location_from_text(window)
            findings.append(_make_finding(
                source_tool="echidna",
                title=f"Echidna Failure Evidence: failure-{position}",
                description="User-supplied Echidna text output contains a failure/counterexample signal. Web3Guard parsed supplied evidence only.",
                evidence=window,
                severity="critical" if "counterexample" in window.lower() else "high",
                category="counterexample" if "counterexample" in window.lower() else "echidna_property_failure",
                affected_file=affected_file,
                affected_line=affected_line,
                affected_column=affected_column,
            ))
    return _unique_findings(findings), {
        "state": "Assessed",
        "artifact_type": "echidna",
        "raw_format": "json" if parsed is not None else "text",
        "failure_count": len(_unique_findings(findings)),
        "parsed": True,
        "top_level_type": type(source).__name__,
    }


def parse_invariant_artifact(raw: str | None) -> tuple[list[Finding], dict[str, Any]]:
    if not raw or not raw.strip():
        return [], {"state": "Not Assessed", "reason": "No invariant artifact supplied."}
    parsed = _json_load(raw)
    if parsed is None:
        return [], {"state": "Manual Review Required", "reason": "Invariant artifact was supplied but is not valid JSON.", "parsed": False}
    findings: list[Finding] = []
    for item in _iter_dicts(parsed):
        item_text = _short(item, 2200)
        status = str(item.get("status") or item.get("result") or item.get("state") or "").lower()
        failed = item.get("passed") is False or item.get("success") is False or status in {"failed", "fail", "failing", "broken", "violated", "false"} or bool(item.get("failed")) or FAIL_WORDS.search(item_text)
        name = item.get("name") or item.get("invariant") or item.get("property") or item.get("scenario") or item.get("id")
        if failed and name:
            affected_file, affected_line, affected_column = _location_from_dict(item)
            severity = _safe_severity(item.get("severity"), "critical" if re.search(r"(?i)(insolvent|drain|fund|accounting|supply|collateral|oracle)", item_text) else "high")
            findings.append(_make_finding(
                source_tool="invariant_artifact",
                title=f"Invariant Failed: {name}",
                description="User-supplied invariant/simulation artifact reports a failed property. This is evidence for manual triage and retest before launch.",
                evidence=item,
                severity=severity,
                category="invariant_failure",
                rule_id=f"W3G-INVARIANT-{_sha(str(name))[:8]}",
                affected_file=affected_file,
                affected_line=affected_line,
                affected_column=affected_column,
                fix=str(item.get("fix") or item.get("recommendation") or _fix_for_tool("invariant_artifact", "invariant_failure")),
            ))
    return _unique_findings(findings), {
        "state": "Assessed",
        "artifact_type": "invariant_artifact",
        "raw_format": "json",
        "failure_count": len(_unique_findings(findings)),
        "parsed": True,
    }


def _unique_findings(findings: list[Finding]) -> list[Finding]:
    seen: set[str] = set()
    out: list[Finding] = []
    for finding in findings:
        key = "|".join([
            finding.rule_id or "",
            finding.title.lower(),
            finding.affected_file or "",
            str(finding.affected_line or ""),
            (finding.evidence or "")[:160],
        ])
        if key in seen:
            continue
        seen.add(key)
        out.append(finding)
    return out


def formal_fuzz_not_assessed_summary() -> dict[str, Any]:
    return {
        "state": "Not Assessed",
        "assessed": False,
        "score": None,
        "risk_label": "Not Assessed",
        "tools": [
            {"tool": "foundry", "state": "Not Assessed", "status": "not_run", "real_findings": 0},
            {"tool": "echidna", "state": "Not Assessed", "status": "not_run", "real_findings": 0},
            {"tool": "invariant_artifact", "state": "Not Assessed", "status": "not_run", "real_findings": 0},
        ],
        "findings": [],
        "status_messages": [],
        "real_only_note": "No Foundry/Echidna/invariant artifact was supplied. Web3Guard did not invent formal/fuzz results.",
        "accepted_inputs": ["foundry_test_output", "echidna_output_json", "invariant_artifact_json", "defi_simulation_json"],
    }


def analyze_formal_fuzz_artifacts(
    *,
    foundry_test_output: str | None = None,
    echidna_output_json: str | None = None,
    invariant_artifact_json: str | None = None,
    defi_simulation_json: str | None = None,
    project_name: str | None = None,
) -> ScanResponse | None:
    foundry_findings, foundry_status = parse_foundry_output(foundry_test_output)
    echidna_findings, echidna_status = parse_echidna_output(echidna_output_json)
    invariant_findings, invariant_status = parse_invariant_artifact(invariant_artifact_json or defi_simulation_json)
    supplied_any = any([
        bool(foundry_test_output and foundry_test_output.strip()),
        bool(echidna_output_json and echidna_output_json.strip()),
        bool((invariant_artifact_json or defi_simulation_json or "").strip()),
    ])
    if not supplied_any:
        return None
    findings = prepare_professional_findings(foundry_findings + echidna_findings + invariant_findings, default_source_tool="formal_fuzz_artifact")
    tool_rows = [
        _tool_row("foundry", foundry_status, len(foundry_findings), bool(foundry_test_output and foundry_test_output.strip())),
        _tool_row("echidna", echidna_status, len(echidna_findings), bool(echidna_output_json and echidna_output_json.strip())),
        _tool_row("invariant_artifact", invariant_status, len(invariant_findings), bool((invariant_artifact_json or defi_simulation_json or "").strip())),
    ]
    score = score_findings(findings)
    metadata = {
        "engine": "web3guard-formal-fuzz-artifact-engine-v1",
        "artifact_trust_level": "user_supplied_evidence",
        "tool_status": tool_rows,
        "foundry": foundry_status,
        "echidna": echidna_status,
        "invariant_artifact": invariant_status,
        "formal_fuzz_summary": _summary_from_findings(findings, tool_rows),
        "real_only_note": "Foundry/Echidna/invariant results are parsed only from supplied artifacts. No fuzzing, forge execution, or exploit automation was run by this endpoint.",
        "safe_boundaries": [
            "No private keys, wallet signing, or exploit automation.",
            "No server-side Foundry/Echidna execution in this phase.",
            "Failures are evidence for triage, not a certified audit conclusion.",
        ],
    }
    return ScanResponse(
        report_id=f"W3G-FORMAL-{_sha(str(datetime.now(timezone.utc).timestamp()) + str(len(findings)))}",
        generated_at=datetime.now(timezone.utc),
        project_name=project_name,
        module_score=ModuleScore(module="deep_analysis", score=score, risk_label=risk_label(score), assessed=True),
        findings=findings,
        severity_breakdown=severity_breakdown(findings),
        priority_actions=priority_actions(findings),
        engine_version="web3guard-formal-fuzz-artifact-engine-v1",
        scan_metadata=metadata,
        disclaimer="Supplied formal/fuzz artifacts are evidence inputs for pre-audit readiness. This is not a certified audit or proof that all invariants are correct.",
    )


def _tool_row(tool: str, status: dict[str, Any], finding_count: int, supplied: bool) -> dict[str, Any]:
    if not supplied:
        state = "Not Assessed"
        run_status = "not_supplied"
    elif status.get("parsed") is False:
        state = "Manual Review Required"
        run_status = "parse_failed"
    else:
        state = "Assessed"
        run_status = "artifact_parsed"
    return {
        "tool": tool,
        "state": state,
        "status": run_status,
        "artifact_supplied": supplied,
        "real_findings": finding_count,
        "failure_count": status.get("failure_count", finding_count),
        "raw_format": status.get("raw_format"),
        "reason": status.get("reason"),
    }


def _summary_from_findings(findings: list[Finding], tools: list[dict[str, Any]]) -> dict[str, Any]:
    critical_high = sum(1 for finding in findings if finding.severity in {"critical", "high"})
    with_location = sum(1 for finding in findings if finding.affected_file or finding.affected_line)
    return {
        "assessed": any(tool.get("artifact_supplied") for tool in tools),
        "total_findings": len(findings),
        "critical_high_findings": critical_high,
        "with_file_or_line_count": with_location,
        "tools": tools,
        "evidence_rule": "Only supplied Foundry/Echidna/invariant artifacts create findings. Missing artifacts stay Not Assessed.",
        "report_ready_fields": ["source_tools", "affected_file", "affected_line", "evidence", "impact", "fix", "repro_steps", "verification_status"],
    }


def formal_fuzz_summary_from_report(report: ScanResponse | None) -> dict[str, Any]:
    if report is None:
        return formal_fuzz_not_assessed_summary()
    metadata = report.scan_metadata or {}
    findings = [f.model_dump(mode="json") if hasattr(f, "model_dump") else f.dict() for f in report.findings]
    summary = metadata.get("formal_fuzz_summary", {}) if isinstance(metadata, dict) else {}
    return {
        "state": "Assessed",
        "assessed": True,
        "score": report.module_score.score,
        "risk_label": report.module_score.risk_label,
        "report_id": report.report_id,
        "tools": (metadata.get("tool_status") or []) if isinstance(metadata, dict) else [],
        "findings": findings[:40],
        "status_messages": [],
        "summary": summary,
        "real_only_note": metadata.get("real_only_note") if isinstance(metadata, dict) else None,
        "safe_boundaries": metadata.get("safe_boundaries", []) if isinstance(metadata, dict) else [],
    }
