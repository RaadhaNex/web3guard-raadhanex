from __future__ import annotations

import json
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

from app.core.config import settings

ZERO_TOPIC_ADDRESS = "0x0000000000000000000000000000000000000000"
EVENT_TOPICS = {
    # keccak256("OwnershipTransferred(address,address)")
    "owner_changed": "0x8be0079c531659141344cd1fd0a4f28419497f9722a3daafe3b4186f6b6457e0",
    # keccak256("RoleGranted(bytes32,address,address)")
    "role_granted": "0x2f878811b10b3a3220e2a76d37c5fb9f78556ccc20e7594d5d99801932dc9a0",
    # keccak256("Paused(address)")
    "pause": "0x62e78cea01bee320cd4e420270b5ea74000d11b0c9f74754ebdbfc544b05a258",
    # keccak256("Unpaused(address)")
    "unpause": "0x5db9ee0a495bf2e6ff9c91a7834c1ba4fdd244a5e8aa4e537bd38aeae4b073aa",
    # keccak256("Upgraded(address)")
    "upgrade": "0xbc7cd75a20ee27f5453f3cc9bf4e1f9a7f1ac499e98e376ec0cc7d37d51e0b2d",
    # keccak256("Transfer(address,address,uint256)")
    "large_mint": "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef",
}

EVENT_LABELS = {
    "owner_changed": ("high", "Ownership transfer event detected"),
    "role_granted": ("high", "Role granted event detected"),
    "pause": ("medium", "Pause event detected"),
    "unpause": ("low", "Unpause event detected"),
    "upgrade": ("high", "Proxy upgrade event detected"),
    "large_mint": ("medium", "Token mint/transfer-from-zero event detected"),
}

CHAIN_RPC_SETTING = {
    "ethereum": "ethereum_rpc_url",
    "polygon": "polygon_rpc_url",
    "bsc": "bsc_rpc_url",
    "arbitrum": "arbitrum_rpc_url",
    "optimism": "optimism_rpc_url",
    "base": "base_rpc_url",
    "avalanche": "avalanche_rpc_url",
}

REAL_ONLY_NOTE = (
    "Monitoring Lite stores real user-created configs and real manual/RPC-detected alerts only. "
    "It does not fabricate live monitoring, hack alerts, transaction alerts, or notification delivery."
)


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


def _read(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows


def _append(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, default=str, ensure_ascii=False) + "\n")


def _rewrite(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, default=str, ensure_ascii=False) + "\n")


def _clean_address(address: str) -> str:
    value = address.strip().lower()
    if not value.startswith("0x") or len(value) != 42:
        raise ValueError("A valid 42-character EVM contract address is required")
    int(value[2:], 16)  # validates hex
    return value


def rpc_url_for_chain(chain: str) -> str | None:
    attr = CHAIN_RPC_SETTING.get((chain or "ethereum").lower())
    return getattr(settings, attr, None) if attr else None


def monitoring_status() -> dict[str, Any]:
    configs = _read(_path(settings.monitoring_configs_file))
    alerts = _read(_path(settings.monitoring_alerts_file))
    chains = {chain: bool(rpc_url_for_chain(chain)) for chain in CHAIN_RPC_SETTING}
    return {
        "ok": True,
        "phase": "Mega Phase C - Phase 23 Monitoring Lite",
        "monitoring_enabled": settings.monitoring_enabled,
        "rpc_enabled": settings.monitoring_rpc_enabled,
        "configured_rpc_chains": chains,
        "config_count": len(configs),
        "alert_count": len(alerts),
        "supported_events": list(EVENT_TOPICS.keys()),
        "rpc_checks": ["eth_blockNumber", "eth_getLogs"],
        "modes": ["manual_admin_ingest", "optional_rpc_read_only_eth_blockNumber_and_eth_getLogs"],
        "real_only_note": REAL_ONLY_NOTE,
        "disabled_note": "If MONITORING_ENABLED or MONITORING_RPC_ENABLED is false, the app will not show fake live alerts. Manual saved configs and manually ingested alerts still work as real records.",
    }


def create_monitoring_config(payload: Any) -> dict[str, Any]:
    row = {
        "id": _id("mon"),
        "created_at": _now().isoformat(),
        "updated_at": _now().isoformat(),
        "project_name": payload.project_name,
        "contract_address": _clean_address(payload.contract_address),
        "chain": (payload.chain or "ethereum").lower(),
        "watch_types": payload.watch_types,
        "alert_channels": payload.alert_channels,
        "notification_target": payload.notification_target,
        "ownership_verified": payload.ownership_verified,
        "notes": payload.notes,
        "status": "active_manual_ready" if not settings.monitoring_rpc_enabled else "active_rpc_ready",
        "rpc_configured": bool(rpc_url_for_chain(payload.chain)),
        "real_only_note": REAL_ONLY_NOTE,
    }
    _append(_path(settings.monitoring_configs_file), row)
    return row


def list_monitoring_configs() -> list[dict[str, Any]]:
    rows = _read(_path(settings.monitoring_configs_file))
    return sorted(rows, key=lambda item: item.get("created_at", ""), reverse=True)


def get_monitoring_config(config_id: str) -> dict[str, Any] | None:
    return next((item for item in list_monitoring_configs() if item.get("id") == config_id), None)


def list_monitoring_alerts(config_id: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
    alerts = _read(_path(settings.monitoring_alerts_file))
    if config_id:
        alerts = [item for item in alerts if item.get("config_id") == config_id]
    alerts.sort(key=lambda item: item.get("created_at", ""), reverse=True)
    return alerts[:limit]


def ingest_monitoring_alert(payload: Any) -> dict[str, Any]:
    config = get_monitoring_config(payload.config_id)
    if not config:
        raise ValueError("Monitoring config not found")
    if payload.source not in {"manual_admin", "rpc_check"}:
        raise ValueError("Manual alert ingest only accepts manual_admin or rpc_check sources in Patch H. Verified webhook alert ingestion is not implemented, so no fake webhook alert was saved.")
    row = {
        "id": _id("alert"),
        "created_at": _now().isoformat(),
        "config_id": payload.config_id,
        "project_name": config.get("project_name"),
        "contract_address": config.get("contract_address"),
        "chain": config.get("chain"),
        "event_type": payload.event_type,
        "severity": payload.severity,
        "description": payload.description,
        "tx_hash": payload.tx_hash,
        "source": payload.source,
        "evidence": payload.evidence or {},
        "source_validation": "manual_admin_acknowledged" if payload.source == "manual_admin" else "rpc_check_recorded",
        "notification_status": "dashboard_recorded_only",
        "real_only_note": "This alert is a real stored record from manual/RPC input. It is not a fabricated live alert.",
    }
    _append(_path(settings.monitoring_alerts_file), row)
    return row


def _rpc_call(rpc_url: str, method: str, params: list[Any]) -> Any:
    payload = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
    with httpx.Client(timeout=15) as client:
        response = client.post(rpc_url, json=payload)
        response.raise_for_status()
        data = response.json()
    if data.get("error"):
        raise ValueError(f"RPC error: {data['error']}")
    return data.get("result")


def _hex_block(n: int) -> str:
    return hex(max(0, n))


def _block_to_int(value: str | None, default: int) -> int:
    if not value:
        return default
    if isinstance(value, str) and value.startswith("0x"):
        return int(value, 16)
    return int(value)


def _topic_matches_zero_from(log: dict[str, Any]) -> bool:
    topics = [str(x).lower() for x in log.get("topics", [])]
    if len(topics) < 3:
        return False
    return topics[1].endswith(ZERO_TOPIC_ADDRESS[2:])


def _alert_from_log(config: dict[str, Any], event_type: str, log: dict[str, Any]) -> dict[str, Any]:
    severity, title = EVENT_LABELS.get(event_type, ("info", "Monitored event detected"))
    if event_type == "large_mint" and not _topic_matches_zero_from(log):
        severity = "info"
        title = "ERC20 Transfer event detected; mint-from-zero evidence not confirmed"
    return {
        "id": _id("alert"),
        "created_at": _now().isoformat(),
        "config_id": config.get("id"),
        "project_name": config.get("project_name"),
        "contract_address": config.get("contract_address"),
        "chain": config.get("chain"),
        "event_type": event_type,
        "severity": severity,
        "description": f"{title} on monitored contract. Review transaction before treating it as an incident.",
        "tx_hash": log.get("transactionHash"),
        "source": "rpc_check",
        "evidence": {"log": log, "topic": EVENT_TOPICS.get(event_type)},
        "notification_status": "dashboard_recorded_only",
        "real_only_note": "Detected from a real read-only RPC eth_getLogs call. No transaction signing or exploit testing was performed.",
    }


def run_rpc_monitoring_check(config_id: str, from_block: str | None = None, to_block: str | None = None) -> dict[str, Any]:
    config = get_monitoring_config(config_id)
    if not config:
        raise ValueError("Monitoring config not found")
    if not settings.monitoring_enabled or not settings.monitoring_rpc_enabled:
        return {
            "ok": True,
            "ran": False,
            "reason": "Monitoring/RPC is disabled in env. No fake live check was performed.",
            "config": config,
            "new_alerts": [],
            "real_only_note": REAL_ONLY_NOTE,
        }
    rpc_url = rpc_url_for_chain(config.get("chain", "ethereum"))
    if not rpc_url:
        return {
            "ok": True,
            "ran": False,
            "reason": f"No RPC URL configured for chain {config.get('chain')}. No fake live check was performed.",
            "config": config,
            "new_alerts": [],
            "real_only_note": REAL_ONLY_NOTE,
        }

    latest_hex = _rpc_call(rpc_url, "eth_blockNumber", [])
    latest = int(latest_hex, 16)
    start = _block_to_int(from_block, max(0, latest - settings.monitoring_default_block_lookback))
    end = _block_to_int(to_block, latest)
    if end < start:
        raise ValueError("to_block must be greater than or equal to from_block")
    if end - start > settings.monitoring_max_block_window:
        raise ValueError(f"Block range too large. Max window is {settings.monitoring_max_block_window} blocks")

    watch_types = set(config.get("watch_types") or [])
    new_alerts: list[dict[str, Any]] = []
    for event_type, topic in EVENT_TOPICS.items():
        if event_type not in watch_types:
            continue
        params = [{"fromBlock": _hex_block(start), "toBlock": _hex_block(end), "address": config.get("contract_address"), "topics": [topic]}]
        logs = _rpc_call(rpc_url, "eth_getLogs", params) or []
        if not isinstance(logs, list):
            continue
        for log in logs[:50]:
            new_alerts.append(_alert_from_log(config, event_type, log))

    existing_hashes = {item.get("tx_hash") + ":" + item.get("event_type", "") for item in _read(_path(settings.monitoring_alerts_file)) if item.get("tx_hash")}
    stored: list[dict[str, Any]] = []
    for alert in new_alerts:
        key = (alert.get("tx_hash") or "") + ":" + alert.get("event_type", "")
        if alert.get("tx_hash") and key in existing_hashes:
            continue
        _append(_path(settings.monitoring_alerts_file), alert)
        stored.append(alert)

    event_row = {
        "id": _id("monrun"),
        "created_at": _now().isoformat(),
        "config_id": config_id,
        "chain": config.get("chain"),
        "from_block": start,
        "to_block": end,
        "logs_detected": len(new_alerts),
        "alerts_stored": len(stored),
        "source": "rpc_check",
        "rpc_checks": ["eth_blockNumber", "eth_getLogs"],
    }
    _append(_path(settings.monitoring_events_file), event_row)
    return {
        "ok": True,
        "ran": True,
        "config": config,
        "from_block": start,
        "to_block": end,
        "alerts_detected": len(new_alerts),
        "alerts_stored": len(stored),
        "new_alerts": stored,
        "real_only_note": REAL_ONLY_NOTE,
    }


def monitoring_dashboard_summary() -> dict[str, Any]:
    configs = list_monitoring_configs()
    alerts = list_monitoring_alerts(limit=250)
    open_high = [a for a in alerts if a.get("severity") in {"critical", "high"}]
    return {
        "ok": True,
        "config_count": len(configs),
        "alert_count": len(alerts),
        "high_or_critical_alerts": len(open_high),
        "recent_configs": configs[:10],
        "recent_alerts": alerts[:20],
        "status": monitoring_status(),
        "real_only_note": REAL_ONLY_NOTE,
    }
