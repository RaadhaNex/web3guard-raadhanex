import asyncio

from app.services import scan_website as website_service
from app.services import unified_url_scan as unified_service
from app.services.scan_website import SafeFetchResult, scan_website


def test_phase48_website_detects_more_real_passive_evidence(monkeypatch):
    async def fake_safe_fetch(client, method, url, *, read_body, max_redirects=5):
        if url.endswith('/app.js.map'):
            return SafeFetchResult(url=url, status_code=200, headers={})
        if url.endswith('/robots.txt') or url.endswith('/sitemap.xml') or url.endswith('/.well-known/security.txt'):
            return SafeFetchResult(url=url, status_code=404, headers={})
        for path in website_service.LIMITED_PATH_HINTS:
            if url.endswith(path):
                return SafeFetchResult(url=url, status_code=404, headers={})
        return SafeFetchResult(
            url='https://demo-web3guard.example/',
            status_code=200,
            headers={
                'content-type': 'text/html; charset=utf-8',
                'content-security-policy': "default-src *; script-src 'unsafe-inline' 'unsafe-eval' *",
                'set-cookie': 'sessionid=abc123; Path=/, prefs=light; Path=/; SameSite=Lax',
            },
            body_text='''
            <html><head>
              <script src="/app.js"></script>
              <base href="http://demo-web3guard.example/">
              <meta http-equiv="refresh" content="0;url=http://evil.example/">
            </head><body>
              <form action="http://demo-web3guard.example/login"><input type="password" name="password"></form>
              <a href="https://external.example" target="_blank">external</a>
              <iframe src="https://widgets.example/embed"></iframe>
              <object data="/legacy.swf"></object>
            </body></html>
            ''',
            elapsed_ms=18,
        )

    monkeypatch.setattr(website_service, '_safe_fetch', fake_safe_fetch)
    monkeypatch.setattr(website_service, 'validate_public_http_url', lambda raw_url: raw_url.strip())
    result = asyncio.run(scan_website('https://demo-web3guard.example', 'Phase 48 Demo'))
    titles = {finding.title for finding in result.findings}

    assert 'Cookie Missing Secure Flag' in titles
    assert 'Cookie Missing HttpOnly Flag' in titles
    assert 'CSP Missing frame-ancestors' in titles
    assert 'CSP Missing object-src none' in titles
    assert 'Insecure Form Action Detected' in titles
    assert 'External Links Missing noopener' in titles
    assert 'External iframe Without Sandbox' in titles
    assert 'Object/Embed Element Present' in titles
    assert 'Public JavaScript Source Map Exposed' in titles
    coverage = result.scan_metadata['bug_detection_coverage']
    assert coverage['phase'] == '48'
    assert coverage['finding_count'] == len(result.findings)
    assert 'cookie flags' in ' '.join(coverage['coverage_scope'])


def test_phase48_unified_scan_exposes_bug_detection_coverage(monkeypatch):
    async def fake_safe_fetch(client, method, url, *, read_body, max_redirects=5):
        if url.endswith('/robots.txt') or url.endswith('/sitemap.xml') or url.endswith('/.well-known/security.txt'):
            return SafeFetchResult(url=url, status_code=404, headers={})
        for path in website_service.LIMITED_PATH_HINTS:
            if url.endswith(path):
                return SafeFetchResult(url=url, status_code=404, headers={})
        return SafeFetchResult(
            url='https://launch.example/',
            status_code=200,
            headers={'content-type': 'text/html', 'content-security-policy': "default-src *; script-src 'unsafe-inline' *"},
            body_text='<html><body><a href="https://x.example" target="_blank">x</a></body></html>',
            elapsed_ms=8,
        )

    monkeypatch.setattr(website_service, '_safe_fetch', fake_safe_fetch)
    monkeypatch.setattr(website_service, 'validate_public_http_url', lambda raw_url: raw_url.strip())
    monkeypatch.setattr(unified_service, 'validate_public_http_url', lambda raw_url: raw_url.strip())

    result = asyncio.run(unified_service.run_unified_url_scan(unified_service.UnifiedUrlScanRequest(
        website_url='https://launch.example',
        project_name='Launch Example',
        authorization_confirmed=True,
        real_only_acknowledged=True,
    )))

    assert result['bug_detection_coverage']['phase'] == '48'
    assert result['bug_detection_coverage']['total_findings_from_assessed_modules'] >= 1
    assert result['bug_detection_coverage']['by_module']['website'] >= 1
    assert result['findings_pipeline']['summary']['real_findings'] >= 1
