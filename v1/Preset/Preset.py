from typing import List
from core.schema import BasicResponse, Preset
from core.utils.dependencies import get_db, validate_auth
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

router = APIRouter(prefix="/preset", tags=["Preset"], dependencies=[Depends(validate_auth)])


@router.get("/", response_model=List[Preset])
async def get_all_presets(db: Session = Depends(get_db)):
    return


@router.post("/", response_model=BasicResponse)
async def new_preset(preset: Preset, db: Session = Depends(get_db)):
    return


@router.patch("/", response_model=BasicResponse)
async def update_preset(preset: Preset, db: Session = Depends(get_db)):
    return


@router.delete("/", response_model=BasicResponse)
async def delete_preset(preset_id: int = Query(None, alias="presetId"), db: Session = Depends(get_db)):
    return
