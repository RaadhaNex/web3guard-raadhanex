from __future__ import annotations

from typing import Any

from app.core.config import settings
from app.models.schemas import BugBountyProgramCreate, BugBountyProgramUpdate, BugBountySubmissionCreate, BugBountySubmissionUpdate
from app.services.mega_phase_d_store import MEGA_PHASE_D_REAL_ONLY_NOTE, append_jsonl, new_id, now_iso, read_jsonl, rewrite_jsonl, sort_created, storage_path

SAFE_HARBOR_TEMPLATE = """Good-faith security research is welcome only within the listed scope. Do not access user data, do not perform denial-of-service, do not exploit third-party systems, do not social engineer, and stop testing if you can demonstrate impact safely. This template is not legal advice and must be reviewed before public launch."""
SEVERITY_TEMPLATE = {
    "critical": "Funds can be directly stolen, mint/treasury/admin control is compromised, or unauthenticated critical action is possible.",
    "high": "Material loss, privilege escalation, or exploit path exists but requires conditions or limited access.",
    "medium": "Security weakness with meaningful impact, limited blast radius, or missing protection.",
    "low": "Hardening issue, disclosure gap, or low-impact misconfiguration.",
    "info": "Best-practice note or documentation improvement.",
}


def bug_bounty_status() -> dict[str, Any]:
    return {
        "ok": True,
        "phase": "Mega Phase D - Phase 25 Bug Bounty Readiness + Marketplace MVP",
        "version": "1.0",
        "enabled": True,
        "live_capabilities": [
            "Create real bounty readiness records",
            "Store scope, safe-harbor, reward tier, and contact details",
            "Accept researcher submissions as real triage records",
            "Update triage status manually",
        ],
        "not_claimed": [
            "No escrow is active unless a real escrow/payment provider is integrated",
            "No automatic vulnerability validation",
            "No researcher KYC/payment automation",
            "No fake public bug bounty activity",
        ],
        "safe_harbor_template": SAFE_HARBOR_TEMPLATE,
        "severity_template": SEVERITY_TEMPLATE,
        "real_only_note": MEGA_PHASE_D_REAL_ONLY_NOTE,
    }


def _program_path():
    return storage_path(settings.bug_bounty_programs_file)


def _submission_path():
    return storage_path(settings.bug_bounty_submissions_file)


def create_program(payload: BugBountyProgramCreate, user_id: str | None = None) -> dict[str, Any]:
    if not payload.authorization_confirmed:
        raise ValueError("Authorization confirmation is required")
    if not payload.real_only_acknowledged:
        raise ValueError("Real-only acknowledgement is required")
    if payload.escrow_enabled:
        raise ValueError("Escrow cannot be enabled in MVP without a real escrow/payment integration")
    now = now_iso()
    row = {
        "id": new_id("bounty"),
        "user_id": user_id or payload.user_id,
        "organization_id": payload.organization_id,
        "project_id": payload.project_id,
        "project_name": payload.project_name,
        "website_url": payload.website_url,
        "scope_summary": payload.scope_summary,
        "in_scope_assets": payload.in_scope_assets,
        "out_of_scope_assets": payload.out_of_scope_assets,
        "reward_low_inr": payload.reward_low_inr,
        "reward_medium_inr": payload.reward_medium_inr,
        "reward_high_inr": payload.reward_high_inr,
        "reward_critical_inr": payload.reward_critical_inr,
        "safe_harbor_text": payload.safe_harbor_text or SAFE_HARBOR_TEMPLATE,
        "contact_email": str(payload.contact_email) if payload.contact_email else None,
        "contact_handle": payload.contact_handle,
        "status": payload.status,
        "escrow_status": "not_enabled_manual_rewards_only",
        "created_at": now,
        "updated_at": now,
        "real_only_note": "Bounty is a real readiness/triage record. Escrow and automated payouts are not enabled.",
    }
    append_jsonl(_program_path(), row)
    return row


def list_programs(status: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
    rows = read_jsonl(_program_path())
    if status:
        rows = [r for r in rows if r.get("status") == status]
    return sort_created(rows)[:limit]


def get_program(program_id: str) -> dict[str, Any] | None:
    return next((r for r in read_jsonl(_program_path()) if r.get("id") == program_id), None)


def update_program(program_id: str, payload: BugBountyProgramUpdate) -> dict[str, Any] | None:
    path = _program_path(); rows = read_jsonl(path); updated = None
    patch = {k: (str(v) if k == "contact_email" and v is not None else v) for k, v in payload.model_dump().items() if v is not None}
    patch["updated_at"] = now_iso()
    for row in rows:
        if row.get("id") == program_id:
            row.update(patch); updated = row; break
    rewrite_jsonl(path, rows)
    return updated


def create_submission(payload: BugBountySubmissionCreate) -> dict[str, Any]:
    if not payload.authorization_confirmed or not payload.safe_testing_acknowledged:
        raise ValueError("Authorization and safe-testing acknowledgements are required")
    if not payload.real_only_acknowledged:
        raise ValueError("Real-only acknowledgement is required")
    program = get_program(payload.program_id)
    if not program:
        raise ValueError("Bug bounty program not found")
    now = now_iso()
    row = {
        "id": new_id("submission"),
        "program_id": payload.program_id,
        "researcher_name": payload.researcher_name,
        "researcher_contact": payload.researcher_contact,
        "title": payload.title,
        "severity_claimed": payload.severity_claimed,
        "affected_asset": payload.affected_asset,
        "description": payload.description,
        "reproduction_steps": payload.reproduction_steps,
        "impact": payload.impact,
        "recommendation": payload.recommendation,
        "proof_links": payload.proof_links,
        "status": "submitted",
        "triage_notes": None,
        "final_severity": None,
        "reward_amount_inr": None,
        "created_at": now,
        "updated_at": now,
        "real_only_note": "Submission is stored for manual triage. It is not automatically validated or paid.",
    }
    append_jsonl(_submission_path(), row)
    return row


def list_submissions(program_id: str | None = None, status: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
    rows = read_jsonl(_submission_path())
    if program_id:
        rows = [r for r in rows if r.get("program_id") == program_id]
    if status:
        rows = [r for r in rows if r.get("status") == status]
    return sort_created(rows)[:limit]


def update_submission(submission_id: str, payload: BugBountySubmissionUpdate) -> dict[str, Any] | None:
    path = _submission_path(); rows = read_jsonl(path); updated = None
    patch = {k: v for k, v in payload.model_dump().items() if v is not None}
    patch["updated_at"] = now_iso()
    for row in rows:
        if row.get("id") == submission_id:
            row.update(patch); updated = row; break
    rewrite_jsonl(path, rows)
    return updated


def bounty_dashboard() -> dict[str, Any]:
    programs = list_programs(limit=1000)
    submissions = list_submissions(limit=1000)
    return {
        "program_count": len(programs),
        "published_count": sum(1 for p in programs if p.get("status") == "published"),
        "submission_count": len(submissions),
        "open_submission_count": sum(1 for s in submissions if s.get("status") in {"submitted", "triage", "needs_more_info"}),
        "programs": programs[:10],
        "recent_submissions": submissions[:10],
        "real_only_note": MEGA_PHASE_D_REAL_ONLY_NOTE,
    }
