from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.services.database_store import get_project, list_projects, list_reports, list_scans
from app.services.trust_readiness import build_trust_readiness
from app.services.public_trust_page import build_public_trust_page
from app.services.continuous_monitoring import user_dashboard

INDIA_LAUNCH_NOTE = (
    "India Launch Pack converts stored Web3Guard readiness evidence into Hindi/Hinglish founder-facing guidance, "
    "investor due-diligence summaries, hackathon checklists, and OpSec reminders. It is not a certified audit, legal opinion, "
    "financial advice, investment advice, or proof that a project is secure."
)

BLOCKED_WORDING = [
    "audited by Web3Guard",
    "certified secure",
    "100% secure",
    "guaranteed safe",
    "exploit-free",
    "government approved",
    "RBI/SEBI approved unless a real approval exists",
]

LANGUAGE_MODES = [
    {"id": "english", "label": "English", "description": "Clean professional founder copy."},
    {"id": "hinglish", "label": "Hinglish", "description": "Simple Hindi + English mix for Indian founders."},
    {"id": "hindi", "label": "Hindi", "description": "Devanagari-friendly plain Hindi guidance."},
]

PACK_SECTIONS = [
    "Founder launch checklist",
    "Investor due-diligence summary",
    "Hackathon demo safety pack",
    "Founder/Admin OpSec in Hindi/Hinglish",
    "Public trust page Hindi summary",
    "UPI/payment safety wording",
]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _as_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return str(value)


def _safe_readiness(user_id: str, project_id: str | None) -> dict[str, Any]:
    try:
        return build_trust_readiness(user_id=user_id, project_id=project_id)
    except Exception as exc:
        return {"ok": False, "score": 0, "label": "Not Assessed", "priority_actions": [], "error": str(exc)}


def _safe_public_trust(user_id: str, project_id: str | None) -> dict[str, Any]:
    if not project_id:
        return {"ok": False, "module_statuses": [], "evidence_summary": [], "fix_status": {}, "disclosure": {}}
    try:
        return build_public_trust_page(user_id=user_id, project_id=project_id)
    except Exception as exc:
        return {"ok": False, "module_statuses": [], "evidence_summary": [], "fix_status": {}, "disclosure": {}, "error": str(exc)}


def _safe_monitoring(user_id: str) -> dict[str, Any]:
    try:
        return user_dashboard(user_id=user_id)
    except Exception as exc:
        return {"ok": False, "configs": [], "alerts": [], "error": str(exc)}


def _mode_text(mode: str, english: str, hinglish: str, hindi: str) -> str:
    clean = (mode or "hinglish").lower()
    if clean == "hindi":
        return hindi
    if clean == "english":
        return english
    return hinglish


def _project_name(project: Any | None, fallback: str = "Your Web3 project") -> str:
    return _as_text(getattr(project, "name", None) or fallback)


def _score_label(readiness: dict[str, Any]) -> tuple[int, str]:
    score = readiness.get("score") or readiness.get("overall_score") or readiness.get("readiness_score") or 0
    try:
        score_int = int(score)
    except Exception:
        score_int = 0
    label = readiness.get("label") or readiness.get("readiness_label") or readiness.get("public_label") or "Not Assessed"
    return max(0, min(100, score_int)), str(label)


def _priority_actions(readiness: dict[str, Any], trust_page: dict[str, Any], monitoring: dict[str, Any]) -> list[dict[str, str]]:
    actions: list[dict[str, str]] = []
    for item in readiness.get("priority_actions") or readiness.get("actions") or []:
        if isinstance(item, dict):
            title = _as_text(item.get("title") or item.get("action") or item.get("label"))
            reason = _as_text(item.get("reason") or item.get("description") or item.get("why"))
        else:
            title = _as_text(item)
            reason = "Readiness action generated from stored project evidence."
        if title:
            actions.append({"title": title, "reason": reason or "Readiness action generated from stored project evidence."})

    module_rows = trust_page.get("module_statuses") or trust_page.get("modules") or []
    for row in module_rows[:8] if isinstance(module_rows, list) else []:
        status = _as_text(row.get("status") or row.get("public_label")).lower()
        title = _as_text(row.get("label") or row.get("module") or row.get("id"))
        if title and "not assessed" in status:
            actions.append({"title": f"Add evidence for {title}", "reason": "This module is still Not Assessed, so public launch readiness stays limited."})

    alerts = monitoring.get("alerts") or []
    for alert in alerts[:5] if isinstance(alerts, list) else []:
        title = _as_text(alert.get("title") or alert.get("message") or alert.get("type"))
        if title:
            actions.append({"title": title, "reason": "Monitoring alert requires founder/admin review before public launch."})

    if not actions:
        actions.append({"title": "Run a fresh unified scan", "reason": "No stored priority action was found. Re-run scan to refresh evidence before public sharing."})
    return actions[:10]


def _founder_checklist(mode: str, project_name: str, actions: list[dict[str, str]]) -> list[dict[str, str]]:
    base = [
        (
            "Complete required evidence",
            "Add website, contract, GitHub, wallet, admin OpSec, report, monitoring, and disclosure evidence before public launch.",
            "Required evidence complete karo",
            "Website, contract, GitHub, wallet, admin OpSec, report, monitoring aur disclosure evidence add karo public launch se pehle.",
            "आवश्यक evidence पूरा करें",
            "Public launch से पहले website, contract, GitHub, wallet, admin OpSec, report, monitoring और disclosure evidence जोड़ें।",
        ),
        (
            "Keep Not Assessed visible",
            "Do not hide missing modules. Treat Not Assessed as an honest trust signal, not as a failure to cover up.",
            "Not Assessed ko hide mat karo",
            "Missing modules ko clearly dikhana trust build karta hai. Fake score mat dikhana.",
            "Not Assessed को छिपाएँ नहीं",
            "Missing modules को साफ़ दिखाना trust build करता है। Fake score न दिखाएँ।",
        ),
        (
            "Verify payment and admin access",
            "Use backend-verified payments only. Keep admin roles, MFA, multisig, and incident contacts documented.",
            "Payment aur admin access verify karo",
            "Sirf backend-verified payment use karo. Admin roles, MFA, multisig aur incident contacts document karo.",
            "Payment और admin access verify करें",
            "सिर्फ backend-verified payment use करें। Admin roles, MFA, multisig और incident contacts document करें।",
        ),
    ]

    rows = [
        {
            "title": _mode_text(mode, english, hinglish, hindi),
            "description": _mode_text(mode, english_desc, hinglish_desc, hindi_desc),
            "status": "manual_review_required",
        }
        for english, english_desc, hinglish, hinglish_desc, hindi, hindi_desc in base
    ]

    for action in actions[:5]:
        rows.append(
            {
                "title": _mode_text(mode, f"Project action: {action['title']}", f"Project action: {action['title']}", f"Project action: {action['title']}"),
                "description": action.get("reason") or f"Review this before launching {project_name}.",
                "status": "open",
            }
        )
    return rows


def _investor_summary(mode: str, project_name: str, score: int, label: str, reports_count: int, scans_count: int) -> dict[str, Any]:
    return {
        "title": _mode_text(mode, "Investor due-diligence summary", "Investor due-diligence summary", "निवेशक due-diligence summary"),
        "one_liner": _mode_text(
            mode,
            f"{project_name} has a Web3Guard Launch Trust Readiness status of {score}/100 ({label}) based on stored pre-audit evidence.",
            f"{project_name} ka Launch Trust Readiness {score}/100 ({label}) hai, jo stored pre-audit evidence ke basis par hai.",
            f"{project_name} की Launch Trust Readiness {score}/100 ({label}) है, जो stored pre-audit evidence पर आधारित है।",
        ),
        "safe_disclaimer": _mode_text(
            mode,
            "This summary is pre-audit readiness information only. It is not a certified audit, legal opinion, or guarantee of safety.",
            "Ye sirf pre-audit readiness summary hai. Ye certified audit, legal opinion ya safety guarantee nahi hai.",
            "यह केवल pre-audit readiness summary है। यह certified audit, legal opinion या safety guarantee नहीं है।",
        ),
        "evidence_counts": {"stored_scans": scans_count, "stored_reports": reports_count},
        "recommended_investor_questions": [
            _mode_text(mode, "Which Not Assessed modules remain before public launch?", "Public launch se pehle kaunse modules Not Assessed hain?", "Public launch से पहले कौनसे modules Not Assessed हैं?"),
            _mode_text(mode, "Which critical/high findings are still open?", "Kaunse critical/high findings abhi open hain?", "कौनसे critical/high findings अभी open हैं?"),
            _mode_text(mode, "Is there a responsible disclosure contact and incident response owner?", "Responsible disclosure contact aur incident response owner hai?", "क्या responsible disclosure contact और incident response owner है?"),
        ],
    }


def _hackathon_pack(mode: str) -> list[dict[str, str]]:
    items = [
        ("Demo boundary slide", "State that Web3Guard output is pre-audit readiness only, not a certified audit."),
        ("Safe testnet demo", "Use testnet/demo data where possible. Do not ask judges/users to sign risky transactions."),
        ("Quick security.txt", "Publish security contact and disclosure scope before demo day."),
        ("Fix-first story", "Show what risk was found, what was fixed, and what still needs manual review."),
    ]
    result = []
    for title, desc in items:
        result.append(
            {
                "title": _mode_text(mode, title, title, title),
                "description": _mode_text(mode, desc, desc.replace("State", "Clearly bolo ki"), desc),
            }
        )
    return result


def _opsec_pack(mode: str) -> list[dict[str, str]]:
    items = [
        (
            "Founder/admin access",
            "Use MFA, strong password manager, no shared admin password, and separate owner/reviewer accounts.",
            "Founder/admin access",
            "MFA use karo, password manager rakho, shared admin password mat use karo, owner/reviewer accounts alag rakho.",
            "Founder/admin access",
            "MFA use करें, password manager रखें, shared admin password न रखें, owner/reviewer accounts अलग रखें।",
        ),
        (
            "Treasury and signer safety",
            "Document multisig, signer rotation, timelock, emergency pause owner, and recovery contacts.",
            "Treasury aur signer safety",
            "Multisig, signer rotation, timelock, emergency pause owner aur recovery contacts document karo.",
            "Treasury और signer safety",
            "Multisig, signer rotation, timelock, emergency pause owner और recovery contacts document करें।",
        ),
        (
            "No secrets in chat or repo",
            "Never paste private keys, seed phrases, mnemonics, API secrets, or customer data into scanner inputs.",
            "Chat ya repo mein secrets mat rakho",
            "Private key, seed phrase, mnemonic, API secret ya customer data scanner mein kabhi paste mat karo.",
            "Chat या repo में secrets न रखें",
            "Private key, seed phrase, mnemonic, API secret या customer data scanner में कभी paste न करें।",
        ),
    ]
    return [{"title": _mode_text(mode, e, h, hi), "description": _mode_text(mode, ed, hd, hid)} for e, ed, h, hd, hi, hid in items]


def _public_trust_summary(mode: str, project_name: str, score: int, label: str, not_assessed_count: int) -> dict[str, str]:
    return {
        "headline": _mode_text(
            mode,
            f"{project_name} has a pre-audit launch readiness summary.",
            f"{project_name} ka pre-audit launch readiness summary ready hai.",
            f"{project_name} की pre-audit launch readiness summary उपलब्ध है।",
        ),
        "summary": _mode_text(
            mode,
            f"Launch Trust Readiness: {score}/100 ({label}). {not_assessed_count} module(s) still require evidence or manual review.",
            f"Launch Trust Readiness: {score}/100 ({label}). {not_assessed_count} module(s) ko abhi evidence ya manual review chahiye.",
            f"Launch Trust Readiness: {score}/100 ({label}). {not_assessed_count} module(s) को अभी evidence या manual review चाहिए।",
        ),
        "disclaimer": _mode_text(
            mode,
            "This is not an audit badge. It is a transparent pre-audit readiness snapshot.",
            "Ye audit badge nahi hai. Ye transparent pre-audit readiness snapshot hai.",
            "यह audit badge नहीं है। यह transparent pre-audit readiness snapshot है।",
        ),
    }


def _payment_wording(mode: str) -> list[dict[str, str]]:
    return [
        {
            "title": _mode_text(mode, "UPI payment safety", "UPI payment safety", "UPI payment safety"),
            "copy": _mode_text(
                mode,
                "Paid access unlocks only after backend-verified Razorpay/UPI records. Screenshot-only payment proof is manual review, not instant plan unlock.",
                "Paid access sirf backend-verified Razorpay/UPI record ke baad unlock hoga. Screenshot-only proof manual review hai, instant unlock nahi.",
                "Paid access सिर्फ backend-verified Razorpay/UPI record के बाद unlock होगा। Screenshot-only proof manual review है, instant unlock नहीं।",
            ),
        },
        {
            "title": _mode_text(mode, "Security wording", "Security wording", "Security wording"),
            "copy": _mode_text(
                mode,
                "Never ask users for seed phrases, private keys, or wallet signing during payment or scanning.",
                "Payment ya scanning ke time user se seed phrase, private key ya wallet signing kabhi mat mango.",
                "Payment या scanning के समय user से seed phrase, private key या wallet signing कभी न माँगें।",
            ),
        },
    ]


def india_launch_status() -> dict[str, Any]:
    return {
        "ok": True,
        "phase": "21",
        "name": "India Launch Pack",
        "description": "Hindi/Hinglish founder launch guidance, investor summaries, hackathon pack, founder OpSec, and public trust summaries generated from stored readiness evidence.",
        "language_modes": LANGUAGE_MODES,
        "sections": PACK_SECTIONS,
        "blocked_wording": BLOCKED_WORDING,
        "note": INDIA_LAUNCH_NOTE,
    }


def build_india_launch_pack(user_id: str, project_id: str | None = None, mode: str = "hinglish") -> dict[str, Any]:
    projects = list_projects(user_id=user_id, limit=50)
    project = get_project(user_id=user_id, project_id=project_id) if project_id else (projects[0] if projects else None)
    active_project_id = project_id or (getattr(project, "id", None) if project else None)
    name = _project_name(project)

    scans = list_scans(user_id=user_id, limit=100, project_id=active_project_id) if active_project_id else list_scans(user_id=user_id, limit=100)
    reports = list_reports(user_id=user_id, limit=50, project_id=active_project_id) if active_project_id else list_reports(user_id=user_id, limit=50)
    readiness = _safe_readiness(user_id=user_id, project_id=active_project_id)
    trust_page = _safe_public_trust(user_id=user_id, project_id=active_project_id)
    monitoring = _safe_monitoring(user_id=user_id)
    score, label = _score_label(readiness)

    module_rows = trust_page.get("module_statuses") or trust_page.get("modules") or []
    not_assessed_count = 0
    if isinstance(module_rows, list):
        not_assessed_count = sum(1 for row in module_rows if "not assessed" in _as_text(row.get("status") or row.get("public_label")).lower())

    actions = _priority_actions(readiness=readiness, trust_page=trust_page, monitoring=monitoring)

    return {
        "ok": True,
        "generated_at": _now(),
        "mode": mode if mode in {"english", "hinglish", "hindi"} else "hinglish",
        "user_id": user_id,
        "project": {
            "id": active_project_id,
            "name": name,
            "website_url": getattr(project, "website_url", None) if project else None,
            "chain": getattr(project, "chain", None) if project else None,
            "project_type": getattr(project, "project_type", None) if project else None,
        },
        "readiness": {"score": score, "label": label, "note": "Launch Trust Readiness only; not an audit score."},
        "founder_checklist": _founder_checklist(mode, name, actions),
        "investor_summary": _investor_summary(mode, name, score, label, len(reports), len(scans)),
        "hackathon_pack": _hackathon_pack(mode),
        "founder_opsec": _opsec_pack(mode),
        "public_trust_summary": _public_trust_summary(mode, name, score, label, not_assessed_count),
        "payment_security_wording": _payment_wording(mode),
        "priority_actions": actions,
        "safe_share_copy": _mode_text(
            mode,
            f"{name} has a Web3Guard pre-audit launch readiness snapshot. This is not a certified audit and does not guarantee safety.",
            f"{name} ke paas Web3Guard pre-audit launch readiness snapshot hai. Ye certified audit nahi hai aur safety guarantee nahi karta.",
            f"{name} के पास Web3Guard pre-audit launch readiness snapshot है। यह certified audit नहीं है और safety guarantee नहीं करता।",
        ),
        "blocked_wording": BLOCKED_WORDING,
        "note": INDIA_LAUNCH_NOTE,
    }
