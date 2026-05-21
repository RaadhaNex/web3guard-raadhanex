from __future__ import annotations

from app.services import professional_direct_level_k as phase_k


def test_phase_k_status_and_gate_are_safe():
    status = phase_k.status()
    assert status["ok"] is True
    assert status["capabilities"]["webhook_and_snapshot_bridge"] is True
    assert status["capabilities"]["certified_audit_public_claim"] is False

    gate = phase_k.direct_competition_readiness_gate()
    assert gate["ok"] is True
    assert gate["certified_audit_public_claim_allowed"] is False
    assert gate["direct_competition_public_claim_allowed"] is False
    assert "Certified audit replacement" in gate["blocked_positioning"]


def test_phase_k_live_snapshot_is_not_faked_when_network_disabled(monkeypatch):
    monkeypatch.setattr(phase_k.settings, "professional_direct_level_network_enabled", False, raising=False)

    class Payload:
        def model_dump(self):
            return {
                "website_url": "https://example.com",
                "contract_address": "0x0000000000000000000000000000000000000000",
                "github_repo_url": "https://github.com/example/repo",
                "authorization_confirmed": True,
                "real_only_acknowledged": True,
            }

    import asyncio

    result = asyncio.run(phase_k.build_live_snapshot(Payload()))
    assert result["ok"] is True
    assert result["status"] == "not_assessed"
    assert "No fake" in result["real_only_note"]


def test_phase_k_compare_snapshots_detects_critical_contract_drift(tmp_path, monkeypatch):
    monkeypatch.setattr(phase_k.settings, "professional_webhook_events_file", str(tmp_path / "events.jsonl"), raising=False)
    baseline = {
        "snapshot_hash": "base",
        "contract": {
            "contract_address": "0x1111111111111111111111111111111111111111",
            "source_hash": "aaa",
            "implementation_address": "0x2222222222222222222222222222222222222222",
        },
        "website": {"headers_hash": "h1"},
        "github": {"tree_sha": "t1"},
    }
    current = {
        "snapshot_hash": "cur",
        "contract": {
            "contract_address": "0x1111111111111111111111111111111111111111",
            "source_hash": "bbb",
            "implementation_address": "0x3333333333333333333333333333333333333333",
        },
        "website": {"headers_hash": "h1"},
        "github": {"tree_sha": "t1"},
    }
    result = phase_k.compare_snapshots({"baseline_snapshot": baseline, "current_snapshot": current})
    assert result["drift_found"] is True
    assert result["highest_severity"] == "critical"
    keys = {event["key"] for event in result["events"]}
    assert "source_hash" in keys
    assert "implementation_address" in keys


def test_phase_k_github_webhook_flags_risky_files(tmp_path, monkeypatch):
    monkeypatch.setattr(phase_k.settings, "professional_webhook_events_file", str(tmp_path / "events.jsonl"), raising=False)
    payload = {
        "repository": {"full_name": "raad/example", "html_url": "https://github.com/raad/example"},
        "ref": "refs/heads/main",
        "before": "old",
        "after": "new",
        "commits": [
            {
                "modified": ["contracts/Vault.sol", ".github/workflows/deploy.yml", "README.md"],
                "added": ["scripts/deploy.ts"],
                "removed": [],
            }
        ],
    }
    result = phase_k.ingest_github_webhook(payload)
    event = result["event"]
    assert event["source"] == "github_webhook"
    assert event["risky_file_count"] >= 2
    assert event["severity"] == "high"


def test_phase_k_onchain_webhook_classifies_admin_events(tmp_path, monkeypatch):
    monkeypatch.setattr(phase_k.settings, "professional_webhook_events_file", str(tmp_path / "events.jsonl"), raising=False)
    payload = {
        "chain": "ethereum",
        "contract_address": "0x1111111111111111111111111111111111111111",
        "event_type": "proxy_implementation_upgrade",
        "tx_hash": "0xabc",
    }
    result = phase_k.ingest_onchain_webhook(payload)
    event = result["event"]
    assert event["source"] == "onchain_webhook"
    assert event["severity"] == "critical"
    assert event["contract_address"] == "0x1111111111111111111111111111111111111111"
