from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from typing import Any

import httpx

from app.core.config import settings
from app.models.schemas import Finding, ModuleScore, ScanResponse
from app.services.scan_contract import scan_solidity
from app.services.static_analysis_tools import run_static_analysis
from app.services.scoring import priority_actions, risk_label, score_findings, severity_breakdown
from app.services.finding_normalizer import audit_grade_summary, prepare_professional_findings

EVM_ADDRESS_RE = re.compile(r"^0x[a-fA-F0-9]{40}$")
ROLE_FUNCTION_RE = re.compile(r"(?i)(owner\(|getOwner\(|hasRole\(|DEFAULT_ADMIN_ROLE|grantRole\(|revokeRole\(|MINTER_ROLE|PAUSER_ROLE|UPGRADER_ROLE)")
PROXY_WORD_RE = re.compile(r"(?i)(proxy|implementation|upgradeTo|upgradeToAndCall|transparent|uups|beacon)")

CHAIN_ID_MAP: dict[str, str] = {
    "ethereum": "1",
    "eth": "1",
    "mainnet": "1",
    "sepolia": "11155111",
    "holesky": "17000",
    "bsc": "56",
    "bnb": "56",
    "bnb smart chain": "56",
    "bsc testnet": "97",
    "polygon": "137",
    "matic": "137",
    "polygon mumbai": "80001",
    "polygon amoy": "80002",
    "arbitrum": "42161",
    "arbitrum one": "42161",
    "arbitrum sepolia": "421614",
    "optimism": "10",
    "optimism sepolia": "11155420",
    "base": "8453",
    "base sepolia": "84532",
    "avalanche": "43114",
    "avax": "43114",
    "avalanche fuji": "43113",
}

SUPPORTED_CHAINS = [
    {"key": "ethereum", "label": "Ethereum Mainnet", "chain_id": "1"},
    {"key": "sepolia", "label": "Ethereum Sepolia", "chain_id": "11155111"},
    {"key": "bsc", "label": "BNB Smart Chain", "chain_id": "56"},
    {"key": "polygon", "label": "Polygon PoS", "chain_id": "137"},
    {"key": "arbitrum", "label": "Arbitrum One", "chain_id": "42161"},
    {"key": "optimism", "label": "Optimism", "chain_id": "10"},
    {"key": "base", "label": "Base", "chain_id": "8453"},
    {"key": "avalanche", "label": "Avalanche C-Chain", "chain_id": "43114"},
]

LEGACY_EXPLORER_BY_CHAIN_ID: dict[str, tuple[str, str, str]] = {
    "1": ("https://api.etherscan.io/api", "ETHERSCAN_API_KEY", "etherscan_api_key"),
    "56": ("https://api.bscscan.com/api", "BSCSCAN_API_KEY", "bscscan_api_key"),
    "137": ("https://api.polygonscan.com/api", "POLYGONSCAN_API_KEY", "polygonscan_api_key"),
    "42161": ("https://api.arbiscan.io/api", "ARBISCAN_API_KEY", "arbiscan_api_key"),
    "10": ("https://api-optimistic.etherscan.io/api", "OPTIMISMSCAN_API_KEY", "optimismscan_api_key"),
    "8453": ("https://api.basescan.org/api", "BASESCAN_API_KEY", "basescan_api_key"),
}


def _explorer_credentials(chain_id: str) -> dict[str, Any]:
    """Return a safe explorer API config.

    Etherscan API V2 is preferred because it supports multi-chain scans with one
    ETHERSCAN_API_KEY + chainid parameter. Chain-specific keys/endpoints remain
    supported as a fallback for deployments that still use legacy explorer keys.
    """
    if settings.etherscan_api_key:
        return {
            "api_base": settings.etherscan_v2_api_base,
            "api_key": settings.etherscan_api_key,
            "env_key": "ETHERSCAN_API_KEY",
            "mode": "etherscan_v2_chainid",
            "chainid_param": chain_id,
        }
    legacy = LEGACY_EXPLORER_BY_CHAIN_ID.get(chain_id)
    if legacy:
        api_base, env_key, attr = legacy
        api_key = getattr(settings, attr, None)
        if api_key:
            return {
                "api_base": api_base,
                "api_key": api_key,
                "env_key": env_key,
                "mode": "legacy_chain_specific_explorer",
                "chainid_param": None,
            }
        raise ValueError(f"Chain API key not configured. Set ETHERSCAN_API_KEY or {env_key}. Paste Solidity source manually.")
    raise ValueError("Chain API key not configured for this chain. Paste Solidity source manually.")



def _now() -> datetime:
    return datetime.now(timezone.utc)


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _new_report_id(chain_id: str, address: str) -> str:
    return f"W3G-ADDR-{chain_id}-{address[-6:].upper()}-{_now().strftime('%Y%m%d%H%M%S')}"


def normalize_chain_id(chain: str | None) -> str:
    value = (chain or "ethereum").strip().lower()
    if value.isdigit():
        return value
    if value in CHAIN_ID_MAP:
        return CHAIN_ID_MAP[value]
    raise ValueError(f"Unsupported chain '{chain}'. Use a supported EVM chain key or numeric chain id.")


def validate_evm_address(address: str) -> str:
    candidate = address.strip()
    if not EVM_ADDRESS_RE.match(candidate):
        raise ValueError("Contract address must be a valid EVM address like 0x followed by 40 hex characters.")
    return candidate


def explorer_status() -> dict[str, Any]:
    return {
        "ok": True,
        "version": "1.0",
        "mode": "verified_source_fetch",
        "etherscan_v2_enabled": bool(settings.etherscan_api_key),
        "legacy_chain_keys_configured": {
            "polygon": bool(settings.polygonscan_api_key),
            "bsc": bool(settings.bscscan_api_key),
            "arbitrum": bool(settings.arbiscan_api_key),
            "optimism": bool(settings.optimismscan_api_key),
            "base": bool(settings.basescan_api_key),
        },
        "api_base": settings.etherscan_v2_api_base,
        "supported_chains": SUPPORTED_CHAINS,
        "limits": {
            "timeout_seconds": settings.explorer_scan_timeout_seconds,
            "max_source_chars": settings.max_explorer_source_chars,
            "max_contract_address_scan_per_hour": settings.max_contract_address_scan_per_hour,
        },
        "real_only_note": "A contract address only becomes a real code scan when verified source is fetched from the explorer API. Unverified contracts are marked as not source-scanned.",
        "not_enabled_or_not_claimed": [
            "No private key collection",
            "No transaction signing",
            "No wallet connection",
            "No bytecode decompilation yet",
            "Slither/Semgrep/Aderyn run only when STATIC_ANALYSIS_ENABLED=true and binaries are installed",
            "No certified audit wording",
        ],
    }


def _finding(
    *,
    idx: int,
    severity: str,
    title: str,
    description: str,
    category: str,
    rule_id: str,
    confidence: str,
    source: str,
    business_impact: str,
    developer_explanation: str,
    recommendation: str,
    line: int | None = None,
    snippet: str | None = None,
    paid: bool = False,
) -> Finding:
    return Finding(
        id=f"addr-{idx:03d}-{_hash(title + description)[:8]}",
        module="contract",
        severity=severity,  # type: ignore[arg-type]
        title=title,
        description=description,
        affected_line=line,
        affected_function=None,
        affected_code=snippet,
        evidence=snippet or description[:420],
        impact=business_impact,
        fix=recommendation,
        source_tools=["explorer" if "Explorer" in source else "web3guard_local_rules"],
        repro_steps=["Open the verified explorer source/ABI metadata and confirm the cited evidence."],
        verification_status="rule_detected_needs_triage",
        confidence=confidence,  # type: ignore[arg-type]
        source=source,
        category=category,
        rule_id=rule_id,
        fingerprint=_hash(f"addr|{rule_id}|{title}|{line}|{snippet or ''}")[:20],
        business_impact=business_impact,
        developer_explanation=developer_explanation,
        recommendation=recommendation,
        references=[],
        paid_review_recommended=paid,
    )


async def _etherscan_call(params: dict[str, str], chain_id: str) -> dict[str, Any]:
    credentials = _explorer_credentials(chain_id)
    query = {**params, "apikey": credentials["api_key"]}
    if credentials.get("chainid_param"):
        query["chainid"] = str(credentials["chainid_param"])
    timeout = httpx.Timeout(settings.explorer_scan_timeout_seconds)
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        response = await client.get(credentials["api_base"], params=query, headers={"User-Agent": "Web3GuardAI-RAADHANEX-ExplorerScanner/13.0"})
    if response.status_code >= 400:
        raise ValueError(f"Explorer API returned HTTP {response.status_code}.")
    data = response.json()
    if str(data.get("status")) == "0" and not data.get("result"):
        raise ValueError(str(data.get("message") or "Explorer API returned an error."))
    data.setdefault("_web3guard_explorer", {"mode": credentials["mode"], "env_key": credentials["env_key"], "api_base": credentials["api_base"]})
    return data


async def fetch_contract_source(address: str, chain_id: str) -> dict[str, Any]:
    data = await _etherscan_call({"module": "contract", "action": "getsourcecode", "address": address}, chain_id)
    result = data.get("result")
    if not isinstance(result, list) or not result:
        raise ValueError("Explorer API did not return a contract source result.")
    record = result[0]
    if not isinstance(record, dict):
        raise ValueError("Explorer API returned an unsupported source response.")
    return record


async def fetch_contract_abi(address: str, chain_id: str) -> list[dict[str, Any]] | None:
    try:
        data = await _etherscan_call({"module": "contract", "action": "getabi", "address": address}, chain_id)
        result = data.get("result")
        if isinstance(result, str) and result and result not in {"Contract source code not verified", "Max rate limit reached"}:
            parsed = json.loads(result)
            if isinstance(parsed, list):
                return parsed
    except Exception:
        return None
    return None


def _extract_standard_json(source_code: str) -> str | None:
    candidate = source_code.strip()
    if candidate.startswith("{{") and candidate.endswith("}}"):
        candidate = candidate[1:-1]
    if not candidate.startswith("{"):
        return None
    try:
        data = json.loads(candidate)
    except json.JSONDecodeError:
        return None
    sources = data.get("sources") if isinstance(data, dict) else None
    if not isinstance(sources, dict):
        return None
    chunks: list[str] = []
    for path, item in sources.items():
        content = item.get("content") if isinstance(item, dict) else None
        if isinstance(content, str):
            chunks.append(f"// File: {path}\n{content}")
    return "\n\n".join(chunks) if chunks else None


def extract_source_text(record: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    raw = str(record.get("SourceCode") or "")
    if not raw.strip():
        return "", {"format": "unverified_or_empty", "files_detected": 0}
    extracted = _extract_standard_json(raw)
    if extracted:
        source = extracted
        fmt = "standard_json"
        files = source.count("// File:")
    else:
        source = raw
        fmt = "single_or_flattened"
        files = 1
    if len(source) > settings.max_explorer_source_chars:
        source = source[: settings.max_explorer_source_chars]
        truncated = True
    else:
        truncated = False
    return source, {"format": fmt, "files_detected": files, "truncated": truncated, "source_chars": len(source)}


def _abi_summary(abi: list[dict[str, Any]] | None) -> dict[str, Any]:
    if not abi:
        return {"available": False, "functions": [], "events": [], "admin_like_functions": []}
    functions = [item.get("name") for item in abi if item.get("type") == "function" and item.get("name")]
    events = [item.get("name") for item in abi if item.get("type") == "event" and item.get("name")]
    admin_like = [name for name in functions if ROLE_FUNCTION_RE.search(str(name)) or str(name).lower() in {"mint", "burn", "pause", "unpause", "blacklist", "setfee", "settax", "upgradeTo".lower()}]
    return {
        "available": True,
        "function_count": len(functions),
        "event_count": len(events),
        "functions": functions[:80],
        "events": events[:40],
        "admin_like_functions": admin_like[:40],
    }


def _metadata_findings(record: dict[str, Any], abi_summary: dict[str, Any], source_text: str) -> list[Finding]:
    findings: list[Finding] = []
    idx = 1
    proxy = str(record.get("Proxy") or "0") == "1"
    implementation = str(record.get("Implementation") or "").strip()
    compiler = str(record.get("CompilerVersion") or "")
    optimization = str(record.get("OptimizationUsed") or "")
    license_type = str(record.get("LicenseType") or "")

    if proxy or implementation or PROXY_WORD_RE.search(source_text):
        findings.append(_finding(
            idx=idx,
            severity="medium",
            title="Proxy / Upgradeability Surface Detected",
            description="Explorer metadata/source indicates proxy or upgradeability-related behavior. Upgrade admin and implementation controls need manual review.",
            category="upgradeability",
            rule_id="ADDR_PROXY_METADATA",
            confidence="high" if proxy or implementation else "medium",
            source="Explorer Metadata + Rule Engine",
            business_impact="A compromised or centralized upgrade admin can change project logic after launch.",
            developer_explanation="Review proxy admin, implementation address, initializer protection, and storage layout before launch.",
            recommendation="Document proxy admin, use multisig/timelock where appropriate, verify implementation, and run upgrade safety review.",
            snippet=f"Proxy={record.get('Proxy')} Implementation={implementation or 'not provided'}",
            paid=True,
        ))
        idx += 1

    if abi_summary.get("admin_like_functions"):
        findings.append(_finding(
            idx=idx,
            severity="info",
            title="Admin-Like ABI Functions Detected",
            description="The verified ABI exposes functions that look like owner/role/admin/mint/pause/upgrade controls.",
            category="centralization",
            rule_id="ADDR_ABI_ADMIN_SURFACE",
            confidence="medium",
            source="Explorer ABI Analysis",
            business_impact="Admin powers may be legitimate, but users/investors should understand who controls them.",
            developer_explanation="ABI names are heuristic; confirm modifiers, role assignments, and multisig/timelock setup manually.",
            recommendation="Generate a founder transparency/permission map and disclose owner/minter/pauser/upgrader powers.",
            snippet=", ".join(abi_summary.get("admin_like_functions", [])[:20]),
            paid=False,
        ))
        idx += 1

    if compiler.startswith("v0.4") or compiler.startswith("v0.5") or compiler.startswith("v0.6"):
        findings.append(_finding(
            idx=idx,
            severity="medium",
            title="Older Solidity Compiler Version",
            description=f"Explorer reports compiler version {compiler}. Older compilers may require additional compatibility and known-risk review.",
            category="compiler",
            rule_id="ADDR_OLD_COMPILER",
            confidence="high",
            source="Explorer Metadata",
            business_impact="Older compiler behavior can increase review cost and may signal legacy code risk.",
            developer_explanation="Confirm known compiler bugs, optimizer behavior, and library compatibility for this exact version.",
            recommendation="Document why this compiler is used and run manual/tool-assisted review before launch.",
            snippet=compiler,
            paid=False,
        ))
        idx += 1

    if optimization in {"0", "False", "false"}:
        findings.append(_finding(
            idx=idx,
            severity="info",
            title="Compiler Optimization Disabled",
            description="Explorer metadata says optimization was not used. This is not always unsafe, but it can affect gas efficiency and bytecode comparison expectations.",
            category="gas",
            rule_id="ADDR_OPTIMIZATION_OFF",
            confidence="medium",
            source="Explorer Metadata",
            business_impact="Users may pay higher gas, and deployment settings should be documented in the report.",
            developer_explanation="Review optimizer settings in deployment scripts and verify the deployed source matches expected settings.",
            recommendation="Document optimizer settings and add gas review if launch volume will be high.",
            snippet=f"OptimizationUsed={optimization}",
        ))
        idx += 1

    if not license_type or license_type in {"None", "Unknown"}:
        findings.append(_finding(
            idx=idx,
            severity="info",
            title="License Metadata Missing or Unknown",
            description="Explorer metadata does not clearly identify the source license.",
            category="transparency",
            rule_id="ADDR_LICENSE_UNKNOWN",
            confidence="medium",
            source="Explorer Metadata",
            business_impact="Missing license metadata can reduce transparency for users, investors, and reviewers.",
            developer_explanation="Check SPDX identifiers and explorer license metadata.",
            recommendation="Add SPDX identifiers and verify explorer metadata where possible.",
            snippet=f"LicenseType={license_type or 'not provided'}",
        ))

    return findings


async def scan_contract_address(address: str, chain: str | None = None, project_name: str | None = None) -> ScanResponse:
    normalized_address = validate_evm_address(address)
    chain_id = normalize_chain_id(chain)
    record = await fetch_contract_source(normalized_address, chain_id)
    source_text, source_meta = extract_source_text(record)
    abi = None
    if record.get("ABI") and isinstance(record.get("ABI"), str):
        try:
            abi = json.loads(str(record.get("ABI")))
        except Exception:
            abi = None
    if abi is None:
        abi = await fetch_contract_abi(normalized_address, chain_id)
    abi_meta = _abi_summary(abi)

    if not source_text.strip():
        finding = _finding(
            idx=1,
            severity="high",
            title="Contract Source Not Verified On Explorer",
            description="The explorer did not return verified Solidity source for this address, so Web3Guard AI cannot run a real code scan from address input.",
            category="transparency",
            rule_id="ADDR_UNVERIFIED_SOURCE",
            confidence="high",
            source="Explorer Metadata",
            business_impact="Users and reviewers cannot independently inspect the deployed contract source through the explorer.",
            developer_explanation="Verify source code on the chain explorer or paste source manually for rule-engine review.",
            recommendation="Verify the contract source on explorer, then re-run this scanner. Do not publish a fake code score.",
            paid=True,
        )
        findings = prepare_professional_findings([finding], default_source_tool="explorer")
        score = score_findings(findings)
        return ScanResponse(
            report_id=_new_report_id(chain_id, normalized_address),
            generated_at=_now(),
            project_name=project_name,
            module_score=ModuleScore(module="contract", score=score, risk_label=risk_label(score), assessed=True),
            findings=findings,
            severity_breakdown=severity_breakdown(findings),
            priority_actions=priority_actions(findings),
            input_hash=_hash(f"{chain_id}:{normalized_address}"),
            engine_version="web3guard-contract-address-engine-v13.0",
            scan_metadata={
                "address": normalized_address,
                "chain_id": chain_id,
                "source_verified": False,
                "not_assessed": [{"module": "contract_static_tools", "reason": "Contract source not verified on Etherscan-compatible explorer. Paste Solidity source manually for full scan."}],
                "explorer_record": {k: record.get(k) for k in ["ContractName", "CompilerVersion", "Proxy", "Implementation"]},
                "abi_summary": abi_meta,
                "safety_controls": {"private_key_collection": False, "wallet_connection": False, "transaction_signing": False, "bytecode_decompilation": False},
                "audit_grade_finding_summary": audit_grade_summary(findings),
            },
        )

    contract_type = str(record.get("ContractName") or "Verified Contract")
    contract_name = str(record.get("ContractName") or normalized_address)
    rule_report = scan_solidity(source_text, project_name=project_name or contract_name, contract_type=contract_type)
    metadata_findings = _metadata_findings(record, abi_meta, source_text)
    tool_report = None
    tool_error: str | None = None
    try:
        tool_report = run_static_analysis(
            source_text,
            project_name=project_name or contract_name,
            file_name=f"{contract_name}.sol",
            requested_tools=["slither", "semgrep", "aderyn"],
        )
    except Exception as exc:
        tool_error = str(exc)[:500]
    tool_findings = tool_report.findings if tool_report else []
    findings = prepare_professional_findings(rule_report.findings + metadata_findings + tool_findings, default_source_tool="explorer_address_scan")
    real_findings = [f for f in findings if f.category != "tool_status"]
    score = score_findings(real_findings) if real_findings else 98
    metadata = {
        **(rule_report.scan_metadata or {}),
        "address": normalized_address,
        "chain_id": chain_id,
        "source_verified": True,
        "source_metadata": source_meta,
        "explorer_record": {
            "contract_name": record.get("ContractName"),
            "compiler_version": record.get("CompilerVersion"),
            "optimization_used": record.get("OptimizationUsed"),
            "runs": record.get("Runs"),
            "license_type": record.get("LicenseType"),
            "proxy": record.get("Proxy"),
            "implementation": record.get("Implementation"),
            "constructor_arguments_present": bool(str(record.get("ConstructorArguments") or "").strip()),
            "evm_version": record.get("EVMVersion"),
        },
        "abi_summary": abi_meta,
        "static_analysis_tools": (tool_report.scan_metadata if tool_report else {"state": "Tool Not Installed / Provider Not Configured / Not Assessed", "error": tool_error}),
        "audit_grade_finding_summary": audit_grade_summary(findings, tool_runs=(tool_report.scan_metadata or {}).get("tool_runs", {}) if tool_report else {}),
        "safety_controls": {
            "verified_source_fetch": True,
            "private_key_collection": False,
            "wallet_connection": False,
            "transaction_signing": False,
            "bytecode_decompilation": False,
            "slither_semgrep_aderyn_auto_attempt": True,
            "slither_semgrep_aderyn_requires_worker_config": True,
        },
    }
    return ScanResponse(
        report_id=_new_report_id(chain_id, normalized_address),
        generated_at=_now(),
        project_name=project_name or str(record.get("ContractName") or normalized_address),
        module_score=ModuleScore(module="contract", score=score, risk_label=risk_label(score), assessed=True),
        findings=findings,
        severity_breakdown=severity_breakdown([f for f in findings if f.category != "tool_status"]),
        priority_actions=priority_actions([f for f in findings if f.category != "tool_status"]),
        input_hash=_hash(f"{chain_id}:{normalized_address}:{source_text[:5000]}"),
        engine_version="web3guard-contract-address-engine-v13.0",
        scan_metadata=metadata,
    )
