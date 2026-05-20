from app.services.static_analysis_artifacts import analyze_static_artifacts, static_artifact_status
from fastapi.testclient import TestClient
from main import app


def test_static_artifact_status_blocks_fake_claims():
    status = static_artifact_status()
    assert status["ok"] is True
    assert "slither" in status["supported_artifacts"]
    assert any("No fake" in claim for claim in status["blocked_claims"])


def test_parse_slither_json_artifact_as_real_static_evidence():
    slither_json = '''{
      "success": true,
      "results": {
        "detectors": [
          {
            "check": "reentrancy-eth",
            "impact": "High",
            "description": "Potential reentrancy detected in withdraw().",
            "elements": [{"source_mapping": {"lines": [42]}}]
          }
        ]
      }
    }'''
    report = analyze_static_artifacts(slither_json=slither_json, project_name="Artifact Demo")
    assert report is not None
    assert report.module_score.assessed is True
    assert report.findings[0].source == "User-Supplied Slither JSON Artifact"
    assert report.findings[0].severity == "high"
    assert report.findings[0].affected_line == 42
    assert report.scan_metadata["artifact_runs"]["slither"]["state"] == "User Artifact Parsed"
    assert "does not claim independent backend execution" in report.scan_metadata["real_only_note"]


def test_invalid_artifact_stays_status_not_fake_bug():
    report = analyze_static_artifacts(semgrep_json="not-json", project_name="Invalid Demo")
    assert report is not None
    assert report.module_score.assessed is False
    assert report.findings[0].category == "tool_status"
    assert report.findings[0].severity == "info"
    assert "Invalid JSON artifact" in report.findings[0].description


def test_static_artifact_parse_endpoint():
    client = TestClient(app)
    response = client.post("/static-artifact/parse", json={
        "project_name": "Endpoint Demo",
        "semgrep_json": '{"results":[{"check_id":"solidity.reentrancy","start":{"line":7},"extra":{"severity":"ERROR","message":"Pattern found","lines":"call.value()"}}]}',
        "real_only_acknowledged": True,
    })
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["findings_count"] == 1
    assert data["findings"][0]["source"] == "User-Supplied Semgrep JSON Artifact"
    assert "does not fake backend tool execution" in data["real_only_rule"].lower()
