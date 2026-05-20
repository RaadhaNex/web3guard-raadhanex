from fastapi import APIRouter

from app.models.schemas import UnifiedUrlScanRequest
from app.services.deep_scan_orchestrator import build_deep_scan_orchestrator

router = APIRouter(prefix="/deep-scan-orchestrator", tags=["phase78-deep-scan-orchestrator"])


@router.get("/status")
def deep_scan_orchestrator_status():
    return {
        "ok": True,
        "phase": "78",
        "name": "Unified Deep Scan Orchestrator + Clean Scanner UX",
        "quick_scan_default": True,
        "modes": ["quick", "deep", "expert"],
        "truth_rule": "URL-only scans auto-run public evidence; optional engines only run when evidence/tool/provider is present.",
        "safe_boundaries": [
            "No fake Slither/Semgrep/GitHub/API/wallet findings.",
            "No exploit automation, brute force, credential testing, DoS, private key/seed collection, or wallet signing.",
            "No certified audit claim or 100% secure claim.",
        ],
    }


@router.post("/preview")
def preview_deep_scan_orchestrator(payload: UnifiedUrlScanRequest):
    return build_deep_scan_orchestrator(payload, module_cards=[], surface_hints={})
