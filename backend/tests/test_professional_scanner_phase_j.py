from types import SimpleNamespace

from fastapi.testclient import TestClient

from main import app
from app.services.professional_monitoring_j import build_monitoring_fingerprint, compare_fingerprints, create_baseline


def test_phase_j_fingerprint_builds_from_scan_result():
    evidence = {
        "website": {"url": "https://example.com", "headers": {"content-security-policy": True, "strict-transport-security": True}, "score": 90},
        "contract": {"chain": "ethereum", "contract_address": "0xabc", "source_hash": "src1"},
        "github": {"repo_url": "https://github.com/acme/protocol", "commit_hash": "abc123"},
        "scan_result": {"findings": [{"title": "A", "severity": "high"}]},
    }
    fp = build_monitoring_fingerprint(evidence)
    assert fp["fingerprint_hash"]
    assert fp["website"]["headers"]["content-security-policy"] is True
    assert fp["contract"]["contract_address"] == "0xabc"
    assert fp["findings"]["critical_high"] == 1


def test_phase_j_compare_detects_contract_and_header_drift():
    baseline = {
        "id": "pmjbase_test",
        "user_id": "u1",
        "project_id": "p1",
        "project_name": "Project",
        "fingerprint": build_monitoring_fingerprint({
            "website": {"url": "https://example.com", "headers": {"content-security-policy": True, "strict-transport-security": True}, "score": 95},
            "contract": {"chain": "ethereum", "contract_address": "0xabc", "proxy_implementation": "0ximpl1", "admin_owner": "0xowner1", "source_hash": "h1"},
            "scan_result": {"findings": []},
        }),
    }
    current = build_monitoring_fingerprint({
        "website": {"url": "https://example.com", "headers": {"content-security-policy": False, "strict-transport-security": True}, "score": 80},
        "contract": {"chain": "ethereum", "contract_address": "0xabc", "proxy_implementation": "0ximpl2", "admin_owner": "0xowner2", "source_hash": "h2"},
        "scan_result": {"findings": [{"title": "Reentrancy", "severity": "critical"}]},
    })
    events = compare_fingerprints(baseline, current)
    types = {event["drift_type"] for event in events}
    assert "security_header_removed" in types
    assert "proxy_implementation_changed" in types
    assert "admin_owner_changed" in types
    assert "source_hash_changed" in types
    assert "critical_high_count_increased" in types


def test_phase_j_create_baseline_requires_authorization():
    payload = SimpleNamespace(
        user_id="u1",
        project_id="p1",
        project_name="Project",
        baseline_type="post_review",
        cadence="manual",
        approved_report_id=None,
        proof_id=None,
        scope={},
        baseline_evidence={},
        authorization_confirmed=False,
        real_only_acknowledged=True,
    )
    try:
        create_baseline(payload)
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "Authorization" in str(exc)


def test_phase_j_api_status_and_readiness():
    client = TestClient(app)
    status = client.get("/professional-monitoring/status")
    assert status.status_code == 200
    assert status.json()["ok"] is True
    readiness = client.get("/professional-monitoring/readiness")
    assert readiness.status_code == 200
    assert readiness.json()["market_claim_allowed"] is False


def test_phase_j_api_baseline_compare_acknowledge_flow():
    client = TestClient(app)
    create = client.post("/professional-monitoring/baselines", json={
        "user_id": "phase-j-user",
        "project_id": "phase-j-project",
        "project_name": "Phase J Project",
        "baseline_evidence": {
            "website": {"url": "https://example.com", "headers": {"content-security-policy": True}, "score": 92},
            "contract": {"chain": "ethereum", "contract_address": "0xabc", "proxy_implementation": "0ximpl1"},
            "scan_result": {"findings": []},
        },
        "authorization_confirmed": True,
        "real_only_acknowledged": True,
    })
    assert create.status_code == 200, create.text
    baseline_id = create.json()["baseline"]["id"]
    compare = client.post("/professional-monitoring/compare", json={
        "baseline_id": baseline_id,
        "user_id": "phase-j-user",
        "current_evidence": {
            "website": {"url": "https://example.com", "headers": {"content-security-policy": False}, "score": 78},
            "contract": {"chain": "ethereum", "contract_address": "0xabc", "proxy_implementation": "0ximpl2"},
            "scan_result": {"findings": [{"title": "New risk", "severity": "high"}]},
        },
        "real_only_acknowledged": True,
    })
    assert compare.status_code == 200, compare.text
    body = compare.json()
    assert body["drift_detected"] is True
    assert body["drift_count"] >= 2
    event_id = body["events"][0]["id"]
    ack = client.post(f"/professional-monitoring/events/{event_id}/acknowledge", json={"status": "acknowledged", "reviewer": "qa"})
    assert ack.status_code == 200, ack.text
    assert ack.json()["event"]["status"] == "acknowledged"
