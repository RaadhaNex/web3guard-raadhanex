from __future__ import annotations

from types import SimpleNamespace

from fastapi.testclient import TestClient

from main import app
import app.routers.database as database_router


client = TestClient(app)


def _auth_as(user_id: str):
    def fake_resolve_user_id(_request, requested_user_id=None):
        return user_id, {"mode": "test", "requested_user_id": requested_user_id, "resolved_user_id": user_id}

    return fake_resolve_user_id


def test_project_detail_uses_resolved_user_id(monkeypatch):
    seen = {}

    def fake_project_detail(user_id: str, project_id: str):
        seen["user_id"] = user_id
        seen["project_id"] = project_id
        return SimpleNamespace(model_dump=lambda: {}) if False else None

    monkeypatch.setattr(database_router, "resolve_user_id", _auth_as("user_a"))
    monkeypatch.setattr(database_router, "project_detail", fake_project_detail)

    response = client.get("/projects/project_owned_by_b?user_id=user_b")

    assert response.status_code == 404
    assert seen == {"user_id": "user_a", "project_id": "project_owned_by_b"}


def test_scan_detail_uses_resolved_user_id(monkeypatch):
    seen = {}

    def fake_get_scan(user_id: str, scan_id: str):
        seen["user_id"] = user_id
        seen["scan_id"] = scan_id
        return None

    monkeypatch.setattr(database_router, "resolve_user_id", _auth_as("user_a"))
    monkeypatch.setattr(database_router, "get_scan", fake_get_scan)

    response = client.get("/scan-history/scan_b?user_id=user_b")

    assert response.status_code == 404
    assert seen == {"user_id": "user_a", "scan_id": "scan_b"}


def test_report_detail_uses_resolved_user_id(monkeypatch):
    seen = {}

    def fake_get_report(user_id: str, report_id: str):
        seen["user_id"] = user_id
        seen["report_id"] = report_id
        return None

    monkeypatch.setattr(database_router, "resolve_user_id", _auth_as("user_a"))
    monkeypatch.setattr(database_router, "get_report", fake_get_report)

    response = client.get("/saved-reports/report_b?user_id=user_b")

    assert response.status_code == 404
    assert seen == {"user_id": "user_a", "report_id": "report_b"}
