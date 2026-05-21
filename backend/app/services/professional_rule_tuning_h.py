"""Professional Scanner Phase H — benchmark-driven rule tuning validation.

Phase H consumes Phase G's real-world-style benchmark and proves that the
scanner rule engine was tuned against the weak families found in Phase G:
upgradeability, oracle, MEV/deadline, cross-chain, ERC4626/vault,
multicall/value, and old compiler arithmetic.

This is an internal quality gate only. It does not certify audit parity.
"""
from __future__ import annotations

from typing import Any

from app.services.professional_benchmark_g import run_real_world_benchmark
from app.services.scan_contract import ENGINE_VERSION

PHASE_H_TUNED_FAMILIES = [
    "upgradeability",
    "oracle_lending",
    "mev_swap",
    "bridge_crosschain",
    "vault_erc4626",
    "multicall_value",
    "old_compiler_math",
]

PHASE_H_TUNED_RULE_IDS = [
    "WG-SOL-UPGRADE-003",
    "WG-SOL-UPGRADE-004",
    "WG-SOL-ORACLE-002",
    "WG-SOL-MEV-002",
    "WG-SOL-XCHAIN-001",
    "WG-SOL-VAULT-001",
    "WG-SOL-VAULT-002",
    "WG-SOL-MULTI-001",
    "WG-SOL-OVFL-001",
]


def phase_h_status() -> dict[str, Any]:
    return {
        "ok": True,
        "phase": "Professional Scanner Phase H",
        "engine_version": ENGINE_VERSION,
        "purpose": "Benchmark-driven rule tuning from Phase G weak families.",
        "tuned_families": PHASE_H_TUNED_FAMILIES,
        "tuned_rule_ids": PHASE_H_TUNED_RULE_IDS,
        "public_claim_allowed": False,
        "claim_policy": "Internal scanner accuracy validation only. Not certified audit parity.",
    }


def run_phase_h_tuning_validation() -> dict[str, Any]:
    benchmark = run_real_world_benchmark()
    quality_gate = benchmark.get("quality_gate") or {}
    tuning_pack = benchmark.get("tuning_pack") or {}
    missed_rules = tuning_pack.get("missed_rules") or {}
    noisy_rules = tuning_pack.get("noisy_rules") or {}
    family_metrics = benchmark.get("family_metrics") or {}

    tuned_family_results = {
        family: family_metrics.get(family, {})
        for family in PHASE_H_TUNED_FAMILIES
    }
    tuned_family_issues = {
        family: metrics
        for family, metrics in tuned_family_results.items()
        if metrics and (
            metrics.get("recall") is not None and float(metrics.get("recall") or 0) < 1.0
            or metrics.get("false_positive_case_count", 0)
        )
    }

    direct_level_engine_progress = bool(quality_gate.get("direct_level_engine_progress"))
    phase_h_passed = (
        benchmark.get("missed_expected_rule_signals") == 0
        and benchmark.get("false_positive_case_count") == 0
        and benchmark.get("severity_fail_case_count") == 0
        and not missed_rules
        and not noisy_rules
    )

    return {
        "ok": phase_h_passed,
        "phase": "Professional Scanner Phase H",
        "engine_version": ENGINE_VERSION,
        "validation_type": "benchmark_driven_rule_tuning_gate",
        "phase_h_passed": phase_h_passed,
        "direct_level_engine_progress": direct_level_engine_progress,
        "public_direct_competition_claim_allowed": False,
        "why_public_claim_still_blocked": [
            "Phase H validates the scanner engine on sanitized benchmark fixtures only.",
            "Certified-audit competition still requires external datasets, independent reviewers, legal report process and public track record.",
            "The product can say benchmark-tuned pre-audit scanner, not audit-company replacement.",
        ],
        "phase_g_benchmark_snapshot": {
            "benchmark_id": benchmark.get("benchmark_id"),
            "case_count": benchmark.get("case_count"),
            "expected_rule_signals": benchmark.get("expected_rule_signals"),
            "detected_expected_rule_signals": benchmark.get("detected_expected_rule_signals"),
            "missed_expected_rule_signals": benchmark.get("missed_expected_rule_signals"),
            "false_positive_case_count": benchmark.get("false_positive_case_count"),
            "severity_fail_case_count": benchmark.get("severity_fail_case_count"),
            "real_world_style_recall": benchmark.get("real_world_style_recall"),
            "clean_specificity": benchmark.get("clean_specificity"),
            "pass_rate": benchmark.get("pass_rate"),
            "quality_gate": quality_gate,
        },
        "tuned_families": PHASE_H_TUNED_FAMILIES,
        "tuned_rule_ids": PHASE_H_TUNED_RULE_IDS,
        "tuned_family_results": tuned_family_results,
        "remaining_tuned_family_issues": tuned_family_issues,
        "remaining_tuning_pack": tuning_pack,
        "next_required_step": "Add independently reviewed public audit/CTF/lab cases and human reviewer confirmation before stronger market claims.",
    }
