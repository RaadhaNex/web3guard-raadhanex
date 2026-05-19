from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

TRUST_METRICS_VERSION = "web3guard-trust-metrics-engine-v29.0"
TRUST_METRICS_NOTE = (
    "Trust Metrics Engine stores real owner-entered metrics, advisory mappings, and disclosure lifecycle records only. "
    "It separates external advisory records, Web3Guard-generated findings, community review items, and disclosures. "
    "It must not imply certified audit status, 100% security, or that Web3Guard discovered a vulnerability unless a real Web3Guard finding record exists."
)
SAFE_PUBLIC_WORDING = (
    "Public metrics are transparency indicators for launch readiness. They are not an audit score, not a certified audit, "
    "not a guarantee of safety, and not proof that every issue has been found."
)

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data" / "db"
SNAPSHOT_FILE = DATA_DIR / "trust_metric_snapshots.jsonl"
ADVISORY_MAP_FILE = DATA_DIR / "trust_metric_advisory_mappings.jsonl"
DISCLOSURE_FILE = DATA_DIR / "trust_metric_disclosures.jsonl"

SAFE_MISSING_LABELS = {"Tool Not Installed", "Provider Not Configured", "Needs API Key", "Manual", "Not Assessed"}
SEVERITIES = {"critical", "high", "medium", "low", "informational", "unknown"}
ADVISORY_SOURCES = {"osv", "nvd", "github_advisory", "cisa_kev", "manual", "other"}
MAPPING_STATUSES = {"mapped", "needs_review", "not_affected", "affected", "resolved", "watching"}
DISCLOSURE_STATUSES = {
    "draft",
    "sent_manually",
    "acknowledged",
    "triaged",
    "fix_in_progress",
    "resolved",
    "closed",
    "not_applicable",
}
DISCLOSURE_ORIGINS = {
    "external_advisory",
    "web3guard_generated_finding",
    "owner_reported",
    "community_review",
    "manual",
}

BLOCKED_PUBLIC_CLAIMS = [
    "certified audit",
    "certified auditor",
    "100% secure",
    "100 percent secure",
    "fully secure",
    "guaranteed secure",
    "exploit proof",
    "hack proof",
    "audited by web3guard",
    "web3guard audited",
    "verified auditor",
    "official audit by web3guard",
    "discovered by web3guard",
    "found by web3guard",
    "we discovered",
    "we found this vulnerability",
]
CVE_RE = re.compile(r"CVE-\d{4}-\d{4,}", re.IGNORECASE)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_json(value: Any) -> str:
    try:
        return json.dumps(value, sort_keys=True, default=str, ensure_ascii=False)
    except Exception:
        return str(value)


def _id(prefix: str, payload: Any) -> str:
    digest = hashlib.sha256(f"{_now()}::{_safe_json(payload)}".encode("utf-8")).hexdigest()[:16]
    return f"{prefix}_{digest}"


def _ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            value = json.loads(line)
            if isinstance(value, dict):
                rows.append(value)
        except json.JSONDecodeError:
            continue
    return rows


def _append_jsonl(path: Path, record: dict[str, Any]) -> None:
    _ensure_parent(path)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True, default=str) + "\n")


def _compact_text(value: Any, limit: int = 1200) -> str:
    return str(value or "").strip()[:limit]


def _compact_list(value: Any, *, limit: int = 20, item_limit: int = 220) -> list[str]:
    if not isinstance(value, list):
        return []
    items: list[str] = []
    seen: set[str] = set()
    for raw in value:
        item = str(raw or "").strip()[:item_limit]
        if not item or item.lower() in seen:
            continue
        seen.add(item.lower())
        items.append(item)
        if len(items) >= limit:
            break
    return items


def _safe_int(value: Any, default: int = 0, max_value: int = 1_000_000) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return default
    return max(0, min(number, max_value))


def _normalize_choice(value: Any, allowed: set[str], default: str) -> str:
    candidate = str(value or default).strip().lower().replace(" ", "_")
    return candidate if candidate in allowed else default


def _contains_blocked_claim(*values: Any) -> str | None:
    joined = "\n".join(str(value or "") for value in values).lower()
    for claim in BLOCKED_PUBLIC_CLAIMS:
        if claim in joined:
            return claim
    return None


def _safe_owner_filter(rows: list[dict[str, Any]], owner_user_id: str | None, organization_id: str | None = None) -> list[dict[str, Any]]:
    owner = str(owner_user_id or "local-demo-user").strip()
    org = str(organization_id or "").strip() or None
    filtered = [row for row in rows if row.get("owner_user_id") == owner]
    if org:
        filtered = [row for row in filtered if row.get("organization_id") == org]
    return sorted(filtered, key=lambda row: str(row.get("created_at") or ""), reverse=True)


def trust_metrics_status() -> dict[str, Any]:
    surfaces = [
        {
            "key": "metric_snapshots",
            "name": "Owner-entered trust metric snapshots",
            "status": "Ready",
            "endpoint": "/trust-metrics/snapshots",
            "stores": ["external advisory count", "Web3Guard-generated finding count", "community review count", "disclosure count"],
            "not_claimed": ["No fake score", "No fake monitoring", "No certified audit claim"],
        },
        {
            "key": "advisory_project_mapping",
            "name": "Advisory-to-project mapping ledger",
            "status": "Ready",
            "endpoint": "/trust-metrics/advisory-mappings",
            "stores": ["source", "advisory id", "severity", "affected component", "mapping status"],
            "not_claimed": ["No upstream advisory mutation", "No automatic disclosure claim", "No fake CVE creation"],
        },
        {
            "key": "disclosure_lifecycle",
            "name": "Responsible disclosure lifecycle",
            "status": "Ready",
            "endpoint": "/trust-metrics/disclosures",
            "stores": ["origin", "status", "manual recipient", "public reference", "timeline notes"],
            "not_claimed": ["No auto-send", "No exploit automation", "No proof-of-exploit generation"],
        },
        {
            "key": "public_safe_summary",
            "name": "Public-safe trust metrics summary",
            "status": "Ready",
            "endpoint": "/trust-metrics/public-summary",
            "stores": ["separate counts", "safe labels", "not-audit disclaimer"],
            "not_claimed": ["No discovered-by-us claim unless record origin is explicit", "No 100% secure claim"],
        },
    ]
    return {
        "ok": True,
        "version": TRUST_METRICS_VERSION,
        "readiness_label": "Trust metrics engine ready for real owner-entered records",
        "surfaces": surfaces,
        "safe_public_wording": SAFE_PUBLIC_WORDING,
        "real_only_note": TRUST_METRICS_NOTE,
        "safe_missing_labels": sorted(SAFE_MISSING_LABELS),
        "safety_boundaries": {
            "no_fake_score": True,
            "no_fake_public_metrics": True,
            "no_fake_monitoring": True,
            "not_certified_audit": True,
            "no_100_percent_secure_claim": True,
            "no_private_key_collection": True,
            "no_wallet_signing": True,
            "no_exploit_automation": True,
        },
    }


def check_public_wording(text: str) -> dict[str, Any]:
    blocked = _contains_blocked_claim(text)
    cves = sorted(set(match.upper() for match in CVE_RE.findall(text or "")))
    return {
        "ok": True,
        "safe": blocked is None,
        "blocked_claim": blocked,
        "detected_cves": cves,
        "safe_rewrite_hint": None if blocked is None else SAFE_PUBLIC_WORDING,
        "real_only_note": TRUST_METRICS_NOTE,
    }


def create_metric_snapshot(payload: dict[str, Any]) -> dict[str, Any]:
    if not payload.get("safe_public_metrics_acknowledged"):
        raise ValueError("safe_public_metrics_acknowledged must be true before saving public metrics")
    project_id = _compact_text(payload.get("project_id"), 160)
    project_name = _compact_text(payload.get("project_name"), 180)
    if len(project_id) < 2 and len(project_name) < 2:
        raise ValueError("project_id or project_name is required")
    note = _compact_text(payload.get("public_metric_note"), 1000)
    blocked = _contains_blocked_claim(project_name, note)
    if blocked:
        raise ValueError(f"Blocked unsafe public claim detected: {blocked}")
    web3guard_generated = _safe_int(payload.get("web3guard_generated_finding_count"))
    external_advisories = _safe_int(payload.get("external_advisory_count"))
    community_reviews = _safe_int(payload.get("community_review_count"))
    disclosures = _safe_int(payload.get("disclosure_count"))
    resolved = min(_safe_int(payload.get("resolved_disclosure_count")), disclosures)
    record = {
        "id": _id("tms", payload),
        "owner_user_id": _compact_text(payload.get("owner_user_id") or "local-demo-user", 160),
        "organization_id": _compact_text(payload.get("organization_id"), 160) or None,
        "project_id": project_id or None,
        "project_name": project_name or None,
        "report_hash": _compact_text(payload.get("report_hash"), 160) or None,
        "external_advisory_count": external_advisories,
        "web3guard_generated_finding_count": web3guard_generated,
        "community_review_count": community_reviews,
        "disclosure_count": disclosures,
        "resolved_disclosure_count": resolved,
        "unresolved_disclosure_count": max(disclosures - resolved, 0),
        "public_metric_note": note or SAFE_PUBLIC_WORDING,
        "metric_sources": _compact_list(payload.get("metric_sources"), limit=12),
        "created_at": _now(),
        "updated_at": _now(),
        "safe_public_metrics_acknowledged": True,
        "not_audit_disclaimer": SAFE_PUBLIC_WORDING,
    }
    _append_jsonl(SNAPSHOT_FILE, record)
    return {"ok": True, "snapshot": record, "real_only_note": TRUST_METRICS_NOTE}


def list_metric_snapshots(owner_user_id: str, organization_id: str | None = None, project_id: str | None = None, limit: int = 100) -> dict[str, Any]:
    rows = _safe_owner_filter(_read_jsonl(SNAPSHOT_FILE), owner_user_id, organization_id)
    if project_id:
        rows = [row for row in rows if row.get("project_id") == project_id]
    rows = rows[:limit]
    return {"ok": True, "snapshots": rows, "count": len(rows), "real_only_note": TRUST_METRICS_NOTE}


def create_advisory_mapping(payload: dict[str, Any]) -> dict[str, Any]:
    if not payload.get("authorization_confirmed"):
        raise ValueError("authorization_confirmed must be true before mapping an advisory to a project")
    project_id = _compact_text(payload.get("project_id"), 160)
    advisory_id = _compact_text(payload.get("advisory_id"), 180)
    if len(project_id) < 2:
        raise ValueError("project_id is required")
    if len(advisory_id) < 2:
        raise ValueError("advisory_id is required")
    notes = _compact_text(payload.get("notes"), 1400)
    blocked = _contains_blocked_claim(payload.get("advisory_title"), notes)
    if blocked:
        raise ValueError(f"Blocked unsafe public claim detected: {blocked}")
    record = {
        "id": _id("tma", payload),
        "owner_user_id": _compact_text(payload.get("owner_user_id") or "local-demo-user", 160),
        "organization_id": _compact_text(payload.get("organization_id"), 160) or None,
        "project_id": project_id,
        "project_name": _compact_text(payload.get("project_name"), 180) or None,
        "advisory_source": _normalize_choice(payload.get("advisory_source"), ADVISORY_SOURCES, "manual"),
        "advisory_id": advisory_id,
        "advisory_title": _compact_text(payload.get("advisory_title"), 240) or None,
        "severity": _normalize_choice(payload.get("severity"), SEVERITIES, "unknown"),
        "affected_component": _compact_text(payload.get("affected_component"), 240) or None,
        "mapping_status": _normalize_choice(payload.get("mapping_status"), MAPPING_STATUSES, "needs_review"),
        "evidence_links": _compact_list(payload.get("evidence_links"), limit=10, item_limit=500),
        "notes": notes,
        "authorization_confirmed": True,
        "created_at": _now(),
        "updated_at": _now(),
        "not_claimed": [
            "This mapping does not create or modify upstream advisory records.",
            "This mapping does not claim Web3Guard discovered the advisory.",
            "This mapping is not a certified audit result.",
        ],
    }
    _append_jsonl(ADVISORY_MAP_FILE, record)
    return {"ok": True, "mapping": record, "real_only_note": TRUST_METRICS_NOTE}


def list_advisory_mappings(owner_user_id: str, organization_id: str | None = None, project_id: str | None = None, limit: int = 100) -> dict[str, Any]:
    rows = _safe_owner_filter(_read_jsonl(ADVISORY_MAP_FILE), owner_user_id, organization_id)
    if project_id:
        rows = [row for row in rows if row.get("project_id") == project_id]
    rows = rows[:limit]
    return {"ok": True, "advisory_mappings": rows, "count": len(rows), "real_only_note": TRUST_METRICS_NOTE}


def create_disclosure_record(payload: dict[str, Any]) -> dict[str, Any]:
    if not payload.get("authorization_confirmed"):
        raise ValueError("authorization_confirmed must be true before saving a disclosure record")
    if not payload.get("manual_send_acknowledged"):
        raise ValueError("manual_send_acknowledged must be true. Web3Guard does not auto-send disclosures in Phase 29")
    project_id = _compact_text(payload.get("project_id"), 160)
    title = _compact_text(payload.get("title"), 240)
    if len(project_id) < 2:
        raise ValueError("project_id is required")
    if len(title) < 3:
        raise ValueError("title is required")
    summary = _compact_text(payload.get("summary"), 2500)
    blocked = _contains_blocked_claim(title, summary, payload.get("public_reference"), payload.get("timeline_notes"))
    if blocked:
        raise ValueError(f"Blocked unsafe public claim detected: {blocked}")
    origin = _normalize_choice(payload.get("origin"), DISCLOSURE_ORIGINS, "manual")
    record = {
        "id": _id("tmd", payload),
        "owner_user_id": _compact_text(payload.get("owner_user_id") or "local-demo-user", 160),
        "organization_id": _compact_text(payload.get("organization_id"), 160) or None,
        "project_id": project_id,
        "project_name": _compact_text(payload.get("project_name"), 180) or None,
        "origin": origin,
        "related_mapping_id": _compact_text(payload.get("related_mapping_id"), 160) or None,
        "title": title,
        "severity": _normalize_choice(payload.get("severity"), SEVERITIES, "unknown"),
        "status": _normalize_choice(payload.get("status"), DISCLOSURE_STATUSES, "draft"),
        "recipient": _compact_text(payload.get("recipient"), 240) or None,
        "public_reference": _compact_text(payload.get("public_reference"), 500) or None,
        "summary": summary,
        "timeline_notes": _compact_text(payload.get("timeline_notes"), 2000),
        "evidence_links": _compact_list(payload.get("evidence_links"), limit=10, item_limit=500),
        "authorization_confirmed": True,
        "manual_send_acknowledged": True,
        "created_at": _now(),
        "updated_at": _now(),
        "not_claimed": [
            "This is a manually tracked disclosure lifecycle record.",
            "Web3Guard did not auto-send this disclosure.",
            "This record is not proof of exploit and not a certified audit claim.",
        ],
    }
    _append_jsonl(DISCLOSURE_FILE, record)
    return {"ok": True, "disclosure": record, "real_only_note": TRUST_METRICS_NOTE}


def list_disclosures(owner_user_id: str, organization_id: str | None = None, project_id: str | None = None, status: str | None = None, limit: int = 100) -> dict[str, Any]:
    rows = _safe_owner_filter(_read_jsonl(DISCLOSURE_FILE), owner_user_id, organization_id)
    if project_id:
        rows = [row for row in rows if row.get("project_id") == project_id]
    if status:
        wanted = _normalize_choice(status, DISCLOSURE_STATUSES, status)
        rows = [row for row in rows if row.get("status") == wanted]
    rows = rows[:limit]
    return {"ok": True, "disclosures": rows, "count": len(rows), "real_only_note": TRUST_METRICS_NOTE}


def public_summary(owner_user_id: str, organization_id: str | None = None, project_id: str | None = None) -> dict[str, Any]:
    snapshots = list_metric_snapshots(owner_user_id, organization_id, project_id, limit=1000)["snapshots"]
    mappings = list_advisory_mappings(owner_user_id, organization_id, project_id, limit=1000)["advisory_mappings"]
    disclosures = list_disclosures(owner_user_id, organization_id, project_id, limit=1000)["disclosures"]
    latest_snapshot = snapshots[0] if snapshots else None
    disclosure_status_counts: dict[str, int] = {}
    origin_counts: dict[str, int] = {}
    for row in disclosures:
        status = str(row.get("status") or "unknown")
        origin = str(row.get("origin") or "unknown")
        disclosure_status_counts[status] = disclosure_status_counts.get(status, 0) + 1
        origin_counts[origin] = origin_counts.get(origin, 0) + 1
    severity_counts: dict[str, int] = {}
    for row in mappings:
        severity = str(row.get("severity") or "unknown")
        severity_counts[severity] = severity_counts.get(severity, 0) + 1
    web3guard_finding_count = sum(1 for row in disclosures if row.get("origin") == "web3guard_generated_finding")
    if latest_snapshot:
        web3guard_finding_count = max(web3guard_finding_count, _safe_int(latest_snapshot.get("web3guard_generated_finding_count")))
    summary = {
        "snapshot_count": len(snapshots),
        "advisory_mapping_count": len(mappings),
        "disclosure_count": len(disclosures),
        "external_advisory_mapping_count": len([row for row in mappings if row.get("advisory_source") in {"osv", "nvd", "github_advisory", "cisa_kev"}]),
        "web3guard_generated_finding_count": web3guard_finding_count,
        "community_review_count": _safe_int(latest_snapshot.get("community_review_count")) if latest_snapshot else 0,
        "resolved_disclosure_count": len([row for row in disclosures if row.get("status") in {"resolved", "closed", "not_applicable"}]),
        "open_disclosure_count": len([row for row in disclosures if row.get("status") not in {"resolved", "closed", "not_applicable"}]),
        "disclosure_status_counts": disclosure_status_counts,
        "disclosure_origin_counts": origin_counts,
        "advisory_severity_counts": severity_counts,
    }
    return {
        "ok": True,
        "version": TRUST_METRICS_VERSION,
        "project_id": project_id,
        "latest_snapshot": latest_snapshot,
        "metrics": summary,
        "safe_public_wording": SAFE_PUBLIC_WORDING,
        "real_only_note": TRUST_METRICS_NOTE,
        "not_claimed": [
            "Not a certified audit score.",
            "Not a guarantee that the project is safe.",
            "Not a claim that Web3Guard discovered external advisory records.",
            "No fake monitoring, fake score, or fake trust badge was generated.",
        ],
    }
