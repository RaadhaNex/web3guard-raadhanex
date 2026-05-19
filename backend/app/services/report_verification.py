from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from app.services.professional_report import get_report_record

VERSION = "web3guard-report-verification-v1"
REAL_ONLY_NOTE = (
    "Verification proves report record/hash metadata consistency only. "
    "It does not prove that the project is safe, audited, exploit-free, or certified."
)

SAFE_BOUNDARIES = {
    "not_certified_audit": True,
    "no_100_percent_secure_claim": True,
    "no_wallet_signing": True,
    "no_private_key_or_seed_phrase_collection": True,
    "verification_scope": "metadata_integrity_only",
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _json_hash(value: Any) -> str:
    stable = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(stable.encode("utf-8")).hexdigest()


def _safe_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _safe_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _score_value(report: dict[str, Any]) -> Any:
    combined = _safe_dict(report.get("combined"))
    return (
        combined.get("overall_score")
        if combined.get("overall_score") is not None
        else combined.get("available_score")
        if combined.get("available_score") is not None
        else report.get("overall_score")
        if report.get("overall_score") is not None
        else report.get("available_score")
    )


def report_integrity_digest(report: dict[str, Any]) -> str:
    """Hash the current report payload, excluding UI-only rendered artifacts.

    This is intentionally not a certified audit signature. It is a stable
    tamper-evidence digest for the report payload the platform has in hand.
    """
    excluded = {"html_preview", "pdf_bytes", "professional_html"}
    normalized = {key: value for key, value in report.items() if key not in excluded}
    return _json_hash(normalized)


def build_evidence_snapshot(report: dict[str, Any]) -> dict[str, Any]:
    evidence_summary = _safe_list(report.get("evidence_summary"))
    evidence_required = _safe_list(report.get("evidence_required"))
    module_matrix = _safe_list(report.get("module_matrix"))
    score_split = _safe_dict(report.get("score_split"))

    assessed_modules: list[str] = []
    not_assessed_modules: list[str] = []
    for item in module_matrix:
        if not isinstance(item, dict):
            continue
        label = str(item.get("label") or item.get("module") or "Unknown module")
        if item.get("assessed"):
            assessed_modules.append(label)
        else:
            not_assessed_modules.append(label)

    evidence_items_count = 0
    for item in evidence_summary:
        if isinstance(item, dict):
            evidence_items_count += len(_safe_list(item.get("evidence")))

    return {
        "assessed_modules": assessed_modules,
        "not_assessed_modules": not_assessed_modules,
        "evidence_summary_count": len(evidence_summary),
        "evidence_items_count": evidence_items_count,
        "evidence_required_count": len(evidence_required),
        "module_matrix_count": len(module_matrix),
        "score_split_keys": list(score_split.keys()),
        "evidence_required": evidence_required[:20],
        "real_only_note": "Missing evidence remains Not Assessed and must not be converted into a fake score.",
    }


def build_finding_status_workflow(report: dict[str, Any]) -> dict[str, Any]:
    findings = _safe_list(report.get("top_findings"))
    action_plan = _safe_list(report.get("priority_action_plan"))
    workflow: list[dict[str, Any]] = []

    for index, finding in enumerate(findings[:50], start=1):
        if not isinstance(finding, dict):
            continue
        severity = str(finding.get("severity") or "info").lower()
        status = "manual_review_required" if severity in {"critical", "high"} else "open"
        if severity in {"critical", "high"}:
            next_action = "Fix or obtain manual security review before public launch."
        elif severity == "medium":
            next_action = "Schedule remediation and verify with a re-scan."
        else:
            next_action = "Track as hardening or documentation work."
        workflow.append(
            {
                "id": finding.get("id") or finding.get("fingerprint") or f"finding-{index}",
                "title": finding.get("title") or "Untitled finding",
                "module": finding.get("module") or finding.get("module_label") or "unknown",
                "severity": severity,
                "status": status,
                "owner": "unassigned",
                "next_action": next_action,
                "verify": _safe_dict(finding.get("fix_guidance")).get("verify") or "Re-run the relevant scan after remediation.",
            }
        )

    if not workflow and action_plan:
        for index, item in enumerate(action_plan[:20], start=1):
            if not isinstance(item, dict):
                continue
            workflow.append(
                {
                    "id": f"action-{index}",
                    "title": item.get("title") or "Priority action",
                    "module": item.get("module") or item.get("module_label") or "launch_readiness",
                    "severity": str(item.get("severity") or "medium").lower(),
                    "status": "open",
                    "owner": "unassigned",
                    "next_action": item.get("recommended_action") or "Review and assign this action.",
                    "verify": "Attach evidence or re-run scan after completion.",
                }
            )

    summary = {
        "open": sum(1 for item in workflow if item["status"] == "open"),
        "manual_review_required": sum(1 for item in workflow if item["status"] == "manual_review_required"),
        "fixed": 0,
        "accepted_risk": 0,
    }

    return {
        "summary": summary,
        "items": workflow,
        "allowed_statuses": ["open", "in_progress", "fixed", "accepted_risk", "manual_review_required"],
        "real_only_note": "Status workflow is a project-management layer. It does not certify that fixes are correct until verified by real evidence/manual review.",
    }


def build_report_verification_packet(report: dict[str, Any], *, source: str = "payload") -> dict[str, Any]:
    report_hash = report.get("report_hash")
    report_id = report.get("report_id")
    evidence_snapshot = build_evidence_snapshot(report)
    finding_workflow = build_finding_status_workflow(report)
    integrity_digest = report_integrity_digest(report)
    score = _score_value(report)

    required_missing = [key for key in ["report_id", "report_hash", "generated_at"] if not report.get(key)]

    return {
        "ok": True,
        "version": VERSION,
        "source": source,
        "generated_at": _now_iso(),
        "report_id": report_id,
        "report_hash": report_hash,
        "project_name": report.get("project_name"),
        "risk_label": _safe_dict(report.get("combined")).get("risk_label") or report.get("risk_label") or "Not Assessed",
        "score": score,
        "required_missing": required_missing,
        "verification": {
            "has_report_id": bool(report_id),
            "has_report_hash": bool(report_hash),
            "has_generated_at": bool(report.get("generated_at")),
            "payload_integrity_digest": integrity_digest,
            "metadata_integrity_ready": bool(report_id and report_hash),
            "scope": "metadata_integrity_only",
        },
        "evidence_snapshot": evidence_snapshot,
        "finding_status_workflow": finding_workflow,
        "safety_boundaries": SAFE_BOUNDARIES,
        "real_only_note": REAL_ONLY_NOTE,
    }


def verify_public_report_record(public_id: str, report_hash: str) -> dict[str, Any]:
    record = get_report_record(public_id, allow_private=True)
    if not record:
        return {
            "ok": False,
            "verified": False,
            "reason": "Report record not found",
            "safety_boundaries": SAFE_BOUNDARIES,
            "real_only_note": REAL_ONLY_NOTE,
        }

    stored_hash = record.get("report_hash")
    report = _safe_dict(record.get("report"))
    hash_match = bool(stored_hash and stored_hash == report_hash)
    packet = build_report_verification_packet(report, source="public_record") if report else None

    return {
        "ok": True,
        "verified": hash_match,
        "public_id": public_id,
        "report_id": record.get("report_id"),
        "visibility": record.get("visibility"),
        "status": record.get("status"),
        "stored_report_hash": stored_hash,
        "submitted_report_hash": report_hash,
        "reason": "Hash matches the published report record" if hash_match else "Hash does not match the published report record",
        "public_wording": record.get("public_wording") or "Pre-audit readiness reviewed by Web3Guard AI by RAADHANEX",
        "blocked_wording": record.get("blocked_wording") or ["Certified audit", "100% secure", "Exploit-proof"],
        "packet": packet,
        "safety_boundaries": SAFE_BOUNDARIES,
        "real_only_note": REAL_ONLY_NOTE,
    }


def report_verification_status() -> dict[str, Any]:
    return {
        "ok": True,
        "version": VERSION,
        "capabilities": [
            "public_report_hash_verification",
            "payload_integrity_digest",
            "evidence_snapshot_summary",
            "finding_status_workflow_bootstrap",
            "safe_public_wording_guardrails",
        ],
        "limitations": [
            "Verification does not prove a project is safe.",
            "Verification does not create a certified audit claim.",
            "Finding status changes still require real evidence or manual review.",
            "Private reports should not be shared unless intentionally published.",
        ],
        "safety_boundaries": SAFE_BOUNDARIES,
        "real_only_note": REAL_ONLY_NOTE,
    }
