from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
PILOT_USERS_FILE = DATA_DIR / "first_10_pilot_users.jsonl"

PHASE = "phase_36_mvp_launch_pack_first_10_users_sprint"

BLOCKED_CLAIM_PATTERNS = [
    "100% secure",
    "certified audit",
    "audited by Web3Guard",
    "audit passed",
    "guaranteed secure",
    "discovered by Web3Guard",
    "payment successful without verification",
    "official audit certificate",
    "bug bounty marketplace",
]

SECRET_LIKE_PATTERNS = [
    re.compile(r"\b(seed phrase|mnemonic|private key|secret key|api key|access token)\b", re.IGNORECASE),
    re.compile(r"\b0x[a-fA-F0-9]{64}\b"),
    re.compile(r"\b[a-z]+(\s+[a-z]+){11,23}\b", re.IGNORECASE),
]

FIRST_10_TRACKER_COLUMNS = [
    "pilot_id",
    "project_name",
    "founder_segment",
    "source_channel",
    "stage",
    "paid_intent",
    "highest_friction",
    "next_action",
]

LAUNCH_CHECKLIST = [
    {
        "group": "Apply and verify code",
        "items": [
            "Apply Phase 31, Phase 32, Phase 33, Phase 34, Phase 35, and Phase 36 patches in order.",
            "Run backend tests: cd backend && python -m pytest -q.",
            "Run frontend checks: cd frontend && npm run typecheck && npm run build.",
            "Do not ship if the result engine cannot clearly show Assessed, Not Assessed, Tool Not Installed, or Needs API Key states.",
        ],
    },
    {
        "group": "Deploy safely",
        "items": [
            "Deploy frontend on Vercel with NEXT_PUBLIC_API_BASE_URL pointing to the Render backend.",
            "Deploy backend on Render with only required env vars and no secrets in frontend code.",
            "Verify /health, /launch-validation/status, /scanner-results/status, /worker-runs/status, and /payment-validation/status.",
            "Keep tools/providers truthful: missing Slither/Semgrep/API keys must remain Tool Not Installed or Needs API Key.",
        ],
    },
    {
        "group": "Revenue validation",
        "items": [
            "Enable Razorpay test mode first and verify order, signature, webhook, and idempotency behavior.",
            "Use the ₹999 Quick Risk Scan Report as the first paid offer only after payment verification is configured.",
            "Never show fake payment success, fake subscription unlock, or fake customer proof.",
        ],
    },
    {
        "group": "First 10 users",
        "items": [
            "Contact Indian Web3 founders, hackathon teams, small dApp teams, and agencies with authorized-scope messaging.",
            "Ask users to run one permitted project and generate a pilot report.",
            "Collect confusion points on Results, Fix Plan, Report, Pricing, and Tool Not Installed states.",
            "Do not add new feature pages until at least 10 real founder sessions are completed.",
        ],
    },
]

OUTREACH_TEMPLATES = [
    {
        "channel": "Twitter / X DM",
        "audience": "Indian Web3 founder",
        "message": "Hey, I am building Web3Guard AI by RAADHANEX — a pre-audit launch readiness scanner for Web3 founders. It checks permitted project scope across website, dApp, API, GitHub, wallet/admin readiness, and smart contract/static-analysis status. It is not a certified audit. Want me to run a pilot readiness report for your project and share the gaps before launch?",
        "cta": "Ask for one authorized URL/repo/contract scope and permission to review.",
    },
    {
        "channel": "ETHIndia / Discord",
        "audience": "Hackathon team",
        "message": "I am offering a limited pilot of Web3Guard AI for hackathon teams: pre-audit launch readiness report, Not Assessed transparency, fix-priority checklist, and no private key/wallet signing requirement. If you have a deployed demo or repo, I can help you see launch blockers before submission.",
        "cta": "Invite them to share public demo scope only; no secrets.",
    },
    {
        "channel": "Agency outreach",
        "audience": "Web3 dev agency",
        "message": "Web3Guard AI helps agencies prepare client projects before professional audits: scanner results, setup gaps, provider/tool readiness, pilot report, and safe trust-page wording. It does not replace human audit, but it can reduce handoff confusion.",
        "cta": "Offer a free/low-cost first client readiness report.",
    },
]

SAMPLE_REPORT_TEMPLATE = {
    "title": "Web3Guard AI Pilot Pre-Audit Readiness Report",
    "required_sections": [
        "Project name and authorized scope",
        "Scan timestamp and environment",
        "Assessed modules with evidence source",
        "Not Assessed modules and why",
        "Tool Not Installed / Needs API Key modules",
        "Static-analysis findings if real tool evidence exists",
        "External advisories from provider data, counted separately",
        "Fix plan with priority order",
        "Limitations and human audit recommendation",
        "No private key, no seed phrase, no wallet signing, no exploit automation policy",
    ],
    "safe_opening_copy": "This is a pre-audit launch readiness report generated from visible evidence and configured tools/providers. It is not a certified audit and does not guarantee security.",
    "safe_close_copy": "Use this report to prepare for professional security review, founder due diligence, and launch readiness. Manual review is still required for business logic, economic attacks, and complete audit assurance.",
}

WHAT_TO_SAY = [
    "Web3Guard AI is a pre-audit launch readiness scanner for Web3 founders.",
    "It helps identify setup gaps, real tool findings, external advisories, and launch blockers before a professional audit.",
    "Missing providers/tools are shown as Not Assessed, Tool Not Installed, or Needs API Key.",
    "The pilot report is a preparation document, not a certified audit report.",
]

WHAT_NOT_TO_CLAIM = [
    "Do not claim 100% secure.",
    "Do not claim certified audit.",
    "Do not claim audited by Web3Guard.",
    "Do not claim payment success or subscription unlock unless verified by Razorpay backend verification.",
    "Do not claim discovered by Web3Guard unless the finding was actually generated and verified by Web3Guard evidence.",
    "Do not present Web3Guard as a bug bounty marketplace until real researcher, safe-harbor, triage, and payout operations exist.",
]

PRODUCT_HUNT_PREP = [
    "Position as pre-audit launch readiness, not audit replacement.",
    "Use screenshots of Scanner, Results, Pilot Report, Payment Validation, and Launch Pack only after they work locally.",
    "Show a sample report with SAMPLE / DEMO labels if it is not from a real permitted project.",
    "Prepare one-line pitch: Web3Guard AI helps Web3 founders find launch readiness gaps before audit.",
    "Prepare first comment with limitations: not a certified audit, no private keys, no wallet signing, no exploit automation.",
]

@dataclass(frozen=True)
class PilotUserRecord:
    pilot_id: str
    created_at: str
    project_name: str
    founder_segment: str
    source_channel: str
    stage: str
    paid_intent: str
    highest_friction: str
    next_action: str
    safe_contact_note: str | None


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _clean_text(value: Any, *, max_len: int) -> str:
    text = str(value or "").strip()
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", text)
    return text[:max_len]


def contains_secret_like_text(text: str) -> bool:
    return any(pattern.search(text or "") for pattern in SECRET_LIKE_PATTERNS)


def check_claim_text(text: str) -> dict[str, Any]:
    lowered = text.lower()
    blocked = [pattern for pattern in BLOCKED_CLAIM_PATTERNS if pattern.lower() in lowered]
    return {
        "allowed": len(blocked) == 0,
        "blocked_terms": blocked,
        "safe_replacement": "Pre-audit launch readiness report with visible evidence, limitations, and Not Assessed states.",
        "rule": "Phase 36 blocks fake audit, fake payment, fake customer, and fake discovery claims before public launch.",
    }


def get_status() -> dict[str, Any]:
    return {
        "ok": True,
        "phase": PHASE,
        "status": "MVP launch pack ready",
        "build_phase_status": "Stop adding new feature phases after this. Apply, test, deploy, and get first users.",
        "primary_goal": "Get 10 real founder sessions and validate the first paid pilot report flow.",
        "visible_user_path": ["Scanner", "Results", "Fix Plan", "Report", "Pricing", "Dashboard", "Docs"],
        "no_fake_claims": True,
        "blocked_claim_patterns": BLOCKED_CLAIM_PATTERNS,
        "data_policy": "Pilot tracker is local JSONL in this patch. Do not store private keys, seed phrases, mnemonics, API keys, or secrets.",
    }


def get_launch_checklist() -> dict[str, Any]:
    return {
        "ok": True,
        "phase": PHASE,
        "checklist": LAUNCH_CHECKLIST,
        "exit_criteria": [
            "Backend tests pass.",
            "Frontend typecheck passes.",
            "Frontend production build passes locally or on Vercel.",
            "One sample pilot report can be generated without fake results.",
            "One Razorpay test checkout is verified before any paid claim.",
            "At least 10 user conversations are tracked before more product pages are added.",
        ],
    }


def get_outreach_kit() -> dict[str, Any]:
    return {
        "ok": True,
        "phase": PHASE,
        "templates": OUTREACH_TEMPLATES,
        "daily_action_plan": [
            "Send 10 targeted messages to Indian Web3 founders or hackathon teams.",
            "Book 2 short feedback calls or async reviews.",
            "Run only authorized project scopes.",
            "Record friction in the First 10 tracker.",
            "Do not promise certified audit or guaranteed security.",
        ],
        "target_segments": ["hackathon teams", "small dApp founders", "Web3 agencies", "NFT/token launch teams", "student founders"],
    }


def get_sample_report_template() -> dict[str, Any]:
    return {
        "ok": True,
        "phase": PHASE,
        "template": SAMPLE_REPORT_TEMPLATE,
        "report_price_anchor_inr": 999,
        "payment_truth_rule": "Only unlock/report-deliver paid flow after backend payment verification. Test mode must be labeled as test mode.",
    }


def get_public_beta_checklist() -> dict[str, Any]:
    return {
        "ok": True,
        "phase": PHASE,
        "product_hunt_prep": PRODUCT_HUNT_PREP,
        "public_beta_assets": [
            "Honest landing page copy",
            "Scanner screenshot",
            "Results screenshot with Not Assessed states visible",
            "Pilot report sample clearly labeled SAMPLE",
            "Limitations page",
            "Responsible use page",
            "Pricing/status page",
        ],
        "do_not_launch_if": [
            "Frontend build fails locally/Vercel.",
            "Payment CTA can show success without backend verification.",
            "Any page claims certified audit, 100% secure, or audited by Web3Guard.",
            "The scanner creates findings when tools/providers did not run.",
        ],
    }


def get_claim_guidance() -> dict[str, Any]:
    return {
        "ok": True,
        "phase": PHASE,
        "what_to_say": WHAT_TO_SAY,
        "what_not_to_claim": WHAT_NOT_TO_CLAIM,
        "positioning": "Affordable pre-audit readiness for Web3 founders, especially India-first teams, not a replacement for CertiK/OpenZeppelin/Hacken-style professional audits.",
    }


def list_pilot_users(limit: int = 10) -> dict[str, Any]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    records: list[dict[str, Any]] = []
    if PILOT_USERS_FILE.exists():
        for line in PILOT_USERS_FILE.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    records = records[-max(1, min(limit, 50)):]
    return {
        "ok": True,
        "phase": PHASE,
        "columns": FIRST_10_TRACKER_COLUMNS,
        "target_count": 10,
        "current_count": len(records),
        "remaining": max(0, 10 - len(records)),
        "records": records,
        "storage": "local_jsonl",
        "next_rule": "Do not add new feature pages until real pilot friction is reviewed.",
    }


def add_pilot_user(payload: dict[str, Any]) -> dict[str, Any]:
    project_name = _clean_text(payload.get("project_name"), max_len=120) or "Unnamed pilot project"
    founder_segment = _clean_text(payload.get("founder_segment"), max_len=100) or "web3 founder"
    source_channel = _clean_text(payload.get("source_channel"), max_len=100) or "manual outreach"
    stage = _clean_text(payload.get("stage"), max_len=80) or "contacted"
    paid_intent = _clean_text(payload.get("paid_intent"), max_len=80) or "unknown"
    highest_friction = _clean_text(payload.get("highest_friction"), max_len=240) or "not recorded"
    next_action = _clean_text(payload.get("next_action"), max_len=240) or "book review"
    safe_contact_note = _clean_text(payload.get("safe_contact_note"), max_len=240) or None

    combined = "\n".join([
        project_name,
        founder_segment,
        source_channel,
        stage,
        paid_intent,
        highest_friction,
        next_action,
        safe_contact_note or "",
    ])
    if contains_secret_like_text(combined):
        return {
            "ok": False,
            "accepted": False,
            "reason": "Pilot tracker rejected because it appears to contain a private key, seed phrase, mnemonic, API key, token, or secret-like value.",
            "safe_next_step": "Remove secrets and save only user/outreach status.",
        }

    record = PilotUserRecord(
        pilot_id=f"mvp_{uuid4().hex[:12]}",
        created_at=_utc_now(),
        project_name=project_name,
        founder_segment=founder_segment,
        source_channel=source_channel,
        stage=stage,
        paid_intent=paid_intent,
        highest_friction=highest_friction,
        next_action=next_action,
        safe_contact_note=safe_contact_note,
    )
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with PILOT_USERS_FILE.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(asdict(record), ensure_ascii=False) + "\n")

    tracker = list_pilot_users(limit=10)
    return {
        "ok": True,
        "accepted": True,
        "pilot_id": record.pilot_id,
        "stored_as": "local_jsonl",
        "current_count": tracker["current_count"],
        "remaining": tracker["remaining"],
        "message": "Pilot user saved. Use this data to fix real friction before adding more features.",
    }
