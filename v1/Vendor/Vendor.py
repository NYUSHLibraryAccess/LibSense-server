from core.schema import Vendor, BasicResponse
from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from core.database import crud
from core.utils.dependencies import get_db, validate_auth, validate_privilege

router = APIRouter(prefix="/vendor", tags=["Vendor"], dependencies=[Depends(validate_auth)])


@router.get("/all-vendors", response_model=List[Vendor])
async def get_all_vendors(db: Session = Depends(get_db)):
    return crud.get_all_vendors(db)


@router.get("", response_model=Vendor)
async def get_vendor(
        vendor_code: str = Query(None, alias="vendorCode"),
        db: Session = Depends(get_db)):
    return crud.get_vendor(db, vendor_code)


@router.post("", response_model=Vendor, dependencies=[Depends(validate_privilege)])
async def new_vendor(vendor: Vendor, db: Session = Depends(get_db)):
    return await crud.add_vendor(db, vendor)


@router.patch("", response_model=BasicResponse, dependencies=[Depends(validate_privilege)])
async def update_vendor(vendor: Vendor, db: Session = Depends(get_db)):
    return await crud.update_vendor(db, vendor)


@router.delete("", response_model=BasicResponse, dependencies=[Depends(validate_privilege)])
async def delete_vendor(
        vendor_code: str = Query(None, alias="vendorCode"), db: Session = Depends(get_db)):
    return await crud.delete_vendor(db, vendor_code)
