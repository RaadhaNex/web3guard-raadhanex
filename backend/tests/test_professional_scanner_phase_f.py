from app.services.professional_accuracy import (
    BENCHMARK_CASES,
    calibration_report,
    run_custom_contract_case,
    run_professional_accuracy_benchmark,
)


def test_professional_accuracy_benchmark_runs():
    result = run_professional_accuracy_benchmark()
    assert result["phase"] == "Professional Scanner Phase F"
    assert result["case_count"] == len(BENCHMARK_CASES)
    assert result["expected_rule_signals"] >= 10
    assert 0 <= result["synthetic_recall"] <= 1
    assert 0 <= result["clean_specificity"] <= 1
    assert "quality_gate" in result
    assert result["quality_gate"]["direct_competition_claim_allowed"] is False


def test_phase_f_has_clean_and_vulnerable_cases():
    classes = {case.case_class for case in BENCHMARK_CASES}
    assert "vulnerable" in classes
    assert "clean" in classes


def test_custom_benchmark_detects_expected_rule():
    code = """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
contract T {
    function kill() public { selfdestruct(payable(msg.sender)); }
}
"""
    result = run_custom_contract_case(code, expected_rule_ids=["WG-SOL-LIFE-001"], project_name="T")
    assert "WG-SOL-LIFE-001" in result["detected_expected_rule_ids"]
    assert result["passed"] is True


def test_calibration_report_shape():
    report = calibration_report()
    assert report["phase"] == "Professional Scanner Phase F"
    assert "benchmark_quality_gate" in report
    assert "rule_calibration_actions" in report
    assert report["public_claim_policy"].startswith("Use this")
