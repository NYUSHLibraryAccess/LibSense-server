from sqlalchemy import Float, DateTime, Boolean, Column, ForeignKey, Integer, String, VARCHAR
from sqlalchemy.orm import relationship

from .database import Base


class Order(Base):
    __tablename__ = "nyc_orders"
    id = Column(Integer, primary_key=True, index=True, unique=True)
    bsn = Column(String, nullable=False)
    title = Column(String, nullable=False)
    arrival_status = Column(String)
    arrival_date = Column(DateTime)
    arrival_operator = Column(String)
    items_created = Column(String)
    barcode = Column(String, nullable=False)
    ips_code = Column(String)
    ips = Column(String)
    ips_date = Column(DateTime)
    ips_update_date = Column(DateTime)
    ips_code_operator = Column(String)
    update_date = Column(DateTime)
    created_date = Column(DateTime)
    sublibrary = Column(String)
    order_unit = Column(String)
    order_number = Column(String)
    order_type = Column(String)
    total_price = Column(Float)
    complete = Column(String)
    order_status_update_date = Column(DateTime)
    invoice_status = Column(String)
    vendor_code = Column(String)
    library_note = Column(String)
    material_format = Column(String)
