"""
OSV.dev dependency vulnerability checker.

Free public API — no key required.
https://osv.dev/docs/

Real-only rule: failures return provider_error/not assessed metadata; this module
never invents vulnerabilities when OSV is unavailable or package input is invalid.
"""

from __future__ import annotations

import json
import re
from typing import Any

import httpx

OSV_API = "https://api.osv.dev/v1/query"
TIMEOUT_SECONDS = 8
MAX_DEPS_PER_REQUEST = 25


def _clean_version(version: str | None) -> str | None:
    if not version:
        return None
    candidate = str(version).strip()
    candidate = re.sub(r"^[\^~><=\s]+", "", candidate)
    candidate = candidate.split("||", 1)[0].strip()
    candidate = candidate.split(" ", 1)[0].strip()
    return candidate if re.match(r"^\d+(?:\.\d+){0,3}(?:[-+][0-9A-Za-z_.-]+)?$", candidate) else None


def _osv_severity(vuln: dict[str, Any]) -> str:
    for sev in vuln.get("severity", []) or []:
        score = str(sev.get("score", "")).upper()
        if "CRITICAL" in score:
            return "critical"
        if "HIGH" in score:
            return "high"
        if "MEDIUM" in score:
            return "medium"
        if "LOW" in score:
            return "low"
    database_specific = vuln.get("database_specific") or {}
    severity = str(database_specific.get("severity", "")).upper()
    if severity in {"CRITICAL", "HIGH", "MEDIUM", "LOW"}:
        return severity.lower()
    return "low"


async def check_package_osv(ecosystem: str, name: str, version: str | None = None) -> dict[str, Any]:
    """Check one package against OSV.

    ecosystem examples: npm, PyPI, Go, Maven.
    """
    package_name = name.strip()
    package_ecosystem = ecosystem.strip()
    if not package_name or not package_ecosystem:
        return {
            "vulnerable": False,
            "vuln_count": 0,
            "vulns": [],
            "error": "Package ecosystem and name are required.",
            "status": "not_assessed",
        }

    payload: dict[str, Any] = {"package": {"name": package_name, "ecosystem": package_ecosystem}}
    clean_version = _clean_version(version)
    if clean_version:
        payload["version"] = clean_version

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
            response = await client.post(OSV_API, json=payload)
        if response.status_code != 200:
            return {
                "vulnerable": False,
                "vuln_count": 0,
                "vulns": [],
                "error": f"OSV API returned HTTP {response.status_code}",
                "status": "provider_error",
            }
        data = response.json()
    except Exception as exc:  # pragma: no cover - network-dependent guard
        return {
            "vulnerable": False,
            "vuln_count": 0,
            "vulns": [],
            "error": str(exc),
            "status": "provider_error",
        }

    vulns = data.get("vulns", []) or []
    normalized = []
    for vuln in vulns[:10]:
        vuln_id = vuln.get("id")
        normalized.append(
            {
                "id": vuln_id,
                "summary": vuln.get("summary", ""),
                "severity": _osv_severity(vuln),
                "url": f"https://osv.dev/vulnerability/{vuln_id}" if vuln_id else None,
            }
        )

    return {
        "vulnerable": bool(vulns),
        "vuln_count": len(vulns),
        "vulns": normalized,
        "error": None,
        "status": "assessed",
        "source": "osv.dev",
        "package": {"ecosystem": package_ecosystem, "name": package_name, "version": clean_version},
    }


def _extract_package_json_dependencies(package_json_text: str) -> tuple[dict[str, str], str | None]:
    try:
        package_json = json.loads(package_json_text)
    except Exception:
        return {}, "Invalid package.json"

    deps: dict[str, str] = {}
    for section in ("dependencies", "devDependencies", "peerDependencies", "optionalDependencies"):
        values = package_json.get(section) or {}
        if isinstance(values, dict):
            for name, version in values.items():
                if isinstance(name, str):
                    deps[name] = str(version)
    return deps, None


async def check_package_json_deps(package_json_text: str) -> dict[str, Any]:
    """Parse package.json text and check npm dependencies against OSV."""
    deps, error = _extract_package_json_dependencies(package_json_text)
    if error:
        return {"error": error, "status": "not_assessed", "results": [], "total_checked": 0}

    results = []
    checked = 0
    for name, version in list(deps.items())[:MAX_DEPS_PER_REQUEST]:
        checked += 1
        result = await check_package_osv("npm", name, version)
        if result.get("vulnerable"):
            results.append(
                {
                    "package": name,
                    "version": version,
                    "vuln_count": result.get("vuln_count", 0),
                    "top_vuln": (result.get("vulns") or [None])[0],
                    "vulns": result.get("vulns", []),
                }
            )

    return {
        "status": "assessed" if checked else "not_assessed",
        "total_dependencies_found": len(deps),
        "total_checked": checked,
        "vulnerable_count": len(results),
        "results": results,
        "source": "osv.dev",
        "disclaimer": "OSV.dev public vulnerability database. This is dependency intelligence, not a complete audit.",
    }
