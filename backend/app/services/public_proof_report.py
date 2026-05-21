from __future__ import annotations

import hashlib
import hmac
import json
import uuid
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.core.config import settings

REAL_ONLY_NOTE = (
    "Web3Guard AI public proof reports are evidence-first pre-audit readiness packets. "
    "They are not certified audits, guarantees, insurance, or proof that every vulnerability was found."
)

BLOCKED_CLAIMS = [
    "certified audit",
    "100% secure",
    "all bugs found",
    "guaranteed safe",
    "insurance guaranteed",
    "exploit-proof",
    "audited by web3guard",
    "certik replacement",
    "openzeppelin certified",
]

ALLOWED_PUBLIC_WORDING = (
    "Web3Guard AI pre-audit readiness proof. Findings are based only on provided evidence, "
    "configured tools, supplied artifacts, and optional human review notes."
)

APPROVED_DECISIONS = {"approved_public_pre_audit", "approved_private_pre_audit"}

SEVERITY_ORDER = {"critical": 5, "high": 4, "medium": 3, "low": 2, "info": 1}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _storage_path() -> Path:
    path = Path(settings.public_proof_reports_file)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.touch(exist_ok=True)
    return path


def _canonical(data: Any) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)


def _sha256(data: Any) -> str:
    return hashlib.sha256(_canonical(data).encode("utf-8")).hexdigest()


def _hmac(data: Any) -> str:
    secret = settings.admin_token or "web3guard-local-proof-secret"
    return hmac.new(secret.encode("utf-8"), _canonical(data).encode("utf-8"), hashlib.sha256).hexdigest()


def _safe_text(value: Any, max_len: int = 1600) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    return text[:max_len]


def _scan_for_blocked_claims(payload: Any) -> list[str]:
    text = _canonical(payload).lower()
    hits: list[str] = []
    for claim in BLOCKED_CLAIMS:
        if claim.lower() in text:
            hits.append(claim)
    return sorted(set(hits))


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _report_from_payload(payload: dict[str, Any]) -> dict[str, Any]:
    report = payload.get("report")
    if isinstance(report, dict):
        return report
    scan_payload = payload.get("scan_payload")
    if isinstance(scan_payload, dict):
        combined = scan_payload.get("combined_report") or scan_payload.get("report")
        if isinstance(combined, dict):
            return combined
        return scan_payload
    return {}


def _extract_project_name(payload: dict[str, Any], report: dict[str, Any]) -> str:
    return (
        _safe_text(payload.get("project_name"), 180)
        or _safe_text(report.get("project_name"), 180)
        or _safe_text((payload.get("scan_payload") or {}).get("project_name") if isinstance(payload.get("scan_payload"), dict) else None, 180)
        or "Web3 project"
    )


def _extract_report_hash(report: dict[str, Any], payload: dict[str, Any]) -> str | None:
    direct = report.get("report_hash") or payload.get("report_hash")
    if direct:
        return str(direct)
    # Draft packets can still be integrity-hashed even when combined report hash is not present.
    return None


def _extract_tool_summary(report: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "local_rules": "unknown",
        "slither": "not_reported",
        "semgrep": "not_reported",
        "aderyn": "not_reported",
        "foundry": "not_reported",
        "echidna": "not_reported",
        "invariant_artifacts": "not_reported",
    }

    candidates = [
        report.get("professional_scanner_summary"),
        report.get("tool_execution_summary"),
        report.get("scan_metadata"),
        payload.get("professional_scanner_summary"),
        payload.get("tool_execution_summary"),
    ]
    scan_payload = payload.get("scan_payload")
    if isinstance(scan_payload, dict):
        candidates.extend([
            scan_payload.get("professional_scanner_summary"),
            scan_payload.get("tool_execution_summary"),
            scan_payload.get("static_analysis"),
            scan_payload.get("contract_address_scan"),
            scan_payload.get("github_repo_scan"),
        ])

    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        tool_status = candidate.get("tool_status") if isinstance(candidate.get("tool_status"), dict) else candidate
        if not isinstance(tool_status, dict):
            continue
        for key in list(summary.keys()):
            value = tool_status.get(key)
            if value is not None:
                if isinstance(value, dict):
                    summary[key] = value.get("state") or value.get("status") or value.get("summary") or value
                else:
                    summary[key] = value

    source_counts = report.get("professional_scanner_summary", {}).get("source_tool_counts") if isinstance(report.get("professional_scanner_summary"), dict) else None
    if isinstance(source_counts, dict):
        summary["source_tool_counts"] = source_counts
    return summary


def _finding_text(finding: dict[str, Any], key: str) -> str:
    value = finding.get(key)
    if value is None:
        return ""
    if isinstance(value, list):
        return "; ".join(str(item) for item in value[:5])
    return str(value)


def _normalize_finding(finding: dict[str, Any], index: int) -> dict[str, Any]:
    severity = str(finding.get("severity") or "info").lower()
    if severity not in SEVERITY_ORDER:
        severity = "info"
    source_tools = finding.get("source_tools")
    if not isinstance(source_tools, list) or not source_tools:
        source = finding.get("source") or finding.get("module") or "scanner"
        source_tools = [str(source)]
    return {
        "id": str(finding.get("id") or finding.get("rule_id") or f"finding-{index + 1}"),
        "title": _safe_text(finding.get("title") or "Security finding", 260),
        "severity": severity,
        "category": _safe_text(finding.get("category") or finding.get("module") or "general", 120),
        "source_tools": sorted({str(item) for item in source_tools if item}),
        "affected_file": finding.get("affected_file"),
        "affected_line": finding.get("affected_line"),
        "affected_column": finding.get("affected_column"),
        "evidence": _safe_text(_finding_text(finding, "evidence") or _finding_text(finding, "description"), 1200),
        "impact": _safe_text(_finding_text(finding, "impact") or _finding_text(finding, "business_impact"), 1000),
        "fix": _safe_text(_finding_text(finding, "fix") or _finding_text(finding, "recommendation"), 1000),
        "confidence": _safe_text(finding.get("confidence") or "medium", 80),
        "verification_status": _safe_text(finding.get("verification_status") or "scanner_detected_needs_review", 120),
    }


def _extract_findings(report: dict[str, Any], payload: dict[str, Any]) -> list[dict[str, Any]]:
    raw: list[Any] = []
    for key in ("top_findings", "findings", "normalized_findings", "report_ready_findings"):
        raw.extend(_as_list(report.get(key)))
    scan_payload = payload.get("scan_payload")
    if isinstance(scan_payload, dict):
        for key in ("findings", "top_findings", "normalized_findings", "report_ready_findings"):
            raw.extend(_as_list(scan_payload.get(key)))
        for nested_key in ("contract_scan", "contract_address_scan", "github_repo_scan", "formal_fuzz_artifacts"):
            nested = scan_payload.get(nested_key)
            if isinstance(nested, dict):
                raw.extend(_as_list(nested.get("findings")))
    normalized: list[dict[str, Any]] = []
    seen: set[str] = set()
    for idx, item in enumerate(raw):
        if not isinstance(item, dict):
            continue
        finding = _normalize_finding(item, idx)
        fingerprint = _sha256({
            "title": finding["title"].lower(),
            "severity": finding["severity"],
            "file": finding.get("affected_file"),
            "line": finding.get("affected_line"),
        })
        if fingerprint in seen:
            continue
        seen.add(fingerprint)
        normalized.append(finding)
    return sorted(normalized, key=lambda f: SEVERITY_ORDER.get(f.get("severity", "info"), 0), reverse=True)


def _coverage(report: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    coverage = report.get("coverage") if isinstance(report.get("coverage"), dict) else {}
    module_matrix = _as_list(report.get("module_matrix"))
    if coverage:
        return {
            "assessed_count": int(coverage.get("assessed_count") or 0),
            "total_modules": int(coverage.get("total_modules") or 0),
            "coverage_percent": coverage.get("coverage_percent", 0),
            "confidence": coverage.get("confidence", "low"),
        }
    if module_matrix:
        assessed = sum(1 for row in module_matrix if isinstance(row, dict) and row.get("assessed"))
        total = len(module_matrix)
        return {
            "assessed_count": assessed,
            "total_modules": total,
            "coverage_percent": round((assessed / total) * 100, 2) if total else 0,
            "confidence": "medium" if assessed and assessed == total else "low",
        }
    scan_payload = payload.get("scan_payload")
    if isinstance(scan_payload, dict):
        cov = scan_payload.get("coverage")
        if isinstance(cov, dict):
            return cov
    return {"assessed_count": 0, "total_modules": 0, "coverage_percent": 0, "confidence": "low"}


def _severity_breakdown(findings: list[dict[str, Any]]) -> dict[str, int]:
    counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
    for finding in findings:
        sev = finding.get("severity", "info")
        counts[sev] = counts.get(sev, 0) + 1
    return counts


def _approval_gate(packet: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    blocked = _scan_for_blocked_claims({
        "project_name": packet.get("project_name"),
        "requested_public_claim": payload.get("requested_public_claim"),
        "custom_summary": payload.get("custom_summary"),
        "public_notes": payload.get("public_notes"),
    })
    report_hash = packet.get("report_hash")
    coverage = packet.get("coverage", {}) or {}
    reasons: list[str] = []
    if not report_hash:
        reasons.append("A combined report_hash is required before public proof approval.")
    if blocked:
        reasons.append("Blocked public wording was detected.")
    if not payload.get("authorized_scope_confirmed", False):
        reasons.append("Authorized scope must be confirmed before approval.")
    if not payload.get("real_only_acknowledged", False):
        reasons.append("Real-only and no-certified-audit terms must be acknowledged.")
    if int(coverage.get("assessed_count") or 0) == 0:
        reasons.append("At least one module must be assessed before proof approval.")
    return {
        "eligible": not reasons,
        "reasons": reasons,
        "blocked_claims_detected": blocked,
        "required_before_publication": [
            "Combined report_hash",
            "Authorized scope confirmation",
            "Real-only/no-certified-audit acknowledgement",
            "At least one assessed module",
            "No blocked certification/guarantee wording",
        ],
    }


def build_public_proof_draft(payload: dict[str, Any]) -> dict[str, Any]:
    report = _report_from_payload(payload)
    project_name = _extract_project_name(payload, report)
    findings = _extract_findings(report, payload)
    coverage = _coverage(report, payload)
    report_hash = _extract_report_hash(report, payload)
    packet_core = {
        "version": "phase-d-public-proof-v1",
        "project_name": project_name,
        "report_id": report.get("report_id") or payload.get("report_id"),
        "report_hash": report_hash,
        "scan_id": payload.get("scan_id") or report.get("scan_id"),
        "generated_from": payload.get("source", "scanner_report_payload"),
        "proof_type": "pre_audit_readiness_proof",
        "allowed_public_wording": ALLOWED_PUBLIC_WORDING,
        "blocked_claims": BLOCKED_CLAIMS,
        "coverage": coverage,
        "severity_breakdown": _severity_breakdown(findings),
        "tool_summary": _extract_tool_summary(report, payload),
        "findings_count": len(findings),
        "multi_tool_confirmed_count": sum(1 for f in findings if len(f.get("source_tools", [])) > 1),
        "top_findings": findings[:25],
        "evidence_manifest": {
            "has_report_hash": bool(report_hash),
            "has_file_line_evidence": any(f.get("affected_file") or f.get("affected_line") for f in findings),
            "has_tool_evidence": any(f.get("source_tools") for f in findings),
            "not_assessed_modules_remain_visible": True,
            "raw_private_artifacts_published": False,
        },
        "limitations": [
            "This proof packet is not a certified audit.",
            "Missing modules remain Not Assessed and must not be marketed as reviewed.",
            "Findings require project-specific validation and fix verification before launch decisions.",
            "Private keys, seed phrases, wallet signatures, and exploit automation are not used or required.",
        ],
        "real_only_note": REAL_ONLY_NOTE,
    }
    integrity_hash = _sha256(packet_core)
    draft = {
        **packet_core,
        "proof_id": f"proof_{uuid.uuid4().hex[:16]}",
        "status": "draft",
        "created_at": _now(),
        "integrity_hash": integrity_hash,
        "server_signature_hash": _hmac(packet_core),
    }
    draft["approval_gate"] = _approval_gate(draft, payload)
    return {"ok": True, "draft": draft, "real_only_note": REAL_ONLY_NOTE}


def approve_public_proof(payload: dict[str, Any]) -> dict[str, Any]:
    draft_payload = payload.get("draft") if isinstance(payload.get("draft"), dict) else None
    draft = deepcopy(draft_payload) if draft_payload else build_public_proof_draft(payload).get("draft", {})
    decision = str(payload.get("decision") or "needs_more_evidence")
    reviewer = _safe_text(payload.get("reviewer") or "Manual reviewer", 160)
    reason = _safe_text(payload.get("reviewer_reason") or payload.get("reason") or "", 2400)
    if len(reason) < 12:
        raise ValueError("reviewer_reason must explain the decision in at least 12 characters")

    gate = _approval_gate(draft, payload)
    approved = decision in APPROVED_DECISIONS and gate["eligible"]
    approval = {
        "decision": decision,
        "approved": approved,
        "reviewer": reviewer,
        "reviewed_at": _now(),
        "reviewer_reason": reason,
        "authorized_scope_confirmed": bool(payload.get("authorized_scope_confirmed")),
        "real_only_acknowledged": bool(payload.get("real_only_acknowledged")),
        "payment_verified": bool(payload.get("payment_verified", False)),
        "manual_review_claim_allowed": approved and bool(payload.get("manual_review_completed", False)),
        "claim_limit": "Allowed wording remains pre-audit readiness/human-reviewed pre-audit only. No certified audit claim.",
        "gate": gate,
    }
    draft["approval"] = approval
    draft["status"] = "approved_pre_audit" if approved else "not_ready"
    draft["approved_public_wording"] = (
        "Human-reviewed Web3Guard AI pre-audit readiness proof" if approval["manual_review_claim_allowed"] else ALLOWED_PUBLIC_WORDING
    )
    draft["integrity_hash"] = _sha256({k: v for k, v in draft.items() if k not in {"integrity_hash", "server_signature_hash"}})
    draft["server_signature_hash"] = _hmac({k: v for k, v in draft.items() if k != "server_signature_hash"})
    return {"ok": True, "packet": draft, "approved": approved, "real_only_note": REAL_ONLY_NOTE}


def _read_records() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line in _storage_path().read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records


def _write_records(records: list[dict[str, Any]]) -> None:
    with _storage_path().open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")


def publish_public_proof(payload: dict[str, Any]) -> dict[str, Any]:
    packet_payload = payload.get("packet") if isinstance(payload.get("packet"), dict) else None
    packet = deepcopy(packet_payload) if packet_payload else approve_public_proof(payload).get("packet", {})
    approval = packet.get("approval") if isinstance(packet.get("approval"), dict) else {}
    if not approval.get("approved"):
        raise ValueError("Only approved pre-audit proof packets can be published")
    visibility = str(payload.get("visibility") or "public")
    if visibility not in {"public", "private"}:
        raise ValueError("visibility must be public or private")
    record = {
        "id": packet.get("proof_id") or f"proof_{uuid.uuid4().hex[:16]}",
        "created_at": packet.get("created_at") or _now(),
        "published_at": _now(),
        "visibility": visibility,
        "status": "published" if visibility == "public" else "private",
        "project_name": packet.get("project_name"),
        "report_id": packet.get("report_id"),
        "report_hash": packet.get("report_hash"),
        "integrity_hash": packet.get("integrity_hash"),
        "public_wording": packet.get("approved_public_wording") or ALLOWED_PUBLIC_WORDING,
        "blocked_claims": BLOCKED_CLAIMS,
        "manual_review_claim_allowed": bool(approval.get("manual_review_claim_allowed", False)),
        "packet": packet,
    }
    records = _read_records()
    records = [row for row in records if row.get("id") != record["id"]]
    records.append(record)
    _write_records(records)
    return {"ok": True, "record": record, "real_only_note": REAL_ONLY_NOTE}


def list_public_proofs(include_private: bool = False, limit: int = 100) -> dict[str, Any]:
    rows = _read_records()
    if not include_private:
        rows = [row for row in rows if row.get("visibility") == "public" and row.get("status") == "published"]
    rows = sorted(rows, key=lambda r: r.get("published_at") or r.get("created_at") or "", reverse=True)[:limit]
    return {"ok": True, "records": rows, "count": len(rows), "real_only_note": REAL_ONLY_NOTE}


def get_public_proof(proof_id: str, allow_private: bool = False) -> dict[str, Any] | None:
    for record in _read_records():
        if record.get("id") == proof_id:
            if record.get("visibility") == "private" and not allow_private:
                return None
            if record.get("status") == "revoked" and not allow_private:
                return None
            return record
    return None


def verify_public_proof(proof_id: str, integrity_hash: str | None = None, report_hash: str | None = None) -> dict[str, Any]:
    record = get_public_proof(proof_id, allow_private=True)
    if not record:
        return {"ok": False, "verified": False, "reason": "Proof record not found"}
    integrity_ok = True if integrity_hash is None else hmac.compare_digest(str(record.get("integrity_hash") or ""), str(integrity_hash))
    report_ok = True if report_hash is None else hmac.compare_digest(str(record.get("report_hash") or ""), str(report_hash))
    status_ok = record.get("status") in {"published", "private"}
    verified = bool(integrity_ok and report_ok and status_ok)
    return {
        "ok": True,
        "verified": verified,
        "proof_id": proof_id,
        "report_id": record.get("report_id"),
        "visibility": record.get("visibility"),
        "status": record.get("status"),
        "integrity_match": integrity_ok,
        "report_hash_match": report_ok,
        "public_wording": record.get("public_wording"),
        "blocked_claims": record.get("blocked_claims", BLOCKED_CLAIMS),
        "reason": "Proof record verified" if verified else "Proof integrity/status check failed",
        "real_only_note": REAL_ONLY_NOTE,
    }


def revoke_public_proof(proof_id: str, reason: str, reviewer: str = "Admin reviewer") -> dict[str, Any]:
    records = _read_records()
    changed = False
    for record in records:
        if record.get("id") == proof_id:
            record["status"] = "revoked"
            record["revoked_at"] = _now()
            record["revoked_by"] = _safe_text(reviewer, 160)
            record["revocation_reason"] = _safe_text(reason, 1200)
            changed = True
            break
    if not changed:
        return {"ok": False, "revoked": False, "reason": "Proof record not found"}
    _write_records(records)
    return {"ok": True, "revoked": True, "proof_id": proof_id, "real_only_note": REAL_ONLY_NOTE}


def status() -> dict[str, Any]:
    records = _read_records()
    return {
        "ok": True,
        "version": "phase-d-public-proof-report-v1",
        "storage": str(_storage_path()),
        "records": len(records),
        "live_endpoints": [
            "POST /proof-reports/draft",
            "POST /proof-reports/approve",
            "POST /proof-reports/publish",
            "GET /proof-reports",
            "GET /proof-reports/{proof_id}",
            "GET /proof-reports/{proof_id}/verify",
            "POST /proof-reports/{proof_id}/revoke",
        ],
        "allowed_public_wording": ALLOWED_PUBLIC_WORDING,
        "blocked_claims": BLOCKED_CLAIMS,
        "real_only_note": REAL_ONLY_NOTE,
    }
