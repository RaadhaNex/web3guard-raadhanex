import asyncio
import hashlib
import html.parser
import time
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlencode, urljoin, urlparse, urlunparse

import httpx

from app.core.config import settings
from app.core.security import validate_public_http_url
from app.models.schemas import Finding, ModuleScore, ScanResponse
from app.services.scoring import priority_actions, risk_label, score_findings_with_trace, severity_breakdown

SECURITY_HEADERS = {
    "strict-transport-security": (
        "medium",
        "HSTS Header Missing",
        "HSTS helps force browsers to use HTTPS and reduces downgrade/SSL-stripping risk.",
        "Add Strict-Transport-Security after HTTPS is fully working. Example: max-age=31536000; includeSubDomains; preload.",
    ),
    "content-security-policy": (
        "high",
        "Content-Security-Policy Missing",
        "CSP reduces XSS, malicious script injection, wallet-drainer script, and supply-chain script impact.",
        "Add a strict Content-Security-Policy. Start with default-src 'self'; script-src 'self' trusted-domains; object-src 'none'; frame-ancestors 'none'.",
    ),
    "x-frame-options": (
        "medium",
        "X-Frame-Options Missing",
        "Frame protection reduces clickjacking risk on mint, claim, login, and wallet-connect pages.",
        "Add X-Frame-Options: DENY or SAMEORIGIN. If using CSP frame-ancestors, keep policy clear and tested.",
    ),
    "x-content-type-options": (
        "low",
        "X-Content-Type-Options Missing",
        "nosniff reduces MIME confusion and unsafe browser interpretation risk.",
        "Add X-Content-Type-Options: nosniff.",
    ),
    "referrer-policy": (
        "low",
        "Referrer-Policy Missing",
        "Referrer policy reduces accidental leakage of wallet/referral/session URLs to third-party domains.",
        "Add Referrer-Policy: strict-origin-when-cross-origin or no-referrer depending on product needs.",
    ),
    "permissions-policy": (
        "low",
        "Permissions-Policy Missing",
        "Permissions Policy limits browser feature abuse such as camera, microphone, geolocation, or clipboard access.",
        "Add a Permissions-Policy that disables unused browser capabilities.",
    ),
}

LIMITED_PATH_HINTS = [
    "/.env",
    "/.env.local",
    "/.git/config",
    "/.git/HEAD",
    "/admin",
    "/api",
    "/api/users",
    "/api/debug",
    "/docs",
    "/swagger",
    "/swagger.json",
    "/openapi.json",
    "/graphql",
    "/backup",
    "/config",
    "/config.json",
    "/debug",
    "/phpinfo.php",
]
DANGEROUS_PATHS = {"/.env", "/.env.local", "/.git/config", "/.git/HEAD", "/backup", "/config", "/config.json", "/debug", "/api/debug", "/phpinfo.php"}
PROOF_FETCH_PATHS = {
    "/.env",
    "/.env.local",
    "/.git/config",
    "/.git/HEAD",
    "/api",
    "/api/users",
    "/api/debug",
    "/docs",
    "/swagger",
    "/swagger.json",
    "/openapi.json",
    "/graphql",
    "/config",
    "/config.json",
    "/debug",
    "/phpinfo.php",
}
SCRIPT_RISK_KEYWORDS = ["eval", "drainer", "walletconnect", "metamask", "claim", "mint"]
DAPP_PAGE_KEYWORDS = ["walletconnect", "metamask", "connect wallet", "mint", "claim", "airdrop", "swap", "stake", "approve", "permit", "bridge", "presale"]
EVM_ADDRESS_HINT_RE = re.compile(r"0x[a-fA-F0-9]{40}")
CDN_HOST_HINTS = (
    "cdn.", "cdnjs", "jsdelivr", "unpkg", "bootstrapcdn", "stackpath",
    "cloudflare", "googleapis", "gstatic", "fontawesome", "tailwindcss",
    "akamai", "fastly", "netdna", "assets.", "static.",
)
OPEN_REDIRECT_PARAMS = ("redirect", "url", "next", "return", "to")
OPEN_REDIRECT_TARGET = "http://evil.com"
ROBOTS_SENSITIVE_WORDS = ("admin", "api", "config", "debug", "internal", "staging", "backup")



@dataclass
class SafeFetchResult:
    url: str
    status_code: int | None = None
    headers: dict[str, str] = field(default_factory=dict)
    body_text: str = ""
    redirect_chain: list[dict[str, str | int]] = field(default_factory=list)
    elapsed_ms: int = 0
    truncated: bool = False
    error: str | None = None


class ScriptParser(html.parser.HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.scripts: list[str] = []
        self.script_tags: list[dict[str, str]] = []
        self.stylesheet_links: list[dict[str, str]] = []
        self.image_tags: list[dict[str, str]] = []
        self.inline_script_count = 0
        self.forms: list[dict[str, str]] = []
        self.links: list[dict[str, str]] = []
        self.iframes: list[dict[str, str]] = []
        self.objects: list[dict[str, str]] = []
        self.meta_tags: list[dict[str, str]] = []
        self.base_tags: list[dict[str, str]] = []
        self.current_form: dict[str, str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag_name = tag.lower()
        attr_map = {key.lower(): value or "" for key, value in attrs}
        if tag_name == "script":
            src = attr_map.get("src", "")
            if src:
                self.scripts.append(src)
                self.script_tags.append(attr_map)
            else:
                self.inline_script_count += 1
        elif tag_name == "link":
            rel_tokens = {token.strip().lower() for token in attr_map.get("rel", "").split()}
            if "stylesheet" in rel_tokens and attr_map.get("href"):
                self.stylesheet_links.append(attr_map)
        elif tag_name == "img":
            if attr_map.get("src"):
                self.image_tags.append(attr_map)
        elif tag_name == "form":
            self.current_form = dict(attr_map)
            self.current_form.setdefault("password_input_count", "0")
            self.current_form.setdefault("hidden_input_count", "0")
            self.forms.append(self.current_form)
        elif tag_name == "input" and self.current_form is not None:
            input_type = attr_map.get("type", "text").lower()
            if input_type == "password":
                self.current_form["password_input_count"] = str(int(self.current_form.get("password_input_count", "0") or "0") + 1)
            if input_type == "hidden":
                self.current_form["hidden_input_count"] = str(int(self.current_form.get("hidden_input_count", "0") or "0") + 1)
        elif tag_name == "a":
            self.links.append(attr_map)
        elif tag_name == "iframe":
            self.iframes.append(attr_map)
        elif tag_name in {"object", "embed"}:
            self.objects.append({"tag": tag_name, **attr_map})
        elif tag_name == "meta":
            self.meta_tags.append(attr_map)
        elif tag_name == "base":
            self.base_tags.append(attr_map)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "form":
            self.current_form = None


def _finding(
    idx: int,
    severity: str,
    title: str,
    description: str,
    recommendation: str,
    confidence: str = "medium",
    category: str = "website_surface",
    rule_id: str | None = None,
) -> Finding:
    return Finding(
        id=f"website-{idx}",
        module="website",
        severity=severity,
        title=title,
        description=description,
        evidence=description,
        fix=recommendation,
        confidence=confidence,
        source="Passive Website Surface Scanner",
        category=category,
        rule_id=rule_id,
        business_impact="Website and dApp surface issues can reduce launch trust, increase phishing exposure, or weaken wallet/user protection before launch.",
        developer_explanation=description,
        recommendation=recommendation,
        references=[],
        paid_review_recommended=severity in {"critical", "high"},
    )


def _host_of(raw_url: str) -> str:
    parsed = urlparse(raw_url)
    return parsed.hostname.lower() if parsed.hostname else ""


def _domain_of_script(src: str, base_url: str) -> str:
    absolute = urljoin(base_url, src)
    return _host_of(absolute)


def _is_external_script(src: str, base_url: str) -> bool:
    base_host = _host_of(base_url)
    src_host = _domain_of_script(src, base_url)
    return bool(src_host and src_host != base_host)


def _headers_lower(headers: httpx.Headers | dict[str, str]) -> dict[str, str]:
    return {str(k).lower(): str(v) for k, v in headers.items()}


def _hash_input(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _split_set_cookie_header(value: str) -> list[str]:
    if not value:
        return []
    # Good enough for scanner evidence: avoid breaking on common Expires comma by
    # splitting only when a comma is followed by a cookie-name style token.
    parts = re.split(r",\s*(?=[A-Za-z0-9_\-]+=)", value)
    return [part.strip() for part in parts if part.strip()]


def _cookie_security_evidence(set_cookie_value: str | None) -> dict:
    cookies = []
    insecure = []
    missing_http_only = []
    missing_same_site = []
    missing_secure = []
    for raw_cookie in _split_set_cookie_header(set_cookie_value or ""):
        lower = raw_cookie.lower()
        name = raw_cookie.split("=", 1)[0].strip()[:80] or "cookie"
        info = {
            "name": name,
            "secure": "secure" in lower,
            "httponly": "httponly" in lower,
            "samesite": "samesite=" in lower,
            "raw_preview": raw_cookie[:180],
        }
        cookies.append(info)
        if not info["secure"]:
            missing_secure.append(name)
        if not info["httponly"]:
            missing_http_only.append(name)
        if not info["samesite"]:
            missing_same_site.append(name)
        if not info["secure"] or not info["httponly"] or not info["samesite"]:
            insecure.append(info)
    return {
        "cookie_count": len(cookies),
        "cookies": cookies[:20],
        "missing_secure": missing_secure[:20],
        "missing_http_only": missing_http_only[:20],
        "missing_same_site": missing_same_site[:20],
        "insecure_cookie_count": len(insecure),
    }


def _csp_analysis(csp: str) -> dict:
    lower = csp.lower()
    return {
        "present": bool(csp),
        "has_default_src": "default-src" in lower,
        "has_script_src": "script-src" in lower,
        "has_object_src_none": "object-src 'none'" in lower or 'object-src "none"' in lower,
        "has_frame_ancestors": "frame-ancestors" in lower,
        "allows_unsafe_inline": "'unsafe-inline'" in lower,
        "allows_unsafe_eval": "'unsafe-eval'" in lower,
        "allows_wildcard": "*" in lower,
        "raw_preview": csp[:500],
    }


SECRET_NAME_RE = re.compile(
    r"(?i)(secret|token|password|passwd|pwd|private[_-]?key|mnemonic|seed[_-]?phrase|database_url|db_url|service[_-]?role|razorpay[_-]?key[_-]?secret|openai[_-]?api[_-]?key|aws[_-]?(access|secret))"
)
ENV_ASSIGNMENT_RE = re.compile(r"(?m)^\s*([A-Z0-9_]*(?:SECRET|TOKEN|KEY|PASSWORD|PASS|PRIVATE|MNEMONIC|DATABASE_URL|DB_URL|SERVICE_ROLE)[A-Z0-9_]*)\s*=\s*([^\n#]+)")
JSON_SECRET_RE = re.compile(r"(?i)[\"']([a-z0-9_.-]*(?:secret|token|password|private|mnemonic|database_url|service_role)[a-z0-9_.-]*)[\"']\s*:\s*[\"']([^\"']{6,})[\"']")


def _redact_secret_text(value: str) -> str:
    text = value[:4000]
    text = re.sub(
        r"(?m)^\s*([A-Z0-9_]*(?:SECRET|TOKEN|KEY|PASSWORD|PASS|PRIVATE|MNEMONIC|DATABASE_URL|DB_URL|SERVICE_ROLE)[A-Z0-9_]*\s*=\s*)([^\n#]+)",
        lambda m: m.group(1) + "<redacted>",
        text,
    )
    text = re.sub(
        r"(?i)([\"']?[a-z0-9_.-]*(?:secret|token|password|private|mnemonic|database_url|service_role)[a-z0-9_.-]*[\"']?\s*:\s*[\"'])([^\"']{6,})([\"'])",
        lambda m: m.group(1) + "<redacted>" + m.group(3),
        text,
    )
    text = re.sub(r"AKIA[0-9A-Z]{16}", "AKIA<redacted>", text)
    text = re.sub(r"(?i)(bearer\s+)[a-z0-9._=-]{16,}", r"\1<redacted>", text)
    text = re.sub(r"0x[a-fA-F0-9]{64}", "0x<redacted-private-key-like-value>", text)
    return text[:900]


def _secret_keys_in_text(text: str) -> list[str]:
    keys = set()
    for match in ENV_ASSIGNMENT_RE.finditer(text[:5000]):
        value = (match.group(2) or "").strip().strip("'\"")
        if value and value.lower() not in {"changeme", "example", "placeholder", "your_key_here", "null", "none"}:
            keys.add(match.group(1)[:80])
    for match in JSON_SECRET_RE.finditer(text[:5000]):
        keys.add(match.group(1)[:80])
    return sorted(keys)[:20]


def _proof_evidence(path: str, status_code: int | None, content_type: str, body: str) -> dict | None:
    if status_code != 200 or not body:
        return None
    lower_path = path.lower()
    lower_body = body[:12000].lower()
    content_type_lower = content_type.lower()
    secret_keys = _secret_keys_in_text(body)

    if lower_path in {"/.env", "/.env.local"} and (secret_keys or "=" in body[:2000]):
        return {
            "kind": "exposed_env_file",
            "severity": "critical" if secret_keys else "high",
            "title": "Public .env File Exposure Confirmed",
            "category": "confirmed_secret_exposure",
            "confidence": "high",
            "evidence": f"{path} returned HTTP 200 and exposed env-style keys: {', '.join(secret_keys[:8]) or 'env-style assignments'}",
            "recommendation": "Immediately remove public .env files, rotate exposed secrets, and block dotfiles at the edge/server.",
            "raw_preview": _redact_secret_text(body),
        }

    if lower_path == "/.git/config" and "[core]" in lower_body and ("[remote" in lower_body or "repositoryformatversion" in lower_body):
        return {
            "kind": "exposed_git_config",
            "severity": "critical",
            "title": "Public .git Repository Metadata Exposure Confirmed",
            "category": "confirmed_repo_exposure",
            "confidence": "high",
            "evidence": "/.git/config returned HTTP 200 with Git config markers.",
            "recommendation": "Block .git access immediately and rotate any secrets that may have existed in repository history.",
            "raw_preview": _redact_secret_text(body),
        }

    if lower_path == "/.git/head" and "ref: refs/" in lower_body:
        return {
            "kind": "exposed_git_head",
            "severity": "high",
            "title": "Public .git HEAD Exposure Confirmed",
            "category": "confirmed_repo_exposure",
            "confidence": "high",
            "evidence": "/.git/HEAD returned HTTP 200 with refs marker.",
            "recommendation": "Block .git paths at the web server/CDN and confirm repository objects are not accessible.",
            "raw_preview": _redact_secret_text(body),
        }

    if secret_keys and (lower_path.endswith(".json") or lower_path in {"/config", "/config.json"} or "javascript" in content_type_lower):
        return {
            "kind": "public_config_secret",
            "severity": "critical",
            "title": "Public Config/Asset Contains Secret-Like Key",
            "category": "confirmed_secret_exposure",
            "confidence": "high",
            "evidence": f"{path} returned HTTP 200 and contains secret-like keys: {', '.join(secret_keys[:8])}.",
            "recommendation": "Remove secrets from public assets/configs and rotate affected credentials immediately.",
            "raw_preview": _redact_secret_text(body),
        }

    if lower_path.endswith(".map") and ("\"sources\"" in lower_body and "\"mappings\"" in lower_body):
        return {
            "kind": "public_source_map",
            "severity": "medium",
            "title": "Public JavaScript Source Map Confirmed",
            "category": "confirmed_source_exposure",
            "confidence": "high",
            "evidence": f"{path} returned HTTP 200 and contains source-map markers.",
            "recommendation": "Disable public production source maps or verify they contain no secrets/internal implementation details.",
            "raw_preview": _redact_secret_text(body),
        }

    if lower_path in {"/openapi.json", "/swagger.json"} and ("\"openapi\"" in lower_body or "\"swagger\"" in lower_body):
        return {
            "kind": "public_api_schema",
            "severity": "medium",
            "title": "Public API Schema Exposure Confirmed",
            "category": "confirmed_api_exposure",
            "confidence": "high",
            "evidence": f"{path} returned HTTP 200 with OpenAPI/Swagger markers.",
            "recommendation": "Keep public API docs intentional, remove sensitive/internal endpoints, and require auth for admin-only docs.",
            "raw_preview": _redact_secret_text(body),
        }

    if lower_path in {"/docs", "/swagger"} and ("swagger-ui" in lower_body or "openapi" in lower_body or "api docs" in lower_body):
        return {
            "kind": "public_api_docs",
            "severity": "low",
            "title": "Public API Documentation Surface Confirmed",
            "category": "confirmed_api_exposure",
            "confidence": "high",
            "evidence": f"{path} returned HTTP 200 with API documentation markers.",
            "recommendation": "Confirm this documentation is intended for public users and does not reveal admin/internal operations.",
            "raw_preview": _redact_secret_text(body),
        }

    if lower_path == "/graphql" and ("graphql" in lower_body or "must provide query" in lower_body or "graphiql" in lower_body):
        return {
            "kind": "public_graphql",
            "severity": "medium",
            "title": "Public GraphQL Endpoint Surface Confirmed",
            "category": "confirmed_api_exposure",
            "confidence": "high",
            "evidence": "/graphql returned HTTP 200 with GraphQL markers.",
            "recommendation": "Disable public GraphiQL/introspection if not needed and require auth/rate limits for sensitive resolvers.",
            "raw_preview": _redact_secret_text(body),
        }

    if lower_path in {"/debug", "/api/debug", "/phpinfo.php"} and any(marker in lower_body for marker in ["traceback", "stack trace", "werkzeug", "phpinfo()", "environment", "debugger"]):
        return {
            "kind": "public_debug_endpoint",
            "severity": "high",
            "title": "Public Debug/Diagnostics Endpoint Confirmed",
            "category": "confirmed_debug_exposure",
            "confidence": "high",
            "evidence": f"{path} returned HTTP 200 with debug/diagnostic markers.",
            "recommendation": "Disable public debug endpoints and review logs/config exposure before launch.",
            "raw_preview": _redact_secret_text(body),
        }

    if lower_path == "/admin" and any(marker in lower_body for marker in ["admin", "dashboard", "sign in", "login", "password"]):
        return {
            "kind": "public_admin_surface",
            "severity": "low",
            "title": "Public Admin/Login Surface Detected",
            "category": "confirmed_admin_surface",
            "confidence": "medium",
            "evidence": "/admin returned HTTP 200 with admin/login-like markers.",
            "recommendation": "Confirm admin routes require strong auth/MFA and are intentionally public. Consider IP allow-listing or moving admin off public paths.",
            "raw_preview": _redact_secret_text(body),
        }

    if lower_path in {"/api", "/api/users"} and ("application/json" in content_type_lower or body.strip().startswith(("{", "["))):
        if any(marker in lower_body for marker in ["email", "password", "access_token", "secret", "private", "user_id"]):
            return {
                "kind": "public_api_data",
                "severity": "high",
                "title": "Public API Data Exposure Hint Confirmed",
                "category": "confirmed_api_exposure",
                "confidence": "medium",
                "evidence": f"{path} returned HTTP 200 JSON-like response with sensitive-field markers.",
                "recommendation": "Verify this endpoint does not expose private user/project data without authentication.",
                "raw_preview": _redact_secret_text(body),
            }

    return None


def _proof_finding(idx: int, proof: dict, path: str) -> Finding:
    return _finding(
        idx,
        str(proof.get("severity") or "medium"),
        str(proof.get("title") or "Confirmed Public Exposure"),
        str(proof.get("evidence") or f"{path} returned public evidence."),
        str(proof.get("recommendation") or "Review and fix before public launch."),
        str(proof.get("confidence") or "high"),
        str(proof.get("category") or "confirmed_public_exposure"),
        f"WEB-PROOF-{str(proof.get('kind') or path).upper().replace('/', '-').replace('.', '')[:60]}",
    )


async def _safe_fetch(
    client: httpx.AsyncClient,
    method: str,
    url: str,
    *,
    read_body: bool,
    max_redirects: int = 5,
) -> SafeFetchResult:
    current_url = validate_public_http_url(url)
    redirect_chain: list[dict[str, str | int]] = []
    started = time.perf_counter()
    max_bytes = settings.website_scan_max_body_bytes

    for _ in range(max_redirects + 1):
        validate_public_http_url(current_url)
        request = client.build_request(method, current_url)
        try:
            response = await client.send(request, stream=True, follow_redirects=False)
        except Exception as exc:
            return SafeFetchResult(url=current_url, redirect_chain=redirect_chain, elapsed_ms=round((time.perf_counter() - started) * 1000), error=str(exc))

        status = response.status_code
        headers = _headers_lower(response.headers)
        if status in {301, 302, 303, 307, 308} and response.headers.get("location"):
            next_url = urljoin(current_url, response.headers["location"])
            try:
                validate_public_http_url(next_url)
            except ValueError as exc:
                await response.aclose()
                return SafeFetchResult(
                    url=current_url,
                    status_code=status,
                    headers=headers,
                    redirect_chain=redirect_chain,
                    elapsed_ms=round((time.perf_counter() - started) * 1000),
                    error=f"Blocked unsafe redirect target: {exc}",
                )
            redirect_chain.append({"from": current_url, "to": next_url, "status_code": status})
            await response.aclose()
            current_url = next_url
            continue

        body = b""
        truncated = False
        if read_body:
            async for chunk in response.aiter_bytes():
                if len(body) + len(chunk) > max_bytes:
                    remaining = max(0, max_bytes - len(body))
                    body += chunk[:remaining]
                    truncated = True
                    break
                body += chunk
        await response.aclose()
        text = ""
        if read_body and body:
            encoding = response.encoding or "utf-8"
            text = body.decode(encoding, errors="replace")
        return SafeFetchResult(
            url=current_url,
            status_code=status,
            headers=headers,
            body_text=text,
            redirect_chain=redirect_chain,
            elapsed_ms=round((time.perf_counter() - started) * 1000),
            truncated=truncated,
        )

    return SafeFetchResult(
        url=current_url,
        redirect_chain=redirect_chain,
        elapsed_ms=round((time.perf_counter() - started) * 1000),
        error="Too many redirects",
    )


def _same_origin(url: str, base_url: str) -> bool:
    return _host_of(urljoin(base_url, url)) == _host_of(base_url)


def _looks_like_cdn_host(host: str) -> bool:
    clean = (host or "").lower()
    return any(hint in clean for hint in CDN_HOST_HINTS)


def _asset_record(tag: str, attr: dict[str, str], key: str, final_url: str) -> dict[str, Any]:
    raw = attr.get(key, "")
    absolute = urljoin(final_url, raw) if raw else ""
    host = _host_of(absolute)
    return {
        "tag": tag,
        "url": absolute,
        "domain": host,
        "external": bool(host and host != _host_of(final_url)),
        "cdn_like": _looks_like_cdn_host(host),
        "integrity_present": bool(attr.get("integrity")),
        "crossorigin": attr.get("crossorigin", ""),
    }


def _build_probe_url(raw_url: str, param: str) -> str:
    parsed = urlparse(raw_url)
    query = f"{parsed.query}&" if parsed.query else ""
    query += urlencode({param: OPEN_REDIRECT_TARGET})
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path or "/", parsed.params, query, ""))


def _is_evil_redirect(location: str, current_url: str) -> bool:
    target = urljoin(current_url, location or "")
    parsed = urlparse(target)
    return parsed.scheme == "http" and (parsed.hostname or "").lower() == "evil.com"


async def _check_open_redirect(client: httpx.AsyncClient, base_url: str) -> dict[str, Any]:
    checked: list[dict[str, Any]] = []
    findings: list[dict[str, str]] = []
    errors: list[str] = []
    for param in OPEN_REDIRECT_PARAMS[:5]:
        probe_url = _build_probe_url(base_url, param)
        try:
            validate_public_http_url(probe_url)
            # Use the project safe fetch wrapper so tests can monkeypatch it, private-IP
            # blocking remains active, and the probe never follows to the external target.
            result = await asyncio.wait_for(_safe_fetch(client, "GET", probe_url, read_body=False, max_redirects=0), timeout=5)
        except Exception as exc:
            errors.append(f"{param}: {exc}")
            checked.append({"param": param, "url": probe_url, "status_code": None, "location": None, "error": str(exc)[:220]})
            continue
        redirect = result.redirect_chain[0] if result.redirect_chain else {}
        location = str(redirect.get("to") or "")
        status = redirect.get("status_code") or result.status_code
        entry = {"param": param, "url": probe_url, "status_code": status, "location": location or None, "open_redirect": False, "error": result.error}
        if location and _is_evil_redirect(location, probe_url):
            entry["open_redirect"] = True
            findings.append({"param": param, "status_code": str(status or "3xx"), "location": location, "url": probe_url})
        checked.append(entry)
    return {"checked": checked, "findings": findings, "errors": errors[:5]}


def _parse_sensitive_robots_lines(body: str) -> list[dict[str, str]]:
    flagged: list[dict[str, str]] = []
    for line_no, raw_line in enumerate((body or "").splitlines(), start=1):
        clean = raw_line.strip()
        if not clean or clean.startswith("#") or ":" not in clean:
            continue
        key, value = clean.split(":", 1)
        if key.strip().lower() != "disallow":
            continue
        target = value.strip()
        lowered = target.lower()
        hit = next((word for word in ROBOTS_SENSITIVE_WORDS if word in lowered), None)
        if hit:
            flagged.append({"line": str(line_no), "keyword": hit, "disallow": target[:240]})
    return flagged[:30]


def _resolve_caa_records(host: str) -> dict[str, Any]:
    try:
        import dns.resolver  # type: ignore[import-not-found]
    except Exception as exc:
        return {"state": "Not Assessed", "reason": f"dnspython is not installed: {exc}"}
    try:
        answers = dns.resolver.resolve(host, "CAA", lifetime=5)
        records = [str(answer) for answer in answers]
        return {"state": "Assessed", "records": records, "record_count": len(records)}
    except Exception as exc:
        return {"state": "Assessed", "records": [], "record_count": 0, "reason": str(exc)[:220]}


async def _check_dns_caa(host: str) -> dict[str, Any]:
    if not host:
        return {"state": "Not Assessed", "reason": "No hostname available for DNS CAA check."}
    return await asyncio.to_thread(_resolve_caa_records, host)


def _extract_html_evidence(html: str, final_url: str) -> dict:
    parser = ScriptParser()
    try:
        parser.feed(html[: settings.website_scan_max_body_bytes])
    except Exception:
        pass

    sri_assets = []
    mixed_assets = []
    for tag, attr, key in [*( ("script", item, "src") for item in parser.script_tags ), *( ("link", item, "href") for item in parser.stylesheet_links ), *( ("img", item, "src") for item in parser.image_tags )]:
        record = _asset_record(tag, attr, key, final_url)
        if final_url.startswith("https://") and record["url"].startswith("http://"):
            mixed_assets.append(record)
        if tag in {"script", "link"} and record["external"] and record["cdn_like"]:
            sri_assets.append(record)

    cdn_assets_missing_sri = [asset for asset in sri_assets if not asset.get("integrity_present")]

    external_scripts = []
    same_origin_scripts = []
    for src in parser.scripts:
        absolute = urljoin(final_url, src)
        domain = _domain_of_script(src, final_url)
        item = {"src": absolute, "domain": domain, "external": _is_external_script(src, final_url)}
        external_scripts.append(item)
        if not item["external"]:
            same_origin_scripts.append(item)

    mixed_content = [script for script in external_scripts if script["src"].startswith("http://")]
    risky_script_hints = [
        script
        for script in external_scripts
        if any(keyword in script["src"].lower() or keyword in script["domain"].lower() for keyword in SCRIPT_RISK_KEYWORDS)
    ]

    lowered_html = html.lower()
    dapp_keyword_hits = sorted({keyword for keyword in DAPP_PAGE_KEYWORDS if keyword in lowered_html})
    evm_address_hints = sorted(set(EVM_ADDRESS_HINT_RE.findall(html)))[:20]

    external_link_domains = sorted({
        _host_of(urljoin(final_url, link.get("href", "")))
        for link in parser.links
        if link.get("href") and _host_of(urljoin(final_url, link.get("href", ""))) and not _same_origin(link.get("href", ""), final_url)
    })
    target_blank_without_noopener = [
        {"href": urljoin(final_url, link.get("href", "")), "rel": link.get("rel", "")}
        for link in parser.links
        if link.get("target", "").lower() == "_blank" and "noopener" not in link.get("rel", "").lower()
    ][:20]

    insecure_form_actions = []
    external_form_actions = []
    password_forms = []
    for form in parser.forms:
        action = form.get("action", "")
        absolute_action = urljoin(final_url, action) if action else final_url
        if absolute_action.startswith("http://"):
            insecure_form_actions.append({"action": absolute_action, "method": form.get("method", "get")})
        if _host_of(absolute_action) and _host_of(absolute_action) != _host_of(final_url):
            external_form_actions.append({"action": absolute_action, "method": form.get("method", "get")})
        if int(form.get("password_input_count", "0") or "0") > 0:
            password_forms.append({"action": absolute_action, "method": form.get("method", "get"), "password_input_count": form.get("password_input_count", "0")})

    iframe_risks = []
    for iframe in parser.iframes:
        src = iframe.get("src", "")
        iframe_risks.append({
            "src": urljoin(final_url, src) if src else "",
            "external": bool(src and not _same_origin(src, final_url)),
            "sandbox_present": "sandbox" in iframe,
            "allow": iframe.get("allow", ""),
        })

    meta_refresh = []
    noindex_tags = []
    for meta in parser.meta_tags:
        http_equiv = meta.get("http-equiv", "").lower()
        name = meta.get("name", "").lower()
        content = meta.get("content", "")
        if http_equiv == "refresh":
            meta_refresh.append({"content": content})
        if name == "robots" and "noindex" in content.lower():
            noindex_tags.append({"content": content})

    base_http = [base for base in parser.base_tags if base.get("href", "").startswith("http://")]
    source_map_hints = sorted({match.strip() for match in re.findall(r"sourceMappingURL=([^\s'\"<>]+)", html) if match.strip()})[:20]
    source_map_hints.extend(sorted(set(re.findall(r"[A-Za-z0-9_./-]+\.js\.map", html)))[:20])
    source_map_hints = source_map_hints[:20]

    return {
        "script_count": len(parser.scripts),
        "external_script_count": sum(1 for script in external_scripts if script["external"]),
        "inline_script_count": parser.inline_script_count,
        "external_scripts": external_scripts[:25],
        "same_origin_scripts": same_origin_scripts[:25],
        "mixed_content_scripts": mixed_content[:25],
        "mixed_content_assets": mixed_assets[:30],
        "cdn_assets_checked_for_sri": sri_assets[:30],
        "cdn_assets_missing_sri": cdn_assets_missing_sri[:30],
        "risky_script_hints": risky_script_hints[:25],
        "dapp_keyword_hits": dapp_keyword_hits,
        "evm_address_hints": evm_address_hints,
        "form_count": len(parser.forms),
        "forms": parser.forms[:10],
        "password_form_count": len(password_forms),
        "password_forms": password_forms[:10],
        "insecure_form_actions": insecure_form_actions[:10],
        "external_form_actions": external_form_actions[:10],
        "link_count": len(parser.links),
        "external_link_domain_count": len(external_link_domains),
        "external_link_domains": external_link_domains[:30],
        "target_blank_without_noopener": target_blank_without_noopener,
        "iframe_count": len(parser.iframes),
        "iframes": iframe_risks[:20],
        "object_embed_count": len(parser.objects),
        "objects": parser.objects[:10],
        "meta_refresh": meta_refresh[:10],
        "noindex_tags": noindex_tags[:10],
        "base_http": base_http[:10],
        "source_map_hints": source_map_hints,
    }

def _build_response(url: str, project_name: str | None, findings: list[Finding], metadata: dict) -> ScanResponse:
    score_trace = score_findings_with_trace(findings)
    score = int(score_trace["score"])
    metadata["dynamic_score_trace"] = score_trace
    metadata["score_explanation"] = {
        "why_score_may_look_stable": "If the same real findings repeat across scans, the score will repeat. It is not random and not fixed.",
        "when_score_changes": [
            "HTTP status/reachability changes",
            "security headers are added/removed or CSP directives change",
            "external/inline/mixed-content script evidence changes",
            "sensitive path responses change",
            "new real findings are generated or existing findings are fixed",
        ],
        "display_rule": "Website score is the assessed website-surface readiness score. Overall launch confidence is gated until other modules have evidence.",
    }
    metadata["professional_evidence_engine_version"] = "web3guard-passive-website-engine-v3.0-deep-evidence"
    digest = _hash_input(url)[:12]
    return ScanResponse(
        report_id=f"W3G-WEBSITE-{digest}",
        generated_at=datetime.now(timezone.utc),
        project_name=project_name,
        module_score=ModuleScore(module="website", score=score, risk_label=risk_label(score)),
        findings=findings,
        severity_breakdown=severity_breakdown(findings),
        priority_actions=priority_actions(findings),
        input_hash=_hash_input(url)[:16],
        engine_version="web3guard-passive-website-engine-v2.9",
        scan_metadata=metadata,
    )


async def scan_website(url: str, project_name: str | None = None) -> ScanResponse:
    safe_url = validate_public_http_url(url)
    findings: list[Finding] = []
    idx = 1

    metadata: dict = {
        "requested_url": safe_url,
        "final_url": None,
        "status_code": None,
        "response_time_ms": None,
        "redirect_chain": [],
        "headers_present": [],
        "headers_missing": [],
        "robots_status": None,
        "sitemap_status": None,
        "limited_path_results": [],
        "html_evidence": {},
        "safety_controls": {
            "mode": "passive_only",
            "methods_used": ["GET", "HEAD"],
            "max_redirects": 5,
            "timeout_seconds": settings.website_scan_timeout_seconds,
            "max_body_bytes": settings.website_scan_max_body_bytes,
            "private_ip_blocking": True,
            "deep_scan_requires_ownership_verification": True,
            "ownership_methods": ["dns_txt", "well_known"],
            "authorization_checkbox_required": True,
            "no_exploit_payloads": True,
            "no_bruteforce": True,
        },
    }

    if not safe_url.startswith("https://"):
        findings.append(
            _finding(
                idx,
                "medium",
                "Submitted URL Does Not Use HTTPS",
                "The submitted URL starts with http://. Web3 launch pages should prefer HTTPS-first links.",
                "Use https:// URLs publicly and configure a permanent HTTP-to-HTTPS redirect.",
                "high",
                "transport_security",
                "WEB-HTTPS-URL",
            )
        )
        idx += 1

    timeout = httpx.Timeout(settings.website_scan_timeout_seconds)
    headers = {
        "User-Agent": settings.website_scanner_user_agent,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    async with httpx.AsyncClient(timeout=timeout, headers=headers) as client:
        page = await _safe_fetch(client, "GET", safe_url, read_body=True)
        metadata["final_url"] = page.url
        metadata["status_code"] = page.status_code
        metadata["response_time_ms"] = page.elapsed_ms
        metadata["redirect_chain"] = page.redirect_chain

        if page.error or page.status_code is None:
            findings.append(
                _finding(
                    idx,
                    "high",
                    "Website Unreachable, Timed Out, Or Blocked By Safety Rules",
                    f"The passive scanner could not safely fetch the public homepage. Reason: {page.error or 'unknown'}.",
                    "Check DNS, hosting, SSL, redirect chain, firewall rules, and uptime before launch. Ensure redirects do not point to private/internal IP ranges.",
                    "medium",
                    "availability",
                    "WEB-REACHABILITY",
                )
            )
            return _build_response(safe_url, project_name, findings, metadata)

        if page.status_code >= 500:
            findings.append(
                _finding(idx, "high", "Homepage Returns Server Error", f"Homepage returned HTTP {page.status_code}.", "Fix server/hosting errors before launch.", "high", "availability", "WEB-STATUS-5XX")
            )
            idx += 1
        elif page.status_code >= 400:
            findings.append(
                _finding(idx, "medium", "Homepage Returns Client Error", f"Homepage returned HTTP {page.status_code}.", "Confirm launch domain, routing, and access rules are correct.", "medium", "availability", "WEB-STATUS-4XX")
            )
            idx += 1

        if safe_url.startswith("http://") and not str(page.url).startswith("https://"):
            findings.append(
                _finding(idx, "high", "HTTP Does Not Redirect To HTTPS", "HTTP traffic was not upgraded to HTTPS during the passive check.", "Configure a 301/308 redirect from HTTP to HTTPS.", "high", "transport_security", "WEB-HTTPS-REDIRECT")
            )
            idx += 1

        if page.redirect_chain and len(page.redirect_chain) > 3:
            findings.append(
                _finding(idx, "low", "Long Redirect Chain", "The homepage uses more than three redirects before the final page.", "Simplify redirect rules to improve reliability and reduce phishing/confusion risk.", "medium", "availability", "WEB-REDIRECT-LONG")
            )
            idx += 1

        header_map = page.headers
        metadata["headers_present"] = sorted([header for header in SECURITY_HEADERS if header in header_map])
        metadata["headers_missing"] = sorted([header for header in SECURITY_HEADERS if header not in header_map])
        cookie_evidence = _cookie_security_evidence(header_map.get("set-cookie"))
        csp_policy_analysis = _csp_analysis(header_map.get("content-security-policy", ""))
        metadata["cookie_evidence"] = cookie_evidence
        metadata["csp_policy_analysis"] = csp_policy_analysis
        metadata["raw_response_evidence"] = {
            "requested_url": safe_url,
            "final_url": page.url,
            "http_status": page.status_code,
            "response_time_ms": page.elapsed_ms,
            "redirect_count": len(page.redirect_chain),
            "redirect_chain": page.redirect_chain,
            "security_headers_present": metadata["headers_present"],
            "security_headers_missing": metadata["headers_missing"],
            "csp_value": header_map.get("content-security-policy"),
            "csp_policy_analysis": csp_policy_analysis,
            "hsts_value": header_map.get("strict-transport-security"),
            "cache_control_value": header_map.get("cache-control"),
            "set_cookie_security": cookie_evidence,
            "content_type": header_map.get("content-type"),
            "evidence_note": "Captured from passive GET/HEAD responses only. This is real observed response evidence, not an exploit or certified audit result.",
        }
        metadata["proof_based_confirmed_exposures"] = []
        metadata["proof_fetch_results"] = []
        if cookie_evidence["missing_secure"]:
            findings.append(
                _finding(idx, "medium", "Cookie Missing Secure Flag", f"Set-Cookie header contains cookie(s) without Secure: {', '.join(cookie_evidence['missing_secure'][:5])}.", "Add Secure to session/auth cookies so browsers send them only over HTTPS.", "medium", "cookie_security", "WEB-COOKIE-SECURE")
            )
            idx += 1
        if cookie_evidence["missing_http_only"]:
            findings.append(
                _finding(idx, "medium", "Cookie Missing HttpOnly Flag", f"Set-Cookie header contains cookie(s) without HttpOnly: {', '.join(cookie_evidence['missing_http_only'][:5])}.", "Add HttpOnly to session/auth cookies to reduce script access impact after XSS.", "medium", "cookie_security", "WEB-COOKIE-HTTPONLY")
            )
            idx += 1
        if cookie_evidence["missing_same_site"]:
            findings.append(
                _finding(idx, "low", "Cookie Missing SameSite Attribute", f"Set-Cookie header contains cookie(s) without SameSite: {', '.join(cookie_evidence['missing_same_site'][:5])}.", "Set SameSite=Lax or Strict for session/auth cookies unless cross-site flows require None; Secure.", "medium", "cookie_security", "WEB-COOKIE-SAMESITE")
            )
            idx += 1
        for header, (severity, title, desc, recommendation) in SECURITY_HEADERS.items():
            if header not in header_map:
                findings.append(
                    _finding(idx, severity, title, desc, recommendation, "high" if severity in {"high", "medium"} else "medium", "security_headers", f"WEB-HEADER-{header.upper()}")
                )
                idx += 1

        csp = header_map.get("content-security-policy", "")
        if csp:
            weak_tokens = ["'unsafe-inline'", "'unsafe-eval'", "*"]
            present_weak = [token for token in weak_tokens if token in csp]
            if present_weak:
                findings.append(
                    _finding(idx, "medium", "Content-Security-Policy Uses Risky Directives", f"CSP contains risky directive(s): {', '.join(present_weak)}.", "Tighten script-src/default-src and remove unsafe-inline/unsafe-eval where possible.", "medium", "security_headers", "WEB-CSP-WEAK")
                )
                idx += 1
            if not csp_policy_analysis["has_frame_ancestors"]:
                findings.append(
                    _finding(idx, "low", "CSP Missing frame-ancestors", "Content-Security-Policy is present but frame-ancestors was not detected.", "Add frame-ancestors 'none' or trusted origins to reduce clickjacking risk on login, mint, and wallet pages.", "medium", "clickjacking", "WEB-CSP-FRAME-ANCESTORS")
                )
                idx += 1
            if not csp_policy_analysis["has_object_src_none"]:
                findings.append(
                    _finding(idx, "low", "CSP Missing object-src none", "Content-Security-Policy is present but object-src 'none' was not detected.", "Add object-src 'none' unless legacy plugin/embed content is intentionally required.", "medium", "security_headers", "WEB-CSP-OBJECT-SRC")
                )
                idx += 1
            if not csp_policy_analysis["has_script_src"]:
                findings.append(
                    _finding(idx, "low", "CSP Missing script-src", "Content-Security-Policy is present but does not define script-src explicitly.", "Define script-src to restrict wallet, analytics, and dApp frontend scripts to trusted origins.", "medium", "security_headers", "WEB-CSP-SCRIPT-SRC")
                )
                idx += 1

        hsts = header_map.get("strict-transport-security", "")
        if hsts and "max-age" in hsts.lower() and "includesubdomains" not in hsts.lower():
            findings.append(
                _finding(idx, "info", "HSTS Does Not Include Subdomains", "HSTS is present, but includeSubDomains was not detected.", "After confirming all subdomains support HTTPS, consider includeSubDomains.", "low", "security_headers", "WEB-HSTS-SUBDOMAINS")
            )
            idx += 1

        cache_control = header_map.get("cache-control", "")
        if "no-store" not in cache_control.lower() and "private" not in cache_control.lower():
            findings.append(
                _finding(idx, "info", "Cache-Control Needs Review", "Sensitive wallet, admin, or session pages should not be cached incorrectly.", "Review cache policy for wallet/admin/session pages. Public marketing pages can still be cached safely.", "low", "cache_policy", "WEB-CACHE-REVIEW")
            )
            idx += 1

        content_type = header_map.get("content-type", "")
        if "text/html" in content_type or page.body_text.strip().startswith("<"):
            html_evidence = _extract_html_evidence(page.body_text, page.url)
            metadata["html_evidence"] = html_evidence
            metadata.setdefault("raw_response_evidence", {})["html_script_evidence"] = {
                "script_count": html_evidence.get("script_count", 0),
                "external_script_count": html_evidence.get("external_script_count", 0),
                "inline_script_count": html_evidence.get("inline_script_count", 0),
                "mixed_content_script_count": len(html_evidence.get("mixed_content_scripts", []) or []),
                "mixed_content_asset_count": len(html_evidence.get("mixed_content_assets", []) or []),
                "cdn_assets_missing_sri_count": len(html_evidence.get("cdn_assets_missing_sri", []) or []),
                "risky_script_hint_count": len(html_evidence.get("risky_script_hints", []) or []),
                "form_count": html_evidence.get("form_count", 0),
                "dapp_keyword_hits": html_evidence.get("dapp_keyword_hits", []),
                "evm_address_hint_count": len(html_evidence.get("evm_address_hints", []) or []),
                "evidence_note": "HTML was parsed from the fetched public homepage only. Counts are real observations; they are not proof of exploitability by themselves.",
            }
            if page.truncated:
                findings.append(
                    _finding(idx, "info", "Homepage Body Was Truncated For Safety", "The scanner stopped reading the homepage after the configured max body size.", "This is expected for large pages. Deep content review requires owner-verified scanning.", "low", "scanner_safety", "WEB-BODY-TRUNCATED")
                )
                idx += 1
            if html_evidence["external_script_count"] > settings.website_scan_external_script_warning_threshold:
                findings.append(
                    _finding(idx, "medium", "High External Script Count", f"Detected {html_evidence['external_script_count']} external scripts on the homepage.", "Reduce third-party scripts and keep only trusted analytics/wallet/CDN sources. Review supply-chain risk before launch.", "medium", "frontend_supply_chain", "WEB-SCRIPT-COUNT")
                )
                idx += 1
            if html_evidence["mixed_content_scripts"]:
                findings.append(
                    _finding(idx, "high", "Mixed Content Script Hint", "One or more scripts appear to load over http:// instead of https://.", "Serve all scripts over HTTPS and remove insecure script sources.", "medium", "frontend_supply_chain", "WEB-MIXED-SCRIPT")
                )
                idx += 1
            mixed_assets = html_evidence.get("mixed_content_assets", []) or []
            if mixed_assets:
                evidence = "; ".join(str(item.get("url")) for item in mixed_assets[:5] if isinstance(item, dict))
                findings.append(
                    _finding(idx, "high", "Mixed Content Asset Detected", f"HTTPS page references http:// asset(s): {evidence}.", "Serve images, scripts, and stylesheets over HTTPS only; remove or upgrade insecure asset URLs.", "high", "frontend_supply_chain", "WEB-MIXED-ASSET")
                )
                idx += 1
            sri_missing = html_evidence.get("cdn_assets_missing_sri", []) or []
            if sri_missing:
                evidence = "; ".join(str(item.get("url")) for item in sri_missing[:5] if isinstance(item, dict))
                findings.append(
                    _finding(idx, "medium", "Third-Party CDN Asset Missing SRI", f"CDN script/stylesheet asset(s) are missing integrity= Subresource Integrity: {evidence}.", "Add integrity and crossorigin attributes for pinned third-party CDN scripts/styles, or self-host reviewed assets.", "medium", "frontend_supply_chain", "WEB-SRI-MISSING")
                )
                idx += 1
            if html_evidence["risky_script_hints"]:
                findings.append(
                    _finding(idx, "info", "Wallet/Mint Script Review Hint", "Homepage includes script URLs containing wallet/mint/claim-related keywords. This can be normal, but should be reviewed before launch.", "Confirm scripts come from trusted domains and match the intended dApp flow. This passive scanner does not classify them as malicious.", "low", "frontend_supply_chain", "WEB-SCRIPT-HINT")
                )
                idx += 1
            if html_evidence["inline_script_count"] > 10:
                findings.append(
                    _finding(idx, "low", "High Inline Script Count", f"Detected {html_evidence['inline_script_count']} inline script blocks.", "Move scripts to bundled assets and combine with a stricter CSP where possible.", "medium", "frontend_supply_chain", "WEB-INLINE-SCRIPTS")
                )
                idx += 1
            if html_evidence["insecure_form_actions"]:
                findings.append(
                    _finding(idx, "high", "Insecure Form Action Detected", "One or more public forms submit to http:// action URLs.", "Change form actions to HTTPS endpoints and review auth/session forms before launch.", "high", "form_security", "WEB-FORM-INSECURE-ACTION")
                )
                idx += 1
            if html_evidence["external_form_actions"]:
                findings.append(
                    _finding(idx, "medium", "External Form Submission Target", "One or more forms submit to an external domain.", "Confirm external form processors are trusted, scoped, and do not collect wallet/auth secrets unexpectedly.", "medium", "form_security", "WEB-FORM-EXTERNAL-ACTION")
                )
                idx += 1
            if html_evidence["password_form_count"] and not safe_url.startswith("https://"):
                findings.append(
                    _finding(idx, "high", "Password Form On Non-HTTPS URL", "A password input was detected while the submitted URL did not start with HTTPS.", "Serve all auth pages only over HTTPS with HSTS and secure cookies.", "high", "form_security", "WEB-PASSWORD-NON-HTTPS")
                )
                idx += 1
            if html_evidence["target_blank_without_noopener"]:
                findings.append(
                    _finding(idx, "low", "External Links Missing noopener", "Links using target=_blank without rel=noopener were detected.", "Add rel=\"noopener noreferrer\" to target=_blank links, especially external links.", "medium", "frontend_supply_chain", "WEB-LINK-NOOPENER")
                )
                idx += 1
            risky_iframes = [frame for frame in html_evidence["iframes"] if frame.get("external") and not frame.get("sandbox_present")]
            if risky_iframes:
                findings.append(
                    _finding(idx, "medium", "External iframe Without Sandbox", "External iframe(s) were detected without a sandbox attribute.", "Add sandbox restrictions or remove untrusted embeds from launch/wallet pages.", "medium", "embedded_content", "WEB-IFRAME-NO-SANDBOX")
                )
                idx += 1
            if html_evidence["object_embed_count"]:
                findings.append(
                    _finding(idx, "medium", "Object/Embed Element Present", "object/embed elements were detected on the public homepage.", "Remove legacy plugin/embed content unless intentionally required and covered by CSP object-src restrictions.", "medium", "embedded_content", "WEB-OBJECT-EMBED")
                )
                idx += 1
            if html_evidence["meta_refresh"]:
                findings.append(
                    _finding(idx, "low", "Meta Refresh Redirect Present", "A meta refresh directive was detected in the homepage HTML.", "Prefer server-side redirects and review refresh targets for phishing/confusion risk.", "medium", "navigation_security", "WEB-META-REFRESH")
                )
                idx += 1
            if html_evidence["base_http"]:
                findings.append(
                    _finding(idx, "medium", "HTTP Base URL In HTML", "A base href using http:// was detected.", "Use HTTPS base URLs so relative assets/forms do not downgrade to insecure origins.", "medium", "transport_security", "WEB-BASE-HTTP")
                )
                idx += 1
            if html_evidence["noindex_tags"]:
                findings.append(
                    _finding(idx, "info", "Page Marked noindex", "A robots noindex meta tag was detected on the homepage.", "If this is a public launch page, remove noindex before launch. If intentional, document it.", "medium", "launch_readiness", "WEB-META-NOINDEX")
                )
                idx += 1
            if html_evidence["source_map_hints"]:
                findings.append(
                    _finding(idx, "info", "Source Map Hint Found In HTML", "The public HTML references source map hints.", "Confirm production source maps do not expose sensitive internal code or env-like config.", "low", "frontend_supply_chain", "WEB-SOURCEMAP-HINT")
                )
                idx += 1

            same_origin_scripts = [script for script in html_evidence.get("same_origin_scripts", []) if isinstance(script, dict)]
            script_asset_results = []
            for script in same_origin_scripts[:6]:
                src = str(script.get("src") or "")
                if not src or src.endswith(".map"):
                    continue
                js_result = await _safe_fetch(client, "GET", src, read_body=True)
                js_path = urlparse(src).path or src
                secret_proof = _proof_evidence(js_path, js_result.status_code, js_result.headers.get("content-type", ""), js_result.body_text)
                script_asset_entry = {"script": src, "status_code": js_result.status_code, "content_type": js_result.headers.get("content-type"), "proof_kind": secret_proof.get("kind") if secret_proof else None, "error": js_result.error}
                script_asset_results.append(script_asset_entry)
                if secret_proof and secret_proof.get("kind") == "public_config_secret":
                    metadata["proof_based_confirmed_exposures"].append({"path": src, **secret_proof})
                    findings.append(_proof_finding(idx, secret_proof, src))
                    idx += 1
            if script_asset_results:
                metadata.setdefault("raw_response_evidence", {})["script_asset_results"] = script_asset_results
                metadata["script_asset_results"] = script_asset_results

            source_map_results = []
            for script in same_origin_scripts[:8]:
                src = str(script.get("src") or "")
                if not src or src.endswith(".map"):
                    continue
                map_url = src + ".map"
                map_result = await _safe_fetch(client, "HEAD", map_url, read_body=False)
                source_map_entry = {"script": src, "map_url": map_url, "status_code": map_result.status_code, "error": map_result.error}
                if map_result.status_code == 200:
                    map_body = await _safe_fetch(client, "GET", map_url, read_body=True)
                    proof = _proof_evidence(urlparse(map_url).path or map_url, map_body.status_code, map_body.headers.get("content-type", ""), map_body.body_text)
                    source_map_entry["proof_kind"] = proof.get("kind") if proof else None
                    if proof:
                        metadata["proof_based_confirmed_exposures"].append({"path": map_url, **proof})
                        findings.append(_proof_finding(idx, proof, map_url))
                    else:
                        findings.append(
                            _finding(idx, "medium", "Public JavaScript Source Map Exposed", f"A same-origin source map returned HTTP 200: {map_url}", "Disable public production source maps or ensure they contain no secrets/internal implementation details.", "medium", "frontend_supply_chain", "WEB-SOURCEMAP-PUBLIC")
                        )
                    idx += 1
                source_map_results.append(source_map_entry)
            if source_map_results:
                metadata.setdefault("raw_response_evidence", {})["source_map_results"] = source_map_results
                metadata["source_map_results"] = source_map_results

        open_redirect = await _check_open_redirect(client, page.url or safe_url)
        metadata["open_redirect_probe"] = open_redirect
        metadata.setdefault("raw_response_evidence", {})["open_redirect_probe"] = open_redirect
        for redirect_finding in open_redirect.get("findings", [])[:5]:
            param = redirect_finding.get("param", "redirect")
            location = redirect_finding.get("location", OPEN_REDIRECT_TARGET)
            findings.append(
                _finding(idx, "critical", "Open Redirect Confirmed", f"Parameter '{param}' redirected to {location} with a 3xx response.", "Reject absolute external redirect targets; allow-list trusted return paths and normalize relative redirects only.", "high", "navigation_security", "WEB-OPEN-REDIRECT")
            )
            idx += 1

        caa_result = await _check_dns_caa(_host_of(page.url or safe_url))
        metadata["dns_caa"] = caa_result
        metadata.setdefault("raw_response_evidence", {})["dns_caa"] = caa_result
        if caa_result.get("state") == "Assessed" and int(caa_result.get("record_count") or 0) == 0:
            findings.append(
                _finding(idx, "low", "DNS CAA Record Missing", f"No CAA records were found for {_host_of(page.url or safe_url)}.", "Add DNS CAA records to restrict which certificate authorities can issue certificates for this domain.", "medium", "dns_tls", "WEB-DNS-CAA-MISSING")
            )
            idx += 1
        elif caa_result.get("state") != "Assessed":
            metadata.setdefault("not_assessed", []).append({"check": "DNS CAA Record", "reason": caa_result.get("reason", "CAA check unavailable")})

        for public_path in ["/robots.txt", "/sitemap.xml", "/.well-known/security.txt"]:
            path_url = urljoin(page.url, public_path)
            path_result = await _safe_fetch(client, "HEAD", path_url, read_body=False)
            status = path_result.status_code
            if public_path == "/robots.txt":
                key = "robots_status"
            elif public_path == "/sitemap.xml":
                key = "sitemap_status"
            else:
                key = "security_txt_status"
            metadata[key] = status
            if public_path == "/robots.txt" and status == 200:
                robots_body = await _safe_fetch(client, "GET", path_url, read_body=True)
                sensitive_lines = _parse_sensitive_robots_lines(robots_body.body_text)
                metadata["robots_sensitive_disallow"] = sensitive_lines
                metadata.setdefault("raw_response_evidence", {})["robots_sensitive_disallow"] = sensitive_lines
                if sensitive_lines:
                    evidence = "; ".join(f"line {item['line']}: Disallow: {item['disallow']}" for item in sensitive_lines[:6])
                    findings.append(
                        _finding(idx, "medium", "robots.txt Sensitive Path Disclosure", f"robots.txt discloses sensitive-looking paths: {evidence}.", "Remove sensitive admin/config/internal paths from robots.txt and protect them with authentication/authorization instead of obscurity.", "medium", "launch_readiness", "WEB-ROBOTS-SENSITIVE-DISALLOW")
                    )
                    idx += 1
            if status is None:
                continue
            if public_path == "/.well-known/security.txt" and status >= 400:
                findings.append(
                    _finding(idx, "info", "security.txt Not Found", f"/.well-known/security.txt returned HTTP {status} in passive check.", "Add security.txt with a safe vulnerability disclosure contact before public launch if appropriate.", "low", "launch_readiness", "WEB-SECURITYTXT-MISSING")
                )
                idx += 1
            elif status >= 400:
                findings.append(
                    _finding(idx, "info", f"{public_path} Not Found", f"{public_path} returned HTTP {status} in passive check.", "Add if useful for SEO/launch clarity. This is not always a security issue.", "low", "launch_readiness", f"WEB-{public_path.upper()}-MISSING")
                )
                idx += 1

        for path in LIMITED_PATH_HINTS:
            path_url = urljoin(page.url, path)
            path_result = await _safe_fetch(client, "HEAD", path_url, read_body=False)
            path_entry = {"path": path, "status_code": path_result.status_code, "error": path_result.error, "proof_checked": False, "proof_kind": None}
            status = path_result.status_code
            if status == 200 and path in PROOF_FETCH_PATHS:
                proof_body = await _safe_fetch(client, "GET", path_url, read_body=True)
                proof = _proof_evidence(path, proof_body.status_code, proof_body.headers.get("content-type", ""), proof_body.body_text)
                path_entry.update({
                    "proof_checked": True,
                    "content_status_code": proof_body.status_code,
                    "content_type": proof_body.headers.get("content-type"),
                    "proof_kind": proof.get("kind") if proof else None,
                })
                metadata["proof_fetch_results"].append(path_entry.copy())
                if proof:
                    metadata["proof_based_confirmed_exposures"].append({"path": path, **proof})
                    findings.append(_proof_finding(idx, proof, path))
                    idx += 1
                    metadata["limited_path_results"].append(path_entry)
                    continue

            metadata["limited_path_results"].append(path_entry)
            if status == 200:
                severity = "high" if path in DANGEROUS_PATHS else "medium"
                findings.append(
                    _finding(
                        idx,
                        severity,
                        f"Sensitive Path Hint: {path}",
                        f"Path {path} returned HTTP 200, but the safe proof check did not confirm secret/debug/schema content.",
                        "Manually confirm the route is intentionally public and does not expose secrets, configs, debug tools, or admin functionality.",
                        "medium" if severity == "high" else "low",
                        "sensitive_paths",
                        f"WEB-PATH-{path.strip('/').replace('.', '').upper() or 'ROOT'}",
                    )
                )
                idx += 1
            elif status in {401, 403} and path in DANGEROUS_PATHS:
                findings.append(
                    _finding(
                        idx,
                        "info",
                        f"Protected Sensitive Path Detected: {path}",
                        f"Path {path} returned HTTP {status}. This indicates the route is not publicly open, but it should still be reviewed for correct access control.",
                        "Keep protected routes authenticated and monitor for accidental public exposure.",
                        "low",
                        "sensitive_paths_protected",
                        f"WEB-PATH-PROTECTED-{path.strip('/').replace('.', '').upper() or 'ROOT'}",
                    )
                )
                idx += 1

    confirmed_observed = []
    potential_hardening = []
    for item in findings:
        entry = {
            "id": item.id,
            "severity": item.severity,
            "title": item.title,
            "category": item.category,
            "rule_id": item.rule_id,
            "confidence": item.confidence,
            "source": item.source,
        }
        if item.category in {"availability", "transport_security", "security_headers", "sensitive_paths", "frontend_supply_chain", "cookie_security", "form_security", "embedded_content", "clickjacking", "navigation_security"}:
            confirmed_observed.append(entry)
        else:
            potential_hardening.append(entry)

    proof_exposures = metadata.get("proof_based_confirmed_exposures", []) if isinstance(metadata.get("proof_based_confirmed_exposures"), list) else []
    metadata["finding_truth_taxonomy"] = {
        "confirmed_observed_issue_count": len(confirmed_observed),
        "potential_hardening_hint_count": len(potential_hardening),
        "confirmed_proof_exposure_count": len(proof_exposures),
        "confirmed_bug_or_exposure_count": len(proof_exposures),
        "confirmed_observed_issues": confirmed_observed[:30],
        "potential_hardening_hints": potential_hardening[:30],
        "confirmed_proof_exposures": proof_exposures[:20],
        "wording_rule": "Observed issues are real response/source observations. Proof-based bugs/exposures require a safe GET/HEAD response with content markers such as public .env, .git, source maps, debug pages, public API docs, or secret-like public config keys.",
    }
    metadata["bug_detection_coverage"] = {
        "phase": "49",
        "engine_version": "website-proof-coverage-v4.0",
        "phase79_deep_checks_enabled": True,
        "coverage_scope": [ 
            "reachability/status",
            "HTTPS/redirects",
            "security headers",
            "CSP directive quality",
            "cookie flags",
            "HTML forms",
            "external/inline/mixed scripts",
            "mixed content assets",
            "CDN Subresource Integrity",
            "open redirect probes",
            "robots.txt sensitive disallow paths",
            "DNS CAA record",
            "iframes/object embeds",
            "target=_blank noopener",
            "source-map hints",
            "robots/sitemap/security.txt",
            "limited sensitive path hints",
        ],
        "finding_count": len(findings),
        "observed_issue_count": len(confirmed_observed),
        "hardening_hint_count": len(potential_hardening),
        "confirmed_proof_exposure_count": len(proof_exposures),
        "confirmed_proof_exposures": proof_exposures[:20],
        "proof_fetch_count": len(metadata.get("proof_fetch_results", []) or []),
        "severity_breakdown": severity_breakdown(findings),
        "real_only_note": "Coverage was increased with passive proof checks only. Findings are created only from fetched headers/HTML/path status/tool output; no exploit payloads, brute force, credential testing, DoS, or fake bugs are generated.",
    }

    return _build_response(safe_url, project_name, findings, metadata)
