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
    extra_info = relationship("ExtraInfo", back_populates="book")


class CDLOrder(Base):
    __tablename__ = "cdl_info"
    book_id = Column(Integer, ForeignKey("nyc_orders.id"), primary_key=True, unique=True, index=True)
    # order_number = Column(String, ForeignKey("nyc_orders.order_number"))
    # title = Column(String)
    # barcode = Column(String)
    cdl_item_status = Column(String)
    order_request_date = Column(DateTime)
    order_purchased_date = Column(DateTime)
    due_date = Column(DateTime)
    physical_copy_status = Column(String)
    scanning_vendor_payment_date = Column(DateTime)
    pdf_delivery_date = Column(DateTime)
    back_to_karms_date = Column(String)
    bobcat_permanent_link = Column(String)
    circ_pdf_url = Column(String)
    vendor_file_url = Column(String)
    file_password = Column(String)
    author = Column(String)
    pages = Column(String)


class TrackingNote(Base):
    __tablename__ = "notes"
    id = Column(Integer, primary_key=True, index=True, unique=True)
    book_id = Column(Integer, ForeignKey("nyc_orders.id"))
    content = Column(String)
    taken_by = Column(String)
    date = Column(DateTime)

    book = relationship("Order", back_populates="tracking_note")


class Vendor(Base):
    __tablename__ = "vendors"
    vendor_code = Column(String, primary_key=True, index=True, unique=True)
    name = Column(String)
    notify_in = Column(Integer)
    local = Column(Integer)


class ExtraInfo(Base):
    __tablename__ = "extra_info"
    id = Column(Integer, ForeignKey("nyc_orders.id"), primary_key=True, index=True, unique=True)
    order_number = Column(String)
    tags = Column(String)
    override_reminder_time = Column(Integer)
    reminder_receiver = Column(String)
    cdl_flag = Column(Integer)

    book = relationship("Order", back_populates="extra_info")


class User(Base):
    __tablename__ = "user"
    username = Column(String, primary_key=True, index=True, unique=True)
    password = Column(String)
    role = Column(String)


MAPPING = {
    "Order": Order,
    "CDLOrder": CDLOrder,
    "TrackingNote": TrackingNote,
    "Vendor": Vendor,
    "ExtraInfo": ExtraInfo
}
