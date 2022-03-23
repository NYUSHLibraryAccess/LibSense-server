from core.models import Vendor
from typing import List, Optional
from fastapi import APIRouter


router = APIRouter(prefix="/vendor", tags=["Vendor"])


@router.get("/", response_model=List[Vendor])
async def get_vendor(vendor_id: Optional[str]):
    return True


@router.post("/", response_model=Vendor)
async def new_vendor(vendor: Vendor):
    return vendor


@router.patch("/", response_model=Vendor)
async def update_vendor(vendor: Vendor):
    return vendor


@router.delete("/")
async def delete_vendor(vendor_id: str):
    return True
