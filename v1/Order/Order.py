import json
from core.schema import *
from fastapi import Body, Depends, APIRouter, Query, Request, HTTPException
from sqlalchemy.orm import Session
from core.database import crud
from core.database.utils import convert_sqlalchemy_objs_to_dict
from core.utils.dependencies import get_db, validate_auth

router = APIRouter(prefix="/orders", tags=["Order"], dependencies=[Depends(validate_auth)])


def get_tags(result_set):
    result_lst = []
    for row in result_set:
        row_dict = dict(row._mapping)
        row_dict["tags"] = Tags.split_tags(row_dict["tags"])
        if row_dict.get("cdl_flag") == 1 and "CDL" not in row_dict["tags"]:
            row_dict["tags"].append("CDL")
        result_lst.append(row_dict)
    return result_lst


def compile_result(result_set, total_records, body: PageableOrderRequest):
    result_lst = get_tags(result_set)
    pageable_set = {
        "page_index": body.page_index,
        "page_limit": body.page_size,
        "total_records": total_records,
        "result": result_lst
    }
    return PageableOrdersSet(**pageable_set)


def compile_cdl_result(result_set, total_records, body: PageableOrderRequest):
    result_lst = get_tags(result_set)
    for idx in range(len(result_lst)):
        result_lst[idx]["cdl_item_status"] = result_lst[idx]["cdl_item_status"]

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


def update_or_add_note(note, body: PatchOrderRequest, db: Session):
    if crud.get_tracking_note(db, body.book_id):
        return crud.update_tracking_note(db, note)

    return crud.add_tracking_note(db, note)


@router.post("/all-orders",
             response_model=Union[PageableCDLOrdersSet, PageableOrdersSet],
             response_model_exclude_unset=True)
def get_all_order(body: PageableOrderRequest, db: Session = Depends(get_db)):
    if body.views.cdl_view:
        return get_cdl_orders(body, db)
    if body.views.pending_rush_local:
        return get_pending_rush_local_orders(body, db)
    if body.views.pending_cdl:
        return get_pending_cdl_orders(body, db)
    return get_normal_orders(body, db)


@router.get("/all-orders/detail",
            response_model=Union[CDLOrderDetail, OrderDetail],
            response_model_exclude_unset=True)
def get_order_detail(
        book_id: int = Query(None, alias="bookId"),
        cdl_view: bool = Query(False, alias="cdlView"),
        db: Session = Depends(get_db)
):
    if cdl_view:
        (cdl, order, extra_info, tracking_note) = crud.get_cdl_detail(db, book_id)
        cdl.cdl_item_status = [cdl.cdl_item_status]
    else:
        (order, extra_info, tracking_note) = crud.get_order_detail(db, book_id)

    extra_info.tags = Tags.split_tags(extra_info.tags)
    if extra_info.cdl_flag == 1 and "CDL" not in extra_info.tags:
        extra_info.tags.append("CDL")

    if cdl_view:
        return convert_sqlalchemy_objs_to_dict(cdl, order, extra_info, tracking_note)

    return convert_sqlalchemy_objs_to_dict(order, extra_info, tracking_note)


@router.patch("/all-orders/detail", response_model=BasicResponse)
def update_order(request: Request, body: PatchOrderRequest, db: Session = Depends(get_db)):
    crud.update_normal_order(db, body)
    if body.cdl:
        if crud.get_cdl_detail(db, body.book_id):
            crud.update_cdl_order(db, body)
        else:
            raise HTTPException(
                status_code=500,
                detail="Incorrect CDL request body. Did you try to update a normal order?"
            )

    note = TrackingNote(
        book_id=body.book_id,
        date=datetime.now(),
        taken_by=request.session["username"],
        tracking_note=body.tracking_note
    )
    update_or_add_note(note, body, db)

    return BasicResponse(msg="Success")


@router.post("/cdl", tags=["CDL Orders"], response_model=BasicResponse)
def new_cdl_order(request: Request, body: PatchOrderRequest, db: Session = Depends(get_db)):
    if body.cdl is not None:
        if body.tracking_note:
            note = TrackingNote(
                book_id=body.book_id,
                date=datetime.now(),
                taken_by=request.session["username"],
                tracking_note=body.tracking_note
            )
            crud.add_tracking_note(db, note)
        return crud.new_cdl_order(db, body)

    raise HTTPException(status_code=400, detail="Failed to create CDL order.")


@router.delete("/cdl", tags=["CDL Orders"], response_model=BasicResponse)
def del_cdl_order(book_id: int = Query(None, alias="bookId"), db: Session = Depends(get_db)):
    return crud.del_cdl_order(db, book_id)


@router.post("/cdl/reset-vendor-date", tags=["CDL Orders"], response_model=BasicResponse)
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
