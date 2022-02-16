from fastapi import APIRouter


router = APIRouter(prefix='/v1', tags=['v1'])


@router.get("/")
def get_root():
    return {"msg": "Hello WMS"}