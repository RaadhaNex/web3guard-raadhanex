import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from app.models.schemas import CombinedReportRequest, Finding, ScanResponse
from app.services.ai_explainer import ai_status, summarize_report
from app.services.scoring import SEVERITY_ORDER, WEIGHTS, combine_scores

DISCLAIMER = (
    "This is an AI-assisted preliminary Web3 launch security review by Web3Guard AI by RAADHANEX. "
    "It does not replace a full manual audit, legal review, financial advice, or independent security assessment. "
    "Do not treat this as a certified audit, insurance certificate, or guarantee of safety."
)

MODULE_LABELS = {
    "contract": "Smart Contract",
    "website": "Website Surface",
    "dapp": "dApp Frontend",
    "api": "API Backend",
    "wallet": "Wallet Flow",
    "admin_opsec": "Founder/Admin OpSec",
}

BEFORE_LAUNCH_CHECKLIST = [
    "Resolve every critical and high severity finding, then regenerate the report.",
    "Confirm owner/admin roles use multisig and timelock where appropriate.",
    "Verify dApp domain, chain ID, contract addresses, spender addresses, and transaction copy.",
    "Keep private keys/seed phrases out of code, cloud notes, chat apps, and shared devices.",
    "Run a manual review before public launch if funds, minting, staking, rewards, or upgrades are involved.",
    "Prepare a clear incident response contact and pause/emergency process before mainnet.",
]

PUBLIC_SUMMARY_NOTE = (
    "Share only the executive summary and module scores publicly unless sensitive details are reviewed. "
    "Use the phrase 'pre-audit readiness reviewed' instead of 'audited/certified'."
)


def _stable_payload(reports: list[ScanResponse]) -> str:
    payload = []
    for report in reports:
        payload.append(
            {
                "report_id": report.report_id,
                "module": report.module_score.module,
                "score": report.module_score.score,
                "input_hash": report.input_hash,
                "findings": [
                    {
                        "id": finding.id,
                        "severity": finding.severity,
                        "title": finding.title,
                        "fingerprint": finding.fingerprint,
                    }
                    for finding in report.findings
                ],
            }
        )
    return json.dumps(payload, sort_keys=True, default=str)


def _report_digest(project_name: str, reports: list[ScanResponse]) -> tuple[str, str]:
    stable = project_name + "|" + _stable_payload(reports)
    full_hash = hashlib.sha256(stable.encode()).hexdigest()
    return full_hash[:12].upper(), full_hash


def _sort_findings(findings: list[Finding]) -> list[Finding]:
    confidence_rank = {"high": 0, "medium": 1, "low": 2}
    return sorted(findings, key=lambda f: (SEVERITY_ORDER.index(f.severity), confidence_rank.get(f.confidence, 3), f.module, f.title))


def _severity_rollup(findings: list[Finding]) -> dict[str, int]:
    return {severity: sum(1 for finding in findings if finding.severity == severity) for severity in SEVERITY_ORDER}


def _module_summaries(reports: list[ScanResponse]) -> list[dict[str, Any]]:
    summaries: list[dict[str, Any]] = []
    for report in reports:
        summaries.append(
            {
                "module": report.module_score.module,
                "label": MODULE_LABELS.get(report.module_score.module, report.module_score.module),
                "score": report.module_score.score,
                "risk_label": report.module_score.risk_label,
                "findings_count": len(report.findings),
                "critical_high_count": sum(1 for f in report.findings if f.severity in {"critical", "high"}),
                "report_id": report.report_id,
                "engine_version": report.engine_version,
                "assessed": True,
            }
        )
    return summaries


def _module_matrix(reports: list[ScanResponse], combined: dict[str, Any]) -> list[dict[str, Any]]:
    by_module = {report.module_score.module: report for report in reports}
    matrix: list[dict[str, Any]] = []
    for module, weight in WEIGHTS.items():
        report = by_module.get(module)
        if report:
            critical_high = sum(1 for finding in report.findings if finding.severity in {"critical", "high"})
            matrix.append(
                {
                    "module": module,
                    "label": MODULE_LABELS[module],
                    "weight_percent": round(weight * 100),
                    "assessed": True,
                    "score": report.module_score.score,
                    "risk_label": report.module_score.risk_label,
                    "findings_count": len(report.findings),
                    "critical_high_count": critical_high,
                    "status": "Needs action" if critical_high else "Reviewed",
                    "evidence": report.scan_metadata.get("phase") or report.engine_version,
                }
            )
        else:
            matrix.append(
                {
                    "module": module,
                    "label": MODULE_LABELS[module],
                    "weight_percent": round(weight * 100),
                    "assessed": False,
                    "score": None,
                    "risk_label": "Not assessed",
                    "findings_count": 0,
                    "critical_high_count": 0,
                    "status": "Missing input",
                    "evidence": "Complete this module for full launch score.",
                }
            )
    matrix.append(
        {
            "module": "overall",
            "label": "Weighted Launch Readiness",
            "weight_percent": 100,
            "assessed": bool(combined.get("available_score") is not None),
            "score": combined.get("overall_score") or combined.get("available_score"),
            "risk_label": combined.get("risk_label", "Not assessed"),
            "findings_count": None,
            "critical_high_count": None,
            "status": "Full score" if combined.get("overall_score") is not None else "Available score only",
            "evidence": "All six modules required for full launch score.",
        }
    )
    return matrix


def _coverage(combined: dict[str, Any]) -> dict[str, Any]:
    assessed = combined.get("assessed_modules", [])
    missing = combined.get("missing_modules", [])
    total = len(WEIGHTS)
    assessed_count = len(assessed)
    percent = round((assessed_count / total) * 100) if total else 0
    if assessed_count == total:
        confidence = "high"
        note = "All six launch-surface modules are assessed. Overall launch score is available."
    elif assessed_count >= 4:
        confidence = "medium"
        note = "Most modules are assessed, but missing modules can hide launch risk."
    elif assessed_count >= 2:
        confidence = "limited"
        note = "Only partial launch surface is assessed. Treat the score as directional."
    else:
        confidence = "low"
        note = "Single-module reports cannot represent full launch readiness."
    return {
        "assessed_count": assessed_count,
        "total_modules": total,
        "coverage_percent": percent,
        "assessed_modules": assessed,
        "missing_modules": missing,
        "confidence": confidence,
        "note": note,
    }


def _package_recommendation(score: int | None, findings: list[Finding], coverage: dict[str, Any]) -> dict[str, str]:
    has_critical = any(f.severity == "critical" for f in findings)
    high_count = sum(1 for f in findings if f.severity == "high")
    if has_critical or (score is not None and score < 50):
        return {
            "package_id": "manual-pre-audit-review",
            "package": "Manual Pre-Audit Review — ₹14,999+",
            "reason": "Critical launch blockers or very high risk need human review before public launch.",
            "cta": "Request manual review before mainnet launch",
        }
    if coverage["coverage_percent"] < 70:
        return {
            "package_id": "detailed-launch-readiness-report",
            "package": "Detailed Web3 Launch Readiness Report — ₹2,999",
            "reason": "The report currently covers only part of the launch surface. A detailed review can complete missing modules and produce a delivery-ready report.",
            "cta": "Complete launch readiness review",
        }
    if high_count >= 2 or (score is not None and score < 75):
        return {
            "package_id": "detailed-launch-readiness-report",
            "package": "Detailed Web3 Launch Readiness Report — ₹2,999",
            "reason": "Multiple high/medium issues should be converted into an actionable fix plan.",
            "cta": "Get detailed fix plan",
        }
    if score is not None and score >= 90:
        return {
            "package_id": "quick-risk-scan-report",
            "package": "Quick Risk Scan Report — ₹999",
            "reason": "The project looks comparatively cleaner, but a packaged report helps document scope and trust notes.",
            "cta": "Package this report",
        }
    return {
        "package_id": "fix-suggestion-pack",
        "package": "Fix Suggestion Pack — ₹7,999",
        "reason": "The project has fixable issues where code/checklist guidance can reduce launch risk.",
        "cta": "Request fix suggestions",
    }


def _priority_plan(findings: list[Finding]) -> list[dict[str, Any]]:
    plan: list[dict[str, Any]] = []
    for index, finding in enumerate(_sort_findings(findings)[:12], start=1):
        plan.append(
            {
                "step": index,
                "severity": finding.severity,
                "title": finding.title,
                "module": finding.module,
                "module_label": MODULE_LABELS.get(finding.module, finding.module),
                "recommended_action": finding.recommendation,
                "business_impact": finding.business_impact,
                "manual_review_recommended": finding.paid_review_recommended or finding.severity in {"critical", "high"},
            }
        )
    return plan


def _executive_summary(project_name: str, combined: dict[str, Any], findings: list[Finding], coverage: dict[str, Any]) -> str:
    score = combined.get("available_score") or combined.get("overall_score")
    risk = combined.get("risk_label", "Not assessed")
    critical = sum(1 for f in findings if f.severity == "critical")
    high = sum(1 for f in findings if f.severity == "high")
    assessed_count = coverage["assessed_count"]
    if score is None:
        return f"{project_name} has not provided enough module data for a launch readiness score. Complete all six modules before making launch decisions."
    score_type = "full weighted launch score" if combined.get("overall_score") is not None else "available partial launch score"
    return (
        f"{project_name} received an {score_type} of {score}/100 ({risk}) across {assessed_count}/6 assessed module(s). "
        f"The report found {critical} critical and {high} high-priority issue(s). "
        "Fix critical/high items first, complete any missing modules, then regenerate this report before public launch."
    )


def _risk_narrative(score: int | None, coverage: dict[str, Any], findings: list[Finding]) -> str:
    if score is None:
        return "No launch readiness score is available yet because no module results were provided."
    critical = any(f.severity == "critical" for f in findings)
    high = any(f.severity == "high" for f in findings)
    if critical:
        return "Critical issues are present. Treat launch as blocked until the issue is fixed and manually reviewed."
    if high:
        return "High-priority issues are present. Launch should be delayed until fixes are reviewed."
    if coverage["coverage_percent"] < 100:
        return "No critical/high issues were detected in assessed modules, but missing modules reduce confidence."
    if score >= 90:
        return "The assessed launch surface looks comparatively clean, but this is still not a certified audit."
    return "The project has fixable risks. Use the priority action plan before launch."


def _limitations(missing_modules: list[str]) -> list[str]:
    items = [
        "This is a preliminary rule/checklist/passive review, not a certified audit.",
        "The scanner does not execute exploits, bypass authentication, brute force endpoints, or guarantee exploitability.",
        "Smart contract findings should be validated with manual review and, in future phases, Slither/Aderyn/Mythril integrations.",
        "Website checks are passive and limited to safe public metadata/header checks.",
        "Checklist modules depend on the accuracy of founder/developer inputs.",
        "AI/fallback explanations are guidance only and must be reviewed before production use.",
    ]
    if missing_modules:
        labels = [MODULE_LABELS.get(module, module) for module in missing_modules]
        items.append(f"Missing modules reduce confidence: {', '.join(labels)}.")
    return items


def _client_delivery(report_id: str, report_hash: str, package_rec: dict[str, str]) -> dict[str, Any]:
    return {
        "report_id": report_id,
        "verification_hash": report_hash,
        "delivery_formats": ["Web preview", "Browser print / Save as PDF", "Markdown", "JSON"],
        "recommended_cta": package_rec["cta"],
        "public_wording": "Pre-audit readiness reviewed by Web3Guard AI by RAADHANEX",
        "do_not_use_wording": ["Certified audit", "100% secure", "Insurance guaranteed", "Exploit-proof"],
        "manual_verification_required": True,
    }


def _markdown_report(report: dict[str, Any]) -> str:
    lines = [
        f"# Web3Guard AI Launch Readiness Report — {report['project_name']}",
        "",
        f"**Report ID:** {report['report_id']}",
        f"**Verification hash:** `{report['report_hash']}`",
        f"**Generated:** {report['generated_at']}",
        f"**Score:** {report['combined'].get('available_score', 'Not assessed')}/100",
        f"**Risk label:** {report['combined'].get('risk_label', 'Not assessed')}",
        f"**Coverage:** {report['coverage']['assessed_count']}/{report['coverage']['total_modules']} modules ({report['coverage']['coverage_percent']}%)",
        f"**Score confidence:** {report['coverage']['confidence']}",
        "",
        "## Executive Summary",
        report["executive_summary"],
        "",
        "## Risk Narrative",
        report["risk_narrative"],
        "",
        "## Module Matrix",
    ]
    for module in report["module_matrix"]:
        score = module["score"] if module["score"] is not None else "Not assessed"
        lines.append(f"- **{module['label']}** ({module['weight_percent']}%): {score} — {module['risk_label']} — {module['status']}")
    lines.extend(["", "## Severity Breakdown"])
    for severity, count in report["severity_breakdown"].items():
        lines.append(f"- **{severity.title()}**: {count}")
    lines.extend(["", "## Priority Action Plan"])
    if report["priority_action_plan"]:
        for item in report["priority_action_plan"]:
            lines.append(
                f"{item['step']}. **{item['severity'].upper()} — {item['title']}** "
                f"({item['module_label']}): {item['recommended_action']}"
            )
    else:
        lines.append("No priority actions were found for the provided modules. Complete all modules before launch decisions.")
    lines.extend(["", "## Before Launch Checklist"])
    for item in report["before_launch_checklist"]:
        lines.append(f"- [ ] {item}")
    lines.extend(["", "## Recommended Package", f"**{report['package_recommendation']['package']}** — {report['package_recommendation']['reason']}"])
    lines.extend(["", "## Public Sharing Note", report["public_summary_note"]])
    lines.extend(["", "## Limitations"])
    for item in report["limitations"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Disclaimer", report["disclaimer"]])
    return "\n".join(lines)


async def build_combined_launch_report(payload: CombinedReportRequest) -> dict[str, Any]:
    module_scores = {report.module_score.module: report.module_score.score for report in payload.reports}
    combined = combine_scores(module_scores)
    findings = [finding for report in payload.reports for finding in report.findings]
    sorted_findings = _sort_findings(findings)
    short_digest, report_hash = _report_digest(payload.project_name, payload.reports)
    report_id = f"W3G-RAADHANEX-{short_digest}"
    coverage = _coverage(combined)
    score = combined.get("available_score") or combined.get("overall_score")
    package_rec = _package_recommendation(score, findings, coverage)
    report = {
        "report_id": report_id,
        "report_hash": report_hash,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "project_name": payload.project_name,
        "report_mode": payload.report_mode,
        "language": payload.preferred_language,
        "scores": module_scores,
        "combined": combined,
        "coverage": coverage,
        "score_confidence": coverage["confidence"],
        "severity_breakdown": _severity_rollup(findings),
        "module_summaries": _module_summaries(payload.reports),
        "module_matrix": _module_matrix(payload.reports, combined),
        "executive_summary": _executive_summary(payload.project_name, combined, findings, coverage),
        "risk_narrative": _risk_narrative(score, coverage, findings),
        "priority_action_plan": _priority_plan(sorted_findings),
        "top_findings": [finding.model_dump(mode="json") for finding in sorted_findings[:15]],
        "package_recommendation": package_rec,
        "before_launch_checklist": BEFORE_LAUNCH_CHECKLIST,
        "limitations": _limitations(combined.get("missing_modules", [])),
        "next_steps": [
            "Fix critical and high severity findings first.",
            "Complete every missing launch-surface module for a full weighted score.",
            "Regenerate the report after fixes to confirm risk reduction.",
            "Use multisig/timelock and clean admin OpSec before mainnet launch.",
            "Book a manual pre-audit review for contracts holding funds or public mint/claim flows.",
        ],
        "public_summary_note": PUBLIC_SUMMARY_NOTE,
        "client_delivery": _client_delivery(report_id, report_hash, package_rec),
        "ai_status": ai_status(),
        "ai_summary": None,
        "disclaimer": DISCLAIMER,
    }
    if payload.include_ai:
        report["ai_summary"] = (await summarize_report(report, payload.preferred_language, payload.report_mode)).model_dump(mode="json")
    report["markdown_report"] = _markdown_report(report)
    report["json_export"] = {
        "report_id": report_id,
        "report_hash": report_hash,
        "project_name": payload.project_name,
        "scores": module_scores,
        "combined": combined,
        "coverage": coverage,
        "severity_breakdown": report["severity_breakdown"],
        "priority_action_plan": report["priority_action_plan"],
        "disclaimer": DISCLAIMER,
    }
    return report
