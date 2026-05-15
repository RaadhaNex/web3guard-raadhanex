from fastapi import APIRouter
from app.services.local_qa import ESSENTIAL_BACKEND_ENDPOINTS, ESSENTIAL_FRONTEND_ROUTES, qa_runbook, validate_environment

router = APIRouter(prefix="/qa", tags=["local-qa"])


@router.get("/status")
def qa_status():
    return validate_environment()


@router.get("/runbook")
def runbook():
    return qa_runbook()


@router.get("/frontend-routes")
def frontend_routes():
    return {"routes": ESSENTIAL_FRONTEND_ROUTES}


@router.get("/backend-endpoints")
def backend_endpoints():
    return {"endpoints": ESSENTIAL_BACKEND_ENDPOINTS}
