from __future__ import annotations

from typing import Any

from app.core.config import settings
from app.models.schemas import RegistryPublicationCreate, RegistryStatusUpdate
from app.services.mega_phase_d_store import MEGA_PHASE_D_REAL_ONLY_NOTE, append_jsonl, new_id, now_iso, read_jsonl, rewrite_jsonl, sha256_text, sort_created, storage_path


def registry_status() -> dict[str, Any]:
    return {
        "phase": "Mega Phase D - Phase 26 Public Registry + Trust Badge",
        "enabled": True,
        "badge_base_url": settings.registry_badge_base_url,
        "live_capabilities": ["Publish real report metadata", "Verify report hash", "Generate non-certified pre-audit badge payload", "Revoke/expire/supersede records"],
        "not_claimed": ["No on-chain certificate yet", "No certified audit badge", "No fake client/project verification", "No guarantee of security"],
        "real_only_note": MEGA_PHASE_D_REAL_ONLY_NOTE,
    }


def _path():
    return storage_path(settings.public_registry_file)


def _events_path():
    return storage_path(settings.registry_events_file)


def create_publication(payload: RegistryPublicationCreate, user_id: str | None = None) -> dict[str, Any]:
    if not payload.real_only_acknowledged:
        raise ValueError("Real-only acknowledgement is required")
    public_id = new_id("reg")
    badge_token = sha256_text(f"{public_id}:{payload.report_id}:{payload.report_hash}")[:32]
    now = now_iso()
    row = {
        "id": public_id,
        "user_id": user_id or payload.user_id,
        "report_id": payload.report_id,
        "project_name": payload.project_name,
        "report_hash": payload.report_hash,
        "score": payload.score,
        "risk_label": payload.risk_label,
        "summary": payload.summary,
        "status": payload.status,
        "expires_at": payload.expires_at,
        "public_notes": payload.public_notes,
        "badge_token": badge_token,
        "public_url": f"{settings.registry_badge_base_url.rstrip('/')}/{public_id}",
        "badge_label": "Pre-audit readiness reviewed",
        "created_at": now,
        "updated_at": now,
        "disclaimer": "This is a public pre-audit readiness record, not a certified audit or security guarantee.",
    }
    append_jsonl(_path(), row)
    append_jsonl(_events_path(), {"id": new_id("reg_evt"), "registry_id": public_id, "event": "published", "created_at": now, "reason": None})
    return row


def list_publications(status: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
    rows = read_jsonl(_path())
    if status:
        rows = [r for r in rows if r.get("status") == status]
    return sort_created(rows)[:limit]


def get_publication(public_id: str) -> dict[str, Any] | None:
    return next((r for r in read_jsonl(_path()) if r.get("id") == public_id), None)


def update_publication_status(public_id: str, payload: RegistryStatusUpdate) -> dict[str, Any] | None:
    path = _path(); rows = read_jsonl(path); updated = None
    now = now_iso()
    for row in rows:
        if row.get("id") == public_id:
            row["status"] = payload.status
            row["updated_at"] = now
            updated = row
            break
    rewrite_jsonl(path, rows)
    if updated:
        append_jsonl(_events_path(), {"id": new_id("reg_evt"), "registry_id": public_id, "event": payload.status, "reason": payload.reason, "created_at": now})
    return updated


def verify_report(public_id: str, report_hash: str | None = None) -> dict[str, Any]:
    row = get_publication(public_id)
    if not row:
        return {"ok": False, "status": "not_found", "verified": False}
    hash_match = None if report_hash is None else report_hash == row.get("report_hash")
    return {
        "ok": True,
        "verified": row.get("status") == "active" and (hash_match is not False),
        "status": row.get("status"),
        "hash_match": hash_match,
        "publication": row,
        "badge": {
            "label": row.get("badge_label"),
            "token": row.get("badge_token"),
            "embed_text": f"{row.get('project_name')} — Pre-audit readiness reviewed by Web3Guard AI by RAADHANEX",
            "disclaimer": row.get("disclaimer"),
        },
        "real_only_note": MEGA_PHASE_D_REAL_ONLY_NOTE,
    }
