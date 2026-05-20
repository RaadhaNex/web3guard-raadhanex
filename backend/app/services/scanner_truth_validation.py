from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Any

ENGINE_VERSION = "web3guard-scanner-truth-validation-v1.0"

SAFE_STATES = {
    "Assessed",
    "Live",
    "Live safe/passive",
    "Live for pasted Solidity",
    "Live from verified explorer source",
    "Live limited hints",
    "Not Assessed",
    "Not assessed",
    "Tool Not Installed",
    "Provider Not Configured",
    "Needs API Key",
    "Manual",
    "Manual Review Required",
    "Manual input required",
    "Input recorded only",
    "Input rejected",
}

BANNED_CLAIM_PATTERNS = [
    ("100_percent_secure", re.compile(r"100\s*%\s*(secure|safe|protected)", re.I)),
    ("certified_audit", re.compile(r"certified\s+audit|audit\s+certified|certified\s+secure", re.I)),
    ("audited_by_web3guard", re.compile(r"audited\s+by\s+web3guard", re.I)),
    ("all_bugs_found", re.compile(r"(all|every)\s+(bugs?|vulnerabilit(?:y|ies))\s+(found|detected)", re.I)),
    ("guaranteed_security", re.compile(r"guarantee(?:d)?\s+(security|safe|secure)", re.I)),
    ("official_openzeppelin", re.compile(r"official\s+openzeppelin|openzeppelin\s+(certified|partner|audited)", re.I)),
]

REQUIRED_UNIFIED_KEYS = [
    "report_id",
    "generated_at",
    "website_url",
    "module_cards",
    "combined_report",
    "surface_hints",
    "safe_public_summary",
    "blocked_claims",
    "disclaimer",
]


def scanner_truth_validation_status() -> dict[str, Any]:
    return {
        "ok": True,
        "phase": "Phase 44 — Scanner Truth Validation",
        "version": ENGINE_VERSION,
        "purpose": "Verify that scanner output is backed by real evidence, clear missing-state labels, and report/result mapping before public beta demos.",
        "what_this_does": [
            "Checks latest unified scan payload shape and required keys.",
            "Checks module cards for Assessed vs Not Assessed truthfulness.",
            "Checks static-analysis, GitHub dependency, and API/admin surface hints for fake-output risk.",
            "Checks combined report/export readiness without claiming certified audit or 100% security.",
            "Produces blockers, warnings, passed checks, and a manual sample validation plan.",
        ],
        "what_this_does_not_do": [
            "It does not install Slither, Semgrep, OSV, or any scanner tool.",
            "It does not run exploit automation, brute force, credential stuffing, DoS, wallet signing, or private-key collection.",
            "It does not certify the project or prove that all bugs were found.",
        ],
        "safe_states": sorted(SAFE_STATES),
        "required_disclaimer": "Pre-audit readiness only. Not a certified audit. No security guarantee. Does not replace professional security review.",
    }


def _is_record(value: Any) -> bool:
    return isinstance(value, dict)


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _as_str(value: Any, fallback: str = "") -> str:
    return value if isinstance(value, str) and value else fallback


def _safe_json_text(value: Any) -> str:
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
    except Exception:
        return str(value)


def _add(issue_list: list[dict[str, Any]], severity: str, title: str, detail: str, action: str, path: str = "") -> None:
    issue_list.append({
        "severity": severity,
        "title": title,
        "detail": detail,
        "action": action,
        "path": path,
    })


def _module_evidence_state(card: dict[str, Any]) -> str:
    status = _as_str(card.get("status"), "Not Assessed")
    assessed = bool(card.get("assessed"))
    score = card.get("score")
    evidence = _as_list(card.get("evidence"))
    required_input = _as_list(card.get("required_input"))
    limitations = _as_list(card.get("limitations"))

    if assessed and isinstance(score, (int, float)) and evidence:
        return "scored_with_evidence"
    if assessed and not evidence:
        return "scored_without_clear_evidence"
    if not assessed and score is None and (required_input or limitations):
        return "missing_state_explained"
    if not assessed and score is None:
        return "missing_state_needs_detail"
    if not assessed and score is not None:
        return "fake_score_risk"
    if status in SAFE_STATES:
        return "safe_state_recorded"
    return "unclear_state"


def _validate_required_shape(result: dict[str, Any], blockers: list[dict[str, Any]], passed: list[str]) -> None:
    for key in REQUIRED_UNIFIED_KEYS:
        if key not in result:
            _add(blockers, "critical", "Unified scan result missing required key", f"Missing `{key}` from latest scan payload.", "Run unified scanner again or fix result persistence/mapping.", key)
        else:
            passed.append(f"Required unified key present: {key}")

    if not isinstance(result.get("module_cards"), list):
        _add(blockers, "critical", "Module cards are not available", "`module_cards` must be a list so Results page can show assessed/missing modules.", "Fix unified scan response shape before demo.", "module_cards")
    if not isinstance(result.get("combined_report"), dict):
        _add(blockers, "critical", "Combined report is not available", "`combined_report` must be present for report/export workflow.", "Fix report-builder mapping before demo.", "combined_report")
    if not isinstance(result.get("surface_hints"), dict):
        _add(blockers, "high", "Surface hints are not available", "`surface_hints` is required for static-analysis/API/GitHub truth checks.", "Fix unified scan response mapping.", "surface_hints")


def _validate_claims(result: dict[str, Any], blockers: list[dict[str, Any]], warnings: list[dict[str, Any]], passed: list[str]) -> None:
    text = _safe_json_text(result)
    for claim_id, pattern in BANNED_CLAIM_PATTERNS:
        for match in pattern.finditer(text):
            context = text[max(0, match.start() - 80): min(len(text), match.end() + 80)].lower()
            if any(safe_negation in context for safe_negation in ["not a certified audit", "not certified audit", "not a security guarantee", "no security guarantee", "do not say", "do not claim", "does not replace"]):
                continue
            _add(blockers, "critical", "Blocked/fake security claim detected", f"Detected banned claim pattern `{claim_id}` in scanner/report payload.", "Replace with pre-audit readiness wording and keep limitations visible.", "payload_text")
            break
    disclaimers = " ".join([
        _as_str(result.get("safe_public_summary")),
        _as_str(result.get("disclaimer")),
        _as_str(result.get("realness_rule")),
    ]).lower()
    required_phrases = ["preliminary", "not a certified audit"]
    if not all(phrase in disclaimers for phrase in required_phrases):
        _add(warnings, "medium", "Disclaimer should be stronger", "Payload should clearly state preliminary/pre-audit and not-certified-audit wording.", "Keep public copy aligned with Web3Guard safety wording.", "disclaimer")
    else:
        passed.append("Safety disclaimer wording is present.")


def _validate_module_cards(result: dict[str, Any], blockers: list[dict[str, Any]], warnings: list[dict[str, Any]], passed: list[str]) -> list[dict[str, Any]]:
    table: list[dict[str, Any]] = []
    cards = _as_list(result.get("module_cards"))
    seen_modules: set[str] = set()
    for index, raw in enumerate(cards):
        if not isinstance(raw, dict):
            _add(warnings, "medium", "Invalid module card", f"Module card at index {index} is not an object.", "Normalize module_cards to objects.", f"module_cards[{index}]")
            continue
        module = _as_str(raw.get("module"), f"module_{index}")
        seen_modules.add(module)
        state = _module_evidence_state(raw)
        assessed = bool(raw.get("assessed"))
        score = raw.get("score")
        status = _as_str(raw.get("status"), "Not Assessed")
        findings_count = raw.get("findings_count", 0)
        issue_count = 0
        action = "Ready"

        if state == "fake_score_risk":
            issue_count += 1
            action = "Remove score until evidence exists"
            _add(blockers, "critical", "Unassessed module has a score", f"Module `{module}` is not assessed but still has score `{score}`.", "Set score to null and show Not Assessed/Manual/Needs API Key state.", f"module_cards[{index}]")
        elif state == "scored_without_clear_evidence":
            issue_count += 1
            action = "Add clear evidence lines"
            _add(warnings, "high", "Assessed module lacks evidence", f"Module `{module}` is assessed but evidence list is empty.", "Show the exact real source used for assessment.", f"module_cards[{index}].evidence")
        elif state == "missing_state_needs_detail":
            issue_count += 1
            action = "Explain required input/limitation"
            _add(warnings, "medium", "Missing module state lacks explanation", f"Module `{module}` is not assessed but has no required_input or limitation.", "Add required evidence and limitation copy.", f"module_cards[{index}]")
        else:
            passed.append(f"Module `{module}` truth state looks acceptable: {state}")

        if status not in SAFE_STATES and not assessed:
            _add(warnings, "low", "Non-standard status label", f"Module `{module}` uses status `{status}`.", "Prefer Assessed / Not Assessed / Tool Not Installed / Needs API Key / Provider Not Configured / Manual Review Required.", f"module_cards[{index}].status")

        table.append({
            "surface": module,
            "label": raw.get("label") or module,
            "status": status,
            "assessed": assessed,
            "score": score,
            "evidence_state": state,
            "findings_count": findings_count,
            "critical_high_count": raw.get("critical_high_count", 0),
            "issue_count": issue_count,
            "action": action,
        })

    expected = {"website", "dapp", "api", "contract", "static_analysis", "wallet", "admin_opsec", "github"}
    missing_expected = sorted(expected - seen_modules)
    if missing_expected:
        _add(warnings, "medium", "Expected surface cards are missing", f"Missing module cards: {', '.join(missing_expected)}.", "Keep every major surface visible even when Not Assessed.", "module_cards")
    else:
        passed.append("All expected unified surfaces have module cards.")

    return table


def _validate_static_truth(surface_hints: dict[str, Any], blockers: list[dict[str, Any]], warnings: list[dict[str, Any]], passed: list[str]) -> dict[str, Any]:
    static = surface_hints.get("static_analysis") if isinstance(surface_hints, dict) else None
    if not isinstance(static, dict):
        _add(warnings, "medium", "Static-analysis truth block missing", "surface_hints.static_analysis is missing.", "Map Slither/Semgrep status from unified scan into surface_hints.static_analysis.", "surface_hints.static_analysis")
        return {"state": "Not Assessed", "tools": []}

    tools = _as_list(static.get("tools"))
    fake_risk = False
    for index, tool in enumerate(tools):
        if not isinstance(tool, dict):
            continue
        state = _as_str(tool.get("state"), "Not Assessed")
        status = _as_str(tool.get("status"), "not_run")
        findings = tool.get("real_findings", 0) or 0
        installed = bool(tool.get("installed"))
        if state == "Assessed" and status not in {"completed", "completed_with_errors"}:
            fake_risk = True
            _add(blockers, "critical", "Static tool marked assessed without completed run", f"Tool `{tool.get('tool')}` state is Assessed but status is `{status}`.", "Only show Assessed after a real completed tool run.", f"surface_hints.static_analysis.tools[{index}]")
        if not installed and findings:
            fake_risk = True
            _add(blockers, "critical", "Static tool has findings while not installed", f"Tool `{tool.get('tool')}` reports findings but installed=false.", "Remove fake findings or fix installed/tool-run state.", f"surface_hints.static_analysis.tools[{index}]")
    if not fake_risk:
        passed.append("Static-analysis state does not show fake Slither/Semgrep findings.")
    return {"state": static.get("state"), "tools": tools, "assessed": static.get("assessed")}


def _validate_github_truth(surface_hints: dict[str, Any], warnings: list[dict[str, Any]], passed: list[str]) -> dict[str, Any]:
    github = surface_hints.get("github_dependency_risk") if isinstance(surface_hints, dict) else None
    if not isinstance(github, dict):
        _add(warnings, "medium", "GitHub dependency truth block missing", "surface_hints.github_dependency_risk is missing.", "Map public repo/dependency manifest state into surface hints.", "surface_hints.github_dependency_risk")
        return {"state": "Not Assessed"}
    state = _as_str(github.get("state"), "Not Assessed")
    manifests = _as_list(github.get("dependency_manifests"))
    osv_state = _as_str(github.get("osv_state"), "Provider Not Configured")
    if state == "Assessed" and not manifests:
        _add(warnings, "medium", "GitHub assessed but no dependency manifests", "Repo may be assessed for hygiene, but dependency-risk proof is weak without package/lock manifests.", "Show repo hygiene separately from dependency vulnerability lookup.", "surface_hints.github_dependency_risk")
    else:
        passed.append("GitHub dependency state is explicit and does not fake OSV lookup.")
    return {"state": state, "manifest_count": len(manifests), "osv_state": osv_state}


def _validate_api_truth(surface_hints: dict[str, Any], warnings: list[dict[str, Any]], passed: list[str]) -> dict[str, Any]:
    api = surface_hints.get("api_admin_exposure") if isinstance(surface_hints, dict) else None
    if not isinstance(api, dict):
        _add(warnings, "medium", "API/admin truth block missing", "surface_hints.api_admin_exposure is missing.", "Map safe passive API/admin checks into surface hints.", "surface_hints.api_admin_exposure")
        return {"state": "Not Assessed"}
    state = _as_str(api.get("state"), "Not Assessed")
    controls = api.get("safety_controls") if isinstance(api.get("safety_controls"), dict) else {}
    if state == "Assessed" and any(controls.get(k) is False for k in ["no_fuzzing", "no_auth_bypass", "no_payload_spraying"]):
        _add(warnings, "high", "API/admin safety controls need review", "Passive API/admin checks should keep fuzzing/auth-bypass/payload-spraying disabled.", "Keep DAST/admin checks safe and authorized only.", "surface_hints.api_admin_exposure.safety_controls")
    else:
        passed.append("API/admin exposure state keeps passive/safe controls visible.")
    return {"state": state, "safe_endpoints_checked": len(_as_list(api.get("safe_endpoints_checked"))), "safety_controls": controls}


def _validate_report_mapping(result: dict[str, Any], blockers: list[dict[str, Any]], warnings: list[dict[str, Any]], passed: list[str]) -> dict[str, Any]:
    report = result.get("combined_report") if isinstance(result.get("combined_report"), dict) else {}
    coverage = report.get("coverage") if isinstance(report.get("coverage"), dict) else {}
    delivery = report.get("client_delivery") if isinstance(report.get("client_delivery"), dict) else {}
    formats = _as_list(delivery.get("delivery_formats"))
    markdown = _as_str(report.get("markdown_report"))
    json_export = report.get("json_export")
    module_matrix = _as_list(report.get("module_matrix"))
    priority_plan = _as_list(report.get("priority_action_plan"))

    if not module_matrix:
        _add(blockers, "high", "Report module matrix missing", "Report page cannot prove module mapping without module_matrix.", "Map module_cards/ScanResponse modules into combined report matrix.", "combined_report.module_matrix")
    else:
        passed.append("Combined report module matrix is present.")
    if not markdown:
        _add(warnings, "medium", "Markdown report missing", "Report export should include markdown_report.", "Ensure report builder returns markdown_report from real scan data.", "combined_report.markdown_report")
    else:
        passed.append("Markdown report is present for export flow.")
    if not isinstance(json_export, dict):
        _add(warnings, "low", "JSON export payload missing", "JSON export is optional but useful for audit handoff.", "Include json_export when possible.", "combined_report.json_export")
    else:
        passed.append("JSON export object is present.")
    if not formats:
        _add(warnings, "medium", "Delivery formats missing", "Report/export UI should list PDF/HTML/MD/JSON states clearly.", "Populate client_delivery.delivery_formats.", "combined_report.client_delivery.delivery_formats")
    if not priority_plan:
        _add(warnings, "medium", "Priority action plan empty", "Founder report should show what to fix first.", "Map real findings into priority_action_plan; if no findings, show evidence-complete/no-finding caveat.", "combined_report.priority_action_plan")

    assessed_count = coverage.get("assessed_count")
    total_modules = coverage.get("total_modules")
    confidence = _as_str(coverage.get("confidence"), "")
    return {
        "coverage": coverage,
        "assessed_count": assessed_count,
        "total_modules": total_modules,
        "coverage_confidence": confidence,
        "delivery_formats": formats,
        "has_markdown_report": bool(markdown),
        "has_json_export": isinstance(json_export, dict),
        "module_matrix_count": len(module_matrix),
        "priority_action_count": len(priority_plan),
    }


def _score_result(blockers: list[dict[str, Any]], warnings: list[dict[str, Any]], passed: list[str]) -> tuple[int, str]:
    score = 100
    score -= sum(30 for item in blockers if item.get("severity") == "critical")
    score -= sum(18 for item in blockers if item.get("severity") == "high")
    score -= sum(12 for item in warnings if item.get("severity") == "high")
    score -= sum(7 for item in warnings if item.get("severity") == "medium")
    score -= sum(3 for item in warnings if item.get("severity") == "low")
    score = max(0, min(100, score))
    if any(item.get("severity") == "critical" for item in blockers):
        verdict = "Not demo-ready — truth blockers found"
    elif score >= 85:
        verdict = "Beta proof-ready"
    elif score >= 70:
        verdict = "Usable, but fix warnings before public demo"
    else:
        verdict = "Needs QA before demo"
    return score, verdict


def scanner_truth_sample_plan() -> dict[str, Any]:
    return {
        "ok": True,
        "phase": "Phase 44 — Scanner Truth Validation",
        "sample_validation_plan": [
            {
                "id": "sample_solidity_static",
                "title": "Solidity source → Slither/Semgrep truth path",
                "steps": [
                    "Run unified scanner with pasted Solidity source.",
                    "Confirm contract module is Assessed by local rule engine.",
                    "Confirm static_analysis shows Assessed only if Slither/Semgrep completed; otherwise Tool Not Installed/Provider Not Configured.",
                    "Open Results and Report; verify exact static-analysis state is visible without fake findings.",
                ],
                "pass_condition": "No fake Slither/Semgrep results. Missing tool is clearly marked as Tool Not Installed/Provider Not Configured.",
            },
            {
                "id": "sample_github_dependency",
                "title": "GitHub repo → dependency truth path",
                "steps": [
                    "Run unified scanner with a public GitHub repo URL.",
                    "Confirm repo hygiene and dependency manifest count are shown.",
                    "Confirm OSV/provider state is explicit and not faked.",
                    "Open Report; verify dependency findings are separated from Not Assessed/provider states.",
                ],
                "pass_condition": "Dependency risk is based on real manifest/provider data or shown as Provider Not Configured/Not Assessed.",
            },
            {
                "id": "sample_api_admin",
                "title": "API/admin passive evidence path",
                "steps": [
                    "Run unified scanner with API base URL that you are authorized to test.",
                    "Confirm no brute force, DoS, exploit payload, credential stuffing, or auth bypass is attempted.",
                    "Confirm safe endpoints checked, CORS/security/auth/webhook hints show exact evidence.",
                    "Open Results and Report; verify API/admin limitations are visible.",
                ],
                "pass_condition": "Only passive/safe checks appear; missing evidence remains Manual Review Required/Not Assessed.",
            },
            {
                "id": "sample_report_unlock",
                "title": "Report/export + paid flow truth path",
                "steps": [
                    "Run unified scanner and open Report.",
                    "Confirm report uses current scan data only.",
                    "Confirm export/pilot copy does not claim payment success unless backend/manual validation is verified.",
                    "Confirm PDF/HTML/MD/JSON buttons are clean and disabled/gated when needed.",
                ],
                "pass_condition": "No fake payment success and no fake audit claim. Export is linked to real scan/report payload.",
            },
        ],
        "real_only_note": "This plan validates existing scanner truthfulness. It does not add new scanner claims or new exploit capability.",
    }


def validate_scanner_truth(payload: dict[str, Any]) -> dict[str, Any]:
    if not payload.get("real_only_acknowledged", True):
        raise ValueError("Real-only acknowledgement is required")
    result = payload.get("unified_scan_result") or payload.get("result") or {}
    if not isinstance(result, dict) or not result:
        raise ValueError("A unified scan result payload is required")

    blockers: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    passed: list[str] = []

    _validate_required_shape(result, blockers, passed)
    _validate_claims(result, blockers, warnings, passed)
    module_table = _validate_module_cards(result, blockers, warnings, passed)
    surface_hints = result.get("surface_hints") if isinstance(result.get("surface_hints"), dict) else {}
    static_truth = _validate_static_truth(surface_hints, blockers, warnings, passed)
    github_truth = _validate_github_truth(surface_hints, warnings, passed)
    api_truth = _validate_api_truth(surface_hints, warnings, passed)
    report_mapping = _validate_report_mapping(result, blockers, warnings, passed)
    truth_score, verdict = _score_result(blockers, warnings, passed)

    return {
        "ok": True,
        "phase": "Phase 44 — Scanner Truth Validation",
        "engine_version": ENGINE_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "project_name": payload.get("project_name") or result.get("project_name") or "Latest scan",
        "report_id": result.get("report_id"),
        "truth_score": truth_score,
        "verdict": verdict,
        "blockers": blockers,
        "warnings": warnings,
        "passed_checks": passed[:80],
        "module_truth_table": module_table,
        "surface_truth": {
            "static_analysis": static_truth,
            "github_dependency": github_truth,
            "api_admin_exposure": api_truth,
        },
        "report_mapping": report_mapping,
        "next_actions": _next_actions(blockers, warnings),
        "manual_sample_plan": scanner_truth_sample_plan()["sample_validation_plan"],
        "safe_public_summary": "This validates scanner truth mapping only. It is not a certified audit, not a penetration test, and not a guarantee of security.",
        "blocked_claims": [claim for claim, _pattern in BANNED_CLAIM_PATTERNS],
    }


def _next_actions(blockers: list[dict[str, Any]], warnings: list[dict[str, Any]]) -> list[str]:
    if blockers:
        return [
            "Fix critical truth blockers before public demo or investor screenshots.",
            "Do not show scored modules unless they are backed by real evidence.",
            "Keep Results and Report pages aligned to the same latest unified scan payload.",
        ]
    actions = []
    if warnings:
        actions.append("Fix warning-level gaps before publishing sample reports.")
    actions.extend([
        "Run one Solidity sample, one GitHub sample, one API/admin sample, and one report/export sample.",
        "Save screenshots/report artifacts for beta proof and false-positive tuning.",
        "Use the truth score as internal QA only, not as a security score for customers.",
    ])
    return actions
