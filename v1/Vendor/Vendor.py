from core.schema import Vendor
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from core.database import crud
from core.database.database import SessionLocal

router = APIRouter(prefix="/vendor", tags=["Vendor"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/all-vendors", response_model=List[Vendor])
async def get_all_vendors(db: Session = Depends(get_db)):
    return crud.get_all_vendors(db)


@router.get("/", response_model=Vendor)
async def get_vendor(vendor_code: str, db: Session = Depends(get_db)):
    return crud.get_vendor(db, vendor_code)


@router.post("/", response_model=Vendor)
async def new_vendor(vendor: Vendor, db: Session = Depends(get_db)):
    return crud.add_vendor(db, vendor)


@router.patch("/")
async def update_vendor(vendor: Vendor, db: Session = Depends(get_db)):
    crud.update_vendor(db, vendor)
    return {"msg": "Success"}


@router.delete("/")
async def delete_vendor(vendor_code: str = Query(None, alias="vendorCode"), db: Session = Depends(get_db)):
    crud.delete_vendor(db, vendor_code)
    return {"msg": "Success"}
