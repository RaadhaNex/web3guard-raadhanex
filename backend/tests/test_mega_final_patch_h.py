from __future__ import annotations

import hashlib
import hmac
import json

from fastapi.testclient import TestClient

import main
from app.core.config import settings
from app.models.schemas import MonitoringAlertIngest, PaymentIntent, PaymentIntentCreate
from app.services.auth_guard import auth_runtime_status
from app.services.deep_analysis_tools import deep_analysis_status, run_deep_analysis
from app.services.monitoring_lite import create_monitoring_config, ingest_monitoring_alert, monitoring_status
from app.services.payment_store import verify_checkout_signature


def test_auth_status_honest_when_supabase_missing():
    status = auth_runtime_status()
    assert status["provider"] == "supabase"
    assert status["status"] in {"Configured", "Provider Not Configured"}
    assert "fake session" in status["real_only_note"].lower()


def test_mythril_is_worker_gated_by_default():
    status = deep_analysis_status()
    mythril = status["tools"]["mythril"]
    assert mythril["worker_status"]["worker_required"] is True
    assert mythril["worker_status"]["mode"] in {"docker_worker_required", "local_explicitly_allowed"}


def test_deep_analysis_reports_mythril_manual_not_fake_when_disabled():
    result = run_deep_analysis(
        solidity_code="pragma solidity ^0.8.20; contract A { function x() external {} }",
        project_name="Patch H",
        file_name="A.sol",
        requested_tools=["mythril"],
        scan_depth="quick",
        ownership_verified=False,
    )
    assert result.findings
    assert result.findings[0].category == "tool_status"
    assert "DEEP_ANALYSIS_ENABLED is false" in result.findings[0].description


def test_monitoring_status_names_real_rpc_methods():
    status = monitoring_status()
    assert "eth_blockNumber" in status["rpc_checks"]
    assert "eth_getLogs" in status["rpc_checks"]


def test_monitoring_rejects_unverified_webhook_source(tmp_path, monkeypatch):
    cfg_file = tmp_path / "monitoring_configs.jsonl"
    alerts_file = tmp_path / "monitoring_alerts.jsonl"
    events_file = tmp_path / "monitoring_events.jsonl"
    monkeypatch.setattr(settings, "monitoring_configs_file", str(cfg_file))
    monkeypatch.setattr(settings, "monitoring_alerts_file", str(alerts_file))
    monkeypatch.setattr(settings, "monitoring_events_file", str(events_file))
    config = create_monitoring_config(type("Payload", (), {
        "project_name": "Patch H",
        "contract_address": "0x0000000000000000000000000000000000000001",
        "chain": "ethereum",
        "watch_types": ["owner_changed"],
        "alert_channels": ["dashboard"],
        "notification_target": None,
        "ownership_verified": True,
        "notes": None,
    })())
    payload = MonitoringAlertIngest(
        config_id=config["id"],
        event_type="custom",
        severity="medium",
        description="Webhook-like alert without verified webhook endpoint",
        source="webhook",
        real_only_acknowledged=True,
    )
    try:
        ingest_monitoring_alert(payload)
    except ValueError as exc:
        assert "no fake webhook alert" in str(exc)
    else:
        raise AssertionError("Webhook source should not be accepted by manual ingest")


def test_pdf_endpoint_returns_application_pdf():
    client = TestClient(main.app)
    report = {
        "report_id": "WG-PATCH-H-TEST",
        "report_hash": "a" * 64,
        "project_name": "Patch H PDF",
        "combined": {"overall_score": None, "available_score": None, "risk_label": "Not assessed"},
        "coverage": {"assessed_count": 0, "total_modules": 6, "coverage_percent": 0, "confidence": "low"},
        "module_matrix": [],
        "priority_action_plan": [],
        "top_findings": [],
        "limitations": ["Test report only"],
        "disclaimer": "Not a certified audit.",
    }
    response = client.post("/report/export/pdf", json={"report": report})
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/pdf")
    assert response.content.startswith(b"%PDF")


def test_razorpay_signature_verification_does_not_fake_success(tmp_path, monkeypatch):
    payments_file = tmp_path / "payments.jsonl"
    events_file = tmp_path / "events.jsonl"
    subs_file = tmp_path / "subs.jsonl"
    monkeypatch.setattr(settings, "payment_intents_file", str(payments_file))
    monkeypatch.setattr(settings, "payment_events_file", str(events_file))
    monkeypatch.setattr(settings, "subscriptions_file", str(subs_file))
    monkeypatch.setattr(settings, "razorpay_key_secret", "test_secret")

    intent = PaymentIntent(
        id="pay_patch_h",
        created_at="2026-05-14T00:00:00+00:00",
        package_id="quick-risk-report",
        package_name="Quick Risk Scan Report",
        amount_inr=999,
        amount_paise=99900,
        billing_cycle="one_time",
        provider="razorpay",
        provider_preference="razorpay",
        upi_id="raadhanex@upi",
        upi_name="RAADHANEX",
        manual_verification_required=False,
        razorpay_enabled=True,
        razorpay_key_id="rzp_test_key",
        razorpay_order_id="order_patch_h",
        status="razorpay_order_created",
        note="Order only; not paid yet.",
    )
    payments_file.write_text(json.dumps(intent.model_dump(mode="json")) + "\n", encoding="utf-8")
    message = "order_patch_h|pay_real_123"
    signature = hmac.new(b"test_secret", message.encode("utf-8"), hashlib.sha256).hexdigest()
    updated = verify_checkout_signature(type("Payload", (), {
        "payment_intent_id": "pay_patch_h",
        "razorpay_order_id": "order_patch_h",
        "razorpay_payment_id": "pay_real_123",
        "razorpay_signature": signature,
    })())
    assert updated.status == "verified"

    bad = type("Payload", (), {
        "payment_intent_id": "pay_patch_h",
        "razorpay_order_id": "order_patch_h",
        "razorpay_payment_id": "pay_real_456",
        "razorpay_signature": "bad-signature",
    })()
    try:
        verify_checkout_signature(bad)
    except ValueError as exc:
        assert "Invalid Razorpay payment signature" in str(exc)
    else:
        raise AssertionError("Invalid signature must not be accepted")
