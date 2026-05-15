from fastapi.testclient import TestClient

from main import app
from app.models.schemas import ApiKeyCreate, BugBountyProgramCreate, BugBountySubmissionCreate, RegistryPublicationCreate
from app.services.bug_bounty import bug_bounty_status, create_program, create_submission, list_submissions
from app.services.developer_api import create_api_key, developer_api_status, verify_api_key
from app.services.public_registry import create_publication, registry_status, verify_report

client = TestClient(app)


def test_bug_bounty_status_is_real_only_and_no_escrow_fake():
    status = bug_bounty_status()
    assert status["phase"] == "Mega Phase D - Phase 25 Bug Bounty Readiness + Marketplace MVP"
    assert any("No escrow" in item for item in status["not_claimed"])


def test_bug_bounty_program_and_submission_are_real_records():
    program = create_program(BugBountyProgramCreate(
        project_name="Bounty Test",
        scope_summary="Safe non destructive bounty scope for listed contracts only.",
        in_scope_assets=["contract.sol"],
        out_of_scope_assets=["DoS"],
        contact_email="security@example.com",
        authorization_confirmed=True,
        real_only_acknowledged=True,
    ), user_id="test-user")
    assert program["id"].startswith("bounty_")
    submission = create_submission(BugBountySubmissionCreate(
        program_id=program["id"],
        title="Safe triage submission",
        severity_claimed="medium",
        description="A detailed safe submission for manual triage without exploit automation.",
        authorization_confirmed=True,
        safe_testing_acknowledged=True,
        real_only_acknowledged=True,
    ))
    assert submission["id"].startswith("submission_")
    assert any(item["id"] == submission["id"] for item in list_submissions(program_id=program["id"]))


def test_bug_bounty_rejects_fake_escrow_enabled():
    response = client.post("/bug-bounty/programs", json={
        "project_name": "Fake Escrow",
        "scope_summary": "Safe scope for public assets only.",
        "escrow_enabled": True,
        "authorization_confirmed": True,
        "real_only_acknowledged": True,
    })
    assert response.status_code == 400
    assert "Escrow cannot be enabled" in response.json()["detail"]


def test_registry_publication_and_hash_verification():
    publication = create_publication(RegistryPublicationCreate(
        report_id="rep_test",
        project_name="Registry Test",
        report_hash="b" * 64,
        score=82,
        risk_label="Low Risk",
        real_only_acknowledged=True,
    ), user_id="test-user")
    assert publication["id"].startswith("reg_")
    verified = verify_report(publication["id"], "b" * 64)
    assert verified["verified"] is True
    mismatch = verify_report(publication["id"], "c" * 64)
    assert mismatch["verified"] is False


def test_registry_status_has_no_certified_claim():
    status = registry_status()
    assert any("No certified audit badge" in item for item in status["not_claimed"])


def test_developer_api_key_hash_and_rule_engine_audit_endpoint():
    created = create_api_key(ApiKeyCreate(
        name="Test API key",
        permissions=["audit:start", "registry:verify", "threat:read"],
        real_only_acknowledged=True,
    ), user_id="test-user")
    raw_key = created["api_key"]
    assert raw_key.startswith("wg_")
    record = verify_api_key(raw_key, "audit:start")
    assert record is not None
    assert "key_hash" not in created["record"]
    response = client.post("/api/v1/audit", headers={"X-Web3Guard-API-Key": raw_key}, json={
        "project_name": "API Audit",
        "solidity_code": "// SPDX-License-Identifier: MIT\npragma solidity ^0.8.20; contract A { function kill() external { selfdestruct(payable(msg.sender)); } }",
        "real_only_acknowledged": True,
    })
    assert response.status_code == 200
    data = response.json()
    assert data["mode"] == "contract_rule_engine"
    assert data["result"]["module_score"]["module"] == "contract"


def test_developer_api_endpoint_rejects_missing_key():
    response = client.post("/api/v1/audit", json={"project_name": "No Key", "real_only_acknowledged": True})
    assert response.status_code == 401


def test_developer_api_status_is_real_only():
    status = developer_api_status()
    assert "No SDK package yet" in status["not_claimed"]
