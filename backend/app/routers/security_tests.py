from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body

from app.services.security_tests import generate_security_test_pack, security_tests_status

router = APIRouter(prefix="/security-tests", tags=["security-tests"])


@router.get("/status")
def status():
    return security_tests_status()


@router.post("/generate")
def generate(payload: dict[str, Any] = Body(default_factory=dict)):
    return generate_security_test_pack(payload)
