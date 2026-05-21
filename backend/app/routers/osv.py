from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services.osv_checker import check_package_json_deps, check_package_osv

router = APIRouter(prefix="/osv", tags=["osv"])


class PackageCheckRequest(BaseModel):
    ecosystem: str = Field(min_length=1, max_length=60)
    name: str = Field(min_length=1, max_length=220)
    version: str | None = Field(default=None, max_length=80)


class PackageJsonRequest(BaseModel):
    package_json: str = Field(min_length=2, max_length=500_000)


@router.post("/check-package")
async def check_package(req: PackageCheckRequest):
    return await check_package_osv(req.ecosystem, req.name, req.version)


@router.post("/check-package-json")
async def check_package_json(req: PackageJsonRequest):
    return await check_package_json_deps(req.package_json)
