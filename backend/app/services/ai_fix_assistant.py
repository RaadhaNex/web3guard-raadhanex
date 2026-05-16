from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Any

import httpx

from app.core.config import settings
from app.models.schemas import AIFixAssistantRequest, AIFixSuggestion, Finding

PRIVATE_KEY_RE = re.compile(r"(?i)(private[_-]?key|mnemonic|seed[_-]?phrase|secret)\s*[:=]\s*['\"]?([A-Za-z0-9_\-+/=\s]{16,})")
HEX_PRIVATE_KEY_RE = re.compile(r"0x[a-fA-F0-9]{64}")
LONG_TOKEN_RE = re.compile(r"(?i)(api[_-]?key|token|secret)\s*[:=]\s*['\"]?([A-Za-z0-9_\-.]{24,})")

FIX_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "summary",
        "root_cause",
        "safe_patch_strategy",
        "suggested_patch_unified_diff",
        "fixed_code_snippet",
        "test_suggestions",
        "validation_steps",
        "risk_notes",
        "manual_review_note",
        "confidence_note",
    ],
    "properties": {
        "summary": {"type": "string"},
        "root_cause": {"type": "string"},
        "safe_patch_strategy": {"type": "string"},
        "suggested_patch_unified_diff": {"type": "string"},
        "fixed_code_snippet": {"type": "string"},
        "test_suggestions": {"type": "array", "items": {"type": "string"}},
        "validation_steps": {"type": "array", "items": {"type": "string"}},
        "risk_notes": {"type": "array", "items": {"type": "string"}},
        "manual_review_note": {"type": "string"},
        "confidence_note": {"type": "string"},
    },
}


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def active_provider() -> tuple[str, str | None, str]:
    provider = (settings.ai_provider or "none").lower().strip()
    if provider == "openai":
        return "openai", settings.openai_api_key or settings.ai_api_key, settings.ai_model
    if provider == "anthropic":
        return "anthropic", settings.anthropic_api_key or settings.ai_api_key, settings.anthropic_model
    return provider, None, "none"


def fix_assistant_status() -> dict[str, Any]:
    provider, key, model = active_provider()
    provider_configured = bool(settings.ai_enabled and settings.ai_fix_enabled and key and provider in {"openai", "anthropic"})
    return {
        "ok": True,
        "phase": "Phase 15 - Real AI Fix Assistant",
        "version": "1.0",
        "ai_enabled": settings.ai_enabled,
        "ai_fix_enabled": settings.ai_fix_enabled,
        "provider": provider,
        "model": model,
        "provider_configured": provider_configured,
        "mode": "provider" if provider_configured else "safe_fallback",
        "ai_send_code": settings.ai_send_code,
        "ai_fix_send_code": settings.ai_fix_send_code,
        "max_code_chars": settings.ai_fix_max_code_chars,
        "auto_apply_allowed": False,
        "code_will_be_sent_only_if": [
            "AI_ENABLED=true",
            "AI_FIX_ENABLED=true",
            "AI_SEND_CODE=true",
            "AI_FIX_SEND_CODE=true",
            "request.include_code=true",
            "request.privacy_acknowledged=true",
        ],
        "blocked_claims": [
            "No guaranteed fix",
            "No automatic production code modification",
            "No exploit generation",
            "No private key or seed phrase collection",
            "No certified audit claim",
        ],
        "real_only_note": "If provider or code-send settings are disabled, Web3Guard AI returns local safe fix guidance and does not fake AI output.",
    }


def redact_sensitive_code(code: str) -> tuple[str, bool, list[str]]:
    flags: list[str] = []
    redacted = code
    if PRIVATE_KEY_RE.search(redacted):
        flags.append("secret_assignment_redacted")
        redacted = PRIVATE_KEY_RE.sub(lambda m: f"{m.group(1)} = <REDACTED_SECRET>", redacted)
    if HEX_PRIVATE_KEY_RE.search(redacted):
        flags.append("hex_private_key_like_value_redacted")
        redacted = HEX_PRIVATE_KEY_RE.sub("0x<REDACTED_64_HEX>", redacted)
    if LONG_TOKEN_RE.search(redacted):
        flags.append("long_token_like_value_redacted")
        redacted = LONG_TOKEN_RE.sub(lambda m: f"{m.group(1)} = <REDACTED_TOKEN>", redacted)
    return redacted, redacted != code, flags


def _should_send_code(payload: AIFixAssistantRequest) -> bool:
    return bool(
        settings.ai_enabled
        and settings.ai_fix_enabled
        and settings.ai_send_code
        and settings.ai_fix_send_code
        and payload.include_code
        and payload.privacy_acknowledged
        and payload.code_context
    )


def _fallback_fix(payload: AIFixAssistantRequest, status: str = "fallback", provider: str = "fallback-local") -> AIFixSuggestion:
    finding = payload.finding
    title_lower = finding.title.lower()
    recommendation = finding.recommendation or "Patch the root cause conservatively, then add regression tests."

    strategy = recommendation
    snippet = "// No automatic patch generated in fallback mode.\n// Apply the recommendation manually and rerun the scanner."
    diff = ""
    tests = [
        "Add a regression test that fails on the vulnerable behavior and passes after the fix.",
        "Rerun Web3Guard AI rule/static scans after patching.",
        "Use a manual pre-audit review for critical/high findings or fund-holding contracts.",
    ]
    validation = [
        "Confirm the finding still maps to the affected function/line.",
        "Patch in a separate branch and review the diff before merge.",
        "Run unit tests and relevant security tools again before deployment.",
    ]

    if "reentr" in title_lower or "external call" in title_lower:
        strategy = "Use checks-effects-interactions, add a reentrancy guard for state-changing value transfers, and update state before external calls."
        snippet = "// Pattern only — adapt to your contract:\n// require(balance[msg.sender] >= amount, 'insufficient');\n// balance[msg.sender] -= amount;\n// (bool ok, ) = msg.sender.call{value: amount}('');\n// require(ok, 'transfer failed');"
        tests.insert(0, "Test a malicious receiver contract cannot reenter withdraw/claim functions.")
    elif "tx.origin" in title_lower:
        strategy = "Replace tx.origin authorization with msg.sender-based access control such as Ownable/AccessControl."
        snippet = "// Replace:\n// require(tx.origin == owner, 'not owner');\n// With:\n// require(msg.sender == owner, 'not owner');"
        tests.insert(0, "Test calls through another contract do not bypass or break authorization unexpectedly.")
    elif "access control" in title_lower or "missing access" in title_lower or "owner" in title_lower:
        strategy = "Restrict sensitive functions with explicit role checks and emit events for privileged actions."
        snippet = "// Pattern only:\n// modifier onlyOwner() { require(msg.sender == owner, 'not owner'); _; }\n// function mint(...) external onlyOwner { ... }"
        tests.insert(0, "Test non-owner/non-role accounts cannot call the sensitive function.")
    elif "random" in title_lower:
        strategy = "Do not use block.timestamp/blockhash as secure randomness. Use a commit-reveal design or a verified randomness provider where appropriate."
        snippet = "// Avoid: uint256(blockhash(block.number - 1)) or block.timestamp for winner selection.\n// Use commit-reveal or a VRF-style integration after threat modeling."
    elif "delegatecall" in title_lower or "upgrade" in title_lower or "proxy" in title_lower:
        strategy = "Review proxy admin controls, initializer protection, storage layout, and upgrade authorization before deployment."
        snippet = "// Ensure initializer can run only once and upgrade functions are restricted to a multisig/timelock role."
        tests.insert(0, "Test initializer cannot be called twice and unauthorized accounts cannot upgrade implementation.")

    if payload.preferred_language == "Hinglish":
        summary = f"{finding.title}: is issue ko launch se pehle verify/fix karna important hai. Yeh auto-fix nahi hai; safe patch direction hai."
        manual = "Critical/high issue ya user funds involved hon to manual pre-audit review zaroor karao."
    elif payload.preferred_language == "Hindi":
        summary = f"{finding.title}: यह production से पहले verify और fix करने वाला preliminary issue है। यह automatic fix नहीं है।"
        manual = "Critical/High issue या user funds होने पर manual pre-audit review जरूरी है।"
    else:
        summary = f"{finding.title}: preliminary safe fix guidance. This is not an automatic or guaranteed fix."
        manual = "Manual review is strongly recommended for critical/high findings or contracts that hold user funds."

    return AIFixSuggestion(
        status=status,
        provider=provider,
        model="local-fallback",
        generated_at=_utc_now(),
        language=payload.preferred_language,
        finding_id=finding.id,
        finding_title=finding.title,
        finding_severity=finding.severity,
        summary=summary,
        root_cause=finding.developer_explanation,
        safe_patch_strategy=strategy,
        suggested_patch_unified_diff=diff,
        fixed_code_snippet=snippet,
        test_suggestions=tests,
        validation_steps=validation,
        risk_notes=[
            "This is a preliminary suggestion, not a certified audit fix.",
            "Do not deploy without tests and manual review for sensitive contracts.",
        ],
        manual_review_note=manual,
        confidence_note=f"Finding confidence is {finding.confidence}; verify root cause manually before patching.",
        auto_apply_allowed=False,
        code_was_sent_to_provider=False,
        redaction_applied=False,
        safety_flags=["fallback_mode", "no_auto_apply", "manual_review_recommended"],
    )


def _build_fix_prompt(payload: AIFixAssistantRequest, code_to_send: str | None) -> str:
    finding = payload.finding
    code_block = ""
    if code_to_send:
        code_block = f"\nCode context excerpt, redacted if needed:\n```solidity\n{code_to_send[: settings.ai_fix_max_code_chars]}\n```"
    return f"""
You are Web3Guard AI by RAADHANEX. Produce a safe fix suggestion for a preliminary Web3 security finding.

Strict rules:
- Do not provide exploit steps, attack scripts, or bypass instructions.
- Do not claim the fix is guaranteed.
- Do not modify production code automatically.
- Suggest conservative patch direction, a minimal code pattern or unified diff when safe, and tests.
- Recommend manual review for critical/high findings and fund-holding contracts.
- Never ask for private keys, seed phrases, mnemonics, or wallet signing.
- Output JSON only matching the requested schema.

Language: {payload.preferred_language}
Mode: {payload.mode}
Finding:
- id: {finding.id}
- module: {finding.module}
- severity: {finding.severity}
- title: {finding.title}
- description: {finding.description}
- affected line: {finding.affected_line}
- affected function: {finding.affected_function}
- source: {finding.source}
- confidence: {finding.confidence}
- business impact: {finding.business_impact}
- developer explanation: {finding.developer_explanation}
- current recommendation: {finding.recommendation}
{code_block}
""".strip()


async def suggest_ai_fix(payload: AIFixAssistantRequest) -> AIFixSuggestion:
    provider, key, model = active_provider()
    should_send_code = _should_send_code(payload)
    redacted_code: str | None = None
    redaction_applied = False
    safety_flags = ["no_auto_apply", "manual_review_recommended"]

    if should_send_code and payload.code_context:
        redacted_code, redaction_applied, redact_flags = redact_sensitive_code(payload.code_context)
        safety_flags.extend(redact_flags)
    elif payload.include_code and payload.code_context and not payload.privacy_acknowledged:
        safety_flags.append("code_not_sent_privacy_not_acknowledged")
    elif payload.include_code and payload.code_context and not (settings.ai_send_code and settings.ai_fix_send_code):
        safety_flags.append("code_not_sent_env_privacy_gate_disabled")

    configured = bool(settings.ai_enabled and settings.ai_fix_enabled and key and provider in {"openai", "anthropic"})
    if not configured:
        fallback = _fallback_fix(payload)
        fallback.safety_flags.extend(flag for flag in safety_flags if flag not in fallback.safety_flags)
        fallback.redaction_applied = redaction_applied
        return fallback

    prompt = _build_fix_prompt(payload, redacted_code if should_send_code else None)
    try:
        if provider == "openai":
            data = await _call_openai_fix(prompt, key or "", model)
        elif provider == "anthropic":
            data = await _call_anthropic_fix(prompt, key or "", model)
        else:
            return _fallback_fix(payload)
        suggestion = _provider_suggestion(payload, data, provider, model, should_send_code, redaction_applied, safety_flags)
        return suggestion
    except Exception:
        fallback = _fallback_fix(payload, status="provider_error", provider=provider)
        fallback.safety_flags.extend(flag for flag in safety_flags if flag not in fallback.safety_flags)
        fallback.redaction_applied = redaction_applied
        return fallback


async def _call_openai_fix(prompt: str, key: str, model: str) -> dict[str, Any]:
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "Return safe Web3 security fix guidance as strict JSON only."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.1,
        "response_format": {
            "type": "json_schema",
            "json_schema": {"name": "web3guard_fix_suggestion", "strict": True, "schema": FIX_SCHEMA},
        },
    }
    async with httpx.AsyncClient(timeout=settings.ai_timeout_seconds) as client:
        response = await client.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        return json.loads(content)


async def _call_anthropic_fix(prompt: str, key: str, model: str) -> dict[str, Any]:
    headers = {"x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"}
    schema_instructions = f"Return JSON only matching this JSON Schema: {json.dumps(FIX_SCHEMA)}"
    payload = {
        "model": model,
        "max_tokens": 1400,
        "temperature": 0.1,
        "messages": [{"role": "user", "content": f"{schema_instructions}\n\n{prompt}"}],
    }
    async with httpx.AsyncClient(timeout=settings.ai_timeout_seconds) as client:
        response = await client.post("https://api.anthropic.com/v1/messages", headers=headers, json=payload)
        response.raise_for_status()
        blocks = response.json().get("content", [])
        text = "".join(block.get("text", "") for block in blocks if block.get("type") == "text")
        return json.loads(_extract_json(text))


def _extract_json(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("{") and stripped.endswith("}"):
        return stripped
    match = re.search(r"\{.*\}", stripped, flags=re.DOTALL)
    if not match:
        raise ValueError("No JSON object returned by provider")
    return match.group(0)


def _provider_suggestion(
    payload: AIFixAssistantRequest,
    data: dict[str, Any],
    provider: str,
    model: str,
    code_was_sent: bool,
    redaction_applied: bool,
    safety_flags: list[str],
) -> AIFixSuggestion:
    fallback = _fallback_fix(payload, provider=provider)
    finding = payload.finding
    return AIFixSuggestion(
        status="provider_success",
        provider=provider,
        model=model,
        generated_at=_utc_now(),
        language=payload.preferred_language,
        finding_id=finding.id,
        finding_title=finding.title,
        finding_severity=finding.severity,
        summary=str(data.get("summary") or fallback.summary),
        root_cause=str(data.get("root_cause") or fallback.root_cause),
        safe_patch_strategy=str(data.get("safe_patch_strategy") or fallback.safe_patch_strategy),
        suggested_patch_unified_diff=str(data.get("suggested_patch_unified_diff") or ""),
        fixed_code_snippet=str(data.get("fixed_code_snippet") or fallback.fixed_code_snippet),
        test_suggestions=[str(item) for item in (data.get("test_suggestions") or fallback.test_suggestions)][:8],
        validation_steps=[str(item) for item in (data.get("validation_steps") or fallback.validation_steps)][:8],
        risk_notes=[str(item) for item in (data.get("risk_notes") or fallback.risk_notes)][:8],
        manual_review_note=str(data.get("manual_review_note") or fallback.manual_review_note),
        confidence_note=str(data.get("confidence_note") or fallback.confidence_note),
        auto_apply_allowed=False,
        code_was_sent_to_provider=code_was_sent,
        redaction_applied=redaction_applied,
        safety_flags=list(dict.fromkeys(safety_flags + ["provider_output", "no_auto_apply"])),
    )
