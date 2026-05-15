from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_notifications_status_and_dry_run_event():
    status = client.get("/notifications/status").json()
    assert status["ok"] is True
    assert "providers" in status
    res = client.post("/notifications/send", json={
        "event_type": "critical_finding",
        "channels": ["manual", "email"],
        "title": "Critical finding preview",
        "message": "Review finding before launch.",
        "severity": "high",
        "dry_run": True,
        "real_only_acknowledged": True,
    })
    assert res.status_code == 200
    event = res.json()["event"]
    assert event["delivery_results"][0]["status"] == "dry_run_preview"
    assert "payload_hash" in event


def test_compliance_scanner_flags_missing_policies():
    res = client.post("/compliance/scan", json={
        "project_name": "Token launch",
        "project_type": "token",
        "jurisdictions": ["general_web3", "india_vda", "gdpr"],
        "collects_personal_data": True,
        "handles_payments_in_inr": True,
        "real_only_acknowledged": True,
    })
    assert res.status_code == 200
    report = res.json()["report"]
    assert report["score"] < 100
    assert report["not_legal_advice"] is True
    assert any("Privacy" in f["title"] for f in report["findings"])
    assert any("GST" in f["title"] for f in report["findings"])


def test_cross_chain_evm_detects_replay_and_bridge_review():
    res = client.post("/cross-chain/scan", json={
        "chain_family": "evm",
        "chains": ["ethereum", "polygon"],
        "source_code": "contract X { function lzReceive(bytes calldata payload) external {} function verify(bytes memory signature) external {} }",
        "real_only_acknowledged": True,
    })
    assert res.status_code == 200
    scan = res.json()["scan"]
    assert scan["score"] < 100
    titles = [f["title"] for f in scan["findings"]]
    assert any("Chain ID" in t or "replay" in t for t in titles)
    assert any("message" in t.lower() for t in titles)


def test_cross_chain_non_evm_manual_review_required():
    res = client.post("/cross-chain/scan", json={
        "chain_family": "solana_anchor",
        "chains": ["solana"],
        "notes": "PDA seeds used but no bump shown",
        "real_only_acknowledged": True,
    })
    assert res.status_code == 200
    scan = res.json()["scan"]
    assert scan["manual_review_required"] is True
