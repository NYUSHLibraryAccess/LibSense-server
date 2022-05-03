from .Auth import Auth
from .Data import Data
from .User import User
from .Order import Order
from .Vendor import Vendor
from .Report import Report
from fastapi import APIRouter, Depends
from core import schema
from sqlalchemy.orm import Session
from core.database.database import SessionLocal
from core.database import crud


router = APIRouter(prefix='/v1')
router.include_router(Auth.router)
router.include_router(Data.router)
# router.include_router(User.router)
router.include_router(Order.router)
router.include_router(Vendor.router)
router.include_router(Report.router)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/test", summary="Test API", tags=["Test"])
def get_root():
    return {"msg": "Hello WMS"}


@router.get("/overview", tags=["Overview"], response_model=schema.Overview)
def get_overview(db: Session = Depends(get_db)):
    local_rush_pending = crud.get_local_rush_pending(db)[0]
    cdl_rs, rush_nyr_rs, rush_local_rs = crud.get_average_days(db)
    return schema.Overview(
        local_rush_pending=local_rush_pending,

        avg_cdl=cdl_rs["avg"],
        avg_rush_nyc=rush_nyr_rs["avg"],
        avg_rush_local=rush_local_rs["avg"],

        min_cdl=cdl_rs["min"],
        min_rush_nyc=rush_nyr_rs["min"],
        min_rush_local=rush_local_rs["min"],

        max_cdl=cdl_rs["max"],
        max_rush_nyc=rush_nyr_rs["max"],
        max_rush_local=rush_local_rs["max"],
    )
