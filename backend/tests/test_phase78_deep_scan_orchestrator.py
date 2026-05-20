from app.models.schemas import UnifiedUrlScanRequest
from app.services.deep_scan_orchestrator import build_deep_scan_orchestrator


def make_payload(**kwargs):
    data = {
        "website_url": "https://example.com",
        "authorization_confirmed": True,
        "real_only_acknowledged": True,
    }
    data.update(kwargs)
    return UnifiedUrlScanRequest(**data)


def test_quick_mode_requires_no_deep_evidence():
    payload = make_payload(scan_mode="quick")
    package = build_deep_scan_orchestrator(payload, module_cards=[], surface_hints={})
    assert package["requested_mode"] == "quick"
    assert package["summary"]["auto_run_count"] >= 4
    assert "URL + permission" in package["summary"]["user_message"]
    assert any(step["state"].startswith("Needs GitHub") for step in package["deep_scan_steps"])


def test_deep_mode_detects_supplied_repo_api_contract():
    payload = make_payload(
        scan_mode="deep",
        github_repo_url="https://github.com/org/repo",
        api_base_url="https://api.example.com",
        solidity_code="contract Demo {}",
    )
    package = build_deep_scan_orchestrator(payload, module_cards=[], surface_hints={})
    assert package["recommended_mode"] == "deep"
    assert package["summary"]["evidence_ready_count"] >= 3


def test_expert_mode_detects_artifacts_and_does_not_claim_audit():
    payload = make_payload(scan_mode="expert", slither_json='{"results":{"detectors":[]}}', har_json='{"log":{"entries":[]}}')
    package = build_deep_scan_orchestrator(payload, module_cards=[], surface_hints={})
    assert package["recommended_mode"] == "expert"
    assert any("certified audit" in boundary.lower() for boundary in package["safe_boundaries"])
