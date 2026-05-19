from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query

from app.services.report_verification import (
    build_report_verification_packet,
    report_verification_status,
    verify_public_report_record,
)

router = APIRouter(prefix="/report-verification", tags=["report-verification"])


@router.get("/status")
def verification_status():
    return report_verification_status()


@router.get("/public/{public_id}")
def verify_public_report(public_id: str, report_hash: str = Query(min_length=32)):
    return verify_public_report_record(public_id, report_hash)


@router.post("/payload")
def verify_report_payload(payload: dict[str, Any]):
    report = payload.get("report") or payload
    if not isinstance(report, dict):
        raise HTTPException(status_code=400, detail="A report object is required")
    return build_report_verification_packet(report, source="payload")
