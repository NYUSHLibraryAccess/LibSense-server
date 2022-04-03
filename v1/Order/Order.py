from core.models import PageableOrdersSet, PageableCDLOrdersSet, TimelineNote, Order, CDLOrder
from fastapi import Depends, HTTPException, APIRouter
from datetime import date
from typing import Optional
from sqlalchemy.orm import Session
from core.database import crud, schema
from core.database.database import SessionLocal, engine

router = APIRouter(prefix="/orders", tags=["Order"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/all-orders", response_model=PageableOrdersSet)
def get_all_order(page_index: Optional[int] = None, page_size: Optional[int] = None,
                        db: Session = Depends(get_db)):
    result_set, total_records = crud.get_all_orders(db, page_index, page_size)
    pageable_set = {
        'page_index': page_index,
        'page_limit': page_size,
        'total_pages': total_records // page_size,
        'result': result_set
    }
    return PageableOrdersSet(**pageable_set)


@router.get("/cdl-order", response_model=PageableCDLOrdersSet, tags=["CDL Order"])
async def get_cdl_order(page_index: Optional[int] = None, page_size: Optional[int] = None):
    return True


@router.patch("/general-order")
async def update_general_order(net_id: str, order: Order):
    return True


@router.patch("/cdl-order", tags=["CDL Order"])
async def update_cdl_order(net_id: str, cdl_order: CDLOrder):
    return True


@router.patch("/add-note")
async def add_note(net_id: str, uuid: str, note: TimelineNote):
    return True
