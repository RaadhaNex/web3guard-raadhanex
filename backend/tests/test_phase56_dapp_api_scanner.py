from fastapi.testclient import TestClient

from main import app
from app.services import scan_dapp_api as dapp_api_service

client = TestClient(app)


def test_dapp_frontend_scanner_detects_code_and_package_risks():
    payload = {
        "project_name": "Risky Mint dApp",
        "authorization_confirmed": True,
        "checklist": [
            {"key": "secrets", "label": "No public secrets", "answer": "no"},
            {"key": "chain_check", "label": "Chain check", "answer": "unknown"},
            {"key": "tx_preview", "label": "Tx preview", "answer": "unknown"},
            {"key": "dangerous_html", "label": "Unsafe HTML", "answer": "unknown"},
        ],
        "frontend_code": """
        const cfg = {
          NEXT_PUBLIC_ADMIN_API_KEY: 'abc123456789',
          rpc: 'https://eth-mainnet.g.alchemy.com/v2/public-demo',
          contract: '0x1111111111111111111111111111111111111111'
        }
        export function Mint() {
          const autoConnect = true;
          const approval = ethers.constants.MaxUint256;
          return <div dangerouslySetInnerHTML={{__html: location.hash}} />
        }
        """,
        "package_json": '{"dependencies":{"web3modal":"^1.9.12","@walletconnect/client":"^1.8.0"}}',
    }
    response = client.post("/scan/dapp-checklist", json=payload)
    assert response.status_code == 200
    data = response.json()
    titles = {finding["title"] for finding in data["findings"]}
    assert data["engine_version"] == "web3guard-dapp-frontend-engine-v2.6"
    assert "Frontend-Exposed Secret Naming Risk" in titles
    assert "Hardcoded RPC Provider URL" in titles
    assert "Unlimited Approval / setApprovalForAll Pattern" in titles
    assert "Unsafe Frontend Rendering / Eval Pattern" in titles
    assert "Frontend Dependency Review Needed" in titles
    assert data["severity_breakdown"]["high"] >= 3
    assert data["scan_metadata"]["safety_controls"]["static_hints_only"] is True


def test_api_backend_scanner_detects_config_risks_and_blocks_private_url(monkeypatch):
    response = client.post(
        "/scan/api-checklist",
        json={
            "project_name": "Risky API",
            "authorization_confirmed": True,
            "api_base_url": "http://localhost:8000",
            "api_code": "app = FastAPI(debug=True)",
            "checklist": [],
        },
    )
    assert response.status_code == 400
    assert "Private/internal" in response.json()["detail"]

    monkeypatch.setattr(dapp_api_service, "validate_public_http_url", lambda raw_url: raw_url.strip())

    payload = {
        "project_name": "Risky API",
        "authorization_confirmed": True,
        "api_base_url": "https://example.com",
        "checklist": [
            {"key": "rate_limit", "label": "Rate limit", "answer": "unknown"},
            {"key": "auth", "label": "Auth", "answer": "unknown"},
            {"key": "cors", "label": "CORS", "answer": "no"},
        ],
        "api_code": """
        from fastapi import FastAPI
        from fastapi.middleware.cors import CORSMiddleware
        JWT_SECRET = 'hardcoded-demo-secret'
        app = FastAPI(debug=True)
        app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_credentials=True)
        @app.post('/webhook/razorpay')
        def webhook(payload: dict):
            return {'ok': True}
        @app.get('/users/{id}')
        def get_user(id: str):
            return {'id': id}
        """,
    }
    response = client.post("/scan/api-checklist", json=payload)
    assert response.status_code == 200
    data = response.json()
    titles = {finding["title"] for finding in data["findings"]}
    assert data["engine_version"] == "web3guard-api-backend-engine-v2.6"
    assert "Hardcoded Backend Secret Pattern" in titles
    assert "Overly Open CORS Pattern" in titles
    assert "Debug Mode / Verbose Error Risk" in titles
    assert "Rate Limiting Not Evident in Provided API Code" in titles
    assert "Webhook Signature Verification Not Evident" in titles
    assert data["scan_metadata"]["validated_api_base"] == "https://example.com"
    assert data["severity_breakdown"]["critical"] >= 1


def test_dapp_api_checklist_templates_are_expanded():
    dapp = client.get("/scan/checklist/dapp")
    api = client.get("/scan/checklist/api")
    assert dapp.status_code == 200
    assert api.status_code == 200
    assert len(dapp.json()["items"]) >= 8
    assert len(api.json()["items"]) >= 9
    assert dapp.json()["engine_version"] == "web3guard-dapp-api-engine-v2.6"
