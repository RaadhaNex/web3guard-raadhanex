from fastapi import APIRouter, HTTPException, Query, Request

from app.core.config import settings
from app.models.schemas import BugBountyProgramCreate, BugBountyProgramUpdate, BugBountySubmissionCreate, BugBountySubmissionUpdate
from app.services.auth_guard import resolve_user_id
from app.services.bug_bounty import (
    bounty_dashboard,
    bug_bounty_status,
    create_program,
    create_submission,
    get_program,
    list_programs,
    list_submissions,
    update_program,
    update_submission,
)
from app.services.rate_limit import enforce_hourly_limit

router = APIRouter(prefix="/bug-bounty", tags=["Mega Phase D - Bug Bounty"])


@router.get("/status")
def status():
    return bug_bounty_status()


@router.get("/dashboard")
def dashboard():
    return {"ok": True, "dashboard": bounty_dashboard()}


@router.post("/programs")
def create_bounty_program(payload: BugBountyProgramCreate, request: Request):
    user_id, auth_context = resolve_user_id(request, payload.user_id)
    client_host = request.client.host if request.client else "unknown"
    enforce_hourly_limit(f"bug-bounty-program:{client_host}", limit=settings.max_bug_bounty_write_per_hour)
    try:
        program = create_program(payload, user_id=user_id)
        return {"ok": True, "auth_context": auth_context, "program": program}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/programs")
def get_bounty_programs(status: str | None = Query(default=None), limit: int = Query(default=100, ge=1, le=200)):
    return {"ok": True, "programs": list_programs(status=status, limit=limit)}


@router.get("/programs/{program_id}")
def get_bounty_program(program_id: str):
    program = get_program(program_id)
    if not program:
        raise HTTPException(status_code=404, detail="Bug bounty program not found")
    return {"ok": True, "program": program}


@router.patch("/programs/{program_id}")
def patch_bounty_program(program_id: str, payload: BugBountyProgramUpdate):
    program = update_program(program_id, payload)
    if not program:
        raise HTTPException(status_code=404, detail="Bug bounty program not found")
    return {"ok": True, "program": program}


@router.post("/submissions")
def create_bounty_submission(payload: BugBountySubmissionCreate, request: Request):
    client_host = request.client.host if request.client else "unknown"
    enforce_hourly_limit(f"bug-bounty-submission:{client_host}", limit=settings.max_bug_bounty_write_per_hour)
    try:
        submission = create_submission(payload)
        return {"ok": True, "submission": submission}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/submissions")
def get_bounty_submissions(program_id: str | None = Query(default=None), status: str | None = Query(default=None), limit: int = Query(default=100, ge=1, le=200)):
    return {"ok": True, "submissions": list_submissions(program_id=program_id, status=status, limit=limit)}


@router.patch("/submissions/{submission_id}")
def patch_bounty_submission(submission_id: str, payload: BugBountySubmissionUpdate):
    submission = update_submission(submission_id, payload)
    if not submission:
        raise HTTPException(status_code=404, detail="Bug bounty submission not found")
    return {"ok": True, "submission": submission}
