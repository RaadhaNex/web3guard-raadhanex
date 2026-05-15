from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def make_scan_payload(module="contract", severity="high", title="Owner can withdraw without event"):
    return {
        "user_id": "phase10-user",
        "module": module,
        "project_name": "Phase 10 Project",
        "score": 62,
        "risk_label": "Medium Risk, Fix Before Launch",
        "report_id": f"phase10-{module}-scan",
        "input_hash": "phase10hash",
        "findings_count": 1,
        "critical_high_count": 1 if severity in {"critical", "high"} else 0,
        "payload": {
            "report_id": f"phase10-{module}-scan",
            "findings": [
                {
                    "id": "phase10-finding-1",
                    "module": module,
                    "severity": severity,
                    "title": title,
                    "description": "This finding is saved from a real scan payload and must be tracked manually.",
                    "confidence": "high",
                    "source": "Phase 10 Test Rule Engine",
                    "category": "access-control",
                    "business_impact": "Funds or project trust can be impacted before launch.",
                    "developer_explanation": "Add correct authorization and event logging before production.",
                    "recommendation": "Fix access control and regenerate the report.",
                    "paid_review_recommended": True,
                }
            ],
        },
    }


def test_phase10_status_is_real_only():
    response = client.get("/securescore/status")
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert "fake findings" in data["real_only_note"].lower()
    assert "Automatic code patching is not enabled" in data["manual_or_not_enabled"]


def test_phase10_saved_scan_drives_overview_and_findings_workflow():
    scan_response = client.post("/scan-history", json=make_scan_payload())
    assert scan_response.status_code == 200, scan_response.text
    scan = scan_response.json()["scan"]

    overview_response = client.get("/securescore/overview", params={"user_id": "phase10-user"})
    assert overview_response.status_code == 200, overview_response.text
    overview = overview_response.json()["overview"]
    assert overview["summary"]["saved_scans"] >= 1
    assert overview["summary"]["open_critical_high"] >= 1
    assert overview["severity_breakdown"]["high"] >= 1
    assert overview["top_open_findings"][0]["workflow_status"] == "open"

    findings_response = client.get("/findings", params={"user_id": "phase10-user", "severity": "high"})
    assert findings_response.status_code == 200, findings_response.text
    findings = findings_response.json()["findings"]
    assert any(item["id"] == "phase10-finding-1" for item in findings)

    update_response = client.patch(
        "/findings/phase10-finding-1/workflow",
        params={"user_id": "phase10-user"},
        json={"scan_id": scan["id"], "status": "fixed", "notes": "Patched and ready for re-scan."},
    )
    assert update_response.status_code == 200, update_response.text
    workflow = update_response.json()["workflow"]
    assert workflow["status"] == "fixed"

    filtered = client.get("/findings", params={"user_id": "phase10-user", "status": "fixed"})
    assert filtered.status_code == 200
    assert any(item["id"] == "phase10-finding-1" and item["workflow_status"] == "fixed" for item in filtered.json()["findings"])


def test_phase10_scan_scorecard_rejects_missing_scan():
    response = client.get("/securescore/scan/not-real", params={"user_id": "phase10-user"})
    assert response.status_code == 404
