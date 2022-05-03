import random
from core.schema import *
from fastapi import Depends, HTTPException, APIRouter, Body, Form, Query
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


def get_tags(result_set):
    result_lst = []
    for row in result_set:
        row_dict = dict(row._mapping)
        row_dict['tags'] = Tags.split_tags(row_dict['tags'])
        if row_dict.get("cdl_flag") == 1 and "CDL" not in row_dict['tags']:
            row_dict['tags'].append("CDL")
        result_lst.append(row_dict)
    return result_lst


@router.post("/all-orders", response_model=PageableOrdersSet)
def get_all_order(body: PageableOrderRequest, db: Session = Depends(get_db)):
    page_index = body.page_index
    page_size = body.page_size
    filters = body.filters
    sorter = body.sorter

    result_set, total_records = crud.get_all_orders(db, page_index, page_size, filters=filters, sorter=sorter)
    result_lst = get_tags(result_set)
    pageable_set = {
        'page_index': page_index,
        'page_limit': page_size,
        'total_records': total_records,
        'result': result_lst
    }
    return PageableOrdersSet(**pageable_set)


@router.get("/all-orders/detail", response_model=OrderDetail)
def get_order_detail(book_id: int = Query(None, alias="bookId"), db: Session = Depends(get_db)):
    row_dict = crud.get_order_detail(db, book_id)
    (order, extra_info) = row_dict
    extra_info.tags = Tags.split_tags(extra_info.tags)
    if extra_info.cdl_flag == 1 and "CDL" not in extra_info.tags:
        extra_info.tags.append("CDL")
    return order.__dict__ | extra_info.__dict__


@router.post("/all-orders/tracking", response_model=PageableOrdersSet)
def get_overdue(body: PageableOrderRequest, db: Session = Depends(get_db)):
    page_index = body.page_index
    page_size = body.page_size
    filters = body.filters
    sorter = body.sorter

    result_set, total_records = crud.get_overdue_rush_local(db, page_index, page_size, filters=filters, sorter=sorter)
    result_lst = get_tags(result_set)

    pageable_set = {
        'page_index': page_index,
        'page_limit': page_size,
        'total_records': total_records,
        'result': result_lst
    }
    return PageableOrdersSet(**pageable_set)


@router.post("/cdl-orders", response_model=PageableCDLOrdersSet, tags=["CDL Orders"])
def get_cdl_order(body: PageableOrderRequest, db: Session = Depends(get_db)):
    page_index = body.page_index
    page_size = body.page_size
    filters = body.filters
    sorter = body.sorter

    result_set, total_records = crud.get_all_cdl(db, page_index, page_size, filters=filters, sorter=sorter)
    result_lst = get_tags(result_set)
    for idx in range(len(result_lst)):
        result_lst[idx]['cdl_item_status'] = [result_lst[idx]['cdl_item_status']]

    pageable_set = {
        'page_index': page_index,
        'page_limit': page_size,
        'total_records': total_records,
        'result': result_lst
    }
    return PageableCDLOrdersSet(**pageable_set)


@router.post("/cdl-orders/new_cdl", tags=["CDL Orders"])
def new_cdl_order(body: CDLRequest, db: Session = Depends(get_db)):
    return crud.new_cdl_order(db, body)


@router.patch("/cdl-orders", tags=["CDL Orders"])
def update_cdl_order(body: CDLRequest, db: Session = Depends(get_db)):
    return crud.update_cdl_order(db, body)


@router.delete("/cdl-orders", tags=["CDL Orders"])
def del_cdl_order(book_id: int = Query(None, alias="bookId"), db: Session = Depends(get_db)):
    return crud.del_cdl_order(db, book_id)


@router.get("/cdl-orders/detail", response_model=CDLOrderDetail, tags=["CDL Orders"])
def get_cdl_detail(book_id: int = Query(None, alias="bookId"), db: Session = Depends(get_db)):
    (cdl, order, extra_info) = crud.get_cdl_detail(db, book_id)
    cdl.cdl_item_status = [cdl.cdl_item_status]
    extra_info.tags = Tags.split_tags(extra_info.tags)
    if extra_info.cdl_flag == 1 and "CDL" not in extra_info.tags:
        extra_info.tags.append("CDL")
    return cdl.__dict__ | order.__dict__ | extra_info.__dict__


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
