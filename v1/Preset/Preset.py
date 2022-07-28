import json
from typing import List
from core.database import crud, model
from core.schema import (
    BasicResponse,
    Preset,
    PresetRequest,
    UpdatePresetRequest,
    EnumPresetTypes,
    FilterOperators,
    FieldFilter,
    OrderViews,
)
from core.utils.dependencies import get_db, validate_auth
from fastapi import APIRouter, Depends, Query, Request, HTTPException
from sqlalchemy.orm import Session

router = APIRouter(prefix="/preset", tags=["Preset"], dependencies=[Depends(validate_auth)])


def preset_to_db(preset, username=None):
    lst = []
    for f in preset.filters:
        filter_dict = {
            "preset_name": preset.preset_name,
            "col": f.col,
            "val": json.dumps(f.val),
            "op": f.op,
            "type": EnumPresetTypes.FILTER,
        }
        if username:
            filter_dict["creator"] = username
        lst.append(filter_dict)

    for col, val in preset.views.__dict__.items():
        view_dict = {
            "preset_name": preset.preset_name,
            "col": col,
            "val": json.dumps(val),
            "op": FilterOperators.EQUAL,
            "type": EnumPresetTypes.VIEW,
        }
        if username:
            view_dict["creator"] = username
        lst.append(view_dict)

    return lst


def db_to_preset(presets: List[model.Preset]):
    lst = []
    preset_dict = {}
    for idx, row in enumerate(presets[1:]):
        if row.preset_id != preset_dict.get("preset_id", None):
            if idx != 0:
                lst.append(preset_dict)
            preset_dict = {
                "preset_id": row.preset_id,
                "preset_name": row.preset_name,
                "creator": row.creator,
                "filters": [],
                "views": OrderViews(),
            }
        if row.type == EnumPresetTypes.FILTER:
            preset_dict["filters"].append(
                FieldFilter(col=row.col, val=json.loads(row.val), op=row.op)
            )
        elif row.type == EnumPresetTypes.VIEW:
            setattr(preset_dict["views"], row.col, json.loads(row.val))

    lst.append(preset_dict)
    preset_lst = [Preset(**p) for p in lst]

    return preset_lst


@router.get("/", response_model=List[Preset])
async def get_all_presets(request: Request, db: Session = Depends(get_db)):
    return db_to_preset(crud.get_all_presets(db, request.session["username"]))


@router.post("/", response_model=BasicResponse)
async def new_preset(request: Request, preset: PresetRequest, db: Session = Depends(get_db)):
    return crud.add_preset(db, preset_to_db(preset, request.session["username"]))


@router.patch("/", response_model=BasicResponse)
async def update_preset(
    request: Request, preset: UpdatePresetRequest, db: Session = Depends(get_db)
):
    result = crud.update_preset(
        db, preset_to_db(preset), preset.preset_id, request.session["username"]
    )
    if result == -1:
        raise (HTTPException(status_code=500, detail="Error when updating preset"))
    return result


@router.delete("/", response_model=BasicResponse)
async def delete_preset(
    request: Request, preset_id: int = Query(None, alias="presetId"), db: Session = Depends(get_db)
):
    result = crud.delete_preset(db, preset_id, request.session["username"])
    if result == -1:
        raise HTTPException(status_code=500, detail="Error when deleting preset")
    return result
