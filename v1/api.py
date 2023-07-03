from .Auth import Auth
from .Data import Data
from .Order import Order
from .Vendor import Vendor
from .Report import Report
from .Preset import Preset
from.Internal import Internal
from fastapi import Body, APIRouter, Depends, HTTPException
from core import schema
from core.utils.dependencies import validate_auth
from sqlalchemy.orm import Session
from core.database.database import SessionLocal
from core.database import crud


router = APIRouter(prefix='/v1')
router.include_router(Auth.router)
router.include_router(Data.router)
router.include_router(Order.router)
router.include_router(Vendor.router)
router.include_router(Report.router)
router.include_router(Preset.router)
router.include_router(Internal.router)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/test", summary="Test API", tags=["Test"])
def get_root(body: dict = Body(...)):
    """
    Internal probe api.
    """
    if body.get("error", False):
        raise HTTPException(status_code=500)
    if body.get("badPayload", False):
        raise HTTPException(status_code=422)
    if body.get("unauthorized", False):
        raise HTTPException(status_code=401)
    return {"msg": "Hello WMS"}


@router.get("/overview", tags=["Data"], dependencies=[Depends(validate_auth)], response_model=schema.Overview)
def get_overview(db: Session = Depends(get_db)):
    local_rush_pending = crud.get_local_rush_pending(db)[0]
    cdl_pending = crud.get_cdl_pending(db)[0]
    cdl_rs, rush_nyr_rs, rush_local_rs, cdl_scan_rs = crud.get_average_days(db)
    return schema.Overview(
        local_rush_pending=local_rush_pending,
        cdl_pending=cdl_pending,

        avg_cdl=cdl_rs["avg"] or 0,
        avg_rush_nyc=rush_nyr_rs["avg"],
        avg_rush_local=rush_local_rs["avg"],

        min_cdl=cdl_rs["min"] or 0,
        min_rush_nyc=rush_nyr_rs["min"],
        min_rush_local=rush_local_rs["min"],

        max_cdl=cdl_rs["max"] or 0,
        max_rush_nyc=rush_nyr_rs["max"],
        max_rush_local=rush_local_rs["max"],

        avg_cdl_scan=cdl_scan_rs["avg"] or 0,
        max_cdl_scan=cdl_scan_rs["max"] or 0,
        min_cdl_scan=cdl_scan_rs["min"] or 0,
    )
