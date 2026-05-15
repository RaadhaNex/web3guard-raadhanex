import hashlib
import html.parser
import re
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse

import httpx

from app.core.config import settings
from app.core.security import validate_public_http_url
from app.models.schemas import Finding, ModuleScore, ScanResponse
from app.services.scan_website import _safe_fetch, _headers_lower, scan_website
from app.services.scoring import priority_actions, risk_label, score_findings, severity_breakdown

WEB3_KEYWORDS = ["connect wallet", "walletconnect", "metamask", "mint", "claim", "airdrop", "swap", "stake", "approve", "permit", "bridge", "presale", "whitelist"]
POLICY_KEYWORDS = ["terms", "privacy", "refund", "scope", "disclaimer", "audit", "security"]
EVM_RE = re.compile(r"0x[a-fA-F0-9]{40}")
API_HINT_RE = re.compile(r"https?://[^\s'\"<>]+|/api/[A-Za-z0-9_./?=&:-]+")

class AdvancedHtmlParser(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.links: list[dict[str, str]] = []
        self.scripts: list[str] = []
        self.inline_scripts = 0
        self.text_chunks: list[str] = []
        self.forms: list[dict[str, str]] = []
        self.buttons: list[str] = []
        self.meta: list[dict[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr = {k.lower(): v or "" for k, v in attrs}
        tag = tag.lower()
        if tag == "a" and attr.get("href"):
            self.links.append({"href": attr.get("href", ""), "text": ""})
        elif tag == "script":
            if attr.get("src"):
                self.scripts.append(attr["src"])
            else:
                self.inline_scripts += 1
        elif tag == "form":
            self.forms.append(attr)
        elif tag == "meta":
            self.meta.append(attr)

    def handle_data(self, data: str) -> None:
        clean = " ".join(data.split())
        if clean:
            self.text_chunks.append(clean[:240])
            if len(clean) < 80:
                self.buttons.append(clean)

def _hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()

def _finding(idx: int, severity: str, title: str, description: str, recommendation: str, confidence: str = "medium", category: str = "advanced_website") -> Finding:
    return Finding(
        id=f"website-advanced-{idx}",
        module="website_advanced",
        severity=severity,
        title=title,
        description=description,
        confidence=confidence,
        source="Advanced Website Launch Intelligence Scanner",
        category=category,
        rule_id=f"WEB-ADV-{idx}",
        business_impact="Website launch-surface gaps can reduce user trust, hide wallet-flow risk, expose API surfaces, or confuse users during token/NFT/dApp launches.",
        developer_explanation=description,
        recommendation=recommendation,
        paid_review_recommended=severity in {"critical", "high"},
    )

def _domain(url: str) -> str:
    parsed = urlparse(url)
    return (parsed.hostname or "").lower()

async def run_advanced_website_scan(website_url: str, project_name: str | None = None, ownership_verified: bool = False, max_internal_pages: int = 4) -> ScanResponse:
    safe_url = validate_public_http_url(website_url)
    base_scan = await scan_website(safe_url, project_name)
    findings: list[Finding] = []
    idx = 1
    metadata: dict = {
        "requested_url": safe_url,
        "base_report_id": base_scan.report_id,
        "base_website_score": base_scan.module_score.score,
        "mode": "advanced_passive_launch_intelligence",
        "ownership_verified": ownership_verified,
        "limited_internal_pages_allowed": max_internal_pages if ownership_verified else 1,
        "deep_scan_locked_without_ownership": not ownership_verified,
        "no_exploit_payloads": True,
        "no_form_submission": True,
        "no_login_bypass": True,
        "pages_checked": [],
        "policy_pages_detected": [],
        "web3_keyword_hits": [],
        "evm_addresses": [],
        "api_hints": [],
        "external_domains": [],
        "social_links": [],
    }

    headers = {"User-Agent": settings.website_scanner_user_agent, "Accept": "text/html,*/*;q=0.8"}
    timeout = httpx.Timeout(settings.website_scan_timeout_seconds)
    async with httpx.AsyncClient(timeout=timeout, headers=headers) as client:
        page = await _safe_fetch(client, "GET", safe_url, read_body=True)
        metadata["final_url"] = page.url
        metadata["status_code"] = page.status_code
        if page.error or not page.body_text:
            findings.append(_finding(idx, "medium", "Advanced Homepage Intelligence Not Available", f"Homepage HTML was not available for advanced passive analysis: {page.error or 'empty body' }.", "Fix website availability and rerun the advanced URL scan. Base passive headers are still reported separately.")); idx += 1
        else:
            parser = AdvancedHtmlParser()
            try:
                parser.feed(page.body_text[: settings.website_scan_max_body_bytes])
            except Exception:
                pass
            lowered = page.body_text.lower()
            base_host = _domain(page.url or safe_url)
            external_domains = sorted({_domain(urljoin(page.url, src)) for src in parser.scripts if _domain(urljoin(page.url, src)) and _domain(urljoin(page.url, src)) != base_host})
            keywords = sorted({kw for kw in WEB3_KEYWORDS if kw in lowered})
            evm_addresses = sorted(set(EVM_RE.findall(page.body_text)))[:30]
            api_hints = sorted(set(API_HINT_RE.findall(page.body_text)))[:30]
            policy_links = []
            social_links = []
            for link in parser.links[:300]:
                href = urljoin(page.url, link["href"])
                low_href = href.lower()
                if any(word in low_href for word in POLICY_KEYWORDS):
                    policy_links.append(href)
                if any(domain in low_href for domain in ["twitter.com", "x.com", "discord", "telegram", "github.com", "medium.com", "mirror.xyz"]):
                    social_links.append(href)
            metadata.update({
                "pages_checked": [{"url": page.url, "status_code": page.status_code}],
                "web3_keyword_hits": keywords,
                "evm_addresses": evm_addresses,
                "api_hints": api_hints,
                "external_domains": external_domains[:40],
                "policy_pages_detected": sorted(set(policy_links))[:20],
                "social_links": sorted(set(social_links))[:20],
                "forms_count": len(parser.forms),
                "inline_script_count": parser.inline_scripts,
                "script_count": len(parser.scripts),
            })
            if keywords and not evm_addresses:
                findings.append(_finding(idx, "medium", "dApp Launch Page Without Visible Contract Address Evidence", "The page appears to describe Web3 actions, but no EVM contract address was visible in the fetched homepage HTML.", "Show verified contract address, chain, and explorer link near mint/claim/swap/approve actions where appropriate.")); idx += 1
            if len(external_domains) >= settings.advanced_website_external_domain_warning_threshold:
                findings.append(_finding(idx, "medium", "High External Script/Domain Dependency Count", f"Detected {len(external_domains)} external script domains on the launch page.", "Reduce third-party script dependencies and document trusted domains in CSP. Review all external scripts before launch.")); idx += 1
            if parser.inline_scripts >= settings.advanced_website_inline_script_warning_threshold:
                findings.append(_finding(idx, "low", "Large Inline Script Surface", f"Detected {parser.inline_scripts} inline script blocks.", "Move inline JavaScript to reviewed bundles where possible and enforce CSP nonces/hashes.")); idx += 1
            missing_policy = []
            for word in ["terms", "privacy", "refund", "disclaimer"]:
                if not any(word in link.lower() for link in policy_links):
                    missing_policy.append(word)
            if missing_policy:
                findings.append(_finding(idx, "low", "Launch Trust Policy Links Missing Or Not Obvious", f"Missing obvious links for: {', '.join(missing_policy)}.", "Add clear Terms, Privacy, Refund/Scope, and security disclaimer links before paid token/NFT launch.")); idx += 1
            if "approve" in keywords and "spender" not in lowered:
                findings.append(_finding(idx, "medium", "Approval UX May Need Spender Explanation", "The page mentions approve/approval but the fetched copy did not clearly mention spender details.", "Show spender address, allowance amount, token, chain, and revoke guidance before users sign approvals.")); idx += 1
            if any(word in keywords for word in ["mint", "claim", "airdrop", "presale"]) and "audit" not in lowered and "security" not in lowered:
                findings.append(_finding(idx, "info", "Security/Readiness Statement Not Found", "The launch page includes Web3 action keywords but no obvious security/readiness statement was visible.", "Add a transparent pre-audit/readiness disclaimer, contract links, and known limitations. Do not claim certified audit unless true.")); idx += 1

            if ownership_verified:
                internal_links = []
                for link in parser.links[:100]:
                    href = urljoin(page.url, link["href"])
                    if _domain(href) == base_host and href.startswith(("http://", "https://")):
                        internal_links.append(href)
                for link in sorted(set(internal_links))[: max(0, max_internal_pages - 1)]:
                    try:
                        sub = await _safe_fetch(client, "GET", link, read_body=True, max_redirects=3)
                        metadata["pages_checked"].append({"url": sub.url, "status_code": sub.status_code})
                    except Exception:
                        continue

    score = score_findings(findings)
    return ScanResponse(
        report_id=f"W3G-WEBADV-{_hash(safe_url)[:12]}",
        generated_at=datetime.now(timezone.utc),
        project_name=project_name,
        module_score=ModuleScore(module="website_advanced", score=score, risk_label=risk_label(score)),
        findings=findings,
        severity_breakdown=severity_breakdown(findings),
        priority_actions=priority_actions(findings),
        input_hash=_hash(safe_url)[:16],
        engine_version="web3guard-advanced-website-engine-v3.0",
        scan_metadata=metadata,
    )


def advanced_website_status() -> dict:
    return {
        "engine": "web3guard-advanced-website-engine-v3.0",
        "status": "live_safe_passive",
        "real_only": True,
        "checks": ["homepage HTML intelligence", "policy/social/API hints", "Web3 keyword detection", "visible EVM address hints", "external script/domain inventory"],
        "locked_without_ownership": ["deeper crawl", "authenticated pages", "form submission", "active probing"],
    }
