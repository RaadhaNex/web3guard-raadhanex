from fastapi.testclient import TestClient

from app.core.config import settings
from main import app

client = TestClient(app)


def test_phase31_status_compresses_visible_journey_and_keeps_boundaries():
    response = client.get("/launch-validation/status")
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["version"] == "web3guard-launch-validation-v31.0"
    assert len(data["visible_journey"]) == 7
    assert any(item["href"] == "/scanner/unified-url" for item in data["visible_journey"])
    assert "Tool Not Installed" in data["safe_missing_labels"]
    assert any("private key" in claim.lower() for claim in data["not_claimed"])


def test_phase31_slither_readiness_is_truthful_without_fake_findings():
    response = client.get("/launch-validation/slither-readiness")
    assert response.status_code == 200
    data = response.json()
    assert data["tool"] == "slither"
    assert data["status"] in {"Ready", "Tool Not Installed"}
    assert "pip install slither-analyzer" in data["render_build_command"]
    assert data["safety_boundaries"]["fake_findings"] is False
    assert "Missing binary" in data["real_only_note"] or "real binary" in data["real_only_note"]


def test_phase31_razorpay_readiness_never_marks_paid_without_env():
    response = client.get("/launch-validation/razorpay-readiness")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in {"Ready", "Needs API Key"}
    assert "RAZORPAY_KEY_ID" in data["missing_env"] or data["key_id_masked"]
    assert any("Subscription active" in item for item in data["never_claim"])


def test_phase31_dependency_intel_parses_package_json_without_live_lookup():
    response = client.post(
        "/launch-validation/dependency-intel",
        json={
            "package_json": '{"dependencies":{"lodash":"^4.17.21"},"devDependencies":{"next":"16.2.6"}}',
            "live_lookup": False,
            "real_only_acknowledged": True,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "Not assessed yet"
    assert data["package_count"] == 2
    assert data["osv_results"] == []
    assert "No fake" in data["real_only_note"]


def test_phase31_dependency_intel_requires_real_only_acknowledgement():
    response = client.post(
        "/launch-validation/dependency-intel",
        json={"packages": [{"name": "lodash", "version": "4.17.21"}], "real_only_acknowledged": False},
    )
    assert response.status_code == 400


def test_phase31_dependency_intel_live_lookup_disabled_returns_provider_not_configured(monkeypatch):
    monkeypatch.setattr(settings, "launch_validation_network_enabled", False)
    monkeypatch.setattr(settings, "provider_live_network_enabled", True)
    response = client.post(
        "/launch-validation/dependency-intel",
        json={"packages": [{"name": "lodash", "version": "4.17.21"}], "live_lookup": True, "real_only_acknowledged": True},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "Provider Not Configured"
    assert data["cisa_kev_matches"] == []
