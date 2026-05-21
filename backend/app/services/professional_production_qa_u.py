from __future__ import annotations

import json
from collections import Counter
from typing import Any

from app.core.config import settings
from app.services.mega_phase_e_store import append_jsonl, new_id, now_iso, read_jsonl, sort_created, storage_path
from app.services import professional_setup_t as setup_t
from app.services import professional_final_stabilization_l as final_l
from app.services import professional_direct_level_k as direct_level_k
from app.services import professional_ops_n_to_s as ops_n_to_s
from app.services import professional_monitoring_j as monitoring_j

REAL_ONLY_NOTE = (
    "Phase U is a first real production QA and launch checklist layer. It records only declared/manual QA evidence, "
    "configuration status, and existing backend readiness signals. It does not fake live scans, customer proof, audits, "
    "webhook deliveries, worker runs, or certified-audit status."
)

BLOCKED_CLAIMS = {
    "certified audit",
    "certified auditor",
    "100% secure",
    "guaranteed secure",
    "all vulnerabilities found",
    "exploit-proof",
    "replaces certik",
    "replaces openzeppelin",
    "replaces hacken",
}

COMPETITOR_LEVELS = {
    "basic_scanner_tools": 82,
    "pre_audit_readiness_product": 76,
    "ai_assisted_audit_prep": 66,
    "continuous_security_os_foundation": 58,
    "full_certified_audit_company": 38,
}


def _text(value: Any, fallback: str = "") -> str:
    if value is None:
        return fallback
    return str(value).strip() or fallback


def _bool(value: Any) -> bool:
    return bool(value)


def _runs_file() -> str:
    return getattr(settings, "professional_production_qa_runs_file", "app/data/db/professional_production_qa_runs.jsonl")


def _read_runs() -> list[dict[str, Any]]:
    return sort_created(read_jsonl(storage_path(_runs_file())))


def _append_run(row: dict[str, Any]) -> None:
    append_jsonl(storage_path(_runs_file()), row)


def _has_blocked_claims(value: Any) -> list[str]:
    text = json.dumps(value, ensure_ascii=False, default=str).lower()
    for safe in [
        "not a certified audit",
        "no certified-audit claim",
        "no certified audit claim",
        "does not replace certik",
        "does not replace openzeppelin",
        "does not replace hacken",
        "not 100% secure",
        "no 100% secure claim",
    ]:
        text = text.replace(safe, "")
    return sorted(claim for claim in BLOCKED_CLAIMS if claim in text)


def _check(key: str, label: str, state: str, required: bool, source: str, evidence: Any = None, fix: str = "") -> dict[str, Any]:
    return {
        "key": key,
        "label": label,
        "state": state,
        "required": required,
        "source": source,
        "evidence": evidence,
        "fix": fix,
    }


def _state(configured: bool, required: bool = True) -> str:
    if configured:
        return "Ready"
    return "Missing" if required else "Optional"


def phase_status() -> dict[str, Any]:
    runs = _read_runs()
    latest = runs[0] if runs else None
    return {
        "ok": True,
        "phase": "U",
        "name": "First Real Production QA + Launch Checklist",
        "certified_audit_claim_allowed": False,
        "direct_competition_public_claim_allowed": False,
        "qa_runs_recorded": len(runs),
        "latest_run": latest,
        "modules": {
            "production_qa_gate": True,
            "live_smoke_test_plan": True,
            "release_checklist": True,
            "competitor_gap_matrix": True,
            "qa_evidence_log": True,
        },
        "real_only_note": REAL_ONLY_NOTE,
    }


def local_test_plan() -> dict[str, Any]:
    return {
        "ok": True,
        "phase": "U",
        "name": "Local validation commands",
        "commands": [
            {"order": 1, "area": "Backend", "command": "cd backend && .\\.venv\\Scripts\\Activate.ps1 && python -m pytest -q", "pass_signal": "All tests passed."},
            {"order": 2, "area": "Frontend typecheck", "command": "cd frontend && npm run typecheck", "pass_signal": "No TypeScript errors."},
            {"order": 3, "area": "Frontend production build", "command": "cd frontend && npm run build", "pass_signal": "Build completes successfully."},
            {"order": 4, "area": "Git state", "command": "git status", "pass_signal": "Only intended files changed, no .venv/.env/node_modules committed."},
        ],
        "must_not_commit": ["backend/.venv", "backend/.env", "frontend/.env.local", "node_modules", ".toolsvenv", "private keys", "seed phrases", "customer secrets"],
        "real_only_note": REAL_ONLY_NOTE,
    }


def live_smoke_checklist() -> dict[str, Any]:
    backend_url = _text(getattr(settings, "backend_url", ""), "<BACKEND_URL>").rstrip("/")
    frontend_url = _text(getattr(settings, "frontend_url", ""), _text(getattr(settings, "frontend_origin", ""), "<FRONTEND_URL>")).rstrip("/")
    return {
        "ok": True,
        "phase": "U",
        "name": "Live production smoke checklist",
        "backend_url": backend_url,
        "frontend_url": frontend_url,
        "steps": [
            {"order": 1, "area": "Backend health", "url": f"{backend_url}/", "expected": "200 OK and Web3Guard service metadata."},
            {"order": 2, "area": "Final gate", "url": f"{backend_url}/professional-final-stabilization/production-gate", "expected": "production_ready signal plus blockers/warnings."},
            {"order": 3, "area": "Setup assistant", "url": f"{backend_url}/professional-setup/production-readiness", "expected": "readiness score and env/webhook/worker status."},
            {"order": 4, "area": "Phase U QA", "url": f"{backend_url}/professional-production-qa/launch-decision", "expected": "safe launch decision with no unsafe claim."},
            {"order": 5, "area": "Frontend setup UI", "url": f"{frontend_url}/professional/setup", "expected": "Real setup assistant loads without localhost API errors."},
            {"order": 6, "area": "Frontend production QA UI", "url": f"{frontend_url}/professional/production-qa", "expected": "Phase U QA dashboard loads."},
            {"order": 7, "area": "URL scan", "url": f"{frontend_url}/scanner/unified-url", "expected": "URL scan completes with evidence-only findings."},
            {"order": 8, "area": "GitHub repo scan", "url": f"{frontend_url}/scanner/unified-url", "expected": "GitHub repository scan shows repo/source evidence or Not Assessed."},
            {"order": 9, "area": "Contract scan", "url": f"{frontend_url}/scanner/unified-url", "expected": "Solidity source/verified address scan shows file/line/source tools when evidence exists."},
            {"order": 10, "area": "Reviewer/proof workflow", "url": f"{frontend_url}/admin/reviewer", "expected": "Assignment/readiness/proof actions work with real data only."},
        ],
        "real_only_note": REAL_ONLY_NOTE,
    }


def release_checklist() -> dict[str, Any]:
    env = setup_t.env_checklist()
    readiness = setup_t.production_readiness()
    worker = setup_t.worker_enablement_gate()
    final_gate = final_l.production_gate()
    direct_gate = direct_level_k.direct_competition_readiness_gate()
    ops = ops_n_to_s.phase_status()
    monitoring = monitoring_j.readiness()

    checks = [
        _check("backend_tests", "Backend pytest full suite", "Manual Required", True, "local", fix="Run python -m pytest -q and record result with /professional-production-qa/runs."),
        _check("frontend_typecheck", "Frontend typecheck", "Manual Required", True, "local", fix="Run npm run typecheck and record result."),
        _check("frontend_build", "Frontend production build", "Manual Required", True, "local", fix="Run npm run build and record result."),
        _check("required_env", "Required production env", _state(bool(env.get("required_ready"))), True, "professional-setup", {"missing_required_count": env.get("missing_required_count")}, "Complete Render/Vercel/secret env setup."),
        _check("worker_safe", "Worker disabled or safely isolated", "Ready" if (not worker.get("currently_enabled", {}).get("effective_professional_runner_enabled") or worker.get("safe_to_turn_true")) else "Blocked", True, "professional-setup", worker.get("currently_enabled"), "Keep worker false on main API until isolated worker gate is green."),
        _check("unsafe_claims", "Unsafe public claims blocked", "Ready", True, "phase-u", {"blocked_claims": sorted(BLOCKED_CLAIMS)}, "Do not publish replacement/certified/100%-secure claims."),
        _check("final_gate", "Final stabilization gate", "Ready" if final_gate.get("production_ready") else "Warning", False, "professional-final-stabilization", {"blockers": final_gate.get("blockers", [])[:5]}, "Review production gate warnings."),
        _check("direct_gate", "Direct-level readiness gate", "Progress" if direct_gate.get("readiness_score", 0) else "Manual Required", False, "professional-direct-level", {"readiness_score": direct_gate.get("readiness_score"), "gate_label": direct_gate.get("gate_label")}, "Use as internal readiness only, not public claim."),
        _check("ops_console", "Ops console available", "Ready" if ops.get("ok") else "Missing", False, "professional-ops", {"counts": ops.get("counts", {})}, "Use /professional/* and /admin pages for ops."),
        _check("monitoring", "Monitoring readiness", "Ready" if monitoring.get("ready") else "Setup Required", False, "professional-monitoring", monitoring, "Create baseline and connect webhooks for real monitoring."),
    ]
    blockers = [item for item in checks if item["required"] and item["state"] in {"Missing", "Blocked"}]
    manual_required = [item for item in checks if item["state"] == "Manual Required"]
    return {
        "ok": True,
        "phase": "U",
        "name": "Release checklist",
        "safe_for_internal_beta": len(blockers) == 0,
        "manual_checks_required_count": len(manual_required),
        "blockers": blockers,
        "checks": checks,
        "real_only_note": REAL_ONLY_NOTE,
    }


def competitor_position() -> dict[str, Any]:
    return {
        "ok": True,
        "phase": "U",
        "name": "Competitor-level internal position",
        "scores_out_of_100": COMPETITOR_LEVELS,
        "what_we_match_now": [
            "Pre-audit readiness automation",
            "Multi-surface evidence collection: website, API/admin, dApp hints, GitHub, Solidity source/address",
            "Static tool aggregation hooks for Slither/Semgrep/Aderyn when installed/configured",
            "Finding normalization with evidence, file/line, source tools, fix guidance",
            "Human reviewer workflow backend and UI foundation",
            "Public proof/report integrity backend and UI foundation",
            "Continuous monitoring/drift backend foundation",
            "Production setup, worker safety, and QA gates",
        ],
        "what_we_do_not_match_yet": [
            "Established brand trust and customer audit history",
            "Senior human auditor team reviewing every line",
            "Large external audited benchmark dataset",
            "Formal verification engine with mathematical proof workflow",
            "Real exploit simulation and protocol-level threat modeling by experts",
            "Legal/compliance-backed signed audit process",
            "24/7 operated monitoring/SLA team",
        ],
        "safe_public_positioning": "AI-powered Web3 pre-audit readiness, human-review workflow, public proof, and continuous monitoring platform.",
        "blocked_public_positioning": ["CertiK replacement", "OpenZeppelin replacement", "Hacken replacement", "certified audit equivalent", "100% secure"],
        "direct_competition_summary": "Strong pre-audit/security-OS foundation; not yet a certified audit-company equivalent until real auditors, external datasets, legal report process, and customer proof exist.",
        "real_only_note": REAL_ONLY_NOTE,
    }


def launch_decision() -> dict[str, Any]:
    checklist = release_checklist()
    runs = _read_runs()
    latest = runs[0] if runs else None
    latest_passed = bool(latest and latest.get("overall_status") in {"passed", "passed_with_warnings"})
    blockers = list(checklist.get("blockers", []))
    if not latest_passed:
        blockers.append(_check("qa_run", "Latest manual QA run", "Manual Required", True, "phase-u", latest, "Record latest local/build/live QA run."))
    decision = "internal_beta_allowed" if not blockers else "hold_until_manual_qa_done"
    return {
        "ok": True,
        "phase": "U",
        "decision": decision,
        "safe_for_public_beta": decision == "internal_beta_allowed",
        "certified_audit_claim_allowed": False,
        "direct_competition_public_claim_allowed": False,
        "latest_run": latest,
        "blockers": blockers,
        "allowed_claim": "Pre-audit readiness and continuous security monitoring platform.",
        "disallowed_claims": sorted(BLOCKED_CLAIMS),
        "next_actions": [
            "Run backend pytest, frontend typecheck, and frontend build.",
            "Open live backend/frontend Phase T and Phase U pages.",
            "Run URL, GitHub, Solidity source/address scans with authorized scope only.",
            "Record QA run result in Phase U after real checks.",
            "Publish only safe pre-audit readiness wording.",
        ],
        "real_only_note": REAL_ONLY_NOTE,
    }


def record_qa_run(payload: dict[str, Any]) -> dict[str, Any]:
    blocked_claims = _has_blocked_claims(payload)
    checks = payload.get("checks") if isinstance(payload.get("checks"), list) else []
    pass_count = sum(1 for item in checks if isinstance(item, dict) and _text(item.get("status")).lower() in {"pass", "passed", "ok"})
    fail_count = sum(1 for item in checks if isinstance(item, dict) and _text(item.get("status")).lower() in {"fail", "failed", "blocked"})
    warning_count = sum(1 for item in checks if isinstance(item, dict) and _text(item.get("status")).lower() in {"warn", "warning", "passed_with_warnings"})
    requested_status = _text(payload.get("overall_status"), "").lower()
    if blocked_claims or fail_count:
        overall_status = "failed"
    elif requested_status in {"passed", "passed_with_warnings", "failed"}:
        overall_status = requested_status
    elif warning_count:
        overall_status = "passed_with_warnings"
    else:
        overall_status = "passed"
    row = {
        "id": new_id("pqa"),
        "created_at": now_iso(),
        "phase": "U",
        "project_name": _text(payload.get("project_name"), "Web3Guard AI"),
        "environment": _text(payload.get("environment"), "production"),
        "overall_status": overall_status,
        "checked_by": _text(payload.get("checked_by"), "manual"),
        "summary": _text(payload.get("summary"), ""),
        "checks": checks,
        "counts": {"passed": pass_count, "failed": fail_count, "warnings": warning_count},
        "blocked_claims": blocked_claims,
        "certified_audit_claim_allowed": False,
        "direct_competition_public_claim_allowed": False,
        "real_only_note": REAL_ONLY_NOTE,
    }
    _append_run(row)
    return {"ok": True, "run": row, "real_only_note": REAL_ONLY_NOTE}


def list_qa_runs(limit: int = 50) -> dict[str, Any]:
    runs = _read_runs()[: max(1, min(int(limit or 50), 200))]
    status_counts = dict(Counter(_text(row.get("overall_status"), "unknown") for row in runs))
    return {"ok": True, "phase": "U", "runs": runs, "count": len(runs), "status_counts": status_counts, "real_only_note": REAL_ONLY_NOTE}
