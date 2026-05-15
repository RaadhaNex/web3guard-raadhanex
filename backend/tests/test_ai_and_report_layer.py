from app.models.schemas import CombinedReportRequest, ExplanationRequest
from app.routers.ai import explain_single_finding, get_ai_status
from app.services.ai_explainer import fallback_finding_explanation
from app.services.report_builder import build_combined_launch_report
from app.services.scan_contract import scan_solidity


SAMPLE = """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
contract Risky {
    address public owner;
    mapping(address => uint256) public balanceOf;
    constructor(){ owner = msg.sender; }
    function mint(address to, uint256 amount) public { balanceOf[to] += amount; }
    function withdraw(address payable to, uint256 amount) public {
        require(tx.origin == owner, "not owner");
        to.call{value: amount}("");
        balanceOf[msg.sender] -= amount;
    }
}
"""


def test_ai_status_is_safe_fallback_by_default():
    status = get_ai_status()
    assert status["mode"] in {"safe_fallback", "provider"}
    assert "disclaimer" in status


def test_fallback_explanation_contains_no_certified_claim():
    scan = scan_solidity(SAMPLE, project_name="Risky", contract_type="ERC20")
    finding = scan.findings[0]
    explanation = fallback_finding_explanation(finding, mode="founder", language="Hinglish")
    assert explanation.status == "fallback"
    assert "manual" in explanation.manual_review_note.lower()
    assert "guarantee" not in explanation.summary.lower()


def test_report_builder_outputs_markdown_and_package():
    import asyncio
    scan = scan_solidity(SAMPLE, project_name="Risky", contract_type="ERC20")
    report = asyncio.run(build_combined_launch_report(CombinedReportRequest(project_name="Risky", reports=[scan], preferred_language="English")))
    assert report["report_id"].startswith("W3G-RAADHANEX-")
    assert report["markdown_report"].startswith("# Web3Guard AI Launch Readiness Report")
    assert report["package_recommendation"]["package"]
    assert "certified audit" in report["disclaimer"]
