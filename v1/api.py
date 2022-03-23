from .User import User
from .Order import Order
from .Vendor import Vendor
from fastapi import APIRouter

router = APIRouter(prefix='/v1')
router.include_router(User.router)
router.include_router(Order.router)
router.include_router(Vendor.router)


@router.get("/test", summary="Test API", tags=["Test"])
def get_root():
    return {"msg": "Hello WMS"}