
from datetime import date
from typing import List, Union, Optional
from pydantic import BaseModel
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


class Message(CamelModel):
    id: int
    message: Optional[str]
    book_related: Optional[str]


class TimelineNote(CamelModel):
    date: date
    message: str


class User(CamelModel):
    net_id: str
    name: str
    role = 'user'
    messages: Optional[int]


class Order(CamelModel):
    uuid: str
    barcode: str
    title: str
    order_type: int
    order_number: str
    order_create_date: date
    order_arrival_date: date
    ips_code: str
    process_status: Optional[str]
    process_status_date: date
    ny_note: Optional[str]
    library_note: Optional[List[TimelineNote]]
    override_date: Union[date, str]

    class Config:
        orm_mode: True


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
