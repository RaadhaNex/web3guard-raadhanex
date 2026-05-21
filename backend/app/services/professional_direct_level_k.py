from __future__ import annotations

import hashlib
import hmac
import json
import re
import secrets
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import httpx

from app.core.config import settings
from app.services.professional_monitoring_j import build_monitoring_fingerprint
from app.services.scan_contract_address import (
    fetch_contract_abi,
    fetch_contract_source,
    normalize_chain_id,
    validate_evm_address,
)

PHASE_K_NOTE = (
    "Professional Scanner Phase K consolidates the remaining direct-level foundations: "
    "safe live snapshots, GitHub/on-chain webhook ingestion, external drift evidence, "
    "and a direct-competition readiness gate. It does not perform exploit automation, wallet signing, "
    "private-key collection, unauthorized active scanning, or certified-audit claims."
)

RISKY_GITHUB_PATHS = (
    ".github/workflows/",
    "hardhat.config",
    "foundry.toml",
    "package.json",
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "requirements.txt",
    "Dockerfile",
    ".env",
    "deploy",
    "scripts/",
    "migrations/",
)

SAFE_HEADERS = {
    "content-security-policy",
    "strict-transport-security",
    "x-frame-options",
    "x-content-type-options",
    "referrer-policy",
    "permissions-policy",
    "cross-origin-opener-policy",
    "cross-origin-resource-policy",
    "cross-origin-embedder-policy",
}

SEVERITY_ORDER = {"critical": 5, "high": 4, "medium": 3, "low": 2, "info": 1}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{secrets.token_hex(10)}"


def _sha(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def _text_hash(value: str | None) -> str | None:
    if not value:
        return None
    return hashlib.sha256(value.encode("utf-8", errors="ignore")).hexdigest()


def _path(raw: str) -> Path:
    path = Path(raw)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text("", encoding="utf-8")
    return path


def _read(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            item = json.loads(line)
            if isinstance(item, dict):
                rows.append(item)
        except json.JSONDecodeError:
            continue
    return rows


def _append(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")


def _snapshots_file() -> Path:
    return _path(getattr(settings, "professional_direct_level_snapshots_file", "app/data/db/professional_direct_level_snapshots.jsonl"))


def _webhooks_file() -> Path:
    return _path(getattr(settings, "professional_webhook_events_file", "app/data/db/professional_webhook_events.jsonl"))


def _has(value: Any) -> bool:
    return bool(str(value or "").strip())


def status() -> dict[str, Any]:
    return {
        "ok": True,
        "phase": "K",
        "name": "Direct-Level Completion Foundation",
        "note": PHASE_K_NOTE,
        "network_enabled": bool(getattr(settings, "professional_direct_level_network_enabled", False)),
        "webhooks": {
            "github_webhook_secret_configured": bool(getattr(settings, "github_webhook_secret", None)),
            "onchain_webhook_secret_configured": bool(getattr(settings, "onchain_webhook_secret", None)),
            "events_file": getattr(settings, "professional_webhook_events_file", "app/data/db/professional_webhook_events.jsonl"),
        },
        "capabilities": {
            "scan_engine": True,
            "tool_verification": True,
            "benchmarking": True,
            "external_validation": True,
            "human_review_backend": True,
            "public_proof_backend": True,
            "continuous_monitoring_backend": True,
            "live_snapshot_bridge": True,
            "github_webhook_bridge": True,
            "onchain_webhook_bridge": True,
            "webhook_and_snapshot_bridge": True,
            "certified_audit_public_claim": False,
        },
        "real_only_rules": [
            "No private key, seed phrase, mnemonic, or wallet signature collection.",
            "No exploit automation or unauthorized active scanning.",
            "No fake scan score, fake tool output, or fake monitoring event.",
            "Certified audit / 100% secure / all bugs found claims are blocked.",
        ],
    }


def direct_competition_readiness_gate() -> dict[str, Any]:
    blockers: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []

    if not bool(getattr(settings, "static_analysis_enabled", False)):
        blockers.append({"area": "static_tools", "reason": "STATIC_ANALYSIS_ENABLED is false."})
    for label, flag, binary in [
        ("Slither", getattr(settings, "slither_enabled", False), getattr(settings, "slither_binary", None)),
        ("Semgrep", getattr(settings, "semgrep_enabled", False), getattr(settings, "semgrep_binary", None)),
        ("Aderyn", getattr(settings, "aderyn_enabled", False), getattr(settings, "aderyn_binary", None)),
    ]:
        if not flag:
            warnings.append({"area": label.lower(), "reason": f"{label} is not enabled. Tool findings will be Not Assessed."})
        elif not binary:
            warnings.append({"area": label.lower(), "reason": f"{label} binary path is not configured. Runtime may return Tool Not Installed."})

    if not _has(getattr(settings, "etherscan_api_key", None)):
        warnings.append({"area": "explorer", "reason": "ETHERSCAN_API_KEY is not configured. Verified source auto-fetch may be Not Assessed."})
    if not _has(getattr(settings, "github_api_token", None)):
        warnings.append({"area": "github", "reason": "GITHUB_API_TOKEN is optional but recommended for rate-limit reliability."})
    if not bool(getattr(settings, "professional_direct_level_network_enabled", False)):
        warnings.append({"area": "live_snapshots", "reason": "PROFESSIONAL_DIRECT_LEVEL_NETWORK_ENABLED is false; live snapshot endpoints will return Not Assessed for network evidence."})
    if not _has(getattr(settings, "github_webhook_secret", None)):
        warnings.append({"area": "github_webhook", "reason": "GITHUB_WEBHOOK_SECRET is not configured. Webhook verification will be unavailable."})
    if not _has(getattr(settings, "onchain_webhook_secret", None)):
        warnings.append({"area": "onchain_webhook", "reason": "ONCHAIN_WEBHOOK_SECRET is not configured. Provider webhook verification will be unavailable."})

    required_foundations = {
        "professional_finding_engine": True,
        "formal_fuzz_artifact_bridge": True,
        "public_proof_backend": True,
        "human_review_backend": True,
        "accuracy_benchmark_backend": True,
        "external_validation_backend": True,
        "continuous_monitoring_backend": True,
        "webhook_and_snapshot_bridge": True,
    }
    readiness_score = 100 - (len(blockers) * 18) - (len(warnings) * 4)
    readiness_score = max(0, min(100, readiness_score))
    direct_claim_allowed = False
    if not blockers and readiness_score >= 92:
        warnings.append({
            "area": "public_claims",
            "reason": "Direct competitor wording is still blocked until real external audited cases and human reviewer identities are published.",
        })

    return {
        "ok": True,
        "readiness_score": readiness_score,
        "gate_label": "direct_level_backend_foundation" if not blockers else "blocked_by_configuration",
        "direct_competition_public_claim_allowed": direct_claim_allowed,
        "certified_audit_public_claim_allowed": False,
        "required_foundations": required_foundations,
        "blockers": blockers,
        "warnings": warnings,
        "allowed_positioning": "AI-assisted, evidence-first Web3 Security OS with human-reviewed pre-audit workflows and continuous assurance.",
        "blocked_positioning": [
            "Certified audit replacement",
            "100% secure",
            "All vulnerabilities found",
            "CertiK/OpenZeppelin/Hacken replacement",
            "Insurance guarantee",
        ],
    }


async def _website_snapshot(url: str) -> dict[str, Any]:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return {"status": "not_assessed", "reason": "Invalid website URL."}
    timeout = httpx.Timeout(10)
    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True, max_redirects=5) as client:
            response = await client.get(url, headers={"User-Agent": "Web3GuardAI-DirectLevelSnapshot/1.0"})
        headers = {key.lower(): value for key, value in response.headers.items() if key.lower() in SAFE_HEADERS or key.lower() in {"server", "location", "set-cookie"}}
        security_headers_present = {key: key in headers for key in SAFE_HEADERS}
        return {
            "status": "assessed",
            "url": str(response.url),
            "requested_url": url,
            "http_status": response.status_code,
            "security_headers": security_headers_present,
            "headers_hash": _sha(headers)[:32],
            "body_sample_hash": hashlib.sha256(response.text[:50000].encode("utf-8", errors="ignore")).hexdigest(),
            "notes": "Passive GET request only; no active exploitation or form submission.",
        }
    except Exception as exc:
        return {"status": "not_assessed", "reason": f"Website snapshot failed: {str(exc)[:240]}"}


async def _contract_snapshot(chain: str | None, address: str | None) -> dict[str, Any]:
    if not address:
        return {"status": "not_assessed", "reason": "No contract address supplied."}
    try:
        clean_address = validate_evm_address(address)
        chain_id = normalize_chain_id(chain)
        source_record = await fetch_contract_source(clean_address, chain_id)
        abi = await fetch_contract_abi(clean_address, chain_id)
    except Exception as exc:
        return {"status": "not_assessed", "reason": str(exc)[:420]}
    source = str(source_record.get("SourceCode") or "")
    if not source.strip():
        return {
            "status": "not_assessed",
            "chain": chain,
            "chain_id": chain_id,
            "contract_address": clean_address.lower(),
            "reason": "Contract source not verified on explorer. Paste Solidity source manually for full scan.",
        }
    abi_text = json.dumps(abi or [], sort_keys=True)
    return {
        "status": "assessed",
        "chain": chain,
        "chain_id": chain_id,
        "contract_address": clean_address.lower(),
        "contract_name": source_record.get("ContractName"),
        "compiler_version": source_record.get("CompilerVersion"),
        "optimization_used": source_record.get("OptimizationUsed"),
        "implementation_address": source_record.get("Implementation") or None,
        "proxy": source_record.get("Proxy") or None,
        "abi_hash": _text_hash(abi_text),
        "source_hash": _text_hash(source),
        "source_length": len(source),
        "notes": "Explorer metadata/source snapshot only; no bytecode exploitation and no wallet signing.",
    }


def _parse_github_repo(url: str) -> tuple[str, str] | None:
    text = url.strip().rstrip("/")
    match = re.search(r"github\.com[:/](?P<owner>[A-Za-z0-9_.-]+)/(?P<repo>[A-Za-z0-9_.-]+)(?:\.git)?", text)
    if not match:
        return None
    return match.group("owner"), match.group("repo").removesuffix(".git")


async def _github_snapshot(repo_url: str | None) -> dict[str, Any]:
    if not repo_url:
        return {"status": "not_assessed", "reason": "No GitHub repo URL supplied."}
    parsed = _parse_github_repo(repo_url)
    if not parsed:
        return {"status": "not_assessed", "reason": "Invalid GitHub repo URL."}
    owner, repo = parsed
    base = getattr(settings, "github_api_base", "https://api.github.com").rstrip("/")
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "Web3GuardAI-DirectLevelGitHubSnapshot/1.0"}
    token = getattr(settings, "github_api_token", None)
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        timeout = httpx.Timeout(getattr(settings, "github_scan_timeout_seconds", 12))
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            repo_resp = await client.get(f"{base}/repos/{owner}/{repo}", headers=headers)
            if repo_resp.status_code >= 400:
                return {"status": "not_assessed", "reason": f"GitHub API returned HTTP {repo_resp.status_code}."}
            repo_data = repo_resp.json()
            branch = repo_data.get("default_branch") or "HEAD"
            tree_resp = await client.get(f"{base}/repos/{owner}/{repo}/git/trees/{branch}", params={"recursive": "1"}, headers=headers)
            if tree_resp.status_code >= 400:
                return {"status": "not_assessed", "reason": f"GitHub tree API returned HTTP {tree_resp.status_code}."}
            tree_data = tree_resp.json()
    except Exception as exc:
        return {"status": "not_assessed", "reason": f"GitHub snapshot failed: {str(exc)[:240]}"}
    tree = tree_data.get("tree") if isinstance(tree_data, dict) else []
    files = [item for item in tree if isinstance(item, dict) and item.get("type") == "blob"] if isinstance(tree, list) else []
    risky_files = []
    sol_files = 0
    dep_files = 0
    workflow_files = 0
    for item in files:
        path = str(item.get("path") or "")
        lower = path.lower()
        if lower.endswith(".sol"):
            sol_files += 1
        if any(lower.endswith(name) for name in ("package.json", "package-lock.json", "pnpm-lock.yaml", "yarn.lock", "requirements.txt")):
            dep_files += 1
        if lower.startswith(".github/workflows/"):
            workflow_files += 1
        if any(token.lower() in lower for token in RISKY_GITHUB_PATHS):
            risky_files.append({"path": path, "sha": item.get("sha"), "size": item.get("size")})
    return {
        "status": "assessed",
        "repo_url": repo_url,
        "owner": owner,
        "repo": repo,
        "default_branch": repo_data.get("default_branch"),
        "private": bool(repo_data.get("private")),
        "pushed_at": repo_data.get("pushed_at"),
        "tree_sha": tree_data.get("sha"),
        "file_counts": {"total": len(files), "solidity": sol_files, "dependencies": dep_files, "workflows": workflow_files, "risky_paths": len(risky_files)},
        "risky_files_sample": risky_files[:40],
        "repo_fingerprint": _sha({"tree_sha": tree_data.get("sha"), "risky_files": risky_files[:200], "counts": {"sol": sol_files, "dep": dep_files, "workflow": workflow_files}})[:32],
        "notes": "Read-only public GitHub metadata/tree snapshot only; no code execution.",
    }


async def build_live_snapshot(payload: Any) -> dict[str, Any]:
    data = payload.model_dump() if hasattr(payload, "model_dump") else dict(payload or {})
    if not bool(getattr(settings, "professional_direct_level_network_enabled", False)):
        return {
            "ok": True,
            "snapshot_id": _id("snap"),
            "generated_at": _now(),
            "status": "not_assessed",
            "reason": "PROFESSIONAL_DIRECT_LEVEL_NETWORK_ENABLED is false. Enable it to run live passive snapshots.",
            "not_assessed": ["website", "contract", "github"],
            "real_only_note": "No fake live snapshot was generated.",
        }
    snapshot_id = _id("snap")
    website = await _website_snapshot(data["website_url"]) if data.get("website_url") else {"status": "not_assessed", "reason": "No website URL supplied."}
    contract = await _contract_snapshot(data.get("chain"), data.get("contract_address")) if data.get("contract_address") else {"status": "not_assessed", "reason": "No contract address supplied."}
    github = await _github_snapshot(data.get("github_repo_url")) if data.get("github_repo_url") else {"status": "not_assessed", "reason": "No GitHub repo URL supplied."}
    snapshot = {
        "snapshot_id": snapshot_id,
        "user_id": data.get("user_id") or "local-demo-user",
        "project_id": data.get("project_id"),
        "project_name": data.get("project_name") or "Web3Guard monitored project",
        "generated_at": _now(),
        "authorization_confirmed": bool(data.get("authorization_confirmed", False)),
        "real_only_acknowledged": bool(data.get("real_only_acknowledged", True)),
        "website": website,
        "contract": contract,
        "github": github,
    }
    assessed = [key for key in ("website", "contract", "github") if snapshot[key].get("status") == "assessed"]
    snapshot["assessed_surfaces"] = assessed
    snapshot["not_assessed"] = {key: snapshot[key].get("reason") for key in ("website", "contract", "github") if snapshot[key].get("status") != "assessed"}
    snapshot["snapshot_hash"] = _sha({"website": website, "contract": contract, "github": github})[:40]
    snapshot["monitoring_fingerprint"] = build_monitoring_fingerprint(snapshot)
    _append(_snapshots_file(), snapshot)
    return {"ok": True, "snapshot": snapshot}


def _field_event(area: str, key: str, before: Any, after: Any, severity: str) -> dict[str, Any] | None:
    if before == after:
        return None
    return {
        "event_id": _id("drift"),
        "area": area,
        "key": key,
        "severity": severity,
        "title": f"{area.title()} drift: {key}",
        "description": f"{key} changed from {before!r} to {after!r}.",
        "before": before,
        "after": after,
        "created_at": _now(),
    }


def compare_snapshots(payload: Any) -> dict[str, Any]:
    data = payload.model_dump() if hasattr(payload, "model_dump") else dict(payload or {})
    baseline = data.get("baseline_snapshot") or {}
    current = data.get("current_snapshot") or {}
    if not isinstance(baseline, dict) or not isinstance(current, dict):
        raise ValueError("baseline_snapshot and current_snapshot must be objects.")
    events: list[dict[str, Any]] = []
    checks = [
        ("website", "headers_hash", "high"),
        ("website", "body_sample_hash", "medium"),
        ("contract", "contract_address", "critical"),
        ("contract", "source_hash", "high"),
        ("contract", "implementation_address", "critical"),
        ("contract", "abi_hash", "medium"),
        ("github", "tree_sha", "medium"),
        ("github", "repo_fingerprint", "medium"),
    ]
    for area, key, severity in checks:
        before = (baseline.get(area) or {}).get(key) if isinstance(baseline.get(area), dict) else None
        after = (current.get(area) or {}).get(key) if isinstance(current.get(area), dict) else None
        event = _field_event(area, key, before, after, severity)
        if event:
            events.append(event)
    highest = "info"
    if events:
        highest = max((event["severity"] for event in events), key=lambda item: SEVERITY_ORDER.get(item, 0))
    result = {
        "ok": True,
        "comparison_id": _id("cmp"),
        "generated_at": _now(),
        "baseline_hash": baseline.get("snapshot_hash") or _sha(baseline)[:40],
        "current_hash": current.get("snapshot_hash") or _sha(current)[:40],
        "drift_found": bool(events),
        "highest_severity": highest,
        "events": events,
        "real_only_note": "Drift is based on provided/snapshotted evidence only. No fake monitoring events are created.",
    }
    for event in events:
        _append(_webhooks_file(), {**event, "source": "snapshot_compare", "comparison_id": result["comparison_id"]})
    return result


def _verify_hmac(secret: str | None, raw_body: str, signature: str | None) -> dict[str, Any]:
    if not secret:
        return {"configured": False, "verified": False, "reason": "Webhook secret not configured."}
    if not signature:
        return {"configured": True, "verified": False, "reason": "Webhook signature missing."}
    digest = hmac.new(secret.encode("utf-8"), raw_body.encode("utf-8"), hashlib.sha256).hexdigest()
    candidates = {signature, signature.removeprefix("sha256=")}
    return {"configured": True, "verified": any(hmac.compare_digest(digest, candidate) for candidate in candidates), "signature_sha256": digest[:16]}


def ingest_github_webhook(payload: dict[str, Any], signature: str | None = None, raw_body: str | None = None) -> dict[str, Any]:
    raw = raw_body if raw_body is not None else json.dumps(payload, sort_keys=True, default=str)
    verification = _verify_hmac(getattr(settings, "github_webhook_secret", None), raw, signature)
    repo = payload.get("repository") if isinstance(payload.get("repository"), dict) else {}
    commits = payload.get("commits") if isinstance(payload.get("commits"), list) else []
    changed_files: set[str] = set()
    for commit in commits[:50]:
        if not isinstance(commit, dict):
            continue
        for key in ("added", "modified", "removed"):
            for path in commit.get(key, []) if isinstance(commit.get(key), list) else []:
                changed_files.add(str(path))
    risky = [path for path in sorted(changed_files) if any(token.lower() in path.lower() for token in RISKY_GITHUB_PATHS)]
    event = {
        "event_id": _id("gh"),
        "source": "github_webhook",
        "created_at": _now(),
        "repository": repo.get("full_name") or repo.get("html_url"),
        "ref": payload.get("ref"),
        "before": payload.get("before"),
        "after": payload.get("after"),
        "commit_count": len(commits),
        "changed_file_count": len(changed_files),
        "risky_file_count": len(risky),
        "risky_files": risky[:50],
        "severity": "high" if any(path.endswith(".sol") or "deploy" in path.lower() or ".env" in path.lower() for path in risky) else ("medium" if risky else "info"),
        "verification": verification,
        "real_only_note": "Webhook metadata only; Web3Guard did not execute repository code.",
    }
    _append(_webhooks_file(), event)
    return {"ok": True, "event": event}


def ingest_onchain_webhook(payload: dict[str, Any], signature: str | None = None, raw_body: str | None = None) -> dict[str, Any]:
    raw = raw_body if raw_body is not None else json.dumps(payload, sort_keys=True, default=str)
    verification = _verify_hmac(getattr(settings, "onchain_webhook_secret", None), raw, signature)
    event_type = str(payload.get("event_type") or payload.get("type") or payload.get("event") or "onchain_event").lower()
    critical_words = ("upgrade", "implementation", "owner", "admin", "role", "pause", "unpause", "mint", "drain")
    high_words = ("large_transfer", "treasury", "approval", "proxy")
    severity = "critical" if any(word in event_type for word in critical_words) else ("high" if any(word in event_type for word in high_words) else "medium")
    event = {
        "event_id": _id("chain"),
        "source": "onchain_webhook",
        "created_at": _now(),
        "chain": payload.get("chain") or payload.get("network"),
        "contract_address": str(payload.get("contract_address") or payload.get("address") or "").lower() or None,
        "event_type": event_type,
        "tx_hash": payload.get("tx_hash") or payload.get("transactionHash"),
        "severity": severity,
        "evidence": {key: value for key, value in payload.items() if key not in {"secret", "token", "private_key", "mnemonic"}},
        "verification": verification,
        "real_only_note": "Provider/on-chain webhook metadata only; Web3Guard did not sign transactions or move funds.",
    }
    _append(_webhooks_file(), event)
    return {"ok": True, "event": event}


def list_webhook_events(source: str | None = None, limit: int = 100) -> dict[str, Any]:
    rows = _read(_webhooks_file())
    if source:
        rows = [row for row in rows if row.get("source") == source]
    rows = rows[-limit:]
    counts = Counter(str(row.get("severity", "info")) for row in rows)
    return {"ok": True, "count": len(rows), "severity_breakdown": dict(counts), "events": list(reversed(rows))}


def remaining_roadmap() -> dict[str, Any]:
    return {
        "ok": True,
        "completed_backend_foundations": [
            "Evidence-first scanner with Not Assessed boundaries",
            "Slither/Semgrep/Aderyn tool status + normalized findings",
            "Contract deep rule expansion + rule tuning",
            "Foundry/Echidna/invariant artifact parser",
            "Public proof report backend + integrity hashes",
            "Human review/fix verification backend",
            "Benchmark/false-positive calibration backend",
            "External validation + reviewer consensus backend",
            "Continuous monitoring baseline/drift backend",
            "Live snapshot + GitHub/on-chain webhook bridge",
        ],
        "still_requires_real_world_execution": [
            "Run real scans on external audited/open-source projects with permission and store measured accuracy.",
            "Build public report UI and admin reviewer UI on top of these APIs.",
            "Onboard real named reviewers and define QA/legal sign-off process.",
            "Deploy scheduler/cron/webhook providers for continuous checks.",
            "Add isolated worker for Foundry/Echidna real execution if budget allows.",
            "Publish transparent benchmark methodology before making strong public claims.",
        ],
        "direct_competitor_strategy": "Do not claim replacement. Win by being a continuous Security OS: scan, human-review, fix-verify, publish proof, and monitor drift before and after audit.",
        "claim_gate": direct_competition_readiness_gate(),
    }

