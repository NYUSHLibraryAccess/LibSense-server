from datetime import date, datetime
from enum import Enum
from typing import List, Union, Optional
from pydantic import BaseModel, conlist
from humps import camelize


def to_camel(string):
    return camelize(string)


class CamelModel(BaseModel):
    class Config:
        orm_mode = True
        use_enum_values = True
        allow_populate_by_alias = True
        alias_generator = to_camel
        allow_population_by_field_name = True


class Tags(str, Enum):
    CDL = "CDL"
    LOCAL = "Local"
    RUSH = "Rush"
    NY = "NY"
    ILL = "ILL"
    NON_RUSH = "Non-Rush"
    SENSITIVE = "Sensitive"
    RESERVE = "Reserve"
    DVD = "DVD"

    @staticmethod
    def split_tags(tag_str):
        return tag_str[1:-1].split("][")

    @staticmethod
    def encode_tags(tags_list):
        return "[" + "][".join(tags_list) + "]"


class CDLStatus(str, Enum):
    CDL_SILENT = "CDL Silent"
    C_PDF_AVAIL = "Circ PDF Available"
    V_PDF_AVAIL = "Vendor PDF Available"
    CDL_DVD = "CDL DVD"
    REQUESTED = "Requested"
    ON_LOAN = "On Loan"


class PhysicalCopyStatus(str, Enum):
    NOT_ARRIVED = "Not Arrived"
    ON_SHELF = "On Shelf"
    DVD = "DVD"


class FilterOperators(str, Enum):
    IN = "in"
    LIKE = "like"
    EQUAL = "eq"  # only used in preset so far.
    BETWEEN = "between"
    GREATER = "greater"
    SMALLER = "smaller"


class ReportTypes(str, Enum):
    RUSH_LOCAL = "RushLocal"
    CDL_ORDER = "CDLOrder"
    SHANGHAI_ORDER = "ShanghaiOrder"


class EnumRole(str, Enum):
    SYS_ADMIN = "System Admin"
    USER = "User"


class EnumPresetTypes(str, Enum):
    FILTER = "filter"
    VIEW = "view"


class BasicResponse(CamelModel):
    msg: Optional[str] = "Success"


class FieldFilter(CamelModel):
    op: FilterOperators
    col: str
    val: Union[str, List, None]


class SortCol(CamelModel):
    col: str
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


class TrackingNote(CamelModel):
    book_id: int
    date: datetime
    taken_by: str
    tracking_note: str

    class Config:
        orm_mode = True


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


class AttentionRequest(CamelModel):
    id: List[int]
    attention: bool


class CheckedRequest(CamelModel):
    id: List[int]
    checked: bool
    date: Optional[date]


class Order(CamelModel):
    id: int
    tags: Optional[List[Tags]]
    barcode: Optional[str]
    title: Optional[str]
    order_number: str
    created_date: Optional[date]
    arrival_date: Optional[date]
    ips_code: Optional[str]
    ips: Optional[str]
    ips_date: Optional[date]
    vendor_code: Optional[str]
    library_note: Optional[str]
    tags: List[str]
    attention: Optional[bool]
    checked: Optional[bool]
    override_reminder_time: Optional[date]
    tracking_note: Optional[str]


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
    result: List[OrderDetail]


class OrderViews(CamelModel):
    cdl_view: Optional[bool] = False
    pending_rush_local: Optional[bool] = False
    pending_cdl: Optional[bool] = False
    prioritize: Optional[bool] = False


class PageableOrderRequest(CamelModel):
    page_index: Optional[int] = 0
    page_size: Optional[int] = 10
    filters: Optional[List[FieldFilter]]
    sorter: Optional[SortCol]
    fuzzy: Optional[str]
    views: Optional[OrderViews] = OrderViews()


class PresetRequest(CamelModel):
    preset_name: str
    filters: List[FieldFilter] = []
    views: OrderViews


class UpdatePresetRequest(PresetRequest):
    preset_id: int


class Preset(UpdatePresetRequest):
    creator: str


class CDLOrder(Order):
    cdl_item_status: Optional[List[CDLStatus]]
    order_request_date: Optional[date]
    scanning_vendor_payment_date: Optional[date]
    pdf_delivery_date: Optional[date]
    back_to_karms_date: Optional[Union[date, str]]
    circ_pdf_url: Optional[str]


class CDLOrderDetail(CDLOrder, OrderDetail):
    order_purchased_date: Optional[date]
    due_date: Optional[date]
    physical_copy_status: Optional[Union[PhysicalCopyStatus, None]]
    vendor_file_url: Optional[str]
    bobcat_permanent_link: Optional[str]
    file_password: Optional[str]
    author: Optional[str]
    pages: Optional[str]


class CDLRequest(CamelModel):
    cdl_item_status: Optional[CDLStatus]
    order_request_date: Optional[date]
    scanning_vendor_payment_date: Optional[date]
    pdf_delivery_date: Optional[date]
    back_to_karms_date: Optional[Union[date, str]]
    circ_pdf_url: Optional[str]
    order_purchased_date: Optional[date]
    due_date: Optional[date]
    physical_copy_status: Optional[str]
    vendor_file_url: Optional[str]
    bobcat_permanent_link: Optional[str]
    file_password: Optional[str]
    author: Optional[str]
    pages: Optional[str]


class PatchOrderRequest(CamelModel):
    book_id: int
    tracking_note: Optional[str]
    checked: Optional[bool] = "undefined"
    attention: Optional[bool] = "undefined"
    override_reminder_time: Optional[date] = "undefined"
    cdl: Optional[CDLRequest] = None


class PageableCDLOrdersSet(PageableResultSet):
    result: List[CDLOrderDetail]


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
    material: Optional[List[Union[str, None]]]
    material_type: Optional[List[Union[str, None]]]
    cdl_tags: Optional[List[Union[str, None]]]
    supported_report: Optional[List[Union[str, None]]]
    physical_copy_status: Optional[List[Union[str, None]]]


class Overview(CamelModel):
    local_rush_pending: int
    cdl_pending: int

    avg_cdl_scan: int
    avg_cdl: int
    avg_rush_nyc: int
    avg_rush_local: int

    max_cdl_scan: int
    max_cdl: int
    max_rush_nyc: int
    max_rush_local: int

    min_cdl_scan: int
    min_cdl: int
    min_rush_nyc: int
    min_rush_local: int


class SystemUser(CamelModel):
    username: str
    role: EnumRole


class LoginRequest(CamelModel):
    username: str
    password: str
    remember: Optional[bool]
    remember_test: Optional[bool]


class NewSystemUser(SystemUser):
    password: str


class SendReportRequest(CamelModel):
    username: str
    email: str
    report_type: List[ReportTypes]
