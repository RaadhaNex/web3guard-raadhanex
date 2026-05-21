from fastapi.testclient import TestClient

from app.core.config import settings
from app.services import professional_production_qa_u as qa
from main import app

client = TestClient(app)


def test_phase_u_status_and_core_routes(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "professional_production_qa_runs_file", str(tmp_path / "qa_runs.jsonl"))
    for path in [
        "/professional-production-qa/status",
        "/professional-production-qa/local-test-plan",
        "/professional-production-qa/live-smoke-checklist",
        "/professional-production-qa/release-checklist",
        "/professional-production-qa/competitor-position",
        "/professional-production-qa/launch-decision",
        "/professional-production-qa/runs",
    ]:
        response = client.get(path)
        assert response.status_code == 200
        assert response.json()["ok"] is True


def test_phase_u_competitor_position_is_honest():
    result = qa.competitor_position()
    assert result["scores_out_of_100"]["pre_audit_readiness_product"] >= 70
    assert result["scores_out_of_100"]["full_certified_audit_company"] < 50
    assert "CertiK replacement" in result["blocked_public_positioning"]
    assert "certified audit equivalent" in result["blocked_public_positioning"]


def test_phase_u_records_manual_qa_run_and_blocks_unsafe_claim(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "professional_production_qa_runs_file", str(tmp_path / "qa_runs.jsonl"))
    result = qa.record_qa_run({
        "project_name": "Web3Guard AI",
        "overall_status": "passed",
        "checked_by": "tester",
        "summary": "This is not a certified audit and does not replace CertiK.",
        "checks": [{"name": "backend_pytest", "status": "pass"}],
    })
    assert result["ok"] is True
    assert result["run"]["overall_status"] == "passed"
    assert result["run"]["blocked_claims"] == []

    blocked = qa.record_qa_run({
        "project_name": "Unsafe Claim Test",
        "summary": "This replaces CertiK and is 100% secure.",
        "checks": [{"name": "claim_review", "status": "pass"}],
    })
    assert blocked["run"]["overall_status"] == "failed"
    assert "100% secure" in blocked["run"]["blocked_claims"]
    assert "replaces certik" in blocked["run"]["blocked_claims"]

    runs = qa.list_qa_runs()
    assert runs["count"] == 2


def test_phase_u_launch_decision_requires_qa_run(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "professional_production_qa_runs_file", str(tmp_path / "qa_runs.jsonl"))
    decision = qa.launch_decision()
    assert decision["certified_audit_claim_allowed"] is False
    assert decision["direct_competition_public_claim_allowed"] is False
    assert any(item["key"] == "qa_run" for item in decision["blockers"])


def test_phase_u_api_records_run(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "professional_production_qa_runs_file", str(tmp_path / "qa_runs.jsonl"))
    response = client.post("/professional-production-qa/runs", json={
        "project_name": "API QA",
        "environment": "production",
        "overall_status": "passed_with_warnings",
        "checked_by": "api-test",
        "summary": "Manual QA evidence recorded.",
        "checks": [{"name": "frontend_build", "status": "warning"}],
    })
    assert response.status_code == 200
    assert response.json()["run"]["overall_status"] == "passed_with_warnings"
    listed = client.get("/professional-production-qa/runs")
    assert listed.status_code == 200
    assert listed.json()["count"] == 1
