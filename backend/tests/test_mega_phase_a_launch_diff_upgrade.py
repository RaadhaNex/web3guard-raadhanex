from fastapi.testclient import TestClient

from main import app
from app.services.launch_transparency import build_launch_transparency_report, launch_transparency_status
from app.services.contract_diff import build_contract_diff_report, contract_diff_status
from app.services.upgrade_safety import build_upgrade_safety_report, upgrade_safety_status

client = TestClient(app)

LAUNCH_CODE = """// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
contract LaunchToken {
    address public owner;
    address public treasury;
    uint256 public feeBps;
    mapping(address => bool) public blacklisted;
    modifier onlyOwner(){ require(msg.sender == owner, 'owner'); _; }
    function mint(address to, uint256 amount) external onlyOwner { }
    function pause() external onlyOwner { }
    function setFee(uint256 fee) external onlyOwner { feeBps = fee; }
    function setBlacklist(address user, bool blocked) external onlyOwner { blacklisted[user] = blocked; }
    function withdraw() external onlyOwner { payable(treasury).transfer(address(this).balance); }
}
"""

OLD_CODE = """// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
contract TokenV1 {
    address public owner;
    modifier onlyOwner(){ require(msg.sender == owner, 'owner'); _; }
}
"""

NEW_CODE = """// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
contract TokenV2 {
    address public owner;
    uint256 public feeBps;
    mapping(address => bool) public blacklisted;
    modifier onlyOwner(){ require(msg.sender == owner, 'owner'); _; }
    function mint(address to, uint256 amount) external onlyOwner { }
    function setFee(uint256 fee) external onlyOwner { feeBps = fee; }
    function setBlacklist(address user, bool blocked) external onlyOwner { blacklisted[user] = blocked; }
    function upgradeTo(address implementation) external onlyOwner { }
}
"""

UPGRADE_CODE = """// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
import '@openzeppelin/contracts-upgradeable/proxy/utils/UUPSUpgradeable.sol';
contract UpgradeableToken is UUPSUpgradeable {
    address public owner;
    uint256 public feeBps;
    function initialize(address _owner) public { owner = _owner; }
    function _authorizeUpgrade(address newImplementation) internal { }
}
"""


def test_mega_phase_a_status_endpoints_are_real_only():
    assert launch_transparency_status()["engine_version"].startswith("web3guard-launch-transparency")
    assert contract_diff_status()["engine_version"].startswith("web3guard-contract-diff")
    assert upgrade_safety_status()["engine_version"].startswith("web3guard-upgrade-safety")
    for path in ["/scan/launch-transparency/status", "/scan/contract-diff/status", "/scan/upgrade-safety/status"]:
        response = client.get(path)
        assert response.status_code == 200
        assert response.json()["ok"] is True


def test_phase17_launch_transparency_detects_owner_powers_without_fake_claims():
    result = build_launch_transparency_report(
        project_name="Launch Token",
        project_type="erc20",
        solidity_code=LAUNCH_CODE,
        website_text="Mint and claim token launch",
        tokenomics_notes="Owner can mint before launch.",
        liquidity_lock_evidence="",
        metadata_freeze_evidence="",
        owner_power_notes="No multisig yet.",
        multisig_enabled=False,
        timelock_enabled=False,
    )
    assert result.module_score.module == "launch_transparency"
    titles = {finding.title for finding in result.findings}
    assert "Mint authority requires launch disclosure" in titles
    assert "Privileged launch controls without multisig evidence" in titles
    assert result.scan_metadata["project_type_detected"] == "erc20"
    assert "does not accuse" not in result.disclaimer.lower()
    assert result.scan_metadata["real_only_note"]


def test_phase17_endpoint_rejects_empty_fake_transparency_report():
    response = client.post("/scan/launch-transparency", json={
        "project_name": "Empty",
        "authorization_confirmed": True,
        "real_only_acknowledged": True,
    })
    assert response.status_code == 400
    assert "No real launch transparency input" in response.json()["detail"]


def test_phase18_contract_diff_detects_added_risks_and_deltas():
    result = build_contract_diff_report(project_name="Diff Token", old_code=OLD_CODE, new_code=NEW_CODE)
    assert result.module_score.module == "contract_diff"
    assert result.scan_metadata["added_line_count"] > 0
    assert result.scan_metadata["new_score"] <= 100
    titles = {finding.title for finding in result.findings}
    assert "New mint/supply control introduced" in titles or "New upgrade-control surface introduced" in titles
    assert result.scan_metadata["diff_preview"].startswith("--- old.sol")


def test_phase18_endpoint_rejects_identical_source():
    response = client.post("/scan/contract-diff", json={
        "project_name": "Same",
        "old_code": OLD_CODE,
        "new_code": OLD_CODE,
        "authorization_confirmed": True,
        "real_only_acknowledged": True,
    })
    assert response.status_code == 400
    assert "identical" in response.json()["detail"].lower()


def test_phase19_upgrade_safety_detects_uups_initializer_and_storage_hints():
    result = build_upgrade_safety_report(
        project_name="Upgradeable Token",
        current_code=UPGRADE_CODE,
        previous_code=OLD_CODE,
        proxy_admin_notes="Proxy admin is a single hot wallet. No multisig yet.",
        ownership_verified=False,
    )
    assert result.module_score.module == "upgrade_safety"
    proxy_types = [item["type"] for item in result.scan_metadata["proxy_types_detected"]]
    assert "uups" in proxy_types
    titles = {finding.title for finding in result.findings}
    assert "initialize() without initializer modifier evidence" in titles
    assert "Proxy admin notes indicate single/hot wallet risk" in titles
    assert result.scan_metadata["storage_layout_hint"]["requires_compiler_storage_layout"] is True


def test_phase19_endpoint_requires_authorization_and_real_only():
    response = client.post("/scan/upgrade-safety", json={
        "project_name": "No auth",
        "current_code": UPGRADE_CODE,
        "authorization_confirmed": False,
        "real_only_acknowledged": True,
    })
    assert response.status_code == 400
    assert "Authorization" in response.json()["detail"]

    response = client.post("/scan/upgrade-safety", json={
        "project_name": "No real only",
        "current_code": UPGRADE_CODE,
        "authorization_confirmed": True,
        "real_only_acknowledged": False,
    })
    assert response.status_code == 400
    assert "Real-only" in response.json()["detail"]
