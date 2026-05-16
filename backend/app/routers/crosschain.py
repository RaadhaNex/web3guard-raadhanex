from fastapi import APIRouter, Query, Request

from app.models.schemas import CrossChainScanRequest
from app.services.auth_guard import resolve_user_id
from app.services.crosschain_support import cross_chain_status, list_cross_chain_scans, run_cross_chain_scan

router = APIRouter(tags=["Cross-chain Support"])


@router.get("/cross-chain/status")
def status():
    return cross_chain_status()


@router.post("/cross-chain/scan")
def scan(payload: CrossChainScanRequest, request: Request):
    user_id, auth_context = resolve_user_id(request, payload.user_id)
    return {"ok": True, "auth_context": auth_context, "scan": run_cross_chain_scan(payload, user_id)}


@router.get("/cross-chain/scans")
def scans(limit: int = Query(default=50, ge=1, le=200)):
    return {"ok": True, "scans": list_cross_chain_scans(limit=limit)}
