from sqlalchemy.orm import Session
from .model import Order


def get_all_orders(db: Session, start_idx: int = 0, limit: int = 10):
    args = [Order.id, Order.barcode, Order.title, Order.order_number, Order.created_date, Order.arrival_date,
            Order.ips_code, Order.ips, Order.ips_date, Order.library_note, Order.vendor_code]
    query = db.query(*args)
    total_records = db.query(Order.id).count()
    if start_idx:
        query = query.offset(start_idx * limit)
    if limit:
        query = query.limit(limit)
    return query.all(), total_records


def get_order_detail(db: Session, order_id: int):
    query = db.query(Order).filter(Order.id == order_id).first()
    print(query.tracking_note)
    return query
