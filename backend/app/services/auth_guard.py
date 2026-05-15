from __future__ import annotations

from typing import Any

import httpx
from fastapi import HTTPException, Request

from app.core.config import settings


PROVIDER_NOT_CONFIGURED = "Provider Not Configured"
NEEDS_API_KEY = "Needs API Key"


def _extract_bearer_token(request: Request) -> str | None:
    header = request.headers.get("authorization") or request.headers.get("Authorization")
    if not header or not header.lower().startswith("bearer "):
        return None
    token = header.split(" ", 1)[1].strip()
    return token or None


def supabase_auth_configured() -> bool:
    return bool(settings.supabase_url and settings.supabase_anon_key)


def auth_runtime_status() -> dict[str, Any]:
    configured = supabase_auth_configured()
    return {
        "ok": True,
        "provider": "supabase",
        "configured": configured,
        "status": "Configured" if configured else PROVIDER_NOT_CONFIGURED,
        "needs": [] if configured else ["SUPABASE_URL", "SUPABASE_ANON_KEY", "NEXT_PUBLIC_SUPABASE_URL", "NEXT_PUBLIC_SUPABASE_ANON_KEY"],
        "jwt_verify_enabled": settings.supabase_jwt_verify_enabled,
        "auth_required": settings.supabase_auth_required,
        "service_role_configured": bool(settings.supabase_service_role_key),
        "real_only_note": "Signup/login/logout/session are handled by Supabase Auth only when real Supabase keys are configured. No fake session is created.",
        "blocked_inputs": ["private key", "seed phrase", "mnemonic"],
    }


def verify_supabase_jwt(token: str) -> dict[str, Any] | None:
    if not settings.supabase_url or not settings.supabase_anon_key:
        return None
    url = f"{settings.supabase_url.rstrip('/')}/auth/v1/user"
    headers = {"apikey": settings.supabase_anon_key, "Authorization": f"Bearer {token}"}
    try:
        with httpx.Client(timeout=8) as client:
            response = client.get(url, headers=headers)
            if response.status_code != 200:
                return None
            data = response.json()
            return {
                "id": data.get("id"),
                "email": data.get("email"),
                "aud": data.get("aud"),
                "raw": data,
            }
    except Exception:
        return None


def resolve_user_id(request: Request, provided_user_id: str | None = None) -> tuple[str, dict[str, Any]]:
    """Resolve identity without fake production auth.

    - Supabase/JWT mode: requires a real Supabase bearer token and validates it by
      calling Supabase Auth `/auth/v1/user`.
    - Local developer mode: accepts a supplied local user id only when auth is not
      explicitly required. This is not presented as a real logged-in session.
    """
    token = _extract_bearer_token(request)
    configured = supabase_auth_configured()

    if token and settings.supabase_jwt_verify_enabled:
        verified = verify_supabase_jwt(token)
        if verified and verified.get("id"):
            return str(verified["id"]), {"source": "supabase_jwt", "email": verified.get("email"), "provider": "supabase"}
        raise HTTPException(status_code=401, detail="Invalid or expired Supabase session token.")

    if settings.supabase_auth_required or (settings.supabase_jwt_verify_enabled and settings.app_env.lower() in {"production", "staging"}):
        if not configured:
            raise HTTPException(status_code=503, detail=f"{PROVIDER_NOT_CONFIGURED}: Supabase Auth env keys are missing.")
        raise HTTPException(status_code=401, detail="Supabase session token is required.")

    user_id = provided_user_id or settings.local_demo_user_id
    return user_id, {
        "source": "local_development_user",
        "provider": "local",
        "warning": "No backend JWT verification in local mode. Do not use this mode for private production data.",
    }
