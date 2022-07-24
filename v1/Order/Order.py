from core.schema import *
from fastapi import Depends, APIRouter, Query, Request, Body
from sqlalchemy.orm import Session
from core.database import crud
from core.utils.dependencies import get_db, validate_auth

router = APIRouter(prefix="/orders", tags=["Order"], dependencies=[Depends(validate_auth)])


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
    fuzzy = body.fuzzy

    result_set, total_records = crud.get_all_orders(db, page_index, page_size, filters=filters, sorter=sorter,
                                                    fuzzy=fuzzy)
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
    (order, extra_info, tracking_note) = row_dict
    extra_info.tags = Tags.split_tags(extra_info.tags)
    if extra_info.cdl_flag == 1 and "CDL" not in extra_info.tags:
        extra_info.tags.append("CDL")
    return order.__dict__ | extra_info.__dict__ | tracking_note.__dict__


@router.patch("/all-orders/detail", response_model=BasicResponse)
def add_note(request: Request, body: TrackingNoteRequest, db: Session = Depends(get_db)):
    # for normal order, all other data are read-only from weekly NYC ORDER REPORT
    # only tracking note is editable

    note = TrackingNote(
        book_id=body.book_id,
        date=datetime.now(),
        taken_by=request.session['username'],
        tracking_note=body.tracking_note
    )

    if crud.get_tracking_note(db, body.book_id):
        return crud.update_tracking_note(db, note)
    else:
        return crud.add_tracking_note(db, note)


@router.post("/cdl-orders/new-cdl", tags=["CDL Orders"], response_model=BasicResponse)
def new_cdl_order(request: Request, body: CDLRequest, db: Session = Depends(get_db)):
    if body.tracking_note:
        note = TrackingNote(
            book_id=body.book_id,
            date=datetime.now(),
            taken_by=request.session['username'],
            tracking_note=body.tracking_note
        )
        crud.add_tracking_note(db, note)
    return crud.new_cdl_order(db, body)


@router.post("/cdl-orders", response_model=PageableCDLOrdersSet, tags=["CDL Orders"])
def get_cdl_order(body: PageableOrderRequest, db: Session = Depends(get_db)):
    page_index = body.page_index
    page_size = body.page_size
    filters = body.filters
    sorter = body.sorter
    fuzzy = body.fuzzy

    result_set, total_records = crud.get_all_cdl(db, page_index, page_size, filters=filters, sorter=sorter, fuzzy=fuzzy)
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


@router.delete("/cdl-orders", tags=["CDL Orders"], response_model=BasicResponse)
def del_cdl_order(book_id: int = Query(None, alias="bookId"), db: Session = Depends(get_db)):
    return crud.del_cdl_order(db, book_id)


@router.get("/cdl-orders/detail", response_model=CDLOrderDetail, tags=["CDL Orders"])
def get_cdl_detail(book_id: int = Query(None, alias="bookId"), db: Session = Depends(get_db)):
    (cdl, order, extra_info, tracking_note) = crud.get_cdl_detail(db, book_id)
    cdl.cdl_item_status = [cdl.cdl_item_status]
    extra_info.tags = Tags.split_tags(extra_info.tags)
    if extra_info.cdl_flag == 1 and "CDL" not in extra_info.tags:
        extra_info.tags.append("CDL")
    return cdl.__dict__ | order.__dict__ | extra_info.__dict__ | tracking_note.__dict__


@router.patch("/cdl-orders/detail", tags=["CDL Orders"], response_model=BasicResponse)
def update_cdl_order(request: Request, body: CDLRequest, db: Session = Depends(get_db)):
    content = body.tracking_note
    crud.update_cdl_order(db, body)
    note = TrackingNote(
        book_id=body.book_id,
        date=datetime.now(),
        taken_by=request.session['username'],
        tracking_note=content,
    )

    if crud.get_tracking_note(db, body.book_id):
        return crud.update_tracking_note(db, note)
    else:
        return crud.add_tracking_note(db, note)


@router.post("/check")
def mark_check(body: CheckedRequest, db: Session = Depends(get_db)):
    return crud.mark_order_checked(db, body.id, body.checked, body.date)


@router.post("/attention")
def mark_attention(body: AttentionRequest, db: Session = Depends(get_db)):
    return crud.mark_order_attention(db, body.id, body.attention)

