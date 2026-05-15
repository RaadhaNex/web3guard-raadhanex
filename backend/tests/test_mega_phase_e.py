from fastapi.testclient import TestClient

from main import app
from app.models.schemas import CiConfigValidateRequest, CiTemplateRequest, LearningProgressCreate
from app.services.admin_super_panel import admin_super_dashboard, admin_super_status, system_health_snapshot, upsert_feature_flag, list_audit_logs
from app.services.cicd import cicd_status, render_template, validate_ci_config
from app.services.learning_center import create_progress, get_lesson, learning_status, list_lessons, list_progress

client = TestClient(app)


def test_cicd_status_and_template_are_real_only():
    status = cicd_status()
    assert status["phase"].startswith("Mega Phase E")
    assert any("No fake CI" in item for item in status["not_claimed"])
    tpl = render_template(CiTemplateRequest(api_base_url="http://localhost:8000", fail_on="critical"))
    assert "WEB3GUARD_API_KEY" in tpl["workflow_yml"]
    assert "scan.py" in tpl["script_path"]
    assert "private keys" in tpl["scan_py"].lower()


def test_cicd_validation_flags_hardcoded_private_key():
    result = validate_ci_config(CiConfigValidateRequest(config_text="PRIVATE_KEY=abc\nname: bad"))
    assert result["valid"] is False
    assert any(f["severity"] == "critical" for f in result["findings"])


def test_learning_center_lessons_and_progress_are_real_records():
    status = learning_status()
    assert status["lesson_count"] >= 5
    lessons = list_lessons(language="hinglish")
    assert lessons
    lesson = get_lesson(lessons[0]["id"])
    assert lesson is not None
    progress = create_progress(LearningProgressCreate(lesson_id=lesson["id"], status="completed"), user_id="test-user")
    assert progress["id"].startswith("learn_")
    assert any(row["id"] == progress["id"] for row in list_progress(user_id="test-user"))


def test_learning_endpoint_rejects_unknown_lesson():
    response = client.post("/learning/progress", json={"lesson_id": "missing-lesson", "status": "completed", "real_only_acknowledged": True})
    assert response.status_code == 404


def test_admin_super_dashboard_is_real_only_and_admin_protected():
    no_token = client.get("/admin/super/dashboard")
    assert no_token.status_code in {401, 403}
    status = admin_super_status()
    assert status["requires_admin_token"] is True
    assert any("No fake MRR" in item for item in status["not_claimed"])
    dashboard = admin_super_dashboard()
    assert "totals" in dashboard
    assert "verified_revenue_inr" in dashboard["revenue"]
    health = system_health_snapshot()
    assert "storage" in health


def test_admin_feature_flag_and_audit_log_record():
    flag = upsert_feature_flag("test_phase_e", True, "enabled in test", actor="pytest")
    assert flag["enabled"] is True
    logs = list_audit_logs()
    assert any(item.get("target_id") == flag["id"] for item in logs)


def test_mega_phase_e_routes_status():
    assert client.get("/cicd/status").status_code == 200
    assert client.get("/learning/status").status_code == 200
