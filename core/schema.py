from datetime import date, datetime
from enum import Enum
from typing import List, Union, Optional, Dict
from pydantic import BaseModel, conlist
from humps import camelize


def to_camel(string):
    return camelize(string)


class Tags(str, Enum):
    CDL = 'CDL'
    LOCAL = 'Local'
    RUSH = 'Rush'
    NYC = 'NYC'
    ILL = 'ILL'
    NON_RUSH = 'Non-Rush'
    SENSITIVE = 'Sensitive'
    COURSE_RESERVE = 'Course-Reserve'
    DVD = 'DVD'


class CamelModel(BaseModel):
    class Config:
        orm_mode = True
        use_enum_values = True
        allow_populate_by_alias = True
        alias_generator = to_camel
        allow_population_by_field_name = True


class FieldFilter(CamelModel):
    op: str
    field_name: str
    val: Union[str, List]


class DateRangeFilter(FieldFilter):
    val: conlist(Union[date, None], min_items=2, max_items=2)


class Filters(CamelModel):
    filters: Union[DateRangeFilter, FieldFilter]


class SortCol(CamelModel):
    row: str
    desc: bool


class PageableResultSet(CamelModel):
    page_index: int = 0
    page_limit: int = 0
    total_records: int = 0

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


class ExtraInfo(CamelModel):
    id: int
    order_number: str
    tags: Optional[str]
    override_reminder_time: Optional[int]
    reminder_receiver: Optional[str]
    validation: Optional[int]


class Order(CamelModel):
    id: int
    tags: Optional[List[Tags]]
    barcode: Optional[str]
    title: str
    order_number: str
    created_date: date
    arrival_date: Optional[date]
    ips_code: Optional[str]
    ips: Optional[str]
    ips_date: Optional[date]
    vendor_code: str
    library_note: Optional[str]
    tags: List[str]
    # override_date: Optional[Union[date, str]]


class OrderDetail(Order):
    bsn: str
    arrival_text: Optional[str]
    arrival_status: Optional[str]
    arrival_operator: Optional[str]
    items_created: Optional[str]
    item_status: Optional[str]
    material: Optional[str]
    collection: Optional[str]
    ips_update_date: Optional[date]
    ips_code_operator: Optional[str]
    update_date: Optional[date]
    sublibrary: Optional[str]
    order_status: Optional[str]
    invoice_status: Optional[str]
    material_type: Optional[str]
    order_type: Optional[str]
    order_unit: Optional[str]
    arrival_status: Optional[str]
    total_price: Optional[float]
    order_status_update_date: Optional[date]
    tracking_note: Optional[List[TimelineNote]]


class OrderFilter(Order):
    id: Optional[str]
    barcode: Optional[str]
    title: Optional[str]
    order_number: Optional[str]
    created_date: Optional[date]
    arrival_date: Optional[date]
    ips_date: Optional[date]
    vendor_code: Optional[str]


class PageableOrdersSet(PageableResultSet):
    result: List[Order]


class PageableOrderRequest(CamelModel):
    page_index: Optional[int] = 0
    page_size: Optional[int] = 10
    filters: Optional[Dict]
    sort: Optional[List[SortCol]]


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
    vendor_code: str
    name: Optional[str]
    # local: 0 - local, 1 - non-local
    local: int
    notify_in: Optional[int]


class MetaData(CamelModel):
    ips_code: Optional[List[Union[str, None]]]
    tags: Optional[List[Union[str, None]]]
    vendors: Optional[List[Union[str, None]]]
    oldest_date: Optional[date]
