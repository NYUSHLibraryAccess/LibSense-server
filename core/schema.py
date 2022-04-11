from datetime import date, datetime
from enum import Enum
from typing import List, Union, Optional
from pydantic import Field, BaseModel
from humps import camelize


def to_camel(string):
    return camelize(string)


class CamelModel(BaseModel):
    class Config:
        alias_generator = to_camel
        allow_population_by_field_name = True


class PageableResultSet(CamelModel):
    page_index: int = 0
    page_limit: int = 0
    total_pages: int = 0

    class Config:
        orm_mode = True


class Message(CamelModel):
    id: int
    message: Optional[str]
    book_related: Optional[str]


class TimelineNote(CamelModel):
    book_id: int
    date: datetime
    taken_by: str
    content: str

    class Config:
        orm_mode = True


class EnumRole(str, Enum):
    admin = 'admin'
    user = 'user'


class User(CamelModel):
    net_id: str
    name: str
    role: EnumRole
    email: str
    messages: Optional[int]


class Order(CamelModel):
    id: int
    barcode: str
    title: str
    order_type: Optional[str]
    order_number: str
    created_date: date
    arrival_date: date
    ips_code: Optional[str]
    ips: Optional[str]
    ips_date: date
    vendor_code: str
    library_note: Optional[str]
    tracking_note: Optional[List[TimelineNote]]
    override_date: Optional[Union[date, str]]

    class Config:
        orm_mode = True
        allow_populate_by_alias = True


class OrderDetail(Order):
    bsn: str
    arrival_status: Optional[str]
    arrival_operator: Optional[str]
    items_created: Optional[str]
    ips_update_date: Optional[date]
    ips_code_operator: Optional[str]
    update_date: date
    sublibrary: str
    total_price: float
    complete: str
    order_status_update_date: date
    invoice_status: str
    material_format: Optional[str]


class PageableOrdersSet(PageableResultSet):
    result: List[Order]


class CDLOrder(Order):
    cdl_status: int
    scan_ven_pymt_date: date
    pdf_delivery_date: date
    date_back_to_karms: Union[date, str]
    file_url: Optional[str]
    password: Optional[str]
    bobcat_link: Optional[str]
    circ_pdf_link: Optional[str]


class PageableCDLOrdersSet(PageableResultSet):
    result: List[CDLOrder]


class Vendor(CamelModel):
    name: str
    id: str
    notify_date: str
