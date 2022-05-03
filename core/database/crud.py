from core import schema
from sqlalchemy import text
from sqlalchemy.orm import Session
from core.database.model import *
from core.database.utils import compile, compile_filters, compile_sorters


def get_overdue_rush_local(db: Session, start_idx: int = 0, limit: int = 10, filters=None, sorter=None, for_pandas=False):
    args = [Order.id, Order.barcode, Order.title, Order.order_number, Order.created_date, Order.arrival_date,
            Order.ips_code, Order.ips, Order.ips_date, Order.library_note, Order.vendor_code, ExtraInfo.tags]
    query = db.query(*args).join(ExtraInfo, Order.id == ExtraInfo.id) \
        .join(Vendor, Order.vendor_code == Vendor.vendor_code) \
        .filter(Order.arrival_date == None)
    if filters:
        table_mapping = {
            "ExtraInfo": ["tags"],
            "default": "Order"
        }
        query = compile_filters(query, filters, table_mapping)
    if sorter:
        query = compile_sorters(query, sorter, table_mapping, Order.id)

    suffix = """extra_info.tags like '%[Rush]%' and extra_info.tags like '%[Local]%'
and (((override_reminder_time is null) and (DATEDIFF(current_timestamp(), created_date) > notify_in))
or ((override_reminder_time is not null) and (DATEDIFF(current_timestamp(), created_date) > override_reminder_time)))
            """
    query = query.filter(text(suffix.replace("\n", " ")))

    if start_idx:
        query = query.offset(start_idx * limit)
    total_records = query.count()
    if limit != -1:
        query = query.limit(limit)

    if for_pandas:
        return query.statement
    return query.all(), start_idx * limit + total_records if total_records != 0 else 0


def get_all_orders(db: Session, start_idx: int = 0, limit: int = 10, filters=None, sorter=None):
    args = [Order.id, Order.barcode, Order.title, Order.order_number, Order.created_date, Order.arrival_date,
            Order.ips_code, Order.ips, Order.ips_date, Order.library_note, Order.vendor_code, ExtraInfo.tags]
    query = db.query(*args).join(ExtraInfo, Order.id == ExtraInfo.id)
    table_mapping = {
        "ExtraInfo": ["tags"],
        "default": "Order"
    }
    query, total_records = compile(query, filters, table_mapping, sorter, Order.id, start_idx, limit)
    return query.all(), start_idx * limit + total_records if total_records != 0 else 0


def get_order_detail(db: Session, book_id: int):
    query = db.query(Order, ExtraInfo).join(ExtraInfo, Order.id == ExtraInfo.id).filter(Order.id == book_id).first()
    return query


def get_all_cdl(db: Session, start_idx: int = 0, limit: int = 10, filters=None, sorter=None):
    args = [CDLOrder.cdl_item_status, CDLOrder.order_request_date, CDLOrder.scanning_vendor_payment_date,
            CDLOrder.pdf_delivery_date, CDLOrder.circ_pdf_url, CDLOrder.back_to_karms_date,
            Order.id, Order.barcode, Order.title, Order.order_number, Order.created_date, Order.arrival_date,
            Order.ips_code, Order.ips, Order.ips_date, Order.library_note, Order.vendor_code, ExtraInfo.tags]
    query = db.query(*args).join(Order, CDLOrder.book_id == Order.id).join(ExtraInfo, ExtraInfo.id == Order.id)
    table_mapping = {
        "ExtraInfo": ["tags"],
        "CDLOrder": ["cdl_item_status", "order_request_date", "scanning_vendor_payment_date", "pdf_delivery_date",
                     "circ_pdf_url", "back_to_karms_date"],
        "default": "Order"
    }
    query, total_records = compile(query, filters, table_mapping, sorter, Order.id, start_idx, limit)
    return query.all(), start_idx * limit + total_records if total_records != 0 else 0


def get_cdl_detail(db: Session, order_id: int):
    query = db.query(CDLOrder, Order, ExtraInfo).join(Order, CDLOrder.book_id == Order.id)\
        .join(ExtraInfo, CDLOrder.book_id == ExtraInfo.id).filter(CDLOrder.book_id == order_id).first()
    return query


def new_cdl_order(db: Session, cdl_request: schema.CDLRequest):
    cdl = CDLOrder(**cdl_request.__dict__)
    db.add(cdl)
    db.query(ExtraInfo).filter(ExtraInfo.id == cdl_request.book_id).update({'tags': ExtraInfo.tags + '[CDL]'})
    db.commit()
    db.refresh(cdl)
    return cdl


def del_cdl_order(db: Session, book_id):
    query = db.query(CDLOrder).filter(CDLOrder.book_id == book_id).first()
    db.delete(query)
    sql = text("UPDATE extra_info SET tags = REPLACE(tags, '[CDL]', '') WHERE id = %d;" % book_id)
    db.execute(sql)
    db.commit()
    return {"msg": "Success"}


def update_cdl_order(db: Session, cdl: schema.CDLRequest):
    db.query(CDLOrder).filter(CDLOrder.book_id == cdl.book_id).update(cdl.__dict__)
    db.commit()
    return {"msg": "Success"}


def add_tracking_note(db: Session, note: schema.TimelineNote):
    new_note = TrackingNote(**note.__dict__)
    db.add(new_note)
    db.commit()
    db.refresh(new_note)
    return new_note


def get_starting_position(db: Session, barcode: int, order_number: str):
    query = db.query(Order).filter(Order.barcode == barcode, Order.order_number == order_number).all()
    print(query)
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
    return True


def get_vendor_meta(db: Session):
    return db.query(Order.vendor_code).group_by(Order.vendor_code).all()


def get_ips_meta(db: Session):
    return db.query(Order.ips_code).group_by(Order.ips_code).all()


def get_oldest_date(db: Session):
    return db.execute("SELECT MIN(created_date) FROM nyc_orders;").first()[0]


def get_material_meta(db: Session):
    return db.execute("SELECT material FROM nyc_orders GROUP BY material").all()


def get_material_type_meta(db: Session):
    return db.execute("SELECT material_type FROM nyc_orders GROUP BY material_type").all()


def get_local_rush_pending(db: Session):
    query = """
        select count(o.id)
        from libsense.nyc_orders as o join libsense.extra_info as e join libsense.vendors as v
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


def get_average_days(db: Session):
    cdl = """
        select floor(avg(datediff(arrival_date, created_date))) as avg,
        max(floor(datediff(arrival_date, created_date))) as max,
        min(floor(datediff(arrival_date, created_date))) as min
        from nyc_orders join extra_info ei on nyc_orders.id = ei.id
        where arrival_date is not null
        and tags like '%%[CDL]%%';
    """
    rush_nyc = """
        select floor(avg(datediff(arrival_date, created_date))) as avg,
        max(floor(datediff(arrival_date, created_date))) as max,
        min(floor(datediff(arrival_date, created_date))) as min
        from nyc_orders join extra_info ei on nyc_orders.id = ei.id
        where arrival_date is not null
        and tags like '%%[Rush]%%'
        and tags like '%%[NYC]%%';
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

    cdl_rs = db.execute(cdl.replace("\n", " ")).first()
    rush_nyc_rs = db.execute(rush_nyc.replace("\n", " ")).first()
    rush_local_rs = db.execute(rush_local.replace("\n", " ")).first()

    return cdl_rs, rush_nyc_rs, rush_local_rs
