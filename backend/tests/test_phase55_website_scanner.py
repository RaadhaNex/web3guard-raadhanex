import asyncio

from fastapi.testclient import TestClient

from main import app
from app.services import scan_website as website_service
from app.services.rate_limit import reset_rate_limits_for_tests
from app.services.scan_website import SafeFetchResult, scan_website

client = TestClient(app)


def test_website_endpoint_blocks_private_internal_hosts():
    reset_rate_limits_for_tests()
    response = client.post(
        "/scan/website",
        json={"url": "http://localhost:8000", "project_name": "Unsafe", "authorization_confirmed": True},
    )
    assert response.status_code == 400
    assert "Private/internal" in response.json()["detail"]


def test_website_endpoint_requires_authorization():
    reset_rate_limits_for_tests()
    response = client.post(
        "/scan/website",
        json={"url": "https://example.com", "project_name": "No Auth", "authorization_confirmed": False},
    )
    assert response.status_code == 400
    assert "Authorization" in response.json()["detail"]


def test_passive_website_scanner_records_headers_paths_and_scripts(monkeypatch):
    async def fake_safe_fetch(client, method, url, *, read_body, max_redirects=5):
        if url.endswith("/robots.txt"):
            return SafeFetchResult(url=url, status_code=404, headers={})
        if url.endswith("/sitemap.xml"):
            return SafeFetchResult(url=url, status_code=200, headers={})
        for path in website_service.LIMITED_PATH_HINTS:
            if url.endswith(path):
                return SafeFetchResult(url=url, status_code=200 if path == "/.env" else 404, headers={})
        return SafeFetchResult(
            url="https://demo-web3guard.example/",
            status_code=200,
            headers={
                "content-type": "text/html; charset=utf-8",
                "x-content-type-options": "nosniff",
            },
            body_text="""
            <html><head>
              <script src="https://cdn.example.com/lib.js"></script>
              <script src="http://unsafe.example.com/mint.js"></script>
              <script>console.log('inline')</script>
            </head><body><form action="/claim"></form></body></html>
            """,
            redirect_chain=[{"from": "http://demo-web3guard.example", "to": "https://demo-web3guard.example/", "status_code": 301}],
            elapsed_ms=21,
        )

    monkeypatch.setattr(website_service, "_safe_fetch", fake_safe_fetch)
    monkeypatch.setattr(website_service, "validate_public_http_url", lambda raw_url: raw_url.strip())
    result = asyncio.run(scan_website("https://demo-web3guard.example", "Demo Website"))

    titles = {finding.title for finding in result.findings}
    assert result.engine_version == "web3guard-passive-website-engine-v2.9"
    assert "Content-Security-Policy Missing" in titles
    assert "Mixed Content Script Hint" in titles
    assert "Sensitive Path Hint: /.env" in titles
    assert result.severity_breakdown["high"] >= 2
    assert result.priority_actions
    assert result.scan_metadata["status_code"] == 200
    assert result.scan_metadata["robots_status"] == 404
    assert result.scan_metadata["sitemap_status"] == 200
    assert result.scan_metadata["html_evidence"]["external_script_count"] == 2
    assert result.scan_metadata["safety_controls"]["mode"] == "passive_only"
