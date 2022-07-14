from core import schema
from sqlalchemy import text
from sqlalchemy.orm import Session
from core.database.model import *
from core.database.utils import compile_query


def login(db: Session, username, password):
    return db.query(User).filter(User.username == username) \
        .filter(User.password == password).first()


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


def get_overdue_rush_local(db: Session, start_idx: int = 0, limit: int = 10, filters=None, sorter=None,
                           for_pandas=False):
    if filters is None:
        filters = []
    args = [Order.barcode, Order.title, Order.order_number, Order.created_date, Order.arrival_date,
            Order.ips_code, Order.ips, Order.ips_date, Order.library_note, Order.vendor_code, ExtraInfo.tags]
    query = db.query(*args).join(ExtraInfo, Order.id == ExtraInfo.id) \
        .join(Vendor, Order.vendor_code == Vendor.vendor_code) \
        .filter(Order.arrival_date == None)
    table_mapping = {
        "ExtraInfo": ["tags"],
        "default": "Order"
    }

    suffix = text("""extra_info.tags like '%[Rush]%' and extra_info.tags like '%[Local]%'
    and (((override_reminder_time is null) and (DATEDIFF(current_timestamp(), created_date) > notify_in))
    or ((override_reminder_time is not null) and (DATEDIFF(current_timestamp(), created_date) > override_reminder_time)))
                """.replace("\n", " "))

    fixed_filters = [schema.FieldFilter(op="in", col="tags", val=["Rush", "Local"])]
    filters.extend(fixed_filters)

    query, total_records = compile_query(query, filters, table_mapping, sorter, Order.id, start_idx, limit, suffix)

    if for_pandas:
        return query.statement

    return query.all(), start_idx * limit + total_records if total_records != 0 else 0


def get_overdue_cdl(db: Session, start_idx: int = 0, limit: int = 10, filters=None, sorter=None, for_pandas=False):
    args = [CDLOrder.cdl_item_status, CDLOrder.order_request_date, CDLOrder.scanning_vendor_payment_date,
            CDLOrder.pdf_delivery_date, CDLOrder.back_to_karms_date,
            Order.barcode, Order.title, Order.order_number, Order.created_date, Order.arrival_date,
            Order.ips_code, Order.ips, Order.ips_date, Order.library_note, Order.vendor_code,
            ExtraInfo.override_reminder_time, ExtraInfo.checked]
    table_mapping = {
        "CDLOrder": [
            "cdl_item_status", "order_request_date", "scanning_vendor_payment_date",
            "pdf_delivery_date", "back_to_karms_date"
        ],
        "default": "Order"
    }
    query = db.query(*args).join(Order, CDLOrder.book_id == Order.id).filter(CDLOrder.pdf_delivery_date == None)
    suffix = text("""datediff(current_timestamp(), order_request_date) > 30
        and (checked = 0 or (override_reminder_time is not null and CURRENT_TIMESTAMP() > override_reminder_time))))""")

    query, total_records = compile_query(query, filters, table_mapping, sorter, Order.id, start_idx, limit, suffix)

    if for_pandas:
        return query.statement

    return query.all(), start_idx * limit + total_records if total_records != 0 else 0


def get_sh_order_report(db: Session, start_idx: int = 0, limit: int = 10, filters=None, sorter=None, for_pandas=False):
    if filters is None:
        filters = []
    args = [Order.order_number, Order.barcode, Order.title, Order.created_date, Order.arrival_date,
            Order.arrival_status,
            Order.arrival_operator, Order.order_status, Order.order_status_update_date, Order.ips_code, Order.ips,
            Order.ips_update_date, Order.ips_code_operator, Order.material, Order.material_type, Order.vendor_code,
            Order.library_note, Order.invoice_status, Order.collection, Order.item_status, Order.total_price, Order.bsn,
            Order.sublibrary]
    query = db.query(*args)
    table_mapping = {"default": "Order"}
    suffix = text("""datediff(current_timestamp(), created_date) <= 1095""")
    fixed_filters = [
        schema.FieldFilter(op="like", col="sublibrary", val="NSHNG"),
        schema.FieldFilter(op="like", col="order_type", val="M")
    ]
    fixed_sorter = schema.SortCol(col="created_date", desc=True)
    filters.extend(fixed_filters)
    sorter = sorter or fixed_sorter
    query, total_records = compile_query(query, filters, table_mapping, sorter, Order.id, start_idx, limit, suffix)

    if for_pandas:
        return query.statement

    return query.all(), start_idx * limit + total_records if total_records != 0 else 0


def get_all_orders(db: Session, start_idx: int = 0, limit: int = 10, filters=None, sorter=None, fuzzy=None):
    args = [*Order.__table__.c, TrackingNote.tracking_note, ExtraInfo.tags, ExtraInfo.cdl_flag, ExtraInfo.checked,
            ExtraInfo.attention, ExtraInfo.override_reminder_time]
    query = db.query(*args).join(ExtraInfo, Order.id == ExtraInfo.id) \
        .join(TrackingNote, Order.id == TrackingNote.book_id)
    table_mapping = {
        "ExtraInfo": ["tags", "checked", "attention"],
        "default": "Order"
    }
    fuzzy_cols = [Order.barcode, Order.bsn, Order.library_note, Order.title, Order.order_number]
    query, total_records = compile_query(query, filters, table_mapping, sorter, Order.id, start_idx, limit, fuzzy=fuzzy,
                                   fuzzy_cols=fuzzy_cols)
    return query.all(), start_idx * limit + total_records if total_records != 0 else 0


def get_order_detail(db: Session, book_id: int):
    query = db.query(Order, ExtraInfo, TrackingNote) \
        .join(ExtraInfo, Order.id == ExtraInfo.id).join(TrackingNote, Order.id == TrackingNote.book_id) \
        .filter(Order.id == book_id).first()
    return query


def get_all_cdl(db: Session, start_idx: int = 0, limit: int = 10, filters=None, sorter=None, fuzzy=None):
    args = [*CDLOrder.__table__.c, *Order.__table__.c, ExtraInfo.tags, ExtraInfo.cdl_flag, ExtraInfo.checked,
            ExtraInfo.attention, ExtraInfo.override_reminder_time, TrackingNote.tracking_note]
    query = db.query(*args).join(Order, CDLOrder.book_id == Order.id) \
        .join(ExtraInfo, ExtraInfo.id == Order.id).join(TrackingNote, TrackingNote.book_id == Order.id)
    table_mapping = {
        "ExtraInfo": ["tags"],
        "CDLOrder": ["cdl_item_status", "order_request_date", "scanning_vendor_payment_date", "pdf_delivery_date",
                     "circ_pdf_url", "back_to_karms_date"],
        "default": "Order"
    }
    fuzzy_cols = [Order.barcode, Order.bsn, Order.library_note, Order.title, Order.order_number]
    query, total_records = compile_query(query, filters, table_mapping, sorter, Order.id, start_idx, limit, fuzzy=fuzzy,
                                   fuzzy_cols=fuzzy_cols)
    return query.all(), start_idx * limit + total_records if total_records != 0 else 0


def get_cdl_detail(db: Session, order_id: int):
    query = db.query(CDLOrder, Order, ExtraInfo, TrackingNote).join(Order, CDLOrder.book_id == Order.id) \
        .join(ExtraInfo, CDLOrder.book_id == ExtraInfo.id).join(TrackingNote, TrackingNote.book_id == Order.id) \
        .filter(CDLOrder.book_id == order_id).first()
    return query


def new_cdl_order(db: Session, cdl_request: schema.CDLRequest):
    cdl_dict = cdl_request.__dict__
    del cdl_dict['tracking_note']
    cdl = CDLOrder(**cdl_dict)
    db.add(cdl)
    db.query(ExtraInfo).filter(ExtraInfo.id == cdl_request.book_id) \
        .update({'tags': ExtraInfo.tags + '[CDL]', 'cdl_flag': 1})
    db.commit()
    return schema.BasicResponse(msg="Success")


def del_cdl_order(db: Session, book_id):
    query = db.query(CDLOrder).filter(CDLOrder.book_id == book_id).first()
    db.delete(query)
    sql = text('''UPDATE extra_info SET tags = REPLACE(tags, '[CDL]', ''), cdl_flag = 0 WHERE id = %d;''' % book_id)
    db.execute(sql)
    db.commit()
    return schema.BasicResponse(msg="Success")


def update_cdl_order(db: Session, cdl: schema.CDLRequest):
    cdl_dict = cdl.__dict__
    if cdl_dict.get('tracking_note', 'undefined') != 'undefined':
        del cdl_dict['tracking_note']
    db.query(CDLOrder).filter(CDLOrder.book_id == cdl.book_id).update(cdl_dict)
    db.commit()
    return schema.BasicResponse(msg="Success")


def mark_order_attention(db: Session, book_ids, direction):
    for book in book_ids:
        db.query(ExtraInfo).filter(ExtraInfo.id == book).update({ExtraInfo.attention: direction})
    db.commit()
    return schema.BasicResponse(msg="Success")


def mark_order_checked(db: Session, book_ids, direction, date):
    for book in book_ids:
        db.query(ExtraInfo).filter(ExtraInfo.id == book) \
            .update(
            {ExtraInfo.checked: direction, ExtraInfo.override_reminder_time: date if direction is True else None})
    db.commit()
    return schema.BasicResponse(msg="Success")


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
    query = db.query(Order).filter(Order.barcode == barcode, Order.order_number == order_number).all()
    return query[0].id if len(query) == 1 else -1


def get_order_count(db: Session):
    return db.query(Order.id).count()


def get_all_vendors(db: Session):
    return db.query(Vendor).all()


def get_local_vendors(db: Session):
    return db.query(Vendor).filter(Vendor.local == 0).all()


def get_non_local_vendors(db: Session):
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
    query = """
        select count(o.id)
        from nyc_orders as o join extra_info as e join vendors as v
        on e.id = o.id and o.vendor_code = v.vendor_code
        where (arrival_date is null)
          and e.checked = 0 
          and e.tags like '%%[Rush]%%'
          and e.tags like '%%[Local]%%'
          and (((override_reminder_time is null) 
                    and (DATEDIFF(current_timestamp(), created_date) > notify_in))
                or ((override_reminder_time is not null) 
                    and (DATEDIFF(current_timestamp(), created_date) > override_reminder_time)));
    """
    return db.execute(query.replace("\n", " ")).first()


def get_cdl_pending(db: Session):
    cdl = """
        select count(book_id)
        from cdl_info inner join extra_info on cdl_info.book_id = extra_info.id
        where pdf_delivery_date is null 
        and datediff(current_timestamp(), order_request_date) > 30
        and (extra_info.checked = 0 or (override_reminder_time is not null and CURRENT_TIMESTAMP() > override_reminder_time));
    """
    return db.execute(cdl.replace("\n", " ")).first()


def get_average_days(db: Session):
    cdl = """
        select floor(avg(datediff(arrival_date, created_date))) as avg,
        floor(max(datediff(arrival_date, created_date))) as max,
        floor(min(datediff(arrival_date, created_date))) as min
        from nyc_orders join extra_info ei on nyc_orders.id = ei.id
        where arrival_date is not null
        and tags like '%%[CDL]%%'
        and nyc_orders.id in (select cdl_info.book_id from cdl_info);
        ;
    """
    rush_nyc = """
        select floor(avg(datediff(arrival_date, created_date))) as avg,
        floor(max(datediff(arrival_date, created_date))) as max,
        floor(min(datediff(arrival_date, created_date))) as min
        from nyc_orders join extra_info ei on nyc_orders.id = ei.id
        where arrival_date is not null
        and tags like '%%[Rush]%%'
        and tags like '%%[NY]%%';
    """
    rush_local = """
        select floor(avg(datediff(arrival_date, created_date))) as avg,
        max(floor(datediff(arrival_date, created_date))) as max,
        min(floor(datediff(arrival_date, created_date))) as min
        from nyc_orders join extra_info ei on nyc_orders.id = ei.id
        where arrival_date is not null
        and tags like '%%[Rush]%%'
        and tags like '%%[Local]%%';
    """

    cdl_delivery = """
        select floor(avg(datediff(pdf_delivery_date, order_request_date))) as avg,
        floor(max(datediff(pdf_delivery_date, order_request_date))) as max,
        floor(min(datediff(pdf_delivery_date, order_request_date))) as min
        from cdl_info
        where pdf_delivery_date is not null and order_request_date is not null;
    """

    cdl_rs = db.execute(cdl.replace("\n", " ")).first()
    rush_nyc_rs = db.execute(rush_nyc.replace("\n", " ")).first()
    rush_local_rs = db.execute(rush_local.replace("\n", " ")).first()
    cdl_scan_rs = db.execute(cdl_delivery.replace("\n", "")).first()

    return cdl_rs, rush_nyc_rs, rush_local_rs, cdl_scan_rs
