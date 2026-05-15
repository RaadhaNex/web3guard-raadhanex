from fastapi import APIRouter

from app.services.payment_store import load_packages, package_with_payment

router = APIRouter(tags=["packages"])


@router.get("/packages")
def get_packages():
    return {"packages": [package_with_payment(package) for package in load_packages()]}
