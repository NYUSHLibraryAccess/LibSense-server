import json
import pandas as pd
from tqdm import tqdm
from sqlalchemy import text, func, insert, and_, delete
from sqlalchemy.orm import Session

from core import schema
from core.database.utils import compile_query
from core.database.model import Order, ExtraInfo, TrackingNote, CDLOrder, User, Vendor, Preset, SensitiveBarcode


def login(db: Session, username, password):
    return (
        db.query(User).filter(User.username == username).filter(User.password == password).first()
    )


def add_user(db: Session, new_user: schema.NewSystemUser):
    user = User(**new_user.__dict__)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def all_users(db: Session):
    return db.query(User.username, User.role).all()


def delete_user(db: Session, username):
    user = db.query(User).filter(User.username == username).first()
    db.delete(user)
    db.commit()
    return schema.BasicResponse(msg="Success")


def get_overdue_rush_local(
        db: Session,
        page_index: int = 0,
        page_size: int = 10,
        filters=None,
        sorter=None,
        for_pandas=False,
        **kwargs,
):
    if filters is None:
        filters = []
    args = [
        *Order.__table__.c,
        *ExtraInfo.__table__.c,
        TrackingNote.tracking_note,
    ]
    query = (
        db.query(*args)
        .join(ExtraInfo, Order.id == ExtraInfo.id)
        .join(Vendor, Order.vendor_code == Vendor.vendor_code)
        .join(TrackingNote, Order.id == TrackingNote.book_id, isouter=True)
        .filter(ExtraInfo.tags.like("%%[Rush]%%"))
        .filter(ExtraInfo.tags.like("%%[Local]%%"))
        # .filter(Order.arrival_date == None)
        # .filter(Order.order_status != "VC")
    )
    table_mapping = {
        "ExtraInfo": ["tags", "checked", "attention"],
        "TrackingNote": ["tracking_note"],
        "default": "Order",
    }

    # when should a local-rush order be checked?
    # when user marked order as check_anyway, or the order takes longer to arrive
    # and the order hasn't been checked yet,or the override time also has been exceeded

    suffix = text(
        """(extra_info.check_anyway = 1 or (
          nyc_orders.arrival_date is null
          and nyc_orders.order_status != 'VC' 
          and DATEDIFF(current_timestamp(), nyc_orders.created_date) > vendors.notify_in
          and (extra_info.checked = 0 or (extra_info.override_reminder_time is not null
            and current_timestamp() > extra_info.override_reminder_time))))
        """.replace("\n", " "))

    # fixed_filters = [schema.FieldFilter(op="in", col="tags", val=["Rush", "Local"])]
    # filters.extend(fixed_filters)

    query, total_records = compile_query(
        query, filters, table_mapping, sorter, Order.id, page_index, page_size, suffix
    )

    if for_pandas:
        return query.statement

    return query.all(), page_index * page_size + total_records if total_records != 0 else 0


def get_overdue_cdl(
        db: Session,
        page_index: int = 0,
        page_size: int = 10,
        filters=None,
        sorter=None,
        for_pandas=False,
        **kwargs,
):
    args = [
        *CDLOrder.__table__.c,
        *Order.__table__.c,
        *ExtraInfo.__table__.c,
        TrackingNote.tracking_note,
    ]
    table_mapping = {
        "CDLOrder": [
            "cdl_item_status",
            "order_request_date",
            "scanning_vendor_payment_date",
            "pdf_delivery_date",
            "back_to_karms_date",
        ],
        "ExtraInfo": ["tags", "checked", "attention"],
        "TrackingNote": ["tracking_note"],
        "default": "Order",
    }

    avg_days = get_cdl_scan_stats(db)["avg"]

    query = (
        db.query(*args)
        .join(Order, CDLOrder.book_id == Order.id)
        .join(ExtraInfo, CDLOrder.book_id == ExtraInfo.id)
        .join(TrackingNote, Order.id == TrackingNote.book_id, isouter=True)
    )

    # override_reminder_time != 0 implicitly indicated checked = 1
    suffix = text(
        """(extra_info.check_anyway = 1 or 
        (cdl_info.pdf_delivery_date is null 
        and datediff(current_timestamp(), cdl_info.order_request_date) > %d
        and (extra_info.checked = 0 or (extra_info.override_reminder_time is not null
        and CURRENT_TIMESTAMP() > extra_info.override_reminder_time))))""" % (avg_days or 0)
    )

    query, total_records = compile_query(
        query, filters, table_mapping, sorter, Order.id, page_index, page_size, suffix
    )

    if for_pandas:
        return query.statement

    return query.all(), page_index * page_size + total_records if total_records != 0 else 0


def get_sh_order_report(
        db: Session,
        page_index: int = 0,
        page_size: int = 10,
        filters=None,
        sorter=None,
        for_pandas=False,
        **kwargs,
):
    if filters is None:
        filters = []
    args = [
        *Order.__table__.c,
        *ExtraInfo.__table__.c,
        TrackingNote.tracking_note,
    ]
    query = (
        db.query(*args)
        .join(ExtraInfo, Order.id == ExtraInfo.id)
        .join(TrackingNote, Order.id == TrackingNote.book_id, isouter=True)
    )
    table_mapping = {
        "ExtraInfo": ["tags", "checked", "attention"],
        "TrackingNote": ["tracking_note"],
        "default": "Order",
    }
    suffix = text("""datediff(current_timestamp(), created_date) <= 1095""")
    fixed_filters = [
        schema.FieldFilter(op="like", col="sublibrary", val="NSHNG"),
        schema.FieldFilter(op="like", col="order_type", val="M"),
    ]
    fixed_sorter = schema.SortCol(col="created_date", desc=True)
    filters.extend(fixed_filters)
    sorter = sorter or fixed_sorter
    query, total_records = compile_query(
        query, filters, table_mapping, sorter, Order.id, page_index, page_size, suffix
    )

    if for_pandas:
        return query.statement

    return query.all(), page_index * page_size + total_records if total_records != 0 else 0


def get_all_orders(
        db: Session,
        page_index: int = 0,
        page_size: int = 10,
        filters=None,
        sorter=None,
        fuzzy=None,
        **kwargs,
):
    args = [
        *Order.__table__.c,
        *ExtraInfo.__table__.c,
        TrackingNote.tracking_note,
    ]
    query = (
        db.query(*args)
        .join(ExtraInfo, Order.id == ExtraInfo.id, isouter=True)
        .join(TrackingNote, Order.id == TrackingNote.book_id, isouter=True)
    )
    table_mapping = {
        "ExtraInfo": ["tags", "checked", "attention"],
        "TrackingNote": ["tracking_note"],
        "default": "Order",
    }
    fuzzy_cols = [Order.barcode, Order.bsn, Order.library_note, Order.title, Order.order_number]
    query, total_records = compile_query(
        query,
        filters,
        table_mapping,
        sorter,
        Order.id,
        page_index,
        page_size,
        fuzzy=fuzzy,
        fuzzy_cols=fuzzy_cols,
    )
    return query.all(), page_index * page_size + total_records if total_records != 0 else 0


def get_order_detail(db: Session, book_id: int):
    query = (
        db.query(Order, ExtraInfo, TrackingNote)
        .join(ExtraInfo, Order.id == ExtraInfo.id, isouter=True)
        .join(TrackingNote, Order.id == TrackingNote.book_id, isouter=True)
        .filter(Order.id == book_id)
        .first()
    )
    return query


def get_all_cdl(
        db: Session,
        page_index: int = 0,
        page_size: int = 10,
        filters=None,
        sorter=None,
        fuzzy=None,
        **kwargs,
):
    args = [
        *CDLOrder.__table__.c,
        *Order.__table__.c,
        *ExtraInfo.__table__.c,
        TrackingNote.tracking_note,
    ]
    query = (
        db.query(*args)
        .join(Order, CDLOrder.book_id == Order.id)
        .join(ExtraInfo, ExtraInfo.id == Order.id, isouter=True)
        .join(TrackingNote, TrackingNote.book_id == Order.id, isouter=True)
    )
    table_mapping = {
        "ExtraInfo": ["tags", "checked", "attention"],
        "TrackingNote": ["tracking_note"],
        "CDLOrder": [
            "cdl_item_status",
            "order_request_date",
            "scanning_vendor_payment_date",
            "pdf_delivery_date",
            "circ_pdf_url",
            "back_to_karms_date",
        ],
        "default": "Order",
    }
    fuzzy_cols = [Order.barcode, Order.bsn, Order.library_note, Order.title, Order.order_number]
    query, total_records = compile_query(
        query,
        filters,
        table_mapping,
        sorter,
        Order.id,
        page_index,
        page_size,
        fuzzy=fuzzy,
        fuzzy_cols=fuzzy_cols,
    )
    return query.all(), page_index * page_size + total_records if total_records != 0 else 0


def get_cdl_detail(db: Session, book_id: int):
    query = (
        db.query(CDLOrder, Order, ExtraInfo, TrackingNote)
        .join(Order, CDLOrder.book_id == Order.id)
        .join(ExtraInfo, CDLOrder.book_id == ExtraInfo.id, isouter=True)
        .join(TrackingNote, TrackingNote.book_id == Order.id, isouter=True)
        .filter(CDLOrder.book_id == book_id)
        .first()
    )
    return query


def new_cdl_order(db: Session, body: schema.PatchOrderRequest):
    created_date = db.query(Order.created_date).filter(Order.id == body.book_id)
    cdl = CDLOrder(book_id=body.book_id, order_request_date=created_date)
    db.add(cdl)
    db.query(ExtraInfo).filter(ExtraInfo.id == body.book_id).update(
        {"tags": ExtraInfo.tags + "[CDL]", "cdl_flag": 1}
    )
    db.commit()
    return schema.BasicResponse(msg="Success")


def del_cdl_order(db: Session, book_id):
    query = db.query(CDLOrder).filter(CDLOrder.book_id == book_id).first()
    db.delete(query)
    sql = text(
        """UPDATE extra_info SET tags = REPLACE(tags, '[CDL]', ''), cdl_flag = -1 WHERE id = %d;"""
        % book_id
    )
    db.execute(sql)
    db.commit()
    return schema.BasicResponse(msg="Success")


def update_cdl_order(db: Session, body: schema.PatchOrderRequest):
    cdl_dict = {k: v for k, v in body.cdl.__dict__.items() if k != "tracking_note"}
    db.query(CDLOrder).filter(CDLOrder.book_id == body.book_id).update(cdl_dict)
    db.commit()
    return schema.BasicResponse(msg="Success")


def update_normal_order(db: Session, body: schema.PatchOrderRequest):
    cols = ["checked", "attention", "override_reminder_time", "check_anyway"]
    info_dict = {k: v for k, v in body.__dict__.items() if k in cols and v != "undefined"}
    if len(info_dict.keys()) > 0:
        db.query(ExtraInfo).filter(ExtraInfo.id == body.book_id).update(info_dict)
        db.commit()


def mark_sensitive(db: Session, book_id: int):
    order = db.query(Order).filter(Order.id == book_id).first()
    if "-" in order.barcode:
        raise schema.LibSenseException("Barcode has not finalized yet.")

    existence = db.query(SensitiveBarcode).filter(SensitiveBarcode.barcode == order.barcode).count()
    if existence == 0:
        stmt = insert(SensitiveBarcode).values(barcode=order.barcode).prefix_with("IGNORE")
        db.execute(stmt)
        db.query(ExtraInfo) \
            .filter(and_(
            Order.id == ExtraInfo.id,
            Order.barcode == order.barcode,
            ExtraInfo.tags.notlike("Sensitive"))) \
            .update({"tags": ExtraInfo.tags + "[Sensitive]"}, synchronize_session='fetch')
    db.commit()


def cancel_sensitive(db: Session, book_id):
    order = db.query(Order).filter(Order.id == book_id).first()
    if "-" in order.barcode:
        raise schema.LibSenseException("Barcode has not finalized yet.")

    existence = db.query(SensitiveBarcode).filter(SensitiveBarcode.barcode == order.barcode).count()
    if existence == 0:
        raise schema.LibSenseException("Barcode not in sensitive database. Please check library note.")

    stmt = delete(SensitiveBarcode).where(SensitiveBarcode.barcode == order.barcode)
    db.execute(stmt)
    db.query(ExtraInfo) \
        .filter(and_(
        Order.id == ExtraInfo.id,
        Order.barcode == order.barcode,
        ExtraInfo.tags.notlike("Sensitive"))) \
        .update({"tags": ExtraInfo.tags.regexp_replace("\[Sensitive\]", "")}, synchronize_session='fetch')
    db.commit()


def mark_order_attention(db: Session, book_ids, direction):
    for book in book_ids:
        db.query(ExtraInfo).filter(ExtraInfo.id == book).update({ExtraInfo.attention: direction})
    db.commit()
    return schema.BasicResponse(msg="Success")


def mark_order_checked(db: Session, book_ids, direction, date):
    for book in book_ids:
        db.query(ExtraInfo).filter(ExtraInfo.id == book).update(
            {
                ExtraInfo.checked: direction,
                ExtraInfo.override_reminder_time: date if direction is True else None,
            }
        )
    db.commit()
    return schema.BasicResponse(msg="Success")


def check_anyway(db: Session, book_id: int, direction: bool):
    if direction:
        tags = db.query(ExtraInfo.tags).filter(ExtraInfo.id == book_id).first()[0]
        if not (("[Rush]" in tags and "[Local]" in tags) or ("[CDL]" in tags)):
            raise schema.LibSenseException(message="Check feature only supports Rush-Local and CDL orders")
    else:
        db.query(ExtraInfo).filter(ExtraInfo.id == book_id).update({"check_anyway": direction})


def get_tracking_note(db: Session, book_id: int):
    return db.query(TrackingNote).filter(TrackingNote.book_id == book_id).first()


def add_tracking_note(db: Session, note: schema.TrackingNote):
    new_note = TrackingNote(**note.__dict__)
    db.add(new_note)
    db.commit()
    db.refresh(new_note)
    return schema.BasicResponse(msg="Success")


def update_tracking_note(db: Session, note: schema.TrackingNote):
    db.query(TrackingNote).filter(TrackingNote.book_id == note.book_id).update(note.__dict__)
    db.commit()
    return schema.BasicResponse(msg="Success")


def get_starting_position(db: Session, barcode: int, order_number: str):
    query = (
        db.query(Order).filter(Order.barcode == barcode, Order.order_number == order_number).all()
    )
    return query[0].id if len(query) == 1 else -1


def update_sensitive(db: Session, output_file):
    if output_file.split(".")[-1] == "csv":
        df = pd.read_csv(output_file, dtype=str, header=None)
    else:
        df = pd.read_excel(output_file, dtype=str, header=None)
    for _, row in tqdm(df.iterrows()):
        stmt = insert(SensitiveBarcode).values(barcode=row.iloc[0]).prefix_with("IGNORE")
        db.execute(stmt)

        db.query(ExtraInfo) \
            .filter(and_(
            Order.id == ExtraInfo.id,
            Order.barcode == row.iloc[0],
            ExtraInfo.tags.notlike("Sensitive"))) \
            .update({"tags": ExtraInfo.tags + "[Sensitive]"}, synchronize_session='fetch')

    db.commit()
    return schema.BasicResponse(msg="Success")


def get_order_count(db: Session):
    return db.query(Order.id).count()


def get_all_vendors(db: Session):
    return db.query(Vendor).all()


def get_non_local_vendors(db: Session):
    return db.query(Vendor).filter(Vendor.local == 0).all()


def get_local_vendors(db: Session):
    return db.query(Vendor).filter(Vendor.local == 1).all()


def get_vendor(db: Session, code: str):
    return db.query(Vendor).filter(Vendor.vendor_code == code).first()


def update_vendor(db: Session, vendor: schema.Vendor):
    db.query(Vendor).filter(Vendor.vendor_code == vendor.vendor_code).update(vendor.__dict__)
    db.commit()
    return schema.BasicResponse(msg="Success")


def add_vendor(db: Session, vendor: schema.Vendor):
    new_vendor = Vendor(**vendor.__dict__)
    db.add(new_vendor)
    db.commit()
    db.refresh(new_vendor)
    return new_vendor


def delete_vendor(db: Session, vendor_code):
    vendor = db.query(Vendor).filter(Vendor.vendor_code == vendor_code).first()
    db.delete(vendor)
    db.commit()
    return schema.BasicResponse(msg="Success")


def get_all_presets(db: Session, username):
    return db.query(Preset).filter(Preset.creator == username).all()


def add_preset(db: Session, preset, preset_id=None):
    next_preset_id = preset_id or (db.query(func.max(Preset.preset_id)).scalar() or 0) + 1
    for preset_row in preset:
        db.add(Preset(**preset_row, preset_id=next_preset_id))

    db.commit()
    return next_preset_id


def update_preset(db: Session, preset, preset_id, username):
    target_preset = (
        db.query(Preset).filter(Preset.preset_id == preset_id).filter(Preset.creator == username)
    )
    if target_preset.count() == 0:
        return -1

    target_preset.delete()
    for insert_preset in preset:
        insert_preset["creator"] = username

    add_preset(db, preset, preset_id)
    return preset_id


def delete_preset(db: Session, preset_id, username):
    target_preset = (
        db.query(Preset).filter(Preset.preset_id == preset_id).filter(Preset.creator == username)
    )
    if target_preset.count() == 0:
        return -1
    target_preset.delete()
    db.commit()
    return schema.BasicResponse(msg="Success")


def get_vendor_meta(db: Session):
    return db.query(Order.vendor_code).group_by(Order.vendor_code).all()


def get_ips_meta(db: Session):
    return db.query(Order.ips_code).group_by(Order.ips_code).all()


def get_physical_copy_meta(db: Session):
    return db.query(CDLOrder.physical_copy_status).group_by(CDLOrder.physical_copy_status).all()


def get_oldest_date(db: Session):
    return db.execute("SELECT MIN(created_date) FROM nyc_orders;").first()[0]


def get_material_meta(db: Session):
    return db.execute("SELECT material FROM nyc_orders GROUP BY material").all()


def get_material_type_meta(db: Session):
    return db.execute("SELECT material_type FROM nyc_orders GROUP BY material_type").all()


def get_local_rush_pending(db: Session):
    # when should a local-rush order be checked?
    # when user marked order as check_anyway, or the order takes longer to arrive
    # and the order hasn't been checked yet,or the override time also has been exceeded

    query = """
        select count(o.id)
        from nyc_orders as o join extra_info as e join vendors as v
        on e.id = o.id and o.vendor_code = v.vendor_code
        where e.tags like '%%[Rush]%%'
          and e.tags like '%%[Local]%%'
          and (e.check_anyway = 1 or (
          arrival_date is null
          and o.order_status != 'VC' 
          and ((DATEDIFF(current_timestamp(), created_date) > notify_in) 
            and (e.checked = 0 or (override_reminder_time is not null
                    and current_timestamp() > override_reminder_time)))
          ))
    """
    return db.execute(query.replace("\n", " ")).first()


def get_cdl_stats(db: Session, avg_only=False):
    with open("configs/config.json") as f:
        config = json.load(f)
        vendor_start_date = config["cdl_config"]["vendor_start_date"]
        if avg_only:
            cdl = """
                select floor(avg(datediff(arrival_date, created_date))) as avg
                from nyc_orders join extra_info ei on nyc_orders.id = ei.id
                where arrival_date is not null
                and tags like '%%[CDL]%%'
                and nyc_orders.id in (select cdl_info.book_id from cdl_info)
                and created_date > '%s';
            """ % vendor_start_date
            return db.execute(cdl.replace("\n", " ")).first()["avg"]

        cdl = """
            select floor(avg(datediff(arrival_date, created_date))) as avg,
            floor(max(datediff(arrival_date, created_date))) as max,
            floor(min(datediff(arrival_date, created_date))) as min
            from nyc_orders join extra_info ei on nyc_orders.id = ei.id
            where arrival_date is not null
            and tags like '%%[CDL]%%'
            and nyc_orders.id in (select cdl_info.book_id from cdl_info)
            and created_date > '%s';
        """ % vendor_start_date
        return db.execute(cdl.replace("\n", " ")).first()


def get_cdl_scan_stats(db: Session):
    with open("configs/config.json") as f:
        config = json.load(f)
        vendor_start_date = config["cdl_config"]["vendor_start_date"]
        cdl_delivery = """
            select floor(avg(datediff(pdf_delivery_date, order_request_date))) as avg,
            floor(max(datediff(pdf_delivery_date, order_request_date))) as max,
            floor(min(datediff(pdf_delivery_date, order_request_date))) as min
            from cdl_info
            where pdf_delivery_date is not null and order_request_date is not null
            and order_request_date > '%s';
        """ % vendor_start_date
        return db.execute(cdl_delivery.replace("\n", "")).first()


def get_cdl_pending(db: Session):
    avg_days = get_cdl_scan_stats(db)["avg"]
    cdl = """
        select count(book_id)
        from cdl_info inner join extra_info on cdl_info.book_id = extra_info.id
        where (extra_info.check_anyway = 1 or (pdf_delivery_date is null 
        and datediff(current_timestamp(), order_request_date) > %d
        and (extra_info.checked = 0 
            or (override_reminder_time is not null and CURRENT_TIMESTAMP() > override_reminder_time))));
    """ % (avg_days or 0)
    return db.execute(cdl.replace("\n", " ")).first()


def get_average_days(db: Session):
    rush_nyc = """
        select floor(avg(datediff(arrival_date, created_date))) as avg,
        floor(max(datediff(arrival_date, created_date))) as max,
        floor(min(datediff(arrival_date, created_date))) as min
        from nyc_orders join extra_info ei on nyc_orders.id = ei.id
        where arrival_date is not null
        and order_status != 'VC'
        and tags like '%%[Rush]%%'
        and tags like '%%[NY]%%';
    """
    rush_local = """
        select floor(avg(datediff(arrival_date, created_date))) as avg,
        max(floor(datediff(arrival_date, created_date))) as max,
        min(floor(datediff(arrival_date, created_date))) as min
        from nyc_orders join extra_info ei on nyc_orders.id = ei.id
        where arrival_date is not null
        and order_status != 'VC'
        and tags like '%%[Rush]%%'
        and tags like '%%[Local]%%';
    """

    cdl_rs = get_cdl_stats(db)
    cdl_scan_rs = get_cdl_scan_stats(db)
    rush_nyc_rs = db.execute(rush_nyc.replace("\n", " ")).first()
    rush_local_rs = db.execute(rush_local.replace("\n", " ")).first()

    return cdl_rs, rush_nyc_rs, rush_local_rs, cdl_scan_rs
