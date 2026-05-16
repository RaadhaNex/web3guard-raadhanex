from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.security import require_admin
from app.services.final_qa import implementation_map, launch_readiness, manual_accounts_needed, record_qa_run

router = APIRouter(prefix="/final-qa", tags=["Final Production QA"])


class QaRunCreate(BaseModel):
    actor: str = "local-admin"
    note: str = "manual QA snapshot"


@router.get("/status")
def status():
    return launch_readiness()


@router.get("/manual-accounts")
def manual_accounts():
    return {"ok": True, "accounts": manual_accounts_needed()}


@router.get("/implementation-map")
def map_implementation():
    return implementation_map()


@router.post("/run", dependencies=[Depends(require_admin)])
def run_snapshot(payload: QaRunCreate):
    return record_qa_run(payload.actor, payload.note)


alias_router = APIRouter(prefix="/production-qa", tags=["Final QA Alias"])

@alias_router.get("/status")
def alias_status():
    return launch_readiness()

@alias_router.get("/account-setup")
def alias_account_setup():
    return {"ok": True, "accounts": manual_accounts_needed()}

@alias_router.get("/implementation-map")
def alias_map():
    return implementation_map()
