from __future__ import annotations

import json
import re
import shutil
from datetime import datetime, timezone
from typing import Any

from app.core.config import settings

ENGINE_VERSION = "web3guard-accuracy-hardening-phase-59-v1.0"

BLOCKED_CLAIM_RE = re.compile(
    r"(?i)(100%\s*secure|all\s+vulnerabilities\s+found|certified\s+audit|audited\s+by\s+web3guard|"
    r"openzeppelin\s+certified|certik\s+level|hacken\s+level|guaranteed\s+safe|guaranteed\s+all\s+bugs)"
)
SECRET_TOKEN_RE = re.compile(r"(?i)(bearer\s+[a-z0-9._\-]{18,}|x-api-key\s*[:=]\s*[a-z0-9._\-]{12,}|secret|private[_\- ]?key|mnemonic|seed\s+phrase)")
SEVERITIES = {"critical", "high", "medium", "low", "info"}
TRIAGE_STATES = {"confirmed", "false_positive", "needs_evidence", "accepted_risk", "fixed", "duplicate"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _short(value: Any, limit: int = 900) -> str:
    text = str(value or "")
    return text if len(text) <= limit else text[:limit] + "..."


def _safe_json_loads(value: str | None, fallback: Any) -> Any:
    if not value or not str(value).strip():
        return fallback
    try:
        return json.loads(value)
    except Exception:
        return fallback


def _finding_key(value: Any) -> str:
    if isinstance(value, dict):
        for key in ("id", "rule_id", "check", "title", "name", "category"):
            if value.get(key):
                return str(value.get(key)).strip().lower()
        return json.dumps(value, sort_keys=True, default=str)[:160].lower()
    return str(value or "").strip().lower()


def _severity(value: Any, default: str = "medium") -> str:
    normal = str(value or default).strip().lower()
    return normal if normal in SEVERITIES else default


def benchmark_scanner_accuracy(samples: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Compare scanner output against user-supplied expected findings.

    This does not claim global accuracy. It produces measurable precision/recall only for the supplied benchmark set.
    """
    samples = samples or []
    if not samples:
        return {
            "phase": 59,
            "engine": "Benchmark Accuracy Harness",
            "state": "Not Assessed",
            "reason": "No benchmark samples were supplied. Accuracy is not guessed.",
            "required_sample_schema": {
                "sample_id": "unique sample id",
                "expected_findings": ["known-vuln-id-or-title"],
                "scanner_findings": ["detected-id-or-title"],
                "known_clean": False,
            },
        }

    rows: list[dict[str, Any]] = []
    total_tp = total_fp = total_fn = total_tn = 0
    for idx, sample in enumerate(samples[:100], start=1):
        sid = str(sample.get("sample_id") or sample.get("id") or f"sample-{idx}")[:120]
        expected = {_finding_key(item) for item in sample.get("expected_findings") or [] if _finding_key(item)}
        detected = {_finding_key(item) for item in sample.get("scanner_findings") or [] if _finding_key(item)}
        known_clean = bool(sample.get("known_clean"))
        tp = len(expected & detected)
        fp = len(detected - expected)
        fn = len(expected - detected)
        tn = 1 if known_clean and not detected and not expected else 0
        total_tp += tp
        total_fp += fp
        total_fn += fn
        total_tn += tn
        rows.append({
            "sample_id": sid,
            "expected_count": len(expected),
            "detected_count": len(detected),
            "true_positive": tp,
            "false_positive": fp,
            "false_negative": fn,
            "true_clean": bool(tn),
            "missed_expected": sorted(expected - detected)[:20],
            "unexpected_detected": sorted(detected - expected)[:20],
        })

    precision = total_tp / (total_tp + total_fp) if total_tp + total_fp else None
    recall = total_tp / (total_tp + total_fn) if total_tp + total_fn else None
    f1 = (2 * precision * recall / (precision + recall)) if precision is not None and recall is not None and precision + recall else None
    return {
        "phase": 59,
        "engine": "Benchmark Accuracy Harness",
        "state": "Assessed",
        "sample_count": len(samples),
        "totals": {
            "true_positive": total_tp,
            "false_positive": total_fp,
            "false_negative": total_fn,
            "true_clean": total_tn,
        },
        "metrics": {
            "precision_on_supplied_dataset": round(precision, 4) if precision is not None else None,
            "recall_on_supplied_dataset": round(recall, 4) if recall is not None else None,
            "f1_on_supplied_dataset": round(f1, 4) if f1 is not None else None,
        },
        "rows": rows,
        "truth_boundary": "These metrics apply only to the supplied benchmark samples. They are not a universal accuracy claim.",
        "next_action": "Add 10 known-vulnerable and 10 known-clean samples, then rerun after every scanner-rule change.",
    }


def tune_false_positive_policy(triaged_findings: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    findings = triaged_findings or []
    if not findings:
        return {
            "phase": 59,
            "engine": "False-Positive Tuning Policy",
            "state": "Not Assessed",
            "reason": "No triaged findings were supplied. False-positive rate is not guessed.",
        }
    counts = {state: 0 for state in TRIAGE_STATES}
    hot_rules: dict[str, dict[str, int]] = {}
    invalid: list[str] = []
    for idx, item in enumerate(findings[:300], start=1):
        state = str(item.get("triage_status") or item.get("status") or "needs_evidence").strip().lower()
        if state not in TRIAGE_STATES:
            invalid.append(f"finding-{idx}: unsupported status {state}")
            state = "needs_evidence"
        counts[state] += 1
        rule = str(item.get("rule_id") or item.get("source") or item.get("title") or "unknown")[:120]
        if rule not in hot_rules:
            hot_rules[rule] = {state_name: 0 for state_name in TRIAGE_STATES}
        hot_rules[rule][state] += 1
    confirmed_like = counts["confirmed"] + counts["fixed"] + counts["accepted_risk"]
    fp_rate = counts["false_positive"] / len(findings) if findings else 0
    precision_proxy = confirmed_like / (confirmed_like + counts["false_positive"]) if confirmed_like + counts["false_positive"] else None
    suppress_candidates = []
    for rule, rule_counts in hot_rules.items():
        total = sum(rule_counts.values())
        if total >= 2 and rule_counts["false_positive"] / total >= 0.5:
            suppress_candidates.append({"rule": rule, "total": total, "false_positive_count": rule_counts["false_positive"], "recommendation": "Lower confidence/severity or require stronger raw evidence before showing as a bug."})
    return {
        "phase": 59,
        "engine": "False-Positive Tuning Policy",
        "state": "Assessed",
        "triaged_count": len(findings),
        "counts": counts,
        "false_positive_rate_on_triaged_set": round(fp_rate, 4),
        "precision_proxy_on_triaged_set": round(precision_proxy, 4) if precision_proxy is not None else None,
        "suppression_or_downgrade_candidates": suppress_candidates[:30],
        "invalid_status_rows": invalid[:20],
        "recommended_policy": [
            "Confirmed proof-based exposure can remain Bug/Exposure.",
            "Needs Evidence stays Warning/Manual Review, not confirmed bug.",
            "Rules with repeated false positives should be downgraded or gated behind stronger evidence.",
        ],
    }


def parse_formal_fuzz_artifacts(foundry_json: str | None = None, echidna_json: str | None = None, invariant_results: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    artifact_states: list[dict[str, Any]] = []

    for label, raw in (("Foundry", foundry_json), ("Echidna", echidna_json)):
        if not raw:
            artifact_states.append({"tool": label, "state": "Not Supplied"})
            continue
        data = _safe_json_loads(raw, None)
        if not isinstance(data, (dict, list)):
            artifact_states.append({"tool": label, "state": "Invalid JSON"})
            continue
        artifact_states.append({"tool": label, "state": "Parsed", "bytes": len(raw)})
        text = json.dumps(data, ensure_ascii=False)[:120000]
        if re.search(r"(?i)(fail|failed|counterexample|revert|assertion|invariant)", text):
            findings.append({
                "title": f"{label} artifact contains failed invariant/test evidence",
                "severity": "high",
                "category": "formal_fuzz_artifact",
                "source": f"Supplied {label} JSON artifact",
                "evidence": _short(text, 900),
                "recommendation": "Reproduce locally, isolate the failing invariant/test, patch, and rerun before reviewed report approval.",
                "proof_level": "supplied_tool_artifact",
            })

    for idx, item in enumerate(invariant_results or [], start=1):
        if not isinstance(item, dict):
            continue
        if item.get("passed") is False:
            findings.append({
                "title": f"Invariant failed: {item.get('name') or f'invariant-{idx}'}",
                "severity": _severity(item.get("severity"), "high"),
                "category": "formal_fuzz_artifact",
                "source": "Supplied invariant result",
                "evidence": _short(item.get("evidence") or item, 900),
                "recommendation": "Treat as launch blocker until reproduced and fixed, or explicitly accepted with reviewer notes.",
                "proof_level": "supplied_invariant_result",
            })
    return {
        "phase": 59,
        "engine": "Formal/Fuzz Artifact Bridge",
        "state": "Assessed" if findings or any(s.get("state") == "Parsed" for s in artifact_states) else "Not Assessed",
        "artifact_states": artifact_states,
        "confirmed_artifact_findings": findings[:60],
        "not_claimed": ["No formal verification is claimed unless a real artifact is supplied.", "No invariant failure is invented from protocol type."],
    }


def validate_authenticated_api_test_plan(plan: dict[str, Any] | None = None, observations: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    plan = plan or {}
    observations = observations or []
    if not plan and not observations:
        return {"phase": 59, "engine": "Authenticated API Test Harness Maturity", "state": "Not Assessed", "reason": "No API test plan or observations supplied."}
    roles = plan.get("roles") if isinstance(plan.get("roles"), list) else []
    endpoints = plan.get("endpoints") if isinstance(plan.get("endpoints"), list) else []
    object_ids = plan.get("object_ids") if isinstance(plan.get("object_ids"), list) else []
    gaps = []
    if len(roles) < 2:
        gaps.append("Add at least two roles/users to test BOLA/IDOR safely.")
    if not endpoints:
        gaps.append("Add endpoint list with expected role/object ownership.")
    if not object_ids:
        gaps.append("Add redacted object IDs owned by different test users.")

    findings = []
    token_leaks = []
    for idx, obs in enumerate(observations[:100], start=1):
        text = json.dumps(obs, ensure_ascii=False)
        if SECRET_TOKEN_RE.search(text):
            token_leaks.append(f"observation-{idx} contains secret-looking text; redact before saving/reporting")
        if obs.get("cross_account_access_proved") is True or obs.get("bola_proof") is True:
            findings.append({
                "title": "Authenticated BOLA/IDOR proof from supplied observation",
                "severity": "critical",
                "category": "authenticated_api",
                "source": "Authorized two-user API observation",
                "evidence": _short({k: v for k, v in obs.items() if k.lower() not in {"token", "authorization"}}, 900),
                "recommendation": "Patch object-level ownership checks and add regression tests for both users.",
                "proof_level": "authorized_supplied_observation",
            })
    return {
        "phase": 59,
        "engine": "Authenticated API Test Harness Maturity",
        "state": "Assessed" if not gaps else "Manual Review Required",
        "roles_count": len(roles),
        "endpoints_count": len(endpoints),
        "object_id_sets": len(object_ids),
        "maturity_gaps": gaps,
        "redaction_warnings": token_leaks[:20],
        "confirmed_findings": findings[:30],
        "safe_scope": ["No brute force", "No credential stuffing", "No DoS", "Only user-supplied authorized observations become proof"],
    }


def validate_defi_invariant_plan(protocol_context: dict[str, Any] | None = None, invariant_catalog: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    ctx = protocol_context or {}
    catalog = invariant_catalog or []
    required: list[str] = ["authorization", "accounting", "pause/emergency", "upgrade safety"]
    if ctx.get("uses_oracle"):
        required.append("oracle bounds/TWAP")
    if ctx.get("has_flash_loan_surface"):
        required.append("flash-loan resistant accounting")
    if ctx.get("has_bridge_or_cross_chain"):
        required.append("bridge replay/finality")
    if ctx.get("has_amm_or_liquidity_pool"):
        required.append("liquidity share/accounting")
    supplied = {str(item.get("category") or item.get("name") or "").lower() for item in catalog if isinstance(item, dict)}
    missing = [name for name in required if not any(name.split("/")[0].lower() in s or s in name.lower() for s in supplied)]
    failing = [item for item in catalog if isinstance(item, dict) and item.get("passed") is False]
    return {
        "phase": 59,
        "engine": "DeFi Invariant Coverage Strengthener",
        "state": "Assessed" if catalog else "Manual Review Required",
        "required_invariant_areas": required,
        "supplied_invariant_count": len(catalog),
        "missing_invariant_areas": missing,
        "failing_invariants": failing[:30],
        "launch_blocker": bool(failing),
        "not_claimed": "No DeFi exploit is confirmed without local/testnet simulation artifact or expert review.",
    }


def build_trust_proof_pack(case_studies: list[dict[str, Any]] | None = None, sample_reports: list[dict[str, Any]] | None = None, claims: list[str] | None = None) -> dict[str, Any]:
    case_studies = case_studies or []
    sample_reports = sample_reports or []
    claims = claims or []
    blocked = [claim for claim in claims if BLOCKED_CLAIM_RE.search(str(claim))]
    usable_case_studies = []
    for item in case_studies[:50]:
        if not isinstance(item, dict):
            continue
        if not item.get("permission_to_publish"):
            continue
        usable_case_studies.append({
            "title": str(item.get("title") or "Untitled case study")[:160],
            "scope": str(item.get("scope") or "pre-audit readiness")[:220],
            "evidence_summary": _short(item.get("evidence_summary"), 500),
            "outcome": _short(item.get("outcome"), 500),
            "disclaimer": "Pre-audit readiness case study; not a certified audit claim.",
        })
    report_count = len([r for r in sample_reports if isinstance(r, dict) and r.get("report_hash")])
    return {
        "phase": 59,
        "engine": "Trust Proof Pack Builder",
        "state": "Blocked" if blocked else "Ready" if usable_case_studies or report_count else "Needs Evidence",
        "publishable_case_studies": usable_case_studies[:12],
        "verifiable_sample_report_count": report_count,
        "blocked_claims": blocked,
        "allowed_claim_template": "Evidence-first pre-audit readiness results for supplied scope. Not a certified audit and no all-bugs guarantee.",
        "no_fake_trust_rules": ["No fake customer logos", "No fake testimonials", "No certified-audit wording", "No all-vulnerabilities-found claim"],
    }


def build_accuracy_hardening_package(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    return {
        "engine_version": ENGINE_VERSION,
        "generated_at": _now(),
        "weak_points_reduced": [
            "Benchmark accuracy proof",
            "False-positive tuning dataset",
            "Formal/fuzz/invariant artifact bridge",
            "Authenticated API test harness maturity",
            "DeFi invariant coverage planning",
            "Trust proof pack without fake claims",
        ],
        "results": {
            "benchmark": benchmark_scanner_accuracy(payload.get("benchmark_samples") if isinstance(payload.get("benchmark_samples"), list) else []),
            "false_positive_tuning": tune_false_positive_policy(payload.get("triaged_findings") if isinstance(payload.get("triaged_findings"), list) else []),
            "formal_fuzz_artifacts": parse_formal_fuzz_artifacts(
                foundry_json=payload.get("foundry_json"),
                echidna_json=payload.get("echidna_json"),
                invariant_results=payload.get("invariant_results") if isinstance(payload.get("invariant_results"), list) else [],
            ),
            "api_harness": validate_authenticated_api_test_plan(
                plan=payload.get("api_test_plan") if isinstance(payload.get("api_test_plan"), dict) else {},
                observations=payload.get("api_observations") if isinstance(payload.get("api_observations"), list) else [],
            ),
            "defi_invariant_plan": validate_defi_invariant_plan(
                protocol_context=payload.get("protocol_context") if isinstance(payload.get("protocol_context"), dict) else {},
                invariant_catalog=payload.get("invariant_catalog") if isinstance(payload.get("invariant_catalog"), list) else [],
            ),
            "trust_proof_pack": build_trust_proof_pack(
                case_studies=payload.get("case_studies") if isinstance(payload.get("case_studies"), list) else [],
                sample_reports=payload.get("sample_reports") if isinstance(payload.get("sample_reports"), list) else [],
                claims=payload.get("claims") if isinstance(payload.get("claims"), list) else [],
            ),
        },
        "truth_boundary": "This hardens accuracy measurement and evidence workflows. It still does not claim all vulnerabilities are found.",
    }


def accuracy_hardening_status() -> dict[str, Any]:
    return {
        "ok": True,
        "engine_version": ENGINE_VERSION,
        "purpose": "Reduce weak points by measuring accuracy, tuning false positives, accepting real formal/fuzz artifacts, strengthening API/DeFi evidence workflows, and blocking fake trust claims.",
        "render_provider_readiness": {
            "provider_live_network_enabled": settings.provider_live_network_enabled,
            "osv_api_base": settings.osv_api_base,
            "github_token_configured": bool(settings.github_api_token),
            "etherscan_key_configured": bool(settings.etherscan_api_key),
            "static_analysis_enabled": settings.static_analysis_enabled,
            "slither_present": shutil.which(settings.slither_binary or "slither") is not None,
            "semgrep_present": shutil.which(settings.semgrep_binary or "semgrep") is not None,
            "foundry_enabled": settings.foundry_enabled,
            "foundry_present": shutil.which(settings.foundry_binary or "forge") is not None,
            "deep_analysis_enabled": settings.deep_analysis_enabled,
            "echidna_enabled": settings.echidna_enabled,
            "echidna_present": shutil.which(settings.echidna_binary or "echidna") is not None,
        },
        "vercel_required_public_env": ["NEXT_PUBLIC_API_BASE_URL", "NEXT_PUBLIC_SUPABASE_URL", "NEXT_PUBLIC_SUPABASE_ANON_KEY"],
        "blocked_claims": ["100% secure", "all vulnerabilities found", "certified audit", "OpenZeppelin/CertiK/Hacken level without real expert process"],
    }
