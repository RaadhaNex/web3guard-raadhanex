from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone
from typing import Any

import httpx

from app.core.config import settings
from app.services.scan_contract_address import (
    SUPPORTED_CHAINS,
    extract_source_text,
    fetch_contract_abi,
    fetch_contract_source,
    normalize_chain_id,
    validate_evm_address,
)
from app.services.scan_github_repo import parse_github_repo_url
from app.services.wallet_risk_integrations import CHAIN_IDS

PROVIDER_LIVE_VERSION = "web3guard-provider-live-integrations-v28.0"
SAFE_MISSING_LABELS = {"Tool Not Installed", "Provider Not Configured", "Needs API Key", "Manual", "Not Assessed"}
CVE_RE = re.compile(r"^CVE-\d{4}-\d{4,}$", re.IGNORECASE)
PACKAGE_RE = re.compile(r"^[A-Za-z0-9_.@/:-]{1,220}$")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _masked(value: str | None) -> str | None:
    if not value:
        return None
    if len(value) <= 8:
        return "configured"
    return f"{value[:4]}...{value[-4:]}"


def _provider_enabled_status(*, enabled: bool, configured: bool = True, needs_key: bool = False) -> str:
    if not settings.provider_live_enabled:
        return "Provider Not Configured"
    if not enabled:
        return "Provider Not Configured"
    if needs_key and not configured:
        return "Needs API Key"
    return "Ready" if configured else "Provider Not Configured"


def _trim_text(value: str | None, limit: int = 5000) -> str | None:
    if value is None:
        return None
    if len(value) <= limit:
        return value
    return value[:limit] + "\n...<trimmed>"


def _safe_error(exc: Exception) -> str:
    message = str(exc).strip()
    if not message:
        return exc.__class__.__name__
    # Keep provider errors usable but avoid dumping huge upstream bodies.
    return message[:500]


def _network_blocked_response(source: str) -> dict[str, Any]:
    return {
        "ok": True,
        "version": PROVIDER_LIVE_VERSION,
        "source": source,
        "status": "Not Assessed",
        "records": [],
        "reason": "Provider live network calls are disabled by PROVIDER_LIVE_NETWORK_ENABLED=false.",
        "real_only_note": "No fallback or fake provider data was generated.",
    }


def provider_live_status() -> dict[str, Any]:
    advisory_enabled = bool(settings.provider_live_advisory_sources_enabled)
    github_token_configured = bool(settings.github_api_token)
    surfaces = [
        {
            "key": "explorer_verified_source",
            "name": "Etherscan V2-compatible verified source fetch",
            "status": _provider_enabled_status(enabled=True, configured=bool(settings.etherscan_api_key), needs_key=True),
            "configured": bool(settings.etherscan_api_key),
            "masked_credential": _masked(settings.etherscan_api_key),
            "api_base": settings.etherscan_v2_api_base,
            "backend_endpoint": "/provider-live/explorer/source",
            "reuses_existing_scanner": "/scan/contract-address",
            "supported_chains": SUPPORTED_CHAINS,
            "when_missing": "Needs API Key",
            "not_claimed": [
                "No bytecode decompilation",
                "No certified audit score",
                "No private key collection",
                "No wallet signing",
            ],
        },
        {
            "key": "goplus_live_risk",
            "name": "GoPlus token / wallet / approval risk provider",
            "status": _provider_enabled_status(enabled=bool(settings.goplus_enabled), configured=True),
            "configured": bool(settings.goplus_enabled),
            "masked_credential": _masked(settings.goplus_access_token),
            "api_base": settings.goplus_api_base,
            "backend_endpoint": "/provider-live/goplus/status",
            "reuses_existing_scanner": "/scan/wallet-risk",
            "supported_chains": CHAIN_IDS,
            "when_missing": "Provider Not Configured",
            "not_claimed": [
                "No wallet connect",
                "No transaction signing",
                "No automatic revoke transaction",
                "No seed phrase or mnemonic collection",
            ],
        },
        {
            "key": "github_public_repo_live",
            "name": "GitHub public repository provider",
            "status": _provider_enabled_status(enabled=True, configured=True),
            "configured": True,
            "masked_credential": _masked(settings.github_api_token),
            "api_base": settings.github_api_base,
            "backend_endpoint": "/provider-live/github/repo-check",
            "reuses_existing_scanner": "/scan/github",
            "token_configured": github_token_configured,
            "token_note": "Token is optional for public repos but recommended for rate limits and authorized private access.",
            "when_missing": "Not Assessed",
            "not_claimed": [
                "No repo clone",
                "No dependency install",
                "No private repo access without authorization",
                "No code execution",
            ],
        },
        {
            "key": "advisory_live_sources",
            "name": "OSV / NVD / GitHub Advisory / CISA KEV source ingestion",
            "status": "Ready" if advisory_enabled else "Provider Not Configured",
            "configured": advisory_enabled,
            "backend_endpoint": "/provider-live/advisory/search",
            "when_missing": "Provider Not Configured",
            "source_matrix": advisory_source_matrix(),
            "not_claimed": [
                "No automatic disclosure claim",
                "No 'discovered by Web3Guard' claim",
                "No vulnerability record mutation",
                "No fake public metrics",
            ],
        },
    ]
    ready_count = sum(1 for item in surfaces if item["status"] == "Ready")
    return {
        "ok": True,
        "version": PROVIDER_LIVE_VERSION,
        "provider_live_enabled": settings.provider_live_enabled,
        "network_enabled": settings.provider_live_network_enabled,
        "ready_count": ready_count,
        "total_count": len(surfaces),
        "readiness_label": "Provider live layer partially ready" if ready_count < len(surfaces) else "Provider live layer ready",
        "surfaces": surfaces,
        "limits": {
            "timeout_seconds": settings.provider_live_timeout_seconds,
            "max_records": settings.provider_live_max_records,
            "max_query_chars": settings.provider_live_max_query_chars,
        },
        "safe_env_to_add": [
            "ETHERSCAN_API_KEY for verified contract source fetching.",
            "GOPLUS_ENABLED=true after accepting provider terms for token/wallet risk checks.",
            "GITHUB_API_TOKEN for higher GitHub rate limits or authorized access.",
            "PROVIDER_LIVE_ADVISORY_SOURCES_ENABLED=true only after source/rate-limit review.",
            "NVD_API_KEY is optional but recommended for NVD rate limits.",
        ],
        "safety_boundaries": {
            "no_fake_provider_data": True,
            "no_fake_monitoring": True,
            "no_private_key_collection": True,
            "no_seed_phrase_collection": True,
            "no_wallet_signing": True,
            "no_exploit_automation": True,
            "not_certified_audit": True,
        },
    }


def advisory_source_matrix() -> list[dict[str, Any]]:
    enabled = bool(settings.provider_live_advisory_sources_enabled and settings.provider_live_enabled)
    return [
        {
            "key": "osv",
            "name": "OSV vulnerability database",
            "status": "Ready" if enabled else "Provider Not Configured",
            "api_base": settings.osv_api_base,
            "requires_api_key": False,
            "supported_query_types": ["package", "ecosystem"],
        },
        {
            "key": "nvd",
            "name": "NVD CVE API",
            "status": "Ready" if enabled else "Provider Not Configured",
            "api_base": settings.nvd_api_base,
            "requires_api_key": False,
            "api_key_configured": bool(settings.nvd_api_key),
            "supported_query_types": ["cve", "keyword"],
        },
        {
            "key": "github_advisory",
            "name": "GitHub Security Advisory API",
            "status": "Ready" if enabled and bool(settings.github_api_token) else ("Needs API Key" if enabled else "Provider Not Configured"),
            "api_base": settings.github_advisory_api_base,
            "requires_api_key": True,
            "api_key_configured": bool(settings.github_api_token),
            "supported_query_types": ["cve", "ecosystem", "package"],
        },
        {
            "key": "cisa_kev",
            "name": "CISA Known Exploited Vulnerabilities catalog",
            "status": "Ready" if enabled else "Provider Not Configured",
            "api_base": settings.cisa_kev_catalog_url,
            "requires_api_key": False,
            "supported_query_types": ["cve", "keyword"],
        },
    ]


async def explorer_source_snapshot(chain: str, address: str, *, include_abi: bool = False) -> dict[str, Any]:
    chain_id = normalize_chain_id(chain)
    valid_address = validate_evm_address(address)
    if not settings.provider_live_enabled:
        return {
            "ok": True,
            "version": PROVIDER_LIVE_VERSION,
            "status": "Provider Not Configured",
            "source_available": False,
            "chain_id": chain_id,
            "address": valid_address,
            "reason": "PROVIDER_LIVE_ENABLED=false.",
            "real_only_note": "No fake verified source was generated.",
        }
    if not settings.provider_live_network_enabled:
        response = _network_blocked_response("explorer_verified_source")
        response.update({"chain_id": chain_id, "address": valid_address, "source_available": False})
        return response
    if not settings.etherscan_api_key:
        return {
            "ok": True,
            "version": PROVIDER_LIVE_VERSION,
            "status": "Needs API Key",
            "source_available": False,
            "chain_id": chain_id,
            "address": valid_address,
            "api_base": settings.etherscan_v2_api_base,
            "reason": "ETHERSCAN_API_KEY is missing. Verified source cannot be fetched.",
            "real_only_note": "No fallback source, fake source, or fake scan result was generated.",
        }
    try:
        record = await fetch_contract_source(valid_address, chain_id)
        source_text, source_meta = extract_source_text(record)
        abi = await fetch_contract_abi(valid_address, chain_id) if include_abi else None
        status = "Ready" if source_text.strip() else "Not Assessed"
        return {
            "ok": True,
            "version": PROVIDER_LIVE_VERSION,
            "status": status,
            "chain_id": chain_id,
            "address": valid_address,
            "source_available": bool(source_text.strip()),
            "source_hash": _hash(source_text)[:24] if source_text.strip() else None,
            "contract_name": record.get("ContractName"),
            "compiler_version": record.get("CompilerVersion"),
            "license_type": record.get("LicenseType"),
            "proxy": str(record.get("Proxy") or "0") == "1",
            "implementation": record.get("Implementation") or None,
            "source_metadata": source_meta,
            "abi_available": bool(abi),
            "abi_function_count": sum(1 for item in abi or [] if item.get("type") == "function"),
            "source_preview": _trim_text(source_text, limit=1800),
            "fetched_at": _now_iso(),
            "real_only_note": "This is upstream explorer data. Treat it as evidence input, not a certified audit.",
        }
    except Exception as exc:
        return {
            "ok": True,
            "version": PROVIDER_LIVE_VERSION,
            "status": "Not Assessed",
            "chain_id": chain_id,
            "address": valid_address,
            "source_available": False,
            "provider_error": _safe_error(exc),
            "real_only_note": "Provider request failed; no fake source or fake scan result was generated.",
        }


async def github_repo_live_check(repo_url: str, branch: str | None = None) -> dict[str, Any]:
    parsed = parse_github_repo_url(repo_url)
    owner = str(parsed["owner"])
    repo = str(parsed["repo"])
    requested_branch = branch or parsed.get("branch_from_url")
    if not settings.provider_live_enabled:
        return {"ok": True, "version": PROVIDER_LIVE_VERSION, "status": "Provider Not Configured", "repo": {"owner": owner, "name": repo}, "real_only_note": "No fake GitHub metadata generated."}
    if not settings.provider_live_network_enabled:
        response = _network_blocked_response("github_public_repo")
        response.update({"repo": {"owner": owner, "name": repo}})
        return response
    api_base = settings.github_api_base.rstrip("/")
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "Web3GuardAI-RAADHANEX-ProviderLive/28.0 (read-only)",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if settings.github_api_token:
        headers["Authorization"] = f"Bearer {settings.github_api_token}"
    timeout = httpx.Timeout(settings.provider_live_timeout_seconds)
    try:
        async with httpx.AsyncClient(timeout=timeout, headers=headers, follow_redirects=True) as client:
            repo_resp = await client.get(f"{api_base}/repos/{owner}/{repo}")
            if repo_resp.status_code == 404:
                return {"ok": True, "version": PROVIDER_LIVE_VERSION, "status": "Not Assessed", "repo": {"owner": owner, "name": repo}, "provider_error": "GitHub repository was not found or is not accessible.", "real_only_note": "No fake repository metadata generated."}
            if repo_resp.status_code == 403:
                return {"ok": True, "version": PROVIDER_LIVE_VERSION, "status": "Needs API Key", "repo": {"owner": owner, "name": repo}, "provider_error": "GitHub API rate limit or access policy blocked the request.", "real_only_note": "Add GITHUB_API_TOKEN or retry later. No fake metadata generated."}
            repo_resp.raise_for_status()
            repo_meta = repo_resp.json()
            default_branch = str(repo_meta.get("default_branch") or "main")
            effective_branch = str(requested_branch or default_branch)
            contents_resp = await client.get(f"{api_base}/repos/{owner}/{repo}/contents", params={"ref": effective_branch})
            root_files: list[str] = []
            if contents_resp.status_code < 400:
                contents = contents_resp.json()
                if isinstance(contents, list):
                    root_files = [str(item.get("name")) for item in contents if item.get("name")]
        return {
            "ok": True,
            "version": PROVIDER_LIVE_VERSION,
            "status": "Ready",
            "repo": {
                "owner": owner,
                "name": repo,
                "url": f"https://github.com/{owner}/{repo}",
                "default_branch": default_branch,
                "checked_branch": effective_branch,
                "private": bool(repo_meta.get("private")),
                "archived": bool(repo_meta.get("archived")),
                "fork": bool(repo_meta.get("fork")),
                "pushed_at": repo_meta.get("pushed_at"),
                "open_issues_count": repo_meta.get("open_issues_count"),
            },
            "root_file_hints": root_files[:40],
            "security_hints": {
                "has_security_md_root": any(name.lower() == "security.md" for name in root_files),
                "has_package_json_root": "package.json" in root_files,
                "has_foundry_config_root": "foundry.toml" in root_files,
                "has_hardhat_config_root": any(name in {"hardhat.config.ts", "hardhat.config.js"} for name in root_files),
            },
            "token_configured": bool(settings.github_api_token),
            "fetched_at": _now_iso(),
            "real_only_note": "Read-only GitHub API metadata. For deeper evidence run /scan/github with owner authorization.",
        }
    except Exception as exc:
        return {
            "ok": True,
            "version": PROVIDER_LIVE_VERSION,
            "status": "Not Assessed",
            "repo": {"owner": owner, "name": repo},
            "provider_error": _safe_error(exc),
            "real_only_note": "GitHub provider request failed; no fake metadata generated.",
        }


def goplus_live_status() -> dict[str, Any]:
    return {
        "ok": True,
        "version": PROVIDER_LIVE_VERSION,
        "status": "Ready" if settings.goplus_enabled else "Provider Not Configured",
        "provider": "goplus",
        "enabled": bool(settings.goplus_enabled),
        "api_base": settings.goplus_api_base,
        "access_token_configured": bool(settings.goplus_access_token),
        "masked_credential": _masked(settings.goplus_access_token),
        "supported_local_chain_aliases": CHAIN_IDS,
        "live_scan_endpoint": "/scan/wallet-risk",
        "real_only_note": "External wallet/token risk data is fetched only when GOPLUS_ENABLED=true and scan input is provided.",
        "safety_boundaries": {
            "no_wallet_connect": True,
            "no_private_key_collection": True,
            "no_seed_phrase_collection": True,
            "no_transaction_signing": True,
        },
    }


def _validate_advisory_query(source: str, query: str | None, ecosystem: str | None, package_name: str | None) -> tuple[str, str | None, str | None, str | None]:
    clean_source = source.strip().lower()
    if clean_source not in {"osv", "nvd", "github_advisory", "cisa_kev"}:
        raise ValueError("Unsupported advisory source. Use osv, nvd, github_advisory, or cisa_kev.")
    clean_query = (query or "").strip()[: settings.provider_live_max_query_chars]
    clean_ecosystem = (ecosystem or "").strip()[:80] or None
    clean_package = (package_name or "").strip()[: settings.provider_live_max_query_chars] or None
    if clean_query and not (CVE_RE.match(clean_query) or PACKAGE_RE.match(clean_query)):
        raise ValueError("Query contains unsupported characters. Use a CVE ID, package name, or simple keyword.")
    if clean_package and not PACKAGE_RE.match(clean_package):
        raise ValueError("Package name contains unsupported characters.")
    return clean_source, clean_query or None, clean_ecosystem, clean_package


def _advisory_disabled(source: str) -> dict[str, Any]:
    return {
        "ok": True,
        "version": PROVIDER_LIVE_VERSION,
        "source": source,
        "status": "Provider Not Configured",
        "records": [],
        "reason": "PROVIDER_LIVE_ADVISORY_SOURCES_ENABLED=false. Enable only after source terms/rate-limit review.",
        "real_only_note": "No fake advisory records were generated.",
    }


async def advisory_live_search(source: str, query: str | None = None, ecosystem: str | None = None, package_name: str | None = None) -> dict[str, Any]:
    clean_source, clean_query, clean_ecosystem, clean_package = _validate_advisory_query(source, query, ecosystem, package_name)
    if not settings.provider_live_enabled:
        return {"ok": True, "version": PROVIDER_LIVE_VERSION, "source": clean_source, "status": "Provider Not Configured", "records": [], "real_only_note": "Provider live layer is disabled. No fake advisories generated."}
    if not settings.provider_live_advisory_sources_enabled:
        return _advisory_disabled(clean_source)
    if not settings.provider_live_network_enabled:
        return _network_blocked_response(clean_source)
    if clean_source == "github_advisory" and not settings.github_api_token:
        return {
            "ok": True,
            "version": PROVIDER_LIVE_VERSION,
            "source": clean_source,
            "status": "Needs API Key",
            "records": [],
            "reason": "GITHUB_API_TOKEN is required for GitHub Security Advisory API access.",
            "real_only_note": "No fake advisory records were generated.",
        }
    timeout = httpx.Timeout(settings.provider_live_timeout_seconds)
    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            if clean_source == "osv":
                records = await _search_osv(client, clean_query, clean_ecosystem, clean_package)
            elif clean_source == "nvd":
                records = await _search_nvd(client, clean_query)
            elif clean_source == "github_advisory":
                records = await _search_github_advisory(client, clean_query, clean_ecosystem, clean_package)
            else:
                records = await _search_cisa_kev(client, clean_query)
        return {
            "ok": True,
            "version": PROVIDER_LIVE_VERSION,
            "source": clean_source,
            "status": "Ready",
            "records": records[: settings.provider_live_max_records],
            "record_count": min(len(records), settings.provider_live_max_records),
            "query": {"query": clean_query, "ecosystem": clean_ecosystem, "package_name": clean_package},
            "fetched_at": _now_iso(),
            "real_only_note": "Records are returned only from the selected upstream source. No fake advisories or Web3Guard discovery claims.",
        }
    except Exception as exc:
        return {
            "ok": True,
            "version": PROVIDER_LIVE_VERSION,
            "source": clean_source,
            "status": "Not Assessed",
            "records": [],
            "provider_error": _safe_error(exc),
            "real_only_note": "Provider request failed; no fake advisory records were generated.",
        }


async def _search_osv(client: httpx.AsyncClient, query: str | None, ecosystem: str | None, package_name: str | None) -> list[dict[str, Any]]:
    base = settings.osv_api_base.rstrip("/")
    if package_name:
        payload: dict[str, Any] = {"package": {"name": package_name}}
        if ecosystem:
            payload["package"]["ecosystem"] = ecosystem
        resp = await client.post(f"{base}/v1/query", json=payload, headers={"User-Agent": "Web3GuardAI-RAADHANEX-ProviderLive/28.0"})
        resp.raise_for_status()
        vulns = resp.json().get("vulns") or []
        return [_normalize_osv(item) for item in vulns if isinstance(item, dict)]
    if query and CVE_RE.match(query):
        resp = await client.get(f"{base}/v1/vulns/{query.upper()}", headers={"User-Agent": "Web3GuardAI-RAADHANEX-ProviderLive/28.0"})
        if resp.status_code == 404:
            return []
        resp.raise_for_status()
        return [_normalize_osv(resp.json())]
    raise ValueError("OSV search requires package_name or a CVE query.")


def _normalize_osv(item: dict[str, Any]) -> dict[str, Any]:
    affected = item.get("affected") if isinstance(item.get("affected"), list) else []
    aliases = item.get("aliases") if isinstance(item.get("aliases"), list) else []
    return {
        "id": item.get("id"),
        "aliases": aliases[:10],
        "summary": item.get("summary") or item.get("details"),
        "modified": item.get("modified"),
        "published": item.get("published"),
        "affected_packages": [entry.get("package", {}).get("name") for entry in affected[:10] if isinstance(entry, dict)],
        "source": "osv",
    }


async def _search_nvd(client: httpx.AsyncClient, query: str | None) -> list[dict[str, Any]]:
    if not query:
        raise ValueError("NVD search requires a CVE ID or keyword query.")
    headers = {"User-Agent": "Web3GuardAI-RAADHANEX-ProviderLive/28.0"}
    if settings.nvd_api_key:
        headers["apiKey"] = settings.nvd_api_key
    params: dict[str, str] = {"resultsPerPage": str(min(settings.provider_live_max_records, 50))}
    if CVE_RE.match(query):
        params["cveId"] = query.upper()
    else:
        params["keywordSearch"] = query
    resp = await client.get(settings.nvd_api_base, params=params, headers=headers)
    resp.raise_for_status()
    vulns = resp.json().get("vulnerabilities") or []
    normalized = []
    for wrapper in vulns:
        cve = wrapper.get("cve") if isinstance(wrapper, dict) else None
        if isinstance(cve, dict):
            descriptions = cve.get("descriptions") if isinstance(cve.get("descriptions"), list) else []
            summary = next((item.get("value") for item in descriptions if item.get("lang") == "en"), None)
            metrics = cve.get("metrics") if isinstance(cve.get("metrics"), dict) else {}
            normalized.append({
                "id": cve.get("id"),
                "summary": summary,
                "published": cve.get("published"),
                "last_modified": cve.get("lastModified"),
                "metrics_keys": list(metrics.keys())[:8],
                "source": "nvd",
            })
    return normalized


async def _search_github_advisory(client: httpx.AsyncClient, query: str | None, ecosystem: str | None, package_name: str | None) -> list[dict[str, Any]]:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "Web3GuardAI-RAADHANEX-ProviderLive/28.0",
        "X-GitHub-Api-Version": "2022-11-28",
        "Authorization": f"Bearer {settings.github_api_token}",
    }
    params: dict[str, str] = {"per_page": str(min(settings.provider_live_max_records, 100))}
    if query and CVE_RE.match(query):
        params["cve_id"] = query.upper()
    elif query:
        params["query"] = query
    if ecosystem:
        params["ecosystem"] = ecosystem
    if package_name:
        params["affects"] = package_name
    resp = await client.get(f"{settings.github_advisory_api_base.rstrip('/')}/advisories", params=params, headers=headers)
    resp.raise_for_status()
    data = resp.json()
    records = []
    for item in data if isinstance(data, list) else []:
        records.append({
            "id": item.get("ghsa_id") or item.get("cve_id"),
            "cve_id": item.get("cve_id"),
            "summary": item.get("summary"),
            "severity": item.get("severity"),
            "published_at": item.get("published_at"),
            "updated_at": item.get("updated_at"),
            "source": "github_advisory",
        })
    return records


async def _search_cisa_kev(client: httpx.AsyncClient, query: str | None) -> list[dict[str, Any]]:
    resp = await client.get(settings.cisa_kev_catalog_url, headers={"User-Agent": "Web3GuardAI-RAADHANEX-ProviderLive/28.0"})
    resp.raise_for_status()
    data = resp.json()
    vulns = data.get("vulnerabilities") if isinstance(data, dict) else []
    results = []
    query_lower = (query or "").lower()
    for item in vulns if isinstance(vulns, list) else []:
        if not isinstance(item, dict):
            continue
        haystack = " ".join(str(item.get(key) or "") for key in ["cveID", "vendorProject", "product", "vulnerabilityName", "shortDescription"]).lower()
        if query_lower and query_lower not in haystack:
            continue
        results.append({
            "id": item.get("cveID"),
            "vendor_project": item.get("vendorProject"),
            "product": item.get("product"),
            "vulnerability_name": item.get("vulnerabilityName"),
            "date_added": item.get("dateAdded"),
            "due_date": item.get("dueDate"),
            "known_ransomware_campaign_use": item.get("knownRansomwareCampaignUse"),
            "source": "cisa_kev",
        })
        if len(results) >= settings.provider_live_max_records:
            break
    return results
