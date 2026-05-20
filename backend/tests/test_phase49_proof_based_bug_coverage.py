import asyncio

from app.services import scan_website as website_service
from app.services import unified_url_scan as unified_service
from app.services.scan_website import SafeFetchResult, scan_website


def test_phase49_confirms_public_env_exposure_without_leaking_secret(monkeypatch):
    async def fake_safe_fetch(client, method, url, *, read_body, max_redirects=5):
        if url.endswith('/.env'):
            if method == 'HEAD':
                return SafeFetchResult(url=url, status_code=200, headers={'content-type': 'text/plain'})
            return SafeFetchResult(
                url=url,
                status_code=200,
                headers={'content-type': 'text/plain'},
                body_text='DATABASE_URL=postgres://prod-secret\nOPENAI_API_KEY=sk-real-secret\n',
            )
        if url.endswith('/robots.txt') or url.endswith('/sitemap.xml') or url.endswith('/.well-known/security.txt'):
            return SafeFetchResult(url=url, status_code=404, headers={})
        for path in website_service.LIMITED_PATH_HINTS:
            if url.endswith(path):
                return SafeFetchResult(url=url, status_code=404, headers={})
        return SafeFetchResult(
            url='https://proof.example/',
            status_code=200,
            headers={'content-type': 'text/html', 'content-security-policy': "default-src 'self'; script-src 'self'; object-src 'none'; frame-ancestors 'none'"},
            body_text='<html><body>ok</body></html>',
        )

    monkeypatch.setattr(website_service, '_safe_fetch', fake_safe_fetch)
    monkeypatch.setattr(website_service, 'validate_public_http_url', lambda raw_url: raw_url.strip())
    result = asyncio.run(scan_website('https://proof.example', 'Proof Demo'))

    titles = {finding.title for finding in result.findings}
    assert 'Public .env File Exposure Confirmed' in titles
    taxonomy = result.scan_metadata['finding_truth_taxonomy']
    assert taxonomy['confirmed_proof_exposure_count'] == 1
    proof = taxonomy['confirmed_proof_exposures'][0]
    assert proof['kind'] == 'exposed_env_file'
    assert '<redacted>' in proof['raw_preview']
    assert 'sk-real-secret' not in proof['raw_preview']
    assert result.scan_metadata['bug_detection_coverage']['confirmed_proof_exposure_count'] == 1


def test_phase49_unified_scan_surfaces_confirmed_proof_exposures(monkeypatch):
    async def fake_safe_fetch(client, method, url, *, read_body, max_redirects=5):
        if url.endswith('/.git/config'):
            if method == 'HEAD':
                return SafeFetchResult(url=url, status_code=200, headers={'content-type': 'text/plain'})
            return SafeFetchResult(url=url, status_code=200, headers={'content-type': 'text/plain'}, body_text='[core]\nrepositoryformatversion = 0\n[remote "origin"]\nurl = https://github.com/example/repo.git\n')
        if url.endswith('/robots.txt') or url.endswith('/sitemap.xml') or url.endswith('/.well-known/security.txt'):
            return SafeFetchResult(url=url, status_code=404, headers={})
        for path in website_service.LIMITED_PATH_HINTS:
            if url.endswith(path):
                return SafeFetchResult(url=url, status_code=404, headers={})
        return SafeFetchResult(
            url='https://gitproof.example/',
            status_code=200,
            headers={'content-type': 'text/html', 'content-security-policy': "default-src 'self'; script-src 'self'; object-src 'none'; frame-ancestors 'none'"},
            body_text='<html><body>ok</body></html>',
        )

    monkeypatch.setattr(website_service, '_safe_fetch', fake_safe_fetch)
    monkeypatch.setattr(website_service, 'validate_public_http_url', lambda raw_url: raw_url.strip())
    monkeypatch.setattr(unified_service, 'validate_public_http_url', lambda raw_url: raw_url.strip())

    result = asyncio.run(unified_service.run_unified_url_scan(unified_service.UnifiedUrlScanRequest(
        website_url='https://gitproof.example',
        project_name='Git Proof Demo',
        authorization_confirmed=True,
        real_only_acknowledged=True,
    )))

    assert result['bug_detection_coverage']['phase'] == '49'
    assert result['bug_detection_coverage']['confirmed_proof_exposure_count'] == 1
    assert result['real_evidence_summary']['confirmed_bug_or_exposure_count'] == 1
    assert result['real_evidence_summary']['confirmed_proof_exposures'][0]['kind'] == 'exposed_git_config'
    assert result['dynamic_score_trace']['score'] < 92
