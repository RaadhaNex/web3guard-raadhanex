from fastapi import APIRouter, HTTPException, Query, Request

from app.models.schemas import LearningProgressCreate
from app.services.auth_guard import resolve_user_id
from app.services.learning_center import create_progress, get_lesson, learning_status, list_lessons, list_progress

router = APIRouter(tags=["Mega Phase E - Learning Center"])


@router.get("/learning/status")
def status():
    return learning_status()


@router.get("/learning/lessons")
def lessons(category: str | None = Query(default=None), language: str | None = Query(default=None)):
    return {"ok": True, "lessons": list_lessons(category=category, language=language)}


@router.get("/learning/lessons/{lesson_id}")
def lesson(lesson_id: str):
    item = get_lesson(lesson_id)
    if not item:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return {"ok": True, "lesson": item}


@router.post("/learning/progress")
def progress(payload: LearningProgressCreate, request: Request):
    user_id, auth_context = resolve_user_id(request, payload.user_id)
    try:
        return {"ok": True, "auth_context": auth_context, "progress": create_progress(payload, user_id=user_id)}
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/learning/progress")
def progress_list(request: Request, user_id: str | None = Query(default=None)):
    resolved_user_id, auth_context = resolve_user_id(request, user_id)
    return {"ok": True, "auth_context": auth_context, "progress": list_progress(user_id=resolved_user_id)}
