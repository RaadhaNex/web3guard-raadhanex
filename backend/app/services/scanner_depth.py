from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.core.config import settings
from app.services.worker_execution import worker_execution_status

PHASE38_VERSION = "web3guard-scanner-depth-hardening-v38.0"
MAX_AUTOMATED_PREAUDIT_COVERAGE = 90
SAFE_STATUS_LABELS = [
    "Assessed",
    "Not assessed yet",
    "Tool Not Installed",
    "Provider Not Configured",
    "Needs API Key",
    "Manual review required",
    "Timeout",
    "Failed",
]
BLOCKED_CLAIMS = [
    "90-99% security guaranteed",
    "100% secure",
    "certified audit",
    "audited by Web3Guard",
    "all vulnerabilities found",
    "exploit automation",
    "wallet signing",
]

WEIGHTS = {
    "slither_static": 14,
    "aderyn_static": 4,
    "semgrep_app_api": 14,
    "osv_advisory": 10,
    "cisa_kev": 6,
    "github_hygiene": 10,
    "website_surface": 4,
    "api_surface": 4,
    "wallet_ux_surface": 4,
    "admin_opsec_surface": 4,
    "foundry_tests": 8,
    "echidna_fuzz": 6,
    "mythril_symbolic": 5,
    "evidence_report": 7,
}

KEY_LABELS = {
    "slither_static": "Slither real static analysis",
    "aderyn_static": "Aderyn static analysis",
    "semgrep_app_api": "Semgrep app/API/code scan",
    "osv_advisory": "OSV dependency advisory lookup",
    "cisa_kev": "CISA KEV exploited-in-the-wild matching",
    "github_hygiene": "GitHub repository hygiene",
    "website_surface": "Website security headers/config review",
    "api_surface": "API/OpenAPI readiness review",
    "wallet_ux_surface": "Wallet UX/manual safety review",
    "admin_opsec_surface": "Admin OpSec/manual safety review",
    "foundry_tests": "Foundry test execution evidence",
    "echidna_fuzz": "Echidna invariant/fuzz evidence",
    "mythril_symbolic": "Mythril Docker symbolic-analysis evidence",
    "evidence_report": "Evidence ledger + pilot report completeness",
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _truthy(data: dict[str, Any], key: str) -> bool:
    return bool(data.get(key) is True or str(data.get(key, "")).strip().lower() in {"true", "yes", "assessed", "ready"})


def _int(data: dict[str, Any], key: str, default: int = 0) -> int:
    try:
        return max(0, int(data.get(key, default) or 0))
    except (TypeError, ValueError):
        return default


def _tool_by_key() -> dict[str, dict[str, Any]]:
    return {item["key"]: item for item in worker_execution_status().get("tools", [])}


def _worker_readiness_items() -> list[dict[str, Any]]:
    tools = _tool_by_key()
    rows: list[dict[str, Any]] = []
    for tool in ["slither", "aderyn", "semgrep", "foundry", "echidna", "mythril"]:
        item = tools.get(tool, {})
        rows.append({
            "tool": tool,
            "status": item.get("status", "Not assessed yet"),
            "installed": bool(item.get("installed")),
            "will_run": bool(item.get("will_run")),
            "enabled_by_env": bool(item.get("enabled_by_env")),
            "next_action": item.get("next_action") or "Configure this worker before counting it toward coverage.",
        })
    return rows


def scanner_depth_status() -> dict[str, Any]:
    worker_status = worker_execution_status()
    ready_tools = [tool["key"] for tool in worker_status.get("tools", []) if tool.get("status") == "Ready"]
    return {
        "ok": True,
        "version": PHASE38_VERSION,
        "target": "Raise Web3Guard to about 90% pre-audit scanner coverage depth for a narrow, evidence-backed scope — not 90% security guarantee.",
        "max_automated_pre_audit_coverage": MAX_AUTOMATED_PREAUDIT_COVERAGE,
        "security_guarantee_percent": 0,
        "ready_worker_tools": ready_tools,
        "worker_readiness": _worker_readiness_items(),
        "network_advisory_ready": bool(settings.launch_validation_network_enabled or settings.provider_live_advisory_sources_enabled),
        "recommended_env_for_90_depth": [
            "STATIC_ANALYSIS_ENABLED=true",
            "SLITHER_ENABLED=true",
            "SEMGREP_ENABLED=true",
            "WORKER_EXECUTION_ENABLED=true",
            "FOUNDRY_ENABLED=true",
            "DEEP_ANALYSIS_ENABLED=true",
            "ECHIDNA_ENABLED=true only with real config/properties",
            "MYTHRIL_ENABLED=true + MYTHRIL_DOCKER_ENABLED=true + MYTHRIL_DOCKER_IMAGE=<real image>",
            "LAUNCH_VALIDATION_NETWORK_ENABLED=true for OSV/CISA checks",
        ],
        "safe_status_labels": SAFE_STATUS_LABELS,
        "blocked_claims": BLOCKED_CLAIMS,
        "not_claimed": [
            "Not a certified audit",
            "No 99% security guarantee",
            "No wallet signing",
            "No private key / seed phrase / mnemonic collection",
            "No unauthorized active scanning",
            "No fake scanner output",
        ],
    }


def _coverage_item(key: str, assessed: bool, evidence: str, status_override: str | None = None) -> dict[str, Any]:
    points = WEIGHTS[key] if assessed else 0
    return {
        "key": key,
        "label": KEY_LABELS[key],
        "status": status_override or ("Assessed" if assessed else "Not assessed yet"),
        "weight": WEIGHTS[key],
        "points": points,
        "evidence": evidence if assessed else "No real evidence counted for this module yet.",
        "next_action": _next_action_for_key(key),
    }


def _next_action_for_key(key: str) -> str:
    return {
        "slither_static": "Run real Slither JSON through the worker. Missing Slither must remain Tool Not Installed.",
        "aderyn_static": "Enable Aderyn only when installed and parsed; otherwise keep Not assessed.",
        "semgrep_app_api": "Run Semgrep rules against the frontend/backend/API workspace; parse JSON output.",
        "osv_advisory": "Enable OSV batch lookup against package.json/lockfile dependency data.",
        "cisa_kev": "Match OSV CVE aliases against the CISA KEV catalog; treat matches as urgent external advisories.",
        "github_hygiene": "Run read-only GitHub repo hygiene checks with a real repo/token if needed.",
        "website_surface": "Run passive website/header/config checks only for owned/authorized URLs.",
        "api_surface": "Analyze user-provided API/OpenAPI metadata; avoid unauthorized active scanning.",
        "wallet_ux_surface": "Perform manual wallet UX checklist; Web3Guard never signs wallet transactions.",
        "admin_opsec_surface": "Perform manual admin OpSec checklist and evidence capture.",
        "foundry_tests": "Run forge test in an isolated worker and attach raw test output evidence.",
        "echidna_fuzz": "Run Echidna only when properties/config exist; otherwise Manual config required.",
        "mythril_symbolic": "Use Docker/isolated Mythril worker with timeout; never fake symbolic-analysis output.",
        "evidence_report": "Attach raw evidence IDs, timestamps, limitations, and pilot report hash.",
    }[key]


def _module_inputs(payload: dict[str, Any]) -> dict[str, bool]:
    evidence_count = _int(payload, "evidence_items_count", 0)
    report_hash_present = bool(payload.get("report_hash"))
    return {
        "slither_static": _truthy(payload, "slither_assessed"),
        "aderyn_static": _truthy(payload, "aderyn_assessed"),
        "semgrep_app_api": _truthy(payload, "semgrep_assessed"),
        "osv_advisory": _truthy(payload, "osv_checked"),
        "cisa_kev": _truthy(payload, "cisa_checked"),
        "github_hygiene": _truthy(payload, "github_checked"),
        "website_surface": _truthy(payload, "website_checked"),
        "api_surface": _truthy(payload, "api_checked"),
        "wallet_ux_surface": _truthy(payload, "wallet_ux_checked"),
        "admin_opsec_surface": _truthy(payload, "admin_opsec_checked"),
        "foundry_tests": _truthy(payload, "foundry_tests_run"),
        "echidna_fuzz": _truthy(payload, "echidna_run"),
        "mythril_symbolic": _truthy(payload, "mythril_run"),
        "evidence_report": evidence_count >= 5 or report_hash_present,
    }


def _status_from_readiness(key: str, assessed: bool) -> str:
    if assessed:
        return "Assessed"
    tool_map = {
        "slither_static": "slither",
        "aderyn_static": "aderyn",
        "semgrep_app_api": "semgrep",
        "foundry_tests": "foundry",
        "echidna_fuzz": "echidna",
        "mythril_symbolic": "mythril",
    }
    tool = tool_map.get(key)
    if tool:
        item = _tool_by_key().get(tool, {})
        return item.get("status") or "Tool Not Installed"
    if key in {"osv_advisory", "cisa_kev"} and not (settings.launch_validation_network_enabled or settings.provider_live_advisory_sources_enabled):
        return "Provider Not Configured"
    if key in {"wallet_ux_surface", "admin_opsec_surface"}:
        return "Manual review required"
    return "Not assessed yet"


def _cap_for_blockers(raw_points: int, payload: dict[str, Any], assessed_map: dict[str, bool]) -> tuple[int, list[str]]:
    cap = MAX_AUTOMATED_PREAUDIT_COVERAGE
    blockers: list[str] = []
    if not assessed_map["slither_static"]:
        cap = min(cap, 76)
        blockers.append("Slither static analysis is not assessed; Solidity coverage cannot be treated as 90-depth.")
    if not assessed_map["semgrep_app_api"]:
        cap = min(cap, 82)
        blockers.append("Semgrep app/API/code scan is not assessed; non-contract code coverage is limited.")
    if not assessed_map["osv_advisory"]:
        cap = min(cap, 80)
        blockers.append("OSV dependency lookup is not assessed; known package vulnerability coverage is limited.")
    if not assessed_map["cisa_kev"]:
        cap = min(cap, 84)
        blockers.append("CISA KEV matching is not assessed; exploited-in-the-wild priority coverage is missing.")
    if _int(payload, "critical_findings", 0) > 0:
        cap = min(cap, 72)
        blockers.append("Critical unresolved findings prevent 90-depth launch readiness.")
    if _int(payload, "high_findings", 0) >= 3:
        cap = min(cap, 78)
        blockers.append("Multiple high findings need triage before claiming high coverage readiness.")
    return min(raw_points, cap), blockers


def evaluate_scanner_depth(payload: dict[str, Any]) -> dict[str, Any]:
    assessed_map = _module_inputs(payload)
    items = []
    for key, assessed in assessed_map.items():
        status = _status_from_readiness(key, assessed)
        items.append(_coverage_item(key, assessed, evidence=str(payload.get(f"{key}_evidence") or f"{KEY_LABELS[key]} evidence supplied by caller."), status_override=status))
    raw_points = sum(item["points"] for item in items)
    capped_points, blockers = _cap_for_blockers(raw_points, payload, assessed_map)
    percent = min(capped_points, MAX_AUTOMATED_PREAUDIT_COVERAGE)
    missing = [item for item in items if item["status"] != "Assessed"]
    target_gap = max(0, MAX_AUTOMATED_PREAUDIT_COVERAGE - percent)
    return {
        "ok": True,
        "version": PHASE38_VERSION,
        "project_name": payload.get("project_name") or "Untitled Web3 project",
        "generated_at": _now_iso(),
        "coverage_depth_percent": percent,
        "raw_module_points": raw_points,
        "max_automated_pre_audit_coverage": MAX_AUTOMATED_PREAUDIT_COVERAGE,
        "target_gap_to_90": target_gap,
        "label": _coverage_label(percent),
        "items": items,
        "missing_modules": missing,
        "blockers": blockers,
        "next_best_actions": _next_best_actions(items, blockers),
        "worker_readiness": _worker_readiness_items(),
        "safe_wording": {
            "allowed": "High-depth pre-audit scanner coverage for assessed modules",
            "blocked": BLOCKED_CLAIMS,
            "required_disclaimer": "This is not a certified audit and does not guarantee that all vulnerabilities are found.",
        },
    }


def _coverage_label(percent: int) -> str:
    if percent >= 88:
        return "90-depth pre-audit coverage ready for narrow scope"
    if percent >= 78:
        return "Strong scanner coverage, still missing a few deep gates"
    if percent >= 60:
        return "Useful beta scanner coverage, not yet 90-depth"
    return "Foundational scanner coverage only"


def _next_best_actions(items: list[dict[str, Any]], blockers: list[str]) -> list[str]:
    if blockers:
        actions = blockers[:3]
    else:
        actions = []
    missing_sorted = sorted([item for item in items if item["status"] != "Assessed"], key=lambda item: item["weight"], reverse=True)
    for item in missing_sorted:
        action = f"+{item['weight']} points: {item['next_action']}"
        if action not in actions:
            actions.append(action)
        if len(actions) >= 6:
            break
    if not actions:
        actions.append("Maintain raw evidence, rerun after fixes, and send report for manual expert review before launch.")
    return actions


def scanner_depth_roadmap() -> dict[str, Any]:
    return {
        "ok": True,
        "version": PHASE38_VERSION,
        "goal": "Reach about 90% pre-audit scanner coverage depth without making a fake 90-99% security guarantee.",
        "phases_inside_phase38": [
            {"order": 1, "name": "Slither + Semgrep real execution", "target_points": WEIGHTS["slither_static"] + WEIGHTS["semgrep_app_api"], "outcome": "Real static-analysis evidence for Solidity/app/API code."},
            {"order": 2, "name": "OSV + CISA KEV intelligence", "target_points": WEIGHTS["osv_advisory"] + WEIGHTS["cisa_kev"], "outcome": "Known dependency vulnerabilities and exploited-in-the-wild priority mapping."},
            {"order": 3, "name": "Foundry + Echidna + Mythril gates", "target_points": WEIGHTS["foundry_tests"] + WEIGHTS["echidna_fuzz"] + WEIGHTS["mythril_symbolic"], "outcome": "Test/fuzz/symbolic evidence when safely configured; otherwise manual/not assessed."},
            {"order": 4, "name": "Surface coverage + evidence report", "target_points": 33, "outcome": "Website/API/wallet/admin/GitHub/evidence completeness."},
        ],
        "minimum_for_90_depth": [
            "Slither assessed",
            "Semgrep assessed",
            "OSV assessed",
            "CISA KEV assessed",
            "GitHub/website/API/wallet/admin scopes assessed or manually marked",
            "At least one test/deep worker evidence path: Foundry, Echidna, or Mythril",
            "Evidence IDs/report hash attached",
            "No unresolved critical findings",
        ],
        "never_claim": BLOCKED_CLAIMS,
    }


def scanner_depth_claim_check(text: str) -> dict[str, Any]:
    lowered = text.lower()
    hits = [claim for claim in BLOCKED_CLAIMS if claim.lower() in lowered]
    # Catch variants that users often write around the blocked list.
    if "99" in lowered and "secure" in lowered and "90-99% security guaranteed" not in hits:
        hits.append("99% secure / guarantee wording")
    if "90" in lowered and "guarantee" in lowered and "90-99% security guaranteed" not in hits:
        hits.append("90% guarantee wording")
    return {
        "ok": not hits,
        "version": PHASE38_VERSION,
        "blocked_matches": hits,
        "safe_rewrite": "Web3Guard provides high-depth pre-audit scanner coverage for assessed modules. It is not a certified audit and does not guarantee all vulnerabilities are found.",
    }
