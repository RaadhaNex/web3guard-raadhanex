import asyncio

from app.services import advanced_website_scan as adv_web
from app.services.advanced_website_scan import run_advanced_website_scan
from app.services.api_deep_readiness import run_api_deep_readiness_scan
from app.services.wallet_risk_integrations import run_wallet_risk_api_scan, wallet_risk_api_status
from app.services.scan_website import SafeFetchResult


def test_advanced_website_detects_launch_surface(monkeypatch):
    async def fake_safe_fetch(client, method, url, *, read_body, max_redirects=5):
        return SafeFetchResult(
            url="https://demo.example/",
            status_code=200,
            headers={"content-type": "text/html"},
            body_text="""
            <html><head>
              <script src="https://cdn1.example/lib.js"></script>
              <script src="https://cdn2.example/walletconnect.js"></script>
            </head><body>
              <a href="/privacy">Privacy</a><a href="https://x.com/demo">X</a>
              <button>Connect Wallet</button><button>Mint</button><p>approve token for claim</p>
            </body></html>
            """,
        )
    async def fake_base_scan(url, project_name=None):
        from app.services.scan_website import scan_website
        return await scan_website("https://example.com", project_name)
    monkeypatch.setattr(adv_web, "_safe_fetch", fake_safe_fetch)
    monkeypatch.setattr(adv_web, "validate_public_http_url", lambda raw: raw)
    # Avoid network inside base passive scan by returning a minimal response object.
    from app.models.schemas import ModuleScore, ScanResponse
    from datetime import datetime, timezone
    async def fake_scan_website(url, project_name=None):
        return ScanResponse(report_id="base", generated_at=datetime.now(timezone.utc), project_name=project_name, module_score=ModuleScore(module="website", score=80, risk_label="Low Risk"), findings=[], scan_metadata={})
    monkeypatch.setattr(adv_web, "scan_website", fake_scan_website)
    result = asyncio.run(run_advanced_website_scan("https://demo.example", "Demo"))
    titles = {f.title for f in result.findings}
    assert result.engine_version == "web3guard-advanced-website-engine-v3.0"
    assert "dApp Launch Page Without Visible Contract Address Evidence" in titles
    assert "Approval UX May Need Spender Explanation" in titles
    assert result.scan_metadata["web3_keyword_hits"]


def test_api_deep_detects_openapi_and_code_risks():
    result = asyncio.run(run_api_deep_readiness_scan(
        project_name="API",
        openapi_json='{"openapi":"3.0.0","paths":{"/admin/withdraw":{"post":{}},"/webhook/payment":{"post":{}}}}',
        api_code='app.add_middleware(CORSMiddleware, allow_origins=["*"])\napp = FastAPI(debug=True)\nPRIVATE_KEY="abc"',
        notes="admin reward allowlist endpoint exists",
    ))
    titles = {f.title for f in result.findings}
    assert result.engine_version == "web3guard-api-deep-readiness-engine-v3.0"
    assert "OpenAPI Spec Has No Obvious Auth/Security Scheme" in titles
    assert "Webhook Route Without Signature Evidence" in titles
    assert "Debug Mode Evidence In API Code" in titles
    assert "Wildcard CORS Evidence In API Code" in titles
    assert result.severity_breakdown["high"] >= 3


def test_wallet_risk_provider_disabled_is_not_fake():
    status = wallet_risk_api_status()
    assert status["no_private_key_collection"] is True
    result = asyncio.run(run_wallet_risk_api_scan(
        chain="ethereum",
        token_address="0x1111111111111111111111111111111111111111",
        spender_address="0x2222222222222222222222222222222222222222",
        project_name="Wallet Risk",
    ))
    titles = {f.title for f in result.findings}
    assert result.engine_version == "web3guard-wallet-risk-api-engine-v3.0"
    assert "External Wallet Risk Provider Not Enabled" in titles
    assert result.scan_metadata["no_private_key_collection"] is True
    assert result.scan_metadata["no_transaction_signing"] is True
