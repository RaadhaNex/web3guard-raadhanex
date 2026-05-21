import asyncio

from app.services import scan_website as website_service
from app.services.scan_website import SafeFetchResult, scan_website


def test_phase79_deep_website_checks_create_real_findings(monkeypatch):
    async def fake_safe_fetch(client, method, url, *, read_body, max_redirects=5):
        if "redirect=http%3A%2F%2Fevil.com" in url:
            return SafeFetchResult(
                url=url,
                status_code=None,
                headers={},
                redirect_chain=[{"from": url, "to": "http://evil.com", "status_code": 302}],
                error="Too many redirects",
            )
        if url.endswith("/robots.txt") and method == "HEAD":
            return SafeFetchResult(url=url, status_code=200, headers={})
        if url.endswith("/robots.txt") and method == "GET":
            return SafeFetchResult(
                url=url,
                status_code=200,
                headers={"content-type": "text/plain"},
                body_text="User-agent: *\nDisallow: /admin\nDisallow: /api/internal\n",
            )
        if url.endswith("/sitemap.xml") or url.endswith("/.well-known/security.txt"):
            return SafeFetchResult(url=url, status_code=404, headers={})
        for path in website_service.LIMITED_PATH_HINTS:
            if url.endswith(path):
                return SafeFetchResult(url=url, status_code=404, headers={})
        return SafeFetchResult(
            url="https://deep.example/",
            status_code=200,
            headers={
                "content-type": "text/html; charset=utf-8",
                "content-security-policy": "default-src 'self'; script-src 'self' https://cdn.jsdelivr.net; object-src 'none'; frame-ancestors 'none'",
                "strict-transport-security": "max-age=31536000; includeSubDomains",
                "x-frame-options": "DENY",
                "x-content-type-options": "nosniff",
                "referrer-policy": "strict-origin-when-cross-origin",
                "permissions-policy": "camera=(), microphone=()",
                "set-cookie": "session=abc; Secure; HttpOnly; SameSite=Lax",
            },
            body_text="""
            <html><head>
              <script src="https://cdn.jsdelivr.net/npm/demo@1.0.0/index.js"></script>
              <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/demo/1.0.0/demo.css">
            </head><body>
              <img src="http://assets.example/logo.png" />
            </body></html>
            """,
            elapsed_ms=11,
        )

    async def fake_caa(host):
        return {"state": "Assessed", "records": [], "record_count": 0}

    monkeypatch.setattr(website_service, "_safe_fetch", fake_safe_fetch)
    monkeypatch.setattr(website_service, "_check_dns_caa", fake_caa)
    monkeypatch.setattr(website_service, "validate_public_http_url", lambda raw_url: raw_url.strip())

    result = asyncio.run(scan_website("https://deep.example", "Deep Evidence Demo"))
    titles = {finding.title for finding in result.findings}

    assert "Third-Party CDN Asset Missing SRI" in titles
    assert "Mixed Content Asset Detected" in titles
    assert "Open Redirect Confirmed" in titles
    assert "robots.txt Sensitive Path Disclosure" in titles
    assert "DNS CAA Record Missing" in titles
    assert result.scan_metadata["html_evidence"]["cdn_assets_missing_sri"]
    assert result.scan_metadata["robots_sensitive_disallow"][0]["keyword"] == "admin"
    assert result.scan_metadata["open_redirect_probe"]["findings"][0]["param"] == "redirect"
    assert result.scan_metadata["dns_caa"]["record_count"] == 0
    assert result.findings[0].evidence is not None
    assert result.findings[0].fix is not None
