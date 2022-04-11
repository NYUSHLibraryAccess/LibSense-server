from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import insert, values, and_
from datetime import date, datetime
from ..schema import *
from .model import *


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


def add_tracking_note(db: Session, note: TimelineNote):
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
