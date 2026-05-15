from __future__ import annotations

from typing import Any

from app.core.config import settings
from app.models.schemas import LearningProgressCreate
from app.services.mega_phase_e_store import MEGA_PHASE_E_REAL_ONLY_NOTE, append_jsonl, new_id, now_iso, read_jsonl, sort_created, storage_path

LESSONS: list[dict[str, Any]] = [
    {
        "id": "reentrancy-basics",
        "title": "Reentrancy basics",
        "category": "smart-contract",
        "level": "beginner",
        "language": "hinglish",
        "summary": "External call ke baad state update karna dangerous ho sakta hai. Checks-effects-interactions pattern use karo.",
        "takeaways": ["State pehle update karo", "ReentrancyGuard consider karo", "Withdraw pattern samjho"],
    },
    {
        "id": "access-control-owner-risk",
        "title": "Access control and owner power risk",
        "category": "founder-transparency",
        "level": "beginner",
        "language": "hinglish",
        "summary": "Owner, admin, minter, pauser jaise roles launch trust ko directly affect karte hain.",
        "takeaways": ["onlyOwner functions disclose karo", "multisig/timelock use karo", "centralization risk explain karo"],
    },
    {
        "id": "wallet-approval-safety",
        "title": "Wallet approvals and spender risk",
        "category": "wallet-flow",
        "level": "beginner",
        "language": "hinglish",
        "summary": "Unlimited approval, setApprovalForAll aur unclear spender address users ke liye risky UX hai.",
        "takeaways": ["spender clearly show karo", "approval amount explain karo", "Permit/Permit2 warnings add karo"],
    },
    {
        "id": "founder-opsec-multisig",
        "title": "Founder OpSec: multisig, hardware wallet, MFA",
        "category": "admin-opsec",
        "level": "beginner",
        "language": "hinglish",
        "summary": "Single hot wallet se admin control rakhna high-risk hai. Treasury/deployer/admin separation zaroori hai.",
        "takeaways": ["seed phrase kabhi share mat karo", "hardware wallet use karo", "multisig + signer rotation plan banao"],
    },
    {
        "id": "api-bola-webhook",
        "title": "API security: BOLA/IDOR and webhook signatures",
        "category": "api-backend",
        "level": "intermediate",
        "language": "english",
        "summary": "Web3 backends often fail at object-level authorization and unsigned webhooks.",
        "takeaways": ["Per-resource auth checks", "Webhook HMAC signature", "Rate limits and audit logs"],
    },
    {
        "id": "github-ci-preaudit",
        "title": "GitHub PR pre-audit scanning",
        "category": "ci-cd",
        "level": "intermediate",
        "language": "english",
        "summary": "Run preliminary scanner on pull requests before code reaches main branch.",
        "takeaways": ["Use API keys via secrets", "Fail only on critical by default", "Do not install dependencies unless sandboxed"],
    },
]


def learning_status() -> dict[str, Any]:
    return {
        "ok": True,
        "phase": "Mega Phase E - Phase 29 Learning Center + Hinglish Knowledge Base",
        "lesson_count": len(LESSONS),
        "live": True,
        "real_only_note": MEGA_PHASE_E_REAL_ONLY_NOTE,
        "not_claimed": [
            "No fake certification is issued.",
            "Progress is created only when a user marks a lesson as completed.",
            "Video hosting, quizzes, and verified certificates require separate real integrations/content review.",
        ],
    }


def list_lessons(category: str | None = None, language: str | None = None) -> list[dict[str, Any]]:
    rows = LESSONS
    if category:
        rows = [item for item in rows if item["category"] == category]
    if language:
        rows = [item for item in rows if item["language"] == language]
    return rows


def get_lesson(lesson_id: str) -> dict[str, Any] | None:
    return next((item for item in LESSONS if item["id"] == lesson_id), None)


def progress_path():
    return storage_path(settings.learning_progress_file)


def create_progress(payload: LearningProgressCreate, user_id: str) -> dict[str, Any]:
    lesson = get_lesson(payload.lesson_id)
    if not lesson:
        raise ValueError("Lesson not found")
    row = {
        "id": new_id("learn"),
        "user_id": user_id,
        "lesson_id": payload.lesson_id,
        "status": payload.status,
        "notes": payload.notes,
        "created_at": now_iso(),
        "real_only_note": "Learning progress was manually recorded by the user. No certificate is issued.",
    }
    append_jsonl(progress_path(), row)
    return row


def list_progress(user_id: str | None = None) -> list[dict[str, Any]]:
    rows = read_jsonl(progress_path())
    if user_id:
        rows = [row for row in rows if row.get("user_id") == user_id]
    return sort_created(rows)
