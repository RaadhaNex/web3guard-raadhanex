from fastapi.testclient import TestClient

from main import app
from app.core import config

client = TestClient(app)


def _local_workspace(tmp_path, monkeypatch):
    monkeypatch.setattr(config.settings, "db_profiles_file", str(tmp_path / "profiles.jsonl"))
    monkeypatch.setattr(config.settings, "db_projects_file", str(tmp_path / "projects.jsonl"))
    monkeypatch.setattr(config.settings, "db_scan_history_file", str(tmp_path / "scans.jsonl"))
    monkeypatch.setattr(config.settings, "db_saved_reports_file", str(tmp_path / "reports.jsonl"))
    monkeypatch.setattr(config.settings, "db_organizations_file", str(tmp_path / "organizations.jsonl"))
    monkeypatch.setattr(config.settings, "db_org_members_file", str(tmp_path / "org_members.jsonl"))
    monkeypatch.setattr(config.settings, "db_finding_tasks_file", str(tmp_path / "finding_tasks.jsonl"))
    monkeypatch.setattr(config.settings, "db_workspace_comments_file", str(tmp_path / "workspace_comments.jsonl"))
    monkeypatch.setattr(config.settings, "db_workspace_activity_file", str(tmp_path / "workspace_activity.jsonl"))


def test_phase72_create_workspace_invite_task_comment_flow(tmp_path, monkeypatch):
    _local_workspace(tmp_path, monkeypatch)

    org_response = client.post("/organizations", json={
        "user_id": "owner-72",
        "name": "RAADHANEX Web3Guard Workspace",
        "website_url": "https://raadhanex.example",
        "billing_email": "billing@example.com",
        "notes": "Real workspace test",
    })
    assert org_response.status_code == 200
    organization = org_response.json()["organization"]
    assert organization["owner_user_id"] == "owner-72"

    member_response = client.post(f"/organizations/{organization['id']}/members?user_id=owner-72", json={
        "email": "reviewer@example.com",
        "full_name": "Security Reviewer",
        "role": "reviewer",
        "status": "invited",
        "note": "Manual invite record only; no fake email sent.",
    })
    assert member_response.status_code == 200
    member = member_response.json()["member"]
    assert member["status"] == "invited"

    task_response = client.post("/workspace/finding-tasks", json={
        "user_id": "owner-72",
        "organization_id": organization["id"],
        "title": "Fix owner-only mint centralization disclosure",
        "module": "contract",
        "severity": "high",
        "status": "open",
        "assigned_to_member_id": member["id"],
        "recommendation": "Move admin power to multisig/timelock before launch.",
    })
    assert task_response.status_code == 200
    task = task_response.json()["task"]
    assert task["severity"] == "high"

    comment_response = client.post("/workspace/comments", json={
        "user_id": "owner-72",
        "organization_id": organization["id"],
        "finding_task_id": task["id"],
        "body": "Reviewer assigned. This is a real saved workspace comment.",
    })
    assert comment_response.status_code == 200

    overview_response = client.get(f"/organizations/{organization['id']}?user_id=owner-72")
    assert overview_response.status_code == 200
    overview = overview_response.json()["workspace"]
    assert overview["totals"]["members"] == 2
    assert overview["totals"]["finding_tasks"] == 1
    assert overview["totals"]["comments"] == 1
    assert "fake" in overview["real_only_note"].lower()


def test_phase72_role_gates_workspace_updates(tmp_path, monkeypatch):
    _local_workspace(tmp_path, monkeypatch)
    org = client.post("/organizations", json={"user_id": "owner-gate", "name": "Gate Workspace"}).json()["organization"]

    blocked = client.post(f"/organizations/{org['id']}/members?user_id=random-user", json={
        "email": "blocked@example.com",
        "role": "viewer",
    })
    assert blocked.status_code == 403

    invited = client.post(f"/organizations/{org['id']}/members?user_id=owner-gate", json={
        "user_id": "member-gate",
        "email": "member@example.com",
        "role": "member",
        "status": "active",
    })
    assert invited.status_code == 200

    task = client.post("/workspace/finding-tasks", json={
        "user_id": "member-gate",
        "organization_id": org["id"],
        "title": "Member can create remediation task",
        "module": "wallet",
    })
    assert task.status_code == 200

    task_id = task.json()["task"]["id"]
    update = client.patch(f"/workspace/finding-tasks/{task_id}?organization_id={org['id']}&user_id=member-gate", json={"status": "in_progress"})
    assert update.status_code == 200
    assert update.json()["task"]["status"] == "in_progress"


def test_phase72_qa_lists_workspace_routes():
    routes = client.get("/qa/frontend-routes").json()["routes"]
    assert "/dashboard/workspace" in routes
    endpoints = client.get("/qa/backend-endpoints").json()["endpoints"]
    assert any(endpoint["path"] == "/workspace/status" for endpoint in endpoints)
    assert any(endpoint["path"] == "/organizations" for endpoint in endpoints)
