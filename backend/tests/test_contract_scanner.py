from pathlib import Path

from app.services.scan_contract import scan_solidity


SAMPLES = Path(__file__).resolve().parents[1] / "app" / "data" / "sample_contracts"


def test_vulnerable_contract_detects_real_launch_risks():
    code = (SAMPLES / "vulnerable_token.sol").read_text(encoding="utf-8")
    result = scan_solidity(code, project_name="Vulnerable Token", contract_type="ERC20")
    titles = {finding.title for finding in result.findings}

    assert result.module_score.score < 75
    assert any("tx.origin" in title for title in titles)
    assert any("Sensitive Function" in title for title in titles)
    assert any("Unchecked Low-Level Call" in title for title in titles)
    assert result.severity_breakdown["critical"] >= 1
    assert result.priority_actions


def test_safer_contract_scores_higher_than_vulnerable_contract():
    vulnerable = (SAMPLES / "vulnerable_token.sol").read_text(encoding="utf-8")
    safer = (SAMPLES / "safer_token.sol").read_text(encoding="utf-8")

    vulnerable_result = scan_solidity(vulnerable, project_name="Vulnerable Token", contract_type="ERC20")
    safer_result = scan_solidity(safer, project_name="Safer Token", contract_type="ERC20")

    assert safer_result.module_score.score > vulnerable_result.module_score.score
    assert safer_result.input_hash != vulnerable_result.input_hash
    assert safer_result.engine_version == "web3guard-solidity-rule-engine-v2.0"


def test_upgradeable_initializer_risk_detected():
    code = (SAMPLES / "upgradeable_init_risk.sol").read_text(encoding="utf-8")
    result = scan_solidity(code, project_name="Upgradeable Risk", contract_type="Other")
    combined_titles = " | ".join(finding.title for finding in result.findings)

    assert "Initializer May Be Unprotected" in combined_titles
    assert "Upgradeable Proxy / Implementation Risk" in combined_titles
