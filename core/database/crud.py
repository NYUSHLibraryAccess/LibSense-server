from core import schema
from sqlalchemy.orm import Session
from core.database.model import *
from humps import decamelize


def get_all_orders(db: Session, start_idx: int = 0, limit: int = 10, filters=None, sorter=None):
    args = [Order.id, Order.barcode, Order.title, Order.order_number, Order.created_date, Order.arrival_date,
            Order.ips_code, Order.ips, Order.ips_date, Order.library_note, Order.vendor_code, ExtraInfo.tags]
    query = db.query(*args).join(ExtraInfo, Order.id == ExtraInfo.id)
    if filters:
        sql_filters = []
        for f in filters:
            if f.op == schema.FilterOperators.IN:
                if f.col == "tags":
                    for t in f.val:
                        sql_filters.append(ExtraInfo.tags.like('%[' + t + ']%'))
                else:
                    sql_filters.append(getattr(Order, decamelize(f.col)).in_(f.val))
            elif f.op == schema.FilterOperators.LIKE:
                sql_filters.append(getattr(Order, decamelize(f.col)).like('%' + f.val + '%'))
        for f in sql_filters:
            query = query.filter(f)
    if sorter:
        col = getattr(Order, decamelize(sorter.col))
        id_col = Order.id
        if sorter.desc:
            col = col.desc()
            id_col = id_col.desc()
        query = query.order_by(col, id_col)
    if start_idx:
        query = query.offset(start_idx * limit)
    total_records = query.count()
    if limit:
        query = query.limit(limit)
    return query.all(), start_idx * limit + total_records if total_records != 0 else 0


def get_order_detail(db: Session, order_id: int):
    query = db.query(Order).filter(Order.id == order_id).first()
    return query


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


def get_vendor_meta(db: Session):
    return db.query(Order.vendor_code).group_by(Order.vendor_code).all()


def get_ips_meta(db: Session):
    return db.query(Order.ips_code).group_by(Order.ips_code).all()


def get_oldest_date(db: Session):
    return db.execute("SELECT MIN(created_date) FROM nyc_orders;").first()[0]
