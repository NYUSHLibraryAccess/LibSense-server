import aiofiles
from core.utils import Data
from starlette import status
from fastapi import APIRouter, FastAPI, File, Header, Depends, BackgroundTasks, UploadFile, HTTPException
from sqlalchemy.orm import Session
from core.database import crud, model
from core.database.database import SessionLocal, engine
router = APIRouter(prefix='/data')


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def valid_content_length(content_length: int = Header(..., lt=8000000)):
    return content_length


@router.post("/upload")
async def upload_file(
        background_tasks: BackgroundTasks,
        db: Session = Depends(get_db),
        file: UploadFile = File(...),
        file_size: int = Depends(valid_content_length)):
    output_file = f"assets/source/{file.filename}"
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
        # background_tasks.add_task(Data.data_ingestion, db, output_file)
        Data.data_ingestion(db, output_file)
    except BaseException as e:
        print(e)
        raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="There was an error processing your file",
                    )

    return {"message": msg}
