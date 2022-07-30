from sqlalchemy import Float, DateTime, Boolean, Column, ForeignKey, Integer, String

from .database import Base


class Order(Base):
    __tablename__ = "nyc_orders"
    id = Column(Integer, primary_key=True, index=True, unique=True)
    bsn = Column(String, nullable=False)
    title = Column(String)
    arrival_text = Column(String)
    arrival_date = Column(DateTime)
    arrival_operator = Column(String)
    items_created = Column(String)
    barcode = Column(String)
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
    vendor_code = Column(String, nullable=False)
    library_note = Column(String)


class CDLOrder(Base):
    __tablename__ = "cdl_info"
    book_id = Column(
        Integer, ForeignKey("nyc_orders.id"), primary_key=True, unique=True, index=True
    )
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
    # didn't put this column in ExtraInfo (1...1 mapping)
    # might be expanded to multiple tracking notes in the future, so a separate table is created
    __tablename__ = "notes"
    note_id = Column(Integer, primary_key=True, index=True, unique=True)
    book_id = Column(Integer, ForeignKey("nyc_orders.id"))
    tracking_note = Column(String)
    taken_by = Column(String)
    date = Column(DateTime)


class Vendor(Base):
    __tablename__ = "vendors"
    vendor_code = Column(String, primary_key=True, index=True, unique=True)
    notify_in = Column(Integer)
    local = Column(Integer)


class ExtraInfo(Base):
    __tablename__ = "extra_info"
    id = Column(Integer, ForeignKey("nyc_orders.id"), primary_key=True, index=True, unique=True)
    order_number = Column(String)
    tags = Column(String)
    reminder_receiver = Column(String)
    cdl_flag = Column(Boolean)
    checked = Column(Boolean)
    override_reminder_time = Column(DateTime)
    attention = Column(Boolean)


class User(Base):
    __tablename__ = "user"
    username = Column(String, primary_key=True, index=True, unique=True)
    password = Column(String)
    role = Column(String)


class Preset(Base):
    __tablename__ = "presets"
    record_id = Column(Integer, primary_key=True, index=True, unique=True)
    preset_id = Column(Integer)
    preset_name = Column(String)
    creator = Column(String)
    type = Column(String)
    col = Column(String)
    val = Column(String)
    op = Column(String)


MAPPING = {
    "Order": Order,
    "CDLOrder": CDLOrder,
    "TrackingNote": TrackingNote,
    "Vendor": Vendor,
    "ExtraInfo": ExtraInfo,
}
