from __future__ import annotations

import json
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.core.config import settings

REAL_ONLY_NOTE = (
    "Threat Intel Feed is local/manual curated in MVP. It does not claim real-time news unless live sources are explicitly enabled and cited."
)

DEFAULT_KNOWLEDGE_BASE = [
    {
        "id": "kb_reentrancy_generic",
        "created_at": "2026-01-01T00:00:00+00:00",
        "title": "Reentrancy remains a recurring smart-contract failure mode",
        "protocol_name": None,
        "chain": "EVM",
        "category": "reentrancy",
        "severity": "high",
        "summary": "Projects with external calls before state updates should review checks-effects-interactions, reentrancy guards, and pull-payment patterns.",
        "technical_notes": "This is an educational threat pattern, not a live incident feed item.",
        "affected_project_types": ["DeFi", "Staking", "Marketplace", "Bridge"],
        "relevance_tags": ["external-call", "withdraw", "reentrancy", "solidity"],
        "source_url": None,
        "source_label": "Manual RAADHANEX knowledge-base entry",
        "amount_lost_usd": None,
        "incident_date": None,
        "curated_by": "RAADHANEX",
        "status": "manual_knowledge_base",
    },
    {
        "id": "kb_wallet_drainer_generic",
        "created_at": "2026-01-01T00:00:00+00:00",
        "title": "Wallet-drainer campaigns commonly abuse unlimited approvals and unclear signatures",
        "protocol_name": None,
        "chain": "EVM",
        "category": "wallet_drainer",
        "severity": "high",
        "summary": "dApps should clearly display spender, token, chain, approval amount, and signature purpose before prompting users.",
        "technical_notes": "This is an educational threat pattern, not a live incident feed item.",
        "affected_project_types": ["NFT", "Airdrop", "Token Launch", "Marketplace"],
        "relevance_tags": ["approval", "permit", "spender", "signature", "wallet"],
        "source_url": None,
        "source_label": "Manual RAADHANEX knowledge-base entry",
        "amount_lost_usd": None,
        "incident_date": None,
        "curated_by": "RAADHANEX",
        "status": "manual_knowledge_base",
    },
    {
        "id": "kb_admin_key_generic",
        "created_at": "2026-01-01T00:00:00+00:00",
        "title": "Single hot-wallet admin control is a major launch-readiness concern",
        "protocol_name": None,
        "chain": "Any",
        "category": "admin_opsec",
        "severity": "medium",
        "summary": "Teams should document multisig, timelock, signer rotation, hardware wallet, and emergency response controls before launch.",
        "technical_notes": "This is an educational threat pattern, not a live incident feed item.",
        "affected_project_types": ["Token", "NFT", "DAO", "DeFi", "Presale"],
        "relevance_tags": ["multisig", "timelock", "owner", "upgrade-admin", "treasury"],
        "source_url": None,
        "source_label": "Manual RAADHANEX knowledge-base entry",
        "amount_lost_usd": None,
        "incident_date": None,
        "curated_by": "RAADHANEX",
        "status": "manual_knowledge_base",
    },
]


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _id(prefix: str) -> str:
    return f"{prefix}_{secrets.token_hex(10)}"


def _path(raw: str) -> Path:
    path = Path(raw)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text("", encoding="utf-8")
    return path


def _read_user_entries() -> list[dict[str, Any]]:
    path = _path(settings.threat_intel_file)
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows


def _append(row: dict[str, Any]) -> None:
    path = _path(settings.threat_intel_file)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, default=str, ensure_ascii=False) + "\n")


def threat_intel_status() -> dict[str, Any]:
    user_entries = _read_user_entries()
    return {
        "ok": True,
        "phase": "Mega Phase C - Phase 24 Threat Intelligence Feed",
        "enabled": settings.threat_intel_enabled,
        "live_sources_enabled": settings.threat_intel_live_sources_enabled,
        "manual_entry_count": len(user_entries),
        "knowledge_base_entry_count": len(DEFAULT_KNOWLEDGE_BASE),
        "modes": ["manual_curated_entries", "local_knowledge_base"],
        "real_only_note": REAL_ONLY_NOTE,
        "live_source_note": "No live/current news feed is claimed unless THREAT_INTEL_LIVE_SOURCES_ENABLED=true and a real feed integration is added.",
    }


def create_threat_intel_entry(payload: Any) -> dict[str, Any]:
    if not payload.real_only_acknowledged:
        raise ValueError("Real-only acknowledgement is required")
    row = payload.model_dump()
    row.update({
        "id": _id("threat"),
        "created_at": _now().isoformat(),
        "updated_at": _now().isoformat(),
        "status": "manual_curated",
        "live_verified": False,
        "real_only_note": REAL_ONLY_NOTE,
    })
    _append(row)
    return row


def list_threat_intel(project_type: str | None = None, chain: str | None = None, tags: list[str] | None = None, limit: int = 20) -> dict[str, Any]:
    rows = [*DEFAULT_KNOWLEDGE_BASE, *_read_user_entries()]
    tags = [t.lower() for t in (tags or []) if t]
    if project_type:
        pt = project_type.lower()
        rows = [r for r in rows if pt in " ".join([str(x) for x in r.get("affected_project_types", [])]).lower() or pt in str(r.get("title", "")).lower()]
    if chain:
        ch = chain.lower()
        rows = [r for r in rows if str(r.get("chain") or "").lower() in {ch, "any", "evm"} or ch in str(r.get("summary", "")).lower()]
    if tags:
        rows = [r for r in rows if any(tag in [str(x).lower() for x in r.get("relevance_tags", [])] or tag in str(r.get("summary", "")).lower() for tag in tags)]
    rows.sort(key=lambda item: item.get("created_at", ""), reverse=True)
    return {
        "ok": True,
        "items": rows[:limit],
        "count": min(len(rows), limit),
        "total_available_after_filter": len(rows),
        "status": threat_intel_status(),
        "real_only_note": REAL_ONLY_NOTE,
    }


def threat_relevance_for_report(findings: list[dict[str, Any]] | None = None, project_type: str | None = None) -> dict[str, Any]:
    tags: list[str] = []
    for finding in findings or []:
        for field in ["category", "title", "description", "recommendation"]:
            value = str(finding.get(field, "")).lower()
            for token in ["reentrancy", "approval", "permit", "spender", "owner", "multisig", "timelock", "oracle", "cors", "webhook", "api", "wallet"]:
                if token in value and token not in tags:
                    tags.append(token)
    return list_threat_intel(project_type=project_type, tags=tags, limit=10)
