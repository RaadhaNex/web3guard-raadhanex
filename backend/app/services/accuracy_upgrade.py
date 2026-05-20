from __future__ import annotations

import json
import re
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import httpx

from app.core.config import settings
from app.services.static_analysis_tools import run_static_analysis, static_analysis_status

ENGINE_VERSION = "web3guard-accuracy-upgrade-phases-52-58-v1.0"

PACKAGE_ECOSYSTEM_BY_FILE = {
    "package.json": "npm",
    "package-lock.json": "npm",
    "pnpm-lock.yaml": "npm",
    "yarn.lock": "npm",
    "requirements.txt": "PyPI",
    "pyproject.toml": "PyPI",
    "poetry.lock": "PyPI",
    "cargo.lock": "crates.io",
    "Cargo.lock": "crates.io",
}

RISKY_SIGNATURE_WORDS = re.compile(r"(?i)(sign in|login|verify|airdrop|claim|free mint|approve|permit|permit2|delegate|setapprovalforall)")
PRIVATE_KEY_REQUEST_RE = re.compile(r"(?i)(private key|seed phrase|mnemonic|recovery phrase|import wallet)")
UNLIMITED_APPROVAL_RE = re.compile(r"(?i)(ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff|maxuint256|unlimited|infinite approval)")
ADMIN_ENDPOINT_RE = re.compile(r"(?i)(/admin|/dashboard/admin|/wp-admin|/debug|/swagger|/openapi|/docs|/redoc|/graphql)")
AUTH_HINT_RE = re.compile(r"(?i)(bearer |authorization|jwt|session|cookie|x-api-key|apikey)")
SENSITIVE_FIELD_RE = re.compile(r"(?i)(password|token|secret|private_key|mnemonic|seed|api_key|authorization|refresh_token)")


@dataclass
class NormalizedFinding:
    title: str
    severity: str
    category: str
    source: str
    evidence: str
    recommendation: str
    confidence: str = "medium"
    proof_level: str = "observed_evidence"

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "severity": self.severity,
            "category": self.category,
            "source": self.source,
            "evidence": self.evidence,
            "recommendation": self.recommendation,
            "confidence": self.confidence,
            "proof_level": self.proof_level,
        }


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_json_loads(value: str | None) -> Any | None:
    if not value or not str(value).strip():
        return None
    try:
        return json.loads(value)
    except Exception:
        return None


def _short(value: Any, limit: int = 900) -> str:
    text = str(value or "")
    return text if len(text) <= limit else text[:limit] + "..."


def _normalize_version(value: Any) -> str:
    text = str(value or "").strip()
    text = re.sub(r"^[\^~><=\s]+", "", text)
    text = text.split(" || ")[0].split(" ")[0]
    return text[:80]


def _extract_package_json_dependencies(raw: str, path: str = "package.json") -> list[dict[str, str]]:
    data = _safe_json_loads(raw)
    if not isinstance(data, dict):
        return []
    deps: list[dict[str, str]] = []
    for bucket in ("dependencies", "devDependencies", "optionalDependencies", "peerDependencies"):
        values = data.get(bucket)
        if not isinstance(values, dict):
            continue
        for name, version in values.items():
            deps.append({
                "name": str(name),
                "version": _normalize_version(version),
                "ecosystem": "npm",
                "manifest": path,
                "scope": bucket,
            })
    return deps


def _extract_requirements_dependencies(raw: str, path: str = "requirements.txt") -> list[dict[str, str]]:
    deps: list[dict[str, str]] = []
    for line in raw.splitlines():
        clean = line.strip()
        if not clean or clean.startswith("#") or clean.startswith("-"):
            continue
        match = re.match(r"^([A-Za-z0-9_.\-]+)\s*(?:==|>=|<=|~=|>|<)?\s*([A-Za-z0-9_.!+\-]*)", clean)
        if not match:
            continue
        name, version = match.groups()
        deps.append({"name": name, "version": _normalize_version(version), "ecosystem": "PyPI", "manifest": path, "scope": "runtime"})
    return deps


def dependencies_from_inputs(package_json: str | None = None, requirements_txt: str | None = None, manifests: list[dict[str, Any]] | None = None) -> list[dict[str, str]]:
    deps: list[dict[str, str]] = []
    if package_json:
        deps.extend(_extract_package_json_dependencies(package_json))
    if requirements_txt:
        deps.extend(_extract_requirements_dependencies(requirements_txt))
    for manifest in manifests or []:
        if not isinstance(manifest, dict):
            continue
        path = str(manifest.get("path") or manifest.get("manifest") or "package.json")
        # Existing GitHub scanner stores security_relevant_dependencies. Use only versions it really saw.
        for item in manifest.get("security_relevant_dependencies") or []:
            if isinstance(item, dict) and item.get("name"):
                deps.append({
                    "name": str(item.get("name")),
                    "version": _normalize_version(item.get("version")),
                    "ecosystem": PACKAGE_ECOSYSTEM_BY_FILE.get(path.rsplit("/", 1)[-1], "npm"),
                    "manifest": path,
                    "scope": "repo_manifest_summary",
                })
    # De-duplicate while preserving evidence source.
    seen: set[tuple[str, str, str]] = set()
    unique: list[dict[str, str]] = []
    for dep in deps:
        key = (dep.get("ecosystem", ""), dep.get("name", ""), dep.get("version", ""))
        if not dep.get("name") or key in seen:
            continue
        seen.add(key)
        unique.append(dep)
    return unique[:80]


async def query_osv_for_dependencies(dependencies: list[dict[str, str]]) -> dict[str, Any]:
    if not dependencies:
        return {
            "state": "Not Assessed",
            "provider": "OSV",
            "dependency_count": 0,
            "vulnerabilities": [],
            "reason": "No dependency name/version evidence was supplied.",
        }
    if not settings.provider_live_network_enabled:
        return {
            "state": "Provider Not Configured",
            "provider": "OSV",
            "dependency_count": len(dependencies),
            "vulnerabilities": [],
            "reason": "PROVIDER_LIVE_NETWORK_ENABLED is false. No OSV vulnerability results are faked.",
        }

    queries = []
    query_deps = []
    for dep in dependencies[:40]:
        name = dep.get("name")
        version = dep.get("version")
        ecosystem = dep.get("ecosystem") or "npm"
        if not name or not version:
            continue
        queries.append({"package": {"name": name, "ecosystem": ecosystem}, "version": version})
        query_deps.append(dep)
    if not queries:
        return {
            "state": "Not Assessed",
            "provider": "OSV",
            "dependency_count": len(dependencies),
            "vulnerabilities": [],
            "reason": "Dependencies were found but no exact name+version pair was available for OSV.",
        }
    try:
        async with httpx.AsyncClient(timeout=settings.provider_live_timeout_seconds) as client:
            response = await client.post(f"{settings.osv_api_base.rstrip('/')}/v1/querybatch", json={"queries": queries})
            response.raise_for_status()
            payload = response.json()
    except Exception as exc:
        return {
            "state": "Provider Error",
            "provider": "OSV",
            "dependency_count": len(dependencies),
            "vulnerabilities": [],
            "reason": f"OSV lookup failed: {_short(exc, 320)}. No vulnerability is invented.",
        }

    results = payload.get("results", []) if isinstance(payload, dict) else []
    vulnerabilities: list[dict[str, Any]] = []
    for dep, result in zip(query_deps, results):
        vulns = result.get("vulns", []) if isinstance(result, dict) else []
        for vuln in vulns[: settings.launch_validation_max_vulnerabilities_per_package]:
            if not isinstance(vuln, dict):
                continue
            vulnerabilities.append({
                "source": "OSV",
                "id": vuln.get("id"),
                "summary": vuln.get("summary"),
                "package": dep.get("name"),
                "version": dep.get("version"),
                "ecosystem": dep.get("ecosystem"),
                "manifest": dep.get("manifest"),
                "aliases": vuln.get("aliases", [])[:10],
                "modified": vuln.get("modified"),
                "published": vuln.get("published"),
                "database_specific": vuln.get("database_specific", {}),
                "severity": vuln.get("severity", [])[:6],
                "references": vuln.get("references", [])[:8],
                "proof": f"OSV matched {dep.get('ecosystem')} package {dep.get('name')}@{dep.get('version')} to advisory {vuln.get('id')}",
            })
    return {
        "state": "Assessed",
        "provider": "OSV",
        "dependency_count": len(dependencies),
        "queried_count": len(query_deps),
        "vulnerability_count": len(vulnerabilities),
        "vulnerabilities": vulnerabilities[:80],
        "raw_provider": "https://api.osv.dev/v1/querybatch",
        "real_only_note": "Only OSV-returned advisories are shown. No dependency vulnerability is guessed from package name alone.",
    }


async def run_dependency_osv_engine(package_json: str | None = None, requirements_txt: str | None = None, manifests: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    deps = dependencies_from_inputs(package_json=package_json, requirements_txt=requirements_txt, manifests=manifests)
    osv = await query_osv_for_dependencies(deps)
    return {
        "phase": "52",
        "engine": "GitHub + OSV Real Dependency Engine",
        "state": osv.get("state"),
        "dependencies": deps[:80],
        "osv": osv,
        "guarantee": "Dependency vulnerabilities are shown only when a concrete dependency name+version is matched by OSV. Missing lockfiles/providers stay Not Assessed/Provider Error.",
    }


def run_static_worker_bridge(solidity_code: str | None, project_name: str | None = None) -> dict[str, Any]:
    status = static_analysis_status()
    if not solidity_code or not solidity_code.strip():
        return {
            "phase": "53",
            "engine": "Backend Slither/Semgrep Worker Runner",
            "state": "Not Assessed",
            "status": status,
            "reason": "No Solidity source was supplied, so backend static tools were not run.",
        }
    if not status.get("static_analysis_enabled"):
        return {
            "phase": "53",
            "engine": "Backend Slither/Semgrep Worker Runner",
            "state": "Provider Not Configured",
            "status": status,
            "reason": "STATIC_ANALYSIS_ENABLED is false. No fake Slither/Semgrep output is generated.",
        }
    try:
        report = run_static_analysis(solidity_code, project_name, "Web3GuardPhase53.sol", ["slither", "semgrep", "aderyn"])
    except Exception as exc:
        return {
            "phase": "53",
            "engine": "Backend Slither/Semgrep Worker Runner",
            "state": "Manual Review Required",
            "status": status,
            "reason": f"Real tool runner failed: {_short(exc, 400)}",
        }
    findings = []
    for finding in report.findings:
        if getattr(finding, "category", "") == "tool_status":
            continue
        data = finding.model_dump(mode="json") if hasattr(finding, "model_dump") else finding.dict()
        findings.append(data)
    return {
        "phase": "53",
        "engine": "Backend Slither/Semgrep Worker Runner",
        "state": "Assessed" if findings else "Assessed — No parsed tool findings",
        "report_id": report.report_id,
        "score": report.module_score.score,
        "risk_label": report.module_score.risk_label,
        "tool_runs": (report.scan_metadata or {}).get("tool_runs", {}),
        "findings": findings[:90],
        "status_messages": [f.model_dump(mode="json") if hasattr(f, "model_dump") else f.dict() for f in report.findings if getattr(f, "category", "") == "tool_status"],
        "real_only_note": "Findings are included only from actual subprocess output. Tool status messages are not counted as vulnerabilities.",
    }


def run_authorized_api_evidence_runner(api_base_url: str | None = None, observations: list[dict[str, Any]] | None = None, openapi_json: str | None = None) -> dict[str, Any]:
    findings: list[NormalizedFinding] = []
    checked: list[dict[str, Any]] = []
    for obs in observations or []:
        if not isinstance(obs, dict):
            continue
        endpoint = str(obs.get("endpoint") or obs.get("url") or "")[:260]
        status_code = obs.get("status_code")
        role = str(obs.get("role") or "unknown")[:80]
        expected = str(obs.get("expected_access") or "")[:120]
        response_hash = str(obs.get("response_hash") or obs.get("body_hash") or "")[:120]
        checked.append({"endpoint": endpoint, "status_code": status_code, "role": role, "expected_access": expected, "response_hash": response_hash})
        if obs.get("cross_account_access_proved") is True or obs.get("bola_proof") is True:
            findings.append(NormalizedFinding(
                title="Authorized BOLA/IDOR Proof From Supplied Evidence",
                severity="critical",
                category="authenticated_api",
                source="User-supplied authorized API observation",
                evidence=f"{role} received HTTP {status_code} on {endpoint}; response hash {response_hash or 'not supplied'}; expected access: {expected or 'not supplied'}",
                recommendation="Block cross-object access with object-level ownership checks and add regression tests using two users.",
                confidence="high",
                proof_level="user_supplied_authorized_test_proof",
            ))
        elif isinstance(status_code, int) and status_code in {401, 403}:
            continue
        elif endpoint and ADMIN_ENDPOINT_RE.search(endpoint) and isinstance(status_code, int) and status_code == 200 and not AUTH_HINT_RE.search(str(obs)):
            findings.append(NormalizedFinding(
                title="Public Admin/Debug/API Surface Reachable In Supplied Evidence",
                severity="high",
                category="authenticated_api",
                source="User-supplied API observation",
                evidence=f"{endpoint} returned HTTP 200 without clear auth evidence in supplied observation.",
                recommendation="Protect admin/debug/docs routes or restrict them to authenticated/admin networks.",
                confidence="medium",
                proof_level="supplied_http_observation",
            ))
        if SENSITIVE_FIELD_RE.search(str(obs.get("response_sample") or "")):
            findings.append(NormalizedFinding(
                title="Sensitive Field Appears In Supplied API Response Sample",
                severity="high",
                category="authenticated_api",
                source="User-supplied API response sample",
                evidence=f"Sensitive-looking field observed for {endpoint}. Response hash: {response_hash or 'not supplied'}",
                recommendation="Remove secrets/tokens from API responses and add response-schema tests.",
                confidence="medium",
                proof_level="supplied_response_sample",
            ))
    openapi_state = "Not Supplied"
    if openapi_json:
        data = _safe_json_loads(openapi_json)
        openapi_state = "Parsed" if isinstance(data, dict) else "Invalid JSON"
        if isinstance(data, dict):
            paths = data.get("paths", {}) if isinstance(data.get("paths"), dict) else {}
            public_admin = [path for path in paths.keys() if ADMIN_ENDPOINT_RE.search(str(path))][:20]
            if public_admin:
                findings.append(NormalizedFinding(
                    title="Admin/Debug/API Docs Paths Present In OpenAPI Evidence",
                    severity="medium",
                    category="api_design",
                    source="Supplied OpenAPI document",
                    evidence=", ".join(public_admin[:8]),
                    recommendation="Verify these routes require auth/admin roles and are not public in production.",
                    confidence="medium",
                    proof_level="supplied_openapi_schema",
                ))
    return {
        "phase": "54",
        "engine": "Authorized API Evidence Runner",
        "state": "Assessed" if checked or openapi_json else "Not Assessed",
        "api_base_url": api_base_url,
        "checked_observations": checked[:50],
        "openapi_state": openapi_state,
        "findings": [finding.to_dict() for finding in findings],
        "safe_scope": ["No brute force", "No credential stuffing", "No DoS", "No exploit payload spraying", "Only supplied/authorized evidence is classified as proof"],
    }


def run_wallet_ux_evidence_engine(wallet_evidence: dict[str, Any] | None = None, signature_samples: list[dict[str, Any]] | None = None, transaction_samples: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    findings: list[NormalizedFinding] = []
    evidence = wallet_evidence or {}
    text_blob = json.dumps(evidence, ensure_ascii=False)[:20000]
    if PRIVATE_KEY_REQUEST_RE.search(text_blob):
        findings.append(NormalizedFinding(
            title="Wallet Flow Mentions Private Key / Seed Phrase Collection",
            severity="critical",
            category="wallet_ux",
            source="Supplied wallet-flow evidence",
            evidence="Private key / seed phrase / mnemonic wording found in supplied wallet evidence.",
            recommendation="Never ask users for seed/private keys. Use wallet connect/signing flows only and remove this copy immediately.",
            confidence="high",
            proof_level="supplied_wallet_evidence",
        ))
    for idx, tx in enumerate(transaction_samples or [], start=1):
        if not isinstance(tx, dict):
            continue
        tx_text = json.dumps(tx, ensure_ascii=False)
        if UNLIMITED_APPROVAL_RE.search(tx_text):
            findings.append(NormalizedFinding(
                title="Unlimited Token Approval Evidence",
                severity="high",
                category="wallet_ux",
                source="Supplied transaction sample",
                evidence=f"Transaction sample #{idx} contains unlimited approval style value/copy.",
                recommendation="Default to exact-spend approvals, show spender, token, chain, amount, and revoke guidance.",
                confidence="high",
                proof_level="supplied_transaction_sample",
            ))
        if tx.get("chain_id") and evidence.get("expected_chain_id") and str(tx.get("chain_id")) != str(evidence.get("expected_chain_id")):
            findings.append(NormalizedFinding(
                title="Wallet Chain Mismatch Evidence",
                severity="high",
                category="wallet_ux",
                source="Supplied transaction sample",
                evidence=f"Expected chain {evidence.get('expected_chain_id')}, sample used {tx.get('chain_id')}.",
                recommendation="Block signing/transactions until the wallet is switched to the expected chain.",
                confidence="high",
                proof_level="supplied_transaction_sample",
            ))
    for idx, sig in enumerate(signature_samples or [], start=1):
        if not isinstance(sig, dict):
            continue
        message = str(sig.get("message") or sig.get("typed_data") or "")
        if RISKY_SIGNATURE_WORDS.search(message) and not sig.get("human_readable_purpose"):
            findings.append(NormalizedFinding(
                title="Risky Signature Message Lacks Clear Human-Readable Purpose",
                severity="medium",
                category="wallet_ux",
                source="Supplied signature sample",
                evidence=f"Signature sample #{idx}: {_short(message, 240)}",
                recommendation="Explain exactly what the user is signing, domain, chain, nonce, expiry, and whether funds/permissions are affected.",
                confidence="medium",
                proof_level="supplied_signature_sample",
            ))
    return {
        "phase": "55",
        "engine": "Wallet UX Risk Evidence Engine",
        "state": "Assessed" if evidence or signature_samples or transaction_samples else "Not Assessed",
        "findings": [finding.to_dict() for finding in findings],
        "not_performed": ["No wallet connection", "No wallet signing", "No private key collection", "No live transaction simulation"],
    }


def build_business_logic_review(business_context: dict[str, Any] | None = None) -> dict[str, Any]:
    context = business_context or {}
    roles = context.get("roles") if isinstance(context.get("roles"), list) else []
    critical_actions = context.get("critical_actions") if isinstance(context.get("critical_actions"), list) else []
    asset_flows = context.get("asset_flows") if isinstance(context.get("asset_flows"), list) else []
    test_cases: list[dict[str, Any]] = []
    for action in critical_actions[:30]:
        action_text = str(action)
        test_cases.append({
            "title": f"Role boundary test: {action_text[:90]}",
            "expected_evidence": "Normal user, owner/admin, and unrelated account results with status codes/response hashes.",
            "risk": "Business logic / authorization bypass",
            "status": "Manual Review Required",
        })
    for flow in asset_flows[:20]:
        flow_text = str(flow)
        test_cases.append({
            "title": f"Asset-flow double-spend/replay test: {flow_text[:90]}",
            "expected_evidence": "One successful action, repeat/replay attempt rejected, ledger balance unchanged.",
            "risk": "Payment/reward/accounting logic",
            "status": "Manual Review Required",
        })
    if not test_cases:
        test_cases = [
            {"title": "Cross-account object access test", "expected_evidence": "User A cannot read/update User B objects.", "risk": "BOLA/IDOR", "status": "Manual Review Required"},
            {"title": "Payment/report unlock bypass test", "expected_evidence": "Unverified payment cannot unlock paid report/export.", "risk": "Payment abuse", "status": "Manual Review Required"},
            {"title": "Referral/reward repeat-claim test", "expected_evidence": "Reward can be claimed once and cannot be replayed.", "risk": "Business logic abuse", "status": "Manual Review Required"},
        ]
    return {
        "phase": "56",
        "engine": "Business Logic Review Builder",
        "state": "Manual Review Required" if not context.get("reviewer_confirmed") else "Reviewed Evidence Supplied",
        "roles_seen": roles[:20],
        "critical_actions_seen": critical_actions[:30],
        "asset_flows_seen": asset_flows[:20],
        "test_cases": test_cases[:60],
        "guarantee": "Business-logic bugs are not invented. The engine creates role/asset-flow tests and records proof only when reviewer/user evidence is supplied.",
    }


def run_defi_simulation_framework(simulation_result: dict[str, Any] | None = None, protocol_context: dict[str, Any] | None = None) -> dict[str, Any]:
    findings: list[NormalizedFinding] = []
    sim = simulation_result or {}
    invariants = sim.get("invariants") if isinstance(sim.get("invariants"), list) else []
    for invariant in invariants:
        if not isinstance(invariant, dict):
            continue
        if invariant.get("passed") is False:
            findings.append(NormalizedFinding(
                title=f"Local Invariant Failed: {invariant.get('name') or 'Unnamed invariant'}",
                severity=str(invariant.get("severity") or "high").lower() if str(invariant.get("severity") or "high").lower() in {"critical", "high", "medium", "low", "info"} else "high",
                category="defi_economic",
                source="User-supplied local/testnet simulation artifact",
                evidence=_short(invariant.get("evidence") or invariant, 500),
                recommendation="Reproduce locally, patch the economic/accounting assumption, and rerun invariants before launch.",
                confidence="high" if invariant.get("evidence") else "medium",
                proof_level="supplied_local_simulation_result",
            ))
    scenario_hints = []
    ctx = protocol_context or {}
    if ctx.get("uses_oracle") and not ctx.get("oracle_twap_or_bounds"):
        scenario_hints.append("Oracle manipulation/TWAP-boundary review required")
    if ctx.get("has_flash_loan_surface"):
        scenario_hints.append("Flash-loan invariant/fork simulation required")
    if ctx.get("has_bridge_or_cross_chain"):
        scenario_hints.append("Bridge message replay/finality simulation required")
    return {
        "phase": "57",
        "engine": "DeFi / Economic Risk Simulation Framework",
        "state": "Assessed" if simulation_result else "Manual Review Required",
        "confirmed_simulation_findings": [finding.to_dict() for finding in findings],
        "scenario_hints": scenario_hints,
        "not_performed": ["No live exploit", "No mainnet attack", "No liquidity manipulation", "No unauthorized fork testing"],
        "guarantee": "Economic exploits are confirmed only from supplied local/testnet simulation artifacts or human review, not guessed from protocol type.",
    }


def build_reviewed_report_confirmation(review_context: dict[str, Any] | None = None) -> dict[str, Any]:
    ctx = review_context or {}
    reviewer = str(ctx.get("reviewer") or "").strip()
    triaged = int(ctx.get("triaged_findings_count") or 0) if str(ctx.get("triaged_findings_count") or "0").isdigit() else 0
    unresolved = int(ctx.get("unresolved_critical_high_count") or 0) if str(ctx.get("unresolved_critical_high_count") or "0").isdigit() else 0
    payment_verified = bool(ctx.get("payment_verified"))
    approved = bool(reviewer and triaged > 0 and unresolved == 0 and payment_verified)
    return {
        "phase": "58",
        "engine": "Reviewed Report Approval + Audit-Style Confirmation",
        "state": "Reviewed Report Ready" if approved else "Not Ready",
        "approved_for_reviewed_pre_audit_report": approved,
        "checks": {
            "reviewer_present": bool(reviewer),
            "triaged_findings_count": triaged,
            "unresolved_critical_high_count": unresolved,
            "payment_verified_or_admin_override": payment_verified,
        },
        "allowed_wording": "Reviewed pre-audit readiness report" if approved else "Scanner result / manual review pending",
        "blocked_wording": ["certified audit", "100% secure", "all vulnerabilities found", "audited by Web3Guard", "OpenZeppelin/CertiK/Hacken level"],
        "guarantee": "Audit-style confirmation means reviewer workflow completed for supplied evidence. It is not a certified audit or all-bugs guarantee.",
    }


async def build_accuracy_upgrade_package(unified_result: dict[str, Any], payload: Any) -> dict[str, Any]:
    surface_hints = unified_result.get("surface_hints", {}) if isinstance(unified_result, dict) else {}
    github_summary = surface_hints.get("github_dependency_risk", {}) if isinstance(surface_hints, dict) else {}
    manifests = github_summary.get("dependency_manifests", []) if isinstance(github_summary, dict) else []

    def parsed_json_attr(name: str, default: Any) -> Any:
        parsed = _safe_json_loads(getattr(payload, name, None))
        return parsed if parsed is not None else default

    api_observations = parsed_json_attr("api_observations_json", [])
    if not isinstance(api_observations, list):
        api_observations = []
    wallet_json = parsed_json_attr("wallet_evidence_json", {})
    if not isinstance(wallet_json, dict):
        wallet_json = {}
    signature_samples = parsed_json_attr("signature_samples_json", [])
    if not isinstance(signature_samples, list):
        signature_samples = []
    transaction_samples = parsed_json_attr("transaction_samples_json", [])
    if not isinstance(transaction_samples, list):
        transaction_samples = []
    business_context = parsed_json_attr("business_context_json", {})
    if not isinstance(business_context, dict):
        business_context = {}
    defi_simulation_json = parsed_json_attr("defi_simulation_json", None)
    if not isinstance(defi_simulation_json, dict):
        defi_simulation_json = None
    protocol_context = parsed_json_attr("protocol_context_json", {})
    if not isinstance(protocol_context, dict):
        protocol_context = {"project_type": getattr(payload, "project_type", None), "chain": getattr(payload, "chain", None)}
    review_context = parsed_json_attr("review_context_json", {})
    if not isinstance(review_context, dict):
        review_context = {}

    dependency_engine = await run_dependency_osv_engine(manifests=manifests if isinstance(manifests, list) else [])
    static_worker = run_static_worker_bridge(getattr(payload, "solidity_code", None), getattr(payload, "project_name", None))
    api_evidence = run_authorized_api_evidence_runner(api_base_url=getattr(payload, "api_base_url", None), observations=api_observations, openapi_json=getattr(payload, "openapi_json", None))
    wallet_evidence = run_wallet_ux_evidence_engine(wallet_json, signature_samples, transaction_samples)
    business_logic = build_business_logic_review(business_context or {"critical_actions": ["report unlock", "scan ownership", "paid export"], "asset_flows": ["₹999 pilot payment to report export"]})
    defi_simulation = run_defi_simulation_framework(simulation_result=defi_simulation_json, protocol_context=protocol_context)
    reviewed_confirmation = build_reviewed_report_confirmation(review_context)
    return {
        "engine_version": ENGINE_VERSION,
        "generated_at": _now(),
        "phases": {
            "52_dependency_osv": dependency_engine,
            "53_static_backend_worker": static_worker,
            "54_authorized_api_evidence": api_evidence,
            "55_wallet_ux_evidence": wallet_evidence,
            "56_business_logic_review": business_logic,
            "57_defi_economic_simulation": defi_simulation,
            "58_reviewed_report_confirmation": reviewed_confirmation,
        },
        "output_authenticity_guarantee": "Every visible finding must be backed by observed evidence, tool/provider output, supplied artifact, or manual triage. Missing coverage is Not Assessed; all-bugs/certified-audit claims remain blocked.",
        "remaining_truth_boundary": "Accuracy can improve with more evidence and tools, but no automated scanner can guarantee all vulnerabilities are found.",
    }


def accuracy_stack_status() -> dict[str, Any]:
    return {
        "ok": True,
        "engine_version": ENGINE_VERSION,
        "phases": [
            {"phase": 52, "name": "GitHub + OSV Real Dependency Engine", "realness": "OSV advisories only from exact dependency evidence"},
            {"phase": 53, "name": "Backend Slither/Semgrep Worker Runner", "realness": "Actual subprocess output only when installed/enabled"},
            {"phase": 54, "name": "Authorized API Evidence Runner", "realness": "Only supplied/authorized observations become proof"},
            {"phase": 55, "name": "Wallet UX Risk Evidence Engine", "realness": "No wallet signing; only supplied transaction/signature/copy evidence"},
            {"phase": 56, "name": "Business Logic Review Builder", "realness": "Manual proof workflow; no invented business-logic bugs"},
            {"phase": 57, "name": "DeFi/Economic Risk Simulation Framework", "realness": "Local/testnet simulation artifacts only"},
            {"phase": 58, "name": "Reviewed Report Approval + Audit-Style Confirmation", "realness": "Triage/reviewer/payment gates; no certified-audit claim"},
        ],
        "providers": {
            "osv_api_base": settings.osv_api_base,
            "provider_live_network_enabled": settings.provider_live_network_enabled,
            "static_analysis_enabled": settings.static_analysis_enabled,
            "slither_binary_present": shutil.which(settings.slither_binary or "slither") is not None,
            "semgrep_binary_present": shutil.which(settings.semgrep_binary or "semgrep") is not None,
        },
        "blocked_claims": ["100% secure", "all vulnerabilities found", "certified audit", "audit-company level confirmed without human reviewers"],
    }
