import hashlib
import json
import re
from datetime import datetime, timezone
from urllib.parse import urljoin

import httpx

from app.core.config import settings
from app.core.security import validate_public_http_url
from app.models.schemas import Finding, ModuleScore, ScanResponse
from app.services.scan_website import _safe_fetch
from app.services.scoring import priority_actions, risk_label, score_findings, severity_breakdown

SECRET_RE = re.compile(r"(?i)(secret|private[_-]?key|api[_-]?key|jwt[_-]?secret|bearer\s+[a-z0-9._-]{20,})")
AUTH_WORDS = ["authorization", "bearer", "oauth", "jwt", "apiKey", "securitySchemes", "cookieAuth"]
DANGEROUS_CORS = ["*", "null"]


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()

def _finding(idx: int, severity: str, title: str, description: str, recommendation: str, confidence: str = "medium", category: str = "api_deep") -> Finding:
    return Finding(
        id=f"api-deep-{idx}",
        module="api_deep",
        severity=severity,
        title=title,
        description=description,
        confidence=confidence,
        source="API Deep Readiness Scanner",
        category=category,
        rule_id=f"API-DEEP-{idx}",
        business_impact="API launch gaps can expose allowlists, rewards, admin actions, metadata, payment callbacks, or user data during Web3 launch.",
        developer_explanation=description,
        recommendation=recommendation,
        paid_review_recommended=severity in {"critical", "high"},
    )

async def run_api_deep_readiness_scan(api_base_url: str | None = None, project_name: str | None = None, openapi_json: str | None = None, api_code: str | None = None, notes: str | None = None, ownership_verified: bool = False) -> ScanResponse:
    findings: list[Finding] = []
    idx = 1
    input_material = "|".join([api_base_url or "", openapi_json or "", api_code or "", notes or ""])
    if len(input_material.strip()) < 8:
        raise ValueError("Provide an API base URL, OpenAPI JSON, code snippet, or notes for API deep readiness scan.")
    metadata: dict = {
        "mode": "safe_api_readiness_only",
        "ownership_verified": ownership_verified,
        "no_fuzzing": True,
        "no_auth_bypass": True,
        "no_payload_spraying": True,
        "safe_endpoints_checked": [],
        "openapi_detected": False,
        "graphql_detected": False,
        "cors_headers": {},
        "auth_evidence": [],
        "webhook_evidence": [],
    }

    if api_base_url:
        safe_url = validate_public_http_url(api_base_url)
        timeout = httpx.Timeout(settings.api_deep_scan_timeout_seconds)
        headers = {"User-Agent": settings.website_scanner_user_agent, "Accept": "application/json,text/html,*/*"}
        async with httpx.AsyncClient(timeout=timeout, headers=headers) as client:
            root = await _safe_fetch(client, "HEAD", safe_url, read_body=False)
            metadata["safe_endpoints_checked"].append({"url": safe_url, "method": "HEAD", "status_code": root.status_code, "error": root.error})
            cors = {k: v for k, v in (root.headers or {}).items() if k.startswith("access-control")}
            metadata["cors_headers"] = cors
            origin = cors.get("access-control-allow-origin", "")
            if origin in DANGEROUS_CORS:
                findings.append(_finding(idx, "high", "Wildcard/Weak CORS Policy Evidence", f"Passive HEAD check found Access-Control-Allow-Origin: {origin!r}.", "Lock CORS to trusted frontend domains, avoid wildcard with credentials, and document staging/prod origins.")); idx += 1
            for path in ["/openapi.json", "/swagger", "/docs", "/graphql"]:
                target = urljoin(safe_url.rstrip("/") + "/", path.lstrip("/"))
                res = await _safe_fetch(client, "GET" if path == "/openapi.json" else "HEAD", target, read_body=path == "/openapi.json", max_redirects=2)
                metadata["safe_endpoints_checked"].append({"url": target, "method": "GET" if path == "/openapi.json" else "HEAD", "status_code": res.status_code, "error": res.error})
                if path == "/openapi.json" and res.status_code and res.status_code < 400 and res.body_text:
                    metadata["openapi_detected"] = True
                    openapi_json = openapi_json or res.body_text[: settings.max_api_deep_openapi_chars]
                if path == "/graphql" and res.status_code and res.status_code < 405:
                    metadata["graphql_detected"] = True
                    findings.append(_finding(idx, "medium", "GraphQL Endpoint Publicly Reachable", "A /graphql endpoint responded to a passive safe check.", "Confirm auth, introspection policy, query depth limits, rate limits, and admin resolver protection.")); idx += 1
                if path in {"/docs", "/swagger"} and res.status_code and res.status_code < 400:
                    findings.append(_finding(idx, "low", f"Public API Documentation Endpoint Reachable: {path}", f"{path} responded to a passive check.", "Public docs can be fine, but remove sensitive schemas/examples and ensure admin endpoints are not exposed.")); idx += 1

    if openapi_json:
        try:
            spec = json.loads(openapi_json)
            metadata["openapi_detected"] = True
            paths = spec.get("paths", {}) if isinstance(spec, dict) else {}
            metadata["openapi_path_count"] = len(paths)
            serialized = json.dumps(spec)[: settings.max_api_deep_openapi_chars]
            auth_hits = [word for word in AUTH_WORDS if word.lower() in serialized.lower()]
            metadata["auth_evidence"] = auth_hits
            if not auth_hits:
                findings.append(_finding(idx, "high", "OpenAPI Spec Has No Obvious Auth/Security Scheme", "The provided/detected OpenAPI JSON did not show obvious auth/security keywords.", "Add explicit securitySchemes and per-route security requirements. Manually review public vs protected endpoints.")); idx += 1
            risky_paths = [path for path in paths if any(word in path.lower() for word in ["admin", "withdraw", "airdrop", "allowlist", "reward", "mint", "webhook"])]
            if risky_paths:
                findings.append(_finding(idx, "medium", "Sensitive API Routes Need Manual Access-Control Review", f"Sensitive-looking routes detected: {', '.join(risky_paths[:8])}.", "Verify role checks, BOLA/IDOR protection, request validation, audit logs, and rate limits for these routes.")); idx += 1
            if "webhook" in serialized.lower() and "signature" not in serialized.lower():
                findings.append(_finding(idx, "high", "Webhook Route Without Signature Evidence", "OpenAPI mentions webhook but no signature verification evidence was found.", "Require HMAC/signature verification, replay protection, timestamp validation, and idempotency for all payment/oracle/webhook callbacks.")); idx += 1
        except Exception:
            findings.append(_finding(idx, "low", "OpenAPI JSON Could Not Be Parsed", "Provided/detected OpenAPI content was not valid JSON.", "Provide valid OpenAPI JSON for stronger API readiness review.")); idx += 1

    combined_text = "\n".join([api_code or "", notes or ""])
    low = combined_text.lower()
    if api_code:
        if "debug=true" in low or "debug: true" in low:
            findings.append(_finding(idx, "high", "Debug Mode Evidence In API Code", "API code snippet contains debug mode evidence.", "Disable debug mode in production and ensure stack traces/secrets are not exposed.")); idx += 1
        if "allow_origins=[\"*\"]" in low or "cors" in low and "*" in low:
            findings.append(_finding(idx, "high", "Wildcard CORS Evidence In API Code", "API code snippet suggests wildcard CORS.", "Restrict CORS to trusted frontend origins only.")); idx += 1
        if SECRET_RE.search(api_code):
            findings.append(_finding(idx, "critical", "Secret-Like Value Evidence In API Code", "API code snippet contains secret/private-key/API-key-like text.", "Move secrets to backend environment variables or secret manager. Rotate any exposed keys immediately.")); idx += 1
        if "rate limit" not in low and "ratelimit" not in low and "limiter" not in low:
            findings.append(_finding(idx, "medium", "No Rate-Limit Evidence In Provided API Code", "The provided API code did not show obvious rate limiting.", "Add per-IP/per-user rate limits for scan, payment, auth, webhook, and claim/allowlist APIs.")); idx += 1
        if "audit" not in low and "logger" not in low and "log" not in low:
            findings.append(_finding(idx, "low", "No Audit Logging Evidence In Provided API Code", "No obvious audit logging evidence was found in the provided API snippet.", "Log admin actions, payment events, allowlist/rewards changes, and manual review status changes.")); idx += 1
    if notes and any(word in low for word in ["admin", "withdraw", "reward", "allowlist"]):
        if not any(word in low for word in ["role", "rbac", "owner", "admin only", "jwt"]):
            findings.append(_finding(idx, "medium", "Sensitive API Notes Without Access-Control Evidence", "Notes mention sensitive API behavior but no access-control evidence.", "Document who can call sensitive APIs, how user/project ownership is checked, and how BOLA/IDOR is prevented.")); idx += 1

    score = score_findings(findings)
    return ScanResponse(
        report_id=f"W3G-APIDEEP-{_hash(input_material)[:12]}",
        generated_at=datetime.now(timezone.utc),
        project_name=project_name,
        module_score=ModuleScore(module="api_deep", score=score, risk_label=risk_label(score)),
        findings=findings,
        severity_breakdown=severity_breakdown(findings),
        priority_actions=priority_actions(findings),
        input_hash=_hash(input_material)[:16],
        engine_version="web3guard-api-deep-readiness-engine-v3.0",
        scan_metadata=metadata,
    )


def api_deep_status() -> dict:
    return {
        "engine": "web3guard-api-deep-readiness-engine-v3.0",
        "status": "live_safe_readiness",
        "real_only": True,
        "checks": ["OpenAPI auth evidence", "safe endpoint presence checks", "CORS evidence", "webhook signature evidence", "API code hints", "BOLA/IDOR education flags"],
        "not_performed": ["fuzzing", "auth bypass", "credential testing", "payload spraying", "destructive tests"],
    }
