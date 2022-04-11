from sqlalchemy import Float, DateTime, Boolean, Column, ForeignKey, Integer, String, VARCHAR
from sqlalchemy.orm import relationship

from .database import Base


class Order(Base):
    __tablename__ = "nyc_orders"
    id = Column(Integer, primary_key=True, index=True, unique=True)
    bsn = Column(String, nullable=False)
    title = Column(String, nullable=False)
    arrival_text = Column(String)
    arrival_date = Column(DateTime)
    arrival_operator = Column(String)
    items_created = Column(String)
    barcode = Column(String, nullable=False)
    ips_code = Column(String)
    ips = Column(String)
    item_status = Column(String)
    material = Column(String)
    collection = Column(String)
    ips_date = Column(DateTime)
    ips_update_date = Column(DateTime)
    ips_code_operator = Column(String)
    update_date = Column(DateTime)
    created_date = Column(DateTime)
    sublibrary = Column(String)
    order_status = Column(String)
    invoice_status = Column(String)
    material_type = Column(String)
    order_number = Column(String)
    order_type = Column(String)
    total_price = Column(Float)
    order_unit = Column(String)
    arrival_status = Column(String)
    order_status_update_date = Column(DateTime)
    vendor_code = Column(String)
    library_note = Column(String)

    tracking_note = relationship("TrackingNote", back_populates="book")


class TrackingNote(Base):
    __tablename__ = "notes"
    id = Column(Integer, primary_key=True, index=True, unique=True)
    book_id = Column(Integer, ForeignKey("nyc_orders.id"))
    content = Column(String)
    taken_by = Column(String)
    date = Column(DateTime)

    book = relationship("Order", back_populates="tracking_note")

