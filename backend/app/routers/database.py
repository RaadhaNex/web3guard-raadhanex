from __future__ import annotations

import json

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, Response

from app.models.schemas import (
    ProjectCreate,
    ProjectUpdate,
    SavedReportCreate,
    SavedReportUpdate,
    ScanHistoryCreate,
    ScanHistoryUpdate,
    UserProfileUpsert,
)
from app.services.auth_guard import auth_runtime_status, resolve_user_id
from app.services.dashboard_report_export import (
    build_professional_report_from_saved,
    build_saved_report_create_from_scan,
)
from app.services.professional_report import build_pdf_bytes, build_professional_html
from app.services.database_store import (
    PHASE7_REAL_ONLY_NOTE,
    create_project,
    dashboard_overview,
    db_status,
    get_report,
    get_scan,
    list_projects,
    list_reports,
    list_scans,
    project_detail,
    save_report,
    save_scan,
    update_project,
    update_report,
    update_scan,
    upsert_profile,
)

router = APIRouter(tags=["Web3Guard Database + Dashboard"])


@router.get("/db/status")
def get_database_status():
    return db_status()


@router.get("/auth/status")
def get_auth_status():
    return auth_runtime_status()


@router.post("/profile")
def save_profile(request: Request, payload: UserProfileUpsert):
    resolved_user_id, auth_context = resolve_user_id(request, payload.id)
    profile = upsert_profile(payload.model_copy(update={"id": resolved_user_id}))
    return {"ok": True, "auth_context": auth_context, "profile": profile, "real_only_note": PHASE7_REAL_ONLY_NOTE}


@router.get("/dashboard/overview")
def get_dashboard_overview(request: Request, user_id: str | None = Query(default=None, max_length=120)):
    resolved_user_id, auth_context = resolve_user_id(request, user_id)
    overview = dashboard_overview(resolved_user_id)
    return {"ok": True, "auth_context": auth_context, "overview": overview}


@router.post("/projects")
def create_project_record(request: Request, payload: ProjectCreate):
    resolved_user_id, auth_context = resolve_user_id(request, payload.user_id)
    project = create_project(resolved_user_id, payload)
    return {"ok": True, "auth_context": auth_context, "project": project, "real_only_note": PHASE7_REAL_ONLY_NOTE}


@router.get("/projects")
def list_project_records(
    request: Request,
    user_id: str | None = Query(default=None, max_length=120),
    limit: int = Query(default=25, ge=1, le=100),
):
    resolved_user_id, auth_context = resolve_user_id(request, user_id)
    projects = list_projects(resolved_user_id, limit=limit)
    return {"ok": True, "auth_context": auth_context, "projects": projects}


@router.get("/projects/{project_id}")
def get_project_record(request: Request, project_id: str, user_id: str | None = Query(default=None, max_length=120)):
    resolved_user_id, auth_context = resolve_user_id(request, user_id)
    detail = project_detail(resolved_user_id, project_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="Project not found for this user")
    return {"ok": True, "auth_context": auth_context, "detail": detail}


@router.patch("/projects/{project_id}")
def update_project_record(request: Request, project_id: str, payload: ProjectUpdate, user_id: str | None = Query(default=None, max_length=120)):
    resolved_user_id, auth_context = resolve_user_id(request, user_id)
    project = update_project(resolved_user_id, project_id, payload)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found for this user")
    return {"ok": True, "auth_context": auth_context, "project": project}


@router.post("/scan-history")
def create_scan_history_record(request: Request, payload: ScanHistoryCreate):
    resolved_user_id, auth_context = resolve_user_id(request, payload.user_id)
    scan = save_scan(resolved_user_id, payload)
    return {"ok": True, "auth_context": auth_context, "scan": scan, "real_only_note": PHASE7_REAL_ONLY_NOTE}


@router.get("/scan-history")
def list_scan_history_records(
    request: Request,
    user_id: str | None = Query(default=None, max_length=120),
    project_id: str | None = Query(default=None, max_length=120),
    limit: int = Query(default=25, ge=1, le=100),
):
    resolved_user_id, auth_context = resolve_user_id(request, user_id)
    scans = list_scans(resolved_user_id, limit=limit, project_id=project_id)
    return {"ok": True, "auth_context": auth_context, "scans": scans}


@router.get("/scan-history/{scan_id}")
def get_scan_history_record(request: Request, scan_id: str, user_id: str | None = Query(default=None, max_length=120)):
    resolved_user_id, auth_context = resolve_user_id(request, user_id)
    scan = get_scan(resolved_user_id, scan_id)
    if scan is None:
        raise HTTPException(status_code=404, detail="Scan not found for this user")
    return {"ok": True, "auth_context": auth_context, "scan": scan}


@router.patch("/scan-history/{scan_id}")
def update_scan_history_record(request: Request, scan_id: str, payload: ScanHistoryUpdate, user_id: str | None = Query(default=None, max_length=120)):
    resolved_user_id, auth_context = resolve_user_id(request, user_id)
    scan = update_scan(resolved_user_id, scan_id, payload)
    if scan is None:
        raise HTTPException(status_code=404, detail="Scan not found for this user")
    return {"ok": True, "auth_context": auth_context, "scan": scan}


@router.post("/saved-reports")
def create_saved_report_record(request: Request, payload: SavedReportCreate):
    resolved_user_id, auth_context = resolve_user_id(request, payload.user_id)
    report = save_report(resolved_user_id, payload)
    return {"ok": True, "auth_context": auth_context, "report": report, "real_only_note": PHASE7_REAL_ONLY_NOTE}


@router.get("/saved-reports")
def list_saved_report_records(
    request: Request,
    user_id: str | None = Query(default=None, max_length=120),
    project_id: str | None = Query(default=None, max_length=120),
    limit: int = Query(default=25, ge=1, le=100),
):
    resolved_user_id, auth_context = resolve_user_id(request, user_id)
    reports = list_reports(resolved_user_id, limit=limit, project_id=project_id)
    return {"ok": True, "auth_context": auth_context, "reports": reports}


@router.get("/saved-reports/{saved_report_id}")
def get_saved_report_record(request: Request, saved_report_id: str, user_id: str | None = Query(default=None, max_length=120)):
    resolved_user_id, auth_context = resolve_user_id(request, user_id)
    report = get_report(resolved_user_id, saved_report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found for this user")
    return {"ok": True, "auth_context": auth_context, "report": report}


@router.patch("/saved-reports/{saved_report_id}")
def update_saved_report_record(request: Request, saved_report_id: str, payload: SavedReportUpdate, user_id: str | None = Query(default=None, max_length=120)):
    resolved_user_id, auth_context = resolve_user_id(request, user_id)
    report = update_report(resolved_user_id, saved_report_id, payload)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found for this user")
    return {"ok": True, "auth_context": auth_context, "report": report}



@router.post("/scan-history/{scan_id}/saved-report")
def create_saved_report_from_scan_record(
    request: Request,
    scan_id: str,
    title: str | None = Query(default=None, max_length=220),
    user_id: str | None = Query(default=None, max_length=120),
):
    """Create a real saved report record from a scan owned by the authenticated user.

    This endpoint never creates a fake report. It only packages an existing
    saved scan payload for professional export/download.
    """

    resolved_user_id, auth_context = resolve_user_id(request, user_id)
    scan = get_scan(resolved_user_id, scan_id)
    if scan is None:
        raise HTTPException(status_code=404, detail="Scan not found for this user")

    saved_report_payload = build_saved_report_create_from_scan(scan, title=title)
    report = save_report(resolved_user_id, saved_report_payload)
    return {
        "ok": True,
        "auth_context": auth_context,
        "report": report,
        "real_only_note": "Report was created from an existing saved scan owned by this user. Not a certified audit.",
    }


@router.get("/saved-reports/{saved_report_id}/export/{export_format}")
def export_saved_report_record(
    request: Request,
    saved_report_id: str,
    export_format: str,
    user_id: str | None = Query(default=None, max_length=120),
):
    """Export an authenticated user's saved report as PDF/HTML/Markdown/JSON.

    Ownership is enforced with the same resolved user id used by the dashboard
    record endpoints. Unknown or cross-user records return 404.
    """

    resolved_user_id, _auth_context = resolve_user_id(request, user_id)
    saved_report = get_report(resolved_user_id, saved_report_id)
    if saved_report is None:
        raise HTTPException(status_code=404, detail="Report not found for this user")

    report = build_professional_report_from_saved(saved_report)
    filename_base = str(report.get("report_id") or saved_report_id).replace("/", "-")

    if export_format == "html":
        return HTMLResponse(
            build_professional_html(report),
            headers={"Content-Disposition": f'attachment; filename="{filename_base}.html"'},
        )

    if export_format == "pdf":
        return Response(
            content=build_pdf_bytes(report),
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename_base}.pdf"'},
        )

    if export_format in {"md", "markdown"}:
        return Response(
            content=report.get("markdown_report", ""),
            media_type="text/markdown; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="{filename_base}.md"'},
        )

    if export_format == "json":
        return Response(
            content=json.dumps(report.get("json_export") or report, ensure_ascii=False, indent=2, default=str),
            media_type="application/json",
            headers={"Content-Disposition": f'attachment; filename="{filename_base}.json"'},
        )

    raise HTTPException(status_code=400, detail="export_format must be one of: pdf, html, markdown, md, json")
