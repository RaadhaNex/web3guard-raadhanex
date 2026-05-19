from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from app.services.launch_validation import dependency_intelligence, razorpay_readiness, slither_render_readiness
from app.services.solidity_utils import sha12
from app.services.static_analysis_tools import run_static_analysis, static_analysis_status

PHASE32_VERSION = "web3guard-scanner-result-engine-v32.0"
SAFE_STATUSES = {
    "Assessed",
    "Not assessed yet",
    "Needs API Key",
    "Tool Not Installed",
    "Provider Not Configured",
    "Manual review required",
    "Live provider unavailable",
    "Failed",
    "Timeout",
}
SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
CVE_RE = re.compile(r"CVE-\d{4}-\d{4,}", re.IGNORECASE)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _count_by_severity(findings: list[dict[str, Any]]) -> dict[str, int]:
    counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
    for item in findings:
        sev = str(item.get("severity") or "info").lower()
        counts[sev if sev in counts else "info"] += 1
    return counts


def _normalize_status(value: str | None) -> str:
    status = str(value or "Not assessed yet").strip()
    if status in SAFE_STATUSES:
        return status
    lowered = status.lower()
    if "not_installed" in lowered or "not installed" in lowered:
        return "Tool Not Installed"
    if "disabled" in lowered or "not configured" in lowered:
        return "Provider Not Configured"
    if "timeout" in lowered:
        return "Timeout"
    if "fail" in lowered or "error" in lowered:
        return "Failed"
    return "Not assessed yet"


def _confidence_from_source(source: str, severity: str = "info") -> str:
    source_lower = source.lower()
    if "slither" in source_lower or "osv" in source_lower or "cisa" in source_lower:
        return "high"
    if severity in {"critical", "high"}:
        return "medium"
    return "low"


def _finding_from_static_finding(item: dict[str, Any], index: int) -> dict[str, Any]:
    category = str(item.get("category") or "general")
    source = str(item.get("source") or "Static analysis")
    severity = str(item.get("severity") or "info").lower()
    title = str(item.get("title") or "Static analysis finding")
    return {
        "id": item.get("id") or f"static-{index:03d}",
        "module": "static_analysis",
        "kind": "tool_finding" if category != "tool_status" else "tool_status",
        "severity": severity,
        "status": "Assessed" if category != "tool_status" else _normalize_status(item.get("description")),
        "title": title,
        "description": item.get("description") or "Static analysis produced an output item.",
        "source": source,
        "rule_id": item.get("rule_id"),
        "confidence": item.get("confidence") or _confidence_from_source(source, severity),
        "evidence_id": f"EVID-STATIC-{sha12(str(item.get('fingerprint') or item.get('id') or title))}",
        "affected_line": item.get("affected_line"),
        "affected_code": item.get("affected_code"),
        "recommendation": item.get("recommendation") or "Review the tool evidence and confirm true/false positive before production use.",
        "limitation": "Static analysis is not a certified audit. False positives and false negatives are possible.",
    }


def _manual_parse_slither_json(slither_json_text: str, limit: int = 40) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    try:
        data = json.loads(slither_json_text)
    except json.JSONDecodeError as exc:
        raise ValueError("slither_json is not valid JSON") from exc

    detectors = data.get("results", {}).get("detectors", []) if isinstance(data, dict) else []
    if not isinstance(detectors, list):
        detectors = []
    findings: list[dict[str, Any]] = []
    for idx, detector in enumerate(detectors[:limit], start=1):
        if not isinstance(detector, dict):
            continue
        impact = str(detector.get("impact") or "informational").lower()
        severity = {"high": "high", "medium": "medium", "low": "low", "informational": "info", "optimization": "info"}.get(impact, "medium")
        check = str(detector.get("check") or "slither-detector")
        description = str(detector.get("description") or detector.get("markdown") or "Slither reported a potential issue.")
        line = None
        elements = detector.get("elements") or []
        if elements and isinstance(elements[0], dict):
            source_mapping = elements[0].get("source_mapping") or {}
            if isinstance(source_mapping, dict):
                lines = source_mapping.get("lines") or []
                line = lines[0] if lines else None
        findings.append({
            "id": f"user-slither-{idx:03d}",
            "module": "static_analysis",
            "kind": "tool_finding",
            "severity": severity,
            "status": "Assessed",
            "title": check.replace("-", " ").title(),
            "description": description,
            "source": "Slither user-supplied JSON output",
            "rule_id": f"SLITHER-{check}",
            "confidence": "medium",
            "evidence_id": f"EVID-USER-SLITHER-{sha12(check + description)}",
            "affected_line": line,
            "affected_code": None,
            "recommendation": "Confirm the user-supplied Slither output against a trusted local/worker run before treating this as production evidence.",
            "limitation": "This JSON was supplied by the user/API client, not generated by this Web3Guard runtime. Treat as imported evidence until verified.",
        })
    return findings, {
        "detectors_total": len(detectors),
        "parsed_findings": len(findings),
        "source": "user_supplied_slither_json",
    }


def _status_from_tool_run(tool: str, tool_runs: dict[str, Any], tool_status: dict[str, Any]) -> dict[str, Any]:
    run = tool_runs.get(tool) or {}
    status = tool_status.get(tool) or {}
    if run:
        if run.get("timed_out"):
            safe_status = "Timeout"
        elif run.get("status") == "completed":
            safe_status = "Assessed"
        elif run.get("real_findings", 0) > 0:
            safe_status = "Assessed"
        else:
            safe_status = _normalize_status(str(run.get("status") or "Failed"))
    elif not status.get("installed"):
        safe_status = "Tool Not Installed"
    elif not status.get("enabled_by_env"):
        safe_status = "Provider Not Configured"
    else:
        safe_status = "Not assessed yet"
    return {
        "tool": tool,
        "status": safe_status,
        "installed": bool(status.get("installed")),
        "enabled_by_env": bool(status.get("enabled_by_env")),
        "will_run": bool(status.get("will_run")),
        "real_findings": int(run.get("real_findings") or 0),
        "returncode": run.get("returncode"),
        "timed_out": bool(run.get("timed_out")),
        "note": "Real tool output only. Missing/disabled tools do not create fake findings.",
    }


def _dependency_findings(dep_result: dict[str, Any]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for result in dep_result.get("osv_results") or []:
        package = result.get("package") or {}
        package_name = package.get("name") or "unknown-package"
        version = package.get("version") or "version not pinned"
        for vuln in result.get("vulnerabilities") or []:
            vuln_id = vuln.get("id") or "OSV vulnerability"
            aliases = vuln.get("aliases") or []
            cve_aliases = [alias for alias in aliases if CVE_RE.match(str(alias))]
            findings.append({
                "id": f"dep-{sha12(str(package_name) + str(version) + str(vuln_id))}",
                "module": "dependency_intelligence",
                "kind": "external_advisory",
                "severity": "high" if cve_aliases else "medium",
                "status": "Assessed",
                "title": f"{package_name} matches {vuln_id}",
                "description": vuln.get("summary") or "OSV returned a known vulnerability for this dependency.",
                "source": "OSV Advisory API",
                "rule_id": vuln_id,
                "aliases": aliases,
                "package": package_name,
                "version": version,
                "confidence": "high",
                "evidence_id": f"EVID-OSV-{sha12(str(vuln_id) + str(package_name))}",
                "recommendation": "Review the advisory, upgrade to a fixed version if available, and retest before launch.",
                "limitation": "External advisory match only. It does not prove exploitability in this project without dependency usage review.",
            })
    cisa_by_cve = {str(item.get("cve") or "").upper(): item for item in dep_result.get("cisa_kev_matches") or []}
    for finding in findings:
        aliases = [str(value).upper() for value in finding.get("aliases") or []]
        matches = [cisa_by_cve[alias] for alias in aliases if alias in cisa_by_cve]
        if matches:
            finding["severity"] = "critical"
            finding["kind"] = "known_exploited_external_advisory"
            finding["cisa_kev"] = matches[0]
            finding["title"] = f"Known exploited vulnerability: {finding['title']}"
            finding["recommendation"] = "Treat as urgent. CISA KEV indicates known exploitation in the wild; prioritize upgrade/mitigation and document evidence."
    return findings


def _not_assessed_modules(static_result: dict[str, Any] | None, dep_result: dict[str, Any] | None, run_static_tools: bool) -> list[dict[str, Any]]:
    modules: list[dict[str, Any]] = []
    if not run_static_tools:
        modules.append({
            "module": "static_analysis",
            "status": "Not assessed yet",
            "reason": "Static tool run was not requested in this evaluation.",
            "enable_next": "Set run_static_tools=true and provide Solidity source. Install/configure Slither/Semgrep for real tool evidence.",
        })
    elif static_result:
        for tool in static_result.get("tool_matrix") or []:
            if tool["status"] != "Assessed":
                modules.append({
                    "module": f"static_analysis.{tool['tool']}",
                    "status": tool["status"],
                    "reason": "Tool did not produce assessed runtime output.",
                    "enable_next": f"Install/configure {tool['tool']} and re-run. Missing tools stay outside findings.",
                })
    if not dep_result or dep_result.get("status") != "Assessed":
        modules.append({
            "module": "dependency_intelligence",
            "status": dep_result.get("status") if dep_result else "Not assessed yet",
            "reason": "Live OSV/CISA dependency lookup did not run successfully.",
            "enable_next": "Provide package data and enable live_lookup plus LAUNCH_VALIDATION_NETWORK_ENABLED=true for real advisory checks.",
        })
    modules.extend([
        {
            "module": "human_audit",
            "status": "Manual review required",
            "reason": "Business logic, economic assumptions, exploitability, and false-positive triage require qualified manual review.",
            "enable_next": "Use this report as a pre-audit handoff pack, not as a certified audit.",
        },
        {
            "module": "wallet_signing",
            "status": "Manual review required",
            "reason": "Web3Guard does not collect private keys, seed phrases, mnemonics, or request wallet signatures.",
            "enable_next": "Manually review wallet UX and transaction preview copy without signing through Web3Guard.",
        },
    ])
    return modules


def _priority_actions(findings: list[dict[str, Any]], not_assessed: list[dict[str, Any]]) -> list[str]:
    actions: list[str] = []
    if any(item.get("kind") == "known_exploited_external_advisory" for item in findings):
        actions.append("Fix/mitigate CISA KEV matched dependencies first; these indicate known exploitation in the wild.")
    if any(item.get("severity") in {"critical", "high"} and item.get("module") == "static_analysis" for item in findings):
        actions.append("Triage high-impact static-analysis findings and confirm true/false positives before public launch.")
    if any(item.get("status") == "Tool Not Installed" for item in not_assessed):
        actions.append("Install missing scanner tools on the worker/runtime or keep those modules clearly Not Assessed.")
    if any(item.get("status") == "Provider Not Configured" for item in not_assessed):
        actions.append("Enable provider/API keys only when ready; do not fake provider results in reports.")
    if not actions:
        actions.append("No critical real findings were produced in this run; still complete manual review and re-run with live providers/tools before launch.")
    actions.append("Export a pilot report with assessed modules and limitations visible before sending to users/investors.")
    return actions[:6]


def scanner_results_status() -> dict[str, Any]:
    static_status = static_analysis_status()
    slither = slither_render_readiness()
    razorpay = razorpay_readiness()
    return {
        "ok": True,
        "version": PHASE32_VERSION,
        "phase": "Phase 32 — Real Scanner Result Engine + Pilot Report Sprint",
        "purpose": "Normalize real scanner/provider outputs into one accurate result and pilot report format without fake findings.",
        "input_sources": ["Solidity source", "real static-analysis runtime output", "user-supplied Slither JSON import", "package.json/packages", "OSV/CISA live lookup when enabled"],
        "static_analysis_enabled": static_status.get("static_analysis_enabled"),
        "slither_status": slither.get("status"),
        "razorpay_status": razorpay.get("status"),
        "safe_statuses": sorted(SAFE_STATUSES),
        "not_claimed": [
            "Not a certified audit",
            "Not 100% secure",
            "No fake scanner/provider/AI output",
            "No private key, seed phrase, mnemonic, or wallet signing",
            "No exploit automation or unauthorized active scanning",
        ],
    }


async def evaluate_scanner_results(
    *,
    project_name: str | None,
    solidity_code: str | None,
    file_name: str,
    tools: list[str],
    run_static_tools: bool,
    slither_json: str | None,
    package_json_text: str | None,
    packages: list[dict[str, Any]] | None,
    live_dependency_lookup: bool,
    real_only_acknowledged: bool,
) -> dict[str, Any]:
    if not real_only_acknowledged:
        raise ValueError("Real-only acknowledgement is required")
    result_id = f"WG-RESULT-{uuid4().hex[:12]}"
    static_result: dict[str, Any] | None = None
    static_findings: list[dict[str, Any]] = []
    imported_meta: dict[str, Any] | None = None

    if run_static_tools and solidity_code:
        scan = run_static_analysis(solidity_code, project_name, file_name, tools)
        dumped = scan.model_dump(mode="json")
        all_findings = [_finding_from_static_finding(item, index) for index, item in enumerate(dumped.get("findings") or [], start=1)]
        static_findings = [item for item in all_findings if item.get("kind") != "tool_status"]
        metadata = dumped.get("scan_metadata") or {}
        tool_matrix = [_status_from_tool_run(tool, metadata.get("tool_runs") or {}, metadata.get("tool_status") or {}) for tool in tools]
        static_result = {
            "status": "Assessed" if static_findings else "Not assessed yet",
            "report_id": dumped.get("report_id"),
            "module_score": dumped.get("module_score"),
            "real_finding_count": len(static_findings),
            "tool_status_items": [item for item in all_findings if item.get("kind") == "tool_status"],
            "tool_matrix": tool_matrix,
            "input_hash": dumped.get("input_hash"),
            "engine_version": dumped.get("engine_version"),
            "limitation": "Static analysis output is preliminary and requires manual triage.",
        }
    elif run_static_tools and not solidity_code:
        static_result = {
            "status": "Not assessed yet",
            "real_finding_count": 0,
            "tool_matrix": [],
            "limitation": "Static tools were requested, but no Solidity source was provided.",
        }

    if slither_json:
        imported_findings, imported_meta = _manual_parse_slither_json(slither_json)
        static_findings.extend(imported_findings)
        if not static_result:
            static_result = {
                "status": "Assessed" if imported_findings else "Not assessed yet",
                "real_finding_count": len(imported_findings),
                "tool_matrix": [{"tool": "slither", "status": "Assessed", "installed": None, "enabled_by_env": None, "will_run": None, "real_findings": len(imported_findings), "note": "Imported user-supplied Slither JSON."}],
                "limitation": "Imported JSON is not the same as a Web3Guard worker-generated run.",
            }
        else:
            static_result["real_finding_count"] = int(static_result.get("real_finding_count") or 0) + len(imported_findings)
            static_result.setdefault("tool_matrix", []).append({"tool": "slither_import", "status": "Assessed", "real_findings": len(imported_findings), "note": "Imported user-supplied Slither JSON."})

    dep_result = await dependency_intelligence(
        package_json_text=package_json_text,
        packages=packages or [],
        live_lookup=live_dependency_lookup,
        real_only_acknowledged=True,
        limit=50,
    )
    dep_findings = _dependency_findings(dep_result)
    all_findings = sorted([*static_findings, *dep_findings], key=lambda item: (SEVERITY_ORDER.get(str(item.get("severity") or "info"), 4), str(item.get("title") or "")))
    not_assessed = _not_assessed_modules(static_result, dep_result, run_static_tools)
    severity = _count_by_severity(all_findings)
    assessed_modules = []
    if static_result and static_result.get("status") == "Assessed":
        assessed_modules.append("static_analysis")
    if dep_result.get("status") == "Assessed":
        assessed_modules.append("dependency_intelligence")
    external_advisories = [item for item in all_findings if "advisory" in str(item.get("kind"))]
    tool_findings = [item for item in all_findings if item.get("kind") == "tool_finding"]
    evidence = [
        {
            "evidence_id": f"EVID-RUN-{sha12(result_id)}",
            "source": "Web3Guard result engine",
            "status": "Assessed",
            "created_at": _now_iso(),
            "input_hash": sha12((solidity_code or "") + (package_json_text or "") + (slither_json or "")),
            "limitation": "Evidence hash is local to this result payload and does not certify security.",
        }
    ]
    if imported_meta:
        evidence.append({
            "evidence_id": f"EVID-IMPORTED-SLITHER-{sha12(str(imported_meta))}",
            "source": "Imported Slither JSON",
            "status": "Assessed",
            "created_at": _now_iso(),
            "limitation": "Imported tool output should be verified by a trusted worker run before external claims.",
            "metadata": imported_meta,
        })
    pricing = razorpay_readiness()
    return {
        "ok": True,
        "version": PHASE32_VERSION,
        "result_id": result_id,
        "project_name": project_name or "Untitled Web3 project",
        "generated_at": _now_iso(),
        "overall_status": "Assessed" if assessed_modules else "Not assessed yet",
        "summary": {
            "assessed_modules": assessed_modules,
            "assessed_module_count": len(assessed_modules),
            "real_findings_count": len(all_findings),
            "tool_findings_count": len(tool_findings),
            "external_advisory_count": len(external_advisories),
            "not_assessed_count": len(not_assessed),
            "severity_breakdown": severity,
            "launch_blockers": severity["critical"] + severity["high"],
        },
        "static_analysis": static_result or {"status": "Not assessed yet", "real_finding_count": 0, "tool_matrix": [], "limitation": "No static analysis evidence in this result."},
        "dependency_intelligence": {
            "status": dep_result.get("status"),
            "package_count": dep_result.get("package_count"),
            "osv_vulnerability_count": dep_result.get("osv_vulnerability_count", 0),
            "cisa_kev_matches": dep_result.get("cisa_kev_matches", []),
            "network_enabled": dep_result.get("network_enabled"),
            "limitation": dep_result.get("real_only_note"),
        },
        "findings": all_findings[:90],
        "not_assessed_modules": not_assessed,
        "evidence": evidence,
        "priority_actions": _priority_actions(all_findings, not_assessed),
        "pilot_report_cta": {
            "label": "Generate pilot report",
            "href": "/report/pilot",
            "paid_cta": "Unlock full launch readiness report — ₹999",
            "payment_status": pricing.get("status"),
            "payment_next_step": "Start test checkout" if pricing.get("status") == "Ready" else "Payment provider not configured",
        },
        "disclaimer": "Pre-audit readiness result only. Not a certified audit, not 100% secure, and not a replacement for qualified manual review.",
    }


def build_pilot_report(result: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(result, dict):
        raise ValueError("result payload is required")
    project_name = result.get("project_name") or "Untitled Web3 project"
    findings = result.get("findings") or []
    not_assessed = result.get("not_assessed_modules") or []
    report_id = f"WG-PILOT-{uuid4().hex[:12]}"
    assessed = result.get("summary", {}).get("assessed_modules", []) if isinstance(result.get("summary"), dict) else []
    report = {
        "ok": True,
        "version": PHASE32_VERSION,
        "report_id": report_id,
        "project_name": project_name,
        "generated_at": _now_iso(),
        "report_type": "pilot_pre_audit_readiness_report",
        "executive_summary": {
            "real_findings_count": len(findings),
            "assessed_modules": assessed,
            "not_assessed_count": len(not_assessed),
            "headline": "This report summarizes available pre-audit readiness evidence. It is not a certified audit or security guarantee.",
        },
        "scope": {
            "included": assessed,
            "not_assessed": [item.get("module") for item in not_assessed],
            "authorization_boundary": "Only user-provided or authorized passive inputs should be assessed.",
        },
        "findings": findings[:60],
        "not_assessed_modules": not_assessed,
        "fix_plan": result.get("priority_actions") or [],
        "evidence": result.get("evidence") or [],
        "limitations": [
            "This is a pre-audit readiness report, not a certified audit.",
            "Static-analysis and advisory results can include false positives and false negatives.",
            "Not Assessed modules must not be presented as passed.",
            "Web3Guard does not collect private keys, seed phrases, mnemonics, or wallet signatures.",
            "No exploit automation or unauthorized active scanning is performed.",
        ],
        "safe_wording": {
            "allowed": ["pre-audit readiness", "static analysis finding", "external advisory match", "manual review required"],
            "blocked": ["100% secure", "certified audit", "audited by Web3Guard", "guaranteed safe"],
        },
        "export_note": "Use this pilot report for founder/user feedback and auditor handoff prep. Keep limitations visible.",
    }
    report["report_hash"] = sha12(json.dumps(report, sort_keys=True, default=str))
    return report
