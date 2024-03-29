import json
from datetime import datetime, timedelta
from core.schema import *
from fastapi import Depends, APIRouter, Query, Request, HTTPException
from sqlalchemy.orm import Session
from core.database import crud
from core.database.utils import convert_sqlalchemy_objs_to_dict
from core.utils.dependencies import get_db, validate_auth, validate_privilege

router = APIRouter(prefix="/orders", tags=["Order"], dependencies=[Depends(validate_auth)])


def parse_result(result_set):
    result_lst = []
    for row in result_set:
        row_dict = dict(row._mapping)
        # parse tags
        row_dict["tags"] = Tags.split_tags(row_dict["tags"])
        if row_dict.get("cdl_flag") == 1 and "CDL" not in row_dict["tags"]:
            row_dict["tags"].append("CDL")
        # parse est arrival
        if row_dict.get("notify_in", None) is not None:
            row_dict["est_arrival"] = (
                    row["created_date"]
                    + timedelta(days=row_dict["notify_in"])
            ).strftime("%Y-%m-%d")

        result_lst.append(row_dict)
    return result_lst


def compile_result(result_set, total_records, body: PageableOrderRequest):
    result_lst = parse_result(result_set)
    pageable_set = {
        "page_index": body.page_index,
        "page_limit": body.page_size,
        "total_records": total_records,
        "result": result_lst
    }
    return PageableOrdersSet(**pageable_set)


def compile_cdl_result(result_set, total_records, body: PageableOrderRequest):
    result_lst = parse_result(result_set)

    pageable_set = {
        "page_index": body.page_index,
        "page_limit": body.page_size,
        "total_records": total_records,
        "result": result_lst
    }
    return PageableCDLOrdersSet(**pageable_set)


def get_normal_orders(body: PageableOrderRequest, db: Session):
    result_set, total_records = crud.get_all_orders(db, **body.__dict__)
    return compile_result(result_set, total_records, body)


def get_cdl_orders(body: PageableOrderRequest, db: Session):
    result_set, total_records = crud.get_all_cdl(db, **body.__dict__)
    return compile_cdl_result(result_set, total_records, body)


def get_pending_cdl_orders(body: PageableOrderRequest, db: Session):
    result_set, total_records = crud.get_overdue_cdl(db, for_pandas=False, **body.__dict__)
    return compile_cdl_result(result_set, total_records, body)


def get_pending_rush_local_orders(body: PageableOrderRequest, db: Session):
    result_set, total_records = crud.get_overdue_rush_local(db, for_pandas=False, **body.__dict__)
    return compile_result(result_set, total_records, body)


@router.post("/all-orders", response_model=Union[PageableCDLOrdersSet, PageableOrdersSet])
def get_all_order(body: PageableOrderRequest, db: Session = Depends(get_db)):
    if body.views.cdl_view:
        if body.views.pending_cdl:
            return get_pending_cdl_orders(body, db)
        return get_cdl_orders(body, db)
    if body.views.pending_rush_local:
        return get_pending_rush_local_orders(body, db)
    return get_normal_orders(body, db)


@router.get("/all-orders/detail", response_model=Union[CDLOrderDetail, OrderDetail])
def get_order_detail(
        book_id: int = Query(None, alias="bookId"),
        cdl_view: bool = Query(False, alias="cdlView"),
        db: Session = Depends(get_db)
):
    if cdl_view:
        (cdl, order, extra_info, tracking_note) = crud.get_cdl_detail(db, book_id)
    else:
        (order, extra_info, tracking_note, vendor) = crud.get_order_detail(db, book_id)
        # vendor could not have been added to system for new orders.
        if vendor and vendor.notify_in:
            order.est_arrival = order.created_date + timedelta(days=vendor.notify_in)

    extra_info.tags = Tags.split_tags(extra_info.tags)
    if extra_info.cdl_flag == 1 and "CDL" not in extra_info.tags:
        extra_info.tags.append("CDL")

    if cdl_view:
        return convert_sqlalchemy_objs_to_dict(cdl, order, extra_info, tracking_note)

    return convert_sqlalchemy_objs_to_dict(order, extra_info, tracking_note)


@router.patch("/all-orders/detail", response_model=BasicResponse, dependencies=[Depends(validate_privilege)])
def update_order(request: Request, body: PatchOrderRequest, db: Session = Depends(get_db)):
    # Full upload. Null is treated as set NULL.
    if body.cdl:
        (cdl, order, extra_info, tracking_note) = crud.get_cdl_detail(db, body.book_id)
    else:
        (order, extra_info, tracking_note, vendor) = crud.get_order_detail(db, body.book_id)

    crud.update_normal_order(db, body)
    try:
        if body.sensitive != ("Sensitive" in extra_info.tags):
            if body.sensitive is True:
                crud.mark_sensitive(db, body.book_id)
            elif body.sensitive is False:
                crud.cancel_sensitive(db, body.book_id)

        if body.check_anyway != extra_info.check_anyway:
            crud.check_anyway(db, body.book_id, body.check_anyway)

    except LibSenseException as err:
        raise HTTPException(status_code=500, detail=err.message)

    if body.cdl:
        if crud.get_cdl_detail(db, body.book_id):
            crud.update_cdl_order(db, body)
        else:
            raise HTTPException(
                status_code=500,
                detail="Incorrect CDL request body. Did you try to update a normal order?"
            )
    if tracking_note is not None:
        if tracking_note.tracking_note != body.tracking_note:
            if body.tracking_note is None:
                crud.delete_tracking_note(db, body.book_id)
            else:
                note = TrackingNote(
                    book_id=body.book_id,
                    date=datetime.now(),
                    taken_by=request.session["username"],
                    tracking_note=body.tracking_note
                )
                crud.update_tracking_note(db, note)
    else:
        if body.tracking_note is not None:
            note = TrackingNote(
                book_id=body.book_id,
                date=datetime.now(),
                taken_by=request.session["username"],
                tracking_note=body.tracking_note
            )
            crud.add_tracking_note(db, note)

    return BasicResponse(msg="Success")


@router.post("/cdl", tags=["CDL Orders"], response_model=BasicResponse, dependencies=[Depends(validate_privilege)])
def new_cdl_order(body: NewCDLRequest, db: Session = Depends(get_db)):
    return crud.new_cdl_order(db, body)


@router.delete("/cdl", tags=["CDL Orders"], response_model=BasicResponse, dependencies=[Depends(validate_privilege)])
def del_cdl_order(book_id: int = Query(None, alias="bookId"), db: Session = Depends(get_db)):
    return crud.del_cdl_order(db, book_id)


@router.post("/cdl/reset-vendor-date",
             tags=["CDL Orders"],
             response_model=BasicResponse,
             dependencies=[Depends(validate_privilege)])
def reset_cdl_vendor_date(body: UpdateCDLVendorDateRequest):
    with open("configs/config.json") as f:
        config = json.loads(f.read())
    config["cdl_config"]["vendor_start_date"] = str(body.date)
    with open("configs/config.json", "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)
    return BasicResponse(msg="Success")


@router.post("/check")
def mark_check(body: CheckedRequest, db: Session = Depends(get_db)):
    return crud.mark_order_checked(db, body.id, body.checked, body.date)


@router.post("/attention")
def mark_attention(body: AttentionRequest, db: Session = Depends(get_db)):
    return crud.mark_order_attention(db, body.id, body.attention)
