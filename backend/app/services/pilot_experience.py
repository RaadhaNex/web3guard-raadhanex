from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
FEEDBACK_FILE = DATA_DIR / "pilot_feedback.jsonl"

PHASE = "phase_35_ui_cleanup_pilot_experience_polish"

VISIBLE_JOURNEY = [
    {
        "step": 1,
        "label": "Scan",
        "route": "/scanner/unified-url",
        "primary_action": "Paste one permitted project URL, contract, or repo input.",
        "success_state": "A scan starts only for authorized scope and returns real evidence or Not Assessed states.",
    },
    {
        "step": 2,
        "label": "Results",
        "route": "/results",
        "primary_action": "Review real findings, provider advisories, and setup gaps in one normalized model.",
        "success_state": "User can tell what was assessed, what was not assessed, and what needs setup.",
    },
    {
        "step": 3,
        "label": "Fix Plan",
        "route": "/fix-plan",
        "primary_action": "Prioritize blockers before spending on deeper review.",
        "success_state": "Every fix is tied to a finding, advisory, or manual-review requirement.",
    },
    {
        "step": 4,
        "label": "Report",
        "route": "/report/pilot",
        "primary_action": "Generate a pilot pre-audit readiness report with limitations visible.",
        "success_state": "The report separates assessed modules, Not Assessed modules, external advisories, and manual gaps.",
    },
    {
        "step": 5,
        "label": "Pricing",
        "route": "/pricing",
        "primary_action": "Validate the ₹999 first paid report flow only after payment verification is configured.",
        "success_state": "No fake payment success or fake subscription unlock is shown.",
    },
    {
        "step": 6,
        "label": "Dashboard",
        "route": "/dashboard",
        "primary_action": "Return to saved projects/scans once auth and storage are configured.",
        "success_state": "Existing advanced pages stay available but do not crowd the first-user journey.",
    },
    {
        "step": 7,
        "label": "Docs",
        "route": "/docs",
        "primary_action": "Explain methodology, limitations, setup, and responsible-use boundaries.",
        "success_state": "User understands Web3Guard is pre-audit readiness, not a certified audit.",
    },
]

ADVANCED_AREAS = [
    {
        "group": "Setup and providers",
        "routes": ["/launch-validation", "/provider-live", "/worker-runs", "/payment-validation"],
        "why_hidden": "Useful for operators, but too technical for first-time founder navigation.",
    },
    {
        "group": "Trust and monitoring",
        "routes": ["/security-passport", "/trust-metrics", "/continuous-monitoring", "/sentinel"],
        "why_hidden": "Power features after first scan/report is understood.",
    },
    {
        "group": "Agency and admin",
        "routes": ["/agency-launch", "/community-review", "/admin/payments", "/admin/leads"],
        "why_hidden": "Internal or later-stage workflows, not part of the first paid-user path.",
    },
]

STATE_COPY = {
    "Assessed": {
        "headline": "Real evidence was produced.",
        "user_copy": "This module produced evidence from a rule, tool, provider, or imported output.",
        "next_action": "Review findings and fix the highest severity items first.",
    },
    "Not assessed yet": {
        "headline": "This area has not been checked yet.",
        "user_copy": "No evidence was provided, live lookup was not requested, or the module is outside the current scope.",
        "next_action": "Add the required input or enable a provider/tool before relying on this area.",
    },
    "Needs API Key": {
        "headline": "Provider exists but is not configured.",
        "user_copy": "The integration cannot run until the required backend API key is added securely.",
        "next_action": "Add the provider key in Render/Vercel environment settings. Never paste secrets into the browser.",
    },
    "Tool Not Installed": {
        "headline": "Worker tool is missing.",
        "user_copy": "The scanner cannot run this tool on the current runtime, so no finding is generated.",
        "next_action": "Install the tool or use Docker worker execution, then re-run the check.",
    },
    "Provider Not Configured": {
        "headline": "Live provider is not ready.",
        "user_copy": "Web3Guard will not invent provider data while the integration is unavailable.",
        "next_action": "Open provider setup, add keys, and verify status before using live results.",
    },
    "Manual review required": {
        "headline": "Human review is required.",
        "user_copy": "This area cannot be safely decided by automation alone.",
        "next_action": "Use the output as a checklist and get a qualified manual review before launch.",
    },
}

BLOCKED_COPY_PATTERNS = [
    "100% secure",
    "certified audit",
    "audited by Web3Guard",
    "audit passed",
    "guaranteed secure",
    "discovered by Web3Guard",
    "payment successful without verification",
]

SECRET_LIKE_PATTERNS = [
    re.compile(r"\b(seed phrase|mnemonic|private key|secret key)\b", re.IGNORECASE),
    re.compile(r"\b0x[a-fA-F0-9]{64}\b"),
    re.compile(r"\b[a-z]+(\s+[a-z]+){11,23}\b", re.IGNORECASE),
]


@dataclass(frozen=True)
class FeedbackRecord:
    feedback_id: str
    created_at: str
    page_path: str
    role: str
    friction_area: str
    message: str
    contact_email: str | None
    can_contact: bool
    safety_status: str


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _clean_text(value: Any, *, max_len: int) -> str:
    text = str(value or "").strip()
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", text)
    return text[:max_len]


def check_claim_text(text: str) -> dict[str, Any]:
    lowered = text.lower()
    blocked = [pattern for pattern in BLOCKED_COPY_PATTERNS if pattern.lower() in lowered]
    return {
        "allowed": len(blocked) == 0,
        "blocked_terms": blocked,
        "safe_replacement": "Pre-audit readiness review with visible limitations and Not Assessed states.",
        "rule": "Phase 35 blocks unsafe security/payment/customer claims in pilot UX copy.",
    }


def contains_secret_like_text(text: str) -> bool:
    return any(pattern.search(text or "") for pattern in SECRET_LIKE_PATTERNS)


def get_status() -> dict[str, Any]:
    return {
        "ok": True,
        "phase": PHASE,
        "status": "Pilot UX cleanup ready",
        "visible_path_count": len(VISIBLE_JOURNEY),
        "visible_paths": [item["label"] for item in VISIBLE_JOURNEY],
        "advanced_areas_hidden_from_primary_nav": [item["group"] for item in ADVANCED_AREAS],
        "no_fake_claims": True,
        "blocked_copy_patterns": BLOCKED_COPY_PATTERNS,
        "data_policy": "Feedback is local JSONL in this patch. Do not paste private keys, seed phrases, mnemonics, or secrets.",
    }


def get_journey() -> dict[str, Any]:
    return {
        "ok": True,
        "phase": PHASE,
        "journey": VISIBLE_JOURNEY,
        "advanced_areas": ADVANCED_AREAS,
        "first_user_rule": "One primary path: scan -> results -> fix plan -> pilot report -> verified payment.",
        "do_not_add_to_primary_nav": [route for group in ADVANCED_AREAS for route in group["routes"]],
    }


def get_state_copy() -> dict[str, Any]:
    return {
        "ok": True,
        "phase": PHASE,
        "states": STATE_COPY,
        "ux_rule": "A missing provider/tool is a setup gap, not a finding and not a pass.",
    }


def get_conversion_checklist() -> dict[str, Any]:
    return {
        "ok": True,
        "phase": PHASE,
        "goal": "Help the first 10 users complete a scan and understand a pilot report without confusion.",
        "checklist": [
            {"item": "Primary nav has seven or fewer links", "status": "Ready", "evidence": "Header uses Scanner, Results, Fix Plan, Report, Pricing, Dashboard, Docs."},
            {"item": "Every setup gap has a next action", "status": "Ready", "evidence": "State copy maps Not Assessed, Needs API Key, Tool Not Installed, Provider Not Configured, and Manual review."},
            {"item": "Pilot report keeps limitations visible", "status": "Ready", "evidence": "Report flow separates real findings, not assessed modules, and external advisories."},
            {"item": "Payment CTA never claims access before verification", "status": "Ready", "evidence": "Phase 34 payment validation remains the source of truth."},
            {"item": "User feedback can be collected without secrets", "status": "Ready", "evidence": "Feedback endpoint blocks private key, mnemonic, seed phrase, and raw key-like inputs."},
        ],
        "next_manual_step": "Run 5-10 founder sessions and record where users get stuck before adding more product pages.",
    }


def submit_feedback(payload: dict[str, Any]) -> dict[str, Any]:
    message = _clean_text(payload.get("message"), max_len=1500)
    page_path = _clean_text(payload.get("page_path"), max_len=180) or "/unknown"
    role = _clean_text(payload.get("role"), max_len=80) or "founder"
    friction_area = _clean_text(payload.get("friction_area"), max_len=120) or "general"
    contact_email = _clean_text(payload.get("contact_email"), max_len=180) or None
    can_contact = bool(payload.get("can_contact", False))

    combined = "\n".join([message, page_path, role, friction_area, contact_email or ""])
    if contains_secret_like_text(combined):
        return {
            "ok": False,
            "accepted": False,
            "reason": "Feedback rejected because it appears to contain a private key, seed phrase, mnemonic, or secret-like value.",
            "safe_next_step": "Remove secrets and submit only product feedback.",
        }

    if len(message) < 8:
        return {
            "ok": False,
            "accepted": False,
            "reason": "Please include a short description of what was confusing or useful.",
            "safe_next_step": "Example: Results page was clear, but payment setup status was confusing.",
        }

    record = FeedbackRecord(
        feedback_id=f"pux_{uuid4().hex[:12]}",
        created_at=_utc_now(),
        page_path=page_path,
        role=role,
        friction_area=friction_area,
        message=message,
        contact_email=contact_email,
        can_contact=can_contact,
        safety_status="accepted_no_secret_detected",
    )

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with FEEDBACK_FILE.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(asdict(record), ensure_ascii=False) + "\n")

    return {
        "ok": True,
        "accepted": True,
        "feedback_id": record.feedback_id,
        "stored_as": "local_jsonl",
        "message": "Feedback saved for pilot UX review. No security result, payment success, or customer claim was generated.",
    }
