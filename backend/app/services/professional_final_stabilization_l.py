from __future__ import annotations

"""Phase L — final integration and production stabilization layer.

This module is intentionally read-only. It does not run scans, does not make
network calls, does not publish reports, and does not relax any real-only guard.
It gives the backend a single place to verify whether the Phase A-K foundation is
wired, whether production configuration is safe, and what remains before public
market claims can be considered.
"""

from dataclasses import dataclass
from importlib import import_module
from typing import Any, Callable

from app.core.config import settings

PHASE = "Professional Scanner Phase L"
PHASE_VERSION = "web3guard-professional-final-stabilization-l-v1.0"

SAFE_PUBLIC_POSITIONING = (
    "Evidence-first Web3 pre-audit readiness scanner with optional human review, "
    "public proof and continuous monitoring. Not a certified audit."
)

BLOCKED_PUBLIC_CLAIMS = [
    "certified audit",
    "100% secure",
    "all vulnerabilities found",
    "CertiK replacement",
    "OpenZeppelin replacement",
    "Hacken replacement",
    "guaranteed secure",
    "bug-free",
]

REQUIRED_PHASE_MODULES: list[dict[str, str]] = [
    {"phase": "D", "service": "app.services.public_proof_report", "function": "status", "label": "Public proof report gate"},
    {"phase": "E", "service": "app.services.review_ops", "function": "status", "label": "Human review operations"},
    {"phase": "F", "service": "app.services.professional_accuracy", "function": "accuracy_readiness_summary", "label": "Accuracy assurance"},
    {"phase": "G", "service": "app.services.professional_benchmark_g", "function": "phase_g_readiness_summary", "label": "Benchmark and tuning dataset"},
    {"phase": "H", "service": "app.services.professional_rule_tuning_h", "function": "phase_h_status", "label": "Rule tuning gate"},
    {"phase": "I", "service": "app.services.professional_external_validation_i", "function": "external_validation_status", "label": "External validation gate"},
    {"phase": "J", "service": "app.services.professional_monitoring_j", "function": "readiness", "label": "Continuous monitoring readiness"},
    {"phase": "K", "service": "app.services.professional_direct_level_k", "function": "direct_competition_readiness_gate", "label": "Direct-level backend bridge"},
]

REQUIRED_ENDPOINT_GROUPS = [
    "/professional-accuracy",
    "/professional-benchmark",
    "/professional-rule-tuning",
    "/professional-external-validation",
    "/review-ops",
    "/proof-reports",
    "/professional-monitoring",
    "/professional-direct-level",
    "/professional-final-stabilization",
]

NEXT_REAL_WORLD_WORK = [
    {
        "id": "external_audited_dataset",
        "title": "Real external audited dataset",
        "status": "pending_real_world_input",
        "why_it_matters": "Synthetic and sanitized fixtures are not enough for audit-company-level trust. Real public/human-reviewed cases are needed.",
    },
    {
        "id": "reviewer_identity_and_qa",
        "title": "Reviewer identity, QA and escalation process",
        "status": "pending_operations",
        "why_it_matters": "Human-reviewed reports need named accountability, second-review workflow and conflict-of-interest handling.",
    },
    {
        "id": "admin_reviewer_ui",
        "title": "Admin reviewer UI",
        "status": "pending_ui",
        "why_it_matters": "The backend workflow exists, but reviewers need a clean UI to triage, verify fixes and approve reports.",
    },
    {
        "id": "public_proof_ui",
        "title": "Public proof report UI",
        "status": "pending_ui",
        "why_it_matters": "Public proof is useful only when clients and users can verify integrity, scope, limitations and current drift status.",
    },
    {
        "id": "scheduler_and_webhooks",
        "title": "Production scheduler and webhook provider setup",
        "status": "pending_deployment",
        "why_it_matters": "Monitoring becomes real when recurring jobs, GitHub webhooks and on-chain provider events are configured in production.",
    },
    {
        "id": "formal_fuzz_workers",
        "title": "Foundry/Echidna worker runner",
        "status": "pending_isolated_worker",
        "why_it_matters": "Phase C parses artifacts safely. Direct-level depth needs isolated workers that can run tests without risking the web server.",
    },
    {
        "id": "legal_report_process",
        "title": "Legal report templates and signed service process",
        "status": "pending_business_process",
        "why_it_matters": "Certified-audit-like wording cannot be used without legal terms, human sign-off and clearly defined scope/liability.",
    },
]


@dataclass(frozen=True)
class CheckResult:
    ok: bool
    state: str
    detail: str
    severity: str = "info"


def _safe_call(module_path: str, function_name: str) -> dict[str, Any]:
    try:
        module = import_module(module_path)
        fn: Callable[..., Any] = getattr(module, function_name)
        value = fn()
        if isinstance(value, dict):
            return {"ok": True, "state": "wired", "data": value}
        return {"ok": True, "state": "wired", "data": {"value": value}}
    except Exception as exc:  # pragma: no cover - intentionally defensive for production status endpoint
        return {"ok": False, "state": "error", "error": str(exc)[:500]}


def phase_module_matrix() -> dict[str, Any]:
    modules: list[dict[str, Any]] = []
    for item in REQUIRED_PHASE_MODULES:
        result = _safe_call(item["service"], item["function"])
        modules.append({**item, **result})
    return {
        "ok": all(item.get("ok") for item in modules),
        "phase": PHASE,
        "version": PHASE_VERSION,
        "modules": modules,
        "endpoint_groups_expected": REQUIRED_ENDPOINT_GROUPS,
    }


def production_config_checks() -> dict[str, Any]:
    checks: dict[str, CheckResult] = {}

    app_env = (settings.app_env or "development").lower()
    production_like = app_env in {"production", "prod", "staging"}
    checks["app_env"] = CheckResult(True, app_env, "App environment loaded.")

    admin_default = settings.admin_token in {"", "change-this-admin-token", None}
    checks["admin_token"] = CheckResult(
        ok=not (production_like and admin_default),
        state="default" if admin_default else "configured",
        detail="Set a strong ADMIN_TOKEN before production admin/reviewer operations.",
        severity="blocker" if production_like and admin_default else "warning" if admin_default else "ok",
    )

    ai_key = bool(settings.ai_api_key or settings.openai_api_key or settings.anthropic_api_key)
    checks["ai_provider"] = CheckResult(
        ok=not settings.ai_enabled or ai_key,
        state="enabled" if settings.ai_enabled else "disabled",
        detail="AI must show Provider Not Configured when enabled without a provider key.",
        severity="blocker" if settings.ai_enabled and not ai_key else "ok",
    )

    razorpay_ready = bool(settings.razorpay_key_id and settings.razorpay_key_secret and settings.razorpay_webhook_secret)
    checks["razorpay"] = CheckResult(
        ok=not settings.razorpay_enabled or razorpay_ready,
        state="enabled" if settings.razorpay_enabled else "disabled",
        detail="Razorpay must not show fake payment success without keys and webhook verification.",
        severity="blocker" if settings.razorpay_enabled and not razorpay_ready else "ok",
    )

    static_tools_ready = {
        "static_analysis_enabled": settings.static_analysis_enabled,
        "slither_configured": bool(settings.slither_binary) or not settings.slither_enabled,
        "semgrep_configured": bool(settings.semgrep_binary) or not settings.semgrep_enabled,
        "aderyn_configured": bool(settings.aderyn_binary) or not settings.aderyn_enabled,
    }
    checks["static_tools"] = CheckResult(
        ok=True,
        state="enabled" if settings.static_analysis_enabled else "disabled",
        detail="Missing static tools must remain Tool Not Installed / Not Assessed, never fake findings.",
        severity="info",
    )

    webhook_secret_missing = settings.professional_direct_level_network_enabled and (not settings.github_webhook_secret or not settings.onchain_webhook_secret)
    checks["direct_level_webhooks"] = CheckResult(
        ok=not webhook_secret_missing,
        state="network_enabled" if settings.professional_direct_level_network_enabled else "network_disabled",
        detail="Use webhook secrets before enabling live GitHub/on-chain event ingestion in production.",
        severity="blocker" if webhook_secret_missing else "ok",
    )

    values = {key: result.__dict__ for key, result in checks.items()}
    blockers = [key for key, result in checks.items() if not result.ok and result.severity == "blocker"]
    warnings = [key for key, result in checks.items() if result.severity == "warning"]
    return {
        "ok": not blockers,
        "phase": PHASE,
        "version": PHASE_VERSION,
        "checks": values,
        "blockers": blockers,
        "warnings": warnings,
        "static_tools_detail": static_tools_ready,
        "real_only_rule": "Disabled or missing providers/tools must show Not Assessed / Provider Not Configured / Tool Not Installed.",
    }


def claim_safety_gate(candidate_claim: str | None = None) -> dict[str, Any]:
    text = (candidate_claim or "").lower()
    hits = [claim for claim in BLOCKED_PUBLIC_CLAIMS if claim.lower() in text]
    return {
        "ok": not hits,
        "phase": PHASE,
        "version": PHASE_VERSION,
        "candidate_claim_checked": bool(candidate_claim),
        "blocked_hits": hits,
        "allowed_positioning": SAFE_PUBLIC_POSITIONING,
        "public_certified_audit_claim_allowed": False,
        "direct_competition_replacement_claim_allowed": False,
        "reason": "Phase L is a production stabilization gate. Market parity claims require real customer evidence, external datasets, human reviewer QA and legal sign-off.",
    }


def production_gate(candidate_claim: str | None = None) -> dict[str, Any]:
    modules = phase_module_matrix()
    config = production_config_checks()
    claim = claim_safety_gate(candidate_claim)
    blockers: list[str] = []
    warnings: list[str] = []

    if not modules["ok"]:
        blockers.append("phase_module_wiring")
    if not config["ok"]:
        blockers.extend(config.get("blockers", []))
    if not claim["ok"]:
        blockers.append("unsafe_public_claim")
    warnings.extend(config.get("warnings", []))

    score = 100 - len(blockers) * 20 - len(warnings) * 5
    score = max(0, min(100, score))
    return {
        "ok": not blockers,
        "phase": PHASE,
        "version": PHASE_VERSION,
        "gate_label": "production_stabilization_ready" if not blockers else "blocked_before_production_claims",
        "readiness_score": score,
        "blockers": blockers,
        "warnings": warnings,
        "modules_ok": modules["ok"],
        "config_ok": config["ok"],
        "claim_ok": claim["ok"],
        "claim_gate": claim,
        "config_gate": config,
        "module_matrix": modules,
        "next_required_real_world_work": NEXT_REAL_WORLD_WORK,
    }


def remaining_after_phase_l() -> dict[str, Any]:
    return {
        "ok": True,
        "phase": PHASE,
        "version": PHASE_VERSION,
        "backend_foundation_status": {
            "scanner_engine": "foundation_ready",
            "tool_verification": "foundation_ready",
            "benchmark_tuning": "foundation_ready",
            "human_review_backend": "foundation_ready",
            "public_proof_backend": "foundation_ready",
            "continuous_monitoring_backend": "foundation_ready",
            "webhook_snapshot_bridge": "foundation_ready",
            "final_stabilization_gate": "ready",
        },
        "remaining": NEXT_REAL_WORLD_WORK,
        "what_chatgpt_can_still_build": [
            "Admin reviewer UI",
            "Public proof report UI",
            "Monitoring dashboard UI",
            "Scheduler/cron bridge code",
            "Webhook provider setup docs",
            "Report templates and PDF/export polish",
            "More benchmark fixtures and regression tests",
            "Frontend build/typecheck cleanup patches",
        ],
        "what_requires_user_or_real_world_input": [
            "API keys and dashboard configuration",
            "Real customer/project permission",
            "Human auditors/reviewers",
            "Legal approval for audit-like wording",
            "External audited datasets or public case-study data",
            "Production webhook secrets and provider setup",
        ],
        "honest_market_status": "Direct-competition backend foundation is strong, but certified-audit competitor status requires real reviewers, real external evidence and legal process.",
    }


def smoke_check() -> dict[str, Any]:
    gate = production_gate()
    return {
        "ok": True,
        "phase": PHASE,
        "version": PHASE_VERSION,
        "service": settings.app_name,
        "env": settings.app_env,
        "router_expected": "/professional-final-stabilization",
        "production_gate_label": gate["gate_label"],
        "module_count": len(gate["module_matrix"]["modules"]),
        "blockers": gate["blockers"],
        "warning_count": len(gate["warnings"]),
        "real_only_controls": {
            "private_key_collection": False,
            "wallet_signing": False,
            "exploit_automation": False,
            "certified_audit_claim": False,
        },
    }
