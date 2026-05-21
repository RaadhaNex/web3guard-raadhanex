from app.services.professional_benchmark_g import (
    dataset_catalog,
    phase_g_readiness_summary,
    run_custom_real_world_case,
    run_real_world_benchmark,
)


def test_phase_g_dataset_catalog_has_real_world_style_families():
    catalog = dataset_catalog()
    assert catalog["phase"] == "Professional Scanner Phase G"
    assert catalog["case_count"] >= 20
    assert "oracle_lending" in catalog["families"]
    assert "bridge_crosschain" in catalog["families"]
    assert all("code_sha256_16" in item for item in catalog["cases"])


def test_phase_g_benchmark_returns_quality_and_tuning_pack():
    result = run_real_world_benchmark()
    assert result["phase"] == "Professional Scanner Phase G"
    assert result["case_count"] >= 20
    assert 0 <= result["real_world_style_recall"] <= 1
    assert 0 <= result["clean_specificity"] <= 1
    assert "quality_gate" in result
    assert result["quality_gate"]["direct_competition_public_claim_allowed"] is False
    assert "tuning_pack" in result
    assert "tickets" in result["tuning_pack"]
    assert "family_metrics" in result
    assert result["blocked_claim"].startswith("Do not claim")


def test_phase_g_custom_case_is_not_stored_and_scans():
    code = """
    // SPDX-License-Identifier: MIT
    pragma solidity ^0.8.20;
    contract CustomPhaseG {
        function kill() external { selfdestruct(payable(msg.sender)); }
    }
    """
    result = run_custom_real_world_case(code, expected_rule_ids=[], forbidden_rule_ids=[], family="custom_phase_g")
    assert result["case_class"] == "regression"
    assert result["family"] == "custom_phase_g"
    assert result["source_type"] == "user_supplied_regression_case_not_stored_by_default"
    assert isinstance(result["top_findings"], list)


def test_phase_g_readiness_summary_points_to_endpoints():
    summary = phase_g_readiness_summary()
    assert summary["status"] == "active"
    assert summary["benchmark_endpoint"] == "/professional-benchmark/run"
    assert summary["public_claim_allowed"] is False
