from .User import User
from .Orders import Orders
from fastapi import APIRouter

router = APIRouter(prefix='/v1')
router.include_router(User.router)
router.include_router(Orders.router)


@router.get("/test", summary="Test API", tags=["Test"])
def get_root():
    return {"msg": "Hello WMS"}