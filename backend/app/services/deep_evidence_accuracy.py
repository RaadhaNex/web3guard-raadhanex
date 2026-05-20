from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse

ENGINE_VERSION = "web3guard-deep-evidence-accuracy-phases-68-77-v1.0"

HIGH_RISK_PATH_RE = re.compile(r"(?i)(/admin|/debug|/swagger|/openapi|/docs|/redoc|/graphql|/api-docs|/actuator|/internal)")
API_PATH_RE = re.compile(r"(?i)(/api/|/rpc|/graphql|/webhook|/auth|/login|/token|/payment|/report|/admin)")
SECRET_WORD_RE = re.compile(r"(?i)(secret|private[_-]?key|mnemonic|seed[_ -]?phrase|service[_-]?role|database[_-]?url|api[_-]?key|access[_-]?token|refresh[_-]?token)")
UNLIMITED_RE = re.compile(r"(?i)(unlimited|infinite|maxuint|ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff|setapprovalforall)")
DANGEROUS_SIGNATURE_RE = re.compile(r"(?i)(permit|permit2|delegate|setapprovalforall|approve|airdrop|claim|free mint|verify wallet|sign in)")
FAIL_RE = re.compile(r"(?i)(fail|failed|falsif|counterexample|panic|revert|invariant.*break|property.*fail)")
PASS_RE = re.compile(r"(?i)(pass|passed|ok|success)")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8", errors="ignore")).hexdigest()


def _short(value: Any, limit: int = 900) -> str:
    text = str(value or "")
    text = _redact(text)
    return text if len(text) <= limit else text[:limit] + "..."


def _redact(text: str) -> str:
    text = re.sub(r"(?i)(secret|token|password|private[_-]?key|mnemonic|seed[_ -]?phrase|service[_-]?role|database[_-]?url|api[_-]?key)(['\"\s:=]+)([^'\"\s]{6,})", r"\1\2<redacted>", text)
    text = re.sub(r"0x[a-fA-F0-9]{64}", "0x<redacted-private-key-like-value>", text)
    text = re.sub(r"sk-[A-Za-z0-9_\-]{16,}", "sk-<redacted>", text)
    return text


def _safe_json_loads(value: str | None) -> Any | None:
    if not value or not str(value).strip():
        return None
    try:
        return json.loads(value)
    except Exception:
        return None


def _as_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if isinstance(value, dict):
        for key in ("items", "findings", "results", "vulnerabilities", "issues", "leaks", "tests", "entries"):
            if isinstance(value.get(key), list):
                return value[key]
        return [value]
    return []


def _finding(*, phase: str, title: str, severity: str, category: str, source: str, evidence: dict[str, Any], recommendation: str, confidence: str = "medium", proof_level: str = "observed_evidence", module: str = "deep_analysis") -> dict[str, Any]:
    evidence_json = json.dumps(evidence, sort_keys=True, default=str)[:4000]
    fid = f"phase{phase}-{_hash(title + evidence_json)[:12]}"
    checked = evidence.get("checked_url") or evidence.get("url") or evidence.get("path") or evidence.get("file") or evidence.get("endpoint") or "supplied evidence"
    return {
        "id": fid,
        "phase": phase,
        "module": module,
        "severity": severity,
        "title": title,
        "description": f"{title}. This item is shown only because Web3Guard captured or received concrete evidence from {source}.",
        "confidence": confidence,
        "source": source,
        "category": category,
        "rule_id": f"PH{phase}-{category.upper().replace('_', '-')}",
        "business_impact": "This can affect production readiness, customer trust, funds safety, access control, or incident response depending on launch context.",
        "developer_explanation": f"Evidence location: {checked}. Review the raw evidence and confirm exploitability/scope before making public claims.",
        "recommendation": recommendation,
        "proof_level": proof_level,
        "raw_evidence": evidence,
        "evidence_quality": {
            "source": source,
            "checked": checked,
            "has_raw_evidence": bool(evidence),
            "redaction_applied": True,
            "claim_boundary": "Evidence-backed finding, not a certified audit or all-bugs guarantee.",
        },
        "reproduction_steps": [
            f"Open or inspect: {checked}",
            "Compare the captured evidence with expected secure behavior.",
            "Fix the control/config/code path, then rerun Web3Guard and verify the finding disappears or becomes triaged as fixed.",
        ],
        "paid_review_recommended": severity in {"critical", "high"},
    }


def _parse_har(value: Any) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    endpoints: dict[str, dict[str, Any]] = {}
    console_or_network_errors: list[dict[str, Any]] = []
    if not isinstance(value, dict):
        return {"state": "Not Assessed", "entries_seen": 0, "endpoints": [], "findings": [], "reason": "No HAR/crawler artifact JSON supplied."}
    entries = value.get("log", {}).get("entries") if isinstance(value.get("log"), dict) else value.get("entries")
    if not isinstance(entries, list):
        entries = []
    for entry in entries[:250]:
        if not isinstance(entry, dict):
            continue
        request = entry.get("request") if isinstance(entry.get("request"), dict) else {}
        response = entry.get("response") if isinstance(entry.get("response"), dict) else {}
        url = str(request.get("url") or entry.get("url") or "")
        method = str(request.get("method") or entry.get("method") or "GET")
        status = int(response.get("status") or entry.get("status") or 0) if str(response.get("status") or entry.get("status") or "0").isdigit() else 0
        parsed = urlparse(url)
        path = parsed.path or url
        if API_PATH_RE.search(path):
            endpoints[path] = {"url": url, "method": method, "status": status, "host": parsed.netloc, "source": "HAR/network artifact"}
        if status >= 500:
            console_or_network_errors.append({"url": url, "method": method, "status": status})
            findings.append(_finding(
                phase="69",
                module="website_advanced",
                title="Network Trace Shows Server Error",
                severity="medium",
                category="runtime_network_error",
                source="User-supplied HAR/network artifact",
                evidence={"checked_url": url, "method": method, "status_code": status},
                recommendation="Investigate the failing endpoint, fix production error handling, and add monitoring for 5xx spikes.",
                confidence="high",
            ))
        if status == 200 and HIGH_RISK_PATH_RE.search(path):
            findings.append(_finding(
                phase="69",
                module="website_advanced",
                title="High-Risk Route Was Reachable In Browser Trace",
                severity="medium",
                category="reachable_high_risk_route",
                source="User-supplied HAR/network artifact",
                evidence={"checked_url": url, "method": method, "status_code": status, "path": path},
                recommendation="Confirm this route is intended to be public. Protect admin/debug/docs routes in production or require auth.",
                confidence="medium",
            ))
    return {
        "state": "Assessed" if entries else "Not Assessed",
        "entries_seen": len(entries),
        "api_endpoint_count": len(endpoints),
        "endpoints": list(endpoints.values())[:80],
        "network_error_count": len(console_or_network_errors),
        "network_errors": console_or_network_errors[:25],
        "findings": findings,
    }


def _parse_auth_api_evidence(value: Any) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    observations = _as_list(value)
    for obs in observations[:120]:
        if not isinstance(obs, dict):
            continue
        endpoint = str(obs.get("endpoint") or obs.get("url") or obs.get("path") or "API observation")
        status = obs.get("status_code") or obs.get("actual_status")
        expected = obs.get("expected_status")
        role = obs.get("role") or obs.get("token_role") or obs.get("actor")
        if obs.get("cross_account_access_proved") is True or obs.get("idor_proved") is True or obs.get("bola_proved") is True:
            findings.append(_finding(
                phase="70",
                module="api_deep",
                title="Authorized Evidence Indicates Possible BOLA/IDOR",
                severity="critical",
                category="object_authorization",
                source="User-supplied authorized API observation",
                evidence={"endpoint": endpoint, "status_code": status, "role": role, "response_hash": obs.get("response_hash"), "evidence_note": _short(obs.get("evidence") or obs)},
                recommendation="Enforce object ownership/tenant checks on this endpoint. Re-test with two separate authorized test users.",
                confidence="high",
                proof_level="authorized_reproduction_evidence",
            ))
        if (str(expected) in {"401", "403"} and str(status).startswith("2")) or obs.get("expected_unauthorized_but_allowed") is True:
            findings.append(_finding(
                phase="70",
                module="api_deep",
                title="Endpoint Allowed Access When Denial Was Expected",
                severity="high",
                category="authorization_bypass_evidence",
                source="User-supplied authorized API observation",
                evidence={"endpoint": endpoint, "expected_status": expected, "actual_status": status, "role": role, "response_hash": obs.get("response_hash")},
                recommendation="Add explicit role/object authorization and regression tests for this endpoint.",
                confidence="high",
            ))
        if obs.get("webhook_signature_missing") is True or obs.get("webhook_without_signature_accepted") is True:
            findings.append(_finding(
                phase="70",
                module="api_deep",
                title="Webhook Evidence Indicates Missing Signature Verification",
                severity="high",
                category="webhook_authentication",
                source="User-supplied API/webhook observation",
                evidence={"endpoint": endpoint, "status_code": status, "provider": obs.get("provider"), "response_hash": obs.get("response_hash")},
                recommendation="Verify provider signatures with the raw request body before changing payment/report/subscription state.",
                confidence="high",
            ))
        sensitive = obs.get("sensitive_fields")
        if isinstance(sensitive, list) and sensitive:
            findings.append(_finding(
                phase="70",
                module="api_deep",
                title="API Response Evidence Contains Sensitive Field Names",
                severity="medium",
                category="sensitive_response_fields",
                source="User-supplied API observation",
                evidence={"endpoint": endpoint, "fields": sensitive[:20], "response_hash": obs.get("response_hash")},
                recommendation="Remove secrets/tokens/internal fields from public or lower-privileged API responses.",
                confidence="medium",
            ))
    return {"state": "Assessed" if observations else "Not Assessed", "observation_count": len(observations), "findings": findings}


def _parse_security_artifacts(value: Any) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    tools: list[str] = []
    if value is None:
        return {"state": "Not Assessed", "tools": [], "findings": [], "reason": "No gitleaks/trufflehog/npm-audit/pip-audit artifact supplied."}
    blobs = value if isinstance(value, dict) else {"artifact": value}
    if not isinstance(blobs, dict):
        return {"state": "Input Rejected", "tools": [], "findings": [], "reason": "Security artifact must be JSON object/list."}
    # Secret scanners: gitleaks/trufflehog usually output arrays or objects with results.
    secret_items: list[Any] = []
    for key in ("gitleaks", "trufflehog", "secret_scanning", "secrets", "leaks", "results"):
        part = blobs.get(key)
        if part is not None:
            tools.append(str(key))
            secret_items.extend(_as_list(part))
    for item in secret_items[:80]:
        if not isinstance(item, dict):
            continue
        rule = str(item.get("RuleID") or item.get("rule") or item.get("DetectorName") or item.get("type") or "secret-like evidence")
        file_path = str(item.get("File") or item.get("file") or item.get("SourceMetadata", {}).get("Data", {}).get("Filesystem", {}).get("file") if isinstance(item.get("SourceMetadata"), dict) else item.get("path") or "artifact")
        if rule or SECRET_WORD_RE.search(json.dumps(item, default=str)[:1000]):
            findings.append(_finding(
                phase="72",
                module="github",
                title="Secret Scanner Artifact Contains Secret-Like Finding",
                severity="critical",
                category="secret_scanning_artifact",
                source="User-supplied secret-scanner artifact",
                evidence={"file": file_path, "rule": rule, "redacted_artifact": _short(item)},
                recommendation="Rotate any exposed secret, remove it from git history if real, and add secret scanning to CI.",
                confidence="high",
                proof_level="tool_artifact_evidence",
            ))
    # SCA tools: npm audit/pip-audit/osv style.
    vuln_items: list[Any] = []
    for key in ("npm_audit", "pip_audit", "osv", "sca", "vulnerabilities"):
        part = blobs.get(key)
        if part is not None:
            tools.append(str(key))
            vuln_items.extend(_as_list(part if key == "vulnerabilities" else part))
    for item in vuln_items[:120]:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or item.get("package") or item.get("dependency") or item.get("module_name") or "dependency")
        vuln_id = str(item.get("id") or item.get("cve") or item.get("advisory") or item.get("ghsa") or item.get("source") or "advisory")
        sev = str(item.get("severity") or item.get("cvss_severity") or "medium").lower()
        severity = "high" if sev in {"critical", "high"} else "medium" if sev in {"moderate", "medium"} else "low"
        if name != "dependency" or vuln_id != "advisory":
            findings.append(_finding(
                phase="72",
                module="github",
                title="Dependency Vulnerability Artifact Finding",
                severity=severity,
                category="dependency_vulnerability_artifact",
                source="User-supplied SCA artifact",
                evidence={"package": name, "advisory_id": vuln_id, "installed_version": item.get("version") or item.get("installed_version"), "fixed_version": item.get("fixed_version"), "raw": _short(item)},
                recommendation="Upgrade to the fixed version or apply the advisory mitigation. Re-run SCA to verify the advisory is gone.",
                confidence="high",
                proof_level="tool_artifact_evidence",
            ))
    return {"state": "Assessed", "tools": sorted(set(tools)) or ["generic_json_artifact"], "findings": findings, "artifact_keys": sorted(blobs.keys())[:20]}


def _parse_wallet_samples(wallet_json: Any, tx_json: Any, sig_json: Any) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    wallet_text = json.dumps(wallet_json, default=str) if wallet_json is not None else ""
    txs = _as_list(tx_json)
    sigs = _as_list(sig_json)
    if SECRET_WORD_RE.search(wallet_text):
        findings.append(_finding(
            phase="75",
            module="wallet_risk",
            title="Wallet Flow Evidence Mentions Secret/Seed Phrase Handling",
            severity="critical",
            category="wallet_secret_request",
            source="User-supplied wallet evidence",
            evidence={"redacted_preview": _short(wallet_text)},
            recommendation="Never request private keys, seed phrases, mnemonics, or recovery phrases. Use wallet-provider connection only.",
            confidence="medium",
        ))
    for tx in txs[:60]:
        text = json.dumps(tx, default=str)
        if UNLIMITED_RE.search(text):
            findings.append(_finding(
                phase="75",
                module="wallet_risk",
                title="Transaction Sample Indicates Unlimited Approval Risk",
                severity="high",
                category="unlimited_approval",
                source="User-supplied transaction sample",
                evidence={"transaction_preview": _short(tx), "spender": tx.get("spender") if isinstance(tx, dict) else None, "chain_id": tx.get("chain_id") if isinstance(tx, dict) else None},
                recommendation="Use exact approval amounts, clear spender labels, revoke guidance, and transaction previews before signing.",
                confidence="high",
            ))
        if isinstance(tx, dict) and tx.get("expected_chain_id") and tx.get("chain_id") and str(tx.get("expected_chain_id")) != str(tx.get("chain_id")):
            findings.append(_finding(
                phase="75",
                module="wallet_risk",
                title="Transaction Sample Shows Chain Mismatch",
                severity="high",
                category="wallet_chain_mismatch",
                source="User-supplied transaction sample",
                evidence={"expected_chain_id": tx.get("expected_chain_id"), "actual_chain_id": tx.get("chain_id"), "method": tx.get("method")},
                recommendation="Block signing until wallet chain matches the intended chain and show a clear chain-switch prompt.",
                confidence="high",
            ))
    for sig in sigs[:60]:
        text = json.dumps(sig, default=str)
        if DANGEROUS_SIGNATURE_RE.search(text) and not (isinstance(sig, dict) and sig.get("human_readable_purpose")):
            findings.append(_finding(
                phase="75",
                module="wallet_risk",
                title="Signature Sample Has Risky Purpose Without Clear Human-Readable Context",
                severity="medium",
                category="signature_clarity",
                source="User-supplied signature sample",
                evidence={"signature_preview": _short(sig)},
                recommendation="Show purpose, domain, chain, contract, expiry, nonce, and risk copy before signature requests.",
                confidence="medium",
            ))
    supplied = bool(wallet_json is not None or txs or sigs)
    return {"state": "Assessed" if supplied else "Not Assessed", "transaction_samples": len(txs), "signature_samples": len(sigs), "findings": findings}


def _parse_smart_contract_artifacts(foundry_output: str | None, echidna_json: Any, invariant_json: Any) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    artifacts_seen = 0
    if foundry_output and foundry_output.strip():
        artifacts_seen += 1
        if FAIL_RE.search(foundry_output):
            findings.append(_finding(
                phase="74",
                module="deep_analysis",
                title="Foundry Test Artifact Indicates Failing Test/Invariant",
                severity="high",
                category="foundry_test_failure",
                source="User-supplied Foundry/forge output",
                evidence={"artifact": "foundry_test_output", "redacted_preview": _short(foundry_output, 1400)},
                recommendation="Fix the failing test/invariant, add regression coverage, and rerun forge tests before launch.",
                confidence="high",
                proof_level="local_test_artifact",
            ))
    for source_name, artifact in (("Echidna", echidna_json), ("Invariant/simulation", invariant_json)):
        if artifact is None:
            continue
        artifacts_seen += 1
        items = _as_list(artifact)
        raw_text = json.dumps(artifact, default=str)[:6000]
        for item in items[:80]:
            item_text = json.dumps(item, default=str)
            if (isinstance(item, dict) and str(item.get("status") or item.get("result") or "").lower() in {"failed", "fail", "falsified"}) or FAIL_RE.search(item_text):
                name = item.get("name") or item.get("property") or item.get("test") if isinstance(item, dict) else "invariant"
                findings.append(_finding(
                    phase="74",
                    module="deep_analysis",
                    title=f"{source_name} Artifact Shows Failed Property",
                    severity="high",
                    category="invariant_failure_artifact",
                    source=f"User-supplied {source_name} artifact",
                    evidence={"property": name, "artifact_preview": _short(item)},
                    recommendation="Treat failed invariants as launch blockers until the property is fixed or explicitly documented as an expected false positive.",
                    confidence="high",
                    proof_level="local_test_artifact",
                ))
        if not findings and FAIL_RE.search(raw_text):
            findings.append(_finding(
                phase="74",
                module="deep_analysis",
                title=f"{source_name} Artifact Contains Failure Marker",
                severity="medium",
                category="simulation_failure_marker",
                source=f"User-supplied {source_name} artifact",
                evidence={"artifact_preview": _short(raw_text)},
                recommendation="Review the artifact manually and isolate the failing scenario before launch.",
                confidence="medium",
            ))
    return {"state": "Assessed" if artifacts_seen else "Not Assessed", "artifact_count": artifacts_seen, "findings": findings}


def _parse_business_logic(value: Any) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    tests: list[dict[str, Any]] = []
    if not isinstance(value, dict):
        return {"state": "Not Assessed", "generated_tests": [], "findings": [], "reason": "No business context JSON supplied."}
    roles = value.get("roles") if isinstance(value.get("roles"), list) else []
    actions = value.get("critical_actions") if isinstance(value.get("critical_actions"), list) else []
    flows = value.get("asset_flows") if isinstance(value.get("asset_flows"), list) else []
    abuse_cases = value.get("abuse_cases") if isinstance(value.get("abuse_cases"), list) else []
    for action in actions[:20]:
        tests.append({"title": f"Verify role authorization for {action}", "expected": "Only intended role can execute", "evidence_needed": "two-account test result or reviewer note"})
    for flow in flows[:20]:
        tests.append({"title": f"Verify state transition/payment integrity for {flow}", "expected": "No replay/unverified unlock/double claim", "evidence_needed": "transaction/log/report ID proof"})
    for abuse in abuse_cases[:50]:
        if not isinstance(abuse, dict):
            continue
        if abuse.get("proved") is True:
            findings.append(_finding(
                phase="76",
                module="api_deep",
                title="Business Logic Abuse Case Marked Proven",
                severity=str(abuse.get("severity") or "high").lower() if str(abuse.get("severity") or "high").lower() in {"critical", "high", "medium", "low", "info"} else "high",
                category="business_logic_abuse",
                source="User-supplied business logic evidence",
                evidence={"case": abuse.get("title") or abuse.get("case"), "flow": abuse.get("flow"), "evidence": _short(abuse.get("evidence") or abuse)},
                recommendation="Patch the affected business rule, add server-side validation, and add regression tests for the abuse case.",
                confidence="high",
                proof_level="manual_reproduction_evidence",
            ))
    return {"state": "Assessed", "roles": roles, "critical_actions": actions, "asset_flows": flows, "generated_tests": tests[:30], "findings": findings}


def _accuracy_feedback(value: Any) -> dict[str, Any]:
    if value is None:
        return {"state": "Not Assessed", "reviewed_findings": 0, "false_positive_rate": None, "reason": "No reviewer feedback/benchmark artifact supplied."}
    items = _as_list(value)
    if not items:
        return {"state": "Input Rejected", "reviewed_findings": 0, "false_positive_rate": None}
    reviewed = [item for item in items if isinstance(item, dict)]
    fp = sum(1 for item in reviewed if str(item.get("status") or "").lower() in {"false_positive", "false positive", "rejected"})
    confirmed = sum(1 for item in reviewed if str(item.get("status") or "").lower() in {"confirmed", "true_positive", "fixed", "accepted_risk"})
    total = len(reviewed)
    fpr = round((fp / total) * 100, 2) if total else None
    return {
        "state": "Assessed",
        "reviewed_findings": total,
        "confirmed_or_actioned": confirmed,
        "false_positive_count": fp,
        "false_positive_rate_percent": fpr,
        "tuning_rule": "Use this feedback to downgrade noisy rules, improve evidence requirements, and track accuracy over time.",
    }


def _phase_status(state: str, findings: int = 0, evidence: str = "") -> dict[str, Any]:
    return {"state": state, "findings": findings, "evidence": evidence}


async def build_deep_evidence_accuracy_package(unified_result: dict[str, Any], payload: Any) -> dict[str, Any]:
    har = _safe_json_loads(getattr(payload, "har_json", None)) or _safe_json_loads(getattr(payload, "crawler_artifact_json", None))
    auth_context = _safe_json_loads(getattr(payload, "auth_test_context_json", None)) or _safe_json_loads(getattr(payload, "api_observations_json", None))
    security_artifacts = _safe_json_loads(getattr(payload, "security_tool_artifacts_json", None))
    wallet_json = _safe_json_loads(getattr(payload, "wallet_evidence_json", None))
    tx_json = _safe_json_loads(getattr(payload, "transaction_samples_json", None))
    sig_json = _safe_json_loads(getattr(payload, "signature_samples_json", None))
    business_json = _safe_json_loads(getattr(payload, "business_context_json", None))
    echidna_json = _safe_json_loads(getattr(payload, "echidna_output_json", None))
    invariant_json = _safe_json_loads(getattr(payload, "invariant_artifact_json", None)) or _safe_json_loads(getattr(payload, "defi_simulation_json", None))
    feedback_json = _safe_json_loads(getattr(payload, "accuracy_feedback_json", None))

    phase69 = _parse_har(har)
    phase70 = _parse_auth_api_evidence(auth_context)
    phase72 = _parse_security_artifacts(security_artifacts)
    phase74 = _parse_smart_contract_artifacts(getattr(payload, "foundry_test_output", None), echidna_json, invariant_json)
    phase75 = _parse_wallet_samples(wallet_json, tx_json, sig_json)
    phase76 = _parse_business_logic(business_json)
    phase77 = _accuracy_feedback(feedback_json)

    all_findings: list[dict[str, Any]] = []
    for phase in (phase69, phase70, phase72, phase74, phase75, phase76):
        all_findings.extend([item for item in phase.get("findings", []) if isinstance(item, dict)])

    by_severity = {key: 0 for key in ["critical", "high", "medium", "low", "info"]}
    by_phase: dict[str, int] = {}
    for finding in all_findings:
        sev = str(finding.get("severity") or "info")
        by_severity[sev if sev in by_severity else "info"] += 1
        phase = str(finding.get("phase") or "unknown")
        by_phase[phase] = by_phase.get(phase, 0) + 1

    assessed_phases = 0
    phase_map = {
        "68": _phase_status("Design Ready", 0, "In-memory job/status APIs provide a safe foundation for queued worker execution without pretending background workers are running."),
        "69": _phase_status(str(phase69.get("state")), len(phase69.get("findings", [])), f"HAR entries: {phase69.get('entries_seen', 0)}; API endpoints: {phase69.get('api_endpoint_count', 0)}"),
        "70": _phase_status(str(phase70.get("state")), len(phase70.get("findings", [])), f"Authorized observations: {phase70.get('observation_count', 0)}"),
        "71": _phase_status("Connected via existing GitHub scanner", 0, "Deep repo signals are handled by GitHub scanner + Phase 72 artifacts. No fake private repo clone."),
        "72": _phase_status(str(phase72.get("state")), len(phase72.get("findings", [])), f"Tools/artifact keys: {', '.join(phase72.get('tools', []) or [])}"),
        "73": _phase_status("Artifact/runner bridge", 0, "Backend Slither/Semgrep artifacts are accepted; compile/dependency install stays disabled unless isolated worker is configured."),
        "74": _phase_status(str(phase74.get("state")), len(phase74.get("findings", [])), f"Local test/simulation artifacts: {phase74.get('artifact_count', 0)}"),
        "75": _phase_status(str(phase75.get("state")), len(phase75.get("findings", [])), f"Transactions: {phase75.get('transaction_samples', 0)}; signatures: {phase75.get('signature_samples', 0)}"),
        "76": _phase_status(str(phase76.get("state")), len(phase76.get("findings", [])), f"Generated review tests: {len(phase76.get('generated_tests', []) or [])}"),
        "77": _phase_status(str(phase77.get("state")), 0, f"Reviewed findings: {phase77.get('reviewed_findings', 0)}; FP rate: {phase77.get('false_positive_rate_percent')}")
    }
    for item in phase_map.values():
        if item["state"] not in {"Not Assessed", "Input Rejected"}:
            assessed_phases += 1

    score_penalty = 0
    for sev, count in by_severity.items():
        score_penalty += count * {"critical": 18, "high": 11, "medium": 6, "low": 2, "info": 1}.get(sev, 1)
    evidence_score = max(0, min(100, 100 - score_penalty))
    if not all_findings and assessed_phases <= 2:
        evidence_score = None

    return {
        "phase_range": "68-77",
        "engine_version": ENGINE_VERSION,
        "generated_at": _now(),
        "state": "Assessed" if assessed_phases > 1 else "Needs Evidence",
        "real_only_rule": "Findings are created only from safe passive evidence, user-supplied artifacts, authorized observations, or manual reviewer feedback. Missing inputs remain Not Assessed.",
        "output_authenticity_guarantee": "Every visible Phase 68-77 finding includes source, checked URL/path/file, raw/redacted evidence, reproduction steps, and a fix direction.",
        "safe_boundaries": [
            "No brute force, credential stuffing, DoS, wallet signing, private-key collection, or live exploit automation.",
            "Authenticated checks require user-supplied test tokens/observations and explicit authorization.",
            "Fuzz/invariant/economic risks are artifact-based unless an isolated worker is configured separately.",
        ],
        "summary": {
            "assessed_phase_count": assessed_phases,
            "total_phase_count": 10,
            "total_findings": len(all_findings),
            "critical_high_findings": by_severity["critical"] + by_severity["high"],
            "evidence_score": evidence_score,
            "by_severity": by_severity,
            "by_phase": by_phase,
        },
        "phases": phase_map,
        "crawler_har": phase69,
        "authorized_api": phase70,
        "repo_sca_secrets": phase72,
        "smart_contract_artifacts": phase74,
        "wallet_decoder": phase75,
        "business_logic_review": phase76,
        "accuracy_feedback": phase77,
        "normalized_findings": all_findings,
        "next_accuracy_steps": [
            "Provide Playwright/HAR artifact from a real authorized browser session to expose JS-rendered API calls.",
            "Provide two authorized API observations for user A/user B object checks to confirm or reject BOLA/IDOR.",
            "Provide gitleaks/trufflehog/npm-audit/pip-audit/OSV artifacts for repo secrets and dependency vulnerabilities.",
            "Provide Foundry/Echidna/invariant artifacts for DeFi or smart-contract economic assertions.",
            "Use manual review feedback to reduce false positives and improve severity mapping.",
        ],
    }


def phase68_77_status() -> dict[str, Any]:
    return {
        "ok": True,
        "phase_range": "68-77",
        "engine_version": ENGINE_VERSION,
        "purpose": "Deep evidence accuracy layer: worker-ready scan jobs, HAR/API capture artifacts, authorized API evidence, SCA/secrets artifacts, compile/fuzz/invariant artifacts, wallet decoding, repro proof format, and accuracy feedback.",
        "real_only_boundary": "This layer increases accuracy by accepting real evidence/artifacts. It never claims all bugs are found and never fakes unavailable tools.",
        "phases": {
            "68": "Scan job queue + sandbox worker readiness",
            "69": "Browser/HAR/API capture artifact analysis",
            "70": "Authorized API/BOLA evidence harness",
            "71": "GitHub deep repo risk scanner linkage",
            "72": "SCA + secrets artifact engine",
            "73": "Smart contract compile/static runner hardening bridge",
            "74": "Fuzz/invariant/local simulation artifact analyzer",
            "75": "Wallet transaction/signature decoder",
            "76": "Evidence quality + reproducible steps format",
            "77": "Benchmark/false-positive accuracy dashboard",
        },
    }
