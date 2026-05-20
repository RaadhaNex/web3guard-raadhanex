from app.services.accuracy_hardening import (
    benchmark_scanner_accuracy,
    build_trust_proof_pack,
    parse_formal_fuzz_artifacts,
    tune_false_positive_policy,
    validate_authenticated_api_test_plan,
    validate_defi_invariant_plan,
)


def test_benchmark_accuracy_computes_precision_recall():
    result = benchmark_scanner_accuracy([
        {"sample_id": "vuln", "expected_findings": ["a", "b"], "scanner_findings": ["a", "c"]},
        {"sample_id": "clean", "expected_findings": [], "scanner_findings": [], "known_clean": True},
    ])
    assert result["state"] == "Assessed"
    assert result["totals"]["true_positive"] == 1
    assert result["totals"]["false_positive"] == 1
    assert result["totals"]["false_negative"] == 1
    assert result["metrics"]["precision_on_supplied_dataset"] == 0.5
    assert result["metrics"]["recall_on_supplied_dataset"] == 0.5


def test_false_positive_tuning_suggests_downgrade():
    result = tune_false_positive_policy([
        {"rule_id": "noisy-rule", "status": "false_positive"},
        {"rule_id": "noisy-rule", "status": "false_positive"},
        {"rule_id": "solid-rule", "status": "confirmed"},
    ])
    assert result["state"] == "Assessed"
    assert result["counts"]["false_positive"] == 2
    assert result["suppression_or_downgrade_candidates"]


def test_formal_fuzz_artifact_marks_failed_invariant():
    result = parse_formal_fuzz_artifacts(invariant_results=[{"name": "supply invariant", "passed": False, "evidence": "counterexample"}])
    assert result["state"] == "Assessed"
    assert result["confirmed_artifact_findings"][0]["proof_level"] == "supplied_invariant_result"


def test_api_harness_detects_auth_evidence_and_redaction_warning():
    result = validate_authenticated_api_test_plan(
        {"roles": ["user_a", "user_b"], "endpoints": ["GET /orders/{id}"], "object_ids": ["a", "b"]},
        [{"endpoint": "/orders/123", "bola_proof": True, "authorization": "Bearer abcdefghijklmnopqrstuvwxyz"}],
    )
    assert result["state"] == "Assessed"
    assert result["confirmed_findings"]
    assert result["redaction_warnings"]


def test_defi_invariant_plan_reports_missing_areas():
    result = validate_defi_invariant_plan({"uses_oracle": True, "has_flash_loan_surface": True}, [{"category": "authorization", "passed": True}])
    assert result["state"] == "Assessed"
    assert "oracle bounds/TWAP" in result["missing_invariant_areas"]
    assert "flash-loan resistant accounting" in result["missing_invariant_areas"]


def test_trust_proof_blocks_certified_audit_claim():
    result = build_trust_proof_pack(
        case_studies=[{"title": "Pilot", "permission_to_publish": True, "evidence_summary": "Real scan", "outcome": "Fixed warnings"}],
        claims=["Web3Guard certified audit and 100% secure"],
    )
    assert result["state"] == "Blocked"
    assert result["blocked_claims"]
