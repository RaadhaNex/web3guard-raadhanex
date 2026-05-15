import json
from typing import Any

import httpx

from app.core.config import settings
from app.models.schemas import AIExplanation, ExplanationMode, Finding

CRITICAL_TERMS = {"exploit", "attack", "drain", "steal", "bypass", "payload", "hack"}


def ai_status() -> dict[str, Any]:
    provider = (settings.ai_provider or "none").lower()
    provider_key = settings.ai_api_key
    if provider == "openai":
        provider_key = settings.openai_api_key or settings.ai_api_key
    elif provider == "anthropic":
        provider_key = settings.anthropic_api_key or settings.ai_api_key
    configured = bool(settings.ai_enabled and provider_key and provider in {"openai", "anthropic"})
    return {
        "ai_enabled": settings.ai_enabled,
        "provider": provider,
        "provider_configured": configured,
        "ai_send_code": settings.ai_send_code,
        "mode": "provider" if configured else "safe_fallback",
        "disclaimer": "AI explanations are guidance only and do not replace a manual audit.",
    }


def fallback_finding_explanation(
    finding: Finding,
    mode: ExplanationMode | str = "founder",
    language: str = "English",
    status: str = "fallback",
) -> AIExplanation:
    severity_intro = {
        "critical": "This should be treated as an urgent launch blocker until manually reviewed.",
        "high": "This can materially increase launch risk and should be fixed before public launch.",
        "medium": "This is a meaningful risk that should be resolved before launch if possible.",
        "low": "This is a lower-risk hardening item, but it still improves trust and launch quality.",
        "info": "This is an informational improvement that can help documentation, trust, or maintainability.",
    }.get(finding.severity, "This finding should be reviewed before launch.")

    if language == "Hinglish":
        summary = f"{finding.title}: ye preliminary finding hai. {severity_intro}"
        business = f"Founder impact: {finding.business_impact} Agar ye project public launch se pehle fix nahi hua, trust aur user funds dono par impact aa sakta hai."
        dev = f"Developer view: {finding.developer_explanation} Pehle root cause verify karo, fir tests ke saath fix apply karo."
        fix = f"Safe fix direction: {finding.recommendation} Production se pehle manual review zaroor karna."
        manual = "Critical/high issues ke liye paid/manual pre-audit review strongly recommended hai."
    elif language == "Hindi":
        summary = f"{finding.title}: यह एक प्रारंभिक सुरक्षा संकेत है। {severity_intro}"
        business = f"व्यावसायिक प्रभाव: {finding.business_impact} लॉन्च से पहले इसे जाँचना भरोसे और सुरक्षा के लिए महत्वपूर्ण है।"
        dev = f"डेवलपर गाइडेंस: {finding.developer_explanation} पहले कारण सत्यापित करें, फिर टेस्ट के साथ सुधार लागू करें।"
        fix = f"सुरक्षित सुधार दिशा: {finding.recommendation} उत्पादन में लगाने से पहले मैनुअल समीक्षा करें।"
        manual = "Critical/High findings के लिए manual pre-audit review strongly recommended है।"
    else:
        summary = f"{finding.title}: {severity_intro}"
        business = f"Business impact: {finding.business_impact} This can affect launch trust, user safety, and investor confidence."
        dev = f"Developer guidance: {finding.developer_explanation} Verify the root cause, patch conservatively, and add regression tests."
        fix = f"Safe fix direction: {finding.recommendation} Review the patch before production use."
        manual = "Manual review is strongly recommended for critical/high findings or contracts holding user funds."

    return AIExplanation(
        status=status,  # type: ignore[arg-type]
        provider="fallback-local" if status == "fallback" else settings.ai_provider,
        mode=mode,
        language=language,
        summary=summary,
        business_impact=business,
        developer_guidance=dev,
        safe_fix_direction=fix,
        manual_review_note=manual,
        confidence_note=f"Confidence is {finding.confidence}. Treat this as a preliminary signal, not proof of exploitability.",
    )


def build_safe_prompt(finding: Finding, mode: str, language: str, include_code: bool) -> str:
    code_text = ""
    if include_code and settings.ai_send_code and finding.affected_code:
        code_text = f"\nAffected code excerpt for context only:\n```solidity\n{finding.affected_code[:1500]}\n```"

    return f"""
You are Web3Guard AI by RAADHANEX. Explain a preliminary Web3 security finding safely.

Rules:
- Do not provide exploit steps or attack instructions.
- Do not claim the issue is definitely exploitable.
- Do not claim the fix is guaranteed.
- Provide conservative mitigation direction.
- Recommend manual review for critical/high issues.
- Output JSON only with keys: summary, business_impact, developer_guidance, safe_fix_direction, manual_review_note, confidence_note.

Language: {language}
Mode: {mode}
Finding:
- Severity: {finding.severity}
- Title: {finding.title}
- Description: {finding.description}
- Confidence: {finding.confidence}
- Business impact: {finding.business_impact}
- Developer explanation: {finding.developer_explanation}
- Recommendation: {finding.recommendation}
{code_text}
""".strip()


def is_safe_ai_request(finding: Finding) -> bool:
    joined = " ".join([finding.title, finding.description, finding.recommendation]).lower()
    # We still allow security explanations, but block prompts that look like explicit exploit generation requests.
    blocked_phrases = ["write exploit", "generate exploit", "attack script", "drain funds", "bypass authentication"]
    return not any(phrase in joined for phrase in blocked_phrases)


async def explain_finding(
    finding: Finding,
    mode: ExplanationMode | str = "founder",
    language: str = "English",
    include_code: bool = False,
) -> AIExplanation:
    if not is_safe_ai_request(finding):
        return fallback_finding_explanation(finding, mode, language, status="blocked_by_policy")

    status = ai_status()
    if not status["provider_configured"]:
        return fallback_finding_explanation(finding, mode, language)

    provider = status["provider"]
    prompt = build_safe_prompt(finding, str(mode), language, include_code)
    try:
        if provider == "openai":
            return await _call_openai(prompt, finding, mode, language)
        if provider == "anthropic":
            return await _call_anthropic(prompt, finding, mode, language)
    except Exception:
        return fallback_finding_explanation(finding, mode, language, status="provider_error")

    return fallback_finding_explanation(finding, mode, language)


async def _call_openai(prompt: str, finding: Finding, mode: str, language: str) -> AIExplanation:
    api_key = settings.openai_api_key or settings.ai_api_key
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": settings.ai_model,
        "messages": [
            {"role": "system", "content": "You produce safe, concise Web3 security explanations as JSON only."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
    }
    async with httpx.AsyncClient(timeout=settings.ai_timeout_seconds) as client:
        response = await client.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        data = json.loads(content)
    return _explanation_from_provider_data(data, finding, mode, language, "openai")


async def _call_anthropic(prompt: str, finding: Finding, mode: str, language: str) -> AIExplanation:
    headers = {
        "x-api-key": settings.anthropic_api_key or settings.ai_api_key or "",
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    payload = {
        "model": settings.anthropic_model,
        "max_tokens": 900,
        "temperature": 0.2,
        "messages": [{"role": "user", "content": prompt}],
    }
    async with httpx.AsyncClient(timeout=settings.ai_timeout_seconds) as client:
        response = await client.post("https://api.anthropic.com/v1/messages", headers=headers, json=payload)
        response.raise_for_status()
        blocks = response.json().get("content", [])
        text = "".join(block.get("text", "") for block in blocks if block.get("type") == "text")
        data = json.loads(text)
    return _explanation_from_provider_data(data, finding, mode, language, "anthropic")


def _explanation_from_provider_data(data: dict[str, Any], finding: Finding, mode: str, language: str, provider: str) -> AIExplanation:
    fallback = fallback_finding_explanation(finding, mode, language)
    return AIExplanation(
        status="provider_success",
        provider=provider,
        mode=mode,
        language=language,
        summary=str(data.get("summary") or fallback.summary),
        business_impact=str(data.get("business_impact") or fallback.business_impact),
        developer_guidance=str(data.get("developer_guidance") or fallback.developer_guidance),
        safe_fix_direction=str(data.get("safe_fix_direction") or fallback.safe_fix_direction),
        manual_review_note=str(data.get("manual_review_note") or fallback.manual_review_note),
        confidence_note=str(data.get("confidence_note") or fallback.confidence_note),
    )


async def summarize_report(report: dict[str, Any], language: str = "English", mode: str = "pre_audit") -> AIExplanation:
    # Keep report-level explanation local by default. This avoids sending full project details to a third-party AI unless future settings explicitly allow it.
    score = report.get("combined", {}).get("available_score") or report.get("combined", {}).get("overall_score") or "not assessed"
    risk = report.get("combined", {}).get("risk_label", "Not assessed")
    priority_count = len(report.get("priority_actions", []))
    pseudo = Finding(
        id="report-summary",
        module="contract",
        severity="medium" if isinstance(score, int) and score >= 60 else "high",
        title=f"Launch readiness summary: {risk}",
        description=f"Available score: {score}. Priority actions: {priority_count}.",
        confidence="medium",
        source="Report Layer",
        category="report",
        business_impact="The project should fix high-priority findings before public launch and use manual review for sensitive assets.",
        developer_explanation="The report combines module-level signals into a preliminary launch readiness view.",
        recommendation="Review priority actions, fix critical/high findings first, then regenerate the report.",
        paid_review_recommended=True,
    )
    return fallback_finding_explanation(pseudo, mode, language)
