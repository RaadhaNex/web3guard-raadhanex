from fastapi import APIRouter, HTTPException

from app.models.schemas import AIFixAssistantRequest, ExplanationRequest, ReportExplanationRequest
from app.services.ai_explainer import ai_status, explain_finding, summarize_report
from app.services.ai_fix_assistant import fix_assistant_status, suggest_ai_fix

router = APIRouter(prefix="/ai", tags=["ai"])


@router.get("/status")
def get_ai_status():
    return ai_status()


@router.post("/explain-finding")
async def explain_single_finding(payload: ExplanationRequest):
    return await explain_finding(
        payload.finding,
        mode=payload.mode,
        language=payload.preferred_language,
        include_code=payload.include_code,
    )


@router.post("/explain-report")
async def explain_report(payload: ReportExplanationRequest):
    return await summarize_report(payload.report, language=payload.preferred_language, mode=payload.mode)


@router.get("/fix-assistant/status")
def get_fix_assistant_status():
    return fix_assistant_status()


@router.post("/fix-assistant/suggest")
async def suggest_fix(payload: AIFixAssistantRequest):
    if not payload.real_only_acknowledged:
        raise HTTPException(status_code=400, detail="Real-only acknowledgement is required. AI suggestions are not guaranteed fixes and are never auto-applied.")
    if payload.include_code and payload.code_context and not payload.privacy_acknowledged:
        # Still allow fallback guidance, but never send code to provider. The service will mark the safety flag clearly.
        pass
    return await suggest_ai_fix(payload)
