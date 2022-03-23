from core.models import PageableOrdersSet, PageableCDLOrdersSet, TimelineNote, Order, CDLOrder
from fastapi import APIRouter
from datetime import date
from typing import Optional

router = APIRouter(prefix="/orders", tags=["Order"])


@router.get("/general-order", response_model=PageableOrdersSet)
async def get_all_order(page_index: Optional[int] = None, page_size: Optional[int] = None):
    return True


@router.get("/cdl-order", response_model=PageableCDLOrdersSet, tags=["CDL Order"])
async def get_cdl_order(page_index: Optional[int] = None, page_size: Optional[int] = None):
    return True


@router.patch("/general-order")
async def update_general_order(net_id: str, order: Order):
    return True


@router.patch("/cdl-order", tags=["CDL Order"])
async def update_cdl_order(net_id: str, cdl_order: CDLOrder):
    return True


@router.patch("/add-note")
async def add_note(net_id: str, uuid: str, note: TimelineNote):
    return True
