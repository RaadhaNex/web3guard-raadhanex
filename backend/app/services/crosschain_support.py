from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from app.core.config import settings
from app.models.schemas import CrossChainScanRequest
from app.services.mega_phase_e_store import append_jsonl, new_id, now_iso, read_jsonl, storage_path

CROSSCHAIN_REAL_ONLY_NOTE = (
    "Cross-chain scanner uses submitted source/ABI/notes only. It does not connect wallets, sign transactions, "
    "or claim complete chain-specific audit coverage. Non-EVM support is checklist/static-hint mode."
)

SUPPORTED_CHAINS = {
    "ethereum": {"family": "evm", "chain_id": 1, "explorer": "Etherscan"},
    "polygon": {"family": "evm", "chain_id": 137, "explorer": "Polygonscan"},
    "bnb": {"family": "evm", "chain_id": 56, "explorer": "BscScan"},
    "arbitrum": {"family": "evm", "chain_id": 42161, "explorer": "Arbiscan"},
    "optimism": {"family": "evm", "chain_id": 10, "explorer": "Optimistic Etherscan"},
    "base": {"family": "evm", "chain_id": 8453, "explorer": "Basescan"},
    "avalanche": {"family": "evm", "chain_id": 43114, "explorer": "Snowtrace/Routescan"},
    "solana": {"family": "solana_anchor", "chain_id": None, "explorer": "Solscan"},
    "sui": {"family": "move_sui_aptos", "chain_id": None, "explorer": "Sui Explorer"},
    "aptos": {"family": "move_sui_aptos", "chain_id": None, "explorer": "Aptos Explorer"},
}


def cross_chain_status() -> dict[str, Any]:
    return {"ok": True, "phase": "Mega Phase F - Phase 33 Cross-chain Support", "supported_chains": SUPPORTED_CHAINS, "evm_enabled": settings.cross_chain_evm_enabled, "solana_checklist_enabled": settings.cross_chain_solana_checklist_enabled, "move_checklist_enabled": settings.cross_chain_move_checklist_enabled, "real_only_note": CROSSCHAIN_REAL_ONLY_NOTE}


def _path() -> Path:
    return storage_path(settings.cross_chain_scans_file)


def _finding(severity: str, title: str, description: str, recommendation: str, family: str, evidence: str | None = None) -> dict[str, Any]:
    return {"id": new_id("xchain_find"), "severity": severity, "title": title, "description": description, "recommendation": recommendation, "chain_family": family, "evidence": evidence, "source": "cross_chain_static_hint", "confidence": 0.76}


def _penalty(sev: str) -> int:
    return {"critical": 25, "high": 15, "medium": 8, "low": 3, "info": 1}.get(sev, 3)


def _evm_checks(text: str, chains: list[str]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    if len(chains) > 1 and "block.chainid" not in text.lower() and "chainid" not in text.lower():
        findings.append(_finding("medium", "Chain ID/domain separation not visible", "Multi-chain deployments should bind signatures/messages to a chain/domain to reduce replay risk.", "Review EIP-712 domain separator, chain ID checks, and bridge message replay protection.", "evm"))
    if re.search(r"ecrecover|permit\(|signature|domainseparator", text, re.I) and not re.search(r"nonce|deadline|chainid", text, re.I):
        findings.append(_finding("high", "Signature flow replay controls not obvious", "Signature/permit style logic appears without visible nonce/deadline/chain separation evidence.", "Add nonce, deadline, chain-specific domain, and signer validation tests.", "evm"))
    if re.search(r"bridge|lzreceive|ccip|wormhole|messenger|crosschain", text, re.I) and not re.search(r"trusted|allowlist|remote|endpoint|sourcechain", text, re.I):
        findings.append(_finding("high", "Cross-chain message sender validation needs review", "Bridge/messaging keywords appear without obvious trusted remote/source validation evidence.", "Verify trusted endpoint, source chain, sender, nonce, replay, and failure handling.", "evm"))
    if re.search(r"oracle|pricefeed|aggregator", text, re.I) and not re.search(r"stale|updatedat|heartbeat|sequencer", text, re.I):
        findings.append(_finding("medium", "Oracle freshness/L2 sequencer checks not visible", "Oracle feeds on L2/multi-chain deployments need stale data and sequencer-down handling.", "Add stale price checks, decimals validation, and L2 sequencer uptime checks where relevant.", "evm"))
    if "delegatecall" in text.lower():
        findings.append(_finding("high", "delegatecall surface present", "delegatecall can be high-risk across chains/proxies if target control is weak.", "Restrict targets, validate implementation addresses, and add upgrade governance.", "evm", "delegatecall"))
    return findings


def _solana_checks(text: str) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    low = text.lower()
    if "signer" not in low:
        findings.append(_finding("medium", "Signer validation not confirmed", "Anchor/Solana programs should explicitly validate signer accounts for privileged actions.", "Confirm has_one/signer constraints and runtime signer checks for admin paths.", "solana_anchor"))
    if "seeds" in low and "bump" not in low:
        findings.append(_finding("medium", "PDA bump handling not visible", "PDA derivation should include seeds and bump validation.", "Review PDA seeds, bump, and account ownership checks.", "solana_anchor"))
    if "owner" not in low and "has_one" not in low:
        findings.append(_finding("medium", "Account ownership constraints not confirmed", "Solana account substitution risks require ownership/has_one constraints.", "Add owner, constraint, has_one, and account discriminator validation.", "solana_anchor"))
    return findings


def _move_checks(text: str) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    low = text.lower()
    if "signer" not in low and "capability" not in low:
        findings.append(_finding("medium", "Signer/capability access model not confirmed", "Move modules rely on signer/capability patterns for privileged operations.", "Review capability creation/storage and privileged entry functions.", "move_sui_aptos"))
    if "public entry" in low and "assert" not in low:
        findings.append(_finding("medium", "Public entry functions need authorization checks", "Public entry functions should enforce ownership/capability/role checks.", "Add asserts for owner/capability and test unauthorized calls.", "move_sui_aptos"))
    if "object" in low and "owner" not in low:
        findings.append(_finding("low", "Object ownership lifecycle not clear", "Sui/Aptos object/resource ownership needs explicit review.", "Document transfer, freeze, burn, and admin object control.", "move_sui_aptos"))
    return findings


def run_cross_chain_scan(payload: CrossChainScanRequest, user_id: str) -> dict[str, Any]:
    text = "\n".join(filter(None, [payload.source_code, payload.abi_json, payload.notes]))
    findings: list[dict[str, Any]] = []
    chains = [c.lower() for c in (payload.chains or [])]
    unknown_chains = [c for c in chains if c not in SUPPORTED_CHAINS]
    for chain in unknown_chains:
        findings.append(_finding("info", f"Chain '{chain}' is not in supported metadata", "The scanner cannot provide chain-specific metadata for this chain.", "Use manual review and add chain metadata before production support.", payload.chain_family))
    if not text.strip():
        findings.append(_finding("info", "No source/ABI/notes submitted", "Cross-chain scan cannot assess code without source/ABI/notes.", "Submit verified source, ABI, or architecture notes for real assessment.", payload.chain_family))
    elif payload.chain_family == "evm":
        findings.extend(_evm_checks(text, chains))
    elif payload.chain_family == "solana_anchor":
        findings.extend(_solana_checks(text))
    else:
        findings.extend(_move_checks(text))
    if payload.contract_address and payload.chain_family == "evm" and not re.fullmatch(r"0x[a-fA-F0-9]{40}", payload.contract_address.strip()):
        findings.append(_finding("medium", "Invalid EVM contract address format", "Provided EVM contract address does not match 0x + 40 hex chars.", "Confirm chain and contract address before public report.", "evm"))
    score = max(0, 100 - sum(_penalty(f["severity"]) for f in findings))
    row = {"id": new_id("xchain_scan"), "user_id": user_id, "created_at": now_iso(), "project_name": payload.project_name, "chain_family": payload.chain_family, "chains": chains, "supported_chain_metadata": {c: SUPPORTED_CHAINS.get(c) for c in chains if c in SUPPORTED_CHAINS}, "score": score, "findings": findings, "manual_review_required": payload.chain_family != "evm" or any(f["severity"] in {"critical", "high"} for f in findings), "real_only_note": CROSSCHAIN_REAL_ONLY_NOTE}
    append_jsonl(_path(), row)
    return row


def list_cross_chain_scans(limit: int = 50) -> list[dict[str, Any]]:
    return sorted(read_jsonl(_path()), key=lambda r: r.get("created_at", ""), reverse=True)[:limit]
