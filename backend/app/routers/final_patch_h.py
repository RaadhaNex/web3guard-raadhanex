from __future__ import annotations

from fastapi import APIRouter

from app.core.config import settings
from app.services.static_analysis_tools import static_analysis_status
from app.services.deep_analysis_tools import deep_analysis_status
from app.services.payment_store import payment_status
from app.services.monitoring_lite import monitoring_status
from app.services.professional_report import delivery_policy
from app.services.scan_contract_address import explorer_status
from app.services.scan_github_repo import github_scanner_status

router = APIRouter(prefix="/final-patch-h", tags=["Mega Final Patch H"])


@router.get("/status")
def final_patch_h_status():
    static_status = static_analysis_status()
    deep_status = deep_analysis_status()
    pay_status = payment_status()
    mon_status = monitoring_status()
    explorer = explorer_status()
    github = github_scanner_status()

    return {
        "ok": True,
        "phase": "Mega Final Patch H - Critical Real Integration + Cleanup",
        "real_only_rule": "Live features must use real provider/tool output. Missing integrations must show Tool Not Installed / Provider Not Configured / Needs API Key / Manual / Not Assessed.",
        "critical_gap_matrix": [
            {
                "area": "Slither / Aderyn / Semgrep",
                "status": "Live if STATIC_ANALYSIS_ENABLED=true and installed binaries are found",
                "evidence": static_status["tools"],
                "missing_behavior": "Tool Not Installed / disabled_by_env, no fake findings",
            },
            {
                "area": "Mythril / Manticore / Echidna",
                "status": "Live only if DEEP_ANALYSIS_ENABLED=true and binaries are installed; Mythril should normally run in Docker/worker",
                "evidence": deep_status["tools"],
                "missing_behavior": "Not Run / Docker worker required, no fake findings",
            },
            {
                "area": "Supabase Auth",
                "status": "Real client auth when NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY are configured; backend JWT enforcement requires SUPABASE_JWT_VERIFY_ENABLED=true",
                "backend_configured": bool(settings.supabase_url and settings.supabase_anon_key),
                "service_role_configured": bool(settings.supabase_service_role_key),
                "jwt_verify_enabled": settings.supabase_jwt_verify_enabled,
            },
            {
                "area": "Razorpay Checkout",
                "status": "Real order/signature/webhook verification when keys are configured",
                "evidence": pay_status,
                "missing_behavior": "Manual UPI fallback / Provider Not Configured, no fake payment success",
            },
            {
                "area": "PDF Export",
                "status": "Server-side ReportLab PDF endpoint available at POST /report/export/pdf",
                "evidence": delivery_policy(),
            },
            {
                "area": "Monitoring Lite",
                "status": "Real read-only RPC check only when MONITORING_ENABLED and MONITORING_RPC_ENABLED and chain RPC URL are configured",
                "evidence": mon_status,
                "missing_behavior": "Provider Not Configured / disabled, no fake live alert",
            },
            {
                "area": "GitHub Repo Scanner",
                "status": "Public repo scan works without token with lower rate limits; token recommended",
                "evidence": github,
            },
            {
                "area": "Contract Address Scanner",
                "status": "Real verified-source fetch only with Etherscan API key",
                "evidence": explorer,
            },
        ],
        "cleanup": {
            "duplicate_root_app_removed": True,
            "local_jsonl_seed_records_removed_from_release": True,
            "backend_source_of_truth": "backend/app",
            "frontend_source_of_truth": "frontend/app and frontend/components",
        },
        "blocked_claims": [
            "certified audit",
            "100% secure",
            "fake AI analysis",
            "fake payment success",
            "fake live monitoring",
            "fake tool findings",
            "fake escrow or on-chain certificate",
        ],
    }
