from __future__ import annotations

from pathlib import Path
from typing import Any

from app.core.config import settings
from app.models.schemas import ComplianceScanRequest
from app.services.mega_phase_e_store import append_jsonl, new_id, now_iso, read_jsonl, storage_path

COMPLIANCE_REAL_ONLY_NOTE = (
    "This is a compliance readiness checklist, not legal advice. It records supplied evidence and flags gaps; "
    "a lawyer/CA/compliance professional should review before launch."
)


def compliance_status() -> dict[str, Any]:
    return {
        "ok": True,
        "version": "1.0",
        "jurisdictions": ["general_web3", "india_vda", "mica_eu", "gdpr", "fatf_aml"],
        "output": ["score", "readiness_label", "findings", "policy_gap_checklist", "manual_review_items"],
        "real_only_note": COMPLIANCE_REAL_ONLY_NOTE,
    }


def _path() -> Path:
    return storage_path(settings.compliance_scans_file)


def _finding(severity: str, title: str, description: str, recommendation: str, jurisdiction: str = "general") -> dict[str, Any]:
    return {"id": new_id("cmp_find"), "severity": severity, "jurisdiction": jurisdiction, "title": title, "description": description, "recommendation": recommendation, "source": "compliance_checklist", "confidence": 0.82}


def _penalty(sev: str) -> int:
    return {"critical": 25, "high": 15, "medium": 8, "low": 3, "info": 1}.get(sev, 3)


def run_compliance_scan(payload: ComplianceScanRequest, user_id: str) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    jurisdictions = set(payload.jurisdictions or ["general_web3"])
    if not payload.has_terms:
        findings.append(_finding("medium", "Terms of Service not confirmed", "Launch page/app has no confirmed terms or usage scope.", "Publish clear terms covering scanner/sale scope, user responsibilities, refunds, prohibited use, and liability limits."))
    if not payload.has_privacy_policy:
        sev = "high" if payload.collects_personal_data else "medium"
        findings.append(_finding(sev, "Privacy policy gap", "Personal or project contact data may be collected without a confirmed privacy policy.", "Publish privacy policy with data collection, retention, deletion, processors, and contact details."))
    if payload.collects_personal_data and not payload.has_data_deletion_flow:
        findings.append(_finding("high", "Data deletion/export flow missing", "User personal data collection needs a deletion/export request workflow.", "Add account/data deletion request flow and document retention period.", "gdpr"))
    if "gdpr" in jurisdictions and payload.collects_personal_data and not payload.has_cookie_banner:
        findings.append(_finding("medium", "Cookie/analytics consent not confirmed", "EU/GDPR readiness may require consent or legitimate interest review for cookies/analytics.", "Review cookie use and add consent/notice where needed.", "gdpr"))
    if payload.handles_payments_in_inr and not payload.has_gst_invoice_flow:
        findings.append(_finding("medium", "GST invoice flow not confirmed", "INR paid plans should have invoice/GST handling before serious launch.", "Add GST fields, invoice numbering, payment receipt, and accountant review.", "india_vda"))
    if ("india_vda" in jurisdictions or "fatf_aml" in jurisdictions) and not payload.has_risk_disclosure:
        findings.append(_finding("medium", "Crypto/Web3 risk disclosure missing", "Users may mistake readiness report as investment/audit guarantee.", "Add no-investment-advice, no-certified-audit, no-100%-security, and crypto-risk disclosure.", "india_vda"))
    if ("fatf_aml" in jurisdictions or payload.has_kyc_flow) and not payload.has_aml_policy:
        findings.append(_finding("medium", "AML/KYC policy evidence missing", "If KYC/regulated flows are used, AML/sanctions handling needs documented process.", "Document KYC/AML vendor, sanctions checks, retention, escalation, and false-positive handling.", "fatf_aml"))
    if not payload.has_refund_policy:
        findings.append(_finding("low", "Refund/scope policy not confirmed", "Paid manual review packages need scope and refund clarity.", "Publish scope/refund policy that separates automated scan, manual review, and out-of-scope work."))
    if not payload.has_incident_response:
        findings.append(_finding("medium", "Incident response process missing", "Security product or Web3 launch needs clear incident contact and escalation flow.", "Add incident response contact, severity triage, response time targets, and disclosure process."))
    if not payload.has_bug_bounty_safe_harbor:
        findings.append(_finding("low", "Safe harbor not confirmed", "If researchers report issues, lack of safe harbor creates trust and legal ambiguity.", "Publish responsible disclosure/safe harbor language."))
    notes = (payload.notes or "").lower()
    if "guaranteed" in notes or "100% secure" in notes or "certified audit" in notes:
        findings.append(_finding("high", "Risky marketing claim detected in notes", "The supplied notes include wording that can create legal/trust risk.", "Replace with 'pre-audit readiness review' and clear limitations."))
    score = max(0, 100 - sum(_penalty(f["severity"]) for f in findings))
    label = "strong" if score >= 85 else "needs review" if score >= 70 else "high priority gaps" if score >= 50 else "not launch-ready"
    report = {
        "id": new_id("cmp_scan"),
        "user_id": user_id,
        "created_at": now_iso(),
        "project_name": payload.project_name,
        "project_type": payload.project_type,
        "jurisdictions": list(jurisdictions),
        "score": score,
        "readiness_label": label,
        "findings": findings,
        "manual_review_required": any(f["severity"] in {"critical", "high"} for f in findings),
        "not_legal_advice": True,
        "real_only_note": COMPLIANCE_REAL_ONLY_NOTE,
    }
    append_jsonl(_path(), report)
    return report


def list_compliance_scans(limit: int = 50) -> list[dict[str, Any]]:
    return sorted(read_jsonl(_path()), key=lambda r: r.get("created_at", ""), reverse=True)[:limit]
