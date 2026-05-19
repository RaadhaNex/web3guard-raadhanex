from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from app.services.security_copilot import answer_prompt, build_workspace, copilot_status

router = APIRouter(prefix="/security-copilot", tags=["security-copilot"])


class CopilotPromptRequest(BaseModel):
    user_id: str = Field(default="local-demo-user", min_length=1)
    project_id: str | None = None
    question: str = Field(default="What should I fix next before launch?", max_length=1200)
    language: str = Field(default="English", max_length=40)
    include_commands: bool = True


@router.get("/status")
def status() -> dict[str, Any]:
    return copilot_status()


@router.get("/workspace")
def workspace(
    user_id: str = Query(default="local-demo-user", min_length=1),
    project_id: str | None = None,
    language: str = "English",
) -> dict[str, Any]:
    return build_workspace(user_id=user_id, project_id=project_id, language=language)


@router.post("/ask")
def ask(payload: CopilotPromptRequest) -> dict[str, Any]:
    return answer_prompt(payload.model_dump())
