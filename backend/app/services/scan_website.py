import hashlib
import html.parser
import time
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse

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

LIMITED_PATH_HINTS = ["/.env", "/admin", "/api", "/swagger", "/graphql", "/.git", "/backup", "/config", "/debug"]
DANGEROUS_PATHS = {"/.env", "/.git", "/backup", "/config", "/debug"}
SCRIPT_RISK_KEYWORDS = ["eval", "drainer", "walletconnect", "metamask", "claim", "mint"]
DAPP_PAGE_KEYWORDS = ["walletconnect", "metamask", "connect wallet", "mint", "claim", "airdrop", "swap", "stake", "approve", "permit", "bridge", "presale"]
EVM_ADDRESS_HINT_RE = re.compile(r"0x[a-fA-F0-9]{40}")


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
            else:
                self.inline_script_count += 1
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


def _extract_html_evidence(html: str, final_url: str) -> dict:
    parser = ScriptParser()
    try:
        parser.feed(html[: settings.website_scan_max_body_bytes])
    except Exception:
        pass

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
            source_map_results = []
            for script in same_origin_scripts[:8]:
                src = str(script.get("src") or "")
                if not src or src.endswith(".map"):
                    continue
                map_url = src + ".map"
                map_result = await _safe_fetch(client, "HEAD", map_url, read_body=False)
                source_map_results.append({"script": src, "map_url": map_url, "status_code": map_result.status_code, "error": map_result.error})
                if map_result.status_code == 200:
                    findings.append(
                        _finding(idx, "medium", "Public JavaScript Source Map Exposed", f"A same-origin source map returned HTTP 200: {map_url}", "Disable public production source maps or ensure they contain no secrets/internal implementation details.", "medium", "frontend_supply_chain", "WEB-SOURCEMAP-PUBLIC")
                    )
                    idx += 1
            if source_map_results:
                metadata.setdefault("raw_response_evidence", {})["source_map_results"] = source_map_results
                metadata["source_map_results"] = source_map_results

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
            metadata["limited_path_results"].append({"path": path, "status_code": path_result.status_code, "error": path_result.error})
            status = path_result.status_code
            if status in {200, 401, 403}:
                severity = "high" if path in DANGEROUS_PATHS and status == 200 else "medium"
                findings.append(
                    _finding(
                        idx,
                        severity,
                        f"Sensitive Path Hint: {path}",
                        f"Path {path} returned HTTP {status}. This passive hint may be normal for protected routes, but public exposure should be reviewed.",
                        "Confirm the route does not expose secrets, configs, debug tools, or admin functionality. Deep checks require ownership verification.",
                        "medium" if severity == "high" else "low",
                        "sensitive_paths",
                        f"WEB-PATH-{path.strip('/').replace('.', '').upper() or 'ROOT'}",
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

    metadata["finding_truth_taxonomy"] = {
        "confirmed_observed_issue_count": len(confirmed_observed),
        "potential_hardening_hint_count": len(potential_hardening),
        "confirmed_observed_issues": confirmed_observed[:30],
        "potential_hardening_hints": potential_hardening[:30],
        "wording_rule": "Observed issues are real response/source observations. They are not automatically confirmed exploitable bugs unless the evidence proves exposure, exploitability, and impact.",
    }
    metadata["bug_detection_coverage"] = {
        "phase": "48",
        "engine_version": "website-coverage-v3.0",
        "coverage_scope": [
            "reachability/status",
            "HTTPS/redirects",
            "security headers",
            "CSP directive quality",
            "cookie flags",
            "HTML forms",
            "external/inline/mixed scripts",
            "iframes/object embeds",
            "target=_blank noopener",
            "source-map hints",
            "robots/sitemap/security.txt",
            "limited sensitive path hints",
        ],
        "finding_count": len(findings),
        "observed_issue_count": len(confirmed_observed),
        "hardening_hint_count": len(potential_hardening),
        "severity_breakdown": severity_breakdown(findings),
        "real_only_note": "Coverage was increased with passive evidence only. Findings are created only from fetched headers/HTML/path status/tool output; no exploit payloads or fake bugs are generated.",
    }

    return _build_response(safe_url, project_name, findings, metadata)
