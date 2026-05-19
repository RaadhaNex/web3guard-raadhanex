from __future__ import annotations

import json
import secrets
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.core.config import settings
from app.services.database_store import list_projects, list_reports, list_scans

SENTINEL_REAL_ONLY_NOTE = (
    "Web3Guard Sentinel separates public vulnerability intelligence from Web3Guard project-specific findings. "
    "Indexed advisories are tracked/mapped from public or manually ingested sources; they are not claimed as vulnerabilities discovered by Web3Guard. "
    "Project alerts are generated only from stored projects, scans, reports, and ingested advisory records. No fake monitoring data is generated."
)

SENTINEL_DISCLOSURE_NOTE = (
    "Responsible disclosure drafts are templates only. They are not sent by Web3Guard automatically. "
    "Admins must validate scope, authorization, evidence quality, and contact method before any outreach."
)

SOURCE_CATALOG = [
    {
        "id": "nvd",
        "name": "NVD CVE API",
        "type": "public_vulnerability_database",
        "mode": "provider_ready",
        "status": "Manual / Provider Not Connected",
        "safe_wording": "CVE records indexed from NVD when ingestion is configured.",
        "unsafe_wording": "Discovered by Web3Guard",
        "requires_key": False,
        "official_endpoint_hint": "https://services.nvd.nist.gov/rest/json/cves/2.0",
    },
    {
        "id": "osv",
        "name": "OSV.dev",
        "type": "open_source_dependency_advisory",
        "mode": "provider_ready",
        "status": "Manual / Provider Not Connected",
        "safe_wording": "Open-source package advisories indexed from OSV when ingestion is configured.",
        "unsafe_wording": "Web3Guard found every vulnerable dependency without lockfile evidence",
        "requires_key": False,
        "official_endpoint_hint": "https://api.osv.dev/v1/querybatch",
    },
    {
        "id": "github_advisory",
        "name": "GitHub Advisory Database",
        "type": "open_source_dependency_advisory",
        "mode": "provider_ready",
        "status": "Needs GitHub token for higher limits" if not settings.github_api_token else "Configured",
        "safe_wording": "GitHub security advisories indexed when ingestion is configured.",
        "unsafe_wording": "Private repositories scanned without authorization",
        "requires_key": False,
        "official_endpoint_hint": "https://api.github.com/advisories",
    },
    {
        "id": "cisa_kev",
        "name": "CISA KEV Catalog",
        "type": "known_exploited_vulnerability",
        "mode": "provider_ready",
        "status": "Manual / Provider Not Connected",
        "safe_wording": "Known exploited vulnerabilities tracked when KEV ingestion is configured.",
        "unsafe_wording": "All exploited systems are verified compromised",
        "requires_key": False,
        "official_endpoint_hint": "https://www.cisa.gov/known-exploited-vulnerabilities-catalog",
    },
    {
        "id": "defillama_hacks",
        "name": "DeFiLlama Hacks Dataset",
        "type": "web3_incident_intelligence",
        "mode": "manual_or_provider_ready",
        "status": "Manual / Provider Not Connected",
        "safe_wording": "Historical Web3 incident patterns mapped to launch-readiness guidance.",
        "unsafe_wording": "Every project with a similar pattern is exploitable",
        "requires_key": False,
        "official_endpoint_hint": "https://defillama.com/hacks",
    },
    {
        "id": "openssf_scorecard",
        "name": "OpenSSF Scorecard",
        "type": "repository_posture_signal",
        "mode": "worker_ready",
        "status": "Tool Not Installed / Manual",
        "safe_wording": "Repository posture signals can be mapped when scorecard results are supplied.",
        "unsafe_wording": "Scorecard score proves project security",
        "requires_key": False,
        "official_endpoint_hint": "https://github.com/ossf/scorecard",
    },
    {
        "id": "goplus",
        "name": "GoPlus Risk Signals",
        "type": "token_wallet_risk_signal",
        "mode": "provider_ready",
        "status": "Configured" if settings.goplus_enabled else "Provider Not Configured",
        "safe_wording": "Token/wallet risk signals mapped when GoPlus is configured and read-only requests succeed.",
        "unsafe_wording": "Wallet is safe forever",
        "requires_key": bool(settings.goplus_access_token),
        "official_endpoint_hint": settings.goplus_api_base,
    },
    {
        "id": "etherscan",
        "name": "Etherscan-compatible Explorer",
        "type": "verified_contract_source_signal",
        "mode": "provider_ready",
        "status": "Configured" if settings.etherscan_api_key else "Needs API Key",
        "safe_wording": "Verified source and metadata can be fetched when explorer API key is configured.",
        "unsafe_wording": "Unverified contract is automatically malicious",
        "requires_key": True,
        "official_endpoint_hint": settings.etherscan_v2_api_base,
    },
]

RISK_PATTERNS = [
    {
        "id": "pattern_missing_security_policy",
        "type": "launch_readiness_pattern",
        "title": "Missing public security policy slows responsible disclosure",
        "severity": "medium",
        "tags": ["security.md", "security.txt", "disclosure", "github"],
        "mapped_to": ["github", "website", "bug_bounty"],
        "fix_direction": "Add SECURITY.md, security.txt, contact channel, scope, and response expectations.",
        "status": "educational_pattern_not_public_advisory",
    },
    {
        "id": "pattern_dependency_advisory_mapping",
        "type": "dependency_mapping_pattern",
        "title": "Dependency advisories should be mapped to project lockfiles before launch",
        "severity": "high",
        "tags": ["dependency", "lockfile", "osv", "github_advisory", "npm"],
        "mapped_to": ["github", "frontend", "api"],
        "fix_direction": "Run dependency audit, pin fixed versions, and keep lockfiles committed.",
        "status": "educational_pattern_not_public_advisory",
    },
    {
        "id": "pattern_admin_opsec_monitoring",
        "type": "admin_opsec_pattern",
        "title": "Admin keys and emergency powers need monitoring and evidence",
        "severity": "high",
        "tags": ["admin", "multisig", "timelock", "owner", "upgrade"],
        "mapped_to": ["admin_opsec", "contract", "permission_map"],
        "fix_direction": "Document multisig/timelock ownership, signer rotation, and emergency procedures.",
        "status": "educational_pattern_not_public_advisory",
    },
    {
        "id": "pattern_wallet_approval_monitoring",
        "type": "wallet_risk_pattern",
        "title": "Wallet approval and signature UX needs continuous review",
        "severity": "high",
        "tags": ["wallet", "approval", "spender", "permit", "signature"],
        "mapped_to": ["wallet", "dapp", "goplus"],
        "fix_direction": "Show spender, token, chain, amount, and signature purpose before wallet prompts.",
        "status": "educational_pattern_not_public_advisory",
    },
]


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _new_id(prefix: str) -> str:
    return f"{prefix}_{secrets.token_hex(10)}"


def _path(raw: str) -> Path:
    path = Path(raw)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text("", encoding="utf-8")
    return path


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            item = json.loads(line)
            if isinstance(item, dict):
                rows.append(item)
        except json.JSONDecodeError:
            continue
    return rows


def _append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")


def _advisory_path() -> Path:
    return _path(settings.sentinel_vulnerability_index_file)


def _matches_path() -> Path:
    return _path(settings.sentinel_matches_file)


def _alerts_path() -> Path:
    return _path(settings.sentinel_alerts_file)


def _disclosure_path() -> Path:
    return _path(settings.sentinel_disclosures_file)


def _read_advisories() -> list[dict[str, Any]]:
    rows = _read_jsonl(_advisory_path())
    rows.sort(key=lambda item: item.get("published_at") or item.get("created_at") or "", reverse=True)
    return rows


def _severity(value: Any) -> str:
    clean = str(value or "info").lower().strip()
    if clean in {"critical", "high", "medium", "low", "info"}:
        return clean
    if clean in {"moderate", "warning"}:
        return "medium"
    return "info"


def _normalise_tags(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).lower().strip() for item in value if str(item).strip()][:20]
    if isinstance(value, str):
        return [item.strip().lower() for item in value.split(",") if item.strip()][:20]
    return []


def _normalise_advisory(raw: dict[str, Any], source: str) -> dict[str, Any]:
    advisory_id = str(raw.get("id") or raw.get("cve") or raw.get("ghsa_id") or raw.get("osv_id") or raw.get("advisory_id") or _new_id("adv"))
    title = str(raw.get("title") or raw.get("summary") or raw.get("name") or advisory_id)[:240]
    package = raw.get("package") or raw.get("package_name") or raw.get("module")
    ecosystem = raw.get("ecosystem") or raw.get("package_ecosystem")
    cve = raw.get("cve") or raw.get("cve_id")
    aliases = raw.get("aliases") if isinstance(raw.get("aliases"), list) else []
    if cve and cve not in aliases:
        aliases.append(cve)
    row = {
        "id": advisory_id,
        "source": source,
        "source_kind": "public_or_manual_advisory",
        "title": title,
        "severity": _severity(raw.get("severity") or raw.get("cvss_severity") or raw.get("level")),
        "summary": str(raw.get("summary") or raw.get("description") or "")[:1200],
        "package": str(package)[:160] if package else None,
        "ecosystem": str(ecosystem)[:80] if ecosystem else None,
        "aliases": aliases[:12],
        "cwe": raw.get("cwe") or raw.get("cwes"),
        "published_at": raw.get("published_at") or raw.get("published") or raw.get("datePublished") or raw.get("created_at") or _now().isoformat(),
        "fixed_version": raw.get("fixed_version") or raw.get("patched_versions"),
        "affected_versions": raw.get("affected_versions") or raw.get("vulnerable_versions"),
        "source_url": raw.get("source_url") or raw.get("url") or raw.get("references"),
        "tags": sorted(set([*_normalise_tags(raw.get("tags")), *[str(x).lower() for x in aliases]]))[:30],
        "created_at": _now().isoformat(),
        "discovered_by_web3guard": False,
        "safe_counting_bucket": "indexed_public_advisory",
        "real_only_note": "This record is indexed/tracked. It is not claimed as a Web3Guard-discovered vulnerability.",
    }
    return row


def sentinel_status() -> dict[str, Any]:
    advisories = _read_advisories()
    matches = _read_jsonl(_matches_path())
    alerts = _read_jsonl(_alerts_path())
    disclosures = _read_jsonl(_disclosure_path())
    return {
        "ok": True,
        "phase": "Phase 15 - Web3Guard Sentinel Monitoring + Vulnerability Intelligence Core",
        "version": "1.0",
        "enabled": settings.sentinel_enabled,
        "live_ingestion_enabled": settings.sentinel_live_ingestion_enabled,
        "user_monitoring_enabled": settings.sentinel_user_monitoring_enabled,
        "admin_intelligence_enabled": settings.sentinel_admin_intelligence_enabled,
        "counts": {
            "indexed_public_advisories": len(advisories),
            "educational_risk_patterns": len(RISK_PATTERNS),
            "stored_matches": len(matches),
            "stored_alerts": len(alerts),
            "disclosure_drafts": len(disclosures),
        },
        "source_count": len(SOURCE_CATALOG),
        "real_only_note": SENTINEL_REAL_ONLY_NOTE,
        "public_stats_wording": {
            "safe": [
                "public vulnerabilities indexed",
                "risk mappings generated",
                "project-specific findings generated from stored scans",
                "responsible disclosure drafts prepared",
            ],
            "blocked": [
                "vulnerabilities discovered by Web3Guard unless verified as original findings",
                "company is hacked",
                "certified audit",
                "100% secure",
            ],
        },
    }


def sentinel_sources() -> dict[str, Any]:
    return {
        "ok": True,
        "sources": SOURCE_CATALOG,
        "real_only_note": "Sources are provider-ready or manual-ingestion ready. No source is claimed live until configured and successfully ingested.",
    }


def list_intelligence(source: str | None = None, severity: str | None = None, query: str | None = None, limit: int = 50) -> dict[str, Any]:
    rows = _read_advisories()
    if source:
        rows = [row for row in rows if str(row.get("source", "")).lower() == source.lower()]
    if severity:
        rows = [row for row in rows if str(row.get("severity", "")).lower() == severity.lower()]
    if query:
        q = query.lower()
        rows = [row for row in rows if q in json.dumps(row, ensure_ascii=False).lower()]
    rows = rows[: max(1, min(limit, settings.sentinel_max_intel_items))]
    by_source = Counter(str(row.get("source") or "unknown") for row in _read_advisories())
    by_severity = Counter(str(row.get("severity") or "info") for row in _read_advisories())
    return {
        "ok": True,
        "items": rows,
        "patterns": RISK_PATTERNS,
        "count": len(rows),
        "totals": {
            "indexed_public_advisories": len(_read_advisories()),
            "by_source": dict(by_source),
            "by_severity": dict(by_severity),
        },
        "real_only_note": SENTINEL_REAL_ONLY_NOTE,
    }


def ingest_intelligence(source: str, records: list[dict[str, Any]], real_only_acknowledged: bool, imported_by: str | None = None) -> dict[str, Any]:
    if not real_only_acknowledged:
        raise ValueError("Real-only acknowledgement is required")
    allowed = {item["id"] for item in SOURCE_CATALOG} | {"manual", "internal_research", "user_supplied"}
    if source not in allowed:
        raise ValueError(f"Unsupported source '{source}'. Use one of: {', '.join(sorted(allowed))}")
    if len(records) > settings.sentinel_max_ingest_records:
        raise ValueError(f"Too many records. Max {settings.sentinel_max_ingest_records} per request")
    existing_ids = {str(item.get("id")) for item in _read_advisories()}
    inserted: list[dict[str, Any]] = []
    skipped: list[str] = []
    for raw in records:
        if not isinstance(raw, dict):
            continue
        row = _normalise_advisory(raw, source)
        row["imported_by"] = imported_by or "manual_admin"
        if row["id"] in existing_ids:
            skipped.append(row["id"])
            continue
        _append_jsonl(_advisory_path(), row)
        existing_ids.add(row["id"])
        inserted.append(row)
    return {
        "ok": True,
        "inserted_count": len(inserted),
        "skipped_duplicate_count": len(skipped),
        "inserted": inserted,
        "skipped_duplicate_ids": skipped[:50],
        "safe_counting_note": "Inserted records are counted as indexed/tracked advisories, not Web3Guard-discovered vulnerabilities.",
    }


def _dump(value: Any) -> str:
    try:
        return json.dumps(value, ensure_ascii=False, default=str).lower()
    except Exception:
        return str(value).lower()


def _scan_payload(scan: Any) -> dict[str, Any]:
    payload = getattr(scan, "payload", None)
    return payload if isinstance(payload, dict) else {}


def _report_payload(report: Any) -> dict[str, Any]:
    payload = getattr(report, "payload", None)
    return payload if isinstance(payload, dict) else {}


def _alert(alert_type: str, severity: str, title: str, detail: str, project_id: str | None = None, href: str | None = None, evidence: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "id": _new_id("sentinel_alert"),
        "type": alert_type,
        "severity": _severity(severity),
        "title": title,
        "detail": detail,
        "project_id": project_id,
        "href": href,
        "evidence": evidence or {},
        "status": "open",
        "source": "derived_from_stored_records",
        "created_at": _now().isoformat(),
    }


def build_project_alerts(user_id: str, project_id: str | None = None) -> dict[str, Any]:
    projects = [p for p in list_projects(user_id, limit=100) if not project_id or p.id == project_id]
    scans = list_scans(user_id, limit=150, project_id=project_id)
    reports = list_reports(user_id, limit=150, project_id=project_id)
    advisories = _read_advisories()
    alerts: list[dict[str, Any]] = []

    if not projects:
        return {
            "ok": True,
            "user_id": user_id,
            "project_id": project_id,
            "alerts": [],
            "summary": {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0},
            "real_only_note": "No stored project records found for this user/project. Sentinel does not generate fake monitoring alerts.",
        }

    project_lookup = {p.id: p for p in projects}
    for project in projects:
        if not getattr(project, "website_url", None):
            alerts.append(_alert(
                "missing_project_website",
                "medium",
                "Project website URL missing",
                "Add a public website URL to enable website, security.txt, headers, and disclosure monitoring.",
                project.id,
                f"/dashboard/projects/{project.id}",
            ))

    for scan in scans:
        pid = getattr(scan, "project_id", None)
        if pid and pid not in project_lookup:
            continue
        score = getattr(scan, "score", None)
        critical_high = int(getattr(scan, "critical_high_count", 0) or 0)
        findings_count = int(getattr(scan, "findings_count", 0) or 0)
        if isinstance(score, int) and score < 40:
            alerts.append(_alert(
                "low_launch_confidence",
                "critical",
                f"Low launch confidence in {getattr(scan, 'module', 'scan')} scan",
                f"Stored scan score is {score}/100. Review findings and Not Assessed modules before launch.",
                pid,
                f"/dashboard/scans/{getattr(scan, 'id', '')}",
                {"scan_id": getattr(scan, "id", None), "score": score},
            ))
        if critical_high > 0:
            alerts.append(_alert(
                "critical_high_findings",
                "high",
                f"{critical_high} critical/high finding(s) in stored scan",
                f"Scan has {findings_count} total finding(s). Prioritize critical/high before public launch.",
                pid,
                f"/dashboard/scans/{getattr(scan, 'id', '')}",
                {"scan_id": getattr(scan, "id", None), "critical_high_count": critical_high, "findings_count": findings_count},
            ))

        payload_text = _dump(_scan_payload(scan))
        for advisory in advisories[:250]:
            tokens = [str(advisory.get("package") or "").lower(), *[str(x).lower() for x in advisory.get("aliases", [])], *[str(x).lower() for x in advisory.get("tags", [])]]
            tokens = [token for token in tokens if len(token) >= 4]
            if tokens and any(token in payload_text for token in tokens[:12]):
                alerts.append(_alert(
                    "advisory_match_candidate",
                    advisory.get("severity") or "medium",
                    f"Potential advisory match: {advisory.get('title')}",
                    "This is a candidate match from stored scan payload text. Confirm package/version/source evidence before notifying anyone.",
                    pid,
                    f"/dashboard/scans/{getattr(scan, 'id', '')}",
                    {"advisory_id": advisory.get("id"), "source": advisory.get("source"), "match_type": "candidate_text_match"},
                ))

    for report in reports:
        pid = getattr(report, "project_id", None)
        if pid and pid not in project_lookup:
            continue
        risk = str(getattr(report, "risk_label", "") or "").lower()
        if any(token in risk for token in ["critical", "high", "manual review", "evidence needed"]):
            alerts.append(_alert(
                "report_followup",
                "medium",
                "Saved report requires follow-up",
                f"Report risk label is '{getattr(report, 'risk_label', 'No risk label')}'. Review fix status and evidence before sharing publicly.",
                pid,
                f"/dashboard/reports/{getattr(report, 'id', '')}",
                {"report_id": getattr(report, "id", None)},
            ))
        payload_text = _dump(_report_payload(report))
        if "not assessed" in payload_text or "not_assessed" in payload_text:
            alerts.append(_alert(
                "not_assessed_modules",
                "medium",
                "Report includes Not Assessed modules",
                "Complete missing evidence before using the report as launch-readiness proof.",
                pid,
                f"/dashboard/reports/{getattr(report, 'id', '')}",
                {"report_id": getattr(report, "id", None)},
            ))

    alerts.sort(key=lambda item: ({"critical": 5, "high": 4, "medium": 3, "low": 2, "info": 1}.get(item["severity"], 0), item["created_at"]), reverse=True)
    summary = Counter(alert["severity"] for alert in alerts)
    return {
        "ok": True,
        "user_id": user_id,
        "project_id": project_id,
        "project_count": len(projects),
        "scan_count": len(scans),
        "report_count": len(reports),
        "alerts": alerts[: settings.sentinel_max_alerts],
        "summary": {key: summary.get(key, 0) for key in ["critical", "high", "medium", "low", "info"]},
        "real_only_note": SENTINEL_REAL_ONLY_NOTE,
    }


def admin_overview(user_id: str | None = None) -> dict[str, Any]:
    demo_user = user_id or settings.local_demo_user_id
    projects = list_projects(demo_user, limit=200)
    scans = list_scans(demo_user, limit=200)
    reports = list_reports(demo_user, limit=200)
    advisories = _read_advisories()
    source_counter = Counter(str(row.get("source") or "unknown") for row in advisories)
    severity_counter = Counter(str(row.get("severity") or "info") for row in advisories)
    project_alerts = build_project_alerts(demo_user)
    return {
        "ok": True,
        "mode": "admin_intelligence_overview",
        "scope_note": "This overview uses stored records for the supplied user/local demo user. Production admin analytics should connect to Supabase role-based views before broad use.",
        "counts": {
            "projects_observed": len(projects),
            "scans_observed": len(scans),
            "reports_observed": len(reports),
            "indexed_public_advisories": len(advisories),
            "educational_patterns": len(RISK_PATTERNS),
            "open_project_alerts": len(project_alerts.get("alerts", [])),
        },
        "advisories_by_source": dict(source_counter),
        "advisories_by_severity": dict(severity_counter),
        "project_alert_summary": project_alerts.get("summary", {}),
        "source_catalog": SOURCE_CATALOG,
        "safe_public_stats": {
            "indexed_public_advisories": len(advisories),
            "educational_patterns_mapped": len(RISK_PATTERNS),
            "project_specific_alerts_generated_from_stored_records": len(project_alerts.get("alerts", [])),
        },
        "blocked_stats_wording": [
            "Do not say 'vulnerabilities discovered by Web3Guard' for public/indexed advisories.",
            "Do not claim companies are hacked from candidate matches.",
            "Do not claim certified audit or 100% secure.",
        ],
        "real_only_note": SENTINEL_REAL_ONLY_NOTE,
    }


def disclosure_draft(payload: dict[str, Any]) -> dict[str, Any]:
    if not payload.get("real_only_acknowledged"):
        raise ValueError("Real-only acknowledgement is required")
    target = str(payload.get("target") or "Project security contact").strip()[:160]
    finding = str(payload.get("finding_summary") or "Public security misconfiguration or vulnerability signal").strip()[:700]
    evidence = str(payload.get("evidence_summary") or "Passive/authorized evidence collected by Web3Guard Sentinel").strip()[:700]
    confidence = str(payload.get("confidence") or "needs_manual_validation").strip()[:80]
    contact = str(payload.get("contact") or "security contact listed by the project").strip()[:180]
    draft = f"""Subject: Responsible disclosure: potential Web3 launch-readiness security issue\n\nHello {target},\n\nWe are contacting you through a responsible disclosure workflow. Web3Guard Sentinel observed a potential security or launch-readiness issue that may affect your public Web3 project.\n\nFinding summary:\n{finding}\n\nEvidence summary:\n{evidence}\n\nConfidence level:\n{confidence}\n\nImportant boundaries:\n- No exploit attempt was performed.\n- No private key, seed phrase, wallet signing, or user funds interaction was requested.\n- This is not a certified audit report or a claim that your project is compromised.\n- Please validate the issue with your internal security team before taking action.\n\nSuggested next step:\nReply with the correct security contact or disclosure process if this message reached the wrong channel.\n\nContact used for draft: {contact}\n\nRegards,\nWeb3Guard AI by RAADHANEX\nPre-audit readiness and responsible disclosure support\n""".strip()
    row = {
        "id": _new_id("disclosure"),
        "created_at": _now().isoformat(),
        "target": target,
        "finding_summary": finding,
        "evidence_summary": evidence,
        "confidence": confidence,
        "contact": contact,
        "status": "draft_only_not_sent",
        "draft": draft,
        "real_only_note": SENTINEL_DISCLOSURE_NOTE,
    }
    _append_jsonl(_disclosure_path(), row)
    return {"ok": True, "draft": row, "real_only_note": SENTINEL_DISCLOSURE_NOTE}
