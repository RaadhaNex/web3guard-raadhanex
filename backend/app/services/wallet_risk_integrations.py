import hashlib
import re
from datetime import datetime, timezone
from typing import Any

import httpx

from app.core.config import settings
from app.models.schemas import Finding, ModuleScore, ScanResponse
from app.services.scoring import priority_actions, risk_label, score_findings, severity_breakdown

EVM_RE = re.compile(r"^0x[a-fA-F0-9]{40}$")
CHAIN_IDS = {"ethereum": "1", "bsc": "56", "polygon": "137", "arbitrum": "42161", "avalanche": "43114", "base": "8453", "optimism": "10"}


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()

def _finding(idx: int, severity: str, title: str, description: str, recommendation: str, confidence: str = "medium", category: str = "wallet_api") -> Finding:
    return Finding(
        id=f"wallet-risk-{idx}",
        module="wallet_risk",
        severity=severity,
        title=title,
        description=description,
        confidence=confidence,
        source="Wallet Risk API Integration Layer",
        category=category,
        rule_id=f"WALLET-RISK-{idx}",
        business_impact="Wallet/token/approval risk checks help founders avoid unsafe signing flows and explain user-facing risk before launch.",
        developer_explanation=description,
        recommendation=recommendation,
        paid_review_recommended=severity in {"critical", "high"},
    )



def _parse_goplus_address(data: dict[str, Any]) -> list[tuple[str, str, str]]:
    result = data.get("result") or {}
    if not isinstance(result, dict):
        return []
    risks: list[tuple[str, str, str]] = []
    checks = {
        "malicious_address": "Address flagged as malicious",
        "is_malicious": "Address flagged as malicious",
        "blacklist_doubt": "Address has blacklist doubt signal",
        "honeypot_related_address": "Address related to honeypot activity",
        "phishing_activities": "Phishing activity signal",
        "fake_kyc": "Fake KYC signal",
        "cybercrime": "Cybercrime signal",
        "stealing_attack": "Stealing attack signal",
        "blackmail_activities": "Blackmail activity signal",
        "darkweb_transactions": "Darkweb transaction signal",
        "money_laundering": "Money laundering signal",
        "financial_crime": "Financial crime signal",
    }
    for key, title in checks.items():
        value = str(result.get(key, "0")).lower()
        if value in {"1", "true", "yes"}:
            risks.append((key, title, str(result.get(key))))
    return risks

def _chain_id(chain: str) -> str:
    value = (chain or "ethereum").lower().strip()
    return CHAIN_IDS.get(value, value)

def _validate_address(value: str | None, label: str) -> str | None:
    if not value:
        return None
    cleaned = value.strip()
    if not EVM_RE.match(cleaned):
        raise ValueError(f"Invalid {label}. Provide a valid EVM 0x address.")
    return cleaned

def _parse_goplus_token(data: dict[str, Any], token: str) -> list[tuple[str, str, str]]:
    result = data.get("result") or {}
    item = None
    if isinstance(result, dict):
        item = result.get(token.lower()) or result.get(token) or next(iter(result.values()), None) if result else None
    risks: list[tuple[str, str, str]] = []
    if isinstance(item, dict):
        checks = {
            "is_honeypot": "Token may be honeypot",
            "is_blacklisted": "Token/owner blacklist capability flagged",
            "can_take_back_ownership": "Ownership can be taken back",
            "owner_change_balance": "Owner may change balances",
            "hidden_owner": "Hidden owner risk flagged",
            "selfdestruct": "Selfdestruct risk flagged",
            "external_call": "External call risk flagged",
            "cannot_sell_all": "Cannot sell all tokens flag",
        }
        for key, title in checks.items():
            if str(item.get(key, "0")).lower() in {"1", "true", "yes"}:
                risks.append((key, title, str(item.get(key))))
    return risks

async def run_wallet_risk_api_scan(chain: str = "ethereum", token_address: str | None = None, spender_address: str | None = None, wallet_address: str | None = None, project_name: str | None = None, approval_contract_address: str | None = None) -> ScanResponse:
    token = _validate_address(token_address, "token address")
    spender = _validate_address(spender_address, "spender address")
    wallet = _validate_address(wallet_address, "wallet address")
    approval_contract = _validate_address(approval_contract_address, "approval contract address")
    chain_id = _chain_id(chain)
    input_material = "|".join([chain_id, token or "", spender or "", wallet or "", approval_contract or ""])
    if len(input_material.replace("|", "")) < 2:
        raise ValueError("Provide at least a token, spender, wallet, or approval contract address.")
    findings: list[Finding] = []
    idx = 1
    metadata: dict = {
        "chain": chain,
        "chain_id": chain_id,
        "token_address": token,
        "spender_address": spender,
        "wallet_address": wallet,
        "approval_contract_address": approval_contract,
        "provider": "goplus",
        "provider_enabled": settings.goplus_enabled,
        "provider_calls": [],
        "raw_provider_data_available": False,
        "no_wallet_connect": True,
        "no_private_key_collection": True,
        "no_transaction_signing": True,
    }
    if spender:
        findings.append(_finding(idx, "info", "Spender Address Provided For Manual Review", f"Spender address recorded: {spender}.", "Display this spender clearly in wallet UI and link it to an explorer/reputation check before users approve.")); idx += 1
    if wallet:
        findings.append(_finding(idx, "info", "Wallet Address Provided For Read-Only Risk Context", "Wallet address was provided for read-only risk context only.", "Never ask users for seed phrases/private keys. Use read-only address checks and clear consent.")); idx += 1
    if not settings.goplus_enabled:
        findings.append(_finding(idx, "info", "External Wallet Risk Provider Not Enabled", "GoPlus/API wallet-risk integration is disabled in backend env, so no external provider risk data was fetched.", "Set GOPLUS_ENABLED=true only after accepting provider terms and validating privacy/availability. Until then, use local wallet-flow checklist.")); idx += 1
    else:
        headers = {"accept": "application/json"}
        if settings.goplus_access_token:
            headers["Authorization"] = f"Bearer {settings.goplus_access_token}"
        timeout = httpx.Timeout(settings.wallet_risk_api_timeout_seconds)
        async with httpx.AsyncClient(timeout=timeout, headers=headers) as client:
            if token:
                url = f"{settings.goplus_api_base.rstrip('/')}/api/v1/token_security/{chain_id}"
                try:
                    resp = await client.get(url, params={"contract_addresses": token})
                    metadata["provider_calls"].append({"type": "token_security", "status_code": resp.status_code})
                    if resp.status_code < 400:
                        data = resp.json()
                        metadata["raw_provider_data_available"] = True
                        metadata["token_security_summary"] = {"code": data.get("code"), "message": data.get("message")}
                        for key, title, evidence in _parse_goplus_token(data, token):
                            findings.append(_finding(idx, "high", f"Provider Risk Flag: {title}", f"GoPlus token security field {key} returned {evidence}.", "Manually verify provider evidence, disclose high-risk controls, and pause launch until reviewed.")); idx += 1
                    else:
                        findings.append(_finding(idx, "low", "Token Security Provider Request Failed", f"Provider returned HTTP {resp.status_code} for token security request.", "Check provider credentials/rate limits and retry. Do not show fake provider result.")); idx += 1
                except Exception as exc:
                    findings.append(_finding(idx, "low", "Token Security Provider Unavailable", f"Provider request failed: {exc}.", "Keep local wallet-flow checklist available and retry provider scan later.")); idx += 1
            for label, address_value in (("wallet", wallet), ("spender", spender)):
                if address_value:
                    url = f"{settings.goplus_api_base.rstrip('/')}/api/v1/address_security/{address_value}"
                    try:
                        resp = await client.get(url, params={"chain_id": chain_id})
                        metadata["provider_calls"].append({"type": f"address_security_{label}", "status_code": resp.status_code})
                        if resp.status_code < 400:
                            data = resp.json()
                            metadata["raw_provider_data_available"] = True
                            metadata[f"{label}_address_security_summary"] = {"code": data.get("code"), "message": data.get("message")}
                            for key, title, evidence in _parse_goplus_address(data):
                                findings.append(_finding(idx, "high", f"Provider Address Risk Flag: {title}", f"GoPlus address security field {key} returned {evidence} for {label} address.", "Manually verify provider evidence, avoid presenting this address as safe, and add a clear warning before launch.")); idx += 1
                        else:
                            findings.append(_finding(idx, "low", "Address Security Provider Request Failed", f"Provider returned HTTP {resp.status_code} for {label} address security request.", "Check provider credentials/rate limits and retry. Do not show fake address risk result.")); idx += 1
                    except Exception as exc:
                        findings.append(_finding(idx, "low", "Address Security Provider Unavailable", f"Provider request failed for {label} address: {exc}.", "Use manual address reputation review until provider is available.")); idx += 1

            if approval_contract:
                url = f"{settings.goplus_api_base.rstrip('/')}/api/v1/approval_security/{chain_id}"
                try:
                    resp = await client.get(url, params={"contract_addresses": approval_contract})
                    metadata["provider_calls"].append({"type": "approval_security", "status_code": resp.status_code})
                    if resp.status_code < 400:
                        data = resp.json()
                        metadata["raw_provider_data_available"] = True
                        metadata["approval_security_summary"] = {"code": data.get("code"), "message": data.get("message")}
                    else:
                        findings.append(_finding(idx, "low", "Approval Security Provider Request Failed", f"Provider returned HTTP {resp.status_code} for approval security request.", "Check provider support for this chain/address and retry.")); idx += 1
                except Exception as exc:
                    findings.append(_finding(idx, "low", "Approval Security Provider Unavailable", f"Provider request failed: {exc}.", "Use manual spender/allowance review until provider is available.")); idx += 1
    score = score_findings(findings)
    return ScanResponse(
        report_id=f"W3G-WALLETAPI-{_hash(input_material)[:12]}",
        generated_at=datetime.now(timezone.utc),
        project_name=project_name,
        module_score=ModuleScore(module="wallet_risk", score=score, risk_label=risk_label(score)),
        findings=findings,
        severity_breakdown=severity_breakdown(findings),
        priority_actions=priority_actions(findings),
        input_hash=_hash(input_material)[:16],
        engine_version="web3guard-wallet-risk-api-engine-v3.0",
        scan_metadata=metadata,
    )

def wallet_risk_api_status() -> dict:
    return {
        "engine": "web3guard-wallet-risk-api-engine-v3.0",
        "status": "live_optional_provider",
        "real_only": True,
        "goplus_enabled": settings.goplus_enabled,
        "provider_base": settings.goplus_api_base,
        "supported_local_chain_aliases": CHAIN_IDS,
        "no_private_key_collection": True,
        "no_wallet_connection": True,
        "no_transaction_signing": True,
        "provider_endpoints": {
            "token_security": "/api/v1/token_security/{chain_id}",
            "address_security": "/api/v1/address_security/{address}",
            "approval_security": "/api/v1/approval_security/{chain_id}",
        },
        "provider_note": "External provider data is fetched only when GOPLUS_ENABLED=true. Missing provider never produces fake risk data.",
    }
