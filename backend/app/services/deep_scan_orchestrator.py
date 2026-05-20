from __future__ import annotations

from typing import Any


def _present(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, set, dict)):
        return bool(value)
    return True


def _payload_value(payload: Any, name: str, default: Any = None) -> Any:
    return getattr(payload, name, default)


def _module_card_map(module_cards: list[dict[str, Any]] | None) -> dict[str, dict[str, Any]]:
    mapped: dict[str, dict[str, Any]] = {}
    for card in module_cards or []:
        module = str(card.get("module") or "").strip()
        if module:
            mapped[module] = card
    return mapped


def _card_state(cards: dict[str, dict[str, Any]], module: str, fallback: str = "Needs Evidence") -> str:
    card = cards.get(module) or {}
    status = str(card.get("status") or "").strip()
    if status:
        return status
    if card.get("assessed"):
        return "Assessed"
    return fallback


def _step(
    key: str,
    label: str,
    state: str,
    *,
    mode: str,
    auto: bool = False,
    evidence: list[str] | None = None,
    needs: list[str] | None = None,
    note: str = "",
) -> dict[str, Any]:
    return {
        "key": key,
        "label": label,
        "state": state,
        "mode": mode,
        "auto": auto,
        "evidence": evidence or [],
        "needs": needs or [],
        "note": note,
    }


def build_deep_scan_orchestrator(
    payload: Any,
    *,
    module_cards: list[dict[str, Any]] | None = None,
    surface_hints: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a user-facing truth map for what auto-runs vs what needs optional evidence.

    This does not invent scan results. It explains which existing engines ran, which are ready
    because evidence was supplied, and which are honestly skipped/Not Assessed.
    """
    cards = _module_card_map(module_cards)
    hints = surface_hints or {}
    requested_mode = str(_payload_value(payload, "scan_mode", "quick") or "quick").lower()
    if requested_mode not in {"quick", "deep", "expert"}:
        requested_mode = "quick"

    has_api = _present(_payload_value(payload, "api_base_url")) or _present(_payload_value(payload, "openapi_json"))
    has_repo = _present(_payload_value(payload, "github_repo_url"))
    has_contract = _present(_payload_value(payload, "solidity_code")) or _present(_payload_value(payload, "contract_address"))
    has_static_artifact = any(_present(_payload_value(payload, field)) for field in ("slither_json", "semgrep_json", "aderyn_json"))
    has_expert_artifact = any(
        _present(_payload_value(payload, field))
        for field in (
            "har_json",
            "crawler_artifact_json",
            "auth_test_context_json",
            "security_tool_artifacts_json",
            "foundry_test_output",
            "echidna_output_json",
            "invariant_artifact_json",
            "accuracy_feedback_json",
        )
    )
    has_wallet = any(_present(_payload_value(payload, field)) for field in ("wallet_evidence_json", "transaction_samples_json", "signature_samples_json"))
    has_business = _present(_payload_value(payload, "business_context_json"))
    has_defi = _present(_payload_value(payload, "defi_simulation_json")) or _present(_payload_value(payload, "protocol_context_json"))
    has_review = _present(_payload_value(payload, "review_context_json"))

    quick_steps = [
        _step(
            "website_surface",
            "Website headers/CSP/cookies/forms",
            _card_state(cards, "website", "Auto-run"),
            mode="quick",
            auto=True,
            evidence=["Website / dApp URL"],
            note="Runs from the URL only using safe passive evidence.",
        ),
        _step(
            "public_exposure",
            "Public exposure paths and source-map hints",
            "Auto-run",
            mode="quick",
            auto=True,
            evidence=["Same-origin public paths", "Homepage/asset evidence"],
            note="Checks only safe public URLs and never authenticates or exploits.",
        ),
        _step(
            "js_api_discovery",
            "JS/API endpoint discovery",
            _card_state(cards, "deep_detection", "Auto-run"),
            mode="quick",
            auto=True,
            evidence=["Homepage HTML", "public JS hints", "safe crawler output"],
            note="Extracts visible endpoints/routes when present; no hidden private code is guessed.",
        ),
        _step(
            "score_gate",
            "Dynamic score proof and coverage gate",
            "Auto-run",
            mode="quick",
            auto=True,
            evidence=["Observed findings", "Not Assessed module count"],
            note="Overall confidence stays gated when deep modules lack evidence.",
        ),
    ]

    deep_steps = [
        _step(
            "github_repo",
            "GitHub deep repo and OSV/dependency evidence",
            _card_state(cards, "github", "Ready if repo URL provided") if has_repo else "Needs GitHub repo URL",
            mode="deep",
            evidence=["GitHub repo URL"] if has_repo else [],
            needs=[] if has_repo else ["GitHub repo URL"],
            note="Repo/dependency findings require a public repo/lockfile/provider response.",
        ),
        _step(
            "api_evidence",
            "API/OpenAPI/admin passive evidence",
            _card_state(cards, "api", "Ready if API evidence provided") if has_api else "Needs API base URL or OpenAPI",
            mode="deep",
            evidence=["API base/OpenAPI evidence"] if has_api else [],
            needs=[] if has_api else ["API base URL", "OpenAPI JSON or safe observations"],
            note="Authenticated/BOLA checks require explicit safe test context.",
        ),
        _step(
            "contract_static",
            "Contract/source/static-analysis execution",
            _card_state(cards, "contract", "Ready if contract evidence provided") if has_contract else "Needs contract/source evidence",
            mode="deep",
            evidence=["Solidity source or contract address"] if has_contract else [],
            needs=[] if has_contract else ["Solidity source", "contract address", "verified explorer source"],
            note="Backend tool execution depends on installed/enabled Slither/Semgrep; otherwise use artifacts.",
        ),
        _step(
            "wallet_business_context",
            "Wallet/business/deFi context readiness",
            "Evidence supplied" if (has_wallet or has_business or has_defi) else "Needs optional workflow evidence",
            mode="deep",
            evidence=[name for name, present in (("wallet", has_wallet), ("business", has_business), ("defi", has_defi)) if present],
            needs=[] if (has_wallet or has_business or has_defi) else ["wallet tx/signature samples", "business context", "DeFi simulation artifact"],
            note="These categories are not guessed from a URL-only scan.",
        ),
    ]

    expert_steps = [
        _step(
            "static_artifacts",
            "Slither/Semgrep/Aderyn JSON artifact bridge",
            _card_state(cards, "static_analysis", "Artifact supplied") if has_static_artifact else "Needs tool artifact or backend runner",
            mode="expert",
            evidence=["Static-analysis JSON artifact"] if has_static_artifact else [],
            needs=[] if has_static_artifact else ["Slither JSON", "Semgrep JSON", "Aderyn JSON", "or backend tool runner"],
            note="Tool artifacts are parsed as user-supplied evidence, not fake backend execution.",
        ),
        _step(
            "har_auth_artifacts",
            "HAR/auth/API evidence artifacts",
            "Evidence supplied" if has_expert_artifact else "Needs expert artifact",
            mode="expert",
            evidence=["HAR/crawler/auth/tool artifacts"] if has_expert_artifact else [],
            needs=[] if has_expert_artifact else ["HAR JSON", "crawler artifact", "authorized API context", "SCA/secrets artifact"],
            note="Used to deepen detection without unsafe unauthorized testing.",
        ),
        _step(
            "review_confirmation",
            "Manual review confirmation and triage state",
            "Reviewer context supplied" if has_review else "Manual review not supplied",
            mode="expert",
            evidence=["Reviewed confirmation JSON"] if has_review else [],
            needs=[] if has_review else ["reviewer/triage confirmation if a reviewed report is requested"],
            note="Reviewed status is never invented without a reviewer/admin decision.",
        ),
    ]

    all_steps = quick_steps + deep_steps + expert_steps
    auto_run = [step for step in quick_steps if step["auto"]]
    evidence_ready = [step for step in all_steps if step.get("evidence") and not step["auto"]]
    needs_evidence = [step for step in all_steps if step.get("needs")]

    recommended_mode = "quick"
    if has_static_artifact or has_expert_artifact or has_review:
        recommended_mode = "expert"
    elif has_api or has_repo or has_contract or has_wallet or has_business or has_defi:
        recommended_mode = "deep"

    return {
        "phase": "78",
        "name": "Unified Deep Scan Orchestrator",
        "requested_mode": requested_mode,
        "recommended_mode": recommended_mode,
        "summary": {
            "auto_run_count": len(auto_run),
            "evidence_ready_count": len(evidence_ready),
            "needs_evidence_count": len(needs_evidence),
            "user_message": "Quick Scan needs only URL + permission. Deep and Expert evidence are optional and only improve coverage when supplied.",
            "truth_rule": "Auto-run public evidence is scanned; missing optional evidence is marked Not Assessed, not guessed.",
        },
        "quick_scan_auto_runs": auto_run,
        "deep_scan_steps": deep_steps,
        "expert_evidence_steps": expert_steps,
        "all_steps": all_steps,
        "ui_guidance": [
            "Default to Quick Scan for normal users.",
            "Show GitHub/API/contract fields only in Deep Scan.",
            "Show JSON artifacts only in Expert Evidence mode.",
            "Display skipped modules as Needs Evidence or Not Assessed.",
        ],
        "safe_boundaries": [
            "No brute force, credential stuffing, DoS, exploit chaining, wallet signing, or private key/seed collection.",
            "Authenticated API checks require explicit owner-supplied test context.",
            "Manual review/triage status requires a real reviewer/admin action.",
            "No certified audit or all-vulnerabilities-found claim.",
        ],
        "surface_hint_keys_seen": sorted(str(key) for key in hints.keys())[:30],
    }
