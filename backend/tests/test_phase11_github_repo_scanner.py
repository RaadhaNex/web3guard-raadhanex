import pytest
from fastapi.testclient import TestClient

import app.services.scan_github_repo as svc
from main import app

client = TestClient(app)


def test_phase11_github_status_endpoint_is_real_only():
    response = client.get("/scan/github/status")
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert "No repository cloning" in data["not_enabled_or_not_claimed"]
    assert data["limits"]["max_github_files"] > 0


def test_phase11_parse_github_repo_url():
    parsed = svc.parse_github_repo_url("https://github.com/owner-name/repo_name/tree/main")
    assert parsed["owner"] == "owner-name"
    assert parsed["repo"] == "repo_name"
    assert parsed["branch_from_url"] == "main"
    with pytest.raises(ValueError):
        svc.parse_github_repo_url("https://gitlab.com/owner/repo")


@pytest.mark.asyncio
async def test_phase11_repo_scanner_uses_mocked_public_evidence(monkeypatch):
    async def fake_get_json(client, url):
        if "/git/trees/" in url:
            return {
                "truncated": False,
                "tree": [
                    {"type": "blob", "path": ".env", "size": 80},
                    {"type": "blob", "path": "package.json", "size": 260},
                    {"type": "blob", "path": "contracts/Vulnerable.sol", "size": 420},
                    {"type": "blob", "path": "backend/main.py", "size": 220},
                    {"type": "blob", "path": "frontend/app/mint/page.tsx", "size": 220},
                ],
            }
        return {
            "default_branch": "main",
            "private": False,
            "fork": False,
            "archived": False,
            "stargazers_count": 1,
            "pushed_at": "2026-05-01T00:00:00Z",
        }

    async def fake_get_text(client, url, *, max_bytes):
        if url.endswith("package.json"):
            return '{"dependencies":{"@walletconnect/client":"^1.8.0","bip39":"^3.1.0"}}'
        if url.endswith("contracts/Vulnerable.sol"):
            return """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
contract Vulnerable {
    address public owner;
    constructor(){ owner = msg.sender; }
    function withdraw() external {
        require(tx.origin == owner);
        payable(msg.sender).call{value: address(this).balance}("");
    }
}
"""
        if url.endswith("backend/main.py"):
            return 'app.add_middleware(CORSMiddleware, allow_origins=["*"])\nDEBUG=True\n'
        if url.endswith("frontend/app/mint/page.tsx"):
            return 'const x = window.ethereum; const y = MaxUint256; <div dangerouslySetInnerHTML={{__html: html}} />'
        if url.endswith(".env"):
            return 'PRIVATE_KEY=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
        return ""

    monkeypatch.setattr(svc, "_get_json", fake_get_json)
    monkeypatch.setattr(svc, "_get_text", fake_get_text)
    result = await svc.scan_github_repository("https://github.com/owner/repo", project_name="Mock Repo")
    assert result.module_score.module == "github"
    assert result.module_score.score < 100
    assert result.scan_metadata["structure_summary"]["solidity_count"] == 1
    titles = {finding.title for finding in result.findings}
    assert "Sensitive Environment File Committed" in titles
    assert "Hardcoded Private Key / Seed Phrase Pattern" in titles
    assert "Wildcard CORS Pattern in Repo" in titles
    assert result.scan_metadata["safety_controls"]["execute_code"] is False
