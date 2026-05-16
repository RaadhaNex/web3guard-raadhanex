from fastapi import APIRouter, Query, Request

from app.models.schemas import NotificationPreferenceCreate, NotificationSendRequest
from app.services.auth_guard import resolve_user_id
from app.services.notification_center import create_preference, list_events, list_preferences, notification_status, send_notification

router = APIRouter(tags=["Notifications"])


@router.get("/notifications/status")
def status():
    return notification_status()


@router.post("/notifications/preferences")
def create_preferences(payload: NotificationPreferenceCreate, request: Request):
    user_id, auth_context = resolve_user_id(request, payload.user_id)
    return {"ok": True, "auth_context": auth_context, "preference": create_preference(payload, user_id)}


@router.get("/notifications/preferences")
def preferences(request: Request, user_id: str | None = Query(default=None)):
    resolved_user_id, auth_context = resolve_user_id(request, user_id)
    return {"ok": True, "auth_context": auth_context, "preferences": list_preferences(resolved_user_id)}


@router.post("/notifications/send")
def send(payload: NotificationSendRequest, request: Request):
    user_id, auth_context = resolve_user_id(request, payload.user_id)
    return {"ok": True, "auth_context": auth_context, "event": send_notification(payload, user_id)}


@router.get("/notifications/events")
def events(limit: int = Query(default=100, ge=1, le=500)):
    return {"ok": True, "events": list_events(limit=limit)}
