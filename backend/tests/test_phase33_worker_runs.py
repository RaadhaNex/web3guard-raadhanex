from fastapi.testclient import TestClient

from app.core.config import settings
from main import app

client = TestClient(app)


def test_phase33_worker_run_status_real_only_boundaries():
    response = client.get("/worker-runs/status")
    assert response.status_code == 200
    data = response.json()
    assert data["version"] == "web3guard-real-worker-run-engine-v33.0"
    assert data["safety_boundaries"]["no_fake_findings"] is True
    assert data["safety_boundaries"]["no_private_key_collection"] is True
    assert data["safety_boundaries"]["no_wallet_signing"] is True
    assert "Tool Not Installed" in data["safe_status_labels"]
    assert "certified audit" in " ".join(data["blocked_claims"]).lower()


def test_phase33_manifest_keeps_missing_tools_status_only():
    response = client.post(
        "/worker-runs/manifest",
        json={
            "project_name": "Manifest Project",
            "tools": ["slither", "semgrep", "mythril"],
            "real_only_acknowledged": True,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert [step["tool"] for step in data["steps"]] == ["slither", "semgrep", "mythril"]
    assert all("Do not invent findings" in step["when_missing"] for step in data["steps"])
    assert "No fake scanner output" in data["blocked_actions"]


def test_phase33_static_worker_plan_only_does_not_execute_or_fake():
    response = client.post(
        "/worker-runs/static",
        json={
            "project_name": "Plan Only",
            "source_code": "pragma solidity ^0.8.20; contract A { function x() external {} }",
            "tools": ["slither"],
            "execute": False,
            "real_only_acknowledged": True,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["mode"] == "plan_only"
    assert data["real_findings_count"] == 0
    assert data["findings"] == []
    assert "no subprocess" in data["note"].lower()


def test_phase33_static_worker_disabled_env_stays_not_assessed(monkeypatch):
    monkeypatch.setattr(settings, "static_analysis_enabled", False)
    response = client.post(
        "/worker-runs/static",
        json={
            "project_name": "No Fake Static",
            "source_code": "pragma solidity ^0.8.20; contract A { function x() external {} }",
            "tools": ["slither"],
            "execute": True,
            "real_only_acknowledged": True,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["real_findings_count"] == 0
    assert data["status"] == "Not assessed yet"
    assert data["findings"][0]["kind"] == "tool_status"


def test_phase33_import_mythril_json_normalizes_imported_evidence():
    mythril_json = {
        "issues": [
            {
                "title": "External Call To User-Supplied Address",
                "severity": "High",
                "swc-id": "SWC-107",
                "description": "Potential reentrancy-style call risk.",
            }
        ]
    }
    import json

    response = client.post(
        "/worker-runs/import-json",
        json={
            "tool": "mythril",
            "tool_json": json.dumps(mythril_json),
            "generated_by_web3guard_worker": False,
            "real_only_acknowledged": True,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["tool"] == "mythril"
    assert data["status"] == "Assessed"
    assert data["real_findings_count"] == 1
    assert data["findings"][0]["severity"] == "high"
    assert data["findings"][0]["evidence_mode"] == "imported_worker_evidence"
    assert "Imported tool JSON" in data["findings"][0]["limitation"]


def test_phase33_rejects_secret_like_source_input():
    response = client.post(
        "/worker-runs/static",
        json={
            "source_code": "PRIVATE_KEY='abc1234567890abc1234567890'",
            "execute": True,
            "real_only_acknowledged": True,
        },
    )
    assert response.status_code == 400
    assert "private key" in response.json()["detail"].lower()


def test_phase33_requires_real_only_acknowledgement():
    response = client.post(
        "/worker-runs/manifest",
        json={"tools": ["slither"], "real_only_acknowledged": False},
    )
    assert response.status_code == 400
