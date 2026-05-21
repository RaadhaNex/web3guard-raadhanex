import hashlib
import re
from typing import Any
from datetime import datetime, timezone
from urllib.parse import urlparse

from app.core.security import validate_public_http_url
from app.models.schemas import CombinedReportRequest, Finding, ModuleScore, ScanResponse, UnifiedUrlScanRequest
from app.services.report_builder import build_combined_launch_report
from app.services.scan_contract import scan_solidity
from app.services.scan_dapp_api import scan_api_backend
from app.services.api_deep_readiness import run_api_deep_readiness_scan, api_deep_status
from app.services.scan_website import scan_website
from app.services.scan_github_repo import scan_github_repository
from app.services.scan_contract_address import scan_contract_address
from app.services.static_analysis_tools import run_static_analysis, static_analysis_status
from app.services.static_analysis_artifacts import analyze_static_artifacts
from app.services.real_findings_pipeline import build_real_findings_pipeline
from app.services.accuracy_upgrade import build_accuracy_upgrade_package
from app.services.detection_expansion import build_detection_expansion_package
from app.services.deep_evidence_accuracy import build_deep_evidence_accuracy_package
from app.services.deep_scan_orchestrator import build_deep_scan_orchestrator
from app.services.source_evidence_mapper import analyze_source_evidence_artifacts

MODULE_LABELS = {
    "website": "Website Surface",
    "dapp": "dApp Frontend Hints",
    "api": "API Backend",
    "contract": "Smart Contract",
    "wallet": "Wallet Flow",
    "admin_opsec": "Founder/Admin OpSec",
    "github": "GitHub Repository",
    "static_analysis": "Slither / Semgrep Static Analysis",
    "deep_detection": "Deep Detection Expansion",
}

REALNESS_MATRIX = [
    {
        "feature": "Website URL passive surface scanner",
        "status": "Live",
        "evidence": "Runs real passive GET/HEAD checks for HTTPS, redirects, headers, robots/sitemap, limited path hints, and public HTML script evidence.",
        "not_claimed": "No exploit testing, no credential testing, no authenticated crawl, no certified audit.",
    },
    {
        "feature": "Unified URL launch surface map",
        "status": "Live",
        "evidence": "Combines live website scan with optional API URL and pasted Solidity source when provided. Missing modules are marked Not assessed.",
        "not_claimed": "It does not infer a full launch score when inputs are missing.",
    },
    {
        "feature": "dApp frontend from website URL",
        "status": "Live limited hints",
        "evidence": "Reads public homepage evidence such as external scripts, inline scripts, dApp keywords, wallet/mint/claim/swap/stake text, and visible EVM address hints.",
        "not_claimed": "It is not a full frontend source-code audit without repo/source input.",
    },
    {
        "feature": "API backend scan",
        "status": "Manual / Live limited",
        "evidence": "Validates public API URL safety and checks pasted API code/config. It does not fuzz or bypass auth.",
        "not_claimed": "No authenticated penetration test or exploit payloads.",
    },
    {
        "feature": "Smart contract scan",
        "status": "Live for pasted Solidity",
        "evidence": "Rule engine runs on user-submitted Solidity source. Contract address fetching is not enabled yet.",
        "not_claimed": "No Slither/Mythril/Aderyn/verified-address fetch unless later configured.",
    },
    {
        "feature": "UPI payment",
        "status": "Manual payment verification",
        "evidence": "Generates real UPI deep links and stores payment reference for admin verification.",
        "not_claimed": "No automatic payment success or active subscription until Razorpay/webhook is implemented.",
    },
    {
        "feature": "AI explanations",
        "status": "Needs API key / fallback when disabled",
        "evidence": "Fallback local explanations run without AI. Real AI only runs if backend env enables provider and key.",
        "not_claimed": "No fake AI analysis when AI provider is disabled.",
    },
    {
        "feature": "GitHub public repo scanner",
        "status": "Live for public GitHub repos",
        "evidence": "Uses GitHub API/raw public files with file/byte limits to detect Solidity, frontend, API, package, config, deployment, and secret-hygiene hints.",
        "not_claimed": "No repo cloning, no dependency install, no code execution, no private repo scan without real token/authorization.",
    },
    {
        "feature": "Slither/Semgrep static-analysis runner",
        "status": "Live only when installed and enabled",
        "evidence": "Runs real subprocess tools against user-supplied Solidity source when backend env and binaries are present. Missing tools are shown as Tool Not Installed / Provider Not Configured.",
        "not_claimed": "No fake Slither/Semgrep findings, no dependency install, no repo clone, no Mythril claim, no certified audit.",
    },
    {
        "feature": "Contract address scanner",
        "status": "Live when explorer API key and verified source are available",
        "evidence": "Fetches verified contract source and ABI metadata from Etherscan API V2-compatible explorer endpoint, then runs local rule engine and metadata checks.",
        "not_claimed": "No private key collection, no wallet signing, no bytecode decompilation, no fake source scan when source is unverified or API key missing.",
    },

    {
        "feature": "Permission map + centralization report",
        "status": "Live for provided Solidity/ABI/manual facts",
        "evidence": "Maps owner, minter, pauser, upgrader, treasury, blacklist/freeze, fee, role-admin, and oracle powers from real source/ABI/manual inputs.",
        "not_claimed": "Does not invent role holders, does not collect private keys, and does not prove live multisig/timelock status without evidence.",
    },
    {
        "feature": "Deep analysis tool runner",
        "status": "Needs local tools / isolated worker",
        "evidence": "Runs real Mythril, Manticore, and Echidna only when installed and enabled; standard/deep modes require ownership verification.",
        "not_claimed": "No fake symbolic execution, no fake fuzzing, no private key collection, no dependency install by default, no mainnet execution.",
    },
]

DAPP_KEYWORDS = ["walletconnect", "metamask", "connect wallet", "mint", "claim", "airdrop", "swap", "stake", "approve", "permit", "bridge", "presale"]
EVM_ADDRESS_RE = re.compile(r"0x[a-fA-F0-9]{40}")


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _status_card(
    module: str,
    status: str,
    *,
    report: ScanResponse | None = None,
    evidence: list[str] | None = None,
    limitations: list[str] | None = None,
    required_input: list[str] | None = None,
) -> dict:
    return {
        "module": module,
        "label": MODULE_LABELS.get(module, module),
        "status": status,
        "score": report.module_score.score if report else None,
        "risk_label": report.module_score.risk_label if report else "Not assessed",
        "assessed": bool(report),
        "report_id": report.report_id if report else None,
        "findings_count": len(report.findings) if report else 0,
        "critical_high_count": sum(1 for f in report.findings if f.severity in {"critical", "high"}) if report else 0,
        "evidence": evidence or [],
        "limitations": limitations or [],
        "required_input": required_input or [],
    }


def _dapp_hints_from_website(website_report: ScanResponse) -> dict:
    metadata = website_report.scan_metadata or {}
    html = metadata.get("html_evidence", {}) if isinstance(metadata, dict) else {}
    keyword_hits = html.get("dapp_keyword_hits", []) if isinstance(html, dict) else []
    evm_addresses = html.get("evm_address_hints", []) if isinstance(html, dict) else []
    external_script_count = html.get("external_script_count", 0) if isinstance(html, dict) else 0
    inline_script_count = html.get("inline_script_count", 0) if isinstance(html, dict) else 0
    risky_script_hints = html.get("risky_script_hints", []) if isinstance(html, dict) else []

    findings: list[dict] = []
    if keyword_hits:
        findings.append({
            "severity": "info",
            "title": "dApp/Wallet Language Detected On Public Homepage",
            "evidence": ", ".join(keyword_hits[:12]),
            "meaning": "The website appears to include Web3 launch flow language, so wallet/transaction UX should be reviewed manually or with source code.",
        })
    if evm_addresses:
        findings.append({
            "severity": "info",
            "title": "Visible EVM Address Hint Found",
            "evidence": ", ".join(evm_addresses[:5]),
            "meaning": "Visible addresses should be paired with chain name, explorer link, and verified contract clarity.",
        })
    if external_script_count and external_script_count > 0:
        findings.append({
            "severity": "info",
            "title": "External Script Surface Present",
            "evidence": f"{external_script_count} external script(s), {inline_script_count} inline script block(s)",
            "meaning": "Third-party scripts can affect wallet/mint pages and should be reviewed before launch.",
        })
    if risky_script_hints:
        findings.append({
            "severity": "info",
            "title": "Wallet/Mint Script URL Hint",
            "evidence": str(risky_script_hints[:3]),
            "meaning": "This is only a keyword hint, not a malicious classification.",
        })

    status = "Live limited hints" if findings else "No dApp hints found from homepage"
    return {
        "status": status,
        "keyword_hits": keyword_hits,
        "visible_evm_addresses": evm_addresses[:10],
        "findings": findings,
        "limitations": [
            "Homepage HTML cannot prove the safety of wallet transaction flow.",
            "Full frontend review needs GitHub/source code or manual UX review.",
            "No wallet connection, signing, or transaction simulation is performed.",
        ],
    }


def _github_not_assessed() -> dict:
    return _status_card(
        "github",
        "Not assessed",
        required_input=["Public GitHub repository URL"],
        limitations=["Provide a GitHub repo URL to run the Web3Guard read-only repository scanner."],
    )


def _finding_to_dict(finding: Finding) -> dict[str, Any]:
    if hasattr(finding, "model_dump"):
        return finding.model_dump(mode="json")
    return finding.dict()


def _short_text(value: Any, limit: int = 900) -> str:
    text = str(value or "")
    return text if len(text) <= limit else text[:limit] + "..."


def _tool_state_label(status: str) -> str:
    normal = (status or "").lower()
    if normal == "not_installed":
        return "Tool Not Installed"
    if normal in {"disabled_by_env", "tool_disabled_by_env"}:
        return "Provider Not Configured"
    if normal == "completed":
        return "Assessed"
    if normal == "completed_with_errors":
        return "Manual Review Required"
    return "Not Assessed"


def _static_summary_from_report(report: ScanResponse) -> dict[str, Any]:
    metadata = report.scan_metadata or {}
    tool_status = metadata.get("tool_status", {}) if isinstance(metadata, dict) else {}
    tool_runs = metadata.get("tool_runs", {}) if isinstance(metadata, dict) else {}
    artifact_runs = metadata.get("artifact_runs", {}) if isinstance(metadata, dict) else {}
    tools: list[dict[str, Any]] = []
    real_tool_completed = False
    real_findings_count = 0

    for tool in ("slither", "semgrep"):
        status_info = tool_status.get(tool, {}) if isinstance(tool_status, dict) else {}
        run = tool_runs.get(tool, {}) if isinstance(tool_runs, dict) else {}
        run_status = str(run.get("status") or "not_run")
        if run_status == "completed":
            real_tool_completed = True
        real_findings = int(run.get("real_findings") or 0)
        real_findings_count += real_findings
        tools.append({
            "tool": tool,
            "state": _tool_state_label(run_status),
            "status": run_status,
            "installed": bool(status_info.get("installed")),
            "enabled_by_env": bool(status_info.get("enabled_by_env")),
            "will_run": bool(status_info.get("will_run")),
            "real_findings": real_findings,
            "returncode": run.get("returncode"),
            "timed_out": bool(run.get("timed_out")),
            "stderr_tail": _short_text(run.get("stderr"), 700),
            "stdout_tail": _short_text(run.get("stdout"), 700),
            "evidence_source": "backend_subprocess",
        })

    if isinstance(artifact_runs, dict):
        for tool in ("slither", "semgrep", "aderyn"):
            artifact = artifact_runs.get(tool) if isinstance(artifact_runs.get(tool), dict) else None
            if not artifact or artifact.get("state") == "Not Supplied":
                continue
            parsed = int(artifact.get("parsed_findings") or 0)
            if parsed:
                real_tool_completed = True
            real_findings_count += parsed
            tools.append({
                "tool": f"{tool}_artifact",
                "state": str(artifact.get("state") or "User Artifact"),
                "status": "artifact_parsed" if parsed else "artifact_status",
                "installed": False,
                "enabled_by_env": True,
                "will_run": False,
                "real_findings": parsed,
                "returncode": None,
                "timed_out": False,
                "stderr_tail": artifact.get("error"),
                "stdout_tail": None,
                "evidence_source": "user_supplied_json_artifact",
                "artifact_shape": artifact.get("artifact_shape"),
            })

    non_status_findings = [f for f in report.findings if getattr(f, "category", "") != "tool_status"]
    status_messages = [f for f in report.findings if getattr(f, "category", "") == "tool_status"]
    if non_status_findings or real_tool_completed or real_findings_count:
        state = "Assessed"
        assessed = True
        score = report.module_score.score
        risk_label_value = report.module_score.risk_label
    elif tools and all(tool["state"] == "Tool Not Installed" for tool in tools):
        state = "Tool Not Installed"
        assessed = False
        score = None
        risk_label_value = "Tool Not Installed"
    elif tools and all(tool["state"] == "Provider Not Configured" for tool in tools):
        state = "Provider Not Configured"
        assessed = False
        score = None
        risk_label_value = "Provider Not Configured"
    else:
        state = "Manual Review Required"
        assessed = False
        score = None
        risk_label_value = "Manual Review Required"

    return {
        "state": state,
        "assessed": assessed,
        "score": score,
        "risk_label": risk_label_value,
        "report_id": report.report_id,
        "engine_version": report.engine_version,
        "artifact_trust_level": metadata.get("artifact_trust_level") if isinstance(metadata, dict) else None,
        "tools": tools,
        "findings": [_finding_to_dict(f) for f in non_status_findings[:36]],
        "status_messages": [_finding_to_dict(f) for f in status_messages[:14]],
        "safety_controls": metadata.get("safety_controls", {}) if isinstance(metadata, dict) else {},
        "real_only_note": metadata.get("real_only_note") if isinstance(metadata, dict) else None,
    }


def _merge_static_summaries(primary: dict[str, Any], extra: dict[str, Any]) -> dict[str, Any]:
    findings = (primary.get("findings") or []) + (extra.get("findings") or [])
    status_messages = (primary.get("status_messages") or []) + (extra.get("status_messages") or [])
    tools = (primary.get("tools") or []) + (extra.get("tools") or [])
    assessed = bool(primary.get("assessed") or extra.get("assessed") or findings)
    scores = [item.get("score") for item in (primary, extra) if isinstance(item.get("score"), (int, float))]
    score = min(scores) if scores else None
    if assessed:
        state = "Assessed"
        risk_label_value = primary.get("risk_label") or extra.get("risk_label") or "Assessed"
    else:
        state = primary.get("state") or extra.get("state") or "Not Assessed"
        risk_label_value = primary.get("risk_label") or extra.get("risk_label") or state
    return {
        **primary,
        "state": state,
        "assessed": assessed,
        "score": score,
        "risk_label": risk_label_value,
        "tools": tools,
        "findings": findings[:48],
        "status_messages": status_messages[:20],
        "real_only_note": "Merged backend tool status/output with user-supplied Slither/Semgrep/Aderyn artifacts. Artifact findings are real evidence inputs but not a Web3Guard-certified audit.",
    }


def _static_module_card(summary: dict[str, Any]) -> dict[str, Any]:
    evidence = [
        f"{tool['tool'].title()}: {tool['state']} ({tool.get('real_findings', 0)} real finding(s))"
        for tool in summary.get("tools", [])
    ]
    if not evidence:
        evidence = ["No external static-analysis tool status is available for this scan."]
    required_input = [] if summary.get("assessed") else ["Install/enable Slither/Semgrep in the tools venv, or paste valid Slither/Semgrep/Aderyn JSON artifacts, then rerun."]
    return {
        "module": "static_analysis",
        "label": MODULE_LABELS["static_analysis"],
        "status": summary.get("state") or "Not Assessed",
        "score": summary.get("score") if summary.get("assessed") else None,
        "risk_label": summary.get("risk_label") or summary.get("state") or "Not assessed",
        "assessed": bool(summary.get("assessed")),
        "report_id": summary.get("report_id"),
        "findings_count": len(summary.get("findings") or []),
        "critical_high_count": sum(1 for f in summary.get("findings") or [] if f.get("severity") in {"critical", "high"}),
        "evidence": evidence,
        "limitations": [
            "External static analyzers are only run for user-supplied Solidity source.",
            "Tool status messages are not fake vulnerabilities and do not prove contract safety.",
            "Mythril/deep symbolic execution remains separate worker-required functionality.",
        ],
        "required_input": required_input,
    }



def _source_evidence_summary(report: ScanResponse) -> dict[str, Any]:
    metadata = report.scan_metadata or {}
    findings = [_finding_to_dict(finding) for finding in report.findings]
    location_index = metadata.get("location_index", []) if isinstance(metadata, dict) else []
    return {
        "state": metadata.get("state", "Assessed" if findings else "Assessed - No Findings"),
        "report_id": report.report_id,
        "score": report.module_score.score,
        "risk_label": report.module_score.risk_label,
        "engine_version": report.engine_version,
        "files_parsed": metadata.get("files_parsed", 0),
        "findings_count": len(findings),
        "critical_high_count": sum(1 for finding in findings if finding.get("severity") in {"critical", "high"}),
        "findings_with_exact_location": metadata.get("findings_with_exact_location", 0),
        "location_index": location_index[:80] if isinstance(location_index, list) else [],
        "file_inventory": metadata.get("file_inventory", []) if isinstance(metadata, dict) else [],
        "parse_status": metadata.get("parse_status", []) if isinstance(metadata, dict) else [],
        "findings": findings[:80],
        "safety_controls": metadata.get("safety_controls", {}) if isinstance(metadata, dict) else {},
        "real_only_note": metadata.get("real_only_note") if isinstance(metadata, dict) else None,
    }


def _source_evidence_module_card(summary: dict[str, Any]) -> dict[str, Any]:
    files_parsed = int(summary.get("files_parsed") or 0)
    exact_count = int(summary.get("findings_with_exact_location") or 0)
    findings_count = int(summary.get("findings_count") or 0)
    return {
        "module": "source_evidence",
        "label": "Source File / Path Evidence",
        "status": "Assessed" if files_parsed else "Not Assessed",
        "score": summary.get("score") if files_parsed else None,
        "risk_label": summary.get("risk_label") if files_parsed else "Not Assessed",
        "assessed": bool(files_parsed),
        "report_id": summary.get("report_id"),
        "findings_count": findings_count,
        "critical_high_count": int(summary.get("critical_high_count") or 0),
        "evidence": [
            f"Source files parsed: {files_parsed}",
            f"Findings with exact path/line: {exact_count}",
            f"Total source evidence findings: {findings_count}",
        ] if files_parsed else ["No source-file artifact was supplied for exact file/path/line mapping."],
        "limitations": [
            "Static source mapper does not execute code, install dependencies, clone repos, or prove exploitability.",
            "Findings are based on supplied source artifacts; exact paths/lines depend on artifact quality.",
            "Secret-like evidence is redacted in output; rotate real secrets before sharing reports.",
        ],
        "required_input": [] if files_parsed else [
            "Expert Evidence → SCA / secrets tool artifact JSON with {files:[{path,content}]} or {sources:{path:{content}}}",
            "For best results include backend, frontend, smart-contract, config, and env/template files.",
        ],
    }


def _static_not_assessed_summary() -> dict[str, Any]:
    status = static_analysis_status()
    tools = []
    for tool in ("slither", "semgrep"):
        info = status.get("tools", {}).get(tool, {})
        if not info.get("installed"):
            state = "Tool Not Installed"
        elif not status.get("static_analysis_enabled") or not info.get("enabled_by_env"):
            state = "Provider Not Configured"
        else:
            state = "Not Assessed"
        tools.append({
            "tool": tool,
            "state": state,
            "status": "not_run",
            "installed": bool(info.get("installed")),
            "enabled_by_env": bool(info.get("enabled_by_env")),
            "will_run": bool(info.get("will_run")),
            "real_findings": 0,
        })
    return {
        "state": "Not Assessed",
        "assessed": False,
        "score": None,
        "risk_label": "Not Assessed",
        "tools": tools,
        "findings": [],
        "status_messages": [],
        "safety_controls": status.get("safety_controls", {}),
        "real_only_note": "Solidity source was not supplied, so external static analysis was not run and no fake findings were created.",
    }


def _api_admin_exposure_summary(report: ScanResponse | None, error: str | None = None) -> dict[str, Any]:
    status = api_deep_status()
    if not report:
        return {
            "state": "Not Assessed" if not error else "Manual Review Required",
            "status": status,
            "error": error,
            "findings": [],
            "safe_endpoints_checked": [],
            "cors_headers": {},
            "openapi_detected": False,
            "graphql_detected": False,
            "auth_evidence": [],
            "webhook_evidence": [],
            "not_performed": status.get("not_performed", []),
        }
    metadata = report.scan_metadata or {}
    return {
        "state": "Assessed",
        "report_id": report.report_id,
        "score": report.module_score.score,
        "risk_label": report.module_score.risk_label,
        "findings": [_finding_to_dict(f) for f in report.findings[:20]],
        "safe_endpoints_checked": metadata.get("safe_endpoints_checked", []),
        "cors_headers": metadata.get("cors_headers", {}),
        "openapi_detected": bool(metadata.get("openapi_detected")),
        "graphql_detected": bool(metadata.get("graphql_detected")),
        "auth_evidence": metadata.get("auth_evidence", []),
        "webhook_evidence": metadata.get("webhook_evidence", []),
        "not_performed": status.get("not_performed", []),
        "safety_controls": {
            "no_fuzzing": metadata.get("no_fuzzing", True),
            "no_auth_bypass": metadata.get("no_auth_bypass", True),
            "no_payload_spraying": metadata.get("no_payload_spraying", True),
        },
    }


def _github_dependency_summary(report: ScanResponse | None, error: str | None = None) -> dict[str, Any]:
    if not report:
        return {
            "state": "Not Assessed" if not error else "Manual Review Required",
            "error": error,
            "dependency_manifests": [],
            "dependency_manifest_count": 0,
            "provider_state": "Provider Not Configured",
            "osv_state": "Provider Not Configured",
            "note": "Provide a public GitHub repo URL for read-only repo and dependency-manifest evidence. OSV live vulnerability lookup is not faked here.",
        }
    metadata = report.scan_metadata or {}
    manifests = metadata.get("dependency_manifests", []) if isinstance(metadata, dict) else []
    structure = metadata.get("structure_summary", {}) if isinstance(metadata, dict) else {}
    return {
        "state": "Assessed",
        "repo": metadata.get("repo", {}) if isinstance(metadata, dict) else {},
        "dependency_manifests": manifests[:10] if isinstance(manifests, list) else [],
        "dependency_manifest_count": len(manifests) if isinstance(manifests, list) else 0,
        "package_json_count": structure.get("package_json_count") if isinstance(structure, dict) else None,
        "lockfile_count": structure.get("lockfile_count") if isinstance(structure, dict) else None,
        "security_policy_count": structure.get("security_policy_count") if isinstance(structure, dict) else None,
        "findings": [_finding_to_dict(f) for f in report.findings if getattr(f, "category", "") == "dependencies"][:12],
        "osv_state": "Provider Not Configured",
        "provider_state": "Read-only GitHub evidence assessed; OSV live dependency vulnerability lookup is separate and not faked.",
        "safety_controls": metadata.get("safety_controls", {}) if isinstance(metadata, dict) else {},
    }


def _score_split(module_cards: list[dict], combined: dict) -> dict:
    by_module = {card.get("module"): card for card in module_cards}

    def module_score(module: str, label: str, source: str) -> dict:
        card = by_module.get(module) or {}
        assessed = bool(card.get("assessed"))
        score = card.get("score") if assessed else None
        return {
            "label": label,
            "score": score,
            "status": card.get("status") or "Not assessed",
            "risk_label": card.get("risk_label") or "Not assessed",
            "source": source if assessed else "Not Assessed — required evidence was not provided.",
        }

    total = len(module_cards) or 1
    assessed_count = sum(1 for card in module_cards if card.get("assessed"))
    required_missing = sum(len(card.get("required_input") or []) for card in module_cards)
    evidence_score = max(0, min(100, round((assessed_count / total) * 100 - min(required_missing * 2, 24))))
    coverage = combined.get("coverage") or {}
    full_coverage = bool(coverage.get("total_modules") and coverage.get("assessed_count") == coverage.get("total_modules"))

    return {
        "website_surface_score": module_score("website", "Website Surface Readiness", "Passive public URL evidence: HTTP/HTTPS, headers, HTML hints, robots/sitemap/policy signals."),
        "contract_rule_score": module_score("contract", "Contract Rule Score", "Pasted Solidity or verified explorer source analyzed by local rules. External tools remain separate."),
        "launch_evidence_score": {
            "label": "Launch Evidence Coverage",
            "score": evidence_score,
            "status": "Evidence complete" if required_missing == 0 else "Evidence needed",
            "risk_label": "Evidence gap" if required_missing else "Evidence present",
            "source": f"{assessed_count}/{total} modules assessed; {required_missing} required evidence item(s) still listed.",
        },
        "overall_launch_confidence": {
            "label": "Overall Launch Confidence",
            "score": (combined.get("combined") or {}).get("overall_score") if full_coverage else None,
            "status": "Full assessed confidence" if full_coverage else "Insufficient evidence — overall confidence gated",
            "risk_label": (combined.get("combined") or {}).get("risk_label") if full_coverage else "Insufficient Evidence",
            "source": "Overall confidence is shown only when every required module has real assessed evidence. Partial URL-only scans show website readiness, not full launch confidence.",
        },
        "no_full_audit_score": not full_coverage,
        "note": "These are launch-readiness scores, not a certified audit score, penetration-test score, or guarantee of security.",
    }


def _coverage_gate(module_cards: list[dict], combined: dict) -> dict[str, Any]:
    total = len(module_cards) or 0
    assessed_count = sum(1 for card in module_cards if card.get("assessed"))
    not_assessed = [card.get("module") for card in module_cards if not card.get("assessed")]
    assessed = [card.get("module") for card in module_cards if card.get("assessed")]
    coverage_percent = round((assessed_count / total) * 100) if total else 0
    full_coverage = bool(total and assessed_count == total)
    return {
        "overall_confidence_allowed": full_coverage,
        "coverage_percent": coverage_percent,
        "assessed_count": assessed_count,
        "total_modules": total,
        "assessed_modules": assessed,
        "not_assessed_modules": not_assessed,
        "display_rule": "Show full overall launch confidence only when all modules are assessed from real evidence.",
        "reason": "Partial URL-only scan: website surface can be scored, but full launch confidence is blocked until API, GitHub, contract/static analysis, wallet flow, and admin OpSec evidence are supplied." if not full_coverage else "All modules are assessed from supplied or live evidence.",
        "blocked_score_fields": [] if full_coverage else ["overall_score", "overall_launch_confidence"],
        "allowed_score_fields": ["website_surface_score", "launch_evidence_score", "available_score"],
        "combined_available_score": (combined.get("combined") or {}).get("available_score"),
        "combined_overall_score_raw": (combined.get("combined") or {}).get("overall_score"),
    }




def _bug_detection_coverage_summary(reports: list[ScanResponse], module_cards: list[dict]) -> dict[str, Any]:
    all_findings: list[Finding] = []
    for report in reports:
        all_findings.extend(report.findings)
    by_module: dict[str, int] = {}
    by_severity = {severity: 0 for severity in ["critical", "high", "medium", "low", "info"]}
    by_category: dict[str, int] = {}
    for finding in all_findings:
        by_module[finding.module] = by_module.get(finding.module, 0) + 1
        by_severity[finding.severity] = by_severity.get(finding.severity, 0) + 1
        category = finding.category or "general"
        by_category[category] = by_category.get(category, 0) + 1
    assessed_modules = [card.get("module") for card in module_cards if card.get("assessed")]
    not_assessed_modules = [card.get("module") for card in module_cards if not card.get("assessed")]
    website_coverage = {}
    for report in reports:
        if report.module_score.module == "website":
            website_coverage = (report.scan_metadata or {}).get("bug_detection_coverage", {})
            break
    return {
        "phase": "49",
        "engine_version": "bug-detection-proof-coverage-v2",
        "real_only_rule": "Every visible bug/warning must come from a real assessed module finding, tool output, supplied evidence, or a clear not-assessed/manual state.",
        "total_findings_from_assessed_modules": len(all_findings),
        "critical_high_count": sum(1 for f in all_findings if f.severity in {"critical", "high"}),
        "by_severity": by_severity,
        "by_module": by_module,
        "by_category": dict(sorted(by_category.items(), key=lambda item: item[0])),
        "assessed_modules": assessed_modules,
        "not_assessed_modules": not_assessed_modules,
        "website_passive_coverage": website_coverage,
        "confirmed_proof_exposure_count": website_coverage.get("confirmed_proof_exposure_count", 0) if isinstance(website_coverage, dict) else 0,
        "confirmed_proof_exposures": website_coverage.get("confirmed_proof_exposures", []) if isinstance(website_coverage, dict) else [],
        "visibility_rule": "Results page should show real findings clearly at the top. Not assessed modules must not be counted as passed or failed.",
        "coverage_added": [
            "cookie Secure/HttpOnly/SameSite evidence",
            "CSP frame-ancestors/object-src/script-src quality",
            "form action security and external form targets",
            "external iframe sandbox evidence",
            "target=_blank noopener evidence",
            "object/embed evidence",
            "source map hints and same-origin .map proof checks",
            "public .env/.git/config/debug/API-doc proof checks",
            "same-origin JS asset secret-like key checks",
            "security.txt launch contact evidence",
        ],
    }

def _real_evidence_summary(website_report: ScanResponse, module_cards: list[dict]) -> dict[str, Any]:
    metadata = website_report.scan_metadata or {}
    taxonomy = metadata.get("finding_truth_taxonomy", {}) if isinstance(metadata, dict) else {}
    raw_response = metadata.get("raw_response_evidence", {}) if isinstance(metadata, dict) else {}
    score_trace = metadata.get("dynamic_score_trace", {}) if isinstance(metadata, dict) else {}
    assessed_count = sum(1 for card in module_cards if card.get("assessed"))
    total = len(module_cards)
    return {
        "summary_rule": "Only observed response/source evidence is counted as real. Not assessed modules are evidence gaps, not fake bugs.",
        "coverage": f"{assessed_count}/{total} modules assessed",
        "real_observed_issue_count": taxonomy.get("confirmed_observed_issue_count", 0),
        "potential_hardening_hint_count": taxonomy.get("potential_hardening_hint_count", 0),
        "confirmed_exploit_count": taxonomy.get("confirmed_proof_exposure_count", 0),
        "confirmed_bug_or_exposure_count": taxonomy.get("confirmed_bug_or_exposure_count", taxonomy.get("confirmed_proof_exposure_count", 0)),
        "confirmed_exploit_note": "This count increases only when safe passive proof exists, such as public .env/.git, source map proof, debug endpoint markers, public API schema/docs, or secret-like keys in public config/assets. It is not a claim of full exploit testing.",
        "observed_issues": taxonomy.get("confirmed_observed_issues", []),
        "hardening_hints": taxonomy.get("potential_hardening_hints", []),
        "confirmed_proof_exposures": taxonomy.get("confirmed_proof_exposures", []),
        "website_raw_evidence": raw_response,
        "dynamic_score_trace": score_trace,
        "score_debug_note": "If the same site keeps the same headers/scripts/status, the score can repeat. If bugs/errors change, the score trace and score change together.",
        "not_assessed_warning": "Modules without evidence are not scanned and must not be treated as passed or failed.",
    }


async def run_unified_url_scan(payload: UnifiedUrlScanRequest) -> dict:
    started = datetime.now(timezone.utc)
    safe_website_url = validate_public_http_url(payload.website_url)
    reports: list[ScanResponse] = []
    module_cards: list[dict] = []
    github_report_for_expansion: ScanResponse | None = None
    surface_hints: dict = {}
    warnings: list[str] = []

    website_report = await scan_website(safe_website_url, payload.project_name)
    reports.append(website_report)
    module_cards.append(
        _status_card(
            "website",
            "Live",
            report=website_report,
            evidence=[
                f"Final URL: {website_report.scan_metadata.get('final_url')}",
                f"HTTP status: {website_report.scan_metadata.get('status_code')}",
                f"Headers present: {', '.join(website_report.scan_metadata.get('headers_present', [])) or 'none detected'}",
            ],
            limitations=["Passive-only public website checks. No login, exploit, brute force, or active security testing."],
        )
    )

    dapp_hints = _dapp_hints_from_website(website_report)
    surface_hints["dapp_from_homepage"] = dapp_hints
    module_cards.append(
        _status_card(
            "dapp",
            dapp_hints["status"],
            evidence=[finding["title"] for finding in dapp_hints["findings"]] or ["No wallet/mint/claim/swap/stake keyword hints found on the fetched homepage."],
            limitations=dapp_hints["limitations"],
            required_input=["Frontend source/GitHub repo for full dApp score", "Wallet flow checklist for transaction UX scoring"],
        )
    )

    if payload.api_base_url:
        api_report = scan_api_backend(checklist=[], project_name=payload.project_name, api_base_url=payload.api_base_url)
        reports.append(api_report)
        api_deep_report: ScanResponse | None = None
        try:
            api_deep_report = await run_api_deep_readiness_scan(
                api_base_url=payload.api_base_url,
                project_name=payload.project_name,
                ownership_verified=True,
            )
        except Exception as exc:
            warnings.append(f"API/admin passive exposure checklist was not completed: {exc}")
            surface_hints["api_admin_exposure"] = _api_admin_exposure_summary(None, str(exc))
        else:
            surface_hints["api_admin_exposure"] = _api_admin_exposure_summary(api_deep_report)
        endpoint_count = len((surface_hints.get("api_admin_exposure") or {}).get("safe_endpoints_checked", [])) if isinstance(surface_hints.get("api_admin_exposure"), dict) else 0
        module_cards.append(
            _status_card(
                "api",
                "Live safe/passive",
                report=api_report,
                evidence=[
                    f"API URL passed public URL safety validation: {api_report.scan_metadata.get('validated_api_base', payload.api_base_url)}",
                    f"Safe passive API/admin checks recorded: {endpoint_count}",
                ],
                limitations=["No fuzzing, auth bypass, credential testing, brute force, DoS, login test, or exploit payloads."],
            )
        )
    else:
        surface_hints["api_admin_exposure"] = _api_admin_exposure_summary(None)
        module_cards.append(
            _status_card(
                "api",
                "Not assessed",
                required_input=["API base URL or API code/config"],
                limitations=["Website URL alone does not prove backend API security."],
            )
        )


    static_artifact_report = analyze_static_artifacts(
        slither_json=getattr(payload, "slither_json", None),
        semgrep_json=getattr(payload, "semgrep_json", None),
        aderyn_json=getattr(payload, "aderyn_json", None),
        project_name=payload.project_name,
    )
    source_evidence_report = analyze_source_evidence_artifacts(
        security_tool_artifacts_json=getattr(payload, "security_tool_artifacts_json", None),
        crawler_artifact_json=getattr(payload, "crawler_artifact_json", None),
        review_context_json=getattr(payload, "review_context_json", None),
        project_name=payload.project_name,
        project_type=payload.project_type,
    )

    if payload.solidity_code and payload.solidity_code.strip():
        contract_report = scan_solidity(payload.solidity_code, payload.project_name, payload.project_type)
        reports.append(contract_report)
        module_cards.append(
            _status_card(
                "contract",
                "Live for pasted Solidity",
                report=contract_report,
                evidence=["User submitted Solidity source was scanned by the local rule engine."],
                limitations=["This is a preliminary rule-engine scan. External Slither/Semgrep evidence is shown separately and only when real tools run or valid tool artifacts are supplied."],
            )
        )
        try:
            static_report = run_static_analysis(
                payload.solidity_code,
                payload.project_name,
                "Web3GuardUnified.sol",
                ["slither", "semgrep"],
            )
            static_summary = _static_summary_from_report(static_report)
        except Exception as exc:
            warnings.append(f"Slither/Semgrep static analysis was not completed: {exc}")
            static_summary = {
                "state": "Manual Review Required",
                "assessed": False,
                "score": None,
                "risk_label": "Manual Review Required",
                "tools": [],
                "findings": [],
                "status_messages": [],
                "real_only_note": f"Static-analysis runner could not complete: {exc}",
            }
        if static_artifact_report:
            reports.append(static_artifact_report)
            static_summary = _merge_static_summaries(static_summary, _static_summary_from_report(static_artifact_report))
        surface_hints["static_analysis"] = static_summary
        module_cards.append(_static_module_card(static_summary))
    elif payload.contract_address:
        if static_artifact_report:
            reports.append(static_artifact_report)
            surface_hints["static_analysis"] = _static_summary_from_report(static_artifact_report)
        else:
            surface_hints["static_analysis"] = _static_not_assessed_summary()
        module_cards.append(_static_module_card(surface_hints["static_analysis"]))
        try:
            address_report = await scan_contract_address(payload.contract_address, payload.chain, payload.project_name)
            reports.append(address_report)
            module_cards.append(
                _status_card(
                    "contract",
                    "Live from verified explorer source" if address_report.scan_metadata.get("source_verified") else "Explorer metadata only",
                    report=address_report,
                    evidence=[
                        f"Address: {payload.contract_address}",
                        f"Chain: {address_report.scan_metadata.get('chain_id')}",
                        f"Source verified: {address_report.scan_metadata.get('source_verified')}",
                    ],
                    limitations=["Explorer-source rule scan only. No wallet signing, bytecode decompilation, Slither/Aderyn/Mythril, or certified audit."],
                )
            )
        except ValueError as exc:
            module_cards.append(
                _status_card(
                    "contract",
                    "Input recorded only",
                    evidence=[f"Contract address provided: {payload.contract_address}", f"Chain: {payload.chain or 'not specified'}"],
                    required_input=[str(exc), "Paste Solidity source as fallback for a live rule-engine scan"],
                    limitations=["No fake contract score is generated when explorer source fetch cannot run."],
                )
            )
            warnings.append(f"Contract address scan was not completed: {exc}")
    else:
        if static_artifact_report:
            reports.append(static_artifact_report)
            surface_hints["static_analysis"] = _static_summary_from_report(static_artifact_report)
            module_cards.append(_static_module_card(surface_hints["static_analysis"]))
        else:
            surface_hints["static_analysis"] = _static_not_assessed_summary()
            module_cards.append(_static_module_card(surface_hints["static_analysis"]))
        module_cards.append(
            _status_card(
                "contract",
                "Not assessed",
                required_input=["Pasted Solidity source, verified contract address, or valid Slither/Semgrep/Aderyn artifact"],
                limitations=["Website URL alone cannot assess smart contract code. Static-analysis artifacts can add real tool evidence, but they do not replace source review."],
            )
        )

    if source_evidence_report:
        reports.append(source_evidence_report)
        source_summary = _source_evidence_summary(source_evidence_report)
        surface_hints["source_evidence_mapper"] = source_summary
        module_cards.append(_source_evidence_module_card(source_summary))
    else:
        surface_hints["source_evidence_mapper"] = {
            "state": "Not Assessed",
            "findings": [],
            "location_index": [],
            "required_input": "Supply source artifacts in Expert Evidence to produce exact affected_file + affected_line output.",
        }

    module_cards.append(
        _status_card(
            "wallet",
            "Manual input required",
            required_input=["Wallet flow checklist or UX/source review"],
            limitations=["No wallet connection, signing, approval lookup, or transaction simulation is performed in URL-only mode."],
        )
    )
    module_cards.append(
        _status_card(
            "admin_opsec",
            "Manual input required",
            required_input=["Founder/admin OpSec checklist: multisig, timelock, roles, treasury, MFA, key storage"],
            limitations=["Website URL cannot prove owner wallet, multisig, private key policy, or incident response readiness."],
        )
    )
    if payload.github_repo_url:
        try:
            github_report = await scan_github_repository(payload.github_repo_url, project_name=payload.project_name)
            github_report_for_expansion = github_report
            reports.append(github_report)
            surface_hints["github_dependency_risk"] = _github_dependency_summary(github_report)
            dependency_summary = surface_hints["github_dependency_risk"]
            module_cards.append(
                _status_card(
                    "github",
                    "Live",
                    report=github_report,
                    evidence=[
                        f"Repo: {github_report.scan_metadata.get('repo', {}).get('url')}",
                        f"Branch: {github_report.scan_metadata.get('repo', {}).get('scanned_branch')}",
                        f"Files seen: {github_report.scan_metadata.get('structure_summary', {}).get('total_files_seen')}",
                        f"Dependency manifests summarized: {dependency_summary.get('dependency_manifest_count', 0) if isinstance(dependency_summary, dict) else 0}",
                    ],
                    limitations=["Read-only public GitHub API/raw file scan. No clone, execution, dependency install, or fake OSV output."],
                )
            )
        except ValueError as exc:
            surface_hints["github_dependency_risk"] = _github_dependency_summary(None, str(exc))
            module_cards.append(
                _status_card(
                    "github",
                    "Input rejected",
                    evidence=[f"Repository URL provided: {payload.github_repo_url}"],
                    required_input=[str(exc)],
                    limitations=["No fake GitHub score is generated when the repo cannot be fetched."],
                )
            )
            warnings.append(f"GitHub repo scan was not completed: {exc}")
    else:
        surface_hints["github_dependency_risk"] = _github_dependency_summary(None)
        module_cards.append(_github_not_assessed())

    detection_expansion = await build_detection_expansion_package(
        website_url=safe_website_url,
        payload=payload,
        github_report=github_report_for_expansion,
        static_summary=surface_hints.get("static_analysis") if isinstance(surface_hints.get("static_analysis"), dict) else None,
    )
    surface_hints["deep_detection_expansion"] = detection_expansion
    expansion_summary = detection_expansion.get("summary", {}) if isinstance(detection_expansion, dict) else {}
    module_cards.append({
        "module": "deep_detection",
        "label": "Deep Detection Expansion",
        "status": "Assessed" if expansion_summary.get("total_findings", 0) or expansion_summary.get("assessed_phase_count", 0) else "Manual Review Required",
        "score": None,
        "risk_label": "Evidence findings present" if expansion_summary.get("total_findings", 0) else "No extra proof findings",
        "assessed": True,
        "report_id": None,
        "findings_count": int(expansion_summary.get("total_findings") or 0),
        "critical_high_count": int(expansion_summary.get("critical_high_findings") or 0),
        "evidence": [
            "Phase 60 same-origin crawler and JS/API endpoint discovery executed.",
            f"Deep detection findings: {int(expansion_summary.get('total_findings') or 0)}",
            f"Critical/high: {int(expansion_summary.get('critical_high_findings') or 0)}",
        ],
        "limitations": detection_expansion.get("safe_scope", [])[:4] if isinstance(detection_expansion, dict) else ["Safe passive expansion only."],
        "required_input": detection_expansion.get("next_accuracy_steps", [])[:4] if isinstance(detection_expansion, dict) else [],
    })

    deep_evidence_accuracy = await build_deep_evidence_accuracy_package(
        {"surface_hints": surface_hints, "module_cards": module_cards},
        payload,
    )
    surface_hints["deep_evidence_accuracy"] = deep_evidence_accuracy
    deep_summary = deep_evidence_accuracy.get("summary", {}) if isinstance(deep_evidence_accuracy, dict) else {}
    module_cards.append({
        "module": "deep_evidence_accuracy",
        "label": "Deep Evidence Accuracy",
        "status": "Assessed" if int(deep_summary.get("assessed_phase_count") or 0) > 1 else "Needs Evidence",
        "score": deep_summary.get("evidence_score"),
        "risk_label": "Evidence-backed findings present" if int(deep_summary.get("total_findings") or 0) else "Needs artifact evidence",
        "assessed": True,
        "report_id": None,
        "findings_count": int(deep_summary.get("total_findings") or 0),
        "critical_high_count": int(deep_summary.get("critical_high_findings") or 0),
        "evidence": [
            "Phase 68-77 deep evidence accuracy layer executed.",
            f"Evidence findings: {int(deep_summary.get('total_findings') or 0)}",
            f"Assessed sub-phases: {int(deep_summary.get('assessed_phase_count') or 0)}/10",
        ],
        "limitations": deep_evidence_accuracy.get("safe_boundaries", [])[:4] if isinstance(deep_evidence_accuracy, dict) else ["Safe evidence/artifact layer only."],
        "required_input": deep_evidence_accuracy.get("next_accuracy_steps", [])[:4] if isinstance(deep_evidence_accuracy, dict) else [],
    })

    combined = await build_combined_launch_report(CombinedReportRequest(
        project_name=payload.project_name or urlparse(safe_website_url).hostname or "Web3 project",
        reports=reports,
        preferred_language="English",
        include_ai=False,
        report_mode="pre_audit",
    ))

    assessed_modules = [card["module"] for card in module_cards if card["assessed"]]
    not_assessed_modules = [card["module"] for card in module_cards if not card["assessed"]]
    live_count = sum(1 for card in module_cards if str(card["status"]).lower().startswith("live"))
    score_split = _score_split(module_cards, combined)

    result = {
        "report_id": f"W3G-URL-LAUNCH-{_hash(safe_website_url)[:12]}",
        "generated_at": started.isoformat(),
        "project_name": payload.project_name,
        "engine_version": "web3guard-unified-url-launch-scanner-v23.0-source-path-line-evidence",
        "mode": "real_only_unified_url_scan",
        "website_url": safe_website_url,
        "chain": payload.chain,
        "project_type": payload.project_type,
        "realness_rule": "Only modules with real input/evidence receive a score. Missing modules are shown as Not assessed instead of fake scores.",
        "available_score": combined.get("combined", {}).get("available_score"),
        "overall_score": combined.get("combined", {}).get("overall_score") if _coverage_gate(module_cards, combined)["overall_confidence_allowed"] else None,
        "risk_label": combined.get("combined", {}).get("risk_label") if _coverage_gate(module_cards, combined)["overall_confidence_allowed"] else "Insufficient Evidence",
        "score_split": score_split,
        "coverage": combined.get("coverage"),
        "coverage_gate": _coverage_gate(module_cards, combined),
        "bug_detection_coverage": _bug_detection_coverage_summary(reports, module_cards),
        "real_evidence_summary": _real_evidence_summary(website_report, module_cards),
        "dynamic_score_trace": (website_report.scan_metadata or {}).get("dynamic_score_trace", {}),
        "assessed_modules": assessed_modules,
        "not_assessed_modules": not_assessed_modules,
        "live_module_count": live_count,
        "module_cards": module_cards,
        "surface_hints": surface_hints,
        "priority_actions": combined.get("priority_action_plan", []),
        "combined_report": combined,
        "feature_status_matrix": REALNESS_MATRIX,
        "warnings": warnings,
        "safe_public_summary": "This is a preliminary URL launch-surface review. Website score is dynamic from observed findings/proof-based exposures; full launch confidence is blocked when required modules are Not Assessed.",
        "blocked_claims": [
            "Do not say this project is certified audited.",
            "Do not claim AI/manual experts reviewed missing modules.",
            "Do not show payment/subscription success without verified payment webhook or admin verification.",
            "Do not show a full launch score unless all required modules are assessed.",
            "Do not call hardening hints confirmed bugs. Only proof-based public exposures from fetched evidence can be shown as confirmed bugs/exposures.",
        ],
        "next_real_inputs_needed": [
            "Paste Solidity source or enable explorer source fetch for contract scan.",
            "Install/enable Slither/Semgrep in the tools venv or paste valid Slither/Semgrep/Aderyn JSON artifact evidence.",
            "Provide API base URL/code for backend review.",
            "Complete wallet-flow checklist for approval/signature UX.",
            "Complete founder/admin OpSec checklist for multisig/timelock/key policy.",
            "Provide a public GitHub repo URL to run the Web3Guard read-only repo scanner and dependency-manifest summary.",
            "For exact file/path/row output, supply source artifacts as JSON: {files:[{path,content}]} or {sources:{path:{content}}}.",
        ],
        "disclaimer": "This is a preliminary security review and does not replace a full manual audit. URL-only scans are partial by design.",
    }
    result["findings_pipeline"] = build_real_findings_pipeline(result)
    result["accuracy_upgrade"] = await build_accuracy_upgrade_package(result, payload)
    result["detection_expansion"] = detection_expansion
    result["deep_evidence_accuracy"] = deep_evidence_accuracy
    deep_scan_orchestrator = build_deep_scan_orchestrator(
        payload,
        module_cards=result.get("module_cards", []),
        surface_hints=result.get("surface_hints", {}),
    )
    result["deep_scan_orchestrator"] = deep_scan_orchestrator
    result.setdefault("surface_hints", {})["deep_scan_orchestrator"] = deep_scan_orchestrator
    return result
