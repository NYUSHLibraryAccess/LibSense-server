
from datetime import date
from typing import List, Optional
from pydantic import BaseModel


class Message(BaseModel):
    id: int
    message: Optional[str]
    book_related: Optional[str]


class TimelineNote(BaseModel):
    date: date
    message: str


class User(BaseModel):
    net_id: str
    name: str
    role = 'user'
    messages: List[Message]


class Order(BaseModel):
    uuid: str
    barcode: str
    title: str
    order_number: str
    order_create_date: date
    order_arrival_date: date
    ips_code: str
    process_status: Optional[str]
    process_status_date: date
    ny_note: Optional[str]
    library_note: Optional[TimelineNote]

    class Config:
        orm_mode: True