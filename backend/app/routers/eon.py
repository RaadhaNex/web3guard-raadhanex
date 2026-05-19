from __future__ import annotations

from fastapi import APIRouter, Query

from app.services.eon import build_fix_plan, build_risk_graph, eon_status, evidence_ledger

router = APIRouter(prefix="/eon", tags=["eon"])


@router.get("/status")
def status():
    return eon_status()


@router.get("/risk-graph")
def risk_graph(user_id: str = Query(..., min_length=1), project_id: str | None = None):
    return build_risk_graph(user_id=user_id, project_id=project_id)


@router.get("/fix-plan")
def fix_plan(user_id: str = Query(..., min_length=1), project_id: str | None = None):
    return build_fix_plan(user_id=user_id, project_id=project_id)


@router.get("/evidence-ledger")
def ledger(user_id: str = Query(..., min_length=1), project_id: str | None = None):
    return evidence_ledger(user_id=user_id, project_id=project_id)
