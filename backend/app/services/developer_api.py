from __future__ import annotations

import hashlib
import hmac
import secrets
from typing import Any

from app.core.config import settings
from app.models.schemas import ApiKeyCreate, ApiKeyUpdate, DeveloperAuditRequest
from app.services.mega_phase_d_store import MEGA_PHASE_D_REAL_ONLY_NOTE, append_jsonl, new_id, now_iso, read_jsonl, rewrite_jsonl, sort_created, storage_path
from app.services.scan_contract import scan_solidity


def developer_api_status() -> dict[str, Any]:
    return {
        "version": "1.0",
        "enabled": settings.developer_api_enabled,
        "auth": "X-Web3Guard-API-Key header for /api/v1 endpoints",
        "live_capabilities": ["Create hashed API keys", "List/manage key metadata", "Verify keys for API endpoints", "Start rule-engine audit via API"],
        "not_claimed": ["No SDK package yet", "No webhook delivery yet", "No fake Slither/AI findings", "No unlimited rate limits"],
        "real_only_note": MEGA_PHASE_D_REAL_ONLY_NOTE,
    }


def _keys_path():
    return storage_path(settings.developer_api_keys_file)


def _events_path():
    return storage_path(settings.developer_api_events_file)


def _hash_key(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def create_api_key(payload: ApiKeyCreate, user_id: str | None = None) -> dict[str, Any]:
    if not payload.real_only_acknowledged:
        raise ValueError("Real-only acknowledgement is required")
    raw_secret = f"wg_{secrets.token_urlsafe(32)}"
    prefix = raw_secret[:10]
    now = now_iso()
    row = {
        "id": new_id("apikey"),
        "user_id": user_id or payload.user_id,
        "organization_id": payload.organization_id,
        "name": payload.name,
        "key_hash": _hash_key(raw_secret),
        "key_prefix": prefix,
        "permissions": payload.permissions,
        "rate_limit_per_hour": payload.rate_limit_per_hour,
        "expires_at": payload.expires_at,
        "status": "active",
        "last_used_at": None,
        "created_at": now,
        "updated_at": now,
    }
    append_jsonl(_keys_path(), row)
    public_row = {k: v for k, v in row.items() if k != "key_hash"}
    return {"api_key": raw_secret, "record": public_row, "warning": "Copy this API key now. It is stored only as a hash and cannot be shown again."}


def list_api_keys(user_id: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
    rows = read_jsonl(_keys_path())
    if user_id:
        rows = [r for r in rows if r.get("user_id") == user_id]
    safe = []
    for row in sort_created(rows)[:limit]:
        safe.append({k: v for k, v in row.items() if k != "key_hash"})
    return safe


def update_api_key(key_id: str, payload: ApiKeyUpdate) -> dict[str, Any] | None:
    path = _keys_path(); rows = read_jsonl(path); updated = None
    patch = {k: v for k, v in payload.model_dump().items() if v is not None}
    patch["updated_at"] = now_iso()
    for row in rows:
        if row.get("id") == key_id:
            row.update(patch); updated = row; break
    rewrite_jsonl(path, rows)
    return {k: v for k, v in updated.items() if k != "key_hash"} if updated else None


def verify_api_key(raw_key: str, required_permission: str) -> dict[str, Any] | None:
    if not settings.developer_api_enabled:
        return None
    key_hash = _hash_key(raw_key)
    rows = read_jsonl(_keys_path())
    for row in rows:
        if hmac.compare_digest(str(row.get("key_hash")), key_hash) and row.get("status") == "active":
            permissions = row.get("permissions") or []
            if required_permission not in permissions and "audit:start" not in permissions and required_permission != "registry:verify":
                return None
            row["last_used_at"] = now_iso()
            rewrite_jsonl(_keys_path(), rows)
            append_jsonl(_events_path(), {"id": new_id("api_evt"), "api_key_id": row.get("id"), "permission": required_permission, "created_at": row["last_used_at"]})
            return {k: v for k, v in row.items() if k != "key_hash"}
    return None


def run_developer_audit(payload: DeveloperAuditRequest, api_key_record: dict[str, Any]) -> dict[str, Any]:
    if not payload.real_only_acknowledged:
        raise ValueError("Real-only acknowledgement is required")
    if payload.solidity_code:
        scan = scan_solidity(payload.solidity_code, payload.project_name or "Developer API audit", "api")
        return {"ok": True, "mode": "contract_rule_engine", "api_key_id": api_key_record.get("id"), "result": scan.model_dump(mode="json"), "real_only_note": MEGA_PHASE_D_REAL_ONLY_NOTE}
    return {"ok": True, "mode": "not_assessed", "api_key_id": api_key_record.get("id"), "result": None, "message": "No supported real input provided. Submit solidity_code for rule-engine audit. Website API audit will be exposed after provider-safe endpoint wiring.", "real_only_note": MEGA_PHASE_D_REAL_ONLY_NOTE}
