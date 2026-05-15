from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_wallet_flow_scanner_detects_approval_signature_and_prompt_risks():
    payload = {
        "project_name": "Risky Wallet Flow",
        "authorization_confirmed": True,
        "checklist": [
            {"key": "domain_verify", "label": "Domain verify", "answer": "unknown"},
            {"key": "allowance_warning", "label": "Allowance warning", "answer": "no"},
            {"key": "spender_display", "label": "Spender display", "answer": "no"},
            {"key": "amount_preview", "label": "Amount preview", "answer": "unknown"},
        ],
        "notes": """
        Mint page requests MaxUint256 unlimited approval.
        Permit2 signature may be used later.
        personal_sign is used for raw signature login.
        Wallet prompt appears on page load and chain mismatch handling is missing.
        """,
    }
    response = client.post("/scan/wallet-checklist", json=payload)
    assert response.status_code == 200
    data = response.json()
    titles = {finding["title"] for finding in data["findings"]}
    assert data["engine_version"] == "web3guard-wallet-flow-engine-v2.7"
    assert "Unlimited Approval Warning Missing" in titles
    assert "Unlimited Approval Pattern Mentioned" in titles
    assert "Permit Signature Flow Needs Extra Clarity" in titles
    assert "Blind / Raw Signature Risk Mentioned" in titles
    assert "Wallet Prompt May Trigger Too Early" in titles
    assert data["scan_metadata"]["safety_controls"]["no_transaction_signing"] is True
    assert data["severity_breakdown"]["high"] >= 2
    assert data["priority_actions"]


def test_admin_opsec_scanner_detects_single_owner_key_storage_and_treasury_risks():
    payload = {
        "project_name": "Risky Admin Setup",
        "authorization_confirmed": True,
        "checklist": [
            {"key": "multisig", "label": "Multisig", "answer": "no"},
            {"key": "timelock", "label": "Timelock", "answer": "no"},
            {"key": "private_key_policy", "label": "Private key policy", "answer": "unknown"},
        ],
        "notes": """
        Current owner is a single owner EOA owner and owner is deployer.
        No multisig and no timelock yet.
        Treasury same wallet as deployer treasury.
        Private key was stored in .env and shared in Telegram during testing.
        MFA missing and no incident response plan exists.
        Upgradeable proxy will be used later.
        """,
    }
    response = client.post("/scan/admin-opsec", json=payload)
    assert response.status_code == 200
    data = response.json()
    titles = {finding["title"] for finding in data["findings"]}
    assert data["engine_version"] == "web3guard-admin-opsec-engine-v2.7"
    assert "Multisig Missing for Owner/Admin" in titles
    assert "Single Owner / EOA Admin Risk Mentioned" in titles
    assert "Unsafe Private Key / Seed Phrase Storage Mentioned" in titles
    assert "Treasury and Admin Wallet Separation Risk" in titles
    assert "Upgradeable Contract Admin Requires Review" in titles
    assert data["scan_metadata"]["safety_controls"]["no_private_key_collection"] is True
    assert data["severity_breakdown"]["critical"] >= 3
    assert data["priority_actions"]


def test_phase57_checklist_templates_are_expanded():
    wallet = client.get("/scan/checklist/wallet")
    admin = client.get("/scan/checklist/admin_opsec")
    assert wallet.status_code == 200
    assert admin.status_code == 200
    assert wallet.json()["engine_version"] == "web3guard-wallet-admin-engine-v2.7"
    assert admin.json()["engine_version"] == "web3guard-wallet-admin-engine-v2.7"
    assert len(wallet.json()["items"]) >= 12
    assert len(admin.json()["items"]) >= 13
