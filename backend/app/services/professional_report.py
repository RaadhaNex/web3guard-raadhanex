from __future__ import annotations

import html
import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from io import BytesIO
from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.core.config import settings

REAL_ONLY_NOTE = (
    "This professional report is generated from provided scanner/checklist/passive-scan data only. "
    "Missing modules remain Not Assessed. This is not a certified audit."
)

REPORT_BRAND = "Web3Guard AI by RAADHANEX"
PUBLIC_WORDING = "Pre-audit readiness reviewed by Web3Guard AI by RAADHANEX"
BLOCKED_WORDING = ["Certified audit", "100% secure", "Insurance guaranteed", "Exploit-proof"]


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _public_reports_path() -> Path:
    path = Path(settings.public_reports_file)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.touch(exist_ok=True)
    return path


def delivery_policy() -> dict[str, Any]:
    return {
        "ok": True,
        "version": "1.0",
        "live_formats": ["professional_html", "server_pdf", "markdown", "json", "public_private_record"],
        "manual_limits": [
            "Report quality depends on modules actually assessed.",
            "Public links use pre-audit readiness wording only.",
            "Server PDF is generated from the same report object; it does not add manual audit claims.",
            "Sensitive findings should be reviewed before publishing publicly.",
        ],
        "blocked_claims": BLOCKED_WORDING,
        "real_only_note": REAL_ONLY_NOTE,
    }


def _score_value(report: dict[str, Any]) -> str:
    combined = report.get("combined", {}) or {}
    score = combined.get("overall_score")
    if score is None:
        score = combined.get("available_score")
    return "Not assessed" if score is None else f"{score}/100"


def _risk_label(report: dict[str, Any]) -> str:
    return (report.get("combined", {}) or {}).get("risk_label") or "Not assessed"


def _safe_text(value: Any) -> str:
    if value is None:
        return ""
    return html.escape(str(value))


def build_professional_html(report: dict[str, Any]) -> str:
    project = _safe_text(report.get("project_name", "Web3 Project"))
    report_id = _safe_text(report.get("report_id", "Not generated"))
    report_hash = _safe_text(report.get("report_hash", "Not available"))
    generated = _safe_text(report.get("generated_at", _now().isoformat()))
    score = _safe_text(_score_value(report))
    risk = _safe_text(_risk_label(report))
    coverage = report.get("coverage", {}) or {}
    coverage_text = _safe_text(f"{coverage.get('assessed_count', 0)}/{coverage.get('total_modules', 6)} modules · {coverage.get('coverage_percent', 0)}% · {coverage.get('confidence', 'low')} confidence")

    matrix_rows = []
    for row in report.get("module_matrix", []) or []:
        score_cell = "Not assessed" if row.get("score") is None else str(row.get("score"))
        assessed = "Yes" if row.get("assessed") else "No"
        matrix_rows.append(
            f"<tr><td>{_safe_text(row.get('label'))}</td><td>{_safe_text(row.get('weight_percent'))}%</td>"
            f"<td>{_safe_text(score_cell)}</td><td>{_safe_text(row.get('risk_label'))}</td>"
            f"<td>{assessed}</td><td>{_safe_text(row.get('status'))}</td></tr>"
        )
    if not matrix_rows:
        matrix_rows.append("<tr><td colspan='6'>No module matrix provided.</td></tr>")

    priority_rows = []
    for item in report.get("priority_action_plan", []) or []:
        priority_rows.append(
            f"<li><strong>{_safe_text(item.get('severity', '')).upper()} — {_safe_text(item.get('title'))}</strong> "
            f"({_safe_text(item.get('module_label', item.get('module')))}): {_safe_text(item.get('recommended_action'))}</li>"
        )
    if not priority_rows:
        priority_rows.append("<li>No priority actions found in assessed modules. Complete missing modules before launch decisions.</li>")

    findings_rows = []
    for finding in (report.get("top_findings", []) or [])[:20]:
        findings_rows.append(
            f"<tr><td>{_safe_text(finding.get('severity', '')).upper()}</td><td>{_safe_text(finding.get('module'))}</td>"
            f"<td>{_safe_text(finding.get('title'))}</td><td>{_safe_text(finding.get('confidence'))}</td>"
            f"<td>{_safe_text(finding.get('recommendation'))}</td></tr>"
        )
    if not findings_rows:
        findings_rows.append("<tr><td colspan='5'>No findings were provided in this report object.</td></tr>")

    checklist = "".join(f"<li>{_safe_text(item)}</li>" for item in report.get("before_launch_checklist", []) or [])
    limitations = "".join(f"<li>{_safe_text(item)}</li>" for item in report.get("limitations", []) or [])
    package = report.get("package_recommendation", {}) or {}

    return f"""<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <title>{project} — Web3Guard AI Launch Readiness Report</title>
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <style>
    :root {{ color-scheme: dark; --bg:#07111f; --card:#0f1b2d; --line:#24405f; --text:#f8fafc; --muted:#b7c4d8; --cyan:#22d3ee; --danger:#fb7185; --warn:#fbbf24; --ok:#34d399; }}
    body {{ margin:0; font-family: Inter, Arial, sans-serif; background:var(--bg); color:var(--text); line-height:1.55; }}
    .page {{ max-width: 980px; margin:0 auto; padding:40px 24px; }}
    .hero {{ border:1px solid var(--line); border-radius:28px; padding:32px; background:linear-gradient(135deg,#0f1b2d,#081120); }}
    .eyebrow {{ color:var(--cyan); text-transform:uppercase; letter-spacing:.25em; font-size:12px; font-weight:900; }}
    h1 {{ margin:12px 0 8px; font-size:40px; line-height:1.05; }}
    h2 {{ margin-top:34px; font-size:24px; }}
    .grid {{ display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:12px; margin-top:22px; }}
    .metric {{ border:1px solid var(--line); border-radius:18px; padding:16px; background:#0b1627; }}
    .metric strong {{ display:block; font-size:22px; }}
    .muted {{ color:var(--muted); }}
    table {{ width:100%; border-collapse:collapse; margin-top:12px; overflow:hidden; border-radius:16px; }}
    th,td {{ border:1px solid var(--line); padding:10px; text-align:left; vertical-align:top; font-size:14px; }}
    th {{ color:var(--cyan); background:#0b1627; }}
    .notice {{ border:1px solid #6b4b13; background:#1f1707; border-radius:18px; padding:16px; margin-top:18px; color:#fde68a; }}
    .section {{ border:1px solid var(--line); background:var(--card); border-radius:22px; padding:22px; margin-top:20px; }}
    .footer {{ color:var(--muted); font-size:12px; margin-top:28px; border-top:1px solid var(--line); padding-top:18px; }}
    @media print {{ body {{ background:white; color:#111827; }} .hero,.section,.metric,.notice {{ background:white; color:#111827; border-color:#d1d5db; }} .muted,.footer {{ color:#374151; }} th {{ color:#111827; background:#f3f4f6; }} }}
  </style>
</head>
<body>
  <main class=\"page\">
    <section class=\"hero\">
      <div class=\"eyebrow\">{REPORT_BRAND}</div>
      <h1>{project}</h1>
      <p class=\"muted\">Professional Launch Readiness Report · {PUBLIC_WORDING}</p>
      <div class=\"grid\">
        <div class=\"metric\"><span class=\"muted\">Score</span><strong>{score}</strong></div>
        <div class=\"metric\"><span class=\"muted\">Risk</span><strong>{risk}</strong></div>
        <div class=\"metric\"><span class=\"muted\">Coverage</span><strong>{coverage_text}</strong></div>
        <div class=\"metric\"><span class=\"muted\">Report ID</span><strong>{report_id}</strong></div>
      </div>
      <div class=\"notice\"><strong>Important:</strong> {REAL_ONLY_NOTE}</div>
    </section>

    <section class=\"section\">
      <h2>Executive Summary</h2>
      <p>{_safe_text(report.get('executive_summary'))}</p>
      <p class=\"muted\">{_safe_text(report.get('risk_narrative'))}</p>
    </section>

    <section class=\"section\">
      <h2>Module Matrix</h2>
      <table><thead><tr><th>Module</th><th>Weight</th><th>Score</th><th>Risk</th><th>Assessed</th><th>Status</th></tr></thead><tbody>{''.join(matrix_rows)}</tbody></table>
    </section>

    <section class=\"section\">
      <h2>Priority Action Plan</h2>
      <ol>{''.join(priority_rows)}</ol>
    </section>

    <section class=\"section\">
      <h2>Top Findings</h2>
      <table><thead><tr><th>Severity</th><th>Module</th><th>Finding</th><th>Confidence</th><th>Recommendation</th></tr></thead><tbody>{''.join(findings_rows)}</tbody></table>
    </section>

    <section class=\"section\">
      <h2>Before Launch Checklist</h2>
      <ul>{checklist}</ul>
    </section>

    <section class=\"section\">
      <h2>Recommended Package</h2>
      <p><strong>{_safe_text(package.get('package'))}</strong></p>
      <p>{_safe_text(package.get('reason'))}</p>
    </section>

    <section class=\"section\">
      <h2>Limitations & Disclaimer</h2>
      <ul>{limitations}</ul>
      <p>{_safe_text(report.get('disclaimer'))}</p>
    </section>

    <section class=\"section\">
      <h2>Verification</h2>
      <p><strong>Report ID:</strong> {report_id}</p>
      <p><strong>Verification hash:</strong> <code>{report_hash}</code></p>
      <p><strong>Generated:</strong> {generated}</p>
      <p class=\"muted\">Public-safe wording: {PUBLIC_WORDING}. Do not use: {', '.join(BLOCKED_WORDING)}.</p>
    </section>

    <div class=\"footer\">Generated by {REPORT_BRAND}. This report is preliminary, AI/rule/checklist-assisted, and not a certified audit.</div>
  </main>
</body>
</html>"""


def _para(text: str, style: ParagraphStyle) -> Paragraph:
    return Paragraph(html.escape(text or ""), style)


def build_pdf_bytes(report: dict[str, Any]) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=42, leftMargin=42, topMargin=42, bottomMargin=42)
    styles = getSampleStyleSheet()
    title = ParagraphStyle("W3GTitle", parent=styles["Title"], fontSize=20, leading=24, spaceAfter=12, textColor=colors.HexColor("#0f172a"))
    h2 = ParagraphStyle("W3GH2", parent=styles["Heading2"], fontSize=13, leading=16, spaceBefore=14, spaceAfter=8, textColor=colors.HexColor("#0f172a"))
    normal = ParagraphStyle("W3GNormal", parent=styles["BodyText"], fontSize=9, leading=12, spaceAfter=6)
    small = ParagraphStyle("W3GSmall", parent=styles["BodyText"], fontSize=8, leading=10, textColor=colors.HexColor("#475569"))

    story: list[Any] = []
    story.append(_para(f"{REPORT_BRAND}", small))
    story.append(_para(f"Launch Readiness Report — {report.get('project_name', 'Web3 Project')}", title))
    story.append(_para(f"Report ID: {report.get('report_id', 'Not generated')}", normal))
    story.append(_para(f"Verification hash: {report.get('report_hash', 'Not available')}", small))
    story.append(_para(f"Score: {_score_value(report)} · Risk: {_risk_label(report)}", h2))
    story.append(_para(REAL_ONLY_NOTE, normal))
    story.append(Spacer(1, 0.12 * inch))

    story.append(_para("Executive Summary", h2))
    story.append(_para(str(report.get("executive_summary", "No executive summary provided.")), normal))
    story.append(_para(str(report.get("risk_narrative", "")), normal))

    story.append(_para("Module Matrix", h2))
    data = [["Module", "Weight", "Score", "Risk", "Status"]]
    for row in report.get("module_matrix", []) or []:
        data.append([
            str(row.get("label", row.get("module", ""))),
            f"{row.get('weight_percent', '')}%",
            "Not assessed" if row.get("score") is None else str(row.get("score")),
            str(row.get("risk_label", "")),
            str(row.get("status", "")),
        ])
    table = Table(data, colWidths=[1.55 * inch, 0.65 * inch, 0.75 * inch, 1.3 * inch, 1.4 * inch], repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("FONTSIZE", (0, 0), (-1, -1), 7),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
    ]))
    story.append(table)

    story.append(_para("Priority Action Plan", h2))
    priority = report.get("priority_action_plan", []) or []
    if priority:
        for item in priority[:12]:
            story.append(_para(f"{item.get('step')}. {str(item.get('severity', '')).upper()} — {item.get('title')}: {item.get('recommended_action')}", normal))
    else:
        story.append(_para("No priority actions found in assessed modules. Complete missing modules before launch decisions.", normal))

    story.append(_para("Top Findings", h2))
    findings = report.get("top_findings", []) or []
    if findings:
        for finding in findings[:12]:
            story.append(_para(f"{str(finding.get('severity', '')).upper()} · {finding.get('module')} · {finding.get('title')}", normal))
            story.append(_para(str(finding.get("recommendation", "")), small))
    else:
        story.append(_para("No findings were provided in this report object.", normal))

    story.append(_para("Limitations", h2))
    for item in report.get("limitations", []) or []:
        story.append(_para(f"• {item}", normal))
    story.append(_para("Disclaimer", h2))
    story.append(_para(str(report.get("disclaimer", "This is not a certified audit.")), normal))
    story.append(_para(f"Generated: {report.get('generated_at', _now().isoformat())}", small))

    doc.build(story)
    return buffer.getvalue()


def build_report_artifacts(report: dict[str, Any]) -> dict[str, Any]:
    html_preview = build_professional_html(report)
    pdf_bytes = build_pdf_bytes(report)
    return {
        "ok": True,
        "version": "1.0",
        "report_id": report.get("report_id"),
        "report_hash": report.get("report_hash"),
        "project_name": report.get("project_name"),
        "formats": {
            "professional_html": True,
            "server_pdf": True,
            "markdown": bool(report.get("markdown_report")),
            "json": True,
            "public_private_report_record": True,
        },
        "file_names": {
            "pdf": f"{report.get('report_id', 'web3guard-report')}.pdf",
            "html": f"{report.get('report_id', 'web3guard-report')}.html",
            "markdown": f"{report.get('report_id', 'web3guard-report')}.md",
            "json": f"{report.get('report_id', 'web3guard-report')}.json",
        },
        "html_preview": html_preview,
        "markdown_report": report.get("markdown_report", ""),
        "json_export": report.get("json_export") or report,
        "pdf_size_bytes": len(pdf_bytes),
        "delivery_policy": delivery_policy(),
        "real_only_note": REAL_ONLY_NOTE,
    }


def _read_public_reports() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in _public_reports_path().read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def _write_public_reports(rows: list[dict[str, Any]]) -> None:
    with _public_reports_path().open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")


def publish_report_record(report: dict[str, Any], visibility: str = "private", user_id: str | None = None, project_id: str | None = None) -> dict[str, Any]:
    if visibility not in {"public", "private"}:
        raise ValueError("visibility must be public or private")
    public_id = f"rpt_{uuid.uuid4().hex[:14]}"
    record = {
        "id": public_id,
        "created_at": _now().isoformat(),
        "visibility": visibility,
        "status": "active",
        "user_id": user_id,
        "project_id": project_id,
        "report_id": report.get("report_id"),
        "report_hash": report.get("report_hash"),
        "project_name": report.get("project_name"),
        "public_wording": PUBLIC_WORDING,
        "blocked_wording": BLOCKED_WORDING,
        "manual_review_claim_allowed": False,
        "report": report,
    }
    with _public_reports_path().open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")
    return record


def list_report_records(include_private: bool = False) -> list[dict[str, Any]]:
    records = _read_public_reports()
    if not include_private:
        records = [row for row in records if row.get("visibility") == "public"]
    return sorted(records, key=lambda row: row.get("created_at", ""), reverse=True)


def get_report_record(public_id: str, allow_private: bool = False) -> dict[str, Any] | None:
    for record in _read_public_reports():
        if record.get("id") == public_id:
            if record.get("visibility") == "private" and not allow_private:
                return None
            return record
    return None


def verify_report_record(public_id: str, report_hash: str) -> dict[str, Any]:
    record = get_report_record(public_id, allow_private=True)
    if not record:
        return {"ok": False, "verified": False, "reason": "Report record not found"}
    match = record.get("report_hash") == report_hash
    return {
        "ok": True,
        "verified": match,
        "report_id": record.get("report_id"),
        "public_id": public_id,
        "visibility": record.get("visibility"),
        "status": record.get("status"),
        "public_wording": record.get("public_wording"),
        "blocked_wording": record.get("blocked_wording"),
        "reason": "Hash matches published record" if match else "Hash does not match published record",
    }
