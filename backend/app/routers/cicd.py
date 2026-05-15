from fastapi import APIRouter

from app.models.schemas import CiConfigValidateRequest, CiTemplateRequest
from app.services.cicd import cicd_status, render_template, validate_ci_config

router = APIRouter(tags=["Mega Phase E - CI/CD"])


@router.get("/cicd/status")
def status():
    return cicd_status()


@router.post("/cicd/template")
def template(payload: CiTemplateRequest):
    return render_template(payload)


@router.post("/cicd/validate")
def validate(payload: CiConfigValidateRequest):
    return validate_ci_config(payload)
