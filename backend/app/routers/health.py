from fastapi import APIRouter
from app.core.config import settings
from app.services.local_qa import validate_environment

router = APIRouter(tags=["health"])


@router.get("/health")
def health():
    return {
        "ok": True,
        "service": settings.app_name,
        "env": settings.app_env,
        "phase": "Mega Phase G - Security Hardening + Final Production Launch QA",
        "python": "3.12 required",
        "frontend_origin": settings.frontend_origin,
        "backend_url": settings.backend_url,
        "ai_enabled": settings.ai_enabled,
        "manual_upi_verification": True,
        "razorpay_enabled": settings.razorpay_enabled,
        "razorpay_configured": bool(settings.razorpay_key_id and settings.razorpay_key_secret),
        "certified_audit": False,
        "auth_database_foundation": True,
        "storage_mode": settings.storage_mode,
        "supabase_configured": bool(settings.supabase_url and settings.supabase_anon_key),
        "disclaimer": "Preliminary security review only. Not a certified audit.",
    }


@router.get("/health/readiness")
def readiness():
    return validate_environment()
