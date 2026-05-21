from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.core.config import settings
from app.services.mega_phase_e_store import append_jsonl, new_id, now_iso, read_jsonl, rewrite_jsonl, sort_created, storage_path
from app.services import professional_monitoring_j as monitoring
from app.services import professional_direct_level_k as direct_level
from app.services import public_proof_report

REAL_ONLY_NOTE = (
    "Phase N-S keeps direct-level work evidence-first: no certified-audit claim, no 100% secure claim, "
    "no private key/seed collection, no wallet signing, and no exploit automation. Missing providers/tools return "
    "Not Assessed / Provider Not Configured / Tool Not Installed."
)

BLOCKED_PUBLIC_CLAIMS = {
    "certified audit",
    "100% secure",
    "guaranteed secure",
    "all vulnerabilities found",
    "exploit-proof",
    "insurance guaranteed",
    "replaces certik",
    "replaces openzeppelin",
    "replaces hacken",
}

ALLOWED_REVIEWER_STATUSES = {"invited", "applied", "screening", "approved", "rejected", "suspended"}
ALLOWED_DELIVERY_STATUSES = {"draft", "sent", "client_viewed", "accepted", "revision_requested", "revoked"}
ALLOWED_WORKER_TYPES = {"foundry", "echidna"}
SAFE_WORKER_EXTENSIONS = {".sol", ".toml", ".json", ".yaml", ".yml", ".txt", ".md"}
PRIVATE_KEY_PATTERNS = [
    re.compile(r"\bprivate[_-]?key\b\s*[:=]\s*[0-9a-fA-Fx]{24,}"),
    re.compile(r"\bmnemonic\b\s*[:=]"),
    re.compile(r"\bseed\s+phrase\b\s*[:=]", re.I),
]


def _path(raw: str) -> Path:
    return storage_path(raw)


def _read(raw: str) -> list[dict[str, Any]]:
    return read_jsonl(_path(raw))


def _append(raw: str, row: dict[str, Any]) -> None:
    append_jsonl(_path(raw), row)


def _rewrite(raw: str, rows: list[dict[str, Any]]) -> None:
    rewrite_jsonl(_path(raw), rows)


def _sha(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, default=str).encode("utf-8")).hexdigest()


def _safe_text(value: Any, limit: int = 1800) -> str:
    text = "" if value is None else str(value)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:limit]


def _has_blocked_claims(value: Any) -> list[str]:
    text = json.dumps(value, ensure_ascii=False, default=str).lower()
    # Allow explicit disclaimers such as "not a certified audit" while still blocking affirmative claims.
    for safe_phrase in [
        "not a certified audit",
        "not certified audit",
        "not a guarantee of safety",
        "does not guarantee safety",
        "no certified-audit claim",
        "no certified audit claim",
    ]:
        text = text.replace(safe_phrase, "")
    return sorted([claim for claim in BLOCKED_PUBLIC_CLAIMS if claim in text])


def _count_status(rows: list[dict[str, Any]], key: str = "status") -> dict[str, int]:
    return dict(Counter(_safe_text(row.get(key) or "unknown", 80) for row in rows))


def _tool_state(enabled: bool, binary: str | None) -> dict[str, Any]:
    installed = bool(binary and shutil.which(binary)) or bool(binary and Path(str(binary)).exists())
    if not enabled:
        state = "Provider Not Configured"
    elif not binary:
        state = "Tool Not Installed"
    elif not installed:
        state = "Tool Not Installed"
    else:
        state = "Ready"
    return {"enabled": bool(enabled), "binary": binary, "installed": installed, "state": state}


def phase_status() -> dict[str, Any]:
    reviewers = _read(settings.professional_reviewer_profiles_file)
    deliveries = _read(settings.professional_client_deliveries_file)
    worker_runs = _read(settings.professional_worker_runs_file)
    direct_gate = direct_level.direct_competition_readiness_gate()
    return {
        "ok": True,
        "phase_range": "N-S",
        "name": "Operational Direct-Level Console",
        "certified_audit": False,
        "direct_competition_public_claim_allowed": False,
        "real_only_note": REAL_ONLY_NOTE,
        "modules": {
            "phase_n_monitoring_dashboard_ui": True,
            "phase_o_github_webhook_setup_ui": True,
            "phase_p_onchain_provider_setup_ui": True,
            "phase_q_foundry_echidna_runner_backend": True,
            "phase_r_reviewer_onboarding_backend_ui": True,
            "phase_s_client_delivery_backend_ui": True,
        },
        "counts": {
            "reviewers": len(reviewers),
            "deliveries": len(deliveries),
            "worker_runs": len(worker_runs),
        },
        "worker_tools": worker_tool_status(),
        "direct_level_gate": {
            "readiness_score": direct_gate.get("readiness_score"),
            "gate_label": direct_gate.get("gate_label"),
            "blockers": direct_gate.get("blockers", []),
            "warnings": direct_gate.get("warnings", []),
        },
        "blocked_claims": sorted(BLOCKED_PUBLIC_CLAIMS),
    }


def monitoring_dashboard() -> dict[str, Any]:
    baselines = monitoring.list_baselines()
    open_events = monitoring.list_events(status="open", limit=250)
    acknowledged_events = monitoring.list_events(status="acknowledged", limit=250)
    resolved_events = monitoring.list_events(status="resolved", limit=250)
    readiness = monitoring.readiness()
    return {
        "ok": True,
        "phase": "N",
        "name": "Monitoring Dashboard Summary",
        "status": monitoring.status(),
        "readiness": readiness,
        "baselines": baselines[:50],
        "events": {
            "open": open_events[:50],
            "acknowledged": acknowledged_events[:25],
            "resolved": resolved_events[:25],
        },
        "counters": {
            "baselines": len(baselines),
            "open_events": len(open_events),
            "acknowledged_events": len(acknowledged_events),
            "resolved_events": len(resolved_events),
        },
        "real_only_note": REAL_ONLY_NOTE,
    }


def github_webhook_setup_status() -> dict[str, Any]:
    events = direct_level.list_webhook_events(source="github", limit=25).get("events", [])
    backend = str(getattr(settings, "backend_url", "http://localhost:8000")).rstrip("/")
    return {
        "ok": True,
        "phase": "O",
        "name": "GitHub Webhook Setup",
        "configured": bool(getattr(settings, "github_webhook_secret", None)),
        "webhook_url": f"{backend}/professional-direct-level/webhooks/github",
        "event_suggestions": ["push", "pull_request", "release", "workflow_run"],
        "secret_required": True,
        "signature_header": "X-Hub-Signature-256",
        "recent_events": events,
        "setup_steps": [
            "Open GitHub repo Settings → Webhooks → Add webhook.",
            "Payload URL: use webhook_url from this response.",
            "Content type: application/json.",
            "Secret: set the same value in GITHUB_WEBHOOK_SECRET on Render.",
            "Select push, pull_request, release, and workflow_run events.",
            "Send a test delivery and verify it appears in recent_events.",
        ],
        "real_only_note": "Webhook events are stored as evidence only. They do not prove safety or certified audit status.",
    }


def onchain_webhook_setup_status() -> dict[str, Any]:
    events = direct_level.list_webhook_events(source="onchain", limit=25).get("events", [])
    backend = str(getattr(settings, "backend_url", "http://localhost:8000")).rstrip("/")
    rpc_configured = any(bool(getattr(settings, name, None)) for name in [
        "ethereum_rpc_url", "polygon_rpc_url", "bsc_rpc_url", "arbitrum_rpc_url", "optimism_rpc_url", "base_rpc_url", "avalanche_rpc_url"
    ])
    return {
        "ok": True,
        "phase": "P",
        "name": "On-chain Provider Webhook Setup",
        "configured": bool(getattr(settings, "onchain_webhook_secret", None)) or rpc_configured,
        "webhook_url": f"{backend}/professional-direct-level/webhooks/onchain",
        "secret_required": True,
        "signature_header": "X-Web3Guard-Signature",
        "rpc_configured": rpc_configured,
        "recent_events": events,
        "provider_examples": ["Tenderly alert webhook", "Alchemy Notify webhook", "OpenZeppelin Defender Monitor webhook", "Blocknative webhook"],
        "tracked_event_types": ["owner_changed", "admin_changed", "proxy_upgraded", "implementation_changed", "critical_role_granted", "paused", "unpaused"],
        "setup_steps": [
            "Create alert in your on-chain monitoring provider for proxy/admin/owner/role events.",
            "Set webhook URL from this response.",
            "Set shared secret in provider and ONCHAIN_WEBHOOK_SECRET on Render.",
            "Send a test event; it should appear in recent_events.",
            "Use professional monitoring baselines to compare events against approved report evidence.",
        ],
        "real_only_note": "Provider webhook evidence is an alert signal, not a certified exploit proof or guarantee.",
    }


def worker_tool_status() -> dict[str, Any]:
    return {
        "enabled": bool(getattr(settings, "professional_worker_runner_enabled", False)),
        "network_enabled": bool(getattr(settings, "professional_worker_network_enabled", False)),
        "allow_local_execution": bool(getattr(settings, "professional_worker_allow_local_execution", False)),
        "cleanup_workspace": bool(getattr(settings, "professional_worker_cleanup_workspace", True)),
        "timeout_seconds": int(getattr(settings, "professional_worker_timeout_seconds", 90)),
        "foundry": _tool_state(bool(getattr(settings, "foundry_enabled", False)), getattr(settings, "foundry_binary", None) or shutil.which("forge")),
        "echidna": _tool_state(bool(getattr(settings, "echidna_enabled", False)), getattr(settings, "echidna_binary", None) or shutil.which("echidna")),
        "real_only_note": "Runner stays disabled unless PROFESSIONAL_WORKER_RUNNER_ENABLED and local execution/tool config are explicitly enabled.",
    }


def _sanitize_worker_files(files: list[dict[str, Any]]) -> dict[str, Any]:
    cleaned: list[dict[str, str]] = []
    rejected: list[dict[str, str]] = []
    total_chars = 0
    max_chars = int(getattr(settings, "professional_worker_max_code_chars", 180000))
    for item in files[:40]:
        path = _safe_text(item.get("path") or "", 240).replace("\\", "/").lstrip("/")
        content = str(item.get("content") or "")
        if not path or ".." in Path(path).parts or path.startswith(".") and path not in {".gitignore"}:
            rejected.append({"path": path, "reason": "Unsafe or empty path"})
            continue
        if Path(path).suffix.lower() not in SAFE_WORKER_EXTENSIONS:
            rejected.append({"path": path, "reason": "Unsupported extension"})
            continue
        if any(pattern.search(content) for pattern in PRIVATE_KEY_PATTERNS):
            rejected.append({"path": path, "reason": "Potential secret/private key text detected"})
            continue
        total_chars += len(content)
        if total_chars > max_chars:
            rejected.append({"path": path, "reason": "Code size limit exceeded"})
            continue
        cleaned.append({"path": path, "content": content})
    return {"files": cleaned, "rejected": rejected, "total_chars": total_chars}


def _write_worker_workspace(root: Path, files: list[dict[str, str]]) -> None:
    for item in files:
        target = (root / item["path"]).resolve()
        if root not in target.parents and target != root:
            raise ValueError("Unsafe worker file path")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(item["content"], encoding="utf-8")


def _run_command(command: list[str], cwd: Path, timeout: int) -> dict[str, Any]:
    env = os.environ.copy()
    if not bool(getattr(settings, "professional_worker_network_enabled", False)):
        env.update({"FOUNDRY_DISABLE_NIGHTLY_WARNING": "1"})
    completed = subprocess.run(
        command,
        cwd=str(cwd),
        env=env,
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
    )
    max_output = int(getattr(settings, "professional_worker_max_output_chars", 18000))
    stdout = (completed.stdout or "")[-max_output:]
    stderr = (completed.stderr or "")[-max_output:]
    return {"returncode": completed.returncode, "stdout_tail": stdout, "stderr_tail": stderr}


def run_worker(payload: dict[str, Any]) -> dict[str, Any]:
    runner_type = _safe_text(payload.get("runner") or payload.get("tool") or "foundry", 40).lower()
    if runner_type not in ALLOWED_WORKER_TYPES:
        raise ValueError("runner must be foundry or echidna")
    authorization_confirmed = bool(payload.get("authorization_confirmed"))
    real_only_acknowledged = bool(payload.get("real_only_acknowledged", True))
    if not authorization_confirmed or not real_only_acknowledged:
        raise ValueError("authorization_confirmed and real_only_acknowledged are required")
    if not bool(getattr(settings, "professional_worker_runner_enabled", False)):
        return {
            "ok": True,
            "status": "Not Assessed",
            "reason": "PROFESSIONAL_WORKER_RUNNER_ENABLED is false.",
            "tool_status": worker_tool_status(),
            "real_only_note": REAL_ONLY_NOTE,
        }
    if not bool(getattr(settings, "professional_worker_allow_local_execution", False)):
        return {
            "ok": True,
            "status": "Provider Not Configured",
            "reason": "PROFESSIONAL_WORKER_ALLOW_LOCAL_EXECUTION is false. Configure isolated worker/runtime before running tools.",
            "tool_status": worker_tool_status(),
            "real_only_note": REAL_ONLY_NOTE,
        }
    files_payload = payload.get("files") if isinstance(payload.get("files"), list) else []
    sanitized = _sanitize_worker_files([item for item in files_payload if isinstance(item, dict)])
    if not sanitized["files"]:
        return {"ok": True, "status": "Not Assessed", "reason": "No safe worker files supplied.", "rejected_files": sanitized["rejected"]}
    tool_status = worker_tool_status()
    tool = tool_status.get(runner_type, {})
    binary = tool.get("binary")
    if tool.get("state") != "Ready" or not binary:
        return {"ok": True, "status": tool.get("state") or "Tool Not Installed", "runner": runner_type, "tool_status": tool_status, "rejected_files": sanitized["rejected"]}

    timeout = int(getattr(settings, "professional_worker_timeout_seconds", 90))
    run_id = new_id("wrk")
    command: list[str]
    if runner_type == "foundry":
        command = [str(binary), "test", "--json"]
    else:
        source = _safe_text(payload.get("source") or "src/Test.sol", 240)
        command = [str(binary), source, "--format", "json"]

    workspace_root = Path(tempfile.mkdtemp(prefix=f"web3guard_{runner_type}_"))
    output: dict[str, Any]
    status = "completed"
    try:
        _write_worker_workspace(workspace_root, sanitized["files"])
        output = _run_command(command, workspace_root, timeout)
        if output.get("returncode") not in {0, None}:
            status = "completed_with_findings_or_errors"
    except subprocess.TimeoutExpired as exc:
        status = "timeout"
        output = {"returncode": None, "stdout_tail": str(exc.stdout or "")[-2000:], "stderr_tail": "Tool timed out."}
    finally:
        if bool(getattr(settings, "professional_worker_cleanup_workspace", True)):
            shutil.rmtree(workspace_root, ignore_errors=True)

    row = {
        "id": run_id,
        "created_at": now_iso(),
        "runner": runner_type,
        "status": status,
        "command": command,
        "files_count": len(sanitized["files"]),
        "rejected_files": sanitized["rejected"],
        "output": output,
        "result_hash": _sha({"runner": runner_type, "status": status, "output": output}),
        "certified_audit": False,
    }
    _append(settings.professional_worker_runs_file, row)
    return {"ok": True, "run": row, "real_only_note": REAL_ONLY_NOTE}


def list_worker_runs(limit: int = 100) -> dict[str, Any]:
    rows = sort_created(_read(settings.professional_worker_runs_file))[:limit]
    return {"ok": True, "runs": rows, "count": len(rows), "tool_status": worker_tool_status()}


def create_reviewer_profile(payload: dict[str, Any]) -> dict[str, Any]:
    name = _safe_text(payload.get("name"), 160)
    email = _safe_text(payload.get("email"), 240).lower()
    role = _safe_text(payload.get("role") or "security_reviewer", 80)
    status = _safe_text(payload.get("status") or "invited", 80)
    if not name:
        raise ValueError("name is required")
    if status not in ALLOWED_REVIEWER_STATUSES:
        raise ValueError("Unsupported reviewer status")
    capabilities = payload.get("capabilities") if isinstance(payload.get("capabilities"), list) else []
    safe_capabilities = [_safe_text(item, 80) for item in capabilities[:12] if _safe_text(item, 80)]
    row = {
        "id": new_id("rev"),
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "name": name,
        "email": email or None,
        "role": role,
        "status": status,
        "capabilities": safe_capabilities,
        "years_experience": int(payload.get("years_experience") or 0),
        "identity_verified": bool(payload.get("identity_verified", False)),
        "nda_signed": bool(payload.get("nda_signed", False)),
        "conflict_check_completed": bool(payload.get("conflict_check_completed", False)),
        "sample_review_completed": bool(payload.get("sample_review_completed", False)),
        "quality_score": min(100, max(0, int(payload.get("quality_score") or 0))),
        "notes": _safe_text(payload.get("notes"), 1200) or None,
        "admin_only": True,
    }
    _append(settings.professional_reviewer_profiles_file, row)
    return {"ok": True, "reviewer": row, "gate": reviewer_gate(row)}


def reviewer_gate(profile: dict[str, Any]) -> dict[str, Any]:
    blockers: list[str] = []
    warnings: list[str] = []
    if not profile.get("identity_verified"):
        blockers.append("identity_not_verified")
    if not profile.get("nda_signed"):
        blockers.append("nda_not_signed")
    if not profile.get("conflict_check_completed"):
        blockers.append("conflict_check_missing")
    if not profile.get("sample_review_completed"):
        warnings.append("sample_review_not_completed")
    if int(profile.get("quality_score") or 0) < 70:
        warnings.append("quality_score_below_70")
    approved = not blockers and str(profile.get("status")) == "approved"
    return {
        "approved_for_client_reports": approved,
        "blockers": blockers,
        "warnings": warnings,
        "allowed_roles": ["lead_reviewer", "contract_reviewer", "web_api_reviewer", "wallet_reviewer", "qa_reviewer", "report_reviewer"],
        "certified_audit_claim_allowed": False,
    }


def list_reviewer_profiles(status: str | None = None, limit: int = 100) -> dict[str, Any]:
    rows = _read(settings.professional_reviewer_profiles_file)
    if status:
        rows = [row for row in rows if row.get("status") == status]
    rows = sort_created(rows)[:limit]
    return {"ok": True, "reviewers": rows, "count": len(rows), "status_counts": _count_status(rows)}


def update_reviewer_status(reviewer_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    rows = _read(settings.professional_reviewer_profiles_file)
    status = _safe_text(payload.get("status") or "screening", 80)
    if status not in ALLOWED_REVIEWER_STATUSES:
        raise ValueError("Unsupported reviewer status")
    updated = None
    for row in rows:
        if row.get("id") == reviewer_id:
            row["status"] = status
            row["updated_at"] = now_iso()
            for flag in ["identity_verified", "nda_signed", "conflict_check_completed", "sample_review_completed"]:
                if flag in payload:
                    row[flag] = bool(payload.get(flag))
            if "quality_score" in payload:
                row["quality_score"] = min(100, max(0, int(payload.get("quality_score") or 0)))
            if payload.get("notes"):
                row["notes"] = _safe_text(payload.get("notes"), 1200)
            updated = row
            break
    if not updated:
        raise ValueError("Reviewer not found")
    _rewrite(settings.professional_reviewer_profiles_file, rows)
    return {"ok": True, "reviewer": updated, "gate": reviewer_gate(updated)}


def create_delivery(payload: dict[str, Any]) -> dict[str, Any]:
    client_name = _safe_text(payload.get("client_name"), 180)
    project_name = _safe_text(payload.get("project_name"), 180)
    if not client_name or not project_name:
        raise ValueError("client_name and project_name are required")
    report_payload = payload.get("report_payload") if isinstance(payload.get("report_payload"), dict) else {}
    blocked = _has_blocked_claims(payload)
    if blocked:
        raise ValueError("Blocked unsafe public claims: " + ", ".join(blocked))
    proof_id = _safe_text(payload.get("proof_id"), 160) or None
    report_id = _safe_text(payload.get("report_id") or report_payload.get("report_id"), 180) or new_id("report")
    status = _safe_text(payload.get("status") or "draft", 60)
    if status not in ALLOWED_DELIVERY_STATUSES:
        raise ValueError("Unsupported delivery status")
    packet = {
        "client_name": client_name,
        "project_name": project_name,
        "report_id": report_id,
        "proof_id": proof_id,
        "summary": _safe_text(payload.get("summary") or "Pre-audit readiness delivery packet prepared from available evidence.", 2200),
        "included_artifacts": payload.get("included_artifacts") if isinstance(payload.get("included_artifacts"), list) else [],
        "report_payload": report_payload,
        "safe_public_wording": "Web3Guard AI pre-audit readiness report. Not a certified audit and not a guarantee of safety.",
        "certified_audit": False,
        "created_at": now_iso(),
    }
    delivery = {
        "id": new_id("delivery"),
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "status": status,
        "client_email": _safe_text(payload.get("client_email"), 240) or None,
        "client_name": client_name,
        "project_name": project_name,
        "report_id": report_id,
        "proof_id": proof_id,
        "packet": packet,
        "integrity_hash": _sha(packet),
        "certified_audit": False,
        "claim_gate": {"blocked_claims": [], "certified_audit_claim_allowed": False, "direct_competition_claim_allowed": False},
    }
    _append(settings.professional_client_deliveries_file, delivery)
    return {"ok": True, "delivery": delivery, "next_steps": ["Share packet with client.", "Track client status changes.", "Publish proof only after approval gate passes."]}


def list_deliveries(status: str | None = None, limit: int = 100) -> dict[str, Any]:
    rows = _read(settings.professional_client_deliveries_file)
    if status:
        rows = [row for row in rows if row.get("status") == status]
    rows = sort_created(rows)[:limit]
    return {"ok": True, "deliveries": rows, "count": len(rows), "status_counts": _count_status(rows)}


def update_delivery_status(delivery_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    rows = _read(settings.professional_client_deliveries_file)
    status = _safe_text(payload.get("status") or "client_viewed", 80)
    if status not in ALLOWED_DELIVERY_STATUSES:
        raise ValueError("Unsupported delivery status")
    updated = None
    for row in rows:
        if row.get("id") == delivery_id:
            row["status"] = status
            row["updated_at"] = now_iso()
            if payload.get("client_note"):
                row["client_note"] = _safe_text(payload.get("client_note"), 1800)
            updated = row
            break
    if not updated:
        raise ValueError("Delivery not found")
    _rewrite(settings.professional_client_deliveries_file, rows)
    return {"ok": True, "delivery": updated}


def verify_delivery(delivery_id: str, integrity_hash: str | None = None) -> dict[str, Any]:
    rows = _read(settings.professional_client_deliveries_file)
    delivery = next((row for row in rows if row.get("id") == delivery_id), None)
    if not delivery:
        raise ValueError("Delivery not found")
    expected = _sha(delivery.get("packet") or {})
    stored = delivery.get("integrity_hash")
    supplied_match = None
    if integrity_hash:
        supplied_match = _safe_text(integrity_hash, 128) == expected == stored
    return {
        "ok": True,
        "delivery_id": delivery_id,
        "stored_hash": stored,
        "computed_hash": expected,
        "record_valid": stored == expected,
        "supplied_hash_match": supplied_match,
        "certified_audit": False,
        "real_only_note": "Integrity hash proves packet consistency only; it does not prove project safety.",
    }


def delivery_public_summary(delivery_id: str) -> dict[str, Any]:
    rows = _read(settings.professional_client_deliveries_file)
    delivery = next((row for row in rows if row.get("id") == delivery_id), None)
    if not delivery:
        raise ValueError("Delivery not found")
    packet = delivery.get("packet") or {}
    return {
        "ok": True,
        "delivery_id": delivery_id,
        "project_name": delivery.get("project_name"),
        "client_name": delivery.get("client_name"),
        "status": delivery.get("status"),
        "report_id": delivery.get("report_id"),
        "proof_id": delivery.get("proof_id"),
        "integrity_hash": delivery.get("integrity_hash"),
        "safe_public_wording": packet.get("safe_public_wording"),
        "summary": packet.get("summary"),
        "certified_audit": False,
        "claim_gate": delivery.get("claim_gate"),
    }
