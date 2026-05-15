from fastapi import APIRouter
from app.services.launch_pack import launch_pack

router = APIRouter(prefix="/launch", tags=["launch-pack"])


@router.get("/pack")
def get_launch_pack():
    return launch_pack()
