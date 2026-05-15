from __future__ import annotations

from pathlib import Path
from typing import Any

from app.core.config import settings
from app.services.mega_phase_e_store import MEGA_PHASE_E_REAL_ONLY_NOTE, append_jsonl, new_id, now_iso, read_jsonl, rewrite_jsonl, safe_count_jsonl, sort_created, storage_path


def _read(raw_path: str) -> list[dict[str, Any]]:
    return read_jsonl(storage_path(raw_path))


def _sum_amount(rows: list[dict[str, Any]]) -> int:
    total = 0
    for row in rows:
        try:
            amount = int(row.get("amount_inr") or row.get("payment_amount_inr") or 0)
        except Exception:
            amount = 0
        total += amount
    return total


def admin_super_status() -> dict[str, Any]:
    return {
        "ok": True,
        "phase": "Mega Phase E - Phase 30 Admin Super Panel v2",
        "live": True,
        "real_only_note": MEGA_PHASE_E_REAL_ONLY_NOTE,
        "requires_admin_token": True,
        "not_claimed": [
            "No fake MRR/revenue metrics are generated.",
            "No real system monitoring provider is connected yet.",
            "No email delivery or background job queue is faked.",
            "Metrics are calculated only from local/Supabase-backed records currently present.",
        ],
    }


def admin_super_dashboard() -> dict[str, Any]:
    leads = _read(settings.leads_file)
    payments = _read(settings.payment_intents_file)
    subscriptions = _read(settings.subscriptions_file)
    projects = _read(settings.db_projects_file)
    scans = _read(settings.db_scan_history_file)
    reports = _read(settings.db_saved_reports_file)
    orgs = _read(settings.db_organizations_file)
    bounties = _read(settings.bug_bounty_programs_file)
    registry = _read(settings.public_registry_file)
    api_keys = _read(settings.developer_api_keys_file)
    threat_entries = _read(settings.threat_intel_file)
    monitoring_configs = _read(settings.monitoring_configs_file)
    monitoring_alerts = _read(settings.monitoring_alerts_file)
    verified_payments = [p for p in payments if p.get("status") in {"verified", "webhook_verified", "razorpay_paid", "captured"}]
    pending_payments = [p for p in payments if p.get("status") not in {"verified", "webhook_verified", "razorpay_paid", "captured", "failed", "cancelled"}]
    return {
        "ok": True,
        "totals": {
            "leads": len(leads),
            "payments": len(payments),
            "subscriptions": len(subscriptions),
            "projects": len(projects),
            "scans": len(scans),
            "reports": len(reports),
            "organizations": len(orgs),
            "bounty_programs": len(bounties),
            "registry_publications": len(registry),
            "developer_api_keys": len(api_keys),
            "threat_intel_entries": len(threat_entries),
            "monitoring_configs": len(monitoring_configs),
            "monitoring_alerts": len(monitoring_alerts),
        },
        "revenue": {
            "verified_revenue_inr": _sum_amount(verified_payments),
            "pending_payment_amount_inr": _sum_amount(pending_payments),
            "real_only_note": "Revenue is summed only from stored payment-intent records. It is not bank-settled revenue unless payment is verified.",
        },
        "recent": {
            "leads": sort_created(leads)[:10],
            "payments": sort_created(payments)[:10],
            "scans": sort_created(scans)[:10],
            "reports": sort_created(reports)[:10],
            "monitoring_alerts": sort_created(monitoring_alerts)[:10],
        },
        "real_only_note": MEGA_PHASE_E_REAL_ONLY_NOTE,
    }


def feature_flags_path() -> Path:
    return storage_path(settings.admin_feature_flags_file)


def audit_log_path() -> Path:
    return storage_path(settings.admin_audit_log_file)


def list_feature_flags() -> list[dict[str, Any]]:
    return sort_created(read_jsonl(feature_flags_path()))


def upsert_feature_flag(key: str, enabled: bool, note: str | None, actor: str | None = None) -> dict[str, Any]:
    rows = read_jsonl(feature_flags_path())
    now = now_iso()
    existing = next((row for row in rows if row.get("key") == key), None)
    if existing:
        existing.update({"enabled": enabled, "note": note, "updated_at": now, "updated_by": actor})
        flag = existing
    else:
        flag = {"id": new_id("flag"), "key": key, "enabled": enabled, "note": note, "created_at": now, "updated_at": now, "updated_by": actor}
        rows.append(flag)
    rewrite_jsonl(feature_flags_path(), rows)
    append_audit_log("feature_flag_updated", f"Feature flag {key} set to {enabled}", actor=actor, target_id=flag["id"])
    return flag


def append_audit_log(action: str, summary: str, actor: str | None = None, target_id: str | None = None, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    row = {"id": new_id("adm_evt"), "action": action, "summary": summary, "actor": actor, "target_id": target_id, "metadata": metadata or {}, "created_at": now_iso()}
    append_jsonl(audit_log_path(), row)
    return row


def list_audit_logs(limit: int = 100) -> list[dict[str, Any]]:
    return sort_created(read_jsonl(audit_log_path()))[:limit]


def system_health_snapshot() -> dict[str, Any]:
    files = {
        "leads_file": settings.leads_file,
        "payment_intents_file": settings.payment_intents_file,
        "scan_history_file": settings.db_scan_history_file,
        "saved_reports_file": settings.db_saved_reports_file,
        "developer_api_keys_file": settings.developer_api_keys_file,
        "admin_feature_flags_file": settings.admin_feature_flags_file,
        "admin_audit_log_file": settings.admin_audit_log_file,
    }
    storage = {}
    for label, raw in files.items():
        path = Path(raw)
        storage[label] = {"path": str(path), "exists": path.exists(), "rows": safe_count_jsonl(raw), "parent_exists": path.parent.exists()}
    return {
        "ok": True,
        "storage": storage,
        "providers": {
            "supabase_configured": bool(settings.supabase_url and settings.supabase_service_role_key),
            "razorpay_enabled": settings.razorpay_enabled,
            "ai_enabled": settings.ai_enabled,
            "monitoring_rpc_enabled": settings.monitoring_rpc_enabled,
            "threat_live_sources_enabled": settings.threat_intel_live_sources_enabled,
        },
        "real_only_note": "This is an app-level readiness snapshot, not Datadog/Sentry/UptimeRobot telemetry.",
    }
