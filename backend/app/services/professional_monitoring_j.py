from __future__ import annotations

import hashlib
import json
import secrets
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.core.config import settings

PHASE_J_NOTE = (
    "Professional Scanner Phase J adds post-review drift detection and continuous assurance baselines. "
    "It stores fingerprints of user-provided scan/proof/repo/contract evidence, compares later snapshots, "
    "and creates evidence-only drift events. It does not perform unauthorized active scanning, exploit automation, "
    "wallet signing, or fake monitoring. Network/provider checks remain opt-in through existing monitoring settings."
)

SEVERITY_ORDER = {"critical": 5, "high": 4, "medium": 3, "low": 2, "info": 1}
DRIFT_SEVERITY = {
    "contract_address_changed": "critical",
    "chain_changed": "high",
    "proxy_implementation_changed": "critical",
    "admin_owner_changed": "critical",
    "upgradeability_changed": "high",
    "source_hash_changed": "high",
    "report_integrity_changed": "high",
    "security_header_removed": "high",
    "cors_became_wildcard": "high",
    "public_exposure_added": "high",
    "score_dropped": "medium",
    "github_commit_changed": "medium",
    "solidity_fingerprint_changed": "medium",
    "dependency_fingerprint_changed": "medium",
    "workflow_fingerprint_changed": "low",
    "website_url_changed": "low",
    "finding_count_increased": "medium",
    "critical_high_count_increased": "high",
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{secrets.token_hex(10)}"


def _path(raw: str) -> Path:
    path = Path(raw)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text("", encoding="utf-8")
    return path


def _read(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
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


def _append(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")


def _rewrite(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")


def _baselines_file() -> Path:
    return _path(getattr(settings, "professional_monitoring_baselines_file", "app/data/db/professional_monitoring_baselines.jsonl"))


def _events_file() -> Path:
    return _path(getattr(settings, "professional_monitoring_events_file", "app/data/db/professional_monitoring_events.jsonl"))


def _runs_file() -> Path:
    return _path(getattr(settings, "professional_monitoring_runs_file", "app/data/db/professional_monitoring_runs.jsonl"))


def _hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def _safe_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _severity(value: str | None) -> str:
    clean = str(value or "info").strip().lower()
    return clean if clean in SEVERITY_ORDER else "info"


def _highest(severities: list[str]) -> str:
    if not severities:
        return "info"
    return max((_severity(item) for item in severities), key=lambda item: SEVERITY_ORDER.get(item, 0))


def _finding_key(item: dict[str, Any]) -> str:
    parts = [
        item.get("rule_id"),
        item.get("title"),
        item.get("severity"),
        item.get("affected_file"),
        item.get("affected_line"),
    ]
    return _hash([part for part in parts if part is not None])[:24]


def _finding_summary(scan_result: dict[str, Any]) -> dict[str, Any]:
    raw_findings = scan_result.get("findings") or scan_result.get("all_findings") or []
    if not isinstance(raw_findings, list):
        raw_findings = []
    findings = [item for item in raw_findings if isinstance(item, dict)]
    severities = [_severity(str(item.get("severity", "info"))) for item in findings]
    counts = Counter(severities)
    high_or_critical = counts.get("critical", 0) + counts.get("high", 0)
    return {
        "total": len(findings),
        "by_severity": dict(counts),
        "critical_high": high_or_critical,
        "keys_hash": _hash(sorted(_finding_key(item) for item in findings))[:32],
    }


def _website_fingerprint(evidence: dict[str, Any]) -> dict[str, Any]:
    website = evidence.get("website") if isinstance(evidence.get("website"), dict) else {}
    scan_result = evidence.get("scan_result") if isinstance(evidence.get("scan_result"), dict) else {}
    surface = scan_result.get("website_scan") if isinstance(scan_result.get("website_scan"), dict) else {}
    headers = {}
    for source in (website, surface, scan_result):
        candidate = source.get("headers") or source.get("security_headers") or source.get("observed_headers")
        if isinstance(candidate, dict):
            headers.update({str(k).lower(): bool(v) if isinstance(v, bool) else str(v) for k, v in candidate.items()})
    public_exposures = []
    for source in (website, surface, scan_result):
        candidate = source.get("public_exposures") or source.get("exposures") or source.get("proof_based_exposures")
        if isinstance(candidate, list):
            public_exposures.extend(str(item) for item in candidate[:100])
    url = _safe_str(website.get("url") or surface.get("url") or scan_result.get("url") or evidence.get("website_url"))
    score = website.get("score") or surface.get("score") or scan_result.get("score") or scan_result.get("website_score")
    cors = website.get("cors") or surface.get("cors") or scan_result.get("cors")
    csp_present = bool(headers.get("content-security-policy") or headers.get("csp"))
    hsts_present = bool(headers.get("strict-transport-security") or headers.get("hsts"))
    frame_present = bool(headers.get("x-frame-options") or headers.get("frame-ancestors"))
    return {
        "url": url,
        "score": score if isinstance(score, int | float) else None,
        "headers": {
            "content-security-policy": csp_present,
            "strict-transport-security": hsts_present,
            "x-frame-options": frame_present,
        },
        "cors": str(cors).lower() if cors is not None else None,
        "public_exposures_hash": _hash(sorted(set(public_exposures)))[:32],
        "public_exposures_count": len(set(public_exposures)),
        "fingerprint_hash": _hash({"url": url, "headers": headers, "cors": cors, "public_exposures": sorted(set(public_exposures)), "score": score})[:32],
    }


def _contract_fingerprint(evidence: dict[str, Any]) -> dict[str, Any]:
    contract = evidence.get("contract") if isinstance(evidence.get("contract"), dict) else {}
    scan_result = evidence.get("scan_result") if isinstance(evidence.get("scan_result"), dict) else {}
    contract_scan = scan_result.get("contract_scan") if isinstance(scan_result.get("contract_scan"), dict) else {}
    source = _safe_str(contract.get("source") or contract_scan.get("source") or evidence.get("solidity_source"))
    source_hash = contract.get("source_hash") or contract_scan.get("source_hash") or (_hash(source)[:32] if source else None)
    return {
        "chain": _safe_str(contract.get("chain") or contract_scan.get("chain") or evidence.get("chain")),
        "contract_address": (_safe_str(contract.get("contract_address") or contract_scan.get("contract_address") or evidence.get("contract_address")) or "").lower() or None,
        "source_hash": source_hash,
        "proxy_implementation": (_safe_str(contract.get("proxy_implementation") or contract.get("implementation_address") or contract_scan.get("proxy_implementation")) or "").lower() or None,
        "admin_owner": (_safe_str(contract.get("admin_owner") or contract.get("owner") or contract_scan.get("owner")) or "").lower() or None,
        "upgradeability": _safe_str(contract.get("upgradeability") or contract_scan.get("upgradeability")),
        "fingerprint_hash": _hash(contract or contract_scan or {"source_hash": source_hash})[:32],
    }


def _github_fingerprint(evidence: dict[str, Any]) -> dict[str, Any]:
    github = evidence.get("github") if isinstance(evidence.get("github"), dict) else {}
    scan_result = evidence.get("scan_result") if isinstance(evidence.get("scan_result"), dict) else {}
    repo_scan = scan_result.get("github_repo_scan") if isinstance(scan_result.get("github_repo_scan"), dict) else {}
    files = github.get("files") or repo_scan.get("files") or []
    if not isinstance(files, list):
        files = []
    sol_hashes: list[str] = []
    dep_hashes: list[str] = []
    workflow_hashes: list[str] = []
    for item in files:
        if not isinstance(item, dict):
            continue
        path = str(item.get("path") or item.get("name") or "").lower()
        content_hash = str(item.get("sha") or item.get("hash") or _hash(item.get("content", ""))[:24])
        if path.endswith(".sol"):
            sol_hashes.append(f"{path}:{content_hash}")
        if any(path.endswith(name) for name in ("package.json", "package-lock.json", "pnpm-lock.yaml", "yarn.lock", "requirements.txt")):
            dep_hashes.append(f"{path}:{content_hash}")
        if ".github/workflows" in path:
            workflow_hashes.append(f"{path}:{content_hash}")
    return {
        "repo_url": _safe_str(github.get("repo_url") or repo_scan.get("repo_url") or evidence.get("github_repo_url")),
        "commit_hash": _safe_str(github.get("commit_hash") or github.get("head_sha") or repo_scan.get("commit_hash")),
        "solidity_fingerprint": _hash(sorted(sol_hashes))[:32] if sol_hashes else _safe_str(github.get("solidity_fingerprint") or repo_scan.get("solidity_fingerprint")),
        "dependency_fingerprint": _hash(sorted(dep_hashes))[:32] if dep_hashes else _safe_str(github.get("dependency_fingerprint") or repo_scan.get("dependency_fingerprint")),
        "workflow_fingerprint": _hash(sorted(workflow_hashes))[:32] if workflow_hashes else _safe_str(github.get("workflow_fingerprint") or repo_scan.get("workflow_fingerprint")),
        "file_counts": {"solidity": len(sol_hashes), "dependency": len(dep_hashes), "workflow": len(workflow_hashes)},
        "fingerprint_hash": _hash(github or repo_scan)[:32],
    }


def _report_fingerprint(evidence: dict[str, Any]) -> dict[str, Any]:
    report = evidence.get("report") if isinstance(evidence.get("report"), dict) else {}
    proof = evidence.get("proof_report") if isinstance(evidence.get("proof_report"), dict) else {}
    return {
        "report_hash": _safe_str(report.get("report_hash") or proof.get("report_hash") or evidence.get("report_hash")),
        "integrity_hash": _safe_str(report.get("integrity_hash") or proof.get("integrity_hash") or evidence.get("integrity_hash")),
        "proof_id": _safe_str(proof.get("proof_id") or proof.get("id") or evidence.get("proof_id")),
        "approval_status": _safe_str(report.get("approval_status") or proof.get("approval_status")),
        "fingerprint_hash": _hash({"report": report, "proof": proof})[:32],
    }


def build_monitoring_fingerprint(evidence: dict[str, Any]) -> dict[str, Any]:
    evidence = evidence or {}
    scan_result = evidence.get("scan_result") if isinstance(evidence.get("scan_result"), dict) else {}
    fingerprint = {
        "website": _website_fingerprint(evidence),
        "contract": _contract_fingerprint(evidence),
        "github": _github_fingerprint(evidence),
        "report": _report_fingerprint(evidence),
        "findings": _finding_summary(scan_result if scan_result else evidence),
    }
    fingerprint["fingerprint_hash"] = _hash(fingerprint)[:40]
    return fingerprint


def _event(baseline: dict[str, Any], drift_type: str, title: str, description: str, before: Any, after: Any, severity: str | None = None) -> dict[str, Any]:
    return {
        "id": _id("pmjdrift"),
        "created_at": _now(),
        "baseline_id": baseline.get("id"),
        "user_id": baseline.get("user_id"),
        "project_id": baseline.get("project_id"),
        "project_name": baseline.get("project_name"),
        "drift_type": drift_type,
        "severity": _severity(severity or DRIFT_SEVERITY.get(drift_type, "info")),
        "title": title,
        "description": description,
        "before": before,
        "after": after,
        "status": "open",
        "recommended_action": _recommended_action(drift_type),
        "real_only_note": PHASE_J_NOTE,
    }


def _recommended_action(drift_type: str) -> str:
    actions = {
        "contract_address_changed": "Freeze public proof status until the new contract scope is reviewed.",
        "proxy_implementation_changed": "Run a new contract scan and require reviewer fix/upgrade verification before launch claims.",
        "admin_owner_changed": "Verify governance/admin transfer evidence and update report scope.",
        "security_header_removed": "Re-run website readiness and restore the removed security header before publishing proof.",
        "public_exposure_added": "Review exposed path/file evidence and remove sensitive public assets.",
        "cors_became_wildcard": "Restrict CORS origins and re-run API/website checks.",
        "github_commit_changed": "Run GitHub and contract scans on the new commit hash.",
        "score_dropped": "Review new findings and run fix verification before marking status clean.",
        "finding_count_increased": "Triaging new findings is required before approval stays valid.",
        "critical_high_count_increased": "Block public readiness claims until high/critical findings are triaged.",
    }
    return actions.get(drift_type, "Review the new snapshot evidence and decide whether a re-scan or manual reviewer confirmation is required.")


def compare_fingerprints(baseline: dict[str, Any], current: dict[str, Any]) -> list[dict[str, Any]]:
    base = baseline.get("fingerprint") or {}
    events: list[dict[str, Any]] = []
    b_web, c_web = base.get("website") or {}, current.get("website") or {}
    b_contract, c_contract = base.get("contract") or {}, current.get("contract") or {}
    b_github, c_github = base.get("github") or {}, current.get("github") or {}
    b_report, c_report = base.get("report") or {}, current.get("report") or {}
    b_findings, c_findings = base.get("findings") or {}, current.get("findings") or {}

    def changed(path: str, before: Any, after: Any) -> bool:
        before_missing = before is None or before == "" or before == {}
        after_missing = after is None or after == "" or after == {}
        return (not before_missing) and (not after_missing) and before != after

    if changed("website.url", b_web.get("url"), c_web.get("url")):
        events.append(_event(baseline, "website_url_changed", "Website URL changed", "The monitored website URL differs from the approved baseline.", b_web.get("url"), c_web.get("url")))

    for header_key in ("content-security-policy", "strict-transport-security", "x-frame-options"):
        if b_web.get("headers", {}).get(header_key) is True and c_web.get("headers", {}).get(header_key) is False:
            events.append(_event(baseline, "security_header_removed", f"Security header removed: {header_key}", "A security header present in the baseline is missing in the current snapshot.", True, False, "high"))

    if b_web.get("cors") not in {"*", "wildcard", "true"} and c_web.get("cors") in {"*", "wildcard", "true", "access-control-allow-origin:*"}:
        events.append(_event(baseline, "cors_became_wildcard", "CORS policy became wildcard", "The current snapshot indicates a wildcard CORS-like signal compared with a stricter baseline.", b_web.get("cors"), c_web.get("cors"), "high"))

    if (c_web.get("public_exposures_count") or 0) > (b_web.get("public_exposures_count") or 0):
        events.append(_event(baseline, "public_exposure_added", "Public exposure count increased", "The current snapshot has more public exposure signals than the baseline.", b_web.get("public_exposures_count"), c_web.get("public_exposures_count"), "high"))

    if isinstance(b_web.get("score"), (int, float)) and isinstance(c_web.get("score"), (int, float)) and (b_web["score"] - c_web["score"]) >= 10:
        events.append(_event(baseline, "score_dropped", "Readiness score dropped", "The current score is at least 10 points lower than the baseline.", b_web.get("score"), c_web.get("score"), "medium"))

    if changed("contract.chain", b_contract.get("chain"), c_contract.get("chain")):
        events.append(_event(baseline, "chain_changed", "Contract chain changed", "The chain in current evidence differs from the approved baseline.", b_contract.get("chain"), c_contract.get("chain"), "high"))
    if changed("contract.address", b_contract.get("contract_address"), c_contract.get("contract_address")):
        events.append(_event(baseline, "contract_address_changed", "Contract address changed", "The contract address differs from the approved baseline scope.", b_contract.get("contract_address"), c_contract.get("contract_address"), "critical"))
    if changed("contract.proxy", b_contract.get("proxy_implementation"), c_contract.get("proxy_implementation")):
        events.append(_event(baseline, "proxy_implementation_changed", "Proxy implementation changed", "The proxy implementation differs from the approved baseline.", b_contract.get("proxy_implementation"), c_contract.get("proxy_implementation"), "critical"))
    if changed("contract.owner", b_contract.get("admin_owner"), c_contract.get("admin_owner")):
        events.append(_event(baseline, "admin_owner_changed", "Admin/owner changed", "The privileged admin/owner signal differs from the approved baseline.", b_contract.get("admin_owner"), c_contract.get("admin_owner"), "critical"))
    if changed("contract.upgradeability", b_contract.get("upgradeability"), c_contract.get("upgradeability")):
        events.append(_event(baseline, "upgradeability_changed", "Upgradeability signal changed", "The upgradeability/proxy signal changed compared with the baseline.", b_contract.get("upgradeability"), c_contract.get("upgradeability"), "high"))
    if changed("contract.source_hash", b_contract.get("source_hash"), c_contract.get("source_hash")):
        events.append(_event(baseline, "source_hash_changed", "Contract source fingerprint changed", "The Solidity/source hash differs from the approved baseline evidence.", b_contract.get("source_hash"), c_contract.get("source_hash"), "high"))

    if changed("github.commit", b_github.get("commit_hash"), c_github.get("commit_hash")):
        events.append(_event(baseline, "github_commit_changed", "GitHub commit changed", "The current GitHub commit differs from the baseline. Run a new scan on the new commit.", b_github.get("commit_hash"), c_github.get("commit_hash"), "medium"))
    for key, drift_type, title in (
        ("solidity_fingerprint", "solidity_fingerprint_changed", "Solidity file fingerprint changed"),
        ("dependency_fingerprint", "dependency_fingerprint_changed", "Dependency fingerprint changed"),
        ("workflow_fingerprint", "workflow_fingerprint_changed", "GitHub workflow fingerprint changed"),
    ):
        if changed(f"github.{key}", b_github.get(key), c_github.get(key)):
            events.append(_event(baseline, drift_type, title, "The current GitHub evidence differs from the approved baseline.", b_github.get(key), c_github.get(key)))

    if changed("report.integrity_hash", b_report.get("integrity_hash"), c_report.get("integrity_hash")):
        events.append(_event(baseline, "report_integrity_changed", "Report integrity hash changed", "The public proof/report integrity hash changed compared with the baseline.", b_report.get("integrity_hash"), c_report.get("integrity_hash"), "high"))

    if (c_findings.get("total") or 0) > (b_findings.get("total") or 0):
        events.append(_event(baseline, "finding_count_increased", "Finding count increased", "Current scan has more findings than the baseline.", b_findings.get("total"), c_findings.get("total"), "medium"))
    if (c_findings.get("critical_high") or 0) > (b_findings.get("critical_high") or 0):
        events.append(_event(baseline, "critical_high_count_increased", "High/Critical finding count increased", "Current scan has more high/critical findings than the baseline.", b_findings.get("critical_high"), c_findings.get("critical_high"), "high"))

    # Do not store duplicates from a single comparison pass.
    unique: dict[str, dict[str, Any]] = {}
    for event in events:
        key = _hash([event.get("drift_type"), event.get("before"), event.get("after")])[:32]
        unique[key] = event
    return list(unique.values())


def create_baseline(payload: Any) -> dict[str, Any]:
    if not bool(getattr(payload, "authorization_confirmed", False)):
        raise ValueError("Authorization confirmation is required before creating a monitoring baseline")
    if not bool(getattr(payload, "real_only_acknowledged", True)):
        raise ValueError("Real-only acknowledgement is required")
    evidence = getattr(payload, "baseline_evidence", None) or {}
    if not isinstance(evidence, dict):
        raise ValueError("baseline_evidence must be a JSON object")
    fingerprint = build_monitoring_fingerprint(evidence)
    now = _now()
    row = {
        "id": _id("pmjbase"),
        "created_at": now,
        "updated_at": now,
        "status": "active",
        "user_id": getattr(payload, "user_id", None) or settings.local_demo_user_id,
        "project_id": getattr(payload, "project_id", None),
        "project_name": getattr(payload, "project_name", None) or "Monitored project",
        "baseline_type": getattr(payload, "baseline_type", None) or "post_review",
        "cadence": getattr(payload, "cadence", None) or "manual",
        "approved_report_id": getattr(payload, "approved_report_id", None),
        "proof_id": getattr(payload, "proof_id", None),
        "scope": getattr(payload, "scope", None) or {},
        "fingerprint": fingerprint,
        "fingerprint_hash": fingerprint.get("fingerprint_hash"),
        "authorization_confirmed": bool(getattr(payload, "authorization_confirmed", False)),
        "real_only_acknowledged": bool(getattr(payload, "real_only_acknowledged", True)),
        "real_only_note": PHASE_J_NOTE,
    }
    _append(_baselines_file(), row)
    return row


def list_baselines(user_id: str | None = None, status: str | None = None) -> list[dict[str, Any]]:
    rows = _read(_baselines_file())
    if user_id:
        rows = [item for item in rows if item.get("user_id") == user_id]
    if status:
        rows = [item for item in rows if item.get("status") == status]
    rows.sort(key=lambda item: item.get("created_at", ""), reverse=True)
    return rows


def get_baseline(baseline_id: str, user_id: str | None = None) -> dict[str, Any] | None:
    for row in list_baselines(user_id=user_id):
        if row.get("id") == baseline_id:
            return row
    return None


def compare_to_baseline(payload: Any) -> dict[str, Any]:
    baseline_id = getattr(payload, "baseline_id", None)
    baseline = get_baseline(baseline_id, user_id=getattr(payload, "user_id", None))
    if not baseline:
        raise ValueError("Professional monitoring baseline not found")
    if baseline.get("status") != "active":
        raise ValueError("Professional monitoring baseline is not active")
    if not bool(getattr(payload, "real_only_acknowledged", True)):
        raise ValueError("Real-only acknowledgement is required")
    evidence = getattr(payload, "current_evidence", None) or {}
    if not isinstance(evidence, dict):
        raise ValueError("current_evidence must be a JSON object")
    current = build_monitoring_fingerprint(evidence)
    events = compare_fingerprints(baseline, current)
    stored_events = []
    for event in events:
        _append(_events_file(), event)
        stored_events.append(event)
    highest = _highest([item.get("severity", "info") for item in events])
    now = _now()
    run = {
        "id": _id("pmjrun"),
        "created_at": now,
        "baseline_id": baseline_id,
        "user_id": baseline.get("user_id"),
        "project_id": baseline.get("project_id"),
        "baseline_hash": baseline.get("fingerprint_hash"),
        "current_hash": current.get("fingerprint_hash"),
        "drift_detected": bool(events),
        "drift_count": len(events),
        "highest_severity": highest,
        "events_stored": len(stored_events),
        "current_fingerprint": current,
        "real_only_note": PHASE_J_NOTE,
    }
    _append(_runs_file(), run)
    baselines = _read(_baselines_file())
    for row in baselines:
        if row.get("id") == baseline_id:
            row["updated_at"] = now
            row["last_compared_at"] = now
            row["last_drift_count"] = len(events)
            row["last_highest_severity"] = highest
            break
    _rewrite(_baselines_file(), baselines)
    return {
        "ok": True,
        "baseline_id": baseline_id,
        "baseline_hash": baseline.get("fingerprint_hash"),
        "current_hash": current.get("fingerprint_hash"),
        "drift_detected": bool(events),
        "drift_count": len(events),
        "highest_severity": highest,
        "events": stored_events,
        "run": run,
        "real_only_note": PHASE_J_NOTE,
    }


def list_events(user_id: str | None = None, baseline_id: str | None = None, status: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
    rows = _read(_events_file())
    if user_id:
        rows = [item for item in rows if item.get("user_id") == user_id]
    if baseline_id:
        rows = [item for item in rows if item.get("baseline_id") == baseline_id]
    if status:
        rows = [item for item in rows if item.get("status") == status]
    rows.sort(key=lambda item: item.get("created_at", ""), reverse=True)
    return rows[: max(1, min(limit, 250))]


def acknowledge_event(event_id: str, status: str = "acknowledged", reviewer: str | None = None, note: str | None = None) -> dict[str, Any]:
    clean = status.strip().lower()
    if clean not in {"acknowledged", "resolved", "accepted_risk", "false_positive", "open"}:
        raise ValueError("Unsupported event status")
    rows = _read(_events_file())
    found = None
    for row in rows:
        if row.get("id") == event_id:
            row["status"] = clean
            row["reviewer"] = reviewer
            row["review_note"] = note
            row["updated_at"] = _now()
            found = row
            break
    if not found:
        raise ValueError("Professional monitoring drift event not found")
    _rewrite(_events_file(), rows)
    return found


def status() -> dict[str, Any]:
    baselines = _read(_baselines_file())
    events = _read(_events_file())
    runs = _read(_runs_file())
    severity_counts = Counter(_severity(str(item.get("severity"))) for item in events if item.get("status", "open") == "open")
    return {
        "ok": True,
        "phase": "Professional Scanner Phase J - Continuous Assurance & Drift Detection",
        "enabled": True,
        "baseline_count": len(baselines),
        "event_count": len(events),
        "run_count": len(runs),
        "open_events_by_severity": dict(severity_counts),
        "supported_drift_types": sorted(DRIFT_SEVERITY.keys()),
        "checks": [
            "website security header drift",
            "public exposure count drift",
            "contract address/source/proxy/admin drift",
            "GitHub commit/dependency/workflow drift",
            "report integrity drift",
            "finding count and high/critical drift",
        ],
        "public_claim_status": "continuous assurance support only; not a certified audit guarantee",
        "real_only_note": PHASE_J_NOTE,
    }


def readiness() -> dict[str, Any]:
    stat = status()
    open_events = [item for item in _read(_events_file()) if item.get("status", "open") == "open"]
    high_or_critical = [item for item in open_events if _severity(str(item.get("severity"))) in {"critical", "high"}]
    return {
        "ok": True,
        "direct_competition_capability": "post_audit_continuous_assurance_layer_added",
        "market_claim_allowed": False,
        "why_not_yet": [
            "Requires real customer projects monitored over time.",
            "Requires human reviewer sign-off for drift events.",
            "Requires production scheduler/webhooks and external chain/GitHub/provider confirmations.",
            "Still must avoid certified audit or guaranteed safety claims.",
        ],
        "ready_layers": [
            "audit-grade finding engine foundation",
            "formal/fuzz artifact parser",
            "proof report approval gate",
            "human review/fix verification workflow",
            "benchmark and rule tuning system",
            "external validation and consensus workflow",
            "continuous assurance drift detection baseline",
        ],
        "open_high_or_critical_drift_events": len(high_or_critical),
        "status": stat,
        "real_only_note": PHASE_J_NOTE,
    }
