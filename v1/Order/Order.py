import random
from core.schema import *
from fastapi import Depends, HTTPException, APIRouter, Body, Form
from datetime import date
from typing import Optional
from sqlalchemy.orm import Session
from core.database import crud, model
from core.database.database import SessionLocal, engine

router = APIRouter(prefix="/orders", tags=["Order"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/all-orders", response_model=PageableOrdersSet)
def get_all_order(body: PageableOrderRequest, db: Session = Depends(get_db)):
    page_index = body.page_index
    page_size = body.page_size
    filters = body.filters
    sorter = body.sorter

    result_set, total_records = crud.get_all_orders(db, page_index, page_size, filters=filters, sorter=sorter)
    result_lst = []

    for row in result_set:
        row_dict = dict(row._mapping)
        row_dict['tags'] = Tags.split_tags(row_dict['tags'])
        result_lst.append(row_dict)

    pageable_set = {
        'page_index': page_index,
        'page_limit': page_size,
        'total_records': total_records,
        'result': result_lst
    }
    return PageableOrdersSet(**pageable_set)


@router.get("/all-orders/detail", response_model=OrderDetail)
def get_order_detail(order_id: int, db: Session = Depends(get_db)):
    row_dict = crud.get_order_detail(db, order_id).__dict__
    row_dict['tags'] = [random.choice(list(Tags))]
    return row_dict


@router.post("/all-orders/tracking", response_model=PageableOrdersSet)
def get_overdue(body: PageableOrderRequest, db: Session = Depends(get_db)):
    page_index = body.page_index
    page_size = body.page_size
    filters = body.filters
    sorter = body.sorter

    result_set, total_records = crud.get_overdue_rush_local(db, page_index, page_size, filters=filters, sorter=sorter)
    result_lst = []

    for row in result_set:
        row_dict = dict(row._mapping)
        row_dict['tags'] = Tags.split_tags(row_dict['tags'])
        result_lst.append(row_dict)

    pageable_set = {
        'page_index': page_index,
        'page_limit': page_size,
        'total_records': total_records,
        'result': result_lst
    }
    return PageableOrdersSet(**pageable_set)


@router.post("/cdl-orders", response_model=PageableCDLOrdersSet, tags=["CDL Order"])
def get_cdl_order(body: PageableOrderRequest, db: Session = Depends(get_db)):
    page_index = body.page_index
    page_size = body.page_size
    filters = body.filters
    sorter = body.sorter

    result_set, total_records = crud.get_all_cdl(db, page_index, page_size, filters=filters, sorter=sorter)
    result_lst = []

    for row in result_set:
        row_dict = dict(row._mapping)
        row_dict['tags'] = Tags.split_tags(row_dict['tags'])
        result_lst.append(row_dict)

    pageable_set = {
        'page_index': page_index,
        'page_limit': page_size,
        'total_records': total_records,
        'result': result_lst
    }
    return PageableCDLOrdersSet(**pageable_set)


@router.patch("/general-order")
def update_general_order(net_id: str, order: Order):
    return True


@router.patch("/cdl-order", tags=["CDL Order"])
async def update_cdl_order(net_id: str, cdl_order: CDLOrder):
    return True


@router.post("/add-note")
def add_note(net_id: str = Form(...),
             book_id: str = Form(...),
             content: str = Form(...),
             db: Session = Depends(get_db)):
    note = TimelineNote(
        book_id=book_id,
        date=datetime.now(),
        taken_by=net_id,
        content=content,
    )
    return crud.add_tracking_note(db, note)
