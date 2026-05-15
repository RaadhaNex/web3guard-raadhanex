import hashlib
import re
from datetime import datetime, timezone
from urllib.parse import urlparse

from app.core.security import validate_public_http_url
from app.models.schemas import CombinedReportRequest, Finding, ModuleScore, ScanResponse, UnifiedUrlScanRequest
from app.services.report_builder import build_combined_launch_report
from app.services.scan_contract import scan_solidity
from app.services.scan_dapp_api import scan_api_backend
from app.services.scan_website import scan_website
from app.services.scan_github_repo import scan_github_repository
from app.services.scan_contract_address import scan_contract_address

MODULE_LABELS = {
    "website": "Website Surface",
    "dapp": "dApp Frontend Hints",
    "api": "API Backend",
    "contract": "Smart Contract",
    "wallet": "Wallet Flow",
    "admin_opsec": "Founder/Admin OpSec",
    "github": "GitHub Repository",
}

REALNESS_MATRIX = [
    {
        "feature": "Website URL passive surface scanner",
        "status": "Live",
        "evidence": "Runs real passive GET/HEAD checks for HTTPS, redirects, headers, robots/sitemap, limited path hints, and public HTML script evidence.",
        "not_claimed": "No exploit testing, no credential testing, no authenticated crawl, no certified audit.",
    },
    {
        "feature": "Unified URL launch surface map",
        "status": "Live",
        "evidence": "Combines live website scan with optional API URL and pasted Solidity source when provided. Missing modules are marked Not assessed.",
        "not_claimed": "It does not infer a full launch score when inputs are missing.",
    },
    {
        "feature": "dApp frontend from website URL",
        "status": "Live limited hints",
        "evidence": "Reads public homepage evidence such as external scripts, inline scripts, dApp keywords, wallet/mint/claim/swap/stake text, and visible EVM address hints.",
        "not_claimed": "It is not a full frontend source-code audit without repo/source input.",
    },
    {
        "feature": "API backend scan",
        "status": "Manual / Live limited",
        "evidence": "Validates public API URL safety and checks pasted API code/config. It does not fuzz or bypass auth.",
        "not_claimed": "No authenticated penetration test or exploit payloads.",
    },
    {
        "feature": "Smart contract scan",
        "status": "Live for pasted Solidity",
        "evidence": "Rule engine runs on user-submitted Solidity source. Contract address fetching is not enabled yet.",
        "not_claimed": "No Slither/Mythril/Aderyn/verified-address fetch unless later configured.",
    },
    {
        "feature": "UPI payment",
        "status": "Manual payment verification",
        "evidence": "Generates real UPI deep links and stores payment reference for admin verification.",
        "not_claimed": "No automatic payment success or active subscription until Razorpay/webhook is implemented.",
    },
    {
        "feature": "AI explanations",
        "status": "Needs API key / fallback when disabled",
        "evidence": "Fallback local explanations run without AI. Real AI only runs if backend env enables provider and key.",
        "not_claimed": "No fake AI analysis when AI provider is disabled.",
    },
    {
        "feature": "GitHub public repo scanner",
        "status": "Live for public GitHub repos",
        "evidence": "Uses GitHub API/raw public files with file/byte limits to detect Solidity, frontend, API, package, config, deployment, and secret-hygiene hints.",
        "not_claimed": "No repo cloning, no dependency install, no code execution, no private repo scan without real token/authorization, no Slither/Aderyn execution yet.",
    },
    {
        "feature": "Contract address scanner",
        "status": "Live when explorer API key and verified source are available",
        "evidence": "Fetches verified contract source and ABI metadata from Etherscan API V2-compatible explorer endpoint, then runs local rule engine and metadata checks.",
        "not_claimed": "No private key collection, no wallet signing, no bytecode decompilation, no fake source scan when source is unverified or API key missing.",
    },

    {
        "feature": "Permission map + centralization report",
        "status": "Live for provided Solidity/ABI/manual facts",
        "evidence": "Maps owner, minter, pauser, upgrader, treasury, blacklist/freeze, fee, role-admin, and oracle powers from real source/ABI/manual inputs.",
        "not_claimed": "Does not invent role holders, does not collect private keys, and does not prove live multisig/timelock status without evidence.",
    },
    {
        "feature": "Deep analysis tool runner",
        "status": "Needs local tools / isolated worker",
        "evidence": "Runs real Mythril, Manticore, and Echidna only when installed and enabled; standard/deep modes require ownership verification.",
        "not_claimed": "No fake symbolic execution, no fake fuzzing, no private key collection, no dependency install by default, no mainnet execution.",
    },
]

DAPP_KEYWORDS = ["walletconnect", "metamask", "connect wallet", "mint", "claim", "airdrop", "swap", "stake", "approve", "permit", "bridge", "presale"]
EVM_ADDRESS_RE = re.compile(r"0x[a-fA-F0-9]{40}")


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _status_card(
    module: str,
    status: str,
    *,
    report: ScanResponse | None = None,
    evidence: list[str] | None = None,
    limitations: list[str] | None = None,
    required_input: list[str] | None = None,
) -> dict:
    return {
        "module": module,
        "label": MODULE_LABELS.get(module, module),
        "status": status,
        "score": report.module_score.score if report else None,
        "risk_label": report.module_score.risk_label if report else "Not assessed",
        "assessed": bool(report),
        "report_id": report.report_id if report else None,
        "findings_count": len(report.findings) if report else 0,
        "critical_high_count": sum(1 for f in report.findings if f.severity in {"critical", "high"}) if report else 0,
        "evidence": evidence or [],
        "limitations": limitations or [],
        "required_input": required_input or [],
    }


def _dapp_hints_from_website(website_report: ScanResponse) -> dict:
    metadata = website_report.scan_metadata or {}
    html = metadata.get("html_evidence", {}) if isinstance(metadata, dict) else {}
    keyword_hits = html.get("dapp_keyword_hits", []) if isinstance(html, dict) else []
    evm_addresses = html.get("evm_address_hints", []) if isinstance(html, dict) else []
    external_script_count = html.get("external_script_count", 0) if isinstance(html, dict) else 0
    inline_script_count = html.get("inline_script_count", 0) if isinstance(html, dict) else 0
    risky_script_hints = html.get("risky_script_hints", []) if isinstance(html, dict) else []

    findings: list[dict] = []
    if keyword_hits:
        findings.append({
            "severity": "info",
            "title": "dApp/Wallet Language Detected On Public Homepage",
            "evidence": ", ".join(keyword_hits[:12]),
            "meaning": "The website appears to include Web3 launch flow language, so wallet/transaction UX should be reviewed manually or with source code.",
        })
    if evm_addresses:
        findings.append({
            "severity": "info",
            "title": "Visible EVM Address Hint Found",
            "evidence": ", ".join(evm_addresses[:5]),
            "meaning": "Visible addresses should be paired with chain name, explorer link, and verified contract clarity.",
        })
    if external_script_count and external_script_count > 0:
        findings.append({
            "severity": "info",
            "title": "External Script Surface Present",
            "evidence": f"{external_script_count} external script(s), {inline_script_count} inline script block(s)",
            "meaning": "Third-party scripts can affect wallet/mint pages and should be reviewed before launch.",
        })
    if risky_script_hints:
        findings.append({
            "severity": "info",
            "title": "Wallet/Mint Script URL Hint",
            "evidence": str(risky_script_hints[:3]),
            "meaning": "This is only a keyword hint, not a malicious classification.",
        })

    status = "Live limited hints" if findings else "No dApp hints found from homepage"
    return {
        "status": status,
        "keyword_hits": keyword_hits,
        "visible_evm_addresses": evm_addresses[:10],
        "findings": findings,
        "limitations": [
            "Homepage HTML cannot prove the safety of wallet transaction flow.",
            "Full frontend review needs GitHub/source code or manual UX review.",
            "No wallet connection, signing, or transaction simulation is performed.",
        ],
    }


def _github_not_assessed() -> dict:
    return _status_card(
        "github",
        "Not assessed",
        required_input=["Public GitHub repository URL"],
        limitations=["Provide a GitHub repo URL to run the Phase 11 read-only repository scanner."],
    )


async def run_unified_url_scan(payload: UnifiedUrlScanRequest) -> dict:
    started = datetime.now(timezone.utc)
    safe_website_url = validate_public_http_url(payload.website_url)
    reports: list[ScanResponse] = []
    module_cards: list[dict] = []
    surface_hints: dict = {}
    warnings: list[str] = []

    website_report = await scan_website(safe_website_url, payload.project_name)
    reports.append(website_report)
    module_cards.append(
        _status_card(
            "website",
            "Live",
            report=website_report,
            evidence=[
                f"Final URL: {website_report.scan_metadata.get('final_url')}",
                f"HTTP status: {website_report.scan_metadata.get('status_code')}",
                f"Headers present: {', '.join(website_report.scan_metadata.get('headers_present', [])) or 'none detected'}",
            ],
            limitations=["Passive-only public website checks. No login, exploit, brute force, or active security testing."],
        )
    )

    dapp_hints = _dapp_hints_from_website(website_report)
    surface_hints["dapp_from_homepage"] = dapp_hints
    module_cards.append(
        _status_card(
            "dapp",
            dapp_hints["status"],
            evidence=[finding["title"] for finding in dapp_hints["findings"]] or ["No wallet/mint/claim/swap/stake keyword hints found on the fetched homepage."],
            limitations=dapp_hints["limitations"],
            required_input=["Frontend source/GitHub repo for full dApp score", "Wallet flow checklist for transaction UX scoring"],
        )
    )

    if payload.api_base_url:
        api_report = scan_api_backend(checklist=[], project_name=payload.project_name, api_base_url=payload.api_base_url)
        reports.append(api_report)
        module_cards.append(
            _status_card(
                "api",
                "Live limited",
                report=api_report,
                evidence=[f"API URL passed public URL safety validation: {api_report.scan_metadata.get('validated_api_base', payload.api_base_url)}"],
                limitations=["No fuzzing, auth bypass, login test, or exploit payloads. Pasted API code/config is needed for deeper hints."],
            )
        )
    else:
        module_cards.append(
            _status_card(
                "api",
                "Not assessed",
                required_input=["API base URL or API code/config"],
                limitations=["Website URL alone does not prove backend API security."],
            )
        )

    if payload.solidity_code and payload.solidity_code.strip():
        contract_report = scan_solidity(payload.solidity_code, payload.project_name, payload.project_type)
        reports.append(contract_report)
        module_cards.append(
            _status_card(
                "contract",
                "Live for pasted Solidity",
                report=contract_report,
                evidence=["User submitted Solidity source was scanned by the local rule engine."],
                limitations=["This is still a preliminary rule-engine scan, not Slither/Mythril/Aderyn or certified audit."],
            )
        )
    elif payload.contract_address:
        try:
            address_report = await scan_contract_address(payload.contract_address, payload.chain, payload.project_name)
            reports.append(address_report)
            module_cards.append(
                _status_card(
                    "contract",
                    "Live from verified explorer source" if address_report.scan_metadata.get("source_verified") else "Explorer metadata only",
                    report=address_report,
                    evidence=[
                        f"Address: {payload.contract_address}",
                        f"Chain: {address_report.scan_metadata.get('chain_id')}",
                        f"Source verified: {address_report.scan_metadata.get('source_verified')}",
                    ],
                    limitations=["Explorer-source rule scan only. No wallet signing, bytecode decompilation, Slither/Aderyn/Mythril, or certified audit."],
                )
            )
        except ValueError as exc:
            module_cards.append(
                _status_card(
                    "contract",
                    "Input recorded only",
                    evidence=[f"Contract address provided: {payload.contract_address}", f"Chain: {payload.chain or 'not specified'}"],
                    required_input=[str(exc), "Paste Solidity source as fallback for a live rule-engine scan"],
                    limitations=["No fake contract score is generated when explorer source fetch cannot run."],
                )
            )
            warnings.append(f"Contract address scan was not completed: {exc}")
    else:
        module_cards.append(
            _status_card(
                "contract",
                "Not assessed",
                required_input=["Pasted Solidity source or future explorer source fetch"],
                limitations=["Website URL alone cannot assess smart contract code."],
            )
        )

    module_cards.append(
        _status_card(
            "wallet",
            "Manual input required",
            required_input=["Wallet flow checklist or UX/source review"],
            limitations=["No wallet connection, signing, approval lookup, or transaction simulation is performed in URL-only mode."],
        )
    )
    module_cards.append(
        _status_card(
            "admin_opsec",
            "Manual input required",
            required_input=["Founder/admin OpSec checklist: multisig, timelock, roles, treasury, MFA, key storage"],
            limitations=["Website URL cannot prove owner wallet, multisig, private key policy, or incident response readiness."],
        )
    )
    if payload.github_repo_url:
        try:
            github_report = await scan_github_repository(payload.github_repo_url, project_name=payload.project_name)
            reports.append(github_report)
            module_cards.append(
                _status_card(
                    "github",
                    "Live",
                    report=github_report,
                    evidence=[
                        f"Repo: {github_report.scan_metadata.get('repo', {}).get('url')}",
                        f"Branch: {github_report.scan_metadata.get('repo', {}).get('scanned_branch')}",
                        f"Files seen: {github_report.scan_metadata.get('structure_summary', {}).get('total_files_seen')}",
                    ],
                    limitations=["Read-only public GitHub API/raw file scan. No clone, execution, dependency install, or Slither/Aderyn in Phase 11."],
                )
            )
        except ValueError as exc:
            module_cards.append(
                _status_card(
                    "github",
                    "Input rejected",
                    evidence=[f"Repository URL provided: {payload.github_repo_url}"],
                    required_input=[str(exc)],
                    limitations=["No fake GitHub score is generated when the repo cannot be fetched."],
                )
            )
            warnings.append(f"GitHub repo scan was not completed: {exc}")
    else:
        module_cards.append(_github_not_assessed())

    combined = await build_combined_launch_report(CombinedReportRequest(
        project_name=payload.project_name or urlparse(safe_website_url).hostname or "Web3 project",
        reports=reports,
        preferred_language="English",
        include_ai=False,
        report_mode="pre_audit",
    ))

    assessed_modules = [card["module"] for card in module_cards if card["assessed"]]
    not_assessed_modules = [card["module"] for card in module_cards if not card["assessed"]]
    live_count = sum(1 for card in module_cards if str(card["status"]).lower().startswith("live"))

    return {
        "report_id": f"W3G-URL-LAUNCH-{_hash(safe_website_url)[:12]}",
        "generated_at": started.isoformat(),
        "project_name": payload.project_name,
        "engine_version": "web3guard-unified-url-launch-scanner-v12.0",
        "mode": "real_only_unified_url_scan",
        "website_url": safe_website_url,
        "chain": payload.chain,
        "project_type": payload.project_type,
        "realness_rule": "Only modules with real input/evidence receive a score. Missing modules are shown as Not assessed instead of fake scores.",
        "available_score": combined.get("combined", {}).get("available_score"),
        "overall_score": combined.get("combined", {}).get("overall_score"),
        "risk_label": combined.get("combined", {}).get("risk_label"),
        "coverage": combined.get("coverage"),
        "assessed_modules": assessed_modules,
        "not_assessed_modules": not_assessed_modules,
        "live_module_count": live_count,
        "module_cards": module_cards,
        "surface_hints": surface_hints,
        "priority_actions": combined.get("priority_action_plan", []),
        "combined_report": combined,
        "feature_status_matrix": REALNESS_MATRIX,
        "warnings": warnings,
        "safe_public_summary": "This is a preliminary URL launch-surface review. It is not a certified audit, penetration test, or guarantee of security.",
        "blocked_claims": [
            "Do not say this project is certified audited.",
            "Do not claim AI/manual experts reviewed missing modules.",
            "Do not show payment/subscription success without verified payment webhook or admin verification.",
            "Do not show a full launch score unless all required modules are assessed.",
        ],
        "next_real_inputs_needed": [
            "Paste Solidity source or enable explorer source fetch for contract scan.",
            "Provide API base URL/code for backend review.",
            "Complete wallet-flow checklist for approval/signature UX.",
            "Complete founder/admin OpSec checklist for multisig/timelock/key policy.",
            "Provide a public GitHub repo URL to run the Phase 11 read-only repo scanner.",
        ],
        "disclaimer": "This is a preliminary security review and does not replace a full manual audit. URL-only scans are partial by design.",
    }
