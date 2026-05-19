from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from app.core.config import settings
from app.services.ai_explainer import ai_status
from app.services.eon import build_fix_plan, build_risk_graph, evidence_ledger
from app.services.india_launch import build_india_launch_pack
from app.services.trust_readiness import build_trust_readiness

SECURITY_COPILOT_REAL_ONLY_NOTE = (
    "Web3Guard Security Copilot is a defensive coach/workspace. It can summarize stored evidence, explain next steps, "
    "draft safe report wording, and generate local verification commands. It is not an AI auditor, does not auto-apply fixes, "
    "does not execute exploits, and does not claim certified audit or 100% security."
)

SECURITY_COPILOT_SAFE_BOUNDARY = (
    "Use Copilot guidance only for projects you own or are authorized to review. Do not paste private keys, seed phrases, "
    "mnemonics, production secrets, or sensitive customer data. Generated commands are local defensive checks and require developer review."
)

SAFE_COMMANDS = [
    {
        "id": "frontend_build",
        "title": "Frontend production build",
        "command": "cd frontend && npm run typecheck && npm run build",
        "purpose": "Catch TypeScript/build regressions before deploy.",
        "risk_level": "safe_local",
    },
    {
        "id": "backend_tests",
        "title": "Backend regression tests",
        "command": "cd backend && python -m pytest -q",
        "purpose": "Verify backend scanner/report/payment/workflow behavior stays stable.",
        "risk_level": "safe_local",
    },
    {
        "id": "foundry_tests",
        "title": "Foundry local tests",
        "command": "forge test -vvv",
        "purpose": "Run local defensive Solidity tests inside your own repository.",
        "risk_level": "safe_local_authorized_only",
    },
    {
        "id": "slither_local",
        "title": "Slither local static analysis",
        "command": "slither . --exclude-dependencies",
        "purpose": "Run Slither locally when installed. Keep status Tool Not Installed if missing.",
        "risk_level": "safe_local_authorized_only",
    },
    {
        "id": "aderyn_local",
        "title": "Aderyn local static analysis",
        "command": "aderyn .",
        "purpose": "Run Aderyn locally when installed. No output should be invented by Web3Guard.",
        "risk_level": "safe_local_authorized_only",
    },
]

REPORT_WORDING_TEMPLATES = {
    "founder_summary": (
        "Web3Guard AI reviewed the supplied launch-readiness evidence for this project. The output is a pre-audit readiness review, "
        "not a certified audit. Assessed modules, missing evidence, open findings, and Not Assessed items are listed separately so readers can understand the scope."
    ),
    "investor_summary": (
        "This project has generated a Web3Guard launch-readiness package that summarizes supplied evidence, report hashes, fix status, "
        "monitoring setup, and remaining manual review items. The package should support due diligence but does not replace independent audit or legal review."
    ),
    "public_trust_summary": (
        "Pre-audit readiness reviewed by Web3Guard AI. This page shows evidence-backed checks and unresolved items; it does not certify the project as secure."
    ),
    "limitation": (
        "Automated checks can miss vulnerabilities. Any missing provider, tool, source code, wallet flow, API evidence, or admin OpSec proof is marked Not Assessed instead of being guessed."
    ),
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_dump(value: Any) -> str:
    try:
        return json.dumps(value, default=str, sort_keys=True, ensure_ascii=False)
    except Exception:
        return str(value)


def _hash(value: Any) -> str:
    return hashlib.sha256(_safe_dump(value).encode("utf-8")).hexdigest()


def _severity_rank(severity: str) -> int:
    return {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}.get((severity or "info").lower(), 4)


def _provider_mode() -> dict[str, Any]:
    status = ai_status()
    provider_configured = bool(status.get("provider_configured"))
    return {
        "ai_enabled": status.get("ai_enabled", False),
        "provider": status.get("provider", "none"),
        "provider_configured": provider_configured,
        "mode": "provider_ready" if provider_configured else "local_fallback",
        "status_label": "Provider Configured" if provider_configured else "Provider Not Configured / Needs API Key",
        "note": "AI provider can be used only if explicitly configured. Local fallback remains available." if provider_configured else "Local deterministic guidance is active. No fake AI output is generated.",
    }


def copilot_status() -> dict[str, Any]:
    return {
        "ok": True,
        "service": "Security Copilot Workspace",
        "mode": _provider_mode(),
        "capabilities": [
            "next_step_assistant",
            "fix_task_explanation",
            "safe_command_pack",
            "report_wording_assistant",
            "evidence_summary",
            "local_checklist_fallback",
        ],
        "blocked": [
            "ai_auditor_claim",
            "certified_audit_claim",
            "exploit_automation",
            "wallet_signing",
            "private_key_or_seed_phrase_collection",
            "fake_ai_output",
        ],
        "real_only_note": SECURITY_COPILOT_REAL_ONLY_NOTE,
        "safe_boundary": SECURITY_COPILOT_SAFE_BOUNDARY,
    }


def _make_next_steps(fix_plan: dict[str, Any], readiness: dict[str, Any]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for item in fix_plan.get("tasks", [])[:8]:
        severity = str(item.get("severity", "info")).lower()
        items.append(
            {
                "id": item.get("id") or f"next_{_hash(item)[:10]}",
                "title": item.get("title") or item.get("action") or "Review launch-readiness item",
                "priority": item.get("priority") or ("P0 launch blocker" if severity == "critical" else "P1/P2 readiness work"),
                "severity": severity,
                "why_it_matters": item.get("why_it_matters") or item.get("reason") or "This item affects launch trust or evidence completeness.",
                "safe_next_step": item.get("safe_next_step") or item.get("action") or "Review the evidence, apply a defensive fix, then re-run the relevant scanner.",
                "verify_command": item.get("verify") or "Re-run the relevant Web3Guard scanner and attach evidence.",
                "source": "eon_fix_plan",
            }
        )

    for component in readiness.get("component_scores", [])[:6]:
        score = component.get("score", 0)
        if isinstance(score, (int, float)) and score < 60:
            items.append(
                {
                    "id": f"readiness_{component.get('id', _hash(component)[:8])}",
                    "title": f"Improve {component.get('label', 'readiness component')}",
                    "priority": "P2 evidence needed",
                    "severity": "medium",
                    "why_it_matters": component.get("description") or "This readiness area is below a comfortable launch threshold.",
                    "safe_next_step": component.get("next_action") or "Add evidence, close open findings, and re-run the readiness score.",
                    "verify_command": "Open /trust-readiness and confirm the component score improved from real stored evidence.",
                    "source": "trust_readiness",
                }
            )

    dedup: dict[str, dict[str, Any]] = {}
    for item in items:
        key = str(item.get("title", "")).lower()
        if key and key not in dedup:
            dedup[key] = item
    ordered = sorted(dedup.values(), key=lambda item: _severity_rank(str(item.get("severity", "info"))))
    return ordered[:12]


def _make_report_assistant(readiness: dict[str, Any], graph: dict[str, Any]) -> dict[str, Any]:
    score = readiness.get("score") or readiness.get("overall_score") or readiness.get("launch_trust_readiness") or "Not scored"
    label = readiness.get("label") or readiness.get("risk_label") or "Readiness review"
    blockers = graph.get("blockers", []) if isinstance(graph, dict) else []
    blocker_text = f"{len(blockers)} launch blocker(s) remain open" if blockers else "No launch blockers were generated from the current stored evidence"
    return {
        "templates": REPORT_WORDING_TEMPLATES,
        "suggested_summary": (
            f"Launch Trust Readiness: {score} ({label}). {blocker_text}. "
            "This summary is generated from stored Web3Guard evidence and should be reviewed before sharing publicly."
        ),
        "safe_public_phrase": "Pre-audit readiness reviewed by Web3Guard AI. Not a certified audit.",
        "blocked_phrases": ["audited by Web3Guard", "certified secure", "100% secure", "exploit-free", "guaranteed safe"],
        "review_note": "Report wording requires human review before publishing or sending to users, investors, or auditors.",
    }


def build_workspace(user_id: str, project_id: str | None = None, language: str = "English") -> dict[str, Any]:
    graph = build_risk_graph(user_id=user_id, project_id=project_id)
    fix_plan = build_fix_plan(user_id=user_id, project_id=project_id)
    ledger = evidence_ledger(user_id=user_id, project_id=project_id)
    readiness = build_trust_readiness(user_id=user_id, project_id=project_id)
    india_pack = build_india_launch_pack(user_id=user_id, project_id=project_id, mode="hinglish" if language.lower() in {"hindi", "hinglish"} else "english")

    next_steps = _make_next_steps(fix_plan, readiness)
    return {
        "ok": True,
        "user_id": user_id,
        "project_id": project_id,
        "language": language,
        "generated_at": _now(),
        "mode": _provider_mode(),
        "workspace_id": f"copilot_{_hash({'user_id': user_id, 'project_id': project_id})[:16]}",
        "summary": {
            "risk_nodes": len(graph.get("nodes", [])),
            "launch_blockers": len(graph.get("blockers", [])),
            "next_steps": len(next_steps),
            "evidence_entries": len(ledger.get("entries", [])),
            "readiness_score": readiness.get("score") or readiness.get("overall_score") or readiness.get("launch_trust_readiness"),
        },
        "next_steps": next_steps,
        "safe_commands": SAFE_COMMANDS,
        "report_assistant": _make_report_assistant(readiness, graph),
        "evidence_digest": ledger.get("entries", [])[:12],
        "india_pack_summary": {
            "mode": india_pack.get("mode"),
            "sections": list((india_pack.get("pack") or {}).keys())[:10] if isinstance(india_pack.get("pack"), dict) else [],
            "note": "India launch guidance is founder support only, not legal or regulatory approval.",
        },
        "real_only_note": SECURITY_COPILOT_REAL_ONLY_NOTE,
        "safe_boundary": SECURITY_COPILOT_SAFE_BOUNDARY,
    }


def answer_prompt(payload: dict[str, Any]) -> dict[str, Any]:
    user_id = str(payload.get("user_id") or "local-demo-user")
    project_id = payload.get("project_id") or None
    question = str(payload.get("question") or "").strip()
    language = str(payload.get("language") or "English")
    include_commands = bool(payload.get("include_commands", True))

    workspace = build_workspace(user_id=user_id, project_id=project_id, language=language)
    top_steps = workspace.get("next_steps", [])[:5]
    if not question:
        question = "What should I fix next before launch?"

    intro = "AI provider is not configured, so this is deterministic local guidance." if not workspace["mode"].get("provider_configured") else "Provider is configured, but this endpoint still returns safe workspace guidance only."
    answer_lines = [intro, f"Question: {question}", "Recommended next steps:"]
    if top_steps:
        for index, step in enumerate(top_steps, start=1):
            answer_lines.append(f"{index}. {step.get('title')} — {step.get('safe_next_step')}")
    else:
        answer_lines.append("1. Save a project, run a scanner, generate a report, then reopen Copilot for evidence-backed guidance.")

    if include_commands:
        answer_lines.append("Safe local verification commands are included separately. Run them only inside your own authorized project.")

    return {
        "ok": True,
        "mode": workspace["mode"],
        "question": question,
        "answer": "\n".join(answer_lines),
        "recommended_steps": top_steps,
        "safe_commands": SAFE_COMMANDS if include_commands else [],
        "blocked": ["exploit automation", "wallet signing", "private key/seed phrase handling", "certified audit claim"],
        "review_note": "Copilot output is guidance only and requires developer/manual review.",
    }
