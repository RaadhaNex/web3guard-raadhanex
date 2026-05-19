from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.security import require_admin
from app.services.final_launch_completion import external_provider_status, final_completion_summary, next_chat_handoff_text, remaining_work_items
from app.services.final_qa import final_launch_checklist, implementation_map, launch_readiness, manual_accounts_needed, record_qa_run

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


@router.get("/final-checklist")
def final_checklist():
    return {"ok": True, "checklist": final_launch_checklist()}


@router.get("/implementation-map")
def map_implementation():
    return implementation_map()


@router.get("/remaining-work")
def remaining_work():
    return {"ok": True, "remaining_work": remaining_work_items()}


@router.get("/external-providers")
def external_providers():
    return external_provider_status()


@router.get("/completion-summary")
def completion_summary():
    return final_completion_summary()


@router.get("/next-chat-handoff")
def next_chat_handoff():
    return {"ok": True, "handoff": next_chat_handoff_text()}


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


@alias_router.get("/final-checklist")
def alias_final_checklist():
    return {"ok": True, "checklist": final_launch_checklist()}


@alias_router.get("/implementation-map")
def alias_map():
    return implementation_map()


@alias_router.get("/remaining-work")
def alias_remaining_work():
    return {"ok": True, "remaining_work": remaining_work_items()}


@alias_router.get("/external-providers")
def alias_external_providers():
    return external_provider_status()


@alias_router.get("/completion-summary")
def alias_completion_summary():
    return final_completion_summary()
