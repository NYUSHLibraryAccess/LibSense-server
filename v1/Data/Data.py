import aiofiles
from core.utils import Data
from starlette import status
from fastapi import APIRouter, File, Header, Depends, UploadFile, HTTPException
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session
from core.database import crud
from loguru import logger
from core import schema
from core.utils.dependencies import get_db, validate_auth

router = APIRouter(prefix='/data', tags=["Data"], dependencies=[Depends(validate_auth)])


async def valid_content_length(content_length: int = Header(..., lt=8000000)):
    return content_length


@router.post("/upload")
async def upload_file(
        db: Session = Depends(get_db),
        file: UploadFile = File(...),
        file_size: int = Depends(valid_content_length)):
    output_file = f"assets/source/{file.filename}"
    if file.filename.split('.')[-1] not in ['csv', 'xls', 'xlsx']:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Please only upload file ends with .csv, .xls, or .xlsx")
    real_file_size = 0

    try:
        async with aiofiles.open(f"{output_file}", "wb") as out_file:
            while content := await file.read(1024):  # async read chunk
                real_file_size += len(content)
                if real_file_size > file_size:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail="Too large",
                    )
                await out_file.write(content)  # async write chunk
        msg = f"Successfully updated database with {file.filename}."
        await run_in_threadpool(lambda: Data.data_ingestion(db, output_file))
        await run_in_threadpool(lambda: Data.flush_tags(db))

    except BaseException as e:
        logger.error(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="There was an error processing your file",
        )

    return {"message": msg}


@router.get("/metadata", response_model=schema.MetaData)
async def get_metadata(db: Session = Depends(get_db)):
    tags = [e.value for e in schema.Tags]
    vendors = crud.get_vendor_meta(db)
    ips = crud.get_ips_meta(db)
    oldest_date = crud.get_oldest_date(db)
    material = crud.get_material_meta(db)
    material_type = crud.get_material_type_meta(db)
    cdl_tags = [i for i in schema.CDLStatus]
    supported_report = [r for r in schema.ReportTypes]

    return schema.MetaData(
        ips_code=[i[0] for i in ips],
        vendors=[v[0] for v in vendors],
        tags=tags,
        oldest_date=oldest_date,
        material=[m[0] for m in material],
        material_type=[mt[0] for mt in material_type],
        cdl_tags=cdl_tags,
        supported_report=supported_report
    )
