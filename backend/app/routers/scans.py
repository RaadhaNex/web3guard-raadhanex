from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import PlainTextResponse

from app.models.schemas import ChecklistScanRequest, ContractAddressScanRequest, ContractScanRequest, DeepAnalysisRequest, GitHubRepoScanRequest, PermissionMapRequest, StaticAnalysisRequest, UnifiedUrlScanRequest, WebsiteScanRequest, LaunchTransparencyRequest, ContractDiffRequest, UpgradeSafetyRequest, AdvancedWebsiteScanRequest, ApiDeepReadinessRequest, WalletRiskApiRequest
from app.services.checklists import checklist_template
from app.services.scan_dapp_api import enhanced_checklist_template, scan_api_backend, scan_dapp_frontend
from app.services.scan_wallet_admin import scan_admin_opsec as run_admin_opsec_scan, scan_wallet_flow, wallet_admin_checklist_template
from app.services.scan_contract import available_contract_rules, scan_solidity
from app.core.config import settings
from app.services.rate_limit import enforce_hourly_limit
from app.services.scan_website import scan_website
from app.services.unified_url_scan import REALNESS_MATRIX, run_unified_url_scan
from app.services.scan_github_repo import github_scanner_status, scan_github_repository
from app.services.scan_contract_address import explorer_status, scan_contract_address
from app.services.static_analysis_tools import static_analysis_status, run_static_analysis
from app.services.deep_analysis_tools import deep_analysis_status, run_deep_analysis
from app.services.permission_map import permission_map_status, build_permission_map
from app.services.launch_transparency import launch_transparency_status, build_launch_transparency_report
from app.services.contract_diff import contract_diff_status, build_contract_diff_report
from app.services.upgrade_safety import upgrade_safety_status, build_upgrade_safety_report
from app.services.advanced_website_scan import advanced_website_status, run_advanced_website_scan
from app.services.api_deep_readiness import api_deep_status, run_api_deep_readiness_scan
from app.services.wallet_risk_integrations import wallet_risk_api_status, run_wallet_risk_api_scan

router = APIRouter(prefix="/scan", tags=["scans"])
SAMPLE_CONTRACT_DIR = Path(__file__).resolve().parents[1] / "data" / "sample_contracts"


# Mega Phase B — Phase 20/21/22
@router.get("/website-advanced/status")
def advanced_website_engine_status():
    return advanced_website_status()


@router.post("/website-advanced")
async def advanced_website_scan_endpoint(payload: AdvancedWebsiteScanRequest, request: Request):
    if not payload.authorization_confirmed:
        raise HTTPException(status_code=400, detail="Authorization confirmation is required")
    if not payload.real_only_acknowledged:
        raise HTTPException(status_code=400, detail="Real-only acknowledgement is required")
    client_host = request.client.host if request.client else "unknown"
    enforce_hourly_limit(f"website-advanced:{client_host}", limit=settings.max_advanced_website_scan_per_hour)
    try:
        return await run_advanced_website_scan(
            website_url=payload.website_url,
            project_name=payload.project_name,
            ownership_verified=payload.ownership_verified,
            max_internal_pages=payload.max_internal_pages,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/api-deep/status")
def api_deep_engine_status():
    return api_deep_status()


@router.post("/api-deep")
async def api_deep_scan_endpoint(payload: ApiDeepReadinessRequest, request: Request):
    if not payload.authorization_confirmed:
        raise HTTPException(status_code=400, detail="Authorization confirmation is required")
    if not payload.real_only_acknowledged:
        raise HTTPException(status_code=400, detail="Real-only acknowledgement is required")
    client_host = request.client.host if request.client else "unknown"
    enforce_hourly_limit(f"api-deep:{client_host}", limit=settings.max_api_deep_scan_per_hour)
    try:
        return await run_api_deep_readiness_scan(
            api_base_url=payload.api_base_url,
            project_name=payload.project_name,
            openapi_json=payload.openapi_json,
            api_code=payload.api_code,
            notes=payload.notes,
            ownership_verified=payload.ownership_verified,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/wallet-risk/status")
def wallet_risk_engine_status():
    return wallet_risk_api_status()


@router.post("/wallet-risk")
async def wallet_risk_scan_endpoint(payload: WalletRiskApiRequest, request: Request):
    if not payload.authorization_confirmed:
        raise HTTPException(status_code=400, detail="Authorization confirmation is required")
    if not payload.real_only_acknowledged:
        raise HTTPException(status_code=400, detail="Real-only acknowledgement is required")
    client_host = request.client.host if request.client else "unknown"
    enforce_hourly_limit(f"wallet-risk:{client_host}", limit=settings.max_wallet_risk_api_scan_per_hour)
    try:
        return await run_wallet_risk_api_scan(
            chain=payload.chain,
            token_address=payload.token_address,
            spender_address=payload.spender_address,
            wallet_address=payload.wallet_address,
            approval_contract_address=payload.approval_contract_address,
            project_name=payload.project_name,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc



@router.post("/contract")
def scan_contract(payload: ContractScanRequest, request: Request):
    if not payload.authorization_confirmed:
        raise HTTPException(status_code=400, detail="Authorization confirmation is required")
    client_host = request.client.host if request.client else "unknown"
    enforce_hourly_limit(f"contract:{client_host}", limit=settings.max_contract_scan_per_hour)
    return scan_solidity(payload.solidity_code, payload.project_name, payload.contract_type)




@router.get("/contract-address/status")
def contract_address_status():
    return explorer_status()


@router.post("/contract-address")
async def scan_contract_address_endpoint(payload: ContractAddressScanRequest, request: Request):
    if not payload.authorization_confirmed:
        raise HTTPException(status_code=400, detail="Authorization confirmation is required")
    if not payload.real_only_acknowledged:
        raise HTTPException(status_code=400, detail="Real-only acknowledgement is required")
    client_host = request.client.host if request.client else "unknown"
    enforce_hourly_limit(f"contract-address:{client_host}", limit=settings.max_contract_address_scan_per_hour)
    try:
        return await scan_contract_address(payload.address, payload.chain, payload.project_name)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc








@router.get("/launch-transparency/status")
def launch_transparency_engine_status():
    return launch_transparency_status()


@router.post("/launch-transparency")
def launch_transparency_scan_endpoint(payload: LaunchTransparencyRequest, request: Request):
    if not payload.authorization_confirmed:
        raise HTTPException(status_code=400, detail="Authorization confirmation is required")
    if not payload.real_only_acknowledged:
        raise HTTPException(status_code=400, detail="Real-only acknowledgement is required")
    client_host = request.client.host if request.client else "unknown"
    enforce_hourly_limit(f"launch-transparency:{client_host}", limit=settings.max_launch_transparency_scan_per_hour)
    try:
        return build_launch_transparency_report(
            project_name=payload.project_name,
            project_type=payload.project_type,
            solidity_code=payload.solidity_code,
            website_text=payload.website_text,
            tokenomics_notes=payload.tokenomics_notes,
            liquidity_lock_evidence=payload.liquidity_lock_evidence,
            metadata_freeze_evidence=payload.metadata_freeze_evidence,
            owner_power_notes=payload.owner_power_notes,
            multisig_enabled=payload.multisig_enabled,
            timelock_enabled=payload.timelock_enabled,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/contract-diff/status")
def contract_diff_engine_status():
    return contract_diff_status()


@router.post("/contract-diff")
def contract_diff_scan_endpoint(payload: ContractDiffRequest, request: Request):
    if not payload.authorization_confirmed:
        raise HTTPException(status_code=400, detail="Authorization confirmation is required")
    if not payload.real_only_acknowledged:
        raise HTTPException(status_code=400, detail="Real-only acknowledgement is required")
    client_host = request.client.host if request.client else "unknown"
    enforce_hourly_limit(f"contract-diff:{client_host}", limit=settings.max_contract_diff_scan_per_hour)
    try:
        return build_contract_diff_report(
            project_name=payload.project_name,
            old_code=payload.old_code,
            new_code=payload.new_code,
            contract_type=payload.contract_type,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/upgrade-safety/status")
def upgrade_safety_engine_status():
    return upgrade_safety_status()


@router.post("/upgrade-safety")
def upgrade_safety_scan_endpoint(payload: UpgradeSafetyRequest, request: Request):
    if not payload.authorization_confirmed:
        raise HTTPException(status_code=400, detail="Authorization confirmation is required")
    if not payload.real_only_acknowledged:
        raise HTTPException(status_code=400, detail="Real-only acknowledgement is required")
    client_host = request.client.host if request.client else "unknown"
    enforce_hourly_limit(f"upgrade-safety:{client_host}", limit=settings.max_upgrade_safety_scan_per_hour)
    try:
        return build_upgrade_safety_report(
            project_name=payload.project_name,
            current_code=payload.current_code,
            previous_code=payload.previous_code,
            proxy_admin_notes=payload.proxy_admin_notes,
            ownership_verified=payload.ownership_verified,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/permission-map/status")
def permission_map_engine_status():
    return permission_map_status()


@router.post("/permission-map")
def permission_map_scan_endpoint(payload: PermissionMapRequest, request: Request):
    if not payload.authorization_confirmed:
        raise HTTPException(status_code=400, detail="Authorization confirmation is required")
    if not payload.real_only_acknowledged:
        raise HTTPException(status_code=400, detail="Real-only acknowledgement is required")
    client_host = request.client.host if request.client else "unknown"
    enforce_hourly_limit(f"permission-map:{client_host}", limit=settings.max_permission_map_scan_per_hour)
    try:
        return build_permission_map(
            project_name=payload.project_name,
            solidity_code=payload.solidity_code,
            abi_json=payload.abi_json,
            contract_address=payload.contract_address,
            chain=payload.chain,
            owner_address=payload.owner_address,
            treasury_address=payload.treasury_address,
            multisig_enabled=payload.multisig_enabled,
            timelock_enabled=payload.timelock_enabled,
            governance_notes=payload.governance_notes,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/static-analysis/status")
def static_analysis_tool_status():
    return static_analysis_status()


@router.get("/deep-analysis/status")
def deep_analysis_tool_status():
    return deep_analysis_status()


@router.post("/deep-analysis")
def deep_analysis_scan_endpoint(payload: DeepAnalysisRequest, request: Request):
    if not payload.authorization_confirmed:
        raise HTTPException(status_code=400, detail="Authorization confirmation is required")
    if not payload.real_only_acknowledged:
        raise HTTPException(status_code=400, detail="Real-only acknowledgement is required")
    client_host = request.client.host if request.client else "unknown"
    enforce_hourly_limit(f"deep-analysis:{client_host}", limit=settings.max_deep_analysis_scan_per_hour)
    try:
        return run_deep_analysis(
            solidity_code=payload.solidity_code,
            project_name=payload.project_name,
            file_name=payload.file_name,
            requested_tools=payload.tools,
            scan_depth=payload.scan_depth,
            ownership_verified=payload.ownership_verified,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/static-analysis")
def static_analysis_scan_endpoint(payload: StaticAnalysisRequest, request: Request):
    if not payload.authorization_confirmed:
        raise HTTPException(status_code=400, detail="Authorization confirmation is required")
    if not payload.real_only_acknowledged:
        raise HTTPException(status_code=400, detail="Real-only acknowledgement is required")
    client_host = request.client.host if request.client else "unknown"
    enforce_hourly_limit(f"static-analysis:{client_host}", limit=settings.max_static_analysis_scan_per_hour)
    try:
        return run_static_analysis(
            solidity_code=payload.solidity_code,
            project_name=payload.project_name,
            file_name=payload.file_name,
            requested_tools=payload.tools,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/contract/rules")
def get_contract_rules():
    return {
        "engine_version": "web3guard-solidity-rule-engine-v2.0",
        "disclaimer": "Rule engine findings are preliminary and do not replace a full manual audit.",
        "rules": available_contract_rules(),
    }


@router.get("/contract/samples")
def list_contract_samples():
    samples = sorted(path.stem for path in SAMPLE_CONTRACT_DIR.glob("*.sol"))
    return {"samples": samples}


@router.get("/contract/samples/{sample_name}", response_class=PlainTextResponse)
def get_contract_sample(sample_name: str):
    safe_name = sample_name.replace(".sol", "")
    sample_path = SAMPLE_CONTRACT_DIR / f"{safe_name}.sol"
    if not sample_path.exists():
        raise HTTPException(status_code=404, detail="Sample contract not found")
    return sample_path.read_text(encoding="utf-8")


@router.post("/website")
async def scan_website_endpoint(payload: WebsiteScanRequest, request: Request):
    if not payload.authorization_confirmed:
        raise HTTPException(status_code=400, detail="Authorization confirmation is required")
    client_host = request.client.host if request.client else "unknown"
    enforce_hourly_limit(f"website:{client_host}")
    try:
        return await scan_website(payload.url, payload.project_name)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/checklist/{module}")
def get_checklist(module: str):
    if module not in {"dapp", "api", "wallet", "admin_opsec"}:
        raise HTTPException(status_code=404, detail="Unknown checklist module")
    if module in {"dapp", "api"}:
        return {"module": module, "items": enhanced_checklist_template(module), "engine_version": "web3guard-dapp-api-engine-v2.6"}
    if module in {"wallet", "admin_opsec"}:
        return {"module": module, "items": wallet_admin_checklist_template(module), "engine_version": "web3guard-wallet-admin-engine-v2.7"}
    return {"module": module, "items": checklist_template(module)}


@router.post("/dapp-checklist")
def scan_dapp(payload: ChecklistScanRequest, request: Request):
    if not payload.authorization_confirmed:
        raise HTTPException(status_code=400, detail="Authorization confirmation is required")
    client_host = request.client.host if request.client else "unknown"
    enforce_hourly_limit(f"dapp:{client_host}", limit=settings.max_checklist_scan_per_hour)
    return scan_dapp_frontend(
        checklist=payload.checklist,
        project_name=payload.project_name,
        frontend_code=payload.frontend_code,
        package_json=payload.package_json,
        notes=payload.notes,
    )


@router.post("/api-checklist")
def scan_api(payload: ChecklistScanRequest, request: Request):
    if not payload.authorization_confirmed:
        raise HTTPException(status_code=400, detail="Authorization confirmation is required")
    client_host = request.client.host if request.client else "unknown"
    enforce_hourly_limit(f"api:{client_host}", limit=settings.max_checklist_scan_per_hour)
    try:
        return scan_api_backend(
            checklist=payload.checklist,
            project_name=payload.project_name,
            api_base_url=payload.api_base_url,
            api_code=payload.api_code,
            notes=payload.notes,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/wallet-checklist")
def scan_wallet(payload: ChecklistScanRequest, request: Request):
    if not payload.authorization_confirmed:
        raise HTTPException(status_code=400, detail="Authorization confirmation is required")
    client_host = request.client.host if request.client else "unknown"
    enforce_hourly_limit(f"wallet:{client_host}", limit=settings.max_checklist_scan_per_hour)
    return scan_wallet_flow(checklist=payload.checklist, project_name=payload.project_name, notes=payload.notes)


@router.post("/admin-opsec")
def scan_admin_opsec(payload: ChecklistScanRequest, request: Request):
    if not payload.authorization_confirmed:
        raise HTTPException(status_code=400, detail="Authorization confirmation is required")
    client_host = request.client.host if request.client else "unknown"
    enforce_hourly_limit(f"admin:{client_host}", limit=settings.max_checklist_scan_per_hour)
    return run_admin_opsec_scan(checklist=payload.checklist, project_name=payload.project_name, notes=payload.notes)


@router.get("/github/status")
def github_status():
    return github_scanner_status()


@router.post("/github-repo")
async def scan_github_repo_endpoint(payload: GitHubRepoScanRequest, request: Request):
    if not payload.authorization_confirmed:
        raise HTTPException(status_code=400, detail="Authorization confirmation is required")
    if not payload.real_only_acknowledged:
        raise HTTPException(status_code=400, detail="Real-only acknowledgement is required")
    client_host = request.client.host if request.client else "unknown"
    enforce_hourly_limit(f"github:{client_host}", limit=settings.max_github_scan_per_hour)
    try:
        return await scan_github_repository(payload.repo_url, project_name=payload.project_name, branch=payload.branch)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/feature-status")
def feature_status_matrix():
    return {
        "rule": "Real-only feature status. Live features must have real backend logic; manual features require human/admin verification; future inputs must not receive fake scores.",
        "features": REALNESS_MATRIX,
    }


@router.post("/unified-url")
async def unified_url_scan_endpoint(payload: UnifiedUrlScanRequest, request: Request):
    if not payload.authorization_confirmed:
        raise HTTPException(status_code=400, detail="Authorization confirmation is required")
    if not payload.real_only_acknowledged:
        raise HTTPException(status_code=400, detail="Real-only acknowledgement is required")
    client_host = request.client.host if request.client else "unknown"
    enforce_hourly_limit(f"unified-url:{client_host}", limit=settings.max_url_scan_per_hour)
    try:
        return await run_unified_url_scan(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
