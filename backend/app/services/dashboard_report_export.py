from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from app.models.schemas import SavedReport, SavedReportCreate, ScanHistoryItem

REAL_ONLY_REPORT_NOTE = (
    "Generated from saved Web3Guard scan/dashboard data only. Missing modules remain Not assessed. "
    "This is a preliminary security review, not a certified audit."
)


MODULE_LABELS = {
    "website": "Website Surface",
    "dapp": "dApp Frontend",
    "api": "API Backend",
    "contract": "Smart Contract",
    "wallet": "Wallet Flow",
    "admin_opsec": "Founder/Admin OpSec",
    "github": "GitHub Repository",
    "static_analysis": "Static Analysis",
    "deep_analysis": "Deep Analysis",
    "unified_url": "Unified URL Launch Scan",
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _json_hash(value: Any) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _normalise_payload(payload: dict[str, Any] | None) -> dict[str, Any]:
    return payload if isinstance(payload, dict) else {}


def _module_cards(payload: dict[str, Any]) -> list[dict[str, Any]]:
    cards = payload.get("module_cards")
    if isinstance(cards, list):
        return [item for item in cards if isinstance(item, dict)]
    return []


def _priority_actions(payload: dict[str, Any]) -> list[dict[str, Any]]:
    actions = payload.get("priority_actions")
    if isinstance(actions, list):
        return [item for item in actions if isinstance(item, dict)]
    combined = payload.get("combined_report") if isinstance(payload.get("combined_report"), dict) else {}
    actions = combined.get("priority_action_plan") if isinstance(combined, dict) else None
    if isinstance(actions, list):
        return [item for item in actions if isinstance(item, dict)]
    return []


def _fix_guidance(title: str, module: str | None = None) -> dict[str, str]:
    text = f"{title} {module or ''}".lower()
    if "content-security-policy" in text or "csp" in text:
        return {
            "where_to_fix": "frontend/next.config.mjs or hosting security headers",
            "why_it_matters": "A stricter CSP reduces XSS impact by limiting allowed scripts, frames, images, and API connections.",
            "how_to_fix": "Remove unsafe-inline/unsafe-eval where possible. Use nonces or hashes for required inline scripts and allow only your frontend, backend, Supabase, and Razorpay domains when enabled.",
            "verify": "Run curl -I https://your-domain.com and confirm Content-Security-Policy is present without unnecessary unsafe directives.",
        }
    if "inline script" in text:
        return {
            "where_to_fix": "frontend app/layout, script tags, third-party widgets, or bundled assets",
            "why_it_matters": "High inline script usage makes CSP harder to lock down and can increase XSS blast radius.",
            "how_to_fix": "Move inline scripts into bundled files, remove unused snippets, and use framework-supported script loading.",
            "verify": "Re-run the URL scan and confirm inline script count drops or is documented as accepted risk.",
        }
    if "robots" in text:
        return {
            "where_to_fix": "frontend/public/robots.txt",
            "why_it_matters": "robots.txt is mainly SEO/launch clarity, not a direct security control.",
            "how_to_fix": "Add a simple robots.txt that allows public pages and points crawlers to sitemap.xml if useful.",
            "verify": "Open https://your-domain.com/robots.txt and confirm HTTP 200.",
        }
    if "sitemap" in text:
        return {
            "where_to_fix": "frontend/public/sitemap.xml or generated sitemap route",
            "why_it_matters": "sitemap.xml improves discovery of public pages and launch clarity.",
            "how_to_fix": "Generate a sitemap with public routes only. Do not include admin/private dashboard URLs.",
            "verify": "Open https://your-domain.com/sitemap.xml and confirm HTTP 200 with public URLs only.",
        }
    if "rate limit" in text:
        return {
            "where_to_fix": "backend middleware and scan/payment routers",
            "why_it_matters": "Missing rate limits can exhaust API quotas or enable automated abuse.",
            "how_to_fix": "Enforce per-user and per-IP limits on scanner, auth-adjacent, report, and payment endpoints.",
            "verify": "Send repeated requests and confirm the API returns 429 after the configured threshold.",
        }
    if "webhook" in text or "payment" in text:
        return {
            "where_to_fix": "backend/app/routers/payments.py and Razorpay dashboard webhook settings",
            "why_it_matters": "Payment access must only activate after verified Razorpay signature/webhook or admin verification.",
            "how_to_fix": "Verify Razorpay signatures using the raw request body and block invalid signatures from changing paid status.",
            "verify": "Use Razorpay test webhook and confirm invalid signatures are rejected and valid payment.captured/order.paid updates audit state.",
        }
    return {
        "where_to_fix": "Manual review required",
        "why_it_matters": "This item needs project-specific context before a safe automatic fix can be recommended.",
        "how_to_fix": "Document the owner, data flow, affected users/funds, then add the missing control or evidence and re-run the scan.",
        "verify": "Re-run the scan and confirm the issue is resolved, reduced, or explicitly accepted as risk.",
    }


def _top_findings(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Return only real assessed-module bugs/actions, not missing input items."""
    findings: list[dict[str, Any]] = []
    for action in _priority_actions(payload):
        title = str(action.get("title") or "Launch risk item")
        module = str(action.get("module") or "unknown")
        findings.append(
            {
                "severity": str(action.get("severity") or "info"),
                "module": module,
                "title": title,
                "confidence": str(action.get("confidence") or "medium"),
                "recommendation": str(action.get("recommended_action") or "Review and fix before production launch."),
                "business_impact": str(action.get("business_impact") or "May reduce launch trust or increase production risk."),
                "fix_guidance": _fix_guidance(title, module),
            }
        )
    if findings:
        return findings[:30]

    combined = payload.get("combined_report") if isinstance(payload.get("combined_report"), dict) else {}
    raw = combined.get("top_findings") if isinstance(combined, dict) else []
    if isinstance(raw, list):
        for item in raw:
            if not isinstance(item, dict):
                continue
            title = str(item.get("title") or "Finding")
            module = str(item.get("module") or "unknown")
            findings.append({**item, "fix_guidance": item.get("fix_guidance") or _fix_guidance(title, module)})
    return findings[:30]


def _evidence_summary(payload: dict[str, Any]) -> list[dict[str, Any]]:
    summary: list[dict[str, Any]] = []
    for card in _module_cards(payload):
        summary.append(
            {
                "module": card.get("module") or "unknown",
                "module_label": card.get("label") or card.get("module") or "Unknown module",
                "status": card.get("status") or "Not assessed",
                "score": card.get("score"),
                "evidence": card.get("evidence") or [],
                "limitations": card.get("limitations") or [],
            }
        )
    return summary


def _evidence_required(payload: dict[str, Any]) -> list[dict[str, Any]]:
    required: list[dict[str, Any]] = []
    for card in _module_cards(payload):
        for item in card.get("required_input") or []:
            required.append(
                {
                    "module": card.get("module") or "unknown",
                    "module_label": card.get("label") or card.get("module") or "Unknown module",
                    "status": card.get("status") or "Not assessed",
                    "required_input": str(item),
                    "next_step": "Provide this evidence/input and re-run the scan. Missing modules must stay Not assessed until real evidence exists.",
                }
            )
    return required


def _module_matrix_from_cards(payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for card in _module_cards(payload):
        assessed = bool(card.get("assessed") or card.get("score") is not None)
        rows.append(
            {
                "label": card.get("label") or card.get("module") or "Unknown module",
                "module": card.get("module") or "unknown",
                "weight_percent": "assessed-only" if assessed else "not-scored",
                "score": card.get("score"),
                "risk_label": card.get("risk_label") or card.get("status") or "Not assessed",
                "assessed": assessed,
                "status": card.get("status") or "Not assessed",
                "evidence": " | ".join(str(x) for x in (card.get("evidence") or [])[:4]) or "No evidence provided",
            }
        )
    return rows


def build_professional_report_from_saved(saved_report: SavedReport) -> dict[str, Any]:
    """Build a delivery-ready report from a saved scan/report without faking missing modules."""
    payload = _normalise_payload(saved_report.payload)
    combined_report = payload.get("combined_report") if isinstance(payload.get("combined_report"), dict) else {}
    report_id = saved_report.report_id or payload.get("report_id") or combined_report.get("report_id") or saved_report.id
    project_name = saved_report.title or payload.get("project_name") or combined_report.get("project_name") or "Web3Guard Saved Report"
    available_score = saved_report.available_score if saved_report.available_score is not None else payload.get("available_score")
    overall_score = saved_report.overall_score if saved_report.overall_score is not None else payload.get("overall_score")
    risk_label = saved_report.risk_label or payload.get("risk_label") or combined_report.get("combined", {}).get("risk_label") or "Not assessed"
    module_cards = _module_cards(payload)
    assessed_count = len([card for card in module_cards if card.get("assessed") or card.get("score") is not None])
    total_modules = max(len(module_cards), 1)
    coverage_percent = round((assessed_count / total_modules) * 100) if total_modules else 0

    base = {
        **combined_report,
        "report_id": report_id,
        "source_saved_report_id": saved_report.id,
        "project_name": project_name,
        "generated_at": _now_iso(),
        "combined": {
            **(combined_report.get("combined") if isinstance(combined_report.get("combined"), dict) else {}),
            "overall_score": overall_score,
            "available_score": available_score,
            "risk_label": risk_label,
        },
        "coverage": {
            "assessed_count": assessed_count,
            "total_modules": total_modules,
            "coverage_percent": coverage_percent,
            "confidence": "high" if coverage_percent == 100 else "limited" if assessed_count else "low",
            "note": "Coverage is based on modules that had real evidence/input. Missing modules remain Not assessed.",
        },
        "module_matrix": _module_matrix_from_cards(payload),
        "priority_action_plan": _priority_actions(payload),
        "top_findings": _top_findings(payload),
        "evidence_summary": _evidence_summary(payload),
        "evidence_required": _evidence_required(payload),
        "executive_summary": payload.get("safe_public_summary")
        or combined_report.get("executive_summary")
        or f"{project_name} was reviewed using saved Web3Guard scan data. Results are limited to modules that had real evidence.",
        "risk_narrative": payload.get("realness_rule") or combined_report.get("risk_narrative") or REAL_ONLY_REPORT_NOTE,
        "before_launch_checklist": [
            "Fix all real findings listed in the report or document accepted risk with owner approval.",
            "Re-run the scanner after changes and save a new report version.",
            "Complete Not assessed modules before using this report for launch decisions.",
            "Do not represent this output as a certified audit.",
        ],
        "limitations": [
            REAL_ONLY_REPORT_NOTE,
            "No exploit automation, wallet signing, seed phrase collection, or certified audit claim is performed.",
            "Missing contract, wallet, admin, or private source evidence remains Not assessed.",
        ],
        "package_recommendation": {
            "package": "Manual security review recommended before public launch",
            "reason": "Automated/passive checks cannot replace manual verification for launch-critical systems.",
        },
        "disclaimer": REAL_ONLY_REPORT_NOTE,
        "blocked_claims": ["Certified audit", "100% secure", "Exploit-proof", "Insurance guaranteed"],
    }
    base["report_hash"] = saved_report.report_hash or combined_report.get("report_hash") or _json_hash(base)
    base["json_export"] = base
    base["markdown_report"] = build_markdown_report(base)
    return base


def build_saved_report_create_from_scan(scan: ScanHistoryItem, title: str | None = None) -> SavedReportCreate:
    payload = _normalise_payload(scan.payload)
    report_seed = {
        "scan_id": scan.id,
        "project_id": scan.project_id,
        "report_id": scan.report_id or f"report_from_{scan.id}",
        "project_name": scan.project_name,
        "score": scan.score,
        "risk_label": scan.risk_label,
        "payload": payload,
    }
    report_hash = _json_hash(report_seed)
    return SavedReportCreate(
        user_id=scan.user_id,
        project_id=scan.project_id,
        scan_id=scan.id,
        report_id=scan.report_id or f"report_from_{scan.id}",
        title=title or f"{scan.project_name or 'Web3Guard'} {scan.module} report",
        report_hash=report_hash,
        overall_score=scan.score,
        available_score=scan.score,
        risk_label=scan.risk_label,
        visibility="private",
        status="draft_from_saved_scan",
        payload=payload,
    )


def build_markdown_report(report: dict[str, Any]) -> str:
    lines = [
        f"# {report.get('project_name', 'Web3Guard Report')}",
        "",
        f"Report ID: `{report.get('report_id', 'not-generated')}`",
        f"Report hash: `{report.get('report_hash', 'not-available')}`",
        "",
        "## Important disclaimer",
        REAL_ONLY_REPORT_NOTE,
        "",
        "## Executive summary",
        str(report.get("executive_summary") or "No executive summary provided."),
        "",
        "## Real bugs / findings with fix hints",
    ]
    findings = report.get("top_findings") or []
    if findings:
        for index, finding in enumerate(findings, start=1):
            fix = finding.get("fix_guidance") or {}
            lines.extend(
                [
                    f"{index}. **{str(finding.get('severity', 'info')).upper()} — {finding.get('title')}**",
                    f"   - Module: {finding.get('module')}",
                    f"   - Recommendation: {finding.get('recommendation')}",
                    f"   - Where to fix: {fix.get('where_to_fix', 'Manual review required')}",
                    f"   - How to fix: {fix.get('how_to_fix', 'Apply project-specific fix and re-run scan.')}",
                    f"   - Verify: {fix.get('verify', 'Re-run scan after the fix.')}",
                ]
            )
    else:
        lines.append("No real assessed-module bugs were detected in this saved scan payload.")

    lines.extend(["", "## Evidence required / Not assessed modules"])
    required = report.get("evidence_required") or []
    if required:
        for item in required:
            lines.append(f"- **{item.get('module_label', item.get('module'))}**: {item.get('required_input')}")
    else:
        lines.append("No missing evidence was listed.")

    lines.extend(["", "## Module coverage"])
    for row in report.get("module_matrix") or []:
        score = row.get("score") if row.get("score") is not None else "Not assessed"
        lines.append(f"- {row.get('label')}: {score} · {row.get('status')}")
    lines.extend(["", "## Limitations"])
    for item in report.get("limitations") or []:
        lines.append(f"- {item}")
    return "\n".join(lines).strip() + "\n"
