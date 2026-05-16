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
    return []


def _top_findings(payload: dict[str, Any]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for card in _module_cards(payload):
        module = str(card.get("module") or card.get("label") or "unknown")
        for evidence in card.get("evidence") or []:
            findings.append(
                {
                    "severity": "info",
                    "module": module,
                    "title": str(evidence),
                    "confidence": "medium",
                    "recommendation": "Review the evidence and apply the module-specific fix guidance before production launch.",
                }
            )
        for missing in card.get("required_input") or []:
            findings.append(
                {
                    "severity": "medium",
                    "module": module,
                    "title": f"Missing input: {missing}",
                    "confidence": "high",
                    "recommendation": "Provide the missing evidence/input and re-run the scan. Do not score missing modules with fake data.",
                }
            )
    return findings[:40]


def build_professional_report_from_saved(saved_report: SavedReport) -> dict[str, Any]:
    """Build a professional report object from a saved dashboard report.

    The returned object is compatible with app.services.professional_report exporters.
    It does not invent manual audit claims or missing-module scores.
    """

    payload = _normalise_payload(saved_report.payload)
    source = payload.get("report") if isinstance(payload.get("report"), dict) else payload
    report_id = saved_report.report_id or source.get("report_id") or saved_report.id
    project_name = saved_report.title or source.get("project_name") or "Web3Guard Saved Report"
    available_score = saved_report.available_score if saved_report.available_score is not None else source.get("available_score")
    overall_score = saved_report.overall_score if saved_report.overall_score is not None else source.get("overall_score")
    risk_label = saved_report.risk_label or source.get("risk_label") or "Not assessed"
    module_cards = _module_cards(source)
    priority_actions = _priority_actions(source)
    assessed_count = len([card for card in module_cards if str(card.get("status", "")).lower().startswith("live") or card.get("score") is not None])
    total_modules = max(len(module_cards), 1)
    coverage_percent = round((assessed_count / total_modules) * 100) if total_modules else 0

    base = {
        "report_id": report_id,
        "source_saved_report_id": saved_report.id,
        "project_name": project_name,
        "generated_at": _now_iso(),
        "combined": {
            "overall_score": overall_score,
            "available_score": available_score,
            "risk_label": risk_label,
        },
        "coverage": {
            "assessed_count": assessed_count,
            "total_modules": total_modules,
            "coverage_percent": coverage_percent,
            "confidence": "medium" if assessed_count else "low",
        },
        "module_matrix": [
            {
                "label": card.get("label") or card.get("module") or "Unknown module",
                "module": card.get("module") or "unknown",
                "weight_percent": card.get("weight_percent") or 0,
                "score": card.get("score"),
                "risk_label": card.get("risk_label") or card.get("status") or "Not assessed",
                "assessed": card.get("score") is not None,
                "status": card.get("status") or "Not assessed",
            }
            for card in module_cards
        ],
        "priority_action_plan": priority_actions,
        "top_findings": _top_findings(source),
        "executive_summary": source.get("safe_public_summary")
        or f"{project_name} was reviewed using saved Web3Guard scan data. Results are limited to modules that had real evidence.",
        "risk_narrative": source.get("realness_rule") or REAL_ONLY_REPORT_NOTE,
        "before_launch_checklist": [
            "Fix all critical/high findings or document accepted risk with owner approval.",
            "Re-run the scanner after changes and save the new report version.",
            "Complete Not assessed modules before using this report for launch decisions.",
            "Do not represent this output as a certified audit.",
        ],
        "limitations": [
            REAL_ONLY_REPORT_NOTE,
            "No exploit automation, wallet signing, seed phrase collection, or certified audit claim is performed.",
            "Missing contract, wallet, admin, or private source evidence remains Not assessed.",
        ],
        "package_recommendation": {
            "package": "Manual security review recommended before launch" if risk_label.lower() != "low" else "Maintenance monitoring recommended",
            "reason": "Automated/passive checks cannot replace manual verification for launch-critical systems.",
        },
        "disclaimer": REAL_ONLY_REPORT_NOTE,
        "blocked_claims": ["Certified audit", "100% secure", "Exploit-proof", "Insurance guaranteed"],
    }
    base["report_hash"] = saved_report.report_hash or _json_hash(base)
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
        "## Priority action plan",
    ]
    actions = report.get("priority_action_plan") or []
    if actions:
        for action in actions:
            lines.append(f"- **{str(action.get('severity', 'info')).upper()}** {action.get('title')}: {action.get('recommended_action')}")
    else:
        lines.append("- No priority actions were provided in the saved report payload.")
    lines.extend(["", "## Module coverage"])
    for row in report.get("module_matrix") or []:
        score = row.get("score") if row.get("score") is not None else "Not assessed"
        lines.append(f"- {row.get('label')}: {score} · {row.get('status')}")
    return "\n".join(lines).strip() + "\n"
