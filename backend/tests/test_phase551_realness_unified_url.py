import asyncio

from fastapi.testclient import TestClient

from main import app
from app.services import scan_website as website_service
from app.services import unified_url_scan as unified_service
from app.services.rate_limit import reset_rate_limits_for_tests
from app.services.scan_website import SafeFetchResult

client = TestClient(app)


def test_feature_status_matrix_endpoint_is_real_only():
    response = client.get("/scan/feature-status")
    assert response.status_code == 200
    data = response.json()
    assert "Real-only" in data["rule"]
    assert any(item["status"] == "Live" for item in data["features"])
    assert any("not" in item["not_claimed"].lower() for item in data["features"])


def test_unified_url_endpoint_requires_real_only_acknowledgement():
    reset_rate_limits_for_tests()
    response = client.post(
        "/scan/unified-url",
        json={
            "website_url": "https://example.com",
            "project_name": "No Acknowledgement",
            "authorization_confirmed": True,
            "real_only_acknowledged": False,
        },
    )
    assert response.status_code == 400
    assert "Real-only" in response.json()["detail"]


def test_unified_url_scan_marks_missing_modules_not_assessed(monkeypatch):
    async def fake_safe_fetch(client, method, url, *, read_body, max_redirects=5):
        if url.endswith("/robots.txt") or url.endswith("/sitemap.xml"):
            return SafeFetchResult(url=url, status_code=200, headers={})
        for path in website_service.LIMITED_PATH_HINTS:
            if url.endswith(path):
                return SafeFetchResult(url=url, status_code=404, headers={})
        return SafeFetchResult(
            url="https://launch.example/",
            status_code=200,
            headers={"content-type": "text/html; charset=utf-8", "x-content-type-options": "nosniff"},
            body_text="""
              <html><head><script src="https://cdn.example/walletconnect.js"></script></head>
              <body>Connect wallet to mint and claim tokens from 0x1111111111111111111111111111111111111111</body></html>
            """,
            elapsed_ms=10,
        )

    monkeypatch.setattr(website_service, "_safe_fetch", fake_safe_fetch)
    monkeypatch.setattr(website_service, "validate_public_http_url", lambda raw_url: raw_url.strip())
    monkeypatch.setattr(unified_service, "validate_public_http_url", lambda raw_url: raw_url.strip())

    result = asyncio.run(unified_service.run_unified_url_scan(unified_service.UnifiedUrlScanRequest(
        website_url="https://launch.example",
        project_name="Launch Example",
        authorization_confirmed=True,
        real_only_acknowledged=True,
    )))

    cards = {card["module"]: card for card in result["module_cards"]}
    assert cards["website"]["assessed"] is True
    assert cards["website"]["status"] == "Live"
    assert cards["contract"]["score"] is None
    assert cards["contract"]["status"] == "Not assessed"
    assert cards["api"]["status"] == "Not assessed"
    assert cards["wallet"]["status"] == "Manual input required"
    assert "walletconnect" in result["surface_hints"]["dapp_from_homepage"]["keyword_hits"]
    assert result["surface_hints"]["dapp_from_homepage"]["visible_evm_addresses"]
    assert result["overall_score"] is None
    assert "fake" in result["realness_rule"].lower()
