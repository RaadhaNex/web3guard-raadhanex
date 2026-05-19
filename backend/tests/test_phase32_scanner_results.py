from fastapi.testclient import TestClient

from app.core.config import settings
from main import app

client = TestClient(app)


def test_phase32_status_keeps_real_only_boundaries():
    response = client.get("/scanner-results/status")
    assert response.status_code == 200
    data = response.json()
    assert data["version"] == "web3guard-scanner-result-engine-v32.0"
    assert "Tool Not Installed" in data["safe_statuses"]
    assert any("certified audit" in item.lower() for item in data["not_claimed"])
    assert any("private key" in item.lower() for item in data["not_claimed"])


def test_phase32_evaluate_without_live_lookup_does_not_fake_findings():
    response = client.post(
        "/scanner-results/evaluate",
        json={
            "project_name": "Pilot Token",
            "package_json": '{"dependencies":{"lodash":"^4.17.21"}}',
            "run_static_tools": False,
            "live_dependency_lookup": False,
            "real_only_acknowledged": True,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["overall_status"] == "Not assessed yet"
    assert data["summary"]["real_findings_count"] == 0
    assert data["dependency_intelligence"]["status"] == "Not assessed yet"
    assert any(item["status"] == "Not assessed yet" for item in data["not_assessed_modules"])
    assert "certified audit" in data["disclaimer"].lower()


def test_phase32_imported_slither_json_is_marked_as_imported_evidence():
    slither_json = {
        "success": True,
        "results": {
            "detectors": [
                {
                    "check": "reentrancy-eth",
                    "impact": "High",
                    "description": "Potential reentrancy in withdraw()",
                    "elements": [{"source_mapping": {"lines": [42]}}],
                }
            ]
        },
    }
    response = client.post(
        "/scanner-results/evaluate",
        json={
            "project_name": "Slither Import",
            "slither_json": slither_json,
            "run_static_tools": False,
            "live_dependency_lookup": False,
            "real_only_acknowledged": True,
        },
    )
    assert response.status_code == 422  # pydantic requires JSON string, not object

    import json

    response = client.post(
        "/scanner-results/evaluate",
        json={
            "project_name": "Slither Import",
            "slither_json": json.dumps(slither_json),
            "run_static_tools": False,
            "live_dependency_lookup": False,
            "real_only_acknowledged": True,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["overall_status"] == "Assessed"
    assert data["summary"]["real_findings_count"] == 1
    assert data["findings"][0]["source"] == "Slither user-supplied JSON output"
    assert "Imported" in data["evidence"][1]["source"]


def test_phase32_static_tools_requested_without_installation_stays_not_assessed(monkeypatch):
    monkeypatch.setattr(settings, "static_analysis_enabled", False)
    response = client.post(
        "/scanner-results/evaluate",
        json={
            "project_name": "No Fake Static",
            "solidity_code": "pragma solidity ^0.8.20; contract A { function x() external {} }",
            "run_static_tools": True,
            "tools": ["slither"],
            "live_dependency_lookup": False,
            "real_only_acknowledged": True,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["summary"]["tool_findings_count"] == 0
    assert any(item["module"] == "static_analysis.slither" for item in data["not_assessed_modules"])
    assert data["static_analysis"]["real_finding_count"] == 0


def test_phase32_pilot_report_preserves_limitations_and_safe_wording():
    result_response = client.post(
        "/scanner-results/evaluate",
        json={"project_name": "Report Project", "live_dependency_lookup": False, "real_only_acknowledged": True},
    )
    result = result_response.json()
    response = client.post("/scanner-results/pilot-report", json={"result": result, "real_only_acknowledged": True})
    assert response.status_code == 200
    data = response.json()
    assert data["report_type"] == "pilot_pre_audit_readiness_report"
    assert "certified audit" in " ".join(data["limitations"]).lower()
    assert "100% secure" in data["safe_wording"]["blocked"]
    assert data["report_hash"]


def test_phase32_requires_real_only_acknowledgement():
    response = client.post("/scanner-results/evaluate", json={"real_only_acknowledged": False})
    assert response.status_code == 400
