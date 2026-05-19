from __future__ import annotations

import json
import re
import shutil
from datetime import datetime, timezone
from typing import Any

import httpx

from app.core.config import settings
from app.services.static_analysis_tools import static_analysis_status

LAUNCH_VALIDATION_VERSION = "web3guard-launch-validation-v31.0"
SAFE_MISSING_LABELS = [
    "Assessed",
    "Not assessed yet",
    "Needs API Key",
    "Tool Not Installed",
    "Provider Not Configured",
    "Manual review required",
    "Live provider unavailable",
]

PACKAGE_NAME_RE = re.compile(r"^[A-Za-z0-9@._/:-]{1,220}$")
VERSION_CLEAN_RE = re.compile(r"^[\^~<>=\s]*")
CVE_RE = re.compile(r"CVE-\d{4}-\d{4,}", re.IGNORECASE)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _masked(value: str | None) -> str | None:
    if not value:
        return None
    if value.startswith("rzp_test_"):
        return "rzp_test_***"
    if value.startswith("rzp_live_"):
        return "rzp_live_***"
    return "configured"


def _clean_version(value: str | None) -> str | None:
    if not value:
        return None
    cleaned = VERSION_CLEAN_RE.sub("", value.strip())
    # npm ranges like "1.2.3 || 2.0.0" should not be sent as exact OSV versions.
    if any(token in cleaned for token in [" ", "||", "*", "x", "X"]):
        return None
    return cleaned or None


def _safe_package(name: str, version: str | None = None, ecosystem: str = "npm") -> dict[str, str | None]:
    safe_name = (name or "").strip()
    if not PACKAGE_NAME_RE.match(safe_name):
        raise ValueError(f"Unsafe or unsupported package name: {name!r}")
    return {"name": safe_name, "version": _clean_version(version), "ecosystem": ecosystem.strip() or "npm"}


def visible_journey() -> dict[str, Any]:
    pages = [
        {"label": "Scanner", "href": "/scanner/unified-url", "purpose": "Start the one real user journey."},
        {"label": "Results", "href": "/results", "purpose": "Explain assessed vs Not Assessed outputs."},
        {"label": "Fix Plan", "href": "/fix-plan", "purpose": "Turn issues into a prioritized launch checklist."},
        {"label": "Report", "href": "/report", "purpose": "Export and verify pre-audit evidence."},
        {"label": "Pricing", "href": "/pricing", "purpose": "Validate paid intent through real payment readiness."},
        {"label": "Dashboard", "href": "/dashboard", "purpose": "Saved scans, projects, and reports."},
        {"label": "Docs", "href": "/docs", "purpose": "Methodology, limitations, responsible use, and setup."},
    ]
    hidden_but_preserved = [
        "/engine-depth",
        "/provider-readiness",
        "/provider-live",
        "/worker-execution",
        "/trust-metrics",
        "/launch-final",
        "/agency-launch",
        "/community-review",
        "/security-passport",
        "/sentinel",
        "/continuous-monitoring",
    ]
    return {
        "ok": True,
        "version": LAUNCH_VALIDATION_VERSION,
        "visible_page_count": len(pages),
        "visible_pages": pages,
        "hidden_but_preserved": hidden_but_preserved,
        "rule": "Keep public navigation to 7 core paths; advanced modules remain searchable and linkable but not noisy in the main nav.",
    }


def slither_render_readiness() -> dict[str, Any]:
    status = static_analysis_status()
    slither = status["tools"]["slither"]
    render_build_command = "python -m pip install --upgrade pip setuptools wheel && pip install slither-analyzer && pip install -r requirements.txt"
    checks = [
        {"key": "binary_found", "passed": bool(slither["installed"]), "status": "Assessed" if slither["installed"] else "Tool Not Installed"},
        {"key": "static_analysis_enabled", "passed": bool(settings.static_analysis_enabled), "status": "Assessed" if settings.static_analysis_enabled else "Provider Not Configured"},
        {"key": "slither_enabled", "passed": bool(settings.slither_enabled), "status": "Assessed" if settings.slither_enabled else "Provider Not Configured"},
    ]
    return {
        "ok": True,
        "version": LAUNCH_VALIDATION_VERSION,
        "tool": "slither",
        "status": "Ready" if all(item["passed"] for item in checks) else "Tool Not Installed",
        "checks": checks,
        "detected_path": slither.get("path"),
        "render_build_command": render_build_command,
        "render_env_to_set": ["STATIC_ANALYSIS_ENABLED=true", "SLITHER_ENABLED=true", "AUDIT_TOOL_TIMEOUT_SECONDS=45"],
        "safety_boundaries": {
            "executes_contract_code": False,
            "collects_private_keys": False,
            "wallet_signing": False,
            "fake_findings": False,
            "certified_audit_claim": False,
        },
        "real_only_note": "Slither results are shown only when the real binary runs and output is parsed. Missing binary remains Tool Not Installed.",
    }


def razorpay_readiness() -> dict[str, Any]:
    missing = []
    if not settings.razorpay_key_id:
        missing.append("RAZORPAY_KEY_ID")
    if not settings.razorpay_key_secret:
        missing.append("RAZORPAY_KEY_SECRET")
    if not settings.razorpay_webhook_secret:
        missing.append("RAZORPAY_WEBHOOK_SECRET")

    key_id = settings.razorpay_key_id or ""
    mode = "test" if key_id.startswith("rzp_test_") else ("live" if key_id.startswith("rzp_live_") else "unknown")
    configured = bool(settings.razorpay_enabled and not missing and settings.payment_mode in {"razorpay", "razorpay_or_upi_manual"})
    return {
        "ok": True,
        "version": LAUNCH_VALIDATION_VERSION,
        "status": "Ready" if configured else "Needs API Key",
        "razorpay_enabled": bool(settings.razorpay_enabled),
        "payment_mode": settings.payment_mode,
        "key_id_masked": _masked(settings.razorpay_key_id),
        "detected_mode": mode,
        "missing_env": missing,
        "test_mode_ready": configured and mode == "test",
        "live_mode_ready": configured and mode == "live",
        "test_checklist": [
            "Use Razorpay Dashboard Test Mode keys first.",
            "Create a test order from /billing or backend payment endpoint.",
            "Verify Checkout signature on backend.",
            "Send Razorpay test webhook to the backend webhook URL.",
            "Confirm subscription/access changes only after verified webhook/signature.",
        ],
        "never_claim": [
            "Paid without verified payment event",
            "Subscription active without backend verification",
            "Refund/compliance status without real payment records",
        ],
    }


def _parse_package_json(package_json_text: str | None) -> list[dict[str, str | None]]:
    if not package_json_text:
        return []
    try:
        data = json.loads(package_json_text)
    except json.JSONDecodeError as exc:
        raise ValueError("package_json is not valid JSON") from exc
    packages: list[dict[str, str | None]] = []
    if not isinstance(data, dict):
        return packages
    for section in ["dependencies", "devDependencies", "optionalDependencies"]:
        deps = data.get(section) or {}
        if not isinstance(deps, dict):
            continue
        for name, version in deps.items():
            packages.append(_safe_package(str(name), str(version), "npm"))
    return packages


def normalize_packages(package_json_text: str | None, packages: list[dict[str, Any]] | None, limit: int) -> list[dict[str, str | None]]:
    parsed = _parse_package_json(package_json_text)
    for item in packages or []:
        name = str(item.get("name") or "").strip()
        if not name:
            continue
        parsed.append(_safe_package(name, str(item.get("version") or "") or None, str(item.get("ecosystem") or "npm")))

    deduped: list[dict[str, str | None]] = []
    seen: set[tuple[str, str | None, str | None]] = set()
    for item in parsed:
        key = (str(item["name"]).lower(), item.get("version"), str(item.get("ecosystem") or "npm").lower())
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
        if len(deduped) >= limit:
            break
    return deduped


async def _query_osv_batch(client: httpx.AsyncClient, packages: list[dict[str, str | None]]) -> list[dict[str, Any]]:
    queries = []
    for item in packages:
        query: dict[str, Any] = {"package": {"name": item["name"], "ecosystem": item.get("ecosystem") or "npm"}}
        if item.get("version"):
            query["version"] = item["version"]
        queries.append(query)
    if not queries:
        return []
    response = await client.post(f"{settings.osv_api_base.rstrip('/')}/v1/querybatch", json={"queries": queries})
    response.raise_for_status()
    data = response.json()
    results = data.get("results", []) if isinstance(data, dict) else []
    normalized: list[dict[str, Any]] = []
    for pkg, result in zip(packages, results):
        vulns = result.get("vulns", []) if isinstance(result, dict) else []
        normalized.append({
            "package": pkg,
            "vulnerability_count": len(vulns),
            "vulnerabilities": [
                {
                    "id": vuln.get("id"),
                    "summary": vuln.get("summary"),
                    "aliases": vuln.get("aliases", []),
                    "modified": vuln.get("modified"),
                }
                for vuln in vulns[: settings.launch_validation_max_vulnerabilities_per_package]
                if isinstance(vuln, dict)
            ],
        })
    return normalized


async def _fetch_cisa_kev(client: httpx.AsyncClient) -> dict[str, Any]:
    response = await client.get(settings.cisa_kev_catalog_url)
    response.raise_for_status()
    data = response.json()
    items = data.get("vulnerabilities", []) if isinstance(data, dict) else []
    mapping: dict[str, dict[str, Any]] = {}
    for item in items:
        if not isinstance(item, dict):
            continue
        cve = str(item.get("cveID") or item.get("cve") or "").upper()
        if CVE_RE.match(cve):
            mapping[cve] = {
                "cve": cve,
                "vendorProject": item.get("vendorProject"),
                "product": item.get("product"),
                "knownRansomwareCampaignUse": item.get("knownRansomwareCampaignUse"),
                "dateAdded": item.get("dateAdded"),
                "dueDate": item.get("dueDate"),
                "requiredAction": item.get("requiredAction"),
            }
    return {"count": len(mapping), "by_cve": mapping}


def _collect_cves(osv_results: list[dict[str, Any]]) -> set[str]:
    cves: set[str] = set()
    for result in osv_results:
        for vuln in result.get("vulnerabilities", []):
            candidates = [vuln.get("id"), *(vuln.get("aliases") or [])]
            for candidate in candidates:
                if not candidate:
                    continue
                for match in CVE_RE.findall(str(candidate)):
                    cves.add(match.upper())
    return cves


async def dependency_intelligence(
    *,
    package_json_text: str | None,
    packages: list[dict[str, Any]] | None,
    live_lookup: bool,
    real_only_acknowledged: bool,
    limit: int,
) -> dict[str, Any]:
    if not real_only_acknowledged:
        raise ValueError("Real-only acknowledgement is required")
    normalized = normalize_packages(package_json_text, packages, limit)
    network_enabled = bool(settings.launch_validation_network_enabled and settings.provider_live_network_enabled)
    base = {
        "ok": True,
        "version": LAUNCH_VALIDATION_VERSION,
        "package_count": len(normalized),
        "packages": normalized,
        "live_lookup_requested": bool(live_lookup),
        "network_enabled": network_enabled,
        "sources": ["OSV", "CISA KEV"],
        "real_only_note": "No fake dependency vulnerabilities are generated. Live records appear only from OSV/CISA responses.",
    }
    if not live_lookup:
        return {
            **base,
            "status": "Not assessed yet",
            "osv_results": [],
            "cisa_kev_matches": [],
            "next_step": "Set live_lookup=true after confirming package list and enabling LAUNCH_VALIDATION_NETWORK_ENABLED=true.",
        }
    if not network_enabled:
        return {
            **base,
            "status": "Provider Not Configured",
            "osv_results": [],
            "cisa_kev_matches": [],
            "next_step": "Enable LAUNCH_VALIDATION_NETWORK_ENABLED=true and PROVIDER_LIVE_NETWORK_ENABLED=true to run OSV/CISA live checks.",
        }

    timeout = httpx.Timeout(settings.launch_validation_timeout_seconds)
    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            osv_results = await _query_osv_batch(client, normalized)
            cisa_catalog = await _fetch_cisa_kev(client)
    except httpx.HTTPError as exc:
        return {
            **base,
            "status": "Live provider unavailable",
            "osv_results": [],
            "cisa_kev_matches": [],
            "error": str(exc)[:500],
            "next_step": "Retry later or keep this module Not Assessed in the report.",
        }

    cves = _collect_cves(osv_results)
    cisa_matches = [cisa_catalog["by_cve"][cve] for cve in sorted(cves) if cve in cisa_catalog["by_cve"]]
    total_vulns = sum(item["vulnerability_count"] for item in osv_results)
    return {
        **base,
        "status": "Assessed",
        "osv_results": osv_results,
        "osv_vulnerability_count": total_vulns,
        "cisa_kev_catalog_count": cisa_catalog["count"],
        "cisa_kev_matches": cisa_matches[: settings.launch_validation_max_cisa_matches],
        "priority": "High" if cisa_matches else ("Medium" if total_vulns else "Info"),
        "generated_at": _now_iso(),
    }


def launch_validation_status() -> dict[str, Any]:
    journey = visible_journey()
    slither = slither_render_readiness()
    razorpay = razorpay_readiness()
    live_gates = [
        {"key": "navigation_compressed", "passed": journey["visible_page_count"] <= 7, "status": "Assessed"},
        {"key": "slither_ready", "passed": slither["status"] == "Ready", "status": slither["status"]},
        {"key": "razorpay_ready", "passed": razorpay["status"] == "Ready", "status": razorpay["status"]},
        {"key": "osv_cisa_ready", "passed": bool(settings.launch_validation_network_enabled), "status": "Ready" if settings.launch_validation_network_enabled else "Provider Not Configured"},
    ]
    return {
        "ok": True,
        "version": LAUNCH_VALIDATION_VERSION,
        "phase": "Phase 31 — Real Launch Compression + Revenue Validation Sprint",
        "summary": "Compress the visible product journey, enable real Slither readiness, verify payment setup, and add OSV/CISA dependency intelligence without fake results.",
        "gates": live_gates,
        "passed_gates": sum(1 for gate in live_gates if gate["passed"]),
        "total_gates": len(live_gates),
        "visible_journey": journey["visible_pages"],
        "safe_missing_labels": SAFE_MISSING_LABELS,
        "not_claimed": [
            "Not a certified audit",
            "Not 100% secure",
            "No fake scanner/provider output",
            "No private key, seed phrase, mnemonic, or wallet signing",
            "No exploit automation or unauthorized active scanning",
        ],
        "next_30_days": [
            "Run and verify Slither on Render with one known Solidity sample.",
            "Activate Razorpay Test Mode and verify order/signature/webhook lifecycle.",
            "Enable OSV/CISA live dependency checks after rate-limit review.",
            "Keep only 7 visible navigation paths and move advanced pages to Docs/Advanced.",
            "Start 10-founder pilot outreach and measure conversion, not just feature count.",
        ],
    }
