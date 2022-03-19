from fastapi import APIRouter, Request

router = APIRouter(prefix='/config', tags=['config'])


@router.get("/openapi")
def get_openapi(request: Request):
    api_json = request.app.openapi()
    return api_json
