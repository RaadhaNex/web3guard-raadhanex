from __future__ import annotations

import uuid
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.config import settings

SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=(), payment=(), usb=()",
    "X-Robots-Tag": "noindex, nofollow",
    "Cross-Origin-Opener-Policy": "same-origin",
    "Cross-Origin-Resource-Policy": "same-site",
}


def csp_value() -> str:
    # API-safe CSP. Frontend has its own Next.js headers in vercel.json.
    return getattr(settings, "security_csp", "default-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'")


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                if int(content_length) > settings.max_request_body_bytes:
                    return JSONResponse(
                        status_code=413,
                        content={
                            "detail": "Request body too large for MVP safety limits.",
                            "max_request_body_bytes": settings.max_request_body_bytes,
                            "request_id": request_id,
                        },
                    )
            except ValueError:
                pass
        response = await call_next(request)
        if settings.security_headers_enabled:
            for key, value in SECURITY_HEADERS.items():
                response.headers.setdefault(key, value)
            response.headers.setdefault("Content-Security-Policy", csp_value())
            if settings.hsts_enabled and settings.app_env.lower() in {"production", "staging"}:
                response.headers.setdefault("Strict-Transport-Security", f"max-age={settings.hsts_max_age}; includeSubDomains")
        response.headers.setdefault("X-Request-ID", request_id)
        response.headers.setdefault("X-Web3Guard-Disclaimer", "pre-audit-readiness-not-certified-audit")
        return response
