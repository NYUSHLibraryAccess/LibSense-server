from .User import User
from fastapi import APIRouter

router = APIRouter(prefix='/v1')
router.include_router(User.router)


@router.get("/test", summary="Test API", tags=["Test"])
def get_root():
    return {"msg": "Hello WMS"}