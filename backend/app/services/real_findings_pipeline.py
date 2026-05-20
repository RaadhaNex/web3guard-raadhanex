from __future__ import annotations

from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any

PHASE = "Phase 45 — Real Findings Pipeline Hardening"
ENGINE_VERSION = "web3guard-real-findings-pipeline-v1.0"

SEVERITY_ORDER = {"critical": 5, "high": 4, "medium": 3, "low": 2, "info": 1}
REAL_ONLY_STATES = {"Assessed", "Live", "Live safe/passive", "Live for pasted Solidity", "Live from verified explorer source"}
SAFE_GAP_STATES = {"Not Assessed", "Tool Not Installed", "Provider Not Configured", "Manual Review Required", "Manual input required", "Input rejected", "Input recorded only"}
BLOCKED_CLAIM_MARKERS = (
    "100% secure",
    "certified audit",
    "audited by web3guard",
    "audited by openzeppelin",
    "openzeppelin certified",
    "finds all bugs",
    "all vulnerabilities found",
    "guaranteed secure",
)


def _is_record(value: Any) -> bool:
    return isinstance(value, dict)


def _as_record(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _text(value: Any, fallback: str = "") -> str:
    if value is None:
        return fallback
    text = str(value).strip()
    return text if text else fallback


def _severity(value: Any) -> str:
    text = _text(value, "info").lower()
    return text if text in SEVERITY_ORDER else "info"


def _state(value: Any) -> str:
    text = _text(value, "Not Assessed")
    lowered = text.lower()
    if "tool not installed" in lowered or "not_installed" in lowered:
        return "Tool Not Installed"
    if "provider not configured" in lowered or "disabled" in lowered or "not configured" in lowered:
        return "Provider Not Configured"
    if "manual" in lowered or "completed_with_errors" in lowered:
        return "Manual Review Required"
    if "not assessed" in lowered or "not_run" in lowered:
        return "Not Assessed"
    if "live" in lowered or ("assessed" in lowered and "not" not in lowered) or "completed" in lowered:
        return "Assessed"
    return text


def _stable_key(finding: dict[str, Any], source_bucket: str) -> str:
    return "|".join([
        _text(finding.get("fingerprint")),
        _text(finding.get("id")),
        source_bucket,
        _text(finding.get("rule_id")),
        _text(finding.get("title")),
        _text(finding.get("affected_line")),
    ]).strip("|")


def _normalize_finding(raw: dict[str, Any], *, source_bucket: str, mapped_to: list[str] | None = None) -> dict[str, Any]:
    severity = _severity(raw.get("severity"))
    title = _text(raw.get("title"), "Untitled finding")
    source = _text(raw.get("source"), source_bucket)
    category = _text(raw.get("category"), "general")
    module = _text(raw.get("module"), _text(raw.get("module_key"), "unknown"))
    description = _text(raw.get("description"), "No description provided by source.")
    recommendation = _text(raw.get("recommendation"), "Review the evidence and fix before public launch.")
    is_status_message = category == "tool_status" or "not run" in title.lower() or "status" in source.lower()
    return {
        "id": _text(raw.get("id"), f"pipeline-{abs(hash((source_bucket, title, description))) % 10_000_000}"),
        "module": module,
        "severity": severity,
        "title": title,
        "description": description,
        "source": source,
        "source_bucket": source_bucket,
        "category": category,
        "rule_id": raw.get("rule_id"),
        "fingerprint": raw.get("fingerprint"),
        "affected_line": raw.get("affected_line"),
        "affected_function": raw.get("affected_function"),
        "affected_code": raw.get("affected_code"),
        "confidence": _text(raw.get("confidence"), "medium"),
        "business_impact": _text(raw.get("business_impact"), "Manual triage recommended."),
        "developer_explanation": _text(raw.get("developer_explanation"), "Review raw evidence."),
        "recommendation": recommendation,
        "references": raw.get("references") if isinstance(raw.get("references"), list) else [],
        "paid_review_recommended": bool(raw.get("paid_review_recommended")) or severity in {"critical", "high"},
        "mapped_to": mapped_to or ["results", "report"],
        "is_status_message": is_status_message,
        "raw_evidence_available": True,
        "raw_evidence": deepcopy(raw),
    }


def _collect_findings(scan_payload: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    surface = _as_record(scan_payload.get("surface_hints"))
    combined = _as_record(scan_payload.get("combined_report"))
    findings: list[dict[str, Any]] = []
    status_messages: list[dict[str, Any]] = []

    def add_many(items: list[Any], bucket: str, mapped_to: list[str] | None = None) -> None:
        for item in items:
            if not isinstance(item, dict):
                continue
            normalized = _normalize_finding(item, source_bucket=bucket, mapped_to=mapped_to)
            if normalized["is_status_message"]:
                status_messages.append(normalized)
            else:
                findings.append(normalized)

    add_many(_as_list(combined.get("top_findings")), "combined_report.top_findings", ["results", "report", "export"])

    static_analysis = _as_record(surface.get("static_analysis"))
    add_many(_as_list(static_analysis.get("findings")), "surface.static_analysis.findings", ["results", "report", "export"])
    add_many(_as_list(static_analysis.get("status_messages")), "surface.static_analysis.status_messages", ["results", "report"])

    github = _as_record(surface.get("github_dependency_risk"))
    add_many(_as_list(github.get("findings")), "surface.github_dependency_risk.findings", ["results", "report", "export"])

    api = _as_record(surface.get("api_admin_exposure"))
    add_many(_as_list(api.get("findings")), "surface.api_admin_exposure.findings", ["results", "report", "export"])

    # De-duplicate real findings without merging away status messages.
    seen: set[str] = set()
    deduped: list[dict[str, Any]] = []
    for finding in sorted(findings, key=lambda f: SEVERITY_ORDER.get(f["severity"], 0), reverse=True):
        key = _stable_key(finding, finding["source_bucket"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(finding)
    return deduped, status_messages


def _module_integrity(scan_payload: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
    cards = [item for item in _as_list(scan_payload.get("module_cards")) if isinstance(item, dict)]
    module_status: list[dict[str, Any]] = []
    issues: list[str] = []
    for card in cards:
        status = _state(card.get("status"))
        assessed = bool(card.get("assessed"))
        score = card.get("score")
        module = _text(card.get("module"), "unknown")
        findings_count = int(card.get("findings_count") or 0)
        required_input = _as_list(card.get("required_input"))
        evidence = _as_list(card.get("evidence"))
        if not assessed and score is not None:
            issues.append(f"{module} is not assessed but has score={score}; score must stay null for missing evidence.")
        if assessed and not evidence:
            issues.append(f"{module} is assessed but has no evidence list.")
        module_status.append({
            "module": module,
            "label": _text(card.get("label"), module),
            "state": status,
            "assessed": assessed,
            "score": score if assessed else None,
            "findings_count": findings_count,
            "critical_high_count": int(card.get("critical_high_count") or 0),
            "evidence_items": len(evidence),
            "required_input_items": len(required_input),
            "exportable": assessed and findings_count >= 0,
        })
    if not cards:
        issues.append("module_cards missing; Results page cannot prove module-level evidence mapping.")
    return module_status, issues


def _tool_run_integrity(scan_payload: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
    static_analysis = _as_record(_as_record(scan_payload.get("surface_hints")).get("static_analysis"))
    tools = [item for item in _as_list(static_analysis.get("tools")) if isinstance(item, dict)]
    issues: list[str] = []
    normalized_tools: list[dict[str, Any]] = []
    for tool in tools:
        state = _state(tool.get("state") or tool.get("status"))
        real_findings = int(tool.get("real_findings") or 0)
        name = _text(tool.get("tool"), "tool")
        if state in {"Tool Not Installed", "Provider Not Configured", "Not Assessed"} and real_findings > 0:
            issues.append(f"{name} has state {state} but real_findings={real_findings}; this would look like fake tool output.")
        normalized_tools.append({
            "tool": name,
            "state": state,
            "installed": bool(tool.get("installed")),
            "enabled_by_env": bool(tool.get("enabled_by_env")),
            "will_run": bool(tool.get("will_run")),
            "real_findings": real_findings,
            "returncode": tool.get("returncode"),
            "timed_out": bool(tool.get("timed_out")),
            "raw_logs_available": bool(tool.get("stderr_tail") or tool.get("stdout_tail")),
        })
    if static_analysis and not tools:
        issues.append("static_analysis surface exists but tool status list is missing.")
    return normalized_tools, issues


def _report_export_integrity(scan_payload: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    combined = _as_record(scan_payload.get("combined_report"))
    client_delivery = _as_record(combined.get("client_delivery"))
    issues: list[str] = []
    report_hash = combined.get("report_hash")
    delivery_formats = _as_list(client_delivery.get("delivery_formats"))
    has_export_payload = bool(combined.get("json_export") is not None or combined.get("markdown_report"))
    if not combined:
        issues.append("combined_report missing; report export must stay blocked.")
    if combined and not report_hash:
        issues.append("combined_report.report_hash missing; export identity is incomplete.")
    if combined and not delivery_formats:
        issues.append("client_delivery.delivery_formats missing; export UI cannot list supported formats.")
    return {
        "report_id": combined.get("report_id") or scan_payload.get("report_id"),
        "report_hash_present": bool(report_hash),
        "delivery_formats": delivery_formats,
        "json_or_markdown_payload_present": has_export_payload,
        "export_ready": bool(combined and report_hash and delivery_formats),
        "manual_payment_validation_required": bool(client_delivery.get("manual_verification_required", True)),
        "public_wording": client_delivery.get("public_wording"),
    }, issues


def _contains_unsafe_claim(summary: str, marker: str) -> bool:
    if marker not in summary:
        return False
    safe_negative_phrases = {
        "certified audit": ["not a certified audit", "no certified audit", "not certified audit", "does not replace certified audit"],
        "100% secure": ["no 100% secure", "do not claim 100% secure", "not 100% secure"],
        "all vulnerabilities found": ["do not claim all vulnerabilities found", "no all vulnerabilities found", "not all vulnerabilities found"],
        "finds all bugs": ["do not claim finds all bugs", "does not find all bugs", "not finds all bugs"],
    }
    for safe_phrase in safe_negative_phrases.get(marker, []):
        if safe_phrase in summary:
            return False
    return True


def _blocked_claim_integrity(scan_payload: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    blocked_claims = " ".join(_text(item) for item in _as_list(scan_payload.get("blocked_claims"))).lower()
    summary = " ".join([
        _text(scan_payload.get("safe_public_summary")),
        _text(scan_payload.get("disclaimer")),
        _text(_as_record(scan_payload.get("combined_report")).get("executive_summary")),
        _text(_as_record(scan_payload.get("combined_report")).get("public_summary_note")),
    ]).lower()
    for marker in BLOCKED_CLAIM_MARKERS:
        if _contains_unsafe_claim(summary, marker):
            issues.append(f"Unsafe claim marker appears in public summary/report: {marker}")
    if not any(word in blocked_claims for word in ("certified", "100%", "all vulnerabilities", "all bugs")):
        issues.append("blocked_claims does not clearly block audit/100%-secure/all-vulnerabilities wording.")
    return issues


def build_real_findings_pipeline(scan_payload: dict[str, Any]) -> dict[str, Any]:
    payload = scan_payload if isinstance(scan_payload, dict) else {}
    findings, status_messages = _collect_findings(payload)
    module_status, module_issues = _module_integrity(payload)
    tool_runs, tool_issues = _tool_run_integrity(payload)
    export_gate, export_issues = _report_export_integrity(payload)
    claim_issues = _blocked_claim_integrity(payload)

    severity_counts = Counter(f["severity"] for f in findings)
    module_counts = Counter(f["module"] for f in findings)
    source_counts = Counter(f["source_bucket"] for f in findings)
    issues = module_issues + tool_issues + export_issues + claim_issues
    blockers = [issue for issue in issues if "score must stay null" in issue or "fake" in issue.lower() or "unsafe claim" in issue.lower()]

    assessed_modules = [m for m in module_status if m["assessed"]]
    missing_modules = [m for m in module_status if not m["assessed"]]
    real_finding_count = len(findings)
    status_message_count = len(status_messages)
    pipeline_ready = not blockers and bool(module_status) and bool(payload.get("combined_report"))

    return {
        "phase": PHASE,
        "engine_version": ENGINE_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "Pipeline Passed" if pipeline_ready else "Pipeline Needs Review",
        "pipeline_ready": pipeline_ready,
        "real_only_rule": "Only normalized findings from backend/tool/repo/API evidence are treated as findings. Tool-status messages stay separate and missing evidence keeps scores null.",
        "summary": {
            "real_findings": real_finding_count,
            "tool_status_messages": status_message_count,
            "modules_assessed": len(assessed_modules),
            "modules_not_assessed": len(missing_modules),
            "critical_high_findings": severity_counts.get("critical", 0) + severity_counts.get("high", 0),
            "export_ready": export_gate["export_ready"],
            "blocker_count": len(blockers),
            "issue_count": len(issues),
        },
        "severity_breakdown": {key: severity_counts.get(key, 0) for key in ["critical", "high", "medium", "low", "info"]},
        "module_breakdown": dict(module_counts),
        "source_breakdown": dict(source_counts),
        "tool_runs": tool_runs,
        "module_status": module_status,
        "normalized_findings": findings[:80],
        "tool_status_messages": status_messages[:30],
        "export_gate": export_gate,
        "integrity": {
            "passed": pipeline_ready,
            "blockers": blockers,
            "issues": issues,
            "checks": [
                "module_cards present and non-assessed scores are null",
                "tool states match real_findings counts",
                "combined_report/report_hash export gate present",
                "blocked unsafe audit/security claims remain visible",
                "status messages are separated from real findings",
            ],
        },
        "next_actions": _next_actions(findings, module_status, export_gate, blockers),
        "admin_panel_note": "This validates admin/API exposure and admin-pentest evidence, but it is not a full internal Admin Panel UI for managing users/payments/reports.",
    }


def _next_actions(findings: list[dict[str, Any]], module_status: list[dict[str, Any]], export_gate: dict[str, Any], blockers: list[str]) -> list[str]:
    if blockers:
        return ["Fix pipeline blockers before showing this scan as export-ready."] + blockers[:4]
    actions: list[str] = []
    if findings:
        actions.append("Triage normalized critical/high findings first; mark false positives only after reviewing raw evidence.")
    missing = [m["label"] for m in module_status if not m["assessed"]]
    if missing:
        actions.append("Collect missing evidence for: " + ", ".join(missing[:5]))
    if not export_gate.get("export_ready"):
        actions.append("Run/attach a combined report with report_hash before enabling exports.")
    if not actions:
        actions.append("Pipeline is clean; run sample scans and tune false positives against real findings.")
    return actions
