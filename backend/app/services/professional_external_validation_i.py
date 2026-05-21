"""Professional Scanner Phase I — external evidence validation + reviewer consensus.

This module does not ship third-party audited project source code and does not claim
certified-audit parity. It provides the infrastructure needed to ingest sanitized
external benchmark cases, compare Web3Guard findings against expected signals, and
record independent reviewer confirmations.
"""
from __future__ import annotations

import hashlib
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any, Literal
from uuid import uuid4

from app.core.config import settings
from app.models.schemas import Finding
from app.services.scan_contract import available_contract_rules, scan_solidity

Decision = Literal["confirmed", "false_positive", "missed", "fixed", "accepted_risk", "needs_evidence"]
CaseType = Literal["vulnerable", "clean", "regression", "external_reference"]
SEVERITY_RANK: dict[str, int] = {"critical": 5, "high": 4, "medium": 3, "low": 2, "info": 1}
BLOCKED_PUBLIC_CLAIMS = (
    "certified audit",
    "100% secure",
    "all bugs found",
    "guaranteed safe",
    "exploit-proof",
    "certik replacement",
    "openzeppelin certified",
    "hacken replacement",
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()


def _jsonl_path(attr: str, default: str) -> Path:
    return Path(getattr(settings, attr, default))


def _ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def _append_jsonl(path: Path, record: dict[str, Any]) -> dict[str, Any]:
    _ensure_parent(path)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
    return record


def _read_jsonl(path: Path, limit: int = 200) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except Exception:
                continue
    return rows[-limit:]


def _normalize_rule_ids(values: list[str] | set[str] | tuple[str, ...] | None) -> set[str]:
    if not values:
        return set()
    return {str(v).strip() for v in values if str(v).strip()}


def _finding_to_external_record(f: Finding) -> dict[str, Any]:
    return {
        "id": f.id,
        "rule_id": f.rule_id,
        "title": f.title,
        "severity": f.severity,
        "category": f.category,
        "confidence": f.confidence,
        "affected_file": f.affected_file,
        "affected_line": f.affected_line,
        "source_tools": f.source_tools or ([f.source] if f.source else []),
        "evidence": f.evidence,
        "impact": f.impact,
        "fix": f.fix,
        "verification_status": f.verification_status,
        "fingerprint": f.fingerprint,
    }


def _severity_at_least(actual: str | None, expected_min: str | None) -> bool:
    if not expected_min:
        return True
    return SEVERITY_RANK.get((actual or "info").lower(), 0) >= SEVERITY_RANK.get(expected_min.lower(), 0)


def _blocked_claims(text: str | None) -> list[str]:
    haystack = (text or "").lower()
    return [claim for claim in BLOCKED_PUBLIC_CLAIMS if claim in haystack]


def _infer_family_from_rule(rule_id: str | None, title: str = "", category: str = "") -> str:
    token = " ".join([rule_id or "", title, category]).lower()
    mapping = [
        ("reentr", "reentrancy"),
        ("oracle", "oracle"),
        ("slippage", "dex_mev"),
        ("deadline", "dex_mev"),
        ("upgrade", "upgradeable_proxy"),
        ("uups", "upgradeable_proxy"),
        ("proxy", "upgradeable_proxy"),
        ("signature", "signature_replay"),
        ("ecrecover", "signature_replay"),
        ("vault", "vault_erc4626"),
        ("4626", "vault_erc4626"),
        ("bridge", "cross_chain"),
        ("messenger", "cross_chain"),
        ("random", "randomness"),
        ("timestamp", "randomness"),
        ("delegatecall", "multicall_value"),
        ("multicall", "multicall_value"),
        ("transferfrom", "token_admin"),
        ("owner", "access_control"),
        ("admin", "access_control"),
    ]
    for needle, family in mapping:
        if needle in token:
            return family
    return "general"


# Sanitized internal fixtures. They are intentionally small, non-third-party, and only
# represent public-risk families commonly observed in security reviews.
SANITIZED_EXTERNAL_FIXTURES: list[dict[str, Any]] = [
    {
        "case_id": "EXT-SAN-REENTRANCY-001",
        "title": "Sanitized external-style vault external call before state update",
        "case_type": "vulnerable",
        "family": "reentrancy",
        "source_label": "sanitized_external_inspired_fixture",
        "expected_rule_ids": ["WG-SOL-REENTRANCY-001"],
        "expected_min_severity": "high",
        "code": """
pragma solidity ^0.8.20;
contract ExternalStyleVault {
    mapping(address => uint256) public balance;
    function withdraw(uint256 amount) external {
        require(balance[msg.sender] >= amount, "bal");
        (bool ok,) = msg.sender.call{value: amount}("");
        require(ok, "send");
        balance[msg.sender] -= amount;
    }
}
""",
    },
    {
        "case_id": "EXT-SAN-ORACLE-001",
        "title": "Sanitized external-style oracle stale price and decimal issue",
        "case_type": "vulnerable",
        "family": "oracle",
        "source_label": "sanitized_external_inspired_fixture",
        "expected_rule_ids": ["WG-SOL-ORACLE-001", "WG-SOL-ORACLE-002"],
        "expected_min_severity": "medium",
        "code": """
pragma solidity ^0.8.20;
interface AggregatorV3Interface { function latestRoundData() external view returns (uint80,int256,uint256,uint256,uint80); function decimals() external view returns(uint8); }
contract ExternalStyleOracleUse {
    AggregatorV3Interface public feed;
    function value(uint256 amount) external view returns (uint256) {
        (, int256 answer,,,) = feed.latestRoundData();
        return amount * uint256(answer);
    }
}
""",
    },
    {
        "case_id": "EXT-SAN-PROXY-001",
        "title": "Sanitized external-style UUPS weak authorization",
        "case_type": "vulnerable",
        "family": "upgradeable_proxy",
        "source_label": "sanitized_external_inspired_fixture",
        "expected_rule_ids": ["WG-SOL-UPGRADE-001"],
        "expected_min_severity": "high",
        "code": """
pragma solidity ^0.8.20;
contract ExternalStyleUUPS {
    address public owner;
    function initialize(address newOwner) public { owner = newOwner; }
    function upgradeTo(address impl) external { _authorizeUpgrade(impl); }
    function _authorizeUpgrade(address) internal {}
}
""",
    },
    {
        "case_id": "EXT-SAN-CLEAN-001",
        "title": "Sanitized external-style clean guarded withdraw",
        "case_type": "clean",
        "family": "reentrancy",
        "source_label": "sanitized_external_inspired_fixture",
        "forbidden_high_or_critical": True,
        "code": """
pragma solidity ^0.8.20;
contract CleanExternalStyleVault {
    mapping(address => uint256) public balance;
    bool private locked;
    modifier nonReentrant(){ require(!locked, "locked"); locked = true; _; locked = false; }
    function withdraw(uint256 amount) external nonReentrant {
        require(balance[msg.sender] >= amount, "bal");
        balance[msg.sender] -= amount;
        (bool ok,) = msg.sender.call{value: amount}("");
        require(ok, "send");
    }
}
""",
    },
]


def external_validation_status() -> dict[str, Any]:
    case_rows = _read_jsonl(_jsonl_path("professional_external_validation_cases_file", "app/data/db/professional_external_validation_cases.jsonl"), limit=1000)
    confirmation_rows = _read_jsonl(_jsonl_path("professional_external_reviewer_confirmations_file", "app/data/db/professional_external_reviewer_confirmations.jsonl"), limit=1000)
    return {
        "ok": True,
        "phase": "Professional Scanner Phase I",
        "engine": "external_evidence_validation_and_reviewer_consensus",
        "scanner_claim_policy": {
            "direct_competition_goal": "supported_as_internal_engine_goal",
            "certified_audit_claim_allowed": False,
            "replacement_claim_allowed": False,
            "allowed_public_wording": "AI-assisted security readiness and human-review workflow; not a certified audit unless separately contracted and manually signed by qualified reviewers.",
        },
        "built_in_sanitized_cases": len(SANITIZED_EXTERNAL_FIXTURES),
        "stored_external_cases": len(case_rows),
        "reviewer_confirmations": len(confirmation_rows),
        "available_contract_rules": len(available_contract_rules()),
        "required_next_for_direct_level": [
            "larger third-party-approved benchmark corpus",
            "independent reviewer confirmations",
            "signed report governance",
            "public retest/fix verification history",
            "continuous monitoring evidence",
        ],
    }


def validate_external_case(payload: dict[str, Any]) -> dict[str, Any]:
    code = str(payload.get("solidity_code") or payload.get("code") or "")
    if len(code.strip()) < 20:
        return {"ok": False, "status": "blocked", "reason": "solidity_code is required for active validation."}
    if not payload.get("authorization_confirmed", True) or not payload.get("real_only_acknowledged", True):
        return {"ok": False, "status": "blocked", "reason": "Authorization and real-only acknowledgement are required."}

    expected_rule_ids = _normalize_rule_ids(payload.get("expected_rule_ids"))
    forbidden_rule_ids = _normalize_rule_ids(payload.get("forbidden_rule_ids"))
    expected_min_severity = payload.get("expected_min_severity")
    case_id = str(payload.get("case_id") or f"EXT-CUSTOM-{uuid4().hex[:10].upper()}")
    family = str(payload.get("family") or "custom")
    result = scan_solidity(code, str(payload.get("project_name") or case_id))
    finding_records = [_finding_to_external_record(f) for f in result.findings]
    detected_rule_ids = {str(f.get("rule_id")) for f in finding_records if f.get("rule_id")}

    missed_rule_ids = sorted(expected_rule_ids - detected_rule_ids)
    forbidden_hits = sorted(forbidden_rule_ids & detected_rule_ids)
    high_or_critical_findings = [f for f in finding_records if SEVERITY_RANK.get(str(f.get("severity", "info")), 0) >= 4]
    severity_failures: list[dict[str, Any]] = []
    if expected_min_severity:
        for rule_id in expected_rule_ids & detected_rule_ids:
            matching = [f for f in finding_records if f.get("rule_id") == rule_id]
            strongest = max(matching, key=lambda f: SEVERITY_RANK.get(str(f.get("severity", "info")), 0), default=None)
            if strongest and not _severity_at_least(str(strongest.get("severity")), str(expected_min_severity)):
                severity_failures.append({"rule_id": rule_id, "actual": strongest.get("severity"), "expected_min": expected_min_severity})

    case_type = str(payload.get("case_type") or "external_reference")
    clean_case_high_critical_fail = case_type == "clean" and bool(high_or_critical_findings)
    score = 100
    score -= len(missed_rule_ids) * 20
    score -= len(forbidden_hits) * 25
    score -= len(severity_failures) * 10
    if clean_case_high_critical_fail:
        score -= 35
    score = max(0, min(100, score))

    validation = {
        "ok": True,
        "validation_id": f"EXTVAL-{uuid4().hex[:12].upper()}",
        "case_id": case_id,
        "case_hash": _sha256(code),
        "case_type": case_type,
        "family": family,
        "project_name": payload.get("project_name"),
        "source_label": payload.get("source_label") or "external_or_custom_case",
        "expected_rule_ids": sorted(expected_rule_ids),
        "detected_rule_ids": sorted(detected_rule_ids),
        "missed_rule_ids": missed_rule_ids,
        "forbidden_hits": forbidden_hits,
        "severity_failures": severity_failures,
        "clean_case_high_critical_fail": clean_case_high_critical_fail,
        "findings_count": len(finding_records),
        "high_or_critical_count": len(high_or_critical_findings),
        "findings": finding_records[:80],
        "score": score,
        "quality_gate": "passed" if score >= 85 and not missed_rule_ids and not forbidden_hits and not severity_failures and not clean_case_high_critical_fail else "needs_rule_tuning",
        "public_claim_allowed": False,
        "created_at": _now(),
    }
    return validation


def run_sanitized_external_suite() -> dict[str, Any]:
    validations = []
    for fixture in SANITIZED_EXTERNAL_FIXTURES:
        validations.append(validate_external_case({**fixture, "authorization_confirmed": True, "real_only_acknowledged": True}))

    total_expected = sum(len(v.get("expected_rule_ids", [])) for v in validations)
    total_missed = sum(len(v.get("missed_rule_ids", [])) for v in validations)
    false_positive_cases = [v for v in validations if v.get("clean_case_high_critical_fail") or v.get("forbidden_hits")]
    severity_fail_cases = [v for v in validations if v.get("severity_failures")]
    family_scores: dict[str, list[int]] = defaultdict(list)
    family_misses: dict[str, list[str]] = defaultdict(list)
    for v in validations:
        family = str(v.get("family") or "general")
        family_scores[family].append(int(v.get("score", 0)))
        for rule_id in v.get("missed_rule_ids", []):
            family_misses[family].append(rule_id)

    recall = 1.0 if total_expected == 0 else round((total_expected - total_missed) / total_expected, 4)
    clean_specificity = round((len([v for v in validations if v.get("case_type") == "clean" and not v.get("clean_case_high_critical_fail")]) / max(1, len([v for v in validations if v.get("case_type") == "clean"]))), 4)
    family_metrics = {
        family: {
            "average_score": round(mean(scores), 2) if scores else 0,
            "missed_rule_ids": sorted(set(family_misses.get(family, []))),
            "gate": "passed" if scores and mean(scores) >= 85 and not family_misses.get(family) else "needs_tuning",
        }
        for family, scores in sorted(family_scores.items())
    }
    quality_gate = "external_validation_progress" if recall >= 0.90 and clean_specificity >= 0.90 and not severity_fail_cases else "needs_rule_tuning"

    run_record = {
        "ok": True,
        "phase": "Professional Scanner Phase I",
        "run_id": f"EXTBENCH-{uuid4().hex[:12].upper()}",
        "created_at": _now(),
        "suite": "sanitized_external_style_validation",
        "cases_total": len(validations),
        "total_expected_signals": total_expected,
        "total_missed_signals": total_missed,
        "recall": recall,
        "clean_specificity": clean_specificity,
        "false_positive_cases": [v.get("case_id") for v in false_positive_cases],
        "severity_fail_cases": [v.get("case_id") for v in severity_fail_cases],
        "family_metrics": family_metrics,
        "quality_gate": quality_gate,
        "direct_competition_engine_progress": quality_gate == "external_validation_progress",
        "direct_competition_public_claim_allowed": False,
        "blocked_public_wording": list(BLOCKED_PUBLIC_CLAIMS),
        "validations": validations,
    }
    _append_jsonl(_jsonl_path("professional_external_benchmark_runs_file", "app/data/db/professional_external_benchmark_runs.jsonl"), run_record)
    return run_record


def ingest_external_case(payload: dict[str, Any]) -> dict[str, Any]:
    if not payload.get("real_only_acknowledged", True):
        return {"ok": False, "status": "blocked", "reason": "real_only_acknowledged is required."}
    if payload.get("store_code") and not payload.get("sanitized_code_confirmed"):
        return {"ok": False, "status": "blocked", "reason": "sanitized_code_confirmed is required before storing source code."}
    blocked_claims = _blocked_claims(payload.get("notes") or "")
    if blocked_claims:
        return {"ok": False, "status": "blocked", "reason": "Unsafe public claim in notes.", "blocked_claims": blocked_claims}

    code = str(payload.get("solidity_code") or payload.get("code") or "")
    record = {
        "id": f"EXTCASE-{uuid4().hex[:12].upper()}",
        "case_id": payload.get("case_id") or f"EXT-CUSTOM-{uuid4().hex[:8].upper()}",
        "title": payload.get("title") or "External validation case",
        "case_type": payload.get("case_type") or "external_reference",
        "family": payload.get("family") or "custom",
        "source_label": payload.get("source_label") or "external_reference",
        "source_url": payload.get("source_url"),
        "expected_rule_ids": sorted(_normalize_rule_ids(payload.get("expected_rule_ids"))),
        "forbidden_rule_ids": sorted(_normalize_rule_ids(payload.get("forbidden_rule_ids"))),
        "expected_min_severity": payload.get("expected_min_severity"),
        "notes": payload.get("notes"),
        "case_hash": _sha256(code) if code else payload.get("case_hash"),
        "code_stored": bool(payload.get("store_code") and code),
        "solidity_code": code if payload.get("store_code") else None,
        "created_at": _now(),
        "public_claim_allowed": False,
    }
    return _append_jsonl(_jsonl_path("professional_external_validation_cases_file", "app/data/db/professional_external_validation_cases.jsonl"), record)


def list_external_cases(limit: int = 100) -> list[dict[str, Any]]:
    rows = _read_jsonl(_jsonl_path("professional_external_validation_cases_file", "app/data/db/professional_external_validation_cases.jsonl"), limit=limit)
    sanitized: list[dict[str, Any]] = []
    for row in rows:
        clean = dict(row)
        if clean.get("solidity_code"):
            clean["solidity_code"] = "[stored but hidden in API list]"
        sanitized.append(clean)
    return sanitized


def validate_stored_case(case_id: str) -> dict[str, Any]:
    for row in reversed(_read_jsonl(_jsonl_path("professional_external_validation_cases_file", "app/data/db/professional_external_validation_cases.jsonl"), limit=1000)):
        if str(row.get("case_id")) == case_id or str(row.get("id")) == case_id:
            if not row.get("solidity_code"):
                return {"ok": False, "status": "not_assessed", "reason": "Stored case has no source code. Add sanitized code or run validate-case directly."}
            return validate_external_case({**row, "code": row.get("solidity_code"), "authorization_confirmed": True, "real_only_acknowledged": True})
    return {"ok": False, "status": "not_found", "reason": "case_id not found"}


def append_reviewer_confirmation(payload: dict[str, Any]) -> dict[str, Any]:
    if not payload.get("real_only_acknowledged", True):
        return {"ok": False, "status": "blocked", "reason": "real_only_acknowledged is required."}
    blocked_claims = _blocked_claims(payload.get("review_note") or "")
    if blocked_claims:
        return {"ok": False, "status": "blocked", "reason": "Unsafe claim in review note.", "blocked_claims": blocked_claims}

    decision = str(payload.get("decision") or "needs_evidence")
    if decision not in {"confirmed", "false_positive", "missed", "fixed", "accepted_risk", "needs_evidence"}:
        return {"ok": False, "status": "blocked", "reason": "Invalid decision."}
    record = {
        "id": f"EXTREV-{uuid4().hex[:12].upper()}",
        "case_id": payload.get("case_id"),
        "finding_id": payload.get("finding_id"),
        "rule_id": payload.get("rule_id"),
        "family": payload.get("family") or _infer_family_from_rule(payload.get("rule_id"), payload.get("title") or "", payload.get("category") or ""),
        "reviewer_id": payload.get("reviewer_id") or "anonymous_reviewer",
        "reviewer_role": payload.get("reviewer_role") or "security_reviewer",
        "decision": decision,
        "severity_override": payload.get("severity_override"),
        "confidence": payload.get("confidence") or "medium",
        "review_note": payload.get("review_note"),
        "evidence_hash": payload.get("evidence_hash"),
        "created_at": _now(),
        "public_claim_allowed": False,
    }
    return _append_jsonl(_jsonl_path("professional_external_reviewer_confirmations_file", "app/data/db/professional_external_reviewer_confirmations.jsonl"), record)


def reviewer_consensus(case_id: str | None = None, limit: int = 1000) -> dict[str, Any]:
    rows = _read_jsonl(_jsonl_path("professional_external_reviewer_confirmations_file", "app/data/db/professional_external_reviewer_confirmations.jsonl"), limit=limit)
    if case_id:
        rows = [r for r in rows if str(r.get("case_id")) == case_id]
    by_rule: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        key = str(row.get("rule_id") or row.get("finding_id") or "unknown")
        by_rule[key].append(row)

    items: list[dict[str, Any]] = []
    for key, decisions in sorted(by_rule.items()):
        counts = Counter(str(d.get("decision") or "needs_evidence") for d in decisions)
        confirmed = counts.get("confirmed", 0)
        false_positive = counts.get("false_positive", 0)
        needs_evidence = counts.get("needs_evidence", 0)
        reviewer_count = len({str(d.get("reviewer_id")) for d in decisions})
        consensus = "needs_more_review"
        if reviewer_count >= 2 and confirmed >= 2 and false_positive == 0:
            consensus = "externally_confirmed"
        elif false_positive >= 2:
            consensus = "likely_false_positive"
        elif confirmed >= 1 and needs_evidence == 0:
            consensus = "single_reviewer_confirmed"
        items.append({
            "key": key,
            "case_id": case_id,
            "reviewer_count": reviewer_count,
            "decision_counts": dict(counts),
            "consensus": consensus,
            "latest_reviewed_at": max(str(d.get("created_at") or "") for d in decisions),
        })

    summary = Counter(item["consensus"] for item in items)
    return {
        "ok": True,
        "case_id": case_id,
        "items": items,
        "summary": dict(summary),
        "external_human_validation_ready": bool(summary.get("externally_confirmed", 0)),
        "public_claim_allowed": False,
        "safe_public_wording": "Independent reviewer confirmations are recorded as evidence; this is not a certified audit claim.",
    }


def direct_competition_readiness_gate() -> dict[str, Any]:
    status = external_validation_status()
    suite = run_sanitized_external_suite()
    consensus = reviewer_consensus(limit=1000)
    stored_cases = int(status.get("stored_external_cases", 0))
    reviewer_confirmations = int(status.get("reviewer_confirmations", 0))
    external_confirmed = int(consensus.get("summary", {}).get("externally_confirmed", 0))
    gates = {
        "scanner_external_suite_passed": suite.get("quality_gate") == "external_validation_progress",
        "stored_external_cases_minimum_met": stored_cases >= 25,
        "reviewer_confirmations_minimum_met": reviewer_confirmations >= 50,
        "multi_reviewer_confirmations_present": external_confirmed >= 10,
        "unsafe_public_claims_blocked": True,
    }
    direct_level_score = round(sum(1 for v in gates.values() if v) / len(gates) * 100, 2)
    return {
        "ok": True,
        "phase": "Professional Scanner Phase I",
        "gate": "engine_progress_not_market_parity" if direct_level_score < 100 else "ready_for_external_audit_lab_review",
        "direct_level_score": direct_level_score,
        "gates": gates,
        "metrics": {
            "stored_external_cases": stored_cases,
            "reviewer_confirmations": reviewer_confirmations,
            "externally_confirmed_rules_or_findings": external_confirmed,
            "sanitized_suite_recall": suite.get("recall"),
            "sanitized_suite_clean_specificity": suite.get("clean_specificity"),
        },
        "public_claim_allowed": False,
        "why_not_direct_claim_yet": [
            "Needs larger externally approved benchmark corpus.",
            "Needs independent reviewer confirmations across risk families.",
            "Needs signed manual review governance before certified-market claims.",
            "Needs legal/brand controls for assurance wording.",
        ],
        "next_phase": "Phase J — continuous monitoring + post-audit drift detection engine",
    }
