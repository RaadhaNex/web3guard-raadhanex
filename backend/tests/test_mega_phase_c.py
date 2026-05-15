from fastapi.testclient import TestClient

from main import app
from app.services.monitoring_lite import create_monitoring_config, ingest_monitoring_alert, monitoring_status, run_rpc_monitoring_check
from app.services.threat_intel import create_threat_intel_entry, list_threat_intel, threat_intel_status
from app.models.schemas import MonitoringAlertIngest, MonitoringConfigCreate, ThreatIntelCreate

client = TestClient(app)


def test_monitoring_status_is_real_only_and_disabled_by_default():
    status = monitoring_status()
    assert status["phase"] == "Mega Phase C - Phase 23 Monitoring Lite"
    assert status["monitoring_enabled"] is False
    assert "does not fabricate" in status["real_only_note"]


def test_monitoring_config_and_manual_alert_are_real_records():
    config = create_monitoring_config(MonitoringConfigCreate(
        project_name="Monitor Demo",
        contract_address="0x" + "a" * 40,
        chain="ethereum",
        authorization_confirmed=True,
        real_only_acknowledged=True,
    ))
    assert config["id"].startswith("mon_")
    alert = ingest_monitoring_alert(MonitoringAlertIngest(
        config_id=config["id"],
        event_type="owner_changed",
        severity="high",
        description="Manual review saw owner transfer transaction.",
        source="manual_admin",
        real_only_acknowledged=True,
    ))
    assert alert["source"] == "manual_admin"
    assert alert["config_id"] == config["id"]


def test_monitoring_rpc_check_returns_not_run_without_env():
    config = create_monitoring_config(MonitoringConfigCreate(
        project_name="RPC Disabled",
        contract_address="0x" + "b" * 40,
        chain="ethereum",
    ))
    result = run_rpc_monitoring_check(config["id"])
    assert result["ran"] is False
    assert "No fake" in result["reason"]


def test_monitoring_endpoints_require_authorization_and_real_only():
    response = client.post("/monitoring/configs", json={
        "project_name": "Bad",
        "contract_address": "0x" + "c" * 40,
        "chain": "ethereum",
        "authorization_confirmed": False,
        "real_only_acknowledged": True,
    })
    assert response.status_code == 400
    response = client.post("/monitoring/configs", json={
        "project_name": "Bad",
        "contract_address": "0x" + "c" * 40,
        "chain": "ethereum",
        "authorization_confirmed": True,
        "real_only_acknowledged": False,
    })
    assert response.status_code == 400


def test_threat_intel_status_and_feed_are_manual_curated():
    status = threat_intel_status()
    assert status["phase"] == "Mega Phase C - Phase 24 Threat Intelligence Feed"
    assert status["live_sources_enabled"] is False
    feed = list_threat_intel(project_type="Token", tags=["approval"], limit=10)
    assert feed["items"]
    assert "does not claim real-time" in feed["real_only_note"]


def test_threat_intel_manual_entry_create_and_filter():
    entry = create_threat_intel_entry(ThreatIntelCreate(
        title="Manual approval-risk note",
        category="wallet_drainer",
        severity="high",
        summary="A manually curated note about risky approvals for launch review.",
        affected_project_types=["Token"],
        relevance_tags=["approval", "spender"],
        source_label="Manual test source",
        real_only_acknowledged=True,
    ))
    assert entry["id"].startswith("threat_")
    feed = list_threat_intel(project_type="Token", tags=["spender"], limit=10)
    assert any(item["id"] == entry["id"] for item in feed["items"])


def test_threat_intel_endpoint_creates_manual_entry():
    response = client.post("/threat-intel/admin/entries", json={
        "title": "Endpoint manual threat note",
        "category": "admin_opsec",
        "severity": "medium",
        "summary": "A manually curated endpoint threat entry with real-only acknowledgement.",
        "affected_project_types": ["DAO"],
        "relevance_tags": ["timelock", "multisig"],
        "source_label": "Manual endpoint test",
        "real_only_acknowledged": True,
    })
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "manual_curated"
