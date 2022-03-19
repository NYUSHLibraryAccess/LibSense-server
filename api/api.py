from fastapi import APIRouter
from .config import config

router = APIRouter(prefix='/api', tags=['api'])
router.include_router(config.router)


@router.get("/test")
def get_root():
    return {"msg": "Hello WMS"}
