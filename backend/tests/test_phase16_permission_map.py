from fastapi.testclient import TestClient

from main import app
from app.services.permission_map import build_permission_map, permission_map_status

client = TestClient(app)

SAMPLE_SOURCE = """// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
contract PermissionRisk {
    address public owner;
    address public treasury;
    uint256 public feeBps;
    mapping(address => bool) public blacklisted;
    modifier onlyOwner(){ require(msg.sender == owner, 'owner'); _; }
    constructor(address _treasury){ owner = msg.sender; treasury = _treasury; }
    function mint(address to, uint256 amount) external onlyOwner { }
    function pause() external onlyOwner { }
    function setFee(uint256 newFee) external onlyOwner { feeBps = newFee; }
    function setBlacklist(address user, bool blocked) external onlyOwner { blacklisted[user] = blocked; }
    function upgradeTo(address implementation) external onlyOwner { }
    function withdraw() external onlyOwner { payable(treasury).transfer(address(this).balance); }
}
"""


def test_phase16_status_is_real_only_permission_map():
    status = permission_map_status()
    assert status["phase"] == "Phase 16 - Contract Permission Map + Centralization Report"
    assert "No wallet connection" in " ".join(status["live_capabilities"])
    assert any("Does not prove" in item for item in status["not_claimed"])


def test_phase16_service_detects_capabilities_and_centralization_findings():
    result = build_permission_map(
        project_name="Permission Risk",
        solidity_code=SAMPLE_SOURCE,
        abi_json='[{"type":"function","name":"mint"},{"type":"function","name":"upgradeTo"}]',
        contract_address="0x" + "a" * 40,
        chain="ethereum",
        owner_address="0x" + "b" * 40,
        treasury_address="0x" + "c" * 40,
        multisig_enabled=False,
        timelock_enabled=False,
        governance_notes="No multisig or timelock yet.",
    )
    assert result.module_score.module == "permission_map"
    assert result.engine_version.startswith("web3guard-permission-map-engine")
    capabilities = result.scan_metadata["permission_map"]["capabilities"]
    keys = {item["key"] for item in capabilities}
    assert {"owner_admin", "minter", "pauser", "upgrader", "treasury", "blacklist_freeze", "fee_manager"}.issubset(keys)
    titles = {finding.title for finding in result.findings}
    assert "Multiple privileged capabilities without multisig evidence" in titles
    assert "Upgradeable contract authority needs governance review" in titles
    assert result.scan_metadata["centralization_report"]["multisig_evidence"] is False
    assert result.scan_metadata["founder_transparency_report"]["required_disclosures"]


def test_phase16_endpoint_requires_real_only_acknowledgement():
    response = client.post("/scan/permission-map", json={
        "project_name": "No Real Only",
        "solidity_code": SAMPLE_SOURCE,
        "authorization_confirmed": True,
        "real_only_acknowledged": False,
    })
    assert response.status_code == 400
    assert "Real-only" in response.json()["detail"]


def test_phase16_endpoint_rejects_empty_fake_permission_map():
    response = client.post("/scan/permission-map", json={
        "project_name": "Empty",
        "authorization_confirmed": True,
        "real_only_acknowledged": True,
    })
    assert response.status_code == 400
    assert "No fake permission map" in response.json()["detail"]


def test_phase16_endpoint_returns_real_permission_map():
    response = client.post("/scan/permission-map", json={
        "project_name": "Endpoint Permission Risk",
        "solidity_code": SAMPLE_SOURCE,
        "abi_json": '[{"type":"function","name":"pause"}]',
        "owner_address": "0x" + "d" * 40,
        "treasury_address": "0x" + "e" * 40,
        "multisig_enabled": True,
        "timelock_enabled": False,
        "authorization_confirmed": True,
        "real_only_acknowledged": True,
    })
    assert response.status_code == 200
    data = response.json()
    assert data["module_score"]["module"] == "permission_map"
    assert data["scan_metadata"]["coverage"]["assessed_from_real_input"] is True
    assert data["findings"]
