from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse, Response, StreamingResponse

from app.models.schemas import CombinedReportRequest
from app.services.professional_report import (
    build_pdf_bytes,
    build_professional_html,
    build_report_artifacts,
    delivery_policy,
    get_report_record,
    list_report_records,
    publish_report_record,
    verify_report_record,
)
from app.services.report_builder import build_combined_launch_report

router = APIRouter(prefix="/report", tags=["reports"])


@router.post("/combined")
async def combined_report(payload: CombinedReportRequest):
    return await build_combined_launch_report(payload)


@router.get("/delivery-policy")
def report_delivery_policy():
    return delivery_policy()


@router.post("/professional")
async def professional_report(payload: CombinedReportRequest):
    """Generate the combined report plus delivery-ready artifacts metadata.

    This endpoint does not fake manual audit claims. It only packages the real
    scanner/checklist/passive scan data provided in the request.
    """
    report = await build_combined_launch_report(payload)
    return {"report": report, "artifacts": build_report_artifacts(report)}


@router.post("/artifacts")
def report_artifacts(payload: dict[str, Any]):
    report = payload.get("report") or payload
    if not isinstance(report, dict) or not report.get("report_hash"):
        raise HTTPException(status_code=400, detail="A combined report object with report_hash is required")
    return build_report_artifacts(report)


@router.post("/export/html")
def export_html(payload: dict[str, Any]):
    report = payload.get("report") or payload
    if not isinstance(report, dict) or not report.get("report_hash"):
        raise HTTPException(status_code=400, detail="A combined report object with report_hash is required")
    return HTMLResponse(build_professional_html(report), headers={"X-Report-Id": str(report.get("report_id", ""))})


@router.post("/export/pdf")
def export_pdf(payload: dict[str, Any]):
    report = payload.get("report") or payload
    if not isinstance(report, dict) or not report.get("report_hash"):
        raise HTTPException(status_code=400, detail="A combined report object with report_hash is required")
    pdf = build_pdf_bytes(report)
    filename = f"{report.get('report_id', 'web3guard-report')}.pdf"
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-Report-Id": str(report.get("report_id", "")),
            "X-Report-Hash": str(report.get("report_hash", "")),
        },
    )


@router.post("/export/markdown")
def export_markdown(payload: dict[str, Any]):
    report = payload.get("report") or payload
    markdown = report.get("markdown_report") if isinstance(report, dict) else None
    if not markdown:
        raise HTTPException(status_code=400, detail="A combined report object with markdown_report is required")
    filename = f"{report.get('report_id', 'web3guard-report')}.md"
    return Response(
        content=markdown,
        media_type="text/markdown; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/export/json")
def export_json(payload: dict[str, Any]):
    report = payload.get("report") or payload
    if not isinstance(report, dict) or not report.get("report_hash"):
        raise HTTPException(status_code=400, detail="A combined report object with report_hash is required")
    export = report.get("json_export") or report
    filename = f"{report.get('report_id', 'web3guard-report')}.json"
    return Response(
        content=json.dumps(export, ensure_ascii=False, indent=2, default=str),
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/publication")
def publish_report(payload: dict[str, Any]):
    report = payload.get("report")
    if not isinstance(report, dict) or not report.get("report_hash"):
        raise HTTPException(status_code=400, detail="A combined report object with report_hash is required")
    visibility = payload.get("visibility", "private")
    try:
        record = publish_report_record(report, visibility=visibility, user_id=payload.get("user_id"), project_id=payload.get("project_id"))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"ok": True, "record": record, "real_only_note": "Public wording is pre-audit readiness only, not certified audit."}


@router.get("/public")
def public_report_records(include_private: bool = Query(default=False)):
    return {"reports": list_report_records(include_private=include_private)}


@router.get("/public/{public_id}")
def public_report(public_id: str, allow_private: bool = Query(default=False)):
    record = get_report_record(public_id, allow_private=allow_private)
    if not record:
        raise HTTPException(status_code=404, detail="Public report not found or private")
    return {"record": record}


@router.get("/public/{public_id}/verify")
def verify_public_report(public_id: str, report_hash: str = Query(min_length=32)):
    return verify_report_record(public_id, report_hash)


@router.get("/public/{public_id}/html")
def public_report_html(public_id: str, allow_private: bool = Query(default=False)):
    record = get_report_record(public_id, allow_private=allow_private)
    if not record:
        raise HTTPException(status_code=404, detail="Public report not found or private")
    return HTMLResponse(build_professional_html(record["report"]))


@router.get("/public/{public_id}/pdf")
def public_report_pdf(public_id: str, allow_private: bool = Query(default=False)):
    record = get_report_record(public_id, allow_private=allow_private)
    if not record:
        raise HTTPException(status_code=404, detail="Public report not found or private")
    pdf = build_pdf_bytes(record["report"])
    filename = f"{record.get('report_id', 'web3guard-report')}.pdf"
    return StreamingResponse(iter([pdf]), media_type="application/pdf", headers={"Content-Disposition": f'attachment; filename="{filename}"'})
