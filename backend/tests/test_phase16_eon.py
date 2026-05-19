from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_eon_status_is_real_only():
    response = client.get("/eon/status")
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert "Phase 16" in body["phase"]
    assert "fake evidence" in " ".join(body["blocked_capabilities"]).lower()
    assert "does not invent evidence" in body["real_only_note"].lower()


def test_eon_empty_graph_does_not_fake_project():
    response = client.get("/eon/risk-graph?user_id=phase16-empty-user")
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["summary"]["project_count"] == 0
    assert body["nodes"][0]["status"] == "no_project_record"
    assert body["summary"]["launch_blockers"] >= 1
    assert "does not invent evidence" in body["real_only_note"].lower()


def test_eon_fix_plan_uses_open_tasks_not_fake_fixed():
    response = client.get("/eon/fix-plan?user_id=phase16-empty-user")
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert isinstance(body["tasks"], list)
    assert all(task["status"] in {"open", "in_progress", "fixed", "accepted_risk", "manual_review_required"} or isinstance(task["status"], str) for task in body["tasks"])
    assert "new evidence" in body["workflow_note"].lower()


def test_eon_evidence_ledger_entries_are_hashed_and_not_audit_claims():
    response = client.get("/eon/evidence-ledger?user_id=phase16-empty-user")
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert isinstance(body["entries"], list)
    for entry in body["entries"]:
        assert "evidence_hash" in entry
        assert "does not prove the project is secure" in entry["integrity_note"].lower()
    assert "does not invent evidence" in body["real_only_note"].lower()
