from __future__ import annotations

import re
from collections import Counter, defaultdict
from typing import Any, Iterable

from app.models.schemas import Finding

SEVERITY_RANK = {"info": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}
CONFIDENCE_RANK = {"low": 0, "medium": 1, "high": 2}

_TOOL_ALIASES = (
    ("slither", "slither"),
    ("semgrep", "semgrep"),
    ("aderyn", "aderyn"),
    ("explorer", "explorer"),
    ("etherscan", "explorer"),
    ("github", "github"),
    ("solidity rule", "web3guard_local_rules"),
    ("rule engine", "web3guard_local_rules"),
    ("static analysis", "static_analysis_runner"),
)


def _norm_text(value: str | None) -> str:
    return re.sub(r"[^a-z0-9]+", "-", (value or "").lower()).strip("-")[:120]


def _norm_path(value: str | None) -> str:
    return (value or "").replace("\\", "/").strip().lower()


def _tool_from_source(source: str | None, fallback: str | None = None) -> str:
    raw = (source or "").lower()
    for needle, tool in _TOOL_ALIASES:
        if needle in raw:
            return tool
    return fallback or "web3guard_scanner"


def _unique(values: Iterable[str | None]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for value in values:
        if not value:
            continue
        clean = str(value).strip()
        if not clean or clean in seen:
            continue
        seen.add(clean)
        out.append(clean)
    return out


def ensure_professional_finding(finding: Finding, *, default_source_tool: str | None = None) -> Finding:
    """Attach report-ready fields without inventing a vulnerability.

    This function only mirrors already-observed evidence, impact and fix data into
    normalized fields expected by professional reports. It never creates a new
    severity or finding.
    """
    tool = _tool_from_source(getattr(finding, "source", None), default_source_tool)
    existing_tools = list(getattr(finding, "source_tools", []) or [])
    source_tools = _unique(existing_tools + [tool])
    category = getattr(finding, "category", "general") or "general"
    evidence = getattr(finding, "evidence", None) or getattr(finding, "affected_code", None)
    if not evidence:
        evidence = (getattr(finding, "description", "") or "")[:420]
    impact = getattr(finding, "impact", None) or getattr(finding, "business_impact", None)
    fix = getattr(finding, "fix", None) or getattr(finding, "recommendation", None)
    line = getattr(finding, "affected_line", None)
    file_path = getattr(finding, "affected_file", None)
    repro_steps = list(getattr(finding, "repro_steps", []) or [])
    if not repro_steps:
        if file_path and line:
            repro_steps.append(f"Open {file_path} around line {line} and verify the cited evidence.")
        elif line:
            repro_steps.append(f"Review the submitted source around line {line} and verify the cited evidence.")
        else:
            repro_steps.append("Review the cited evidence and confirm whether the issue applies in project context.")
    if category == "tool_status":
        verification_status = "status_only"
        remediation_priority = "informational"
    elif any(t in source_tools for t in ("slither", "semgrep", "aderyn")):
        verification_status = "tool_detected_needs_triage"
        remediation_priority = "fix_before_launch" if finding.severity in {"critical", "high"} else "review_before_launch"
    else:
        verification_status = "rule_detected_needs_triage"
        remediation_priority = "fix_before_launch" if finding.severity in {"critical", "high"} else "review_before_launch"
    exploitability = "high" if finding.severity in {"critical", "high"} else "medium" if finding.severity == "medium" else "low"
    update = {
        "evidence": evidence,
        "impact": impact,
        "fix": fix,
        "source_tools": source_tools,
        "repro_steps": repro_steps,
        "verification_status": verification_status,
        "exploitability": exploitability,
        "remediation_priority": remediation_priority,
        "merged_from": list(getattr(finding, "merged_from", []) or []) or [getattr(finding, "id", "finding")],
        "occurrence_count": int(getattr(finding, "occurrence_count", 1) or 1),
    }
    return finding.model_copy(update=update)


def _dedupe_key(finding: Finding) -> tuple[Any, ...]:
    category = _norm_text(getattr(finding, "category", None) or "general")
    module = getattr(finding, "module", "unknown")
    path = _norm_path(getattr(finding, "affected_file", None))
    line = getattr(finding, "affected_line", None)
    title = _norm_text(getattr(finding, "title", None))
    rule = _norm_text(getattr(finding, "rule_id", None))
    if category == "tool-status":
        return ("status", rule, title, path, line)
    if path or line:
        # This merges the same issue confirmed by multiple tools at the same location.
        return (module, category, path, line or 0)
    if rule:
        return (module, category, rule)
    return (module, category, title)


def _best_finding(items: list[Finding]) -> Finding:
    return max(
        items,
        key=lambda f: (
            SEVERITY_RANK.get(str(f.severity), 0),
            CONFIDENCE_RANK.get(str(getattr(f, "confidence", "medium")), 1),
            len(getattr(f, "evidence", "") or ""),
        ),
    )


def merge_duplicate_findings(findings: list[Finding], *, default_source_tool: str | None = None) -> list[Finding]:
    normalized = [ensure_professional_finding(f, default_source_tool=default_source_tool) for f in findings]
    groups: dict[tuple[Any, ...], list[Finding]] = defaultdict(list)
    for finding in normalized:
        groups[_dedupe_key(finding)].append(finding)

    merged: list[Finding] = []
    for items in groups.values():
        if len(items) == 1:
            merged.append(items[0])
            continue
        best = _best_finding(items)
        source_tools = _unique(tool for item in items for tool in (getattr(item, "source_tools", []) or []))
        merged_from = _unique(value for item in items for value in (getattr(item, "merged_from", []) or [getattr(item, "id", "finding")]))
        references = _unique(ref for item in items for ref in (getattr(item, "references", []) or []))
        evidence_parts = _unique(getattr(item, "evidence", None) for item in items)
        repro_steps = _unique(step for item in items for step in (getattr(item, "repro_steps", []) or []))
        title = best.title
        if len(source_tools) > 1 and "Confirmed by" not in title:
            title = f"{best.title} (confirmed by {', '.join(source_tools[:4])})"
        description = best.description
        if len(items) > 1:
            description = f"{best.description}\n\nMerged evidence from {len(items)} scanner signal(s): {', '.join(source_tools)}."
        update = {
            "title": title,
            "description": description[:3000],
            "source_tools": source_tools,
            "merged_from": merged_from,
            "occurrence_count": len(items),
            "references": references,
            "evidence": "\n---\n".join(evidence_parts[:4])[:2500] if evidence_parts else getattr(best, "evidence", None),
            "repro_steps": repro_steps[:8],
            "verification_status": "multi_tool_detected_needs_triage" if len(source_tools) > 1 else getattr(best, "verification_status", "unreviewed"),
            "fingerprint": getattr(best, "fingerprint", None) or _norm_text("|".join(merged_from)),
        }
        merged.append(best.model_copy(update=update))

    merged.sort(key=lambda f: (SEVERITY_RANK.get(str(f.severity), 0), CONFIDENCE_RANK.get(str(getattr(f, "confidence", "medium")), 0)), reverse=True)
    return merged


def prepare_professional_findings(findings: list[Finding], *, default_source_tool: str | None = None) -> list[Finding]:
    real = [f for f in findings if getattr(f, "category", "") != "tool_status"]
    status = [ensure_professional_finding(f, default_source_tool=default_source_tool) for f in findings if getattr(f, "category", "") == "tool_status"]
    return merge_duplicate_findings(real, default_source_tool=default_source_tool) + status


def audit_grade_summary(findings: list[Finding], *, tool_runs: dict[str, Any] | None = None) -> dict[str, Any]:
    real_findings = [f for f in findings if getattr(f, "category", "") != "tool_status"]
    status_findings = [f for f in findings if getattr(f, "category", "") == "tool_status"]
    source_tool_counts = Counter(tool for f in real_findings for tool in (getattr(f, "source_tools", []) or []))
    with_locations = [f for f in real_findings if getattr(f, "affected_file", None) or getattr(f, "affected_line", None)]
    multi_tool = [f for f in real_findings if len(getattr(f, "source_tools", []) or []) > 1]
    severity_counts = Counter(str(f.severity) for f in real_findings)
    return {
        "report_ready": True,
        "real_findings_count": len(real_findings),
        "status_message_count": len(status_findings),
        "with_file_or_line_count": len(with_locations),
        "multi_tool_confirmed_count": len(multi_tool),
        "source_tool_counts": dict(source_tool_counts),
        "severity_counts": dict(severity_counts),
        "dedupe_policy": "merge by module/category/file/line or rule identity; tool status never becomes a vulnerability",
        "tool_runs": tool_runs or {},
        "required_human_step": "Manual triage is still required before any certified-audit or security-guarantee wording.",
    }
